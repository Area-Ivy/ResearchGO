"""
Chat Message Model
用于 OpenAI API 调用
"""
from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal['user', 'assistant', 'system']
    content: str

