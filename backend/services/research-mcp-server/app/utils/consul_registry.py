"""
Consul 服务注册与发现模块
提供：
1. 服务注册/注销
2. 服务发现（动态获取其他服务地址）
3. 配置中心（KV Store）
4. 配置监听（热更新）
"""
import os
import json
import socket
import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """服务实例信息"""
    id: str
    name: str
    address: str
    port: int
    tags: List[str]
    healthy: bool
    
    @property
    def url(self) -> str:
        return f"http://{self.address}:{self.port}"


class ConsulClient:
    """
    Consul 客户端
    提供服务注册、发现和配置管理功能
    """
    
    def __init__(
        self,
        consul_host: str = None,
        consul_port: int = 8500,
        service_name: str = None,
        service_port: int = None,
        service_tags: List[str] = None,
        health_check_path: str = "/health",
        health_check_interval: str = "10s",
        deregister_critical_service_after: str = "30s"
    ):
        self.consul_host = consul_host or os.getenv("CONSUL_HOST", "localhost")
        self.consul_port = consul_port
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown-service")
        self.service_port = service_port or int(os.getenv("SERVICE_PORT", "8000"))
        self.service_tags = service_tags or ["researchgo", "microservice"]
        self.health_check_path = health_check_path
        self.health_check_interval = health_check_interval
        self.deregister_after = deregister_critical_service_after
        
        # 获取容器/主机地址
        self.service_address = self._get_host_ip()
        
        # 服务 ID
        self.service_id = f"{self.service_name}-{self.service_address}-{self.service_port}"
        
        self.consul_url = f"http://{self.consul_host}:{self.consul_port}"
        self._registered = False
        
        # 服务地址缓存
        self._service_cache: Dict[str, List[ServiceInstance]] = {}
        self._cache_ttl = 30  # 缓存 30 秒
        self._cache_timestamps: Dict[str, float] = {}
        
        # 配置缓存
        self._config_cache: Dict[str, Any] = {}
        self._config_watchers: Dict[str, List[Callable]] = {}
        
    def _get_host_ip(self) -> str:
        """获取当前主机/容器的地址"""
        try:
            container_name = os.getenv("HOSTNAME", socket.gethostname())
            return container_name
        except Exception:
            return "127.0.0.1"
    
    # ==================== 服务注册 ====================
    
    async def register(self) -> bool:
        """注册服务到 Consul"""
        if self._registered:
            logger.warning(f"Service {self.service_name} already registered")
            return True
        
        service_definition = {
            "ID": self.service_id,
            "Name": self.service_name,
            "Address": self.service_address,
            "Port": self.service_port,
            "Tags": self.service_tags + [
                "traefik.enable=true",
                f"traefik.http.routers.{self.service_name}.entrypoints=web",
            ],
            "Meta": {
                "version": "1.0.0",
                "protocol": "http"
            },
            "Check": {
                "HTTP": f"http://{self.service_address}:{self.service_port}{self.health_check_path}",
                "Interval": self.health_check_interval,
                "Timeout": "5s",
                "DeregisterCriticalServiceAfter": self.deregister_after
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.consul_url}/v1/agent/service/register",
                    json=service_definition
                )
                
                if response.status_code == 200:
                    self._registered = True
                    logger.info(f"✓ 服务注册成功: {self.service_name} ({self.service_id})")
                    return True
                else:
                    logger.error(f"服务注册失败: {response.status_code}")
                    return False
                    
        except httpx.ConnectError:
            logger.warning(f"无法连接 Consul ({self.consul_url})，服务将以独立模式运行")
            return False
        except Exception as e:
            logger.error(f"服务注册异常: {e}")
            return False
    
    async def deregister(self) -> bool:
        """从 Consul 注销服务"""
        if not self._registered:
            return True
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.consul_url}/v1/agent/service/deregister/{self.service_id}"
                )
                
                if response.status_code == 200:
                    self._registered = False
                    logger.info(f"✓ 服务注销成功: {self.service_name}")
                    return True
                return False
                    
        except Exception as e:
            logger.error(f"服务注销异常: {e}")
            return False
    
    # ==================== 服务发现 ====================
    
    async def discover(self, service_name: str, use_cache: bool = True) -> Optional[ServiceInstance]:
        """
        发现服务 - 返回一个健康的服务实例
        
        Args:
            service_name: 要发现的服务名称
            use_cache: 是否使用缓存
            
        Returns:
            ServiceInstance 或 None
        """
        instances = await self.discover_all(service_name, use_cache)
        if instances:
            # 简单轮询，返回第一个健康实例
            healthy = [i for i in instances if i.healthy]
            return healthy[0] if healthy else None
        return None
    
    async def discover_all(self, service_name: str, use_cache: bool = True) -> List[ServiceInstance]:
        """
        发现服务的所有实例
        
        Args:
            service_name: 要发现的服务名称
            use_cache: 是否使用缓存
            
        Returns:
            ServiceInstance 列表
        """
        import time
        
        # 检查缓存
        if use_cache and service_name in self._service_cache:
            cache_time = self._cache_timestamps.get(service_name, 0)
            if time.time() - cache_time < self._cache_ttl:
                return self._service_cache[service_name]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.consul_url}/v1/health/service/{service_name}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    instances = []
                    
                    for entry in data:
                        service = entry.get("Service", {})
                        checks = entry.get("Checks", [])
                        
                        # 判断服务是否健康
                        healthy = all(
                            check.get("Status") == "passing" 
                            for check in checks
                        )
                        
                        instance = ServiceInstance(
                            id=service.get("ID", ""),
                            name=service.get("Service", ""),
                            address=service.get("Address", ""),
                            port=service.get("Port", 0),
                            tags=service.get("Tags", []),
                            healthy=healthy
                        )
                        instances.append(instance)
                    
                    # 更新缓存
                    self._service_cache[service_name] = instances
                    self._cache_timestamps[service_name] = time.time()
                    
                    return instances
                    
        except Exception as e:
            logger.error(f"服务发现失败 ({service_name}): {e}")
        
        # 返回缓存的数据（即使过期）
        return self._service_cache.get(service_name, [])
    
    async def get_service_url(self, service_name: str, fallback: str = None) -> str:
        """
        获取服务 URL（便捷方法）
        
        Args:
            service_name: 服务名称
            fallback: 如果发现失败，使用的备用 URL
            
        Returns:
            服务 URL
        """
        instance = await self.discover(service_name)
        if instance:
            return instance.url
        
        if fallback:
            logger.warning(f"服务发现失败 ({service_name})，使用备用地址: {fallback}")
            return fallback
        
        # 默认使用 Docker DNS
        default_ports = {
            "agent-service": 8000,
            "auth-service": 8001,
            "conversation-service": 8002,
            "paper-storage-service": 8003,
            "vector-search-service": 8004,
            "literature-search-service": 8005,
            "mindmap-service": 8007,
            "analysis-service": 8008,
        }
        port = default_ports.get(service_name, 8000)
        fallback_url = f"http://{service_name}:{port}"
        logger.warning(f"服务发现失败 ({service_name})，使用 Docker DNS: {fallback_url}")
        return fallback_url
    
    # ==================== 配置中心 (KV Store) ====================
    
    async def get_config(self, key: str, default: Any = None) -> Any:
        """
        从 Consul KV 获取配置
        
        Args:
            key: 配置键（如 "config/openai/model"）
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.consul_url}/v1/kv/{key}",
                    params={"raw": "true"}
                )
                
                if response.status_code == 200:
                    value = response.text
                    # 尝试解析 JSON
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                elif response.status_code == 404:
                    return default
                    
        except Exception as e:
            logger.error(f"获取配置失败 ({key}): {e}")
        
        return default
    
    async def set_config(self, key: str, value: Any) -> bool:
        """
        设置 Consul KV 配置
        
        Args:
            key: 配置键
            value: 配置值（支持 dict/list，会自动转 JSON）
            
        Returns:
            是否成功
        """
        try:
            # 如果是复杂类型，转为 JSON
            if isinstance(value, (dict, list)):
                data = json.dumps(value, ensure_ascii=False)
            else:
                data = str(value)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.consul_url}/v1/kv/{key}",
                    content=data.encode('utf-8')
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ 配置已保存: {key}")
                    return True
                    
        except Exception as e:
            logger.error(f"设置配置失败 ({key}): {e}")
        
        return False
    
    async def delete_config(self, key: str) -> bool:
        """删除配置"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.consul_url}/v1/kv/{key}"
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"删除配置失败 ({key}): {e}")
            return False
    
    async def list_configs(self, prefix: str = "") -> List[str]:
        """列出所有配置键"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.consul_url}/v1/kv/{prefix}",
                    params={"keys": "true"}
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"列出配置失败: {e}")
        
        return []
    
    async def get_all_configs(self, prefix: str = "config/") -> Dict[str, Any]:
        """
        获取指定前缀下的所有配置
        
        Returns:
            {key: value} 字典
        """
        configs = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.consul_url}/v1/kv/{prefix}",
                    params={"recurse": "true"}
                )
                
                if response.status_code == 200:
                    import base64
                    data = response.json()
                    for item in data:
                        key = item.get("Key", "")
                        value_b64 = item.get("Value")
                        if value_b64:
                            value = base64.b64decode(value_b64).decode('utf-8')
                            try:
                                configs[key] = json.loads(value)
                            except json.JSONDecodeError:
                                configs[key] = value
                                
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
        
        return configs
    
    # ==================== 配置监听（热更新） ====================
    
    async def watch_config(self, key: str, callback: Callable[[str, Any], None], interval: float = 5.0):
        """
        监听配置变化
        
        Args:
            key: 配置键
            callback: 回调函数 (key, new_value) -> None
            interval: 检查间隔（秒）
        """
        last_value = await self.get_config(key)
        
        while True:
            try:
                await asyncio.sleep(interval)
                current_value = await self.get_config(key)
                
                if current_value != last_value:
                    logger.info(f"配置变更: {key}")
                    last_value = current_value
                    try:
                        callback(key, current_value)
                    except Exception as e:
                        logger.error(f"配置回调执行失败: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"配置监听异常: {e}")


# ==================== 全局实例和便捷函数 ====================

_consul_client: Optional[ConsulClient] = None


def get_consul_client() -> ConsulClient:
    """获取全局 Consul 客户端实例"""
    global _consul_client
    if _consul_client is None:
        _consul_client = ConsulClient()
    return _consul_client


async def register_service() -> bool:
    """便捷函数：注册当前服务"""
    client = get_consul_client()
    return await client.register()


async def deregister_service() -> bool:
    """便捷函数：注销当前服务"""
    client = get_consul_client()
    return await client.deregister()


async def discover_service(service_name: str) -> Optional[str]:
    """便捷函数：发现服务，返回 URL"""
    client = get_consul_client()
    return await client.get_service_url(service_name)


async def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置"""
    client = get_consul_client()
    return await client.get_config(key, default)


async def set_config(key: str, value: Any) -> bool:
    """便捷函数：设置配置"""
    client = get_consul_client()
    return await client.set_config(key, value)
