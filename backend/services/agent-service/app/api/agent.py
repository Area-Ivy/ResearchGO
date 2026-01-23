"""
Agent API Endpoints
"""
import json
import logging
from typing import Optional, Union
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..agent.graph import get_agent
from ..models.state import ChatRequest, ChatResponse, StreamEvent
from ..utils.auth import get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])


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


@router.post("/chat")
async def agent_chat(
    request: AgentChatRequest,
    req: Request,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Agent 聊天接口
    
    - 支持流式和非流式响应
    - 流式响应返回 SSE 事件流
    """
    user_id = current_user.get("user_id") if current_user else None
    token = req.headers.get("Authorization", "").replace("Bearer ", "") if req.headers.get("Authorization") else None
    
    agent = get_agent()
    
    if request.stream:
        # 流式响应
        async def event_generator():
            try:
                async for event in agent.run_stream(
                    user_input=request.message,
                    user_id=user_id,
                    token=token
                ):
                    yield {
                        "event": event.event,
                        "data": json.dumps(event.data, ensure_ascii=False) if event.data else ""
                    }
            except Exception as e:
                logger.error(f"Agent stream error: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
        
        return EventSourceResponse(event_generator())
    else:
        # 非流式响应
        try:
            result = await agent.run(
                user_input=request.message,
                user_id=user_id,
                token=token
            )
            return AgentChatResponse(
                message=result["answer"],
                thoughts=result.get("thoughts", []),
                tool_calls=[tc.dict() if hasattr(tc, 'dict') else tc for tc in result.get("tool_calls", [])]
            )
        except Exception as e:
            logger.error(f"Agent error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


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
    return {
        "status": "healthy",
        "service": "agent-service"
    }

