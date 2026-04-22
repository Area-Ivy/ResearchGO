from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from ..config import MCP_SERVER_URL, MCP_TOOLS_CACHE_TTL
from ..utils.service_discovery import get_service_discovery

logger = logging.getLogger(__name__)


class McpClient:
    def __init__(
        self,
        service_name: str = "research-mcp-server",
        fallback_url: Optional[str] = None,
        tools_cache_ttl: int = MCP_TOOLS_CACHE_TTL,
    ):
        self.service_name = service_name
        self.fallback_url = fallback_url
        self.tools_cache_ttl = max(0, tools_cache_ttl)
        self._initialized = False
        self._tool_cache: List[Dict[str, Any]] = []
        self._tool_cache_expires_at: float = 0.0

    async def _resolve_base_url(self) -> str:
        if self.fallback_url:
            return self.fallback_url.rstrip("/")
        sd = get_service_discovery()
        return (await sd.get_url(self.service_name)).rstrip("/")

    async def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
        base_url = await self._resolve_base_url()
        payload = {"jsonrpc": "2.0", "id": method, "method": method, "params": params or {}}
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url}/mcp", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        if body.get("error"):
            raise RuntimeError(body["error"].get("message", "MCP request failed"))
        return body.get("result", {})

    async def initialize(self):
        if self._initialized:
            return
        await self._rpc("initialize")
        self._initialized = True

    def _tool_cache_valid(self) -> bool:
        return bool(self._tool_cache) and time.monotonic() < self._tool_cache_expires_at

    async def list_tools(self, refresh: bool = False) -> List[Dict[str, Any]]:
        await self.initialize()
        if not refresh and self._tool_cache_valid():
            return self._tool_cache
        result = await self._rpc("tools/list")
        self._tool_cache = result.get("tools", [])
        self._tool_cache_expires_at = time.monotonic() + self.tools_cache_ttl
        return self._tool_cache

    async def call_tool(self, name: str, arguments: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        await self.initialize()
        return await self._rpc("tools/call", {"name": name, "arguments": arguments}, token=token)


_mcp_client: Optional[McpClient] = None


def get_mcp_client() -> McpClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = McpClient(fallback_url=MCP_SERVER_URL)
    return _mcp_client
