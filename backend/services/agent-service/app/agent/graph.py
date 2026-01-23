"""
LangGraph Agent Implementation
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
from ..config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, MAX_ITERATIONS

logger = logging.getLogger(__name__)

# System prompt
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
4. 如果工具调用失败，尝试其他方案或告知用户
5. 回答要简洁清晰，重点突出

你可以使用的工具：
{tool_descriptions}

记住：你是一个专业的研究助手，要帮助用户高效地完成研究任务。"""


class ResearchAgent:
    """ResearchGO Agent 基于 LangGraph"""
    
    def __init__(self):
        # 初始化 LLM
        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.7,
            "api_key": OPENAI_API_KEY,
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 绑定工具到 LLM
        self.tools = tool_registry.get_openai_functions()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 构建图
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
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
    
    async def _reason_node(self, state: AgentState) -> Dict[str, Any]:
        """推理节点：分析用户意图，决定是否调用工具"""
        logger.info(f"Reason node - iteration: {state.get('iteration', 0)}")
        
        # 构建消息列表
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(
                tool_descriptions=tool_registry.get_tool_descriptions()
            ))
        ]
        
        # 添加历史消息
        for msg in state.get("messages", []):
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
    
    async def run(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None
    ) -> Dict[str, Any]:
        """运行 Agent（非流式）"""
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "user_id": user_id,
            "token": token,
            "tool_calls": [],
            "iteration": 0,
            "should_continue": True,
            "final_answer": None,
            "error": None,
            "thoughts": []
        }
        
        # 添加用户消息
        initial_state["messages"].append({"role": "user", "content": user_input})
        
        # 运行图
        final_state = await self.app.ainvoke(initial_state)
        
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
        conversation_history: Optional[List[dict]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """运行 Agent（流式）"""
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "user_id": user_id,
            "token": token,
            "tool_calls": [],
            "iteration": 0,
            "should_continue": True,
            "final_answer": None,
            "error": None,
            "thoughts": []
        }
        
        # 添加用户消息
        initial_state["messages"].append({"role": "user", "content": user_input})
        
        # 流式运行
        last_thoughts_count = 0
        async for event in self.app.astream(initial_state):
            for node_name, node_output in event.items():
                # 发送思考过程（只发送新增的）
                thoughts = node_output.get("thoughts", [])
                if len(thoughts) > last_thoughts_count:
                    for thought in thoughts[last_thoughts_count:]:
                        yield StreamEvent(event="thinking", data=thought)
                    last_thoughts_count = len(thoughts)
                
                # 发送工具调用信息
                if node_output.get("tool_calls"):
                    for tc in node_output["tool_calls"]:
                        yield StreamEvent(
                            event="tool_call",
                            data={
                                "name": tc.name,
                                "arguments": tc.arguments
                            }
                        )
                
                # 发送工具执行结果（用于前端特殊渲染）
                messages = node_output.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "tool":
                        try:
                            tool_data = json.loads(msg.get("content", "{}"))
                            # 检测是否是论文搜索结果
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
                
                # 发送最终答案
                if node_output.get("final_answer"):
                    yield StreamEvent(
                        event="answer",
                        data=node_output["final_answer"]
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

