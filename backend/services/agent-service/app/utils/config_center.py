"""
配置中心模块
从 Consul KV 读取配置，支持热更新
"""
import os
import asyncio
import logging
from typing import Any, Dict, Optional, Callable, List

logger = logging.getLogger(__name__)


class ConfigCenter:
    """
    配置中心
    
    优先级：
    1. Consul KV
    2. 环境变量
    3. 默认值
    """
    
    # 配置键到环境变量的映射
    ENV_MAPPING = {
        "config/openai/api_key": "OPENAI_API_KEY",
        "config/openai/model": "OPENAI_MODEL",
        "config/openai/base_url": "OPENAI_BASE_URL",
        "config/agent/max_iterations": "MAX_ITERATIONS",
        "config/agent/timeout": "AGENT_TIMEOUT",
        "config/memory/sliding_window_size": "SLIDING_WINDOW_SIZE",
        "config/memory/enable_summary": "ENABLE_CONVERSATION_SUMMARY",
        "config/memory/enable_semantic": "ENABLE_SEMANTIC_MEMORY",
    }
    
    # 默认值
    DEFAULTS = {
        "config/openai/model": "gpt-4o",
        "config/agent/max_iterations": 10,
        "config/agent/timeout": 120,
        "config/memory/sliding_window_size": 10,
        "config/memory/enable_summary": True,
        "config/memory/enable_semantic": True,
    }
    
    def __init__(self):
        self._consul_client = None
        self._consul_available = None
        self._cache: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._watch_tasks: List[asyncio.Task] = []
    
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
    
    def _get_from_env(self, key: str) -> Optional[Any]:
        """从环境变量获取配置"""
        env_var = self.ENV_MAPPING.get(key)
        if env_var:
            value = os.getenv(env_var)
            if value is not None:
                # 尝试转换类型
                default = self.DEFAULTS.get(key)
                if isinstance(default, bool):
                    return value.lower() in ("true", "1", "yes")
                elif isinstance(default, int):
                    try:
                        return int(value)
                    except ValueError:
                        pass
                elif isinstance(default, float):
                    try:
                        return float(value)
                    except ValueError:
                        pass
                return value
        return None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置
        
        Args:
            key: 配置键（如 "config/openai/model"）
            default: 默认值
            
        Returns:
            配置值
        """
        # 检查缓存
        if key in self._cache:
            return self._cache[key]
        
        value = None
        
        # 1. 尝试从 Consul KV 获取
        if await self._check_consul_available():
            try:
                client = await self._get_consul_client()
                value = await client.get_config(key)
                if value is not None:
                    logger.info(f"[ConfigCenter] 从 Consul KV 获取: {key} = {value}")
            except Exception as e:
                logger.warning(f"从 Consul 获取配置失败 ({key}): {e}")
        
        # 2. 尝试从环境变量获取
        if value is None:
            value = self._get_from_env(key)
            if value is not None:
                logger.debug(f"从环境变量获取配置: {key} = {value}")
        
        # 3. 使用默认值
        if value is None:
            value = default if default is not None else self.DEFAULTS.get(key)
            logger.debug(f"使用默认配置: {key} = {value}")
        
        # 缓存配置
        if value is not None:
            self._cache[key] = value
        
        return value
    
    async def set(self, key: str, value: Any) -> bool:
        """
        设置配置（写入 Consul KV）
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            是否成功
        """
        if await self._check_consul_available():
            try:
                client = await self._get_consul_client()
                success = await client.set_config(key, value)
                if success:
                    self._cache[key] = value
                    # 触发监听器
                    await self._notify_watchers(key, value)
                return success
            except Exception as e:
                logger.error(f"设置配置失败 ({key}): {e}")
        
        return False
    
    async def refresh(self, key: str = None):
        """刷新配置缓存"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    # ==================== 配置监听 ====================
    
    def watch(self, key: str, callback: Callable[[str, Any], None]):
        """
        注册配置变更监听器
        
        Args:
            key: 配置键
            callback: 回调函数 (key, new_value) -> None
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
    
    async def _notify_watchers(self, key: str, value: Any):
        """通知所有监听器"""
        callbacks = self._watchers.get(key, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(key, value)
                else:
                    callback(key, value)
            except Exception as e:
                logger.error(f"配置监听器执行失败: {e}")
    
    async def start_watching(self, keys: List[str], interval: float = 5.0):
        """
        开始监听配置变更
        
        Args:
            keys: 要监听的配置键列表
            interval: 检查间隔（秒）
        """
        if not await self._check_consul_available():
            logger.warning("Consul 不可用，配置监听未启动")
            return
        
        async def watch_key(key: str):
            last_value = await self.get(key)
            while True:
                try:
                    await asyncio.sleep(interval)
                    # 强制从 Consul 刷新
                    self._cache.pop(key, None)
                    current_value = await self.get(key)
                    
                    if current_value != last_value:
                        logger.info(f"配置变更: {key}: {last_value} -> {current_value}")
                        last_value = current_value
                        await self._notify_watchers(key, current_value)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"配置监听异常 ({key}): {e}")
        
        for key in keys:
            task = asyncio.create_task(watch_key(key))
            self._watch_tasks.append(task)
        
        logger.info(f"已启动配置监听: {keys}")
    
    async def stop_watching(self):
        """停止配置监听"""
        for task in self._watch_tasks:
            task.cancel()
        self._watch_tasks.clear()
    
    # ==================== 便捷方法 ====================
    
    async def get_openai_model(self) -> str:
        return await self.get("config/openai/model", "gpt-4o")
    
    async def get_agent_timeout(self) -> int:
        return await self.get("config/agent/timeout", 120)
    
    async def get_max_iterations(self) -> int:
        return await self.get("config/agent/max_iterations", 10)
    
    async def get_sliding_window_size(self) -> int:
        return await self.get("config/memory/sliding_window_size", 10)


# 全局实例
_config_center: Optional[ConfigCenter] = None


def get_config_center() -> ConfigCenter:
    """获取全局配置中心实例"""
    global _config_center
    if _config_center is None:
        _config_center = ConfigCenter()
    return _config_center


# 便捷函数
async def get_config(key: str, default: Any = None) -> Any:
    """获取配置"""
    cc = get_config_center()
    return await cc.get(key, default)


async def set_config(key: str, value: Any) -> bool:
    """设置配置"""
    cc = get_config_center()
    return await cc.set(key, value)

