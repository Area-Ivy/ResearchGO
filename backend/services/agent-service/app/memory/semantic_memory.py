"""Markdown-backed semantic memory service for ResearchGO."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import (
    ENABLE_SEMANTIC_MEMORY,
    MEMORY_IMPORTANCE_THRESHOLD,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SEMANTIC_MEMORY_DIR,
    SEMANTIC_MEMORY_TOP_K,
)

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    USER_PREFERENCE = "user_preference"
    RESEARCH_INTEREST = "research_interest"
    KEY_FINDING = "key_finding"
    TASK_CONTEXT = "task_context"
    FEEDBACK = "feedback"


@dataclass
class Memory:
    id: str
    user_id: str
    content: str
    memory_type: MemoryType
    importance: float
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0


@dataclass
class MemoryExtractionResult:
    memories: List[Dict[str, Any]]
    has_important_info: bool


SECTION_TITLES = {
    MemoryType.USER_PREFERENCE: "User Preferences",
    MemoryType.RESEARCH_INTEREST: "Research Interests",
    MemoryType.KEY_FINDING: "Key Findings",
    MemoryType.TASK_CONTEXT: "Task Context",
    MemoryType.FEEDBACK: "Feedback",
}

SECTION_ORDER = [
    MemoryType.RESEARCH_INTEREST,
    MemoryType.USER_PREFERENCE,
    MemoryType.TASK_CONTEXT,
    MemoryType.KEY_FINDING,
    MemoryType.FEEDBACK,
]

ENTRY_RE = re.compile(
    r"^- \[(?P<created_at>[^\]|]+) \| importance=(?P<importance>[0-9.]+)(?: \| metadata=(?P<metadata>.+?))?\] (?P<content>.+)$"
)
TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")


class SemanticMemoryService:
    """Persist long-term memory as per-user markdown files."""

    def __init__(
        self,
        top_k: int = SEMANTIC_MEMORY_TOP_K,
        importance_threshold: float = MEMORY_IMPORTANCE_THRESHOLD,
        memory_dir: str = SEMANTIC_MEMORY_DIR,
    ):
        self.top_k = top_k
        self.importance_threshold = importance_threshold
        self.memory_dir = Path(memory_dir)
        self._ensure_memory_dir()

        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.2,
            "api_key": OPENAI_API_KEY,
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        self.llm = ChatOpenAI(**llm_kwargs)

    def _ensure_memory_dir(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _safe_user_id(self, user_id: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", user_id)

    def _memory_path(self, user_id: str) -> Path:
        return self.memory_dir / f"{self._safe_user_id(user_id)}.md"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _make_memory_id(self, user_id: str, memory_type: MemoryType, content: str) -> str:
        normalized = self._normalize_text(content)
        return f"{self._safe_user_id(user_id)}:{memory_type.value}:{abs(hash(normalized))}"

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        if not metadata:
            return ""
        return json.dumps(metadata, ensure_ascii=True, sort_keys=True)

    def _parse_metadata(self, raw: Optional[str]) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            logger.warning("Failed to parse memory metadata: %s", raw)
            return {}

    def _load_memories(self, user_id: str) -> List[Memory]:
        path = self._memory_path(user_id)
        if not path.exists():
            return []

        current_type: Optional[MemoryType] = None
        memories: List[Memory] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("## "):
                title = line[3:].strip()
                current_type = next(
                    (memory_type for memory_type, section_title in SECTION_TITLES.items() if section_title == title),
                    None,
                )
                continue
            if not current_type or not line.startswith("- "):
                continue
            match = ENTRY_RE.match(line)
            if not match:
                continue
            metadata = self._parse_metadata(match.group("metadata"))
            content = match.group("content").strip()
            memories.append(
                Memory(
                    id=self._make_memory_id(user_id, current_type, content),
                    user_id=user_id,
                    content=content,
                    memory_type=current_type,
                    importance=float(match.group("importance")),
                    created_at=match.group("created_at"),
                    metadata=metadata,
                )
            )
        return memories

    def _render_markdown(self, user_id: str, memories: List[Memory]) -> str:
        lines = [
            "# Semantic Memory",
            "",
            f"- User ID: {user_id}",
            f"- Updated At: {self._now_iso()}",
            f"- Total Entries: {len(memories)}",
            "",
        ]

        grouped: Dict[MemoryType, List[Memory]] = {memory_type: [] for memory_type in SECTION_ORDER}
        for memory in memories:
            grouped.setdefault(memory.memory_type, []).append(memory)

        for memory_type in SECTION_ORDER:
            lines.append(f"## {SECTION_TITLES[memory_type]}")
            entries = sorted(
                grouped.get(memory_type, []),
                key=lambda item: (-item.importance, item.created_at, item.content.lower()),
            )
            if not entries:
                lines.append("- None")
                lines.append("")
                continue
            for memory in entries:
                metadata = self._serialize_metadata(memory.metadata)
                meta_suffix = f" | metadata={metadata}" if metadata else ""
                lines.append(
                    f"- [{memory.created_at} | importance={memory.importance:.2f}{meta_suffix}] {memory.content}"
                )
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    def _save_memories(self, user_id: str, memories: List[Memory]) -> None:
        self._ensure_memory_dir()
        rendered = self._render_markdown(user_id, memories)
        self._memory_path(user_id).write_text(rendered, encoding="utf-8")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end >= start:
            cleaned = cleaned[start : end + 1]
        return json.loads(cleaned)

    def _score_memory(self, query: str, memory: Memory) -> float:
        query_tokens = set(TOKEN_RE.findall(query.lower()))
        content_tokens = set(TOKEN_RE.findall(memory.content.lower()))
        overlap = len(query_tokens & content_tokens)
        coverage = overlap / max(len(query_tokens), 1)
        metadata_text = " ".join(str(value) for value in memory.metadata.values()).lower()
        metadata_bonus = 0.05 if metadata_text and any(token in metadata_text for token in query_tokens) else 0.0
        return round((memory.importance * 0.6) + (coverage * 0.35) + metadata_bonus, 4)

    def _merge_memory(self, memories: List[Memory], incoming: Memory) -> Tuple[List[Memory], bool]:
        incoming_key = (incoming.memory_type, self._normalize_text(incoming.content))
        for index, existing in enumerate(memories):
            existing_key = (existing.memory_type, self._normalize_text(existing.content))
            if existing_key != incoming_key:
                continue
            merged_metadata = {**existing.metadata, **incoming.metadata}
            memories[index] = Memory(
                id=existing.id,
                user_id=existing.user_id,
                content=existing.content,
                memory_type=existing.memory_type,
                importance=max(existing.importance, incoming.importance),
                created_at=existing.created_at,
                metadata=merged_metadata,
                relevance_score=existing.relevance_score,
            )
            return memories, False
        memories.append(incoming)
        return memories, True

    async def extract_memories(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
    ) -> MemoryExtractionResult:
        if not ENABLE_SEMANTIC_MEMORY:
            return MemoryExtractionResult(memories=[], has_important_info=False)

        recent_messages = messages[-10:] if len(messages) > 10 else messages
        conversation_lines: List[str] = []
        for message in recent_messages:
            role = message.get("role", "unknown")
            content = str(message.get("content", "")).strip()
            if role not in {"user", "assistant"} or not content:
                continue
            conversation_lines.append(f"{role}: {content[:500]}")

        if not conversation_lines:
            return MemoryExtractionResult(memories=[], has_important_info=False)

        conversation_text = "\n".join(conversation_lines)
        prompt = f"""Review the conversation below and extract only long-lived memory worth saving for future chats.

