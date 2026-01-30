"""
Conversation Cache - Redis 对话历史缓存

优化对话历史的读写：
- 热数据存储在 Redis，快速读取
- 异步写入 conversation-service（持久化）
- 自动同步和缓存失效
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis
import httpx

from ..config import REDIS_URL, CONVERSATION_SERVICE_URL

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    writes: int = 0


class ConversationCache:
    """
    对话历史缓存管理器
    
    设计原则：
    1. 读取优先从 Redis 缓存
    2. 缓存未命中时从 conversation-service 加载
    3. 写入时先更新缓存，再异步写入 conversation-service
    
    缓存结构：
    - conv_history:{conversation_id} -> JSON 消息列表
    - conv_meta:{conversation_id} -> 元数据（标题、创建时间等）
    """
    
    def __init__(
        self,
        redis_url: str = REDIS_URL,
        service_url: str = CONVERSATION_SERVICE_URL,
        cache_ttl: int = 3600 * 6  # 6小时缓存
    ):
        self.redis_url = redis_url
        self.service_url = service_url
        self.cache_ttl = cache_ttl
        self._client: Optional[redis.Redis] = None
        self.stats = CacheStats()
        
        # 后台写入队列
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task] = None
    
    async def _get_client(self) -> redis.Redis:
        """获取 Redis 客户端"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _history_key(self, conversation_id: Union[str, int]) -> str:
        return f"conv_history:{conversation_id}"
    
    def _meta_key(self, conversation_id: Union[str, int]) -> str:
        return f"conv_meta:{conversation_id}"
    
    async def start_background_writer(self):
        """启动后台写入任务"""
        if self._writer_task is None or self._writer_task.done():
            self._writer_task = asyncio.create_task(self._background_writer())
            logger.info("Started background conversation writer")
    
    async def _background_writer(self):
        """后台写入任务 - 异步写入 conversation-service"""
        while True:
            try:
                # 等待写入任务
                task = await self._write_queue.get()
                
                if task is None:  # 停止信号
                    break
                
                action = task.get("action")
                
                if action == "save_message":
                    await self._do_save_message(
                        task["conversation_id"],
                        task["role"],
                        task["content"],
                        task["token"]
                    )
                elif action == "create_conversation":
                    # 创建对话的结果已经同步返回了，这里只是确认
                    pass
                
                self._write_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background writer error: {e}")
    
    async def _do_save_message(
        self,
        conversation_id: Union[str, int],
        role: str,
        content: str,
        token: str
    ):
        """实际执行保存消息到 conversation-service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.service_url}/api/conversations/{conversation_id}/messages",
                    json={"role": role, "content": content},
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 201:
                    logger.debug(f"Persisted {role} message to conversation {conversation_id}")
                    self.stats.writes += 1
                else:
                    logger.warning(f"Failed to persist message: {response.status_code}")
        except Exception as e:
            logger.error(f"Error persisting message: {e}")
    
    async def load_history(
        self,
        conversation_id: Union[str, int],
        token: str
    ) -> List[Dict[str, Any]]:
        """
        加载对话历史（缓存优先）
        
        流程：
        1. 检查 Redis 缓存
        2. 缓存命中 → 直接返回
        3. 缓存未命中 → 从 conversation-service 加载 → 写入缓存
        """
        client = await self._get_client()
        cache_key = self._history_key(conversation_id)
        
        # 1. 尝试从缓存读取
        cached = await client.get(cache_key)
        if cached:
            self.stats.hits += 1
            logger.debug(f"Cache HIT for conversation {conversation_id}")
            return json.loads(cached)
        
        # 2. 缓存未命中，从 conversation-service 加载
        self.stats.misses += 1
        logger.debug(f"Cache MISS for conversation {conversation_id}, loading from service")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(
                    f"{self.service_url}/api/conversations/{conversation_id}/messages",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    # 转换格式
                    history = []
                    for msg in messages:
                        history.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
                    
                    # 3. 写入缓存
                    await client.setex(cache_key, self.cache_ttl, json.dumps(history))
                    logger.info(f"Loaded and cached {len(history)} messages for conversation {conversation_id}")
                    
                    return history
                elif response.status_code == 404:
                    logger.warning(f"Conversation {conversation_id} not found")
                    return []
                else:
                    logger.error(f"Failed to load history: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return []
    
    async def append_message(
        self,
        conversation_id: Union[str, int],
        role: str,
        content: str,
        token: str
    ):
        """
        追加消息（先更新缓存，再异步持久化）
        
        这是核心优化：
        - 缓存更新是同步的（快）
        - 持久化是异步的（不阻塞响应）
        """
        client = await self._get_client()
        cache_key = self._history_key(conversation_id)
        
        # 1. 更新缓存（同步）
        cached = await client.get(cache_key)
        if cached:
            history = json.loads(cached)
        else:
            history = []
        
        history.append({"role": role, "content": content})
        await client.setex(cache_key, self.cache_ttl, json.dumps(history))
        
        logger.debug(f"Appended {role} message to cache for conversation {conversation_id}")
        
        # 2. 异步持久化到 conversation-service
        await self._write_queue.put({
            "action": "save_message",
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "token": token
        })
    
    async def create_conversation(
        self,
        token: str,
        title: str = "新对话"
    ) -> Optional[int]:
        """
        创建新对话
        
        这个操作需要同步，因为需要返回 conversation_id
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.service_url}/api/conversations",
                    json={"title": title},
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 201:
                    data = response.json()
                    conversation_id = data.get("id")
                    
                    # 初始化空缓存
                    redis_client = await self._get_client()
                    cache_key = self._history_key(conversation_id)
                    await redis_client.setex(cache_key, self.cache_ttl, "[]")
                    
                    logger.info(f"Created new conversation: {conversation_id}")
                    return conversation_id
                else:
                    logger.error(f"Failed to create conversation: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    async def invalidate_cache(self, conversation_id: Union[str, int]):
        """使缓存失效"""
        client = await self._get_client()
        await client.delete(
            self._history_key(conversation_id),
            self._meta_key(conversation_id)
        )
        logger.debug(f"Invalidated cache for conversation {conversation_id}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.stats.hits + self.stats.misses
        hit_rate = (self.stats.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "writes": self.stats.writes,
            "hit_rate": f"{hit_rate:.1f}%",
            "queue_size": self._write_queue.qsize()
        }
    
    async def close(self):
        """关闭连接和后台任务"""
        # 停止后台写入
        if self._writer_task and not self._writer_task.done():
            await self._write_queue.put(None)  # 发送停止信号
            await self._writer_task
        
        # 关闭 Redis 连接
        if self._client:
            await self._client.close()
            self._client = None


# 全局实例
_conversation_cache: Optional[ConversationCache] = None


def get_conversation_cache() -> ConversationCache:
    """获取对话缓存单例"""
    global _conversation_cache
    if _conversation_cache is None:
        _conversation_cache = ConversationCache()
        logger.info("Initialized ConversationCache")
    return _conversation_cache


async def init_conversation_cache():
    """初始化对话缓存（启动后台写入）"""
    cache = get_conversation_cache()
    await cache.start_background_writer()
    return cache

