"""
论文相关的Pydantic模型（Schema）
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PaperUploadResponse(BaseModel):
    """论文上传响应"""
    object_name: str = Field(..., description="MinIO中的对象名称")
    original_name: str = Field(..., description="原始文件名")
    size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件类型")
    upload_time: str = Field(..., description="上传时间")
    message: str = Field(default="文件上传成功")


class PaperInfo(BaseModel):
    """论文信息"""
    id: int
    object_name: str
    original_name: str
    file_size: int
    content_type: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """论文列表响应"""
    total: int = Field(..., description="论文总数")
    papers: List[PaperInfo] = Field(..., description="论文列表")


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    object_name: str = Field(..., description="被删除的对象名称")

