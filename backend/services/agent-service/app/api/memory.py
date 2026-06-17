"""Editable markdown memory API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..memory.semantic_memory import get_semantic_memory_service
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/memory", tags=["Memory"])

MAX_MEMORY_BYTES = 200_000


class MemoryDocumentResponse(BaseModel):
    content: str
    file_name: str
    exists: bool
    updated_at: Optional[str] = None


class MemoryDocumentUpdate(BaseModel):
    content: str = Field(default="", max_length=MAX_MEMORY_BYTES)


def _current_user_id(current_user: Dict[str, Any]) -> str:
    user_id = current_user.get("user_id") or current_user.get("username")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return str(user_id)


def _response_for_user(user_id: str) -> MemoryDocumentResponse:
    service = get_semantic_memory_service()
    info = service.get_memory_file_info(user_id)
    return MemoryDocumentResponse(
        content=service.get_memory_markdown(user_id),
        file_name=info["file_name"],
        exists=info["exists"],
        updated_at=info["updated_at"],
    )


@router.get("", response_model=MemoryDocumentResponse)
async def get_memory_document(current_user: Dict[str, Any] = Depends(get_current_user)):
    return _response_for_user(_current_user_id(current_user))


@router.put("", response_model=MemoryDocumentResponse)
async def update_memory_document(
    payload: MemoryDocumentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if len(payload.content.encode("utf-8")) > MAX_MEMORY_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Memory file is too large")

    user_id = _current_user_id(current_user)
    get_semantic_memory_service().save_memory_markdown(user_id, payload.content)
    return _response_for_user(user_id)


@router.delete("", response_model=MemoryDocumentResponse)
async def clear_memory_document(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = _current_user_id(current_user)
    success = await get_semantic_memory_service().clear_user_memories(user_id, token=None)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear memory")
    return _response_for_user(user_id)
