"""
LangGraph Agent Implementation

集成三层记忆系统：
1. 短期记忆: 滑动窗口 + Redis Checkpointer
2. 长对话摘要: 自动摘要超长对话
3. 语义记忆: 基于向量的跨会话记忆
"""
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from ..models.state import AgentState, ToolCall, StreamEvent
from ..tools.registry import tool_registry
from ..config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, MAX_ITERATIONS,
    SLIDING_WINDOW_SIZE, ENABLE_CONVERSATION_SUMMARY, ENABLE_SEMANTIC_MEMORY,
    ENABLE_CHECKPOINTER
)
from ..memory.sliding_window import SmartSlidingWindow
from ..memory.checkpointer import get_checkpointer
from ..memory.summary import get_summary_manager
from ..memory.semantic_memory import get_semantic_memory_service
from ..utils.circuit_breaker import get_breaker_manager, TOOL_ALTERNATIVES

logger = logging.getLogger(__name__)

# System prompt with memory context placeholder
SYSTEM_PROMPT = """你是 ResearchGO 的 AI 研究助手，专门帮助用户进行学术研究。

你的能力：
1. 搜索学术文献（OpenAlex 数据库，包含数亿篇论文）
2. 管理用户的论文库（上传、搜索、查看）
3. 语义搜索（基于内容的智能检索）
4. 论文问答（基于论文内容回答问题）
5. 论文分析（生成分析报告、思维导图）
6. 论文对比（对比多篇论文的异同）

工作原则：
1. 优先理解用户意图，选择最合适的工具
2. 如果需要多步操作，按顺序执行
3. 工具返回结果后，用自然语言总结给用户
4. **智能降级原则**（重要）：
   - 如果工具调用失败或返回降级通知，**不要直接告诉用户"请稍后重试"**
   - 首先查看降级通知中的替代方案建议
   - 尝试使用替代工具完成用户需求
   - 如果没有合适的替代工具，尝试基于你的知识直接回答
   - 只有在完全无法帮助时，才告知用户并提供替代建议
5. 回答要简洁清晰，重点突出

你可以使用的工具：
{tool_descriptions}
{memory_context}
{degraded_tools_notice}
记住：你是一个专业的研究助手，即使某些工具暂时不可用，也要想办法帮助用户完成任务。"""


# 降级工具通知模板
DEGRADED_TOOLS_NOTICE = """
⚠️ **当前不可用的工具**：{tools}

这些工具因为服务问题暂时熔断。当用户请求相关功能时：
1. 优先使用替代工具
2. 或基于你的知识回答
3. 不要简单地说"请稍后重试"
"""


