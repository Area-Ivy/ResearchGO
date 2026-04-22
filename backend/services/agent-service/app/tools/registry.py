"""
Tool registry for local and MCP-backed tools.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .analysis_tools import AnalyzePaperTool, ComparePapersTool, GenerateMindmapTool
from .base import BaseTool
from .literature_tools import (
    ExportCitationTool,
    GetRelatedWorksTool,
    GetWorkDetailTool,
    SearchLiteratureTool,
)
from .paper_tools import GetPaperContentTool, SearchUserPapersTool
from .vector_tools import AskPaperTool, SemanticSearchTool


class ToolRegistry:
    """Keeps local tool implementations and optional remote MCP tool schemas."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._remote_tools: List[Dict[str, Any]] = []
        self._register_default_tools()

    def _register_default_tools(self):
        default_tools = [
            SearchLiteratureTool(),
            GetWorkDetailTool(),
            GetRelatedWorksTool(),
            ExportCitationTool(),
            SearchUserPapersTool(),
            GetPaperContentTool(),
            SemanticSearchTool(),
            AskPaperTool(),
            AnalyzePaperTool(),
            GenerateMindmapTool(),
            ComparePapersTool(),
        ]
        for tool in default_tools:
            self.register(tool)

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def set_remote_tools(self, tools: List[Dict[str, Any]]):
        self._remote_tools = tools or []

    def clear_remote_tools(self):
        self._remote_tools = []

    def has_remote_tools(self) -> bool:
        return bool(self._remote_tools)

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all(self) -> List[Any]:
        if self._remote_tools:
            return self._remote_tools
        return list(self._tools.values())

    def get_openai_functions(self) -> List[dict]:
        if self._remote_tools:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
                    },
                }
                for tool in self._remote_tools
            ]
        return [tool.to_openai_function() for tool in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        if self._remote_tools:
            return [tool["name"] for tool in self._remote_tools]
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> str:
        if self._remote_tools:
            return "\n".join(f"- {tool['name']}: {tool['description']}" for tool in self._remote_tools)
        return "\n".join(
            f"- {tool.name}: {tool.description.split('.')[0]}" for tool in self._tools.values()
        )

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        status = {}
        for name, tool in self._tools.items():
            circuit_status = tool.get_circuit_status()
            if circuit_status:
                status[name] = circuit_status
        return status

    def get_degraded_tools(self) -> List[str]:
        degraded = []
        for name, tool in self._tools.items():
            if tool.breaker and tool.breaker.is_open:
                degraded.append(name)
        return degraded


tool_registry = ToolRegistry()


def get_all_tools() -> List[Any]:
    return tool_registry.get_all()


def get_circuit_status() -> Dict[str, Any]:
    return tool_registry.get_circuit_breaker_status()


def get_degraded_tools() -> List[str]:
    return tool_registry.get_degraded_tools()
