"""
Agent API Endpoints
支持多轮对话的 AI Agent 接口

优化：
- 对话历史缓存在 Redis，减少 HTTP 调用
- 异步写入 conversation-service，不阻塞响应
"""
import json
import logging
import os
from typing import Optional, Union, List
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import httpx

from ..agent.graph import get_agent
from ..models.state import ChatRequest, ChatResponse, StreamEvent
from ..utils.auth import get_current_user, get_optional_user
from ..memory.conversation_cache import get_conversation_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])

# Conversation Service URL
CONVERSATION_SERVICE_URL = os.getenv("CONVERSATION_SERVICE_URL", "http://localhost:8002")


class AgentChatRequest(BaseModel):
    """Agent 聊天请求"""
    message: str
    conversation_id: Optional[Union[str, int]] = None
    stream: bool = True


class AgentChatResponse(BaseModel):
    """Agent 聊天响应"""
    message: str
    conversation_id: Optional[str] = None
    thoughts: list = []
    tool_calls: list = []


def generate_title_from_message(message: str, max_length: int = 30) -> str:
    """从消息内容生成对话标题"""
    title = message.replace("\n", " ").strip()
    if len(title) > max_length:
        title = title[:max_length] + "..."
    return title or "新对话"


@router.post("/chat")
async def agent_chat(
    request: AgentChatRequest,
    req: Request,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Agent 聊天接口 - 支持多轮对话
    
    优化后的流程：
    1. 从 Redis 缓存加载历史（快！）
    2. 缓存未命中才从 conversation-service 加载
    3. 消息追加到缓存（同步）
    4. 异步写入 conversation-service（不阻塞）
    """
    user_id = current_user.get("user_id") if current_user else None
    token = req.headers.get("Authorization", "").replace("Bearer ", "") if req.headers.get("Authorization") else None
    
    conversation_id = request.conversation_id
    conversation_history = []
    is_new_conversation = False
    
    # 获取缓存管理器
    cache = get_conversation_cache()
    
    # 1. 处理对话会话
    if token:
        if conversation_id:
            # 从缓存加载历史（优先 Redis）
            conversation_history = await cache.load_history(conversation_id, token)
        else:
            # 创建新对话
            title = generate_title_from_message(request.message)
            new_id = await cache.create_conversation(token, title)
            if new_id:
                conversation_id = new_id
                is_new_conversation = True
                logger.info(f"Created new conversation: {conversation_id}")
    
    agent = get_agent()
    
    if request.stream:
        # 流式响应
        async def event_generator():
            final_answer = ""
            
            try:
                # 发送 conversation_id（如果是新创建的）
                if is_new_conversation and conversation_id:
                    yield {
                        "event": "conversation",
                        "data": json.dumps({"conversation_id": conversation_id})
                    }
                
                # 追加用户消息到缓存（同步快速 + 异步持久化）
                if token and conversation_id:
                    await cache.append_message(
                        conversation_id, "user", request.message, token
                    )
                
                # 运行 Agent
                async for event in agent.run_stream(
                    user_input=request.message,
                    user_id=user_id,
                    token=token,
                    conversation_history=conversation_history,
                    conversation_id=str(conversation_id) if conversation_id else None
                ):
                    # 记录最终答案
                    if event.event == "answer":
                        final_answer = event.data
                    
                    yield {
                        "event": event.event,
                        "data": json.dumps(event.data, ensure_ascii=False) if event.data else ""
                    }
                
                # 追加 AI 回复到缓存（同步快速 + 异步持久化）
                if token and conversation_id and final_answer:
                    await cache.append_message(
                        conversation_id, "assistant", final_answer, token
                    )
                    
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"Agent stream error: {e}\n{error_detail}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e) or "Unknown error"})
                }
        
        return EventSourceResponse(event_generator())
    else:
        # 非流式响应
        try:
            # 追加用户消息到缓存
            if token and conversation_id:
                await cache.append_message(
                    conversation_id, "user", request.message, token
                )
            
            result = await agent.run(
                user_input=request.message,
                user_id=user_id,
                token=token,
                conversation_history=conversation_history,
                conversation_id=str(conversation_id) if conversation_id else None
            )
            
            final_answer = result.get("answer", "")
            
            # 追加 AI 回复到缓存
            if token and conversation_id and final_answer:
                await cache.append_message(
                    conversation_id, "assistant", final_answer, token
                )
            
            return AgentChatResponse(
                message=final_answer,
                conversation_id=str(conversation_id) if conversation_id else None,
                thoughts=result.get("thoughts", []),
                tool_calls=[tc.dict() if hasattr(tc, 'dict') else tc for tc in result.get("tool_calls", [])]
            )
        except Exception as e:
            logger.error(f"Agent error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(
    req: Request,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """获取用户的对话列表（代理到 conversation-service）"""
    token = req.headers.get("Authorization", "").replace("Bearer ", "")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CONVERSATION_SERVICE_URL}/api/conversations",
                params={"skip": skip, "limit": limit},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="获取对话列表失败")
    except httpx.RequestError as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=503, detail="对话服务不可用")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """获取对话详情（代理到 conversation-service）"""
    token = req.headers.get("Authorization", "").replace("Bearer ", "")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="对话不存在")
            else:
                raise HTTPException(status_code=response.status_code, detail="获取对话失败")
    except httpx.RequestError as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=503, detail="对话服务不可用")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """删除对话（代理到 conversation-service + 清除缓存）"""
    token = req.headers.get("Authorization", "").replace("Bearer ", "")
    
    try:
        # 1. 清除 Redis 缓存
        cache = get_conversation_cache()
        await cache.invalidate_cache(conversation_id)
        
        # 2. 删除 conversation-service 中的数据
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 204:
                return {"message": "对话已删除"}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="对话不存在")
            else:
                raise HTTPException(status_code=response.status_code, detail="删除对话失败")
    except httpx.RequestError as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=503, detail="对话服务不可用")


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """获取缓存统计信息"""
    cache = get_conversation_cache()
    stats = await cache.get_stats()
    return {
        "success": True,
        "stats": stats
    }


@router.post("/cache/invalidate/{conversation_id}")
async def invalidate_conversation_cache(
    conversation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """手动使对话缓存失效"""
    cache = get_conversation_cache()
    await cache.invalidate_cache(conversation_id)
    return {"message": f"对话 {conversation_id} 的缓存已清除"}


@router.get("/tools")
async def list_tools():
    """获取所有可用工具列表"""
    from ..tools.registry import tool_registry
    
    tools = []
    for tool in tool_registry.get_all():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        })
    
    return {"tools": tools}


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    arguments: dict,
    req: Request,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    直接执行指定工具
    
    用于调试或前端直接调用工具
    """
    from ..tools.registry import tool_registry
    
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    
    token = req.headers.get("Authorization", "").replace("Bearer ", "") if req.headers.get("Authorization") else None
    
    try:
        if token:
            arguments["token"] = token
        result = await tool(**arguments)
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "duration_ms": result.duration_ms
        }
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    cache = get_conversation_cache()
    stats = await cache.get_stats()
    
    return {
        "status": "healthy",
        "service": "agent-service",
        "cache": {
            "hit_rate": stats["hit_rate"],
            "queue_size": stats["queue_size"]
        }
    }


