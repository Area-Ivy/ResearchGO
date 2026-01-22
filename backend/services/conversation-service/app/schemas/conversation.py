"""
对话相关的Pydantic模型（Schema）
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """创建消息模型"""
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """创建对话会话模型"""
    title: str = Field(..., min_length=1, max_length=255, description="对话标题")


class ConversationUpdate(BaseModel):
    """更新对话会话模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="对话标题")


class ConversationResponse(BaseModel):
    """对话会话响应模型"""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """对话会话详情响应模型（包含消息）"""
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话会话列表响应模型"""
    total: int
    conversations: List[ConversationResponse]

