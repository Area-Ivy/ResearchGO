"""Service discovery helpers for the MCP server."""
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

SERVICE_PORTS = {
    "auth-service": 8001,
    "paper-storage-service": 8003,
    "vector-search-service": 8004,
    "literature-search-service": 8005,
    "mindmap-service": 8007,
    "analysis-service": 8008,
}

ENV_VAR_MAPPING = {
    "auth-service": "AUTH_SERVICE_URL",
    "paper-storage-service": "PAPER_STORAGE_SERVICE_URL",
    "vector-search-service": "VECTOR_SEARCH_SERVICE_URL",
    "literature-search-service": "LITERATURE_SERVICE_URL",
    "mindmap-service": "MINDMAP_SERVICE_URL",
    "analysis-service": "ANALYSIS_SERVICE_URL",
}


class ServiceDiscovery:
    def __init__(self):
        self._consul_client = None
        self._consul_available = None
        self._url_cache: Dict[str, str] = {}

    async def _get_consul_client(self):
        if self._consul_client is None:
            from .consul_registry import get_consul_client
            self._consul_client = get_consul_client()
        return self._consul_client

    async def _check_consul_available(self) -> bool:
        if self._consul_available is not None:
            return self._consul_available

        try:
            client = await self._get_consul_client()
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as http_client:
                response = await http_client.get(f"{client.consul_url}/v1/status/leader")
                self._consul_available = response.status_code == 200
        except Exception:
            self._consul_available = False
        return self._consul_available

    def _get_fallback_url(self, service_name: str) -> str:
        env_var = ENV_VAR_MAPPING.get(service_name)
        if env_var:
            url = os.getenv(env_var)
            if url:
                return url
        port = SERVICE_PORTS.get(service_name, 8000)
        return f"http://{service_name}:{port}"

    async def get_url(self, service_name: str) -> str:
        if service_name in self._url_cache:
            return self._url_cache[service_name]

        url = None
        if await self._check_consul_available():
            try:
                client = await self._get_consul_client()
                instance = await client.discover(service_name)
                if instance and instance.healthy:
                    url = instance.url
            except Exception as exc:
                logger.warning("Consul discovery failed for %s: %s", service_name, exc)

        if not url:
            url = self._get_fallback_url(service_name)
        self._url_cache[service_name] = url
        return url


_service_discovery: Optional[ServiceDiscovery] = None


def get_service_discovery() -> ServiceDiscovery:
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
    return _service_discovery
