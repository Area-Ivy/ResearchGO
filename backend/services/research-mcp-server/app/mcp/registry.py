from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from pydantic import BaseModel

from ..utils.circuit_breaker import get_breaker, get_breaker_manager, get_degraded_response
from ..utils.service_discovery import get_service_discovery


class McpToolResult(BaseModel):
    content: List[Dict[str, Any]]
    structuredContent: Dict[str, Any]
    isError: bool = False


class McpTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolContext(BaseModel):
    token: Optional[str] = None


class ToolDefinition:
    def __init__(self, tool: McpTool, handler: Callable[[Dict[str, Any], ToolContext], Awaitable[McpToolResult]]):
        self.tool = tool
        self.handler = handler


class ResearchMcpRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_defaults()

    def _register(self, tool: McpTool, handler: Callable[[Dict[str, Any], ToolContext], Awaitable[McpToolResult]]):
        self._tools[tool.name] = ToolDefinition(tool=tool, handler=handler)

    def list_tools(self) -> List[McpTool]:
        return [definition.tool for definition in self._tools.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        definition = self._tools.get(name)
        if not definition:
            return McpToolResult(
                content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                structuredContent={"error": f"Unknown tool: {name}"},
                isError=True,
            )
        breaker = get_breaker(name)
        if not await breaker.can_execute():
            degraded = get_degraded_response(name, breaker)
            return McpToolResult(
                content=[{"type": "text", "text": degraded["error"]}],
                structuredContent=degraded,
                isError=True,
            )
        try:
            result = await definition.handler(arguments, context)
            if result.isError:
                await breaker.record_failure(result.structuredContent.get("error"))
            else:
                await breaker.record_success()
            return result
        except Exception as exc:
            await breaker.record_failure(str(exc))
            raise

    def _register_defaults(self):
        self._register(
            McpTool(
                name="search_literature",
                description="Search literature from OpenAlex and return lightweight paper metadata.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "year_from": {"type": "integer"},
                        "year_to": {"type": "integer"},
                        "open_access": {"type": "boolean"},
                        "sort": {"type": "string", "enum": ["relevance", "cited_by_count", "publication_date"]},
                        "limit": {"type": "integer"}
                    },
                    "required": ["query"]
                },
            ),
            self._search_literature,
        )
        self._register(
            McpTool(
                name="get_work_detail",
                description="Get detailed metadata for a specific OpenAlex work.",
                inputSchema={"type": "object", "properties": {"work_id": {"type": "string"}}, "required": ["work_id"]},
            ),
            self._get_work_detail,
        )
        self._register(
            McpTool(
                name="get_related_works",
                description="Get references or citing works for an OpenAlex paper.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_id": {"type": "string"},
                        "relation_type": {"type": "string", "enum": ["references", "cited_by"]},
                        "limit": {"type": "integer"}
                    },
                    "required": ["work_id"]
                },
            ),
            self._get_related_works,
        )
        self._register(
            McpTool(
                name="export_citation",
                description="Export a citation for an OpenAlex paper in a standard format.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_id": {"type": "string"},
                        "format": {"type": "string", "enum": ["bibtex", "apa", "mla", "chicago", "gb_t_7714"]}
                    },
                    "required": ["work_id", "format"]
                },
            ),
            self._export_citation,
        )
        self._register(
            McpTool(
                name="search_user_papers",
                description="Search papers uploaded by the current user.",
                inputSchema={"type": "object", "properties": {"query": {"type": "string"}}},
            ),
            self._search_user_papers,
        )
        self._register(
            McpTool(
                name="get_paper_content",
                description="Fetch metadata for a specific user paper and explain how to retrieve content.",
                inputSchema={
                    "type": "object",
                    "properties": {"paper_id": {"type": "string"}, "max_length": {"type": "integer"}},
                    "required": ["paper_id"]
                },
            ),
            self._get_paper_content,
        )
        self._register(
            McpTool(
                name="semantic_search",
                description="Run semantic search across uploaded user papers.",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}},
                    "required": ["query"]
                },
            ),
            self._semantic_search,
        )
        self._register(
            McpTool(
                name="ask_about_paper",
                description="Answer a question about one uploaded paper using RAG.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "paper_id": {"type": "string"},
                        "paper_name": {"type": "string"}
                    },
                    "required": ["question"]
                },
            ),
            self._ask_about_paper,
        )
        self._register(
            McpTool(
                name="analyze_paper",
                description="Analyze a user paper and return a structured summary.",
                inputSchema={"type": "object", "properties": {"paper_id": {"type": "string"}, "paper_name": {"type": "string"}}},
            ),
            self._analyze_paper,
        )
        self._register(
            McpTool(
                name="generate_mindmap",
                description="Generate a mindmap for a user paper.",
                inputSchema={"type": "object", "properties": {"paper_id": {"type": "string"}, "paper_name": {"type": "string"}}},
            ),
            self._generate_mindmap,
        )
        self._register(
            McpTool(
                name="compare_papers",
                description="Compare multiple papers across selected aspects.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_names": {"type": "array", "items": {"type": "string"}},
                        "aspects": {"type": "array", "items": {"type": "string", "enum": ["methodology", "dataset", "results", "contribution"]}}
                    },
                    "required": ["paper_names"]
                },
            ),
            self._compare_papers,
        )

    async def _request(self, method: str, service_name: str, path: str, *, context: ToolContext, json_body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, timeout: float = 60.0) -> Dict[str, Any]:
        sd = get_service_discovery()
        base_url = await sd.get_url(service_name)
        headers = {}
        if context.token:
            headers["Authorization"] = f"Bearer {context.token}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, f"{base_url}{path}", json=json_body, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _ok(data: Dict[str, Any]) -> McpToolResult:
        return McpToolResult(content=[{"type": "text", "text": str(data)}], structuredContent=data)

    @staticmethod
    def _error(message: str) -> McpToolResult:
        return McpToolResult(content=[{"type": "text", "text": message}], structuredContent={"error": message}, isError=True)

    async def _search_literature(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        payload = {"query": arguments["query"], "sort": arguments.get("sort", "relevance"), "per_page": arguments.get("limit", 10)}
        for key in ("year_from", "year_to", "open_access"):
            if key in arguments and arguments[key] is not None:
                payload[key] = arguments[key]
        data = await self._request("POST", "literature-search-service", "/api/literature/search", context=context, json_body=payload)
        results = []
        for work in data.get("results", [])[: payload["per_page"]]:
            results.append({
                "id": work.get("id"),
                "title": work.get("title"),
                "authors": [a.get("name") for a in work.get("authorships", [])[:3]],
                "year": work.get("publication_year"),
                "cited_by_count": work.get("cited_by_count"),
                "abstract": (work.get("abstract", "")[:300] + "...") if work.get("abstract") else None,
                "open_access": work.get("open_access", {}).get("is_oa", False),
                "doi": work.get("doi"),
            })
        return self._ok({"query": arguments["query"], "total_count": data.get("meta", {}).get("count", 0), "results": results})

    async def _get_work_detail(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        work_id = arguments["work_id"].split("/")[-1]
        data = await self._request("GET", "literature-search-service", f"/api/literature/works/{work_id}", context=context)
        return self._ok({
            "id": data.get("id"),
            "title": data.get("title"),
            "authors": [{"name": a.get("author", {}).get("display_name"), "institution": a.get("institutions", [{}])[0].get("display_name") if a.get("institutions") else None} for a in data.get("authorships", [])],
            "year": data.get("publication_year"),
            "venue": data.get("primary_location", {}).get("source", {}).get("display_name") if data.get("primary_location") else None,
            "cited_by_count": data.get("cited_by_count"),
            "abstract": data.get("abstract"),
            "doi": data.get("doi"),
            "open_access": data.get("open_access", {}),
            "concepts": [c.get("display_name") for c in data.get("concepts", [])[:5]],
        })

    async def _get_related_works(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        work_id = arguments["work_id"].split("/")[-1]
        relation_type = arguments.get("relation_type", "cited_by")
        limit = arguments.get("limit", 10)
        data = await self._request("GET", "literature-search-service", f"/api/literature/works/{work_id}/related", context=context, params={"type": relation_type, "limit": limit})
        results = [{"id": work.get("id"), "title": work.get("title"), "year": work.get("publication_year"), "cited_by_count": work.get("cited_by_count")} for work in data.get("results", [])[:limit]]
        return self._ok({"work_id": work_id, "relation_type": relation_type, "results": results})

    async def _export_citation(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        work_id = arguments["work_id"].split("/")[-1]
        citation_format = arguments["format"]
        data = await self._request("GET", "literature-search-service", f"/api/literature/works/{work_id}/citation", context=context, params={"format": citation_format})
        return self._ok({"format": citation_format, "citation": data.get("citation")})

    async def _search_user_papers(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        params = {}
        if arguments.get("query"):
            params["search"] = arguments["query"]
        data = await self._request("GET", "paper-storage-service", "/api/papers/", context=context, params=params)
        papers = []
        for paper in data.get("papers", data if isinstance(data, list) else []):
            papers.append({"id": paper.get("id"), "filename": paper.get("original_filename") or paper.get("filename"), "title": paper.get("title"), "upload_time": paper.get("upload_time") or paper.get("created_at"), "size": paper.get("file_size")})
        return self._ok({"query": arguments.get("query"), "count": len(papers), "papers": papers})

    async def _get_paper_content(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        paper_id = arguments["paper_id"]
        data = await self._request("GET", "paper-storage-service", f"/api/papers/{paper_id}", context=context)
        return self._ok({"paper_id": paper_id, "filename": data.get("original_filename"), "title": data.get("title"), "note": "Use semantic_search or ask_about_paper to retrieve grounded content."})

    async def _semantic_search(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        top_k = arguments.get("top_k", 5)
        data = await self._request("POST", "vector-search-service", "/api/vector/search", context=context, json_body={"query": arguments["query"], "top_k": top_k})
        results = []
        for item in data.get("results", []):
            content = item.get("content", "")
            results.append({"content": content[:500] + "..." if len(content) > 500 else content, "paper_name": item.get("paper_name"), "paper_id": item.get("paper_id"), "score": item.get("score"), "chunk_index": item.get("chunk_index")})
        return self._ok({"query": arguments["query"], "results": results})

    async def _ask_about_paper(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        paper_id = arguments.get("paper_id") or arguments.get("paper_name")
        if not paper_id:
            return self._error("paper_id is required. Use the attached conversation paper_id or search_user_papers first.")
        data = await self._request("POST", "vector-search-service", "/api/vector/qa", context=context, json_body={"paper_id": paper_id, "question": arguments["question"]})
        return self._ok({"paper_id": paper_id, "question": arguments["question"], "answer": data.get("answer"), "sources": data.get("sources", [])})

    async def _analyze_paper(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        paper_id = arguments.get("paper_id") or arguments.get("paper_name")
        if not paper_id:
            return self._error("paper_id is required for paper analysis")
        data = await self._request("POST", "analysis-service", "/api/analysis/analyze", context=context, json_body={"object_name": paper_id}, timeout=120.0)
        return self._ok({"paper_id": paper_id, "analysis": data.get("analysis")})

    async def _generate_mindmap(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        paper_id = arguments.get("paper_id") or arguments.get("paper_name")
        if not paper_id:
            return self._error("paper_id is required for mindmap generation")
        data = await self._request("POST", "mindmap-service", "/api/mindmap/generate", context=context, json_body={"object_name": paper_id}, timeout=90.0)
        return self._ok({"paper_id": paper_id, "mindmap": data.get("mindmap"), "message": "Mindmap generated successfully."})

    async def _compare_papers(self, arguments: Dict[str, Any], context: ToolContext) -> McpToolResult:
        paper_names = arguments.get("paper_names") or []
        if len(paper_names) < 2:
            return self._error("At least two papers are required for comparison")
        if len(paper_names) > 5:
            return self._error("At most five papers can be compared at once")
        payload = {"paper_names": paper_names}
        if arguments.get("aspects"):
            payload["aspects"] = arguments["aspects"]
        data = await self._request("POST", "analysis-service", "/api/analysis/compare", context=context, json_body=payload, timeout=180.0)
        return self._ok({"paper_names": paper_names, "comparison": data.get("comparison")})


_registry: Optional[ResearchMcpRegistry] = None


def get_registry() -> ResearchMcpRegistry:
    global _registry
    if _registry is None:
        _registry = ResearchMcpRegistry()
    return _registry
