from pydantic import BaseModel
from typing import List, Optional, Literal


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal['user', 'assistant', 'system']
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    stream: bool = True
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    role: str = 'assistant'
    finish_reason: Optional[str] = None

