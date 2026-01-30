"""
Sliding Window Manager for Conversation Context

支持两种模式：
1. 简单滑动窗口：按消息数量限制
2. Token 感知滑动窗口：按 Token 数量限制
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..config import (
    SLIDING_WINDOW_SIZE,
    MAX_CONTEXT_TOKENS,
    ENABLE_TOKEN_COUNTING
)

logger = logging.getLogger(__name__)

# 尝试导入 tiktoken（可选依赖）
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, using approximate token counting")


@dataclass
class WindowStats:
    """滑动窗口统计信息"""
    original_count: int
    final_count: int
    tokens_used: int
    messages_dropped: int
    has_summary: bool


class SlidingWindowManager:
    """
    简单滑动窗口管理器
    
    按消息数量限制上下文长度
    """
    
    def __init__(self, window_size: int = SLIDING_WINDOW_SIZE):
        self.window_size = window_size
    
    def apply(
        self,
        messages: List[Dict[str, Any]],
        keep_system: bool = True,
        keep_first_user: bool = True
    ) -> Tuple[List[Dict[str, Any]], WindowStats]:
        """
        应用滑动窗口
        
        Args:
            messages: 消息列表
            keep_system: 是否保留 system 消息
            keep_first_user: 是否保留第一条 user 消息（原始意图）
            
        Returns:
            (处理后的消息, 统计信息)
        """
        if not messages:
            return [], WindowStats(0, 0, 0, 0, False)
        
        original_count = len(messages)
        
        # 如果消息数量在窗口内，直接返回
        if original_count <= self.window_size * 2:
            return messages.copy(), WindowStats(
                original_count=original_count,
                final_count=original_count,
                tokens_used=0,  # 未计算
                messages_dropped=0,
                has_summary=False
            )
        
        result = []
        
        # 1. 保留 system 消息
        if keep_system:
            system_msgs = [m for m in messages if m.get("role") == "system"]
            result.extend(system_msgs)
        
        # 2. 保留第一条 user 消息
        first_user_msg = None
        if keep_first_user:
            for msg in messages:
                if msg.get("role") == "user":
                    first_user_msg = msg
                    break
            if first_user_msg and first_user_msg not in result:
                result.append(first_user_msg)
        
        # 3. 取最近的消息（排除已添加的）
        non_system_msgs = [m for m in messages if m.get("role") != "system"]
        recent_count = self.window_size * 2 - len(result)
        recent_msgs = non_system_msgs[-recent_count:]
        
        # 避免重复添加第一条 user 消息
        for msg in recent_msgs:
            if msg != first_user_msg:
                result.append(msg)
            elif first_user_msg not in result:
                result.append(msg)
        
        final_count = len(result)
        
        logger.info(
            f"Sliding window applied: {original_count} -> {final_count} messages "
            f"(dropped {original_count - final_count})"
        )
        
        return result, WindowStats(
            original_count=original_count,
            final_count=final_count,
            tokens_used=0,
            messages_dropped=original_count - final_count,
            has_summary=False
        )


class TokenAwareSlidingWindow:
    """
    Token 感知滑动窗口
    
    精确控制上下文 Token 数量，避免超限
    """
    
    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        model: str = "gpt-4"
    ):
        self.max_tokens = max_tokens
        self.model = model
        
        # 初始化 tokenizer
        if TIKTOKEN_AVAILABLE and ENABLE_TOKEN_COUNTING:
            try:
                self.tokenizer = tiktoken.encoding_for_model(model)
            except KeyError:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # 近似估算：中文约 1.5 token/字符，英文约 0.25 token/词
            return len(text) // 3
    
    def count_message_tokens(self, message: Dict[str, Any]) -> int:
        """计算单条消息的 token 数"""
        content = message.get("content", "")
        # 额外添加角色和格式 token
        overhead = 4  # role + format tokens
        return self.count_tokens(content) + overhead
    
    def apply(
        self,
        messages: List[Dict[str, Any]],
        reserve_tokens: int = 500,  # 预留给响应的 token
        priority_roles: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], WindowStats]:
        """
        应用 Token 感知滑动窗口
        
        从最新消息开始，往回添加直到达到 Token 限制
        
        Args:
            messages: 消息列表
            reserve_tokens: 为响应预留的 token 数
            priority_roles: 优先保留的角色（如 ["tool"]）
            
        Returns:
            (处理后的消息, 统计信息)
        """
        if not messages:
            return [], WindowStats(0, 0, 0, 0, False)
        
        original_count = len(messages)
        available_tokens = self.max_tokens - reserve_tokens
        
        # 分离 system 消息（始终保留）
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # 计算 system 消息的 token
        system_tokens = sum(self.count_message_tokens(m) for m in system_msgs)
        remaining_tokens = available_tokens - system_tokens
        
        if remaining_tokens <= 0:
            logger.warning("System messages alone exceed token limit!")
            return system_msgs, WindowStats(
                original_count=original_count,
                final_count=len(system_msgs),
                tokens_used=system_tokens,
                messages_dropped=original_count - len(system_msgs),
                has_summary=False
            )
        
        # 从最新消息开始往回添加
        result_other = []
        total_tokens = 0
        
        # 优先处理特定角色的消息
        priority_roles = priority_roles or ["tool"]
        priority_msgs = []
        normal_msgs = []
        
        for msg in reversed(other_msgs):
            if msg.get("role") in priority_roles:
                priority_msgs.append(msg)
            else:
                normal_msgs.append(msg)
        
        # 先添加优先消息（如工具结果）
        for msg in priority_msgs[:5]:  # 最多保留最近5个工具消息
            msg_tokens = self.count_message_tokens(msg)
            if total_tokens + msg_tokens <= remaining_tokens:
                result_other.insert(0, msg)
                total_tokens += msg_tokens
        
        # 再添加普通消息
        for msg in normal_msgs:
            msg_tokens = self.count_message_tokens(msg)
            if total_tokens + msg_tokens <= remaining_tokens:
                result_other.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        # 合并结果
        result = system_msgs + result_other
        final_tokens = system_tokens + total_tokens
        
        logger.info(
            f"Token-aware sliding window: {original_count} -> {len(result)} messages, "
            f"{final_tokens}/{available_tokens} tokens"
        )
        
        return result, WindowStats(
            original_count=original_count,
            final_count=len(result),
            tokens_used=final_tokens,
            messages_dropped=original_count - len(result),
            has_summary=False
        )


class SmartSlidingWindow:
    """
    智能滑动窗口
    
    结合消息数量和 Token 限制，并保留重要消息
    """
    
    def __init__(
        self,
        window_size: int = SLIDING_WINDOW_SIZE,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        model: str = "gpt-4"
    ):
        self.simple_window = SlidingWindowManager(window_size)
        self.token_window = TokenAwareSlidingWindow(max_tokens, model)
    
    def apply(
        self,
        messages: List[Dict[str, Any]],
        strategy: str = "hybrid"  # "simple", "token", "hybrid"
    ) -> Tuple[List[Dict[str, Any]], WindowStats]:
        """
        应用智能滑动窗口
        
        Args:
            messages: 消息列表
            strategy: 策略 - "simple"(简单), "token"(Token感知), "hybrid"(混合)
        """
        if strategy == "simple":
            return self.simple_window.apply(messages)
        elif strategy == "token":
            return self.token_window.apply(messages)
        else:
            # 混合策略：先用简单窗口粗筛，再用 Token 窗口精筛
            simple_result, _ = self.simple_window.apply(messages)
            return self.token_window.apply(simple_result)

