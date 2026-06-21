"""
Memory system for ResearchGO Agent.

Layers:
1. Short-term memory: Redis checkpointer + sliding window.
2. Long-term conversation: conversation summaries.
3. Semantic memory: editable per-user Markdown files.
"""

from .checkpointer import get_checkpointer, RedisCheckpointer
from .sliding_window import (
    SlidingWindowManager,
    TokenAwareSlidingWindow,
    SmartSlidingWindow,
    WindowStats,
)
from .summary import ConversationSummaryManager, get_summary_manager, SummaryResult
from .semantic_memory import (
    SemanticMemoryService,
    get_semantic_memory_service,
    Memory,
    MemoryType,
)
from .conversation_cache import (
    ConversationCache,
    get_conversation_cache,
    init_conversation_cache,
    CacheStats,
)

__all__ = [
    "get_checkpointer",
    "RedisCheckpointer",
    "SlidingWindowManager",
    "TokenAwareSlidingWindow",
    "SmartSlidingWindow",
    "WindowStats",
    "ConversationSummaryManager",
    "get_summary_manager",
    "SummaryResult",
    "SemanticMemoryService",
    "get_semantic_memory_service",
    "Memory",
    "MemoryType",
    "ConversationCache",
    "get_conversation_cache",
    "init_conversation_cache",
    "CacheStats",
]
