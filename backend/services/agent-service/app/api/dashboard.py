"""Dashboard aggregation API."""
import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, Request

from ..utils.auth import get_current_user
from ..utils.service_discovery import get_service_discovery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

DASHBOARD_FIELDS = ["Algorithms", "Data", "Systems", "AI/ML", "Theory", "Security"]


def _empty_weekly_counts() -> list[dict[str, Any]]:
    now = datetime.utcnow()
    current_week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    first_week_start = current_week_start - timedelta(weeks=29)
    return [
        {
            "label": f"W{index + 1}",
            "value": 0,
            "start": (first_week_start + timedelta(weeks=index)).isoformat(),
            "end": (first_week_start + timedelta(weeks=index + 1) - timedelta(microseconds=1)).isoformat(),
        }
        for index in range(30)
    ]


def _default_paper_stats() -> dict[str, Any]:
    return {
        "total": 0,
        "indexed": 0,
        "indexing": 0,
        "failed": 0,
        "uploaded": 0,
        "uploaded_this_month": 0,
        "indexed_this_month": 0,
        "recent_papers": [],
        "weekly_uploads": _empty_weekly_counts(),
        "field_distribution": {field: 0 for field in DASHBOARD_FIELDS},
    }


def _default_conversation_stats() -> dict[str, Any]:
    return {
        "total": 0,
        "messages_this_month": 0,
        "weekly_messages": _empty_weekly_counts(),
    }


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _relative_time(value: Optional[str]) -> str:
    timestamp = _parse_datetime(value)
    if not timestamp:
        return "unknown"
    delta = datetime.utcnow() - timestamp
    if delta.days >= 7:
        return f"{delta.days // 7}w"
    if delta.days >= 1:
        return f"{delta.days}d"
    hours = delta.seconds // 3600
    if hours >= 1:
        return f"{hours}h"
    minutes = max(delta.seconds // 60, 1)
    return f"{minutes}m"


def _primary_field(field_distribution: dict[str, int]) -> str:
    if not field_distribution:
        return "Computer Science"
    field, count = max(field_distribution.items(), key=lambda item: item[1])
    return field if count > 0 else "Computer Science"


def _entropy(field_distribution: dict[str, int]) -> float:
    counts = [count for count in field_distribution.values() if count > 0]
    total = sum(counts)
    if total <= 0 or len(counts) <= 1:
        return 0.0
    raw_entropy = -sum((count / total) * math.log(count / total) for count in counts)
    return round((raw_entropy / math.log(len(DASHBOARD_FIELDS))) * 10, 1)


def _knowledge_status(entropy_value: float) -> str:
    if entropy_value < 3.3:
        return "LOW_ENTROPY"
    if entropy_value < 6.6:
        return "MEDIUM_ENTROPY"
    return "HIGH_ENTROPY"


def _knowledge_description(status_value: str) -> str:
    descriptions = {
        "LOW_ENTROPY": "Your knowledge base is structured around a focused set of concepts.",
        "MEDIUM_ENTROPY": "Your knowledge base spans several connected research areas.",
        "HIGH_ENTROPY": "Your knowledge base is broad and may benefit from more synthesis.",
    }
    return descriptions.get(status_value, descriptions["LOW_ENTROPY"])


def _format_authors(work: dict[str, Any]) -> str:
    authors = work.get("authors") or []
    names = [author.get("name") for author in authors if author.get("name")]
    if not names:
        return f"Unknown authors - {work.get('publication_year') or 'n.d.'}"
    if len(names) > 3:
        names = names[:3] + ["et al."]
    return f"{', '.join(names)} - {work.get('publication_year') or 'n.d.'}"


def _work_id(work: dict[str, Any]) -> str:
    raw_id = work.get("id") or work.get("openalex_url") or ""
    return str(raw_id).rstrip("/").split("/")[-1] or str(work.get("title") or "work")


def _work_url(work: dict[str, Any]) -> Optional[str]:
    doi_url = work.get("doi_url")
    if isinstance(doi_url, str) and doi_url.startswith("https://doi.org/https://"):
        doi_url = doi_url.replace("https://doi.org/", "", 1)
    return doi_url or work.get("openalex_url") or work.get("pdf_url")


def _recommendations_from_literature(payload: dict[str, Any], category: str) -> list[dict[str, Any]]:
    return [
        {
            "id": _work_id(work),
            "category": category,
            "title": work.get("title") or "Untitled",
            "authors": _format_authors(work),
            "year": work.get("publication_year"),
            "url": _work_url(work),
        }
        for work in (payload.get("results") or [])[:3]
    ]


def _field_progress_from_literature(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for work in (payload.get("results") or [])[:3]:
        source = work.get("venue") or "OpenAlex"
        items.append(
            {
                "id": _work_id(work),
                "title": work.get("title") or "Untitled",
                "source": source,
                "time": _relative_time(work.get("publication_date")),
                "url": _work_url(work),
            }
        )
    return items


def _queue_from_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for paper in papers:
        status_value = paper.get("processing_status") or "uploaded"
        if status_value not in {"uploaded", "indexing", "failed"}:
            continue
        is_failed = status_value == "failed"
        queue.append(
            {
                "id": f"PDF-{paper.get('id')}",
                "operation": f"Processing PDF: {paper.get('original_name') or paper.get('title') or paper.get('object_name')}",
                "status": "failed" if is_failed else "processing",
                "statusText": "Failed" if is_failed else "Processing",
                "time": _relative_time(paper.get("updated_at") or paper.get("created_at")),
            }
        )
    return queue[:5]


def _cognitive_architecture(field_distribution: dict[str, int]) -> dict[str, Any]:
    values = [_safe_int(field_distribution.get(field)) for field in DASHBOARD_FIELDS]
    max_value = max(values) if values else 0
    normalized = [round((value / max_value) * 100) if max_value else 0 for value in values]
    return {
        "labels": DASHBOARD_FIELDS,
        "values": normalized,
        "updatedAt": datetime.utcnow().isoformat() + "Z",
    }


def _neural_imprint(paper_stats: dict[str, Any], conversation_stats: dict[str, Any]) -> dict[str, Any]:
    paper_weeks = paper_stats.get("weekly_uploads") or _empty_weekly_counts()
    message_weeks = conversation_stats.get("weekly_messages") or _empty_weekly_counts()
    values = []
    labels = []
    for index in range(30):
        paper_value = _safe_int((paper_weeks[index] if index < len(paper_weeks) else {}).get("value"))
        message_value = _safe_int((message_weeks[index] if index < len(message_weeks) else {}).get("value"))
        labels.append(f"W{index + 1}")
        values.append(message_value + paper_value)
    return {"labels": labels, "values": values, "period": "Last 30 Weeks"}


async def _get_json(client: httpx.AsyncClient, url: str, headers: dict[str, str]) -> Optional[dict[str, Any]]:
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Dashboard dependency failed: %s (%s)", url, exc)
        return None


async def _post_json(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> Optional[dict[str, Any]]:
    try:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Dashboard literature request failed: %s (%s)", url, exc)
        return None


@router.get("/summary")
async def get_dashboard_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Aggregate dashboard data from existing ResearchGO services."""
    del current_user

    authorization = request.headers.get("Authorization")
    headers = {"Authorization": authorization} if authorization else {}
    service_discovery = get_service_discovery()
    paper_url, conversation_url, literature_url = await asyncio.gather(
        service_discovery.paper_storage_service(),
        service_discovery.conversation_service(),
        service_discovery.literature_service(),
    )

    async with httpx.AsyncClient(timeout=8.0) as client:
        paper_payload, conversation_payload = await asyncio.gather(
            _get_json(client, f"{paper_url}/api/papers/stats", headers),
            _get_json(client, f"{conversation_url}/api/conversations/stats", headers),
        )

        paper_stats = paper_payload or _default_paper_stats()
        conversation_stats = conversation_payload or _default_conversation_stats()
        field_distribution = {
            field: _safe_int((paper_stats.get("field_distribution") or {}).get(field))
            for field in DASHBOARD_FIELDS
        }
        primary_field = _primary_field(field_distribution)
        current_year = datetime.utcnow().year
        recommendation_payload, progress_payload = await asyncio.gather(
            _post_json(
                client,
                f"{literature_url}/api/literature/search",
                {
                    "query": primary_field,
                    "page": 1,
                    "per_page": 3,
                    "sort": "relevance",
                },
                headers,
            ),
            _post_json(
                client,
                f"{literature_url}/api/literature/search",
                {
                    "query": f"{primary_field} research",
                    "filters": {"publication_year_start": current_year - 1, "publication_year_end": current_year},
                    "page": 1,
                    "per_page": 3,
                    "sort": "publication_date",
                },
                headers,
            ),
        )

    entropy_value = _entropy(field_distribution)
    knowledge_status = _knowledge_status(entropy_value)
    total_papers = _safe_int(paper_stats.get("total"))
    indexed_papers = _safe_int(paper_stats.get("indexed"))

    return {
        "knowledge": {
            "entropyValue": entropy_value,
            "status": knowledge_status,
            "indexedPaperPercent": round((indexed_papers / total_papers) * 100) if total_papers else 0,
            "description": _knowledge_description(knowledge_status),
        },
        "recommendations": _recommendations_from_literature(recommendation_payload or {}, primary_field),
        "fieldProgress": _field_progress_from_literature(progress_payload or {}),
        "cognitiveArchitecture": _cognitive_architecture(field_distribution),
        "neuralImprint": _neural_imprint(paper_stats, conversation_stats),
        "queue": _queue_from_papers(paper_stats.get("recent_papers") or []),
        "papers": {
            "total": total_papers,
            "indexed": indexed_papers,
            "indexing": _safe_int(paper_stats.get("indexing")) + _safe_int(paper_stats.get("uploaded")),
            "failed": _safe_int(paper_stats.get("failed")),
        },
        "conversations": {
            "total": _safe_int(conversation_stats.get("total")),
            "messagesThisMonth": _safe_int(conversation_stats.get("messages_this_month")),
        },
    }
