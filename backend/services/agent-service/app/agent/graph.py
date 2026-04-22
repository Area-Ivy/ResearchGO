"""LangGraph agent implementation for ResearchGO."""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from ..config import (
    ENABLE_CHECKPOINTER,
    ENABLE_CONVERSATION_SUMMARY,
    ENABLE_SEMANTIC_MEMORY,
    MAX_ITERATIONS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SLIDING_WINDOW_SIZE,
    USE_MCP_TOOLS,
)
from ..mcp.client import get_mcp_client
from ..memory.checkpointer import get_checkpointer
from ..memory.semantic_memory import get_semantic_memory_service
from ..memory.sliding_window import SmartSlidingWindow
from ..memory.summary import get_summary_manager
from ..models.state import AgentState, StreamEvent, ToolCall
from ..tools.registry import tool_registry
from ..utils.circuit_breaker import TOOL_ALTERNATIVES, get_breaker_manager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the ResearchGO AI research assistant.
You can search literature, inspect user papers, run vector retrieval, analyze papers, build mindmaps, and compare papers.
Use the available tools when they improve factual accuracy. Prefer attached conversation paper_id values for paper-specific operations.

Available tools:
{tool_descriptions}
{memory_context}
{degraded_tools_notice}
"""

DEGRADED_TOOLS_NOTICE = """
Some local tools are currently degraded or unavailable:
{tools}
Prefer alternatives when possible and explain limitations briefly.
"""


class ResearchAgent:
    def __init__(self):
        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.7,
            "api_key": OPENAI_API_KEY,
            "streaming": True,
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)
        self.mcp_client = get_mcp_client()
        self.tools = tool_registry.get_openai_functions()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.sliding_window = SmartSlidingWindow(window_size=SLIDING_WINDOW_SIZE)
        self.checkpointer = get_checkpointer() if ENABLE_CHECKPOINTER else None
        self.graph = self._build_graph()
        if self.checkpointer:
            self.app = self.graph.compile(checkpointer=self.checkpointer)
            logger.info("Agent compiled with Redis Checkpointer")
        else:
            self.app = self.graph.compile()
            logger.info("Agent compiled without Checkpointer")

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("prepare_context", self._prepare_context_node)
        graph.add_node("refresh_capabilities", self._refresh_capabilities_node)
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("handle_tool_outcome", self._handle_tool_outcome_node)
        graph.add_node("merge_tool_results", self._merge_tool_results_node)
        graph.add_node("handle_degraded", self._handle_degraded_node)
        graph.add_node("handle_error", self._handle_error_node)
        graph.add_node("synthesize_answer", self._synthesize_answer_node)
        graph.add_node("finalize", self._finalize_node)

        graph.set_entry_point("prepare_context")
        graph.add_edge("prepare_context", "refresh_capabilities")
        graph.add_edge("refresh_capabilities", "plan")
        graph.add_conditional_edges(
            "plan",
            self._route_after_plan,
            {
                "execute_tools": "execute_tools",
                "synthesize_answer": "synthesize_answer",
                "finalize": "finalize",
            },
        )
        graph.add_edge("execute_tools", "handle_tool_outcome")
        graph.add_conditional_edges(
            "handle_tool_outcome",
            self._route_tool_outcome,
            {
                "merge_tool_results": "merge_tool_results",
                "handle_degraded": "handle_degraded",
                "handle_error": "handle_error",
            },
        )
        graph.add_edge("merge_tool_results", "plan")
        graph.add_edge("handle_degraded", "plan")
        graph.add_edge("handle_error", "plan")
        graph.add_edge("synthesize_answer", "finalize")
        graph.add_edge("finalize", END)
        return graph

    async def refresh_tools(self, force: bool = False):
        if not USE_MCP_TOOLS:
            return
        remote_tools = await self.mcp_client.list_tools(refresh=force)
        if remote_tools:
            tool_registry.set_remote_tools(remote_tools)
            self.tools = tool_registry.get_openai_functions()
            self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def _prepare_context(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str],
        user_input: str,
        conversation_id: Optional[str],
        token: Optional[str],
        attached_papers: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        summary = ""
        memory_context = ""
        processed_messages = messages

        if ENABLE_CONVERSATION_SUMMARY and conversation_id:
            try:
                summary_manager = get_summary_manager()
                summary_result = await summary_manager.process(
                    messages=messages,
                    conversation_id=conversation_id,
                    window_size=SLIDING_WINDOW_SIZE,
                )
                if summary_result.summary:
                    summary = summary_result.summary
                    processed_messages = summary_result.window_messages
            except Exception as exc:
                logger.warning("Summary processing failed: %s", exc)

        processed_messages, window_stats = self.sliding_window.apply(processed_messages, strategy="hybrid")
        if window_stats.messages_dropped > 0:
            logger.info("Sliding window dropped %s messages", window_stats.messages_dropped)

        if ENABLE_SEMANTIC_MEMORY and user_id and token:
            try:
                semantic_memory = get_semantic_memory_service()
                memory_context = await semantic_memory.get_user_context(
                    user_id=user_id,
                    current_query=user_input,
                    token=token,
                )
            except Exception as exc:
                logger.warning("Semantic memory retrieval failed: %s", exc)

        attached_papers = attached_papers or []
        if attached_papers:
            paper_lines = []
            for paper in attached_papers:
                paper_id = paper.get("paper_id")
                paper_name = paper.get("name", paper_id)
                if paper_id:
                    paper_lines.append(f"- {paper_name} (paper_id: {paper_id})")
            if paper_lines:
                suffix = "\n".join(paper_lines)
                memory_context = (
                    f"{memory_context}\n\n[Current conversation papers]\n"
                    "Prefer these paper_id values when using paper-related tools.\n"
                    f"{suffix}"
                ).strip()

        return processed_messages, summary, memory_context

    def _build_memory_section(self, summary: str, memory_context: str) -> str:
        if not summary and not memory_context:
            return ""

        parts = []
        if summary:
            parts.append(f"[Conversation summary]\n{summary}")
        if memory_context:
            parts.append(f"[Relevant memory]\n{memory_context}")
        return "\n\n" + "\n\n".join(parts)

    def _build_degraded_tools_notice(self) -> str:
        if USE_MCP_TOOLS:
            return ""

        degraded_tools = get_breaker_manager().get_degraded_tools()
        if not degraded_tools:
            return ""

        degraded_info = []
        for tool_name in degraded_tools:
            alt_info = TOOL_ALTERNATIVES.get(tool_name, {})
            alternatives = alt_info.get("alternatives", [])
            if alternatives:
                degraded_info.append(f"- {tool_name}: alternatives -> {', '.join(alternatives)}")
            else:
                degraded_info.append(f"- {tool_name}: no alternatives registered")
        return DEGRADED_TOOLS_NOTICE.format(tools="\n".join(degraded_info))

    def _build_llm_messages(self, processed_messages: List[Dict[str, Any]], summary: str, memory_context: str):
        messages = [
            SystemMessage(
                content=SYSTEM_PROMPT.format(
                    tool_descriptions=tool_registry.get_tool_descriptions(),
                    memory_context=self._build_memory_section(summary, memory_context),
                    degraded_tools_notice=self._build_degraded_tools_notice(),
                )
            )
        ]

        for msg in processed_messages:
            role = msg["role"]
            if role == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif role == "assistant":
                if msg.get("tool_calls"):
                    messages.append(AIMessage(content=msg.get("content", ""), tool_calls=msg["tool_calls"]))
                else:
                    messages.append(AIMessage(content=msg.get("content", "")))
            elif role == "tool":
                messages.append(ToolMessage(content=msg["content"], tool_call_id=msg.get("tool_call_id", "")))

        return messages

    async def _prepare_context_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Prepare context node")
        processed_messages, summary, memory_context = await self._prepare_context(
            messages=state.get("messages", []),
            user_id=state.get("user_id"),
            user_input=state.get("user_input", ""),
            conversation_id=state.get("conversation_id"),
            token=state.get("token"),
            attached_papers=state.get("attached_papers", []),
        )
        return {
            "prepared_messages": processed_messages,
            "summary": summary,
            "memory_context": memory_context,
            "draft_answer": None,
            "tool_outcome": None,
        }

    async def _refresh_capabilities_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Refresh capabilities node")
        await self.refresh_tools()
        return {}

    async def _plan_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Plan node - iteration: %s", state.get("iteration", 0))
        messages = self._build_llm_messages(
            state.get("prepared_messages") or state.get("messages", []),
            state.get("summary", "") or "",
            state.get("memory_context", "") or "",
        )
        response = await self.llm_with_tools.ainvoke(messages)
        thoughts = state.get("thoughts", [])
        tool_calls: List[ToolCall] = []

        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_calls.append(ToolCall(id=tool_call["id"], name=tool_call["name"], arguments=tool_call["args"]))
                thoughts.append(f"Planning tool call: {tool_call['name']}")
            return {
                "messages": [{"role": "assistant", "content": response.content or "", "tool_calls": response.tool_calls}],
                "tool_calls": tool_calls,
                "thoughts": thoughts,
                "should_continue": True,
                "draft_answer": None,
                "final_answer": None,
                "iteration": state.get("iteration", 0) + 1,
            }

        thoughts.append("Planning complete: enough context to answer")
        return {
            "messages": [{"role": "assistant", "content": response.content}],
            "tool_calls": [],
            "thoughts": thoughts,
            "should_continue": False,
            "draft_answer": response.content,
            "iteration": state.get("iteration", 0) + 1,
        }

    async def _execute_tools_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Execute tools node")
        tool_calls = state.get("tool_calls", [])
        thoughts = state.get("thoughts", [])
        new_messages = []
        outcome = "success"

        for tool_call in tool_calls:
            thoughts.append(f"Executing tool: {tool_call.name}")
            arguments = tool_call.arguments.copy()

            if USE_MCP_TOOLS:
                try:
                    result_payload = await self.mcp_client.call_tool(tool_call.name, arguments, token=state.get("token"))
                    structured = result_payload.get("structuredContent", {})
                    if result_payload.get("isError"):
                        if structured.get("status") == "degraded":
                            outcome = "degraded"
                            thoughts.append(f"Tool degraded: {tool_call.name}")
                        else:
                            outcome = "error"
                            thoughts.append(f"Tool failed: {tool_call.name}: {structured.get('error', 'unknown error')}")
                        new_messages.append({
                            "role": "tool",
                            "content": json.dumps(structured, ensure_ascii=False),
                            "tool_call_id": tool_call.id,
                        })
                        tool_call.error = structured.get("error")
                    else:
                        thoughts.append(f"Tool succeeded: {tool_call.name}")
                        new_messages.append({
                            "role": "tool",
                            "content": json.dumps(structured, ensure_ascii=False),
                            "tool_call_id": tool_call.id,
                        })
                        tool_call.result = structured
                    continue
                except Exception as exc:
                    outcome = "error"
                    thoughts.append(f"MCP tool failed: {tool_call.name}: {exc}")
                    new_messages.append({
                        "role": "tool",
                        "content": json.dumps({"error": str(exc)}, ensure_ascii=False),
                        "tool_call_id": tool_call.id,
                    })
                    tool_call.error = str(exc)
                    continue

            tool = tool_registry.get(tool_call.name)
            if not tool:
                outcome = "error"
                error = f"Unknown tool: {tool_call.name}"
                thoughts.append(error)
                new_messages.append({"role": "tool", "content": json.dumps({"error": error}), "tool_call_id": tool_call.id})
                tool_call.error = error
                continue

            if state.get("token"):
                arguments["token"] = state["token"]
            result = await tool(**arguments)
            tool_call.duration_ms = result.duration_ms

            if result.success:
                thoughts.append(f"Tool succeeded: {tool_call.name}")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps(result.data, ensure_ascii=False),
                    "tool_call_id": tool_call.id,
                })
                tool_call.result = result.data
            elif result.is_degraded:
                outcome = "degraded"
                alt_info = TOOL_ALTERNATIVES.get(tool_call.name, {})
                degraded_guidance = {
                    "status": "degraded",
                    "tool": tool_call.name,
                    "message": result.error,
                    "alternatives": alt_info.get("alternatives", []),
                    "hint": alt_info.get("hint", ""),
                }
                thoughts.append(f"Tool degraded: {tool_call.name}")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps(degraded_guidance, ensure_ascii=False),
                    "tool_call_id": tool_call.id,
                })
                tool_call.error = result.error
            else:
                outcome = "error"
                thoughts.append(f"Tool failed: {tool_call.name}: {result.error}")
                new_messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": result.error}, ensure_ascii=False),
                    "tool_call_id": tool_call.id,
                })
                tool_call.error = result.error

        return {
            "messages": new_messages,
            "thoughts": thoughts,
            "tool_outcome": outcome,
        }

    async def _handle_tool_outcome_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Handle tool outcome node: %s", state.get("tool_outcome"))
        return {}

    async def _merge_tool_results_node(self, state: AgentState) -> Dict[str, Any]:
        thoughts = state.get("thoughts", [])
        thoughts.append("Merged tool results into the next planning cycle")
        return {
            "tool_calls": [],
            "should_continue": True,
            "draft_answer": None,
            "tool_outcome": None,
            "thoughts": thoughts,
        }

    async def _handle_degraded_node(self, state: AgentState) -> Dict[str, Any]:
        thoughts = state.get("thoughts", [])
        thoughts.append("Tool degradation detected; replanning with alternatives")
        return {
            "tool_calls": [],
            "should_continue": True,
            "draft_answer": None,
            "tool_outcome": None,
            "thoughts": thoughts,
        }

    async def _handle_error_node(self, state: AgentState) -> Dict[str, Any]:
        thoughts = state.get("thoughts", [])
        thoughts.append("Tool execution error detected; replanning with the latest failure context")
        return {
            "tool_calls": [],
            "should_continue": True,
            "draft_answer": None,
            "tool_outcome": None,
            "thoughts": thoughts,
        }

    async def _synthesize_answer_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Synthesize answer node")
        draft_answer = state.get("draft_answer") or state.get("final_answer")
        if draft_answer:
            return {"final_answer": draft_answer}
        return {"final_answer": "I could not produce a final answer."}

    async def _finalize_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("Finalize node")
        return {"final_answer": state.get("final_answer", "I could not produce a final answer.")}

    def _route_after_plan(self, state: AgentState) -> str:
        iteration = state.get("iteration", 0)
        if iteration >= MAX_ITERATIONS:
            logger.warning("Max iterations (%s) reached", MAX_ITERATIONS)
            return "finalize"
        if state.get("tool_calls"):
            return "execute_tools"
        if state.get("draft_answer"):
            return "synthesize_answer"
        return "finalize"

    def _route_tool_outcome(self, state: AgentState) -> str:
        outcome = state.get("tool_outcome")
        if outcome == "degraded":
            return "handle_degraded"
        if outcome == "error":
            return "handle_error"
        return "merge_tool_results"

    async def _post_process_memories(self, messages: List[Dict[str, Any]], user_id: Optional[str], token: Optional[str]):
        if not ENABLE_SEMANTIC_MEMORY or not user_id or not token:
            return
        try:
            semantic_memory = get_semantic_memory_service()
            stored_count = await semantic_memory.process_and_store(messages=messages, user_id=user_id, token=token)
            if stored_count > 0:
                logger.info("Post-process stored %s memories for user %s", stored_count, user_id)
        except Exception as exc:
            logger.warning("Post-process memory storage failed: %s", exc)

    def _build_initial_state(
        self,
        user_input: str,
        user_id: Optional[str],
        token: Optional[str],
        conversation_history: Optional[List[dict]],
        conversation_id: Optional[str],
        attached_papers: Optional[List[Dict[str, str]]],
    ) -> Dict[str, Any]:
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "user_id": user_id,
            "token": token,
            "conversation_id": conversation_id,
            "attached_papers": attached_papers or [],
            "tool_calls": [],
            "iteration": 0,
            "should_continue": True,
            "final_answer": None,
            "draft_answer": None,
            "error": None,
            "thoughts": [],
            "prepared_messages": [],
            "summary": None,
            "memory_context": None,
            "tool_outcome": None,
        }
        initial_state["messages"].append({"role": "user", "content": user_input})
        return initial_state

    async def run(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        conversation_id: Optional[str] = None,
        attached_papers: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        initial_state = self._build_initial_state(
            user_input=user_input,
            user_id=user_id,
            token=token,
            conversation_history=conversation_history,
            conversation_id=conversation_id,
            attached_papers=attached_papers,
        )

        config = {}
        if self.checkpointer and conversation_id:
            config = {"configurable": {"thread_id": f"conv_{conversation_id}"}}

        final_state = await self.app.ainvoke(initial_state, config=config)
        await self._post_process_memories(final_state.get("messages", []), user_id=user_id, token=token)
        return {
            "answer": final_state.get("final_answer", ""),
            "thoughts": final_state.get("thoughts", []),
            "tool_calls": final_state.get("tool_calls", []),
        }

    async def run_stream(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        conversation_id: Optional[str] = None,
        attached_papers: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        initial_state = self._build_initial_state(
            user_input=user_input,
            user_id=user_id,
            token=token,
            conversation_history=conversation_history,
            conversation_id=conversation_id,
            attached_papers=attached_papers,
        )

        config = {}
        if self.checkpointer and conversation_id:
            config = {"configurable": {"thread_id": f"conv_{conversation_id}"}}

        last_thoughts_count = 0
        final_messages: List[Dict[str, Any]] = []
        final_answer_chunks: List[str] = []
        tracked_nodes = {
            "prepare_context",
            "refresh_capabilities",
            "plan",
            "execute_tools",
            "handle_tool_outcome",
            "merge_tool_results",
            "handle_degraded",
            "handle_error",
            "synthesize_answer",
            "finalize",
        }

        async for event in self.app.astream_events(initial_state, config=config, version="v2"):
            event_type = event.get("event")
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and getattr(chunk, "content", None):
                    final_answer_chunks.append(chunk.content)
                    yield StreamEvent(event="token", data=chunk.content)
            elif event_type == "on_chain_start":
                node_name = event.get("name", "")
                if node_name in tracked_nodes:
                    yield StreamEvent(event="node_start", data=node_name)
            elif event_type == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    if output.get("messages"):
                        final_messages.extend(output["messages"])
                    thoughts = output.get("thoughts", [])
                    if len(thoughts) > last_thoughts_count:
                        for thought in thoughts[last_thoughts_count:]:
                            yield StreamEvent(event="thinking", data=thought)
                        last_thoughts_count = len(thoughts)
                    if output.get("tool_calls"):
                        for tool_call in output["tool_calls"]:
                            yield StreamEvent(event="tool_call", data={"name": tool_call.name, "arguments": tool_call.arguments})
                    for msg in output.get("messages", []):
                        if msg.get("role") == "tool":
                            try:
                                tool_data = json.loads(msg.get("content", "{}"))
                                if tool_data.get("results") and isinstance(tool_data["results"], list):
                                    if tool_data["results"] and "title" in tool_data["results"][0]:
                                        yield StreamEvent(event="papers", data={
                                            "query": tool_data.get("query", ""),
                                            "total": tool_data.get("total_count", len(tool_data["results"])),
                                            "papers": tool_data["results"],
                                        })
                            except Exception:
                                pass
                    if output.get("final_answer"):
                        if not final_answer_chunks:
                            yield StreamEvent(event="answer", data=output["final_answer"])
                        else:
                            yield StreamEvent(event="answer_end", data=None)

        await self._post_process_memories(initial_state["messages"] + final_messages, user_id=user_id, token=token)
        yield StreamEvent(event="done", data=None)


_agent_instance: Optional[ResearchAgent] = None


def get_agent() -> ResearchAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ResearchAgent()
    return _agent_instance
