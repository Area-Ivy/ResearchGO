"""
Redis Checkpointer for LangGraph

基于 Redis 的检查点存储，支持：
- 自动保存/恢复 Agent 状态
- TTL 过期清理
- 跨进程状态共享
"""

import json
import logging
from typing import Optional, Dict, Any, Iterator, Sequence, Tuple
from datetime import datetime
import uuid

import redis.asyncio as redis
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)

from ..config import REDIS_URL, CHECKPOINT_TTL, ENABLE_CHECKPOINTER

logger = logging.getLogger(__name__)


class RedisCheckpointer(BaseCheckpointSaver):
    """
    基于 Redis 的 LangGraph Checkpointer
    
    实现 LangGraph 新版接口：
    - aget_tuple / get_tuple
    - aput / put
    - alist / list
    
    存储结构:
    - checkpoint:{thread_id}:{checkpoint_id} -> checkpoint 数据
    - checkpoint_meta:{thread_id}:{checkpoint_id} -> 元数据
    - checkpoint_latest:{thread_id} -> 最新 checkpoint_id
    """
    
    def __init__(self, redis_url: str = REDIS_URL, ttl: int = CHECKPOINT_TTL):
        super().__init__()
        self.redis_url = redis_url
        self.ttl = ttl
        self._client: Optional[redis.Redis] = None
        self._sync_client = None
    
    async def _get_client(self) -> redis.Redis:
        """获取异步 Redis 客户端"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _get_sync_client(self):
        """获取同步 Redis 客户端"""
        if self._sync_client is None:
            import redis as sync_redis
            self._sync_client = sync_redis.from_url(self.redis_url, decode_responses=True)
        return self._sync_client
    
    def _checkpoint_key(self, thread_id: str, checkpoint_id: str) -> str:
        return f"checkpoint:{thread_id}:{checkpoint_id}"
    
    def _meta_key(self, thread_id: str, checkpoint_id: str) -> str:
        return f"checkpoint_meta:{thread_id}:{checkpoint_id}"
    
    def _latest_key(self, thread_id: str) -> str:
        return f"checkpoint_latest:{thread_id}"
    
    def _serialize(self, data: Any) -> str:
        """序列化数据"""
        try:
            if hasattr(data, '_asdict'):
                data = data._asdict()
            elif hasattr(data, '__dict__') and not isinstance(data, dict):
                data = dict(data)
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Serialize error: {e}")
            return "{}"
    
    def _deserialize(self, data: str) -> Any:
        """反序列化数据"""
        try:
            return json.loads(data) if data else None
        except json.JSONDecodeError as e:
            logger.warning(f"Deserialize error: {e}")
            return None
    
    # ==================== 异步方法 (LangGraph 新版接口) ====================
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """异步获取 checkpoint tuple"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        
        if not thread_id:
            return None
        
        try:
            client = await self._get_client()
            
            # 如果没有指定 checkpoint_id，获取最新的
            if not checkpoint_id:
                checkpoint_id = await client.get(self._latest_key(thread_id))
                if not checkpoint_id:
                    return None
            
            # 获取 checkpoint 数据
            checkpoint_data = await client.get(self._checkpoint_key(thread_id, checkpoint_id))
            if not checkpoint_data:
                return None
            
            # 获取元数据
            meta_data = await client.get(self._meta_key(thread_id, checkpoint_id))
            
            checkpoint = self._deserialize(checkpoint_data)
            metadata = self._deserialize(meta_data) if meta_data else {}
            
            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": "",
                        "checkpoint_id": checkpoint_id,
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=None,
            )
        except Exception as e:
            logger.error(f"aget_tuple error: {e}")
            return None
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> Dict[str, Any]:
        """异步保存 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id is required in config")
        
        # 生成 checkpoint_id
        checkpoint_id = str(uuid.uuid4())
        
        try:
            client = await self._get_client()
            
            # 序列化并保存
            checkpoint_data = self._serialize(checkpoint)
            meta_data = self._serialize(metadata) if metadata else "{}"
            
            # 使用 pipeline 批量操作
            pipe = client.pipeline()
            pipe.setex(self._checkpoint_key(thread_id, checkpoint_id), self.ttl, checkpoint_data)
            pipe.setex(self._meta_key(thread_id, checkpoint_id), self.ttl, meta_data)
            pipe.setex(self._latest_key(thread_id), self.ttl, checkpoint_id)
            await pipe.execute()
            
            logger.debug(f"Saved checkpoint: thread={thread_id}, id={checkpoint_id}")
            
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": "",
                    "checkpoint_id": checkpoint_id,
                }
            }
        except Exception as e:
            logger.error(f"aput error: {e}")
            raise
    
    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """异步保存 pending writes（LangGraph 新版接口）"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        
        if not thread_id or not checkpoint_id:
            return
        
        try:
            client = await self._get_client()
            
            # 将 writes 存储为 JSON
            writes_key = f"checkpoint_writes:{thread_id}:{checkpoint_id}:{task_id}"
            writes_data = self._serialize(list(writes))
            
            await client.setex(writes_key, self.ttl, writes_data)
            logger.debug(f"Saved writes: thread={thread_id}, task={task_id}")
        except Exception as e:
            logger.error(f"aput_writes error: {e}")
    
    async def alist(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """列出所有 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id") if config else None
        if not thread_id:
            return
        
        try:
            client = await self._get_client()
            
            pattern = f"checkpoint:{thread_id}:*"
            count = 0
            async for key in client.scan_iter(match=pattern):
                if limit and count >= limit:
                    break
                    
                checkpoint_id = key.split(":")[-1]
                checkpoint_data = await client.get(key)
                if checkpoint_data:
                    checkpoint = self._deserialize(checkpoint_data)
                    yield CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": "",
                                "checkpoint_id": checkpoint_id,
                            }
                        },
                        checkpoint=checkpoint,
                        metadata={},
                        parent_config=None,
                    )
                    count += 1
        except Exception as e:
            logger.error(f"alist error: {e}")
    
    # ==================== 同步方法 ====================
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """同步获取 checkpoint tuple"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        
        if not thread_id:
            return None
        
        try:
            client = self._get_sync_client()
            
            if not checkpoint_id:
                checkpoint_id = client.get(self._latest_key(thread_id))
                if not checkpoint_id:
                    return None
            
            checkpoint_data = client.get(self._checkpoint_key(thread_id, checkpoint_id))
            if not checkpoint_data:
                return None
            
            meta_data = client.get(self._meta_key(thread_id, checkpoint_id))
            
            checkpoint = self._deserialize(checkpoint_data)
            metadata = self._deserialize(meta_data) if meta_data else {}
            
            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": "",
                        "checkpoint_id": checkpoint_id,
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=None,
            )
        except Exception as e:
            logger.error(f"get_tuple error: {e}")
            return None
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> Dict[str, Any]:
        """同步保存 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id is required")
        
        checkpoint_id = str(uuid.uuid4())
        
        try:
            client = self._get_sync_client()
            
            checkpoint_data = self._serialize(checkpoint)
            meta_data = self._serialize(metadata) if metadata else "{}"
            
            pipe = client.pipeline()
            pipe.setex(self._checkpoint_key(thread_id, checkpoint_id), self.ttl, checkpoint_data)
            pipe.setex(self._meta_key(thread_id, checkpoint_id), self.ttl, meta_data)
            pipe.setex(self._latest_key(thread_id), self.ttl, checkpoint_id)
            pipe.execute()
            
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": "",
                    "checkpoint_id": checkpoint_id,
                }
            }
        except Exception as e:
            logger.error(f"put error: {e}")
            raise
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """同步保存 pending writes"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        
        if not thread_id or not checkpoint_id:
            return
        
        try:
            client = self._get_sync_client()
            
            writes_key = f"checkpoint_writes:{thread_id}:{checkpoint_id}:{task_id}"
            writes_data = self._serialize(list(writes))
            
            client.setex(writes_key, self.ttl, writes_data)
        except Exception as e:
            logger.error(f"put_writes error: {e}")
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """同步列出 checkpoints"""
        thread_id = config.get("configurable", {}).get("thread_id") if config else None
        if not thread_id:
            return
        
        try:
            client = self._get_sync_client()
            
            count = 0
            for key in client.scan_iter(match=f"checkpoint:{thread_id}:*"):
                if limit and count >= limit:
                    break
                    
                checkpoint_id = key.split(":")[-1]
                checkpoint_data = client.get(key)
                if checkpoint_data:
                    yield CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": "",
                                "checkpoint_id": checkpoint_id,
                            }
                        },
                        checkpoint=self._deserialize(checkpoint_data),
                        metadata={},
                        parent_config=None,
                    )
                    count += 1
        except Exception as e:
            logger.error(f"list error: {e}")
    
    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None


# 全局实例
_checkpointer_instance: Optional[RedisCheckpointer] = None


def get_checkpointer() -> Optional[RedisCheckpointer]:
    """获取 Checkpointer 单例"""
    global _checkpointer_instance
    
    if not ENABLE_CHECKPOINTER:
        logger.info("Checkpointer is disabled")
        return None
    
    if _checkpointer_instance is None:
        _checkpointer_instance = RedisCheckpointer()
        logger.info(f"Initialized Redis Checkpointer: {REDIS_URL}")
    
    return _checkpointer_instance
