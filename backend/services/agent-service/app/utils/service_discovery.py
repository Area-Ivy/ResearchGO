"""
服务发现模块
提供动态服务发现，优先使用 Consul，失败时回退到环境变量
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# 服务名称到端口的映射
SERVICE_PORTS = {
    "auth-service": 8001,
    "conversation-service": 8002,
    "paper-storage-service": 8003,
    "vector-search-service": 8004,
    "literature-search-service": 8005,
    "mindmap-service": 8007,
    "analysis-service": 8008,
}

# 环境变量名称映射
ENV_VAR_MAPPING = {
    "auth-service": "AUTH_SERVICE_URL",
    "conversation-service": "CONVERSATION_SERVICE_URL",
    "paper-storage-service": "PAPER_STORAGE_SERVICE_URL",
    "vector-search-service": "VECTOR_SEARCH_SERVICE_URL",
    "literature-search-service": "LITERATURE_SERVICE_URL",
    "mindmap-service": "MINDMAP_SERVICE_URL",
    "analysis-service": "ANALYSIS_SERVICE_URL",
}


class ServiceDiscovery:
    """
    服务发现客户端
    
    优先级：
    1. Consul 动态发现
    2. 环境变量配置
    3. Docker DNS 默认地址
    """
    
    def __init__(self):
        self._consul_client = None
        self._consul_available = None
        self._url_cache: Dict[str, str] = {}
    
    async def _get_consul_client(self):
        """懒加载 Consul 客户端"""
        if self._consul_client is None:
            try:
                from .consul_registry import get_consul_client
                self._consul_client = get_consul_client()
            except Exception as e:
                logger.warning(f"无法初始化 Consul 客户端: {e}")
        return self._consul_client
    
    async def _check_consul_available(self) -> bool:
        """检查 Consul 是否可用"""
        if self._consul_available is not None:
            return self._consul_available
        
        try:
            client = await self._get_consul_client()
            if client:
                # 尝试获取服务列表来验证连接
                import httpx
                async with httpx.AsyncClient(timeout=3.0) as http_client:
                    response = await http_client.get(
                        f"{client.consul_url}/v1/status/leader"
                    )
                    self._consul_available = response.status_code == 200
            else:
                self._consul_available = False
        except Exception:
            self._consul_available = False
        
        return self._consul_available
    
    def _get_fallback_url(self, service_name: str) -> str:
        """获取备用 URL（环境变量或 Docker DNS）"""
        # 首先尝试环境变量
        env_var = ENV_VAR_MAPPING.get(service_name)
        if env_var:
            url = os.getenv(env_var)
            if url:
                return url
        
        # 使用 Docker DNS
        port = SERVICE_PORTS.get(service_name, 8000)
        return f"http://{service_name}:{port}"
    
    async def get_url(self, service_name: str) -> str:
        """
        获取服务 URL
        
        Args:
            service_name: 服务名称（如 "auth-service"）
            
        Returns:
            服务 URL
        """
        # 检查缓存
        if service_name in self._url_cache:
            return self._url_cache[service_name]
        
        url = None
        
        # 尝试 Consul 发现
        if await self._check_consul_available():
            try:
                client = await self._get_consul_client()
                instance = await client.discover(service_name)
                if instance and instance.healthy:
                    url = instance.url
                    logger.debug(f"从 Consul 发现服务: {service_name} -> {url}")
            except Exception as e:
                logger.warning(f"Consul 发现失败 ({service_name}): {e}")
        
        # 使用备用地址
        if not url:
            url = self._get_fallback_url(service_name)
            logger.debug(f"使用备用地址: {service_name} -> {url}")
        
        # 缓存 URL（注意：这会缓存直到服务重启）
        self._url_cache[service_name] = url
        
        return url
    
    async def clear_cache(self, service_name: str = None):
        """清除 URL 缓存"""
        if service_name:
            self._url_cache.pop(service_name, None)
        else:
            self._url_cache.clear()
    
    # 便捷方法
    async def auth_service(self) -> str:
        return await self.get_url("auth-service")
    
    async def conversation_service(self) -> str:
        return await self.get_url("conversation-service")
    
    async def paper_storage_service(self) -> str:
        return await self.get_url("paper-storage-service")
    
    async def vector_search_service(self) -> str:
        return await self.get_url("vector-search-service")
    
    async def literature_service(self) -> str:
        return await self.get_url("literature-search-service")
    
    async def mindmap_service(self) -> str:
        return await self.get_url("mindmap-service")
    
    async def analysis_service(self) -> str:
        return await self.get_url("analysis-service")


# 全局实例
_service_discovery: Optional[ServiceDiscovery] = None


def get_service_discovery() -> ServiceDiscovery:
    """获取全局服务发现实例"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
    return _service_discovery


# 便捷函数
async def discover(service_name: str) -> str:
    """发现服务，返回 URL"""
    sd = get_service_discovery()
    return await sd.get_url(service_name)

