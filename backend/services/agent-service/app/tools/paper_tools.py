"""
Paper Storage Tools - 论文存储相关工具
"""
from typing import Optional, List
from .base import BaseTool, ToolResult
from ..config import PAPER_STORAGE_SERVICE_URL
import logging

logger = logging.getLogger(__name__)


class SearchUserPapersTool(BaseTool):
    """搜索用户论文库"""
    
    name = "search_user_papers"
    description = """在用户已上传的论文库中搜索。
用于查找用户自己收藏/上传的论文。
返回用户论文库中匹配的论文列表。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词（可选，不填则返回所有论文）"
            }
        },
        "required": []
    }
    
    async def execute(self, query: Optional[str] = None, token: str = None, **kwargs) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            params = {}
            if query:
                params["search"] = query
            
            response = await self.http_client.get(
                f"{PAPER_STORAGE_SERVICE_URL}/api/papers/",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper in data.get("papers", data if isinstance(data, list) else []):
                papers.append({
                    "id": paper.get("id"),
                    "filename": paper.get("original_filename") or paper.get("filename"),
                    "title": paper.get("title"),
                    "upload_time": paper.get("upload_time") or paper.get("created_at"),
                    "size": paper.get("file_size")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "count": len(papers),
                    "papers": papers
                }
            )
        except Exception as e:
            logger.error(f"Search user papers error: {e}")
            return ToolResult(success=False, error=str(e))


class GetPaperContentTool(BaseTool):
    """获取论文内容"""
    
    name = "get_paper_content"
    description = """获取论文的文本内容（从已上传的PDF提取）。
用于需要阅读论文原文的场景。
需要先通过 search_user_papers 获取论文ID。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "用户论文库中的论文ID"
            },
            "max_length": {
                "type": "integer",
                "description": "最大返回字符数（可选，默认10000）"
            }
        },
        "required": ["paper_id"]
    }
    
    async def execute(
        self,
        paper_id: str,
        max_length: int = 10000,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # 获取论文详情（包含 object_name）
            response = await self.http_client.get(
                f"{PAPER_STORAGE_SERVICE_URL}/api/papers/{paper_id}",
                headers=headers
            )
            response.raise_for_status()
            paper_data = response.json()
            
            # 这里假设有一个获取内容的端点
            # 实际可能需要调用 vector-search-service 来获取已索引的内容
            return ToolResult(
                success=True,
                data={
                    "paper_id": paper_id,
                    "filename": paper_data.get("original_filename"),
                    "title": paper_data.get("title"),
                    "note": "论文内容需要通过语义搜索或问答功能来查询"
                }
            )
        except Exception as e:
            logger.error(f"Get paper content error: {e}")
            return ToolResult(success=False, error=str(e))

