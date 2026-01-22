"""
OpenAI服务 - 用于生成文本嵌入和AI回答
"""
import os
from typing import List, AsyncGenerator
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI服务类"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
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
        self.embedding_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        logger.info(f"Using chat model: {self.default_model}")
        logger.info(f"Using embedding model: {self.embedding_model}")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = None
    ) -> List[List[float]]:
        """
        生成文本嵌入向量
        
        Args:
            texts: 文本列表
            model: 嵌入模型（默认使用配置的模型）
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            response = await self.client.embeddings.create(
                model=model or self.embedding_model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def chat_completion_stream(
        self,
        messages: List[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        流式生成聊天回复
        
        Args:
            messages: 消息列表
            model: 使用的模型
            temperature: 温度
            max_tokens: 最大tokens
            
        Yields:
            str: 生成的文本片段
        """
        try:
            stream = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield f"\n\n[Error: {str(e)}]"
    
    async def generate_answer(
        self,
        question: str,
        context: str,
        chat_history: List[dict] = None,
        model: str = None
    ) -> str:
        """
        基于上下文生成答案
        
        Args:
            question: 用户问题
            context: 参考上下文
            chat_history: 聊天历史
            model: 使用的模型
            
        Returns:
            str: AI生成的答案
        """
        try:
            # 构建系统提示
            system_prompt = """你是一个专业的学术助手，帮助用户理解和分析研究论文。

基于提供的论文内容片段，请准确、详细地回答用户的问题。

注意事项：
1. 只基于提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，明确告知用户
3. 回答要专业、准确、有条理
4. 必要时可以引用原文
5. 使用中文回答"""

            # 构建用户提示
            user_prompt = f"""参考内容：
{context}

问题：{question}

请基于以上参考内容回答问题。"""

            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加聊天历史
            if chat_history:
                for msg in chat_history[-5:]:  # 只保留最近5轮对话
                    messages.append(msg)
            
            # 添加当前问题
            messages.append({"role": "user", "content": user_prompt})
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"抱歉，生成答案时出错：{str(e)}"


# 全局实例
_openai_service = None


def get_openai_service() -> OpenAIService:
    """获取OpenAI服务实例"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
