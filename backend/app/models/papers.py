"""
Papers Models
文献管理相关的数据模型
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PaperUploadResponse(BaseModel):
    """文件上传响应"""
    object_name: str = Field(..., description="MinIO 中的对象名称")
    original_name: str = Field(..., description="原始文件名")
    size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件类型")
    upload_time: str = Field(..., description="上传时间")
    message: str = Field(default="File uploaded successfully")


class PaperInfo(BaseModel):
    """文件信息"""
    object_name: str = Field(..., description="MinIO 中的对象名称")
    original_name: str = Field(..., description="原始文件名")
    size: int = Field(..., description="文件大小（字节）")
    last_modified: Optional[str] = Field(None, description="最后修改时间")
    content_type: str = Field(..., description="文件类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class PaperListResponse(BaseModel):
    """文件列表响应"""
    total: int = Field(..., description="文件总数")
    papers: list[PaperInfo] = Field(..., description="文件列表")


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    object_name: str = Field(..., description="被删除的对象名称")

