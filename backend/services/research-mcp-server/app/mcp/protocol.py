from typing import Any, Dict, Optional

from pydantic import BaseModel

from ..config import MCP_PROTOCOL_VERSION, SERVICE_NAME
from ..mcp.registry import ToolContext, get_registry


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Dict[str, Any] = {}


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


async def handle_rpc(payload: JsonRpcRequest, authorization: Optional[str]) -> JsonRpcResponse:
    registry = get_registry()
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    context = ToolContext(token=token)

    try:
        if payload.method == "initialize":
            return JsonRpcResponse(id=payload.id, result={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "serverInfo": {"name": SERVICE_NAME, "version": "1.0.0"},
                "capabilities": {"tools": {}}
            })
        if payload.method == "tools/list":
            return JsonRpcResponse(id=payload.id, result={"tools": [tool.model_dump() for tool in registry.list_tools()]})
        if payload.method == "tools/call":
            name = payload.params.get("name")
            arguments = payload.params.get("arguments", {})
            result = await registry.call_tool(name, arguments, context)
            return JsonRpcResponse(id=payload.id, result=result.model_dump())
        return JsonRpcResponse(id=payload.id, error={"code": -32601, "message": f"Method not found: {payload.method}"})
    except Exception as exc:
        return JsonRpcResponse(id=payload.id, error={"code": -32000, "message": str(exc)})
