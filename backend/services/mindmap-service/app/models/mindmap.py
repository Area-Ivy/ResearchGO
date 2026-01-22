"""
Mindmap Models
思维导图相关的数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MindmapNode(BaseModel):
    """思维导图节点"""
    id: str = Field(..., description="节点ID")
    content: str = Field(..., description="节点内容")
    level: int = Field(..., description="节点层级")
    children: List['MindmapNode'] = Field(default_factory=list, description="子节点列表")


class MindmapGenerateRequest(BaseModel):
    """生成思维导图请求"""
    object_name: str = Field(..., description="MinIO中的PDF文件对象名称")
    max_depth: Optional[int] = Field(default=3, description="思维导图最大深度")
    language: Optional[str] = Field(default="zh", description="语言（zh/en）")


class MindmapGenerateResponse(BaseModel):
    """生成思维导图响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    mindmap_data: Optional[Dict[str, Any]] = Field(None, description="jsMind格式的思维导图数据")
    pdf_info: Optional[Dict[str, Any]] = Field(None, description="PDF文件信息")


# 更新前向引用
MindmapNode.model_rebuild()

