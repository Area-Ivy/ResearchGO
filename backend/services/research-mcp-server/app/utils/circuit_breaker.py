"""
Circuit breaker support for MCP-backed tools.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    circuit_opened_at: Optional[float] = None


@dataclass
class CircuitBreakerConfig:
    fail_threshold: int = 5
    reset_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_calls = 0
        self._half_open_successes = 0
        self._lock = asyncio.Lock()

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    async def can_execute(self) -> bool:
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self._should_try_reset():
                    self._transition_to_half_open()
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        return False

    def _should_try_reset(self) -> bool:
        if self.stats.circuit_opened_at is None:
            return False
        return (time.time() - self.stats.circuit_opened_at) >= self.config.reset_timeout

    def _transition_to_half_open(self):
        logger.info("[CircuitBreaker:%s] OPEN -> HALF_OPEN", self.name)
        self.state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._half_open_successes = 0

    async def record_success(self):
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.success_calls += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.config.success_threshold:
                    self._close_circuit()

    async def record_failure(self, error: Optional[str] = None):
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.failure_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self._open_circuit()
            elif self.state == CircuitState.CLOSED and self.stats.consecutive_failures >= self.config.fail_threshold:
                self._open_circuit()
        if error:
            logger.warning("[CircuitBreaker:%s] recorded failure: %s", self.name, error)

    def _open_circuit(self):
        logger.warning(
            "[CircuitBreaker:%s] opening circuit after %s consecutive failures",
            self.name,
            self.stats.consecutive_failures,
        )
        self.state = CircuitState.OPEN
        self.stats.circuit_opened_at = time.time()

    def _close_circuit(self):
        logger.info("[CircuitBreaker:%s] closing circuit", self.name)
        self.state = CircuitState.CLOSED
        self.stats.consecutive_failures = 0
        self._half_open_calls = 0
        self._half_open_successes = 0

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "success_calls": self.stats.success_calls,
                "failure_calls": self.stats.failure_calls,
                "consecutive_failures": self.stats.consecutive_failures,
            },
            "config": {
                "fail_threshold": self.config.fail_threshold,
                "reset_timeout": self.config.reset_timeout,
            },
        }


TOOL_ALTERNATIVES = {
    "search_literature": {
        "alternatives": ["semantic_search", "search_user_papers"],
        "description": "Search literature from OpenAlex.",
        "hint": "Try semantic_search on uploaded papers or search_user_papers if the user already imported papers.",
    },
    "get_work_detail": {
        "alternatives": ["search_literature"],
        "description": "Get work metadata by OpenAlex work id.",
        "hint": "Search the paper again and answer from the search hit if direct detail lookup is unavailable.",
    },
    "get_related_works": {
        "alternatives": ["search_literature", "semantic_search"],
        "description": "Get references or citing papers.",
        "hint": "Search by title/keywords or pivot to semantic_search for local evidence.",
    },
    "semantic_search": {
        "alternatives": ["search_user_papers"],
        "description": "Semantic retrieval over uploaded papers.",
        "hint": "List or search uploaded papers first, then narrow to a specific paper.",
    },
    "ask_about_paper": {
        "alternatives": ["semantic_search"],
        "description": "RAG QA on a single paper.",
        "hint": "Fallback to semantic_search and summarize the retrieved chunks.",
    },
    "analyze_paper": {
        "alternatives": ["ask_about_paper", "semantic_search"],
        "description": "Structured analysis for a paper.",
        "hint": "Fallback to ask_about_paper or semantic_search and answer manually.",
    },
    "generate_mindmap": {
        "alternatives": ["analyze_paper"],
        "description": "Mindmap generation for a paper.",
        "hint": "Fallback to analyze_paper and present a bullet hierarchy.",
    },
    "compare_papers": {
        "alternatives": ["analyze_paper", "ask_about_paper"],
        "description": "Compare multiple papers.",
        "hint": "Analyze the papers separately and compare manually.",
    },
}


def get_degraded_response(tool_name: str, breaker: CircuitBreaker) -> Dict[str, Any]:
    info = TOOL_ALTERNATIVES.get(tool_name, {})
    return {
        "status": "degraded",
        "tool": tool_name,
        "error": f"Circuit breaker open for {tool_name}. Retry after approximately {int(breaker.config.reset_timeout)}s.",
        "alternatives": info.get("alternatives", []),
        "hint": info.get("hint", ""),
        "description": info.get("description", tool_name),
    }


class CircuitBreakerManager:
    DEFAULT_CONFIG = CircuitBreakerConfig()
    TOOL_CONFIGS = {
        "search_literature": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        "get_work_detail": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        "get_related_works": CircuitBreakerConfig(fail_threshold=3, reset_timeout=60.0),
        "semantic_search": CircuitBreakerConfig(fail_threshold=5, reset_timeout=30.0),
        "ask_about_paper": CircuitBreakerConfig(fail_threshold=5, reset_timeout=30.0),
        "analyze_paper": CircuitBreakerConfig(fail_threshold=5, reset_timeout=45.0),
        "generate_mindmap": CircuitBreakerConfig(fail_threshold=5, reset_timeout=45.0),
        "compare_papers": CircuitBreakerConfig(fail_threshold=5, reset_timeout=45.0),
    }

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        if tool_name not in self._breakers:
            self._breakers[tool_name] = CircuitBreaker(
                tool_name,
                self.TOOL_CONFIGS.get(tool_name, self.DEFAULT_CONFIG),
            )
        return self._breakers[tool_name]

    def get_all_status(self) -> Dict[str, Any]:
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    def get_degraded_tools(self) -> list[str]:
        return [name for name, breaker in self._breakers.items() if breaker.is_open]


_breaker_manager: Optional[CircuitBreakerManager] = None


def get_breaker_manager() -> CircuitBreakerManager:
    global _breaker_manager
    if _breaker_manager is None:
        _breaker_manager = CircuitBreakerManager()
    return _breaker_manager


def get_breaker(tool_name: str) -> CircuitBreaker:
    return get_breaker_manager().get_breaker(tool_name)
