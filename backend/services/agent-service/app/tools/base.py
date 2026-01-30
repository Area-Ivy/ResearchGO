"""
Base Tool Class
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
import httpx
import time
import logging

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    is_degraded: bool = False  # 是否为降级响应


class BaseTool(ABC):
    """
    工具基类
    
    所有 MCP Tools 都需要继承此类并实现 execute 方法
    集成熔断器，支持智能降级
    """
    
    name: str  # 工具名称（唯一标识）
    description: str  # 工具描述（给 LLM 看的）
    parameters: Dict[str, Any]  # JSON Schema 格式的参数定义
    enable_circuit_breaker: bool = True  # 是否启用熔断器
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self._breaker = None
    
    @property
    def breaker(self):
        """懒加载熔断器"""
        if self._breaker is None and self.enable_circuit_breaker:
            try:
                from ..utils.circuit_breaker import get_breaker
                self._breaker = get_breaker(self.name)
            except Exception as e:
                logger.warning(f"Failed to initialize circuit breaker for {self.name}: {e}")
        return self._breaker
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    async def __call__(self, **kwargs) -> ToolResult:
        """
        允许工具像函数一样被调用
        集成熔断器检查和降级逻辑
        """
        start_time = time.time()
        
        # 检查熔断器状态
        if self.breaker and not await self.breaker.can_execute():
            # 熔断器开启，返回降级响应
            logger.warning(f"[Tool:{self.name}] 熔断器开启，返回降级响应")
            from ..utils.circuit_breaker import get_degraded_response
            degraded_message = get_degraded_response(self.name, self.breaker)
            return ToolResult(
                success=False,
                error=degraded_message,
                duration_ms=0,
                is_degraded=True
            )
        
        try:
            result = await self.execute(**kwargs)
            result.duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录成功
            if self.breaker and result.success:
                await self.breaker.record_success()
            elif self.breaker and not result.success:
                # execute 返回 success=False 也算失败
                await self.breaker.record_failure(result.error)
            
            return result
            
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            logger.error(f"Tool {self.name} execution error: {e}")
            
            # 记录失败
            if self.breaker:
                await self.breaker.record_failure(str(e))
            
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=duration
            )
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def get_circuit_status(self) -> Optional[Dict[str, Any]]:
        """获取熔断器状态"""
        if self.breaker:
            return self.breaker.get_status()
        return None
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()

