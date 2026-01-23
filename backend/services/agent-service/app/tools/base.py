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


class BaseTool(ABC):
    """
    工具基类
    
    所有 MCP Tools 都需要继承此类并实现 execute 方法
    """
    
    name: str  # 工具名称（唯一标识）
    description: str  # 工具描述（给 LLM 看的）
    parameters: Dict[str, Any]  # JSON Schema 格式的参数定义
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
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
        """允许工具像函数一样被调用"""
        start_time = time.time()
        try:
            result = await self.execute(**kwargs)
            result.duration_ms = int((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} execution error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
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
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()

