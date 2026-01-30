"""
熔断器模块
实现工具调用的熔断降级机制
"""
import time
import asyncio
import logging
from enum import Enum
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态，允许调用
    OPEN = "open"          # 熔断状态，拒绝调用
    HALF_OPEN = "half_open"  # 半开状态，尝试恢复


@dataclass
class CircuitStats:
    """熔断器统计信息"""
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    circuit_opened_at: Optional[float] = None
    

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    fail_threshold: int = 5          # 连续失败多少次后熔断
    reset_timeout: float = 30.0      # 熔断后多少秒尝试恢复
    half_open_max_calls: int = 3     # 半开状态最多允许多少次调用
    success_threshold: int = 2       # 半开状态成功多少次后关闭熔断器


class CircuitBreaker:
    """
    熔断器
    
    状态转换：
    CLOSED ---(连续失败N次)---> OPEN
    OPEN ---(等待reset_timeout)---> HALF_OPEN
    HALF_OPEN ---(成功)---> CLOSED
    HALF_OPEN ---(失败)---> OPEN
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_calls = 0
        self._half_open_successes = 0
        self._lock = asyncio.Lock()
    
    @property
    def is_open(self) -> bool:
        """熔断器是否开启（拒绝调用）"""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """熔断器是否关闭（允许调用）"""
        return self.state == CircuitState.CLOSED
    
    async def can_execute(self) -> bool:
        """
        检查是否可以执行调用
        
        Returns:
            bool: True 可以执行，False 应该降级
        """
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # 检查是否应该进入半开状态
                if self._should_try_reset():
                    self._transition_to_half_open()
                    return True
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态限制调用次数
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        
        return False
    
    def _should_try_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.stats.circuit_opened_at is None:
            return False
        elapsed = time.time() - self.stats.circuit_opened_at
        return elapsed >= self.config.reset_timeout
    
    def _transition_to_half_open(self):
        """转换到半开状态"""
        logger.info(f"[CircuitBreaker:{self.name}] OPEN -> HALF_OPEN (尝试恢复)")
        self.state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._half_open_successes = 0
    
    async def record_success(self):
        """记录成功调用"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.success_calls += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.config.success_threshold:
                    self._close_circuit()
    
    async def record_failure(self, error: str = None):
        """记录失败调用"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.failure_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，重新打开熔断器
                self._open_circuit()
            elif self.state == CircuitState.CLOSED:
                # 检查是否应该打开熔断器
                if self.stats.consecutive_failures >= self.config.fail_threshold:
                    self._open_circuit()
    
    def _open_circuit(self):
        """打开熔断器"""
        logger.warning(
            f"[CircuitBreaker:{self.name}] 熔断器开启! "
            f"连续失败 {self.stats.consecutive_failures} 次, "
            f"将在 {self.config.reset_timeout}s 后尝试恢复"
        )
        self.state = CircuitState.OPEN
        self.stats.circuit_opened_at = time.time()
    
    def _close_circuit(self):
        """关闭熔断器"""
        logger.info(f"[CircuitBreaker:{self.name}] 熔断器关闭，服务已恢复正常")
        self.state = CircuitState.CLOSED
        self.stats.consecutive_failures = 0
        self._half_open_calls = 0
        self._half_open_successes = 0
    
    def get_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "success_calls": self.stats.success_calls,
                "failure_calls": self.stats.failure_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "success_rate": (
                    self.stats.success_calls / self.stats.total_calls * 100
                    if self.stats.total_calls > 0 else 100
                )
            },
            "config": {
                "fail_threshold": self.config.fail_threshold,
                "reset_timeout": self.config.reset_timeout
            }
        }


class CircuitBreakerManager:
    """
    熔断器管理器
    管理所有工具的熔断器实例
    """
    
    # 默认熔断器配置
    DEFAULT_CONFIG = CircuitBreakerConfig(
        fail_threshold=5,
        reset_timeout=30.0,
        half_open_max_calls=3,
        success_threshold=2
    )
    
    # 工具特定配置
    TOOL_CONFIGS = {
        # 外部 API 依赖的工具，更敏感
        "search_literature": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        "get_work_detail": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        "get_related_works": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        # 内部服务工具
        "semantic_search": CircuitBreakerConfig(fail_threshold=5, reset_timeout=30.0),
        "ask_paper": CircuitBreakerConfig(fail_threshold=5, reset_timeout=30.0),
        "analyze_paper": CircuitBreakerConfig(fail_threshold=5, reset_timeout=45.0),
        "generate_mindmap": CircuitBreakerConfig(fail_threshold=5, reset_timeout=45.0),
    }
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        """获取工具的熔断器"""
        if tool_name not in self._breakers:
            config = self.TOOL_CONFIGS.get(tool_name, self.DEFAULT_CONFIG)
            self._breakers[tool_name] = CircuitBreaker(tool_name, config)
        return self._breakers[tool_name]
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有熔断器状态"""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }
    
    def get_degraded_tools(self) -> list:
        """获取当前被熔断的工具列表"""
        return [
            name for name, breaker in self._breakers.items()
            if breaker.is_open
        ]