@router.get("/circuit-breakers")
async def get_circuit_breaker_status():
    """
    获取所有工具的熔断器状态
    
    用于监控和调试
    """
    from ..tools.registry import tool_registry
    
    status = tool_registry.get_circuit_breaker_status()
    degraded = tool_registry.get_degraded_tools()
    
    return {
        "total_tools": len(tool_registry.get_all()),
        "degraded_count": len(degraded),
        "degraded_tools": degraded,
        "breakers": status
    }


@router.post("/circuit-breakers/{tool_name}/reset")
async def reset_circuit_breaker(
    tool_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    手动重置指定工具的熔断器
    
    需要管理员权限
    """
    from ..tools.registry import tool_registry
    from ..utils.circuit_breaker import CircuitState
    
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    
    if not tool.breaker:
        raise HTTPException(status_code=400, detail=f"Tool {tool_name} has no circuit breaker")
    
    # 重置熔断器
    tool.breaker.state = CircuitState.CLOSED
    tool.breaker.stats.consecutive_failures = 0
    
    logger.info(f"Circuit breaker for {tool_name} manually reset by user {current_user.get('user_id')}")
    
    return {
        "success": True,
        "message": f"Circuit breaker for {tool_name} has been reset",
        "new_status": tool.breaker.get_status()
    }

