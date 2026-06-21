"""
Pydantic schemas for paper storage.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PaperUploadResponse(BaseModel):
    object_name: str = Field(..., description="MinIO object name")
    original_name: str = Field(..., description="Original file name")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_time: str = Field(..., description="Upload timestamp")
    processing_status: str = Field(..., description="Indexing status")
    processing_error: Optional[str] = Field(default=None, description="Last indexing error")
    chunks_created: int = Field(default=0, description="Created vector chunks")
    indexed_at: Optional[str] = Field(default=None, description="Index completion time")
    message: str = Field(default="File uploaded successfully")


class PaperInfo(BaseModel):
    id: int
    object_name: str
    original_name: str
    file_size: int
    content_type: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    processing_status: str = "uploaded"
    processing_error: Optional[str] = None
    indexed_at: Optional[datetime] = None
    chunks_created: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    total: int = Field(..., description="Total papers")
    papers: List[PaperInfo] = Field(..., description="Paper list")


class PaperRenameRequest(BaseModel):
    original_name: str = Field(..., min_length=1, max_length=500, description="New display file name")


class DeleteResponse(BaseModel):
    success: bool = Field(..., description="Deletion result")
    message: str = Field(..., description="Response message")
    object_name: str = Field(..., description="Deleted object name")


class PaperStatusResponse(BaseModel):
    object_name: str = Field(..., description="MinIO object name")
    processing_status: str = Field(..., description="Indexing status")
    processing_error: Optional[str] = Field(default=None, description="Last indexing error")
    chunks_created: int = Field(default=0, description="Created vector chunks")
    indexed_at: Optional[str] = Field(default=None, description="Index completion time")
    updated_at: Optional[str] = Field(default=None, description="Last status update time")


class WeeklyCount(BaseModel):
    label: str
    value: int
    start: str
    end: str


class PaperStatsResponse(BaseModel):
    total: int = Field(..., description="Total paper count")
    indexed: int = Field(default=0, description="Indexed paper count")
    indexing: int = Field(default=0, description="Indexing paper count")
    failed: int = Field(default=0, description="Failed paper count")
    uploaded: int = Field(default=0, description="Uploaded but not indexed count")
    uploaded_this_month: int = Field(default=0, description="Papers uploaded in the current month")
    indexed_this_month: int = Field(default=0, description="Papers indexed in the current month")
    recent_papers: List[PaperInfo] = Field(default_factory=list, description="Recent papers")
    weekly_uploads: List[WeeklyCount] = Field(default_factory=list, description="Last 30 week upload trend")
    field_distribution: Dict[str, int] = Field(default_factory=dict, description="Paper count by dashboard field")