# 全局熔断器管理器
_breaker_manager: Optional[CircuitBreakerManager] = None


def get_breaker_manager() -> CircuitBreakerManager:
    """获取全局熔断器管理器"""
    global _breaker_manager
    if _breaker_manager is None:
        _breaker_manager = CircuitBreakerManager()
    return _breaker_manager


def get_breaker(tool_name: str) -> CircuitBreaker:
    """便捷函数：获取工具的熔断器"""
    return get_breaker_manager().get_breaker(tool_name)


# ==================== 智能降级策略 ====================

# 工具替代关系：定义每个工具不可用时可以尝试的替代方案
TOOL_ALTERNATIVES = {
    "search_literature": {
        "alternatives": ["semantic_search", "list_papers"],
        "fallback_strategy": "search_local",  # 在本地论文库中搜索
        "description": "外部文献搜索服务（OpenAlex）",
        "hint": "可以尝试在用户已上传的论文库中进行语义搜索(semantic_search)，或列出用户的论文(list_papers)"
    },
    "get_work_detail": {
        "alternatives": ["semantic_search"],
        "fallback_strategy": "search_local",
        "description": "获取论文详细信息",
        "hint": "如果是用户上传的论文，可以使用semantic_search搜索相关内容"
    },
    "get_related_works": {
        "alternatives": ["search_literature", "semantic_search"],
        "fallback_strategy": "search_similar",
        "description": "获取相关论文",
        "hint": "可以使用search_literature搜索相似主题，或用semantic_search在本地库中查找"
    },
    "semantic_search": {
        "alternatives": ["list_papers"],
        "fallback_strategy": "list_and_filter",
        "description": "语义搜索服务",
        "hint": "可以先用list_papers列出所有论文，然后根据标题筛选"
    },
    "ask_paper": {
        "alternatives": ["semantic_search"],
        "fallback_strategy": "search_and_summarize",
        "description": "论文问答服务",
        "hint": "可以用semantic_search搜索相关内容，然后基于搜索结果回答问题"
    },
    "generate_mindmap": {
        "alternatives": ["analyze_paper"],
        "fallback_strategy": "analyze_instead",
        "description": "思维导图生成服务",
        "hint": "可以使用analyze_paper进行论文分析，提供文字总结代替思维导图"
    },
    "analyze_paper": {
        "alternatives": ["ask_paper", "semantic_search"],
        "fallback_strategy": "qa_instead",
        "description": "论文分析服务",
        "hint": "可以使用ask_paper针对具体问题进行问答，或用semantic_search获取相关内容"
    },
    "compare_papers": {
        "alternatives": ["analyze_paper", "ask_paper"],
        "fallback_strategy": "analyze_each",
        "description": "论文对比服务",
        "hint": "可以分别使用analyze_paper分析每篇论文，然后综合比较"
    },
    "list_papers": {
        "alternatives": [],
        "fallback_strategy": "direct_answer",
        "description": "论文列表服务",
        "hint": "可以直接回答，告知用户服务暂时不可用"
    },
    "upload_paper": {
        "alternatives": [],
        "fallback_strategy": "direct_answer",
        "description": "论文上传服务",
        "hint": "上传服务不可用时无替代方案，建议用户稍后重试"
    }
}

# 智能降级响应模板
SMART_DEGRADED_RESPONSE = """[工具降级通知]
工具 "{tool_name}" ({description}) 当前不可用。

**替代方案建议：**
{alternatives_hint}

**你应该：**
1. 首先尝试使用替代工具完成用户的需求
2. 如果替代工具也不适用，尝试基于你已有的知识回答
3. 只有在完全无法帮助时，才告知用户服务暂时不可用

**注意：不要直接告诉用户"请稍后重试"，要先尝试其他方法帮助用户。**
"""


def get_degraded_response(tool_name: str, breaker: CircuitBreaker) -> str:
    """
    生成智能降级响应消息
    
    这个消息是给 LLM 看的，引导它进行智能降级决策
    """
    tool_info = TOOL_ALTERNATIVES.get(tool_name, {
        "alternatives": [],
        "description": tool_name,
        "hint": "可以尝试基于你的知识直接回答用户问题"
    })
    
    alternatives = tool_info.get("alternatives", [])
    hint = tool_info.get("hint", "")
    description = tool_info.get("description", tool_name)
    
    # 构建替代方案建议
    if alternatives:
        alt_list = ", ".join(alternatives)
        alternatives_hint = f"- 可用的替代工具: {alt_list}\n- {hint}"
    else:
        alternatives_hint = f"- 没有直接替代工具\n- {hint}"
    
    return SMART_DEGRADED_RESPONSE.format(
        tool_name=tool_name,
        description=description,
        alternatives_hint=alternatives_hint
    )


def get_tool_alternatives(tool_name: str) -> dict:
    """获取工具的替代方案信息"""
    return TOOL_ALTERNATIVES.get(tool_name, {
        "alternatives": [],
        "fallback_strategy": "direct_answer",
        "description": tool_name,
        "hint": "尝试直接回答"
    })

