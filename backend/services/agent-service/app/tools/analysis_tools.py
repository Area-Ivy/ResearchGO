"""
Analysis Tools - 论文分析相关工具
"""
from typing import Optional, List
from .base import BaseTool, ToolResult
from ..config import ANALYSIS_SERVICE_URL, MINDMAP_SERVICE_URL
import logging

logger = logging.getLogger(__name__)


class AnalyzePaperTool(BaseTool):
    """分析论文"""
    
    name = "analyze_paper"
    description = """对论文进行深度分析，生成结构化分析报告。
包括研究问题、方法、贡献、局限性等。
需要论文已上传到用户论文库。
这是一个耗时操作，可能需要1-2分钟。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "paper_name": {
                "type": "string",
                "description": "论文文件名（如 xxx.pdf）"
            }
        },
        "required": ["paper_name"]
    }
    
    async def execute(self, paper_name: str, token: str = None, **kwargs) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = await self.http_client.post(
                f"{ANALYSIS_SERVICE_URL}/api/analysis/analyze",
                json={"paper_name": paper_name},
                headers=headers,
                timeout=120.0  # 分析可能需要较长时间
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "paper_name": paper_name,
                    "analysis": data.get("analysis")
                }
            )
        except Exception as e:
            logger.error(f"Analyze paper error: {e}")
            return ToolResult(success=False, error=str(e))


class GenerateMindmapTool(BaseTool):
    """生成思维导图"""
    
    name = "generate_mindmap"
    description = """为论文生成思维导图，可视化论文结构和关键概念。
返回思维导图数据，可在前端渲染展示。
这是一个耗时操作，可能需要30秒-1分钟。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "paper_name": {
                "type": "string",
                "description": "论文文件名（如 xxx.pdf）"
            }
        },
        "required": ["paper_name"]
    }
    
    async def execute(self, paper_name: str, token: str = None, **kwargs) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = await self.http_client.post(
                f"{MINDMAP_SERVICE_URL}/api/mindmap/generate",
                json={"paper_name": paper_name},
                headers=headers,
                timeout=90.0
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "paper_name": paper_name,
                    "mindmap": data.get("mindmap"),
                    "message": "思维导图已生成，可在前端查看"
                }
            )
        except Exception as e:
            logger.error(f"Generate mindmap error: {e}")
            return ToolResult(success=False, error=str(e))


class ComparePapersTool(BaseTool):
    """对比论文"""
    
    name = "compare_papers"
    description = """对比多篇论文，分析它们的异同。
适合文献综述、方法对比等场景。
需要提供2-5篇论文的文件名。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "paper_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要对比的论文文件名列表（2-5篇）"
            },
            "aspects": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["methodology", "dataset", "results", "contribution"]
                },
                "description": "对比维度（可选）"
            }
        },
        "required": ["paper_names"]
    }
    
    async def execute(
        self,
        paper_names: List[str],
        aspects: Optional[List[str]] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        try:
            if len(paper_names) < 2:
                return ToolResult(success=False, error="至少需要2篇论文进行对比")
            if len(paper_names) > 5:
                return ToolResult(success=False, error="最多支持5篇论文对比")
            
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            payload = {"paper_names": paper_names}
            if aspects:
                payload["aspects"] = aspects
            
            response = await self.http_client.post(
                f"{ANALYSIS_SERVICE_URL}/api/analysis/compare",
                json=payload,
                headers=headers,
                timeout=180.0
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "paper_names": paper_names,
                    "comparison": data.get("comparison")
                }
            )
        except Exception as e:
            logger.error(f"Compare papers error: {e}")
            return ToolResult(success=False, error=str(e))

