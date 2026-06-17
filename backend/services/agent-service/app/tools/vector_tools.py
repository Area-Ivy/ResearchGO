"""
Vector Search Tools - semantic search and paper QA.
"""
from typing import Optional
import logging

from .base import BaseTool, ToolResult
from ..config import VECTOR_SEARCH_SERVICE_URL

logger = logging.getLogger(__name__)


class SemanticSearchTool(BaseTool):
    """Search across uploaded paper chunks."""

    name = "semantic_search"
    description = "Run semantic search across the user's uploaded papers."

    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for semantic retrieval"
            },
            "top_k": {
                "type": "integer",
                "description": "Maximum number of chunks to return"
            }
        },
        "required": ["query"]
    }

    async def execute(
        self,
        query: str,
        top_k: Optional[int] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            payload = {"query": query}
            if top_k is not None:
                payload["top_k"] = top_k

            response = await self.http_client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/search",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                content = item.get("content", "")
                results.append({
                    "content": content[:500] + "..." if len(content) > 500 else content,
                    "paper_name": item.get("paper_name"),
                    "paper_id": item.get("paper_id"),
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
    """Answer questions about a specific uploaded paper."""

    name = "ask_about_paper"
    description = "Use RAG to answer a question about a specific uploaded paper."

    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question to answer about the paper"
            },
            "paper_id": {
                "type": "string",
                "description": "Required stable paper identifier returned by upload/list APIs"
            },
            "paper_name": {
                "type": "string",
                "description": "Legacy fallback field; prefer paper_id"
            }
        },
        "required": ["question"]
    }

    async def execute(
        self,
        question: str,
        paper_id: Optional[str] = None,
        paper_name: Optional[str] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        resolved_paper_id = paper_id or paper_name
        if not resolved_paper_id:
            return ToolResult(
                success=False,
                error="paper_id is required. Use the attached conversation paper_id or search_user_papers first."
            )

        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = await self.http_client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/qa",
                json={"paper_id": resolved_paper_id, "question": question},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult(
                success=True,
                data={
                    "paper_id": resolved_paper_id,
                    "question": question,
                    "answer": data.get("answer"),
                    "sources": data.get("sources", [])
                }
            )
        except Exception as e:
            logger.error(f"Ask paper error: {e}")
            return ToolResult(success=False, error=str(e))
