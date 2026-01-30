"""
Memory System for ResearchGO Agent

包含三层记忆架构：
1. 短期记忆 (Short-term): Redis Checkpointer + 滑动窗口
2. 长期对话 (Long-term Conversation): 对话摘要
3. 语义记忆 (Semantic Memory): 基于向量的跨会话记忆

使用方式：
```python
from app.memory import (
    get_checkpointer,          # Redis Checkpointer
    SmartSlidingWindow,        # 智能滑动窗口
    get_summary_manager,       # 对话摘要管理器
    get_semantic_memory_service # 语义记忆服务
)
```
"""

from .checkpointer import get_checkpointer, RedisCheckpointer
from .sliding_window import (
    SlidingWindowManager,
    TokenAwareSlidingWindow,
    SmartSlidingWindow,
    WindowStats
)
from .summary import ConversationSummaryManager, get_summary_manager, SummaryResult
from .semantic_memory import (
    SemanticMemoryService,
    get_semantic_memory_service,
    Memory,
    MemoryType
)
from .conversation_cache import (
    ConversationCache,
    get_conversation_cache,
    init_conversation_cache,
    CacheStats
)

__all__ = [
    # Checkpointer
    "get_checkpointer",
    "RedisCheckpointer",
    # Sliding Window
    "SlidingWindowManager",
    "TokenAwareSlidingWindow",
    "SmartSlidingWindow",
    "WindowStats",
    # Summary
    "ConversationSummaryManager",
    "get_summary_manager",
    "SummaryResult",
    # Semantic Memory
    "SemanticMemoryService",
    "get_semantic_memory_service",
    "Memory",
    "MemoryType",
    # Conversation Cache
    "ConversationCache",
    "get_conversation_cache",
    "init_conversation_cache",
    "CacheStats",
]

