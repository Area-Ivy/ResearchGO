"""
Literature Search Tools - 文献检索相关工具
"""
from typing import Optional, List
from .base import BaseTool, ToolResult
from ..config import LITERATURE_SERVICE_URL
import logging

logger = logging.getLogger(__name__)


class SearchLiteratureTool(BaseTool):
    """搜索学术文献"""
    
    name = "search_literature"
    description = """搜索学术文献数据库（OpenAlex）。
用于发现新论文、了解研究领域、寻找相关文献。
返回论文列表，包含标题、作者、引用数、摘要等。
当用户想要查找某个主题的论文时使用此工具。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或短语"
            },
            "year_from": {
                "type": "integer",
                "description": "起始年份（可选）"
            },
            "year_to": {
                "type": "integer",
                "description": "结束年份（可选）"
            },
            "open_access": {
                "type": "boolean",
                "description": "是否只返回开放获取论文（可选）"
            },
            "sort": {
                "type": "string",
                "enum": ["relevance", "cited_by_count", "publication_date"],
                "description": "排序方式：relevance（相关性）、cited_by_count（引用数）、publication_date（发表日期）"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量，默认10"
            }
        },
        "required": ["query"]
    }
    
    async def execute(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        open_access: Optional[bool] = None,
        sort: str = "relevance",
        limit: int = 10,
        **kwargs
    ) -> ToolResult:
        try:
            payload = {
                "query": query,
                "sort": sort,
                "per_page": limit
            }
            
            if year_from:
                payload["year_from"] = year_from
            if year_to:
                payload["year_to"] = year_to
            if open_access is not None:
                payload["open_access"] = open_access
            
            response = await self.http_client.post(
                f"{LITERATURE_SERVICE_URL}/api/literature/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # 简化返回结果，只保留关键信息
            results = []
            for work in data.get("results", [])[:limit]:
                results.append({
                    "id": work.get("id"),
                    "title": work.get("title"),
                    "authors": [a.get("name") for a in work.get("authorships", [])[:3]],
                    "year": work.get("publication_year"),
                    "cited_by_count": work.get("cited_by_count"),
                    "abstract": work.get("abstract", "")[:300] + "..." if work.get("abstract") else None,
                    "open_access": work.get("open_access", {}).get("is_oa", False),
                    "doi": work.get("doi")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "total_count": data.get("meta", {}).get("count", 0),
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Search literature error: {e}")
            return ToolResult(success=False, error=str(e))


class GetWorkDetailTool(BaseTool):
    """获取论文详细信息"""
    
    name = "get_work_detail"
    description = """获取论文的详细元信息。
包括完整标题、所有作者、发表期刊、DOI、引用数、摘要等。
当需要了解特定论文的详细信息时使用此工具。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "work_id": {
                "type": "string",
                "description": "OpenAlex Work ID (如 W2963403868) 或完整 URL"
            }
        },
        "required": ["work_id"]
    }
    
    async def execute(self, work_id: str, **kwargs) -> ToolResult:
        try:
            # 处理 work_id 格式
            if work_id.startswith("https://"):
                work_id = work_id.split("/")[-1]
            
            response = await self.http_client.get(
                f"{LITERATURE_SERVICE_URL}/api/literature/works/{work_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "authors": [
                        {
                            "name": a.get("author", {}).get("display_name"),
                            "institution": a.get("institutions", [{}])[0].get("display_name") if a.get("institutions") else None
                        }
                        for a in data.get("authorships", [])
                    ],
                    "year": data.get("publication_year"),
                    "venue": data.get("primary_location", {}).get("source", {}).get("display_name") if data.get("primary_location") else None,
                    "cited_by_count": data.get("cited_by_count"),
                    "abstract": data.get("abstract"),
                    "doi": data.get("doi"),
                    "open_access": data.get("open_access", {}),
                    "concepts": [c.get("display_name") for c in data.get("concepts", [])[:5]]
                }
            )
        except Exception as e:
            logger.error(f"Get work detail error: {e}")
            return ToolResult(success=False, error=str(e))


class GetRelatedWorksTool(BaseTool):
    """获取相关论文"""
    
    name = "get_related_works"
    description = """获取论文的引用关系。
可以获取该论文引用了哪些文献（references），以及被哪些文献引用（cited_by）。
用于追踪研究脉络、发现相关工作。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "work_id": {
                "type": "string",
                "description": "OpenAlex Work ID"
            },
            "relation_type": {
                "type": "string",
                "enum": ["references", "cited_by"],
                "description": "关系类型：references（该论文引用的文献）或 cited_by（引用该论文的文献）"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量，默认10"
            }
        },
        "required": ["work_id"]
    }
    
    async def execute(
        self,
        work_id: str,
        relation_type: str = "cited_by",
        limit: int = 10,
        **kwargs
    ) -> ToolResult:
        try:
            if work_id.startswith("https://"):
                work_id = work_id.split("/")[-1]
            
            response = await self.http_client.get(
                f"{LITERATURE_SERVICE_URL}/api/literature/works/{work_id}/related",
                params={"type": relation_type, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for work in data.get("results", [])[:limit]:
                results.append({
                    "id": work.get("id"),
                    "title": work.get("title"),
                    "year": work.get("publication_year"),
                    "cited_by_count": work.get("cited_by_count")
                })
            
            return ToolResult(
                success=True,
                data={
                    "work_id": work_id,
                    "relation_type": relation_type,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Get related works error: {e}")
            return ToolResult(success=False, error=str(e))


class ExportCitationTool(BaseTool):
    """导出引用格式"""
    
    name = "export_citation"
    description = """导出论文引用格式。
支持 BibTeX、APA、MLA、Chicago、GB/T 7714 等格式。
当用户需要论文的引用格式时使用此工具。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "work_id": {
                "type": "string",
                "description": "OpenAlex Work ID"
            },
            "format": {
                "type": "string",
                "enum": ["bibtex", "apa", "mla", "chicago", "gb_t_7714"],
                "description": "引用格式"
            }
        },
        "required": ["work_id", "format"]
    }
    
    async def execute(self, work_id: str, format: str = "bibtex", **kwargs) -> ToolResult:
        try:
            if work_id.startswith("https://"):
                work_id = work_id.split("/")[-1]
            
            response = await self.http_client.get(
                f"{LITERATURE_SERVICE_URL}/api/literature/works/{work_id}/citation",
                params={"format": format}
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "format": format,
                    "citation": data.get("citation")
                }
            )
        except Exception as e:
            logger.error(f"Export citation error: {e}")
            return ToolResult(success=False, error=str(e))