User ID: {user_id}
Conversation:
{conversation_text}

Extract only information that is stable or repeatedly useful, such as:
- user_preference: answer style, habits, formatting preferences
- research_interest: recurring topics, domains, methods, datasets
- key_finding: durable facts established during the discussion
- task_context: ongoing project context that may matter in future turns
- feedback: explicit feedback on what the assistant should keep doing or avoid

Rules:
- Ignore one-off small talk and transient logistics.
- Keep each memory concise and standalone.
- Use importance between 0.0 and 1.0.
- Return valid JSON only.

Expected format:
{{
  "memories": [
    {{
      "type": "research_interest",
      "content": "User is focused on retrieval-augmented generation evaluation.",
      "importance": 0.84
    }}
  ],
  "has_important_info": true
}}

If nothing is worth storing, return:
{{"memories": [], "has_important_info": false}}"""

        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You extract durable conversational memory. "
                            "Return compact JSON only, with no markdown wrapper."
                        )
                    ),
                    HumanMessage(content=prompt),
                ]
            )
            result = self._extract_json(str(response.content))
            memories = []
            for memory in result.get("memories", []):
                memory_type = str(memory.get("type", "")).strip()
                if memory_type not in {item.value for item in MemoryType}:
                    continue
                importance = float(memory.get("importance", 0.0))
                if importance < self.importance_threshold:
                    continue
                content = str(memory.get("content", "")).strip()
                if not content:
                    continue
                memories.append(
                    {
                        "type": memory_type,
                        "content": content,
                        "importance": max(0.0, min(1.0, importance)),
                    }
                )
            return MemoryExtractionResult(
                memories=memories,
                has_important_info=bool(memories) and bool(result.get("has_important_info", True)),
            )
        except Exception as exc:
            logger.warning("Memory extraction failed for user %s: %s", user_id, exc)
            return MemoryExtractionResult(memories=[], has_important_info=False)

    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float,
        token: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not ENABLE_SEMANTIC_MEMORY:
            return False

        try:
            memories = self._load_memories(user_id)
            incoming = Memory(
                id=self._make_memory_id(user_id, memory_type, content),
                user_id=user_id,
                content=content.strip(),
                memory_type=memory_type,
                importance=max(0.0, min(1.0, importance)),
                created_at=self._now_iso(),
                metadata=metadata or {},
            )
            memories, created = self._merge_memory(memories, incoming)
            self._save_memories(user_id, memories)
            logger.info("%s semantic memory for user %s: %s", "Stored" if created else "Updated", user_id, memory_type.value)
            return True
        except Exception as exc:
            logger.error("Failed to store semantic memory for user %s: %s", user_id, exc)
            return False

    async def recall_relevant(
        self,
        user_id: str,
        query: str,
        token: Optional[str],
        top_k: Optional[int] = None,
    ) -> List[Memory]:
        if not ENABLE_SEMANTIC_MEMORY:
            return []

        memories = self._load_memories(user_id)
        if not memories:
            return []

        for memory in memories:
            memory.relevance_score = self._score_memory(query, memory)

        limit = top_k or self.top_k
        ranked = sorted(
            (memory for memory in memories if memory.relevance_score > 0 or memory.importance >= self.importance_threshold),
            key=lambda item: (-item.relevance_score, -item.importance, item.created_at),
        )
        return ranked[:limit]

    async def get_user_context(
        self,
        user_id: str,
        current_query: str,
        token: Optional[str],
    ) -> str:
        memories = await self.recall_relevant(user_id=user_id, query=current_query, token=token)
        if not memories:
            return ""

        grouped: Dict[MemoryType, List[str]] = {memory_type: [] for memory_type in SECTION_ORDER}
        for memory in memories:
            grouped.setdefault(memory.memory_type, []).append(memory.content)

        parts: List[str] = []
        for memory_type in SECTION_ORDER:
            entries = grouped.get(memory_type, [])
            if not entries:
                continue
            label = SECTION_TITLES[memory_type]
            bullet_lines = "\n".join(f"- {entry}" for entry in entries[:3])
            parts.append(f"{label}:\n{bullet_lines}")
        return "\n\n".join(parts)

    async def process_and_store(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        token: Optional[str],
    ) -> int:
        if not ENABLE_SEMANTIC_MEMORY:
            return 0

        extraction = await self.extract_memories(messages=messages, user_id=user_id)
        if not extraction.has_important_info:
            return 0

        stored_count = 0
        for memory in extraction.memories:
            try:
                success = await self.store_memory(
                    user_id=user_id,
                    content=memory["content"],
                    memory_type=MemoryType(memory["type"]),
                    importance=float(memory["importance"]),
                    token=token,
                    metadata={"source": "conversation"},
                )
                if success:
                    stored_count += 1
            except Exception as exc:
                logger.warning("Failed to persist extracted memory for user %s: %s", user_id, exc)
        return stored_count

    async def clear_user_memories(self, user_id: str, token: Optional[str]) -> bool:
        try:
            path = self._memory_path(user_id)
            if path.exists():
                path.unlink()
            return True
        except Exception as exc:
            logger.error("Failed to clear semantic memories for user %s: %s", user_id, exc)
            return False


_semantic_memory_service: Optional[SemanticMemoryService] = None


def get_semantic_memory_service() -> SemanticMemoryService:
    global _semantic_memory_service
    if _semantic_memory_service is None:
        _semantic_memory_service = SemanticMemoryService()
    return _semantic_memory_service
