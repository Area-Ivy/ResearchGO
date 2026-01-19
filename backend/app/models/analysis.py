"""
Analysis Models
论文分析相关的数据模型
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class AnalysisRequest(BaseModel):
    """论文分析请求"""
    object_name: str  # MinIO中的PDF文件对象名称
    language: str = "zh"  # 语言：zh/en


class PaperAnalysis(BaseModel):
    """论文分析结果"""
    title: str  # 论文标题
    abstract: str  # 论文摘要
    research_background: str  # 研究背景
    research_problem: str  # 研究问题
    methodology: str  # 研究方法
    key_findings: str  # 主要发现
    innovations: str  # 创新点
    limitations: str  # 局限性
    future_work: str  # 未来工作
    conclusion: str  # 结论


class AnalysisResponse(BaseModel):
    """论文分析响应"""
    success: bool
    message: str
    analysis: Optional[PaperAnalysis] = None
    pdf_info: Optional[Dict[str, Any]] = None

