"""System status aggregation API."""
import asyncio
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends

from ..utils.auth import get_current_user
from ..utils.service_discovery import get_service_discovery

router = APIRouter(prefix="/api/system", tags=["System"])

SERVICES = [
    ("agent-service", "Agent Service", None),
    ("auth-service", "Auth Service", "auth_service"),
    ("conversation-service", "Conversation Service", "conversation_service"),
    ("paper-storage-service", "Paper Storage Service", "paper_storage_service"),
    ("vector-search-service", "Vector Search Service", "vector_search_service"),
    ("literature-search-service", "Literature Search Service", "literature_service"),
    ("mindmap-service", "Mindmap Service", "mindmap_service"),
    ("analysis-service", "Analysis Service", "analysis_service"),
    ("research-mcp-server", "Research MCP Server", "mcp_service"),
]


async def _service_url(method_name: str | None) -> str:
    if method_name is None:
        return "http://agent-service:8000"
    discovery = get_service_discovery()
    return await getattr(discovery, method_name)()


async def _check_service(name: str, label: str, method_name: str | None) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        base_url = (await _service_url(method_name)).rstrip("/")
        async with httpx.AsyncClient(timeout=2.5) as client:
            response = await client.get(f"{base_url}/health")
        latency_ms = round((time.perf_counter() - started_at) * 1000)
        healthy = response.status_code == 200
        payload = {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        return {
            "id": name,
            "name": label,
            "status": "healthy" if healthy else "degraded",
            "statusCode": response.status_code,
            "latencyMs": latency_ms,
            "url": base_url,
            "detail": payload.get("status") or response.reason_phrase,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started_at) * 1000)
        return {
            "id": name,
            "name": label,
            "status": "down",
            "statusCode": None,
            "latencyMs": latency_ms,
            "url": None,
            "detail": str(exc),
        }


@router.get("/status")
async def get_system_status(_current_user: dict = Depends(get_current_user)):
    checks = await asyncio.gather(
        *[_check_service(name, label, method_name) for name, label, method_name in SERVICES]
    )
    healthy_count = sum(1 for item in checks if item["status"] == "healthy")
    return {
        "status": "healthy" if healthy_count == len(checks) else "degraded",
        "healthy": healthy_count,
        "total": len(checks),
        "services": checks,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
