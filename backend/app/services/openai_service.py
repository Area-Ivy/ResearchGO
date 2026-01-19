import os
from typing import List, AsyncGenerator
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
        
        # Initialize OpenAI client with minimal parameters
        try:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=60.0,
                max_retries=2
            )
            logger.info("✓ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
        
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        logger.info(f"Using model: {self.default_model}")
    
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from OpenAI API
        
        Args:
            messages: List of chat messages
            model: OpenAI model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            
        Yields:
            str: Chunks of the response text
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Stream the response
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Get complete chat response from OpenAI API
        
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
            return f"[Error: {str(e)}]"

