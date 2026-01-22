"""
OpenAI Service for Mindmap Generation
"""
import os
from typing import List
from openai import AsyncOpenAI
from app.models.chat import ChatMessage
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Get optional base URL for custom endpoints
        base_url = os.getenv('OPENAI_BASE_URL')
        
        # Initialize OpenAI client
        try:
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": 120.0,
                "max_retries": 2
            }
            if base_url:
                client_kwargs["base_url"] = base_url
            
            self.client = AsyncOpenAI(**client_kwargs)
            logger.info("✓ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
        
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        logger.info(f"Using model: {self.default_model}")
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Get chat completion from OpenAI API
        
        Args:
            messages: List of chat messages
            model: OpenAI model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            
        Returns:
            str: Complete response text
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Create completion
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return f"[Error: {str(e)}]"


# 单例服务实例
_openai_service = None

def get_openai_service() -> OpenAIService:
    """获取 OpenAI 服务实例"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service

