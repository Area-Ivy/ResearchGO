"""
Vector Search Tools - 向量搜索相关工具
"""
from typing import Optional, List
from .base import BaseTool, ToolResult
from ..config import VECTOR_SEARCH_SERVICE_URL
import logging

logger = logging.getLogger(__name__)


class SemanticSearchTool(BaseTool):
    """语义搜索"""
    
    name = "semantic_search"
    description = """基于语义的论文内容搜索（向量检索）。
使用自然语言描述来查找相关内容，比关键词搜索更智能。
适合查找"类似概念"或"相关讨论"。
搜索范围是用户已上传并索引的论文。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "自然语言查询，描述你想找的内容"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认5"
            }
        },
        "required": ["query"]
    }
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = await self.http_client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/search",
                json={"query": query, "top_k": top_k},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "content": item.get("content", "")[:500] + "..." if len(item.get("content", "")) > 500 else item.get("content", ""),
                    "paper_name": item.get("paper_name"),
                    "score": item.get("score"),
                    "chunk_index": item.get("chunk_index")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return ToolResult(success=False, error=str(e))


class AskPaperTool(BaseTool):
    """论文问答"""
    
    name = "ask_about_paper"
    description = """针对用户上传的论文提问（RAG模式）。
基于论文内容回答问题，并会标注信息来源。
适合需要从论文中获取具体信息的场景。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "针对论文的问题"
            },
            "paper_name": {
                "type": "string",
                "description": "论文文件名（可选，不指定则搜索所有论文）"
            }
        },
        "required": ["question"]
    }
    
    async def execute(
        self,
        question: str,
        paper_name: Optional[str] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            payload = {"query": question}
            if paper_name:
                payload["paper_name"] = paper_name
            
            response = await self.http_client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/qa",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "question": question,
                    "answer": data.get("answer"),
                    "sources": data.get("sources", [])
                }
            )
        except Exception as e:
            logger.error(f"Ask paper error: {e}")
            return ToolResult(success=False, error=str(e))

