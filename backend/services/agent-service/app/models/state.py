"""
Agent State Definition for LangGraph
"""
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from pydantic import BaseModel
import operator


class Message(BaseModel):
    """Chat message"""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call record"""
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class AgentState(TypedDict):
    """
    Agent 状态定义
    
    使用 Annotated 来定义状态的更新方式：
    - messages: 累加模式，新消息添加到列表末尾
    - 其他字段：覆盖模式，新值替换旧值
    """
    # 对话历史（累加）
    messages: Annotated[List[dict], operator.add]
    
    # 当前用户输入
    user_input: str
    
    # 用户信息
    user_id: Optional[str]
    
    # 对话ID（用于记忆系统）
    conversation_id: Optional[str]
    
    # 认证 Token（用于调用其他服务）
    token: Optional[str]
    
    # 工具调用记录
    tool_calls: List[ToolCall]
    
    # 当前迭代次数
    iteration: int
    
    # 是否需要继续
    should_continue: bool
    
    # 最终回答
    final_answer: Optional[str]
    
    # 错误信息
    error: Optional[str]
    
    # 思考过程（用于流式输出）
    thoughts: List[str]


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    conversation_id: Optional[str] = None
    tool_calls: List[ToolCall] = []
    thoughts: List[str] = []


class StreamEvent(BaseModel):
    """流式事件"""
    event: str  # "thinking", "tool_call", "tool_result", "answer", "error", "done"
    data: Any

