"""
OpenAI Service for Literature Search
Handles AI-powered summarization
"""
import os
import logging
from typing import List, Dict
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, AI features will be disabled")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url if base_url else None
            )
        
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        logger.info(f"OpenAI service initialized with model: {self.default_model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override
            temperature: Creativity parameter (0-2)
            max_tokens: Maximum response tokens
            
        Returns:
            Generated text response
        """
        if not self.client:
            raise Exception("OpenAI service not configured")
        
        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")


# 单例服务实例
_openai_service = None

def get_openai_service() -> OpenAIService:
    """获取 OpenAI 服务实例"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service

