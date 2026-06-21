"""
Analysis Tools - paper analysis and mindmap generation.
"""
from typing import Optional, List
import logging

from .base import BaseTool, ToolResult
from ..config import ANALYSIS_SERVICE_URL, MINDMAP_SERVICE_URL

logger = logging.getLogger(__name__)


def _resolve_paper_ref(paper_id: Optional[str], paper_name: Optional[str]) -> Optional[str]:
    """Prefer stable paper_id/object_name, but keep paper_name as fallback for compatibility."""
    return paper_id or paper_name


class AnalyzePaperTool(BaseTool):
    """Analyze an uploaded paper."""

    name = "analyze_paper"
    description = "Analyze a user paper and return a structured summary."

    parameters = {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "Preferred stable paper identifier returned by upload/list APIs"
            },
            "paper_name": {
                "type": "string",
                "description": "Legacy fallback paper reference"
            }
        }
    }

    async def execute(
        self,
        paper_id: Optional[str] = None,
        paper_name: Optional[str] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        object_name = _resolve_paper_ref(paper_id, paper_name)
        if not object_name:
            return ToolResult(success=False, error="paper_id is required for paper analysis")

        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = await self.http_client.post(
                f"{ANALYSIS_SERVICE_URL}/api/analysis/generate",
                json={"object_name": object_name},
                headers=headers,
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult(
                success=True,
                data={
                    "paper_id": object_name,
                    "analysis": data.get("analysis")
                }
            )
        except Exception as e:
            logger.error(f"Analyze paper error: {e}")
            return ToolResult(success=False, error=str(e))


class GenerateMindmapTool(BaseTool):
    """Generate a mindmap from an uploaded paper."""

    name = "generate_mindmap"
    description = "Generate a mindmap for a user paper."

    parameters = {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "Preferred stable paper identifier returned by upload/list APIs"
            },
            "paper_name": {
                "type": "string",
                "description": "Legacy fallback paper reference"
            }
        }
    }

    async def execute(
        self,
        paper_id: Optional[str] = None,
        paper_name: Optional[str] = None,
        token: str = None,
        **kwargs
    ) -> ToolResult:
        object_name = _resolve_paper_ref(paper_id, paper_name)
        if not object_name:
            return ToolResult(success=False, error="paper_id is required for mindmap generation")

        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = await self.http_client.post(
                f"{MINDMAP_SERVICE_URL}/api/mindmap/generate",
                json={"object_name": object_name},
                headers=headers,
                timeout=90.0
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult(
                success=True,
                data={
                    "paper_id": object_name,
                    "mindmap_data": data.get("mindmap_data") or data.get("mindmap"),
                    "message": "Mindmap generated successfully. Do not output any image URLs, markdown links, placeholder links, or download links. The UI will render the visual mindmap directly."
                }
            )
        except Exception as e:
            logger.error(f"Generate mindmap error: {e}")
            return ToolResult(success=False, error=str(e))


class ComparePapersTool(BaseTool):
    """Compare multiple papers."""

    name = "compare_papers"
    description = "Compare multiple papers across selected aspects."

    parameters = {
        "type": "object",
        "properties": {
            "paper_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Two to five paper names for comparison"
            },
            "aspects": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["methodology", "dataset", "results", "contribution"]
                },
                "description": "Optional aspects to compare"
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
                return ToolResult(success=False, error="At least two papers are required for comparison")
            if len(paper_names) > 5:
                return ToolResult(success=False, error="At most five papers can be compared at once")

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
