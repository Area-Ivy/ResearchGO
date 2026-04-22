from fastapi import APIRouter, Header

from ..mcp.protocol import JsonRpcRequest, handle_rpc

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.post("")
async def rpc(payload: JsonRpcRequest, authorization: str | None = Header(default=None)):
    return (await handle_rpc(payload, authorization)).model_dump(exclude_none=True)