class ResearchAgent:
    """
    ResearchGO Agent 基于 LangGraph
    
    集成三层记忆架构：
    - 短期记忆: 滑动窗口限制上下文长度
    - 长对话摘要: 超长对话自动生成摘要
    - 语义记忆: 跨会话的用户画像和偏好
    """
    
    def __init__(self):
        # 初始化 LLM（启用流式输出）
        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.7,
            "api_key": OPENAI_API_KEY,
            "streaming": True,  # 启用流式输出
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 绑定工具到 LLM
        self.tools = tool_registry.get_openai_functions()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 初始化记忆组件
        self.sliding_window = SmartSlidingWindow(window_size=SLIDING_WINDOW_SIZE)
        self.checkpointer = get_checkpointer() if ENABLE_CHECKPOINTER else None
        
        # 构建图
        self.graph = self._build_graph()
        
        # 编译图（带/不带 checkpointer）
        if self.checkpointer:
            self.app = self.graph.compile(checkpointer=self.checkpointer)
            logger.info("Agent compiled with Redis Checkpointer")
        else:
            self.app = self.graph.compile()
            logger.info("Agent compiled without Checkpointer")
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        graph = StateGraph(AgentState)
        
        # 添加节点
        graph.add_node("reason", self._reason_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("respond", self._respond_node)
        
        # 设置入口点
        graph.set_entry_point("reason")
        
        # 添加条件边
        graph.add_conditional_edges(
            "reason",
            self._should_continue,
            {
                "execute_tools": "execute_tools",
                "respond": "respond",
                "end": END
            }
        )
        
        # 工具执行后回到推理节点
        graph.add_edge("execute_tools", "reason")
        
        # 响应节点结束
        graph.add_edge("respond", END)
        
        return graph
    
    async def _prepare_context(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str],
        user_input: str,
        conversation_id: Optional[str],
        token: Optional[str]
    ) -> tuple[List[Dict[str, Any]], str, str]:
        """
        准备上下文：应用三层记忆系统
        
        Returns:
            (处理后的消息, 对话摘要, 用户记忆上下文)
        """
        summary = ""
        memory_context = ""
        processed_messages = messages
        
        # 1. 长对话摘要
        if ENABLE_CONVERSATION_SUMMARY and conversation_id:
            try:
                summary_manager = get_summary_manager()
                summary_result = await summary_manager.process(
                    messages=messages,
                    conversation_id=conversation_id,
                    window_size=SLIDING_WINDOW_SIZE
                )
                
                if summary_result.summary:
                    summary = summary_result.summary
                    processed_messages = summary_result.window_messages
                    logger.info(
                        f"Applied summary: {summary_result.original_count} -> "
                        f"{len(processed_messages)} messages (summarized: {summary_result.summarized_count})"
                    )
            except Exception as e:
                logger.warning(f"Summary processing failed: {e}")
        
        # 2. 滑动窗口（在摘要之后应用，进一步控制 Token）
        processed_messages, window_stats = self.sliding_window.apply(
            processed_messages,
            strategy="hybrid"
        )
        
        if window_stats.messages_dropped > 0:
            logger.info(f"Sliding window dropped {window_stats.messages_dropped} messages")
        
        # 3. 语义记忆（获取用户相关上下文）
        if ENABLE_SEMANTIC_MEMORY and user_id and token:
            try:
                semantic_memory = get_semantic_memory_service()
                memory_context = await semantic_memory.get_user_context(
                    user_id=user_id,
                    current_query=user_input,
                    token=token
                )
                
                if memory_context:
                    logger.info(f"Retrieved semantic memory context for user {user_id}")
            except Exception as e:
                logger.warning(f"Semantic memory retrieval failed: {e}")
        
        return processed_messages, summary, memory_context
    
    async def _reason_node(self, state: AgentState) -> Dict[str, Any]:
        """推理节点：分析用户意图，决定是否调用工具"""
        logger.info(f"Reason node - iteration: {state.get('iteration', 0)}")
        
        # 获取状态信息
        raw_messages = state.get("messages", [])
        user_id = state.get("user_id")
        user_input = state.get("user_input", "")
        conversation_id = state.get("conversation_id")
        token = state.get("token")
        
        logger.debug(f"Reason node: user_input='{user_input[:50] if user_input else ''}...', messages={len(raw_messages)}")
        
        # 应用三层记忆系统
        processed_messages, summary, memory_context = await self._prepare_context(
            messages=raw_messages,
            user_id=user_id,
            user_input=user_input,
            conversation_id=conversation_id,
            token=token
        )
        
        # 构建 memory context 部分
        memory_section = ""
        if summary or memory_context:
            memory_section = "\n\n--- 上下文信息 ---"
            if summary:
                memory_section += f"\n[对话摘要]: {summary}"
            if memory_context:
                memory_section += f"\n[用户背景]:\n{memory_context}"
            memory_section += "\n--- 上下文结束 ---\n"
        
        # 获取当前被熔断的工具
        degraded_tools_notice = ""
        breaker_manager = get_breaker_manager()
        degraded_tools = breaker_manager.get_degraded_tools()
        if degraded_tools:
            # 构建详细的降级工具通知，包含替代方案
            degraded_info_list = []
            for tool_name in degraded_tools:
                alt_info = TOOL_ALTERNATIVES.get(tool_name, {})
                alternatives = alt_info.get("alternatives", [])
                hint = alt_info.get("hint", "")
                if alternatives:
                    degraded_info_list.append(f"- {tool_name} → 替代方案: {', '.join(alternatives)}")
                else:
                    degraded_info_list.append(f"- {tool_name} → 无替代工具，需直接回答")
            
            degraded_tools_notice = DEGRADED_TOOLS_NOTICE.format(
                tools="\n".join(degraded_info_list)
            )
            logger.warning(f"当前被熔断的工具: {degraded_tools}")
        
        # 构建消息列表
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(
                tool_descriptions=tool_registry.get_tool_descriptions(),
                memory_context=memory_section,
                degraded_tools_notice=degraded_tools_notice
            ))
        ]
        
        # 添加处理后的历史消息
        for msg in processed_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # 检查是否有 tool_calls
                if msg.get("tool_calls"):
                    # 创建带有 tool_calls 的 AIMessage
                    ai_msg = AIMessage(
                        content=msg.get("content", ""),
                        tool_calls=msg["tool_calls"]
                    )
                    messages.append(ai_msg)
                else:
                    messages.append(AIMessage(content=msg.get("content", "")))
            elif msg["role"] == "tool":
                messages.append(ToolMessage(
                    content=msg["content"],
                    tool_call_id=msg.get("tool_call_id", "")
                ))
        
        logger.debug(f"Calling LLM with {len(messages)} messages")
        
        # 调用 LLM
        response = await self.llm_with_tools.ainvoke(messages)
        
        # 处理响应
        tool_calls = []
        thoughts = state.get("thoughts", [])
        
        if response.tool_calls:
            # LLM 决定调用工具
            for tc in response.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["args"]
                ))
                thoughts.append(f"🔧 准备调用工具: {tc['name']}")
            
            return {
                "messages": [{"role": "assistant", "content": response.content or "", "tool_calls": response.tool_calls}],
                "tool_calls": tool_calls,
                "thoughts": thoughts,
                "should_continue": True,
                "iteration": state.get("iteration", 0) + 1
            }
        else:
            # LLM 直接回答
            return {
                "messages": [{"role": "assistant", "content": response.content}],
                "final_answer": response.content,
                "should_continue": False,
                "iteration": state.get("iteration", 0) + 1
            }
    
    async def _execute_tools_node(self, state: AgentState) -> Dict[str, Any]:
        """工具执行节点"""
        logger.info("Execute tools node")
        
        tool_calls = state.get("tool_calls", [])
        thoughts = state.get("thoughts", [])
        new_messages = []
        
        for tc in tool_calls:
            tool = tool_registry.get(tc.name)
            if not tool:
                error_msg = f"工具 {tc.name} 不存在"
                thoughts.append(f"❌ {error_msg}")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": error_msg}),
                    "tool_call_id": tc.id
                })
                continue
            
            # 执行工具
            thoughts.append(f"⚙️ 正在执行: {tc.name}")
            
            # 添加 token（如果状态中有的话）
            kwargs = tc.arguments.copy()
            if state.get("token"):
                kwargs["token"] = state["token"]
            
            result = await tool(**kwargs)
            
            if result.success:
                thoughts.append(f"✅ {tc.name} 执行成功")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps(result.data, ensure_ascii=False),
                    "tool_call_id": tc.id
                })
            elif result.is_degraded:
                # 智能降级响应：工具被熔断
                thoughts.append(f"⚠️ {tc.name} 服务熔断，需要智能降级")
                
                # 获取替代方案信息
                alt_info = TOOL_ALTERNATIVES.get(tc.name, {})
                alternatives = alt_info.get("alternatives", [])
                hint = alt_info.get("hint", "")
                
                # 构建给 LLM 的降级指导
                degraded_guidance = {
                    "status": "degraded",
                    "tool": tc.name,
                    "message": "该工具暂时不可用，请采取智能降级策略",
                    "alternatives": alternatives,
                    "hint": hint,
                    "instruction": "请根据以上替代方案尝试其他方法帮助用户，不要直接告诉用户'请稍后重试'"
                }
                
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps(degraded_guidance, ensure_ascii=False),
                    "tool_call_id": tc.id
                })
                
                logger.warning(f"工具 {tc.name} 返回降级响应，替代方案: {alternatives}")
            else:
                thoughts.append(f"❌ {tc.name} 执行失败: {result.error}")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": result.error}),
                    "tool_call_id": tc.id
                })
            
            # 更新工具调用结果
            tc.result = result.data if result.success else None
            tc.error = result.error if not result.success else None
            tc.duration_ms = result.duration_ms
        
        return {
            "messages": new_messages,
            "thoughts": thoughts,
            "tool_calls": []  # 清空已执行的工具调用
        }
    
    async def _respond_node(self, state: AgentState) -> Dict[str, Any]:
        """响应节点：生成最终回答"""
        logger.info("Respond node")
        return {
            "final_answer": state.get("final_answer", "抱歉，我无法处理您的请求。")
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """决定下一步走向"""
        iteration = state.get("iteration", 0)
        
        # 检查迭代次数限制
        if iteration >= MAX_ITERATIONS:
            logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached")
            return "respond"
        
        # 检查是否有工具需要执行
        if state.get("tool_calls"):
            return "execute_tools"
        
        # 检查是否应该继续
        if state.get("should_continue", False):
            return "execute_tools"
        
        # 有最终答案则结束
        if state.get("final_answer"):
            return "end"
        
        return "respond"
    
    async def _post_process_memories(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str],
        token: Optional[str]
    ):
        """
        后处理：从对话中提取并存储语义记忆
        
        在对话结束后异步执行，不阻塞响应
        """
        if not ENABLE_SEMANTIC_MEMORY or not user_id or not token:
            return
        
        try:
            semantic_memory = get_semantic_memory_service()
            stored_count = await semantic_memory.process_and_store(
                messages=messages,
                user_id=user_id,
                token=token
            )
            
            if stored_count > 0:
                logger.info(f"Post-process: stored {stored_count} memories for user {user_id}")
        except Exception as e:
            logger.warning(f"Post-process memory storage failed: {e}")
    
    async def run(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行 Agent（非流式）"""
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "user_id": user_id,
            "token": token,
            "conversation_id": conversation_id,
            "tool_calls": [],
            "iteration": 0,
            "should_continue": True,
            "final_answer": None,
            "error": None,
            "thoughts": []
        }
        
        # 添加用户消息
        initial_state["messages"].append({"role": "user", "content": user_input})
        
        # 构建配置（用于 checkpointer）
        config = {}
        if self.checkpointer and conversation_id:
            config = {"configurable": {"thread_id": f"conv_{conversation_id}"}}
        
        # 运行图
        final_state = await self.app.ainvoke(initial_state, config=config)
        
        # 后处理：提取语义记忆（异步，不阻塞）
        await self._post_process_memories(
            messages=final_state.get("messages", []),
            user_id=user_id,
            token=token
        )
        
        return {
            "answer": final_state.get("final_answer", ""),
            "thoughts": final_state.get("thoughts", []),
            "tool_calls": final_state.get("tool_calls", [])
        }
    
    async def run_stream(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """运行 Agent（流式）"""
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "user_id": user_id,
            "token": token,
            "conversation_id": conversation_id,
            "tool_calls": [],
            "iteration": 0,
            "should_continue": True,
            "final_answer": None,
            "error": None,
            "thoughts": []
        }
        
        # 添加用户消息
        initial_state["messages"].append({"role": "user", "content": user_input})
        
        # 构建配置（用于 checkpointer）
        config = {}
        if self.checkpointer and conversation_id:
            config = {"configurable": {"thread_id": f"conv_{conversation_id}"}}
        
        # 流式运行 - 使用 astream_events 获取 token 级别流式输出
        last_thoughts_count = 0
        final_messages = []
        final_answer_chunks = []
        
        async for event in self.app.astream_events(initial_state, config=config, version="v2"):
            event_type = event.get("event")
            
            # LLM token 流式输出
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    final_answer_chunks.append(chunk.content)
                    yield StreamEvent(event="token", data=chunk.content)
            
            # 节点开始
            elif event_type == "on_chain_start":
                node_name = event.get("name", "")
                if node_name in ["reason", "execute_tools", "respond"]:
                    yield StreamEvent(event="node_start", data=node_name)
            
            # 节点结束
            elif event_type == "on_chain_end":
                node_name = event.get("name", "")
                output = event.get("data", {}).get("output", {})
                
                if isinstance(output, dict):
                    # 收集消息用于后处理
                    if output.get("messages"):
                        final_messages.extend(output["messages"])
                    
                    # 发送思考过程
                    thoughts = output.get("thoughts", [])
                    if len(thoughts) > last_thoughts_count:
                        for thought in thoughts[last_thoughts_count:]:
                            yield StreamEvent(event="thinking", data=thought)
                        last_thoughts_count = len(thoughts)
                    
                    # 发送工具调用信息
                    if output.get("tool_calls"):
                        for tc in output["tool_calls"]:
                            yield StreamEvent(
                                event="tool_call",
                                data={
                                    "name": tc.name,
                                    "arguments": tc.arguments
                                }
                            )
                    
                    # 发送工具执行结果
                    messages = output.get("messages", [])
                    for msg in messages:
                        if msg.get("role") == "tool":
                            try:
                                tool_data = json.loads(msg.get("content", "{}"))
                                if tool_data.get("results") and isinstance(tool_data["results"], list):
                                    if tool_data["results"] and "title" in tool_data["results"][0]:
                                        yield StreamEvent(
                                            event="papers",
                                            data={
                                                "query": tool_data.get("query", ""),
                                                "total": tool_data.get("total_count", len(tool_data["results"])),
                                                "papers": tool_data["results"]
                                            }
                                        )
                            except:
                                pass
                    
                    # 发送最终答案完成信号
                    if output.get("final_answer"):
                        # 如果之前没有流式输出 token，发送完整答案
                        if not final_answer_chunks:
                            yield StreamEvent(event="answer", data=output["final_answer"])
                        else:
                            yield StreamEvent(event="answer_end", data=None)
        
        # 后处理：提取语义记忆
        await self._post_process_memories(
            messages=initial_state["messages"] + final_messages,
            user_id=user_id,
            token=token
        )
        
        yield StreamEvent(event="done", data=None)


# 全局 Agent 实例
_agent_instance: Optional[ResearchAgent] = None


def get_agent() -> ResearchAgent:
    """获取 Agent 单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ResearchAgent()
    return _agent_instance
