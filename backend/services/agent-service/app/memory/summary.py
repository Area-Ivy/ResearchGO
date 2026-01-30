"""
Conversation Summary Manager

长对话摘要管理器：
- 当对话超过阈值时，自动生成摘要
- 摘要缓存在 Redis 中
- 支持增量摘要更新
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import (
    REDIS_URL,
    ENABLE_CONVERSATION_SUMMARY,
    SUMMARY_THRESHOLD,
    SUMMARY_MAX_TOKENS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL
)

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """摘要结果"""
    summary: str
    original_count: int
    summarized_count: int
    window_messages: List[Dict[str, Any]]
    from_cache: bool


class ConversationSummaryManager:
    """
    对话摘要管理器
    
    功能：
    1. 自动检测长对话
    2. 生成对话摘要
    3. 缓存摘要到 Redis
    4. 支持增量更新
    
    存储结构：
    - summary:{conversation_id} -> 摘要内容
    - summary_meta:{conversation_id} -> 元数据（最后更新时间、消息数等）
    """
    
    def __init__(
        self,
        threshold: int = SUMMARY_THRESHOLD,
        max_tokens: int = SUMMARY_MAX_TOKENS,
        redis_url: str = REDIS_URL
    ):
        self.threshold = threshold
        self.max_tokens = max_tokens
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        
        # 初始化 LLM
        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.3,  # 低温度保证摘要一致性
            "api_key": OPENAI_API_KEY,
            "max_tokens": max_tokens
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.llm = ChatOpenAI(**llm_kwargs)
    
    async def _get_client(self) -> redis.Redis:
        """获取 Redis 客户端"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _summary_key(self, conversation_id: str) -> str:
        return f"summary:{conversation_id}"
    
    def _meta_key(self, conversation_id: str) -> str:
        return f"summary_meta:{conversation_id}"
    
    async def _get_cached_summary(self, conversation_id: str) -> Optional[Tuple[str, int]]:
        """获取缓存的摘要"""
        client = await self._get_client()
        summary = await client.get(self._summary_key(conversation_id))
        meta_str = await client.get(self._meta_key(conversation_id))
        
        if summary and meta_str:
            meta = json.loads(meta_str)
            return summary, meta.get("message_count", 0)
        
        return None
    
    async def _cache_summary(
        self,
        conversation_id: str,
        summary: str,
        message_count: int
    ):
        """缓存摘要"""
        client = await self._get_client()
        meta = {
            "message_count": message_count,
            "updated_at": datetime.now().isoformat()
        }
        
        pipe = client.pipeline()
        pipe.set(self._summary_key(conversation_id), summary)
        pipe.set(self._meta_key(conversation_id), json.dumps(meta))
        await pipe.execute()
        
        logger.debug(f"Cached summary for conversation {conversation_id}")
    
    async def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """使用 LLM 生成对话摘要"""
        # 构建对话文本
        conversation_text = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:500]  # 截断长内容
            
            if role == "user":
                conversation_text.append(f"用户: {content}")
            elif role == "assistant":
                conversation_text.append(f"助手: {content}")
            elif role == "tool":
                # 简化工具结果
                conversation_text.append(f"[工具调用结果]")
        
        conversation_str = "\n".join(conversation_text)
        
        prompt = f"""请用简洁的中文总结以下对话的关键信息，包括：
1. 用户的主要需求和问题
2. 助手提供的关键信息和建议
3. 讨论的主要论文或研究主题（如有）

对话内容：
{conversation_str}

摘要（不超过3句话）："""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="你是一个专业的对话摘要助手，善于提取关键信息。"),
            HumanMessage(content=prompt)
        ])
        
        return response.content.strip()
    
    async def process(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
        window_size: int = 10
    ) -> SummaryResult:
        """
        处理对话历史
        
        如果对话超过阈值：
        1. 检查是否有缓存的摘要
        2. 如果有新消息，增量更新摘要
        3. 返回摘要 + 最近的窗口消息
        
        Args:
            messages: 完整对话历史
            conversation_id: 对话ID
            window_size: 保留的最近消息数量
            
        Returns:
            SummaryResult 包含摘要和窗口消息
        """
        if not ENABLE_CONVERSATION_SUMMARY:
            return SummaryResult(
                summary="",
                original_count=len(messages),
                summarized_count=0,
                window_messages=messages,
                from_cache=False
            )
        
        original_count = len(messages)
        
        # 如果消息数量在阈值内，不需要摘要
        if original_count <= self.threshold:
            return SummaryResult(
                summary="",
                original_count=original_count,
                summarized_count=0,
                window_messages=messages,
                from_cache=False
            )
        
        # 分割：需要摘要的部分 | 保留的窗口
        cutoff = original_count - (window_size * 2)
        to_summarize = messages[:cutoff]
        window_messages = messages[cutoff:]
        
        # 检查缓存
        cached = await self._get_cached_summary(conversation_id)
        
        if cached:
            cached_summary, cached_count = cached
            
            # 检查是否需要更新摘要（有新的待摘要消息）
            if cutoff <= cached_count:
                # 缓存仍有效
                logger.info(f"Using cached summary for conversation {conversation_id}")
                return SummaryResult(
                    summary=cached_summary,
                    original_count=original_count,
                    summarized_count=cutoff,
                    window_messages=window_messages,
                    from_cache=True
                )
            else:
                # 需要增量更新：合并旧摘要和新消息
                new_messages = messages[cached_count:cutoff]
                combined_text = f"之前的摘要：{cached_summary}\n\n新增对话需要合并到摘要中。"
                
                # 将旧摘要作为第一条消息
                augmented_messages = [
                    {"role": "system", "content": combined_text}
                ] + new_messages
                
                summary = await self._generate_summary(augmented_messages)
                await self._cache_summary(conversation_id, summary, cutoff)
                
                logger.info(f"Updated summary for conversation {conversation_id}: +{len(new_messages)} messages")
                
                return SummaryResult(
                    summary=summary,
                    original_count=original_count,
                    summarized_count=cutoff,
                    window_messages=window_messages,
                    from_cache=False
                )
        
        # 首次生成摘要
        summary = await self._generate_summary(to_summarize)
        await self._cache_summary(conversation_id, summary, cutoff)
        
        logger.info(f"Generated new summary for conversation {conversation_id}: {cutoff} messages summarized")
        
        return SummaryResult(
            summary=summary,
            original_count=original_count,
            summarized_count=cutoff,
            window_messages=window_messages,
            from_cache=False
        )
    
    async def clear_summary(self, conversation_id: str):
        """清除对话摘要缓存"""
        client = await self._get_client()
        await client.delete(
            self._summary_key(conversation_id),
            self._meta_key(conversation_id)
        )
        logger.info(f"Cleared summary for conversation {conversation_id}")
    
    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None


# 全局实例
_summary_manager: Optional[ConversationSummaryManager] = None


def get_summary_manager() -> ConversationSummaryManager:
    """获取摘要管理器单例"""
    global _summary_manager
    if _summary_manager is None:
        _summary_manager = ConversationSummaryManager()
        logger.info("Initialized ConversationSummaryManager")
    return _summary_manager

