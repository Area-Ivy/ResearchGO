"""
搜索相关的Pydantic模型
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., description="搜索查询", min_length=1)
    top_k: int = Field(10, description="返回结果数量", ge=1, le=50)
    uploaded_after: Optional[str] = Field(None, description="过滤上传时间（ISO格式）")


class SearchResult(BaseModel):
    """搜索结果项"""
    # 系统字段
    id: int = Field(..., description="Milvus主键")
    distance: float = Field(..., description="向量距离")
    relevance_score: float = Field(..., description="相关性分数（0-1）")
    
    # Paper信息
    paper_id: str = Field(..., description="论文ID")
    title: str = Field(..., description="论文标题")
    file_name: str = Field(..., description="原始文件名")
    upload_time: str = Field(..., description="上传时间")
    
    # Chunk信息
    chunk_id: str = Field(..., description="Chunk ID")
    chunk_index: int = Field(..., description="Chunk索引")
    content: str = Field(..., description="Chunk内容")
    chunk_chars: int = Field(..., description="字符数")
    page_range: str = Field(..., description="页码范围")
    source: str = Field(..., description="来源类型")


class SemanticSearchResponse(BaseModel):
    """语义搜索响应"""
    query: str = Field(..., description="搜索查询")
    results: List[SearchResult] = Field(..., description="搜索结果列表")
    total: int = Field(..., description="结果总数")
    search_time_ms: float = Field(..., description="搜索耗时（毫秒）")


class PaperQARequest(BaseModel):
    """论文问答请求"""
    paper_id: str = Field(..., description="论文ID（MinIO对象名）")
    question: str = Field(..., description="用户问题", min_length=1)
    chat_history: List[Dict[str, str]] = Field(default_factory=list, description="聊天历史")
    top_k: int = Field(10, description="检索相关内容数量", ge=1, le=20)


class PaperQAResponse(BaseModel):
    """论文问答响应"""
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="AI回答")
    references: List[SearchResult] = Field(..., description="参考内容")
    response_time_ms: float = Field(..., description="响应耗时（毫秒）")


class StructuredChunk(BaseModel):
    """结构化内容块"""
    content: str = Field(..., description="内容")
    chunk_index: int = Field(0, description="块索引")
    section_type: str = Field("other", description="章节类型: abstract/introduction/methods/results/discussion/conclusion/other")
    section_title: str = Field("", description="章节标题")
    subsection_title: Optional[str] = Field(None, description="子章节标题")
    hierarchy_path: str = Field("", description="层级路径，如 'Methods > Data Collection'")
    char_count: int = Field(0, description="字符数")
    is_complete_section: bool = Field(False, description="是否是完整章节（未被切分）")
    metadata: Dict = Field(default_factory=dict, description="元数据")


class IndexPaperRequest(BaseModel):
    """索引论文请求
    
    支持两种模式:
    1. 简单模式: 只传 content，自动切分
    2. 结构化模式: 传 structured_chunks（来自 LLM 结构解析 + 递归语义切分）
    """
    paper_id: str = Field(..., description="论文ID（MinIO对象名）")
    title: str = Field(..., description="论文标题")
    file_name: str = Field(..., description="原始文件名")
    content: str = Field("", description="论文内容（全文）- 简单模式")
    max_chunk_size: int = Field(1000, description="最大chunk大小", ge=100, le=5000)
    
    # 结构化支持
    structured_chunks: Optional[List[StructuredChunk]] = Field(
        None, 
        description="结构化内容块（来自 LLM 结构解析 + 递归语义切分）"
    )
    
    # 论文元信息
    paper_metadata: Optional[Dict] = Field(
        default_factory=dict,
        description="论文元信息（标题、作者、摘要等）"
    )


class IndexPaperResponse(BaseModel):
    """索引论文响应"""
    paper_id: str = Field(..., description="论文ID")
    chunks_created: int = Field(..., description="创建的chunk数量")
    message: str = Field(..., description="消息")
    section_types: Optional[Dict[str, int]] = Field(None, description="章节类型分布")
    structured: bool = Field(False, description="是否使用结构化解析")
