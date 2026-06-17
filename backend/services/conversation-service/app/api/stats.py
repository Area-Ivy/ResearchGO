"""
Dashboard statistics for conversations.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationStatsResponse, WeeklyCount
from app.utils.auth_client import get_current_active_user

router = APIRouter(prefix="/api/conversations", tags=["conversation-stats"])


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _week_windows(now: datetime, weeks: int = 30):
    current_week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    first_week_start = current_week_start - timedelta(weeks=weeks - 1)
    return [
        (
            first_week_start + timedelta(weeks=index),
            first_week_start + timedelta(weeks=index + 1),
        )
        for index in range(weeks)
    ]


def _format_weekly_counts(timestamps, now: datetime) -> list[WeeklyCount]:
    windows = _week_windows(now)
    counts = [0 for _ in windows]

    for timestamp in timestamps:
        if not timestamp:
            continue
        for index, (start, end) in enumerate(windows):
            if start <= timestamp < end:
                counts[index] += 1
                break

    return [
        WeeklyCount(
            label=f"W{index + 1}",
            value=counts[index],
            start=start.isoformat(),
            end=(end - timedelta(microseconds=1)).isoformat(),
        )
        for index, (start, end) in enumerate(windows)
    ]


@router.get("/stats", response_model=ConversationStatsResponse)
async def get_conversation_stats(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return dashboard-friendly conversation statistics for the current user."""
    try:
        now = datetime.utcnow()
        month_start = _month_start(now)
        base_query = db.query(Conversation).filter(
            Conversation.user_id == current_user["id"],
            Conversation.is_deleted == False,
        )
        conversation_ids = [conversation.id for conversation in base_query.all()]

        if not conversation_ids:
            return ConversationStatsResponse(
                total=0,
                messages_this_month=0,
                weekly_messages=_format_weekly_counts([], now),
            )

        message_timestamps = [
            row[0]
            for row in db.query(Message.created_at)
            .filter(Message.conversation_id.in_(conversation_ids))
            .all()
        ]
        messages_this_month = sum(
            1 for timestamp in message_timestamps if timestamp and timestamp >= month_start
        )

        return ConversationStatsResponse(
            total=len(conversation_ids),
            messages_this_month=messages_this_month,
            weekly_messages=_format_weekly_counts(message_timestamps, now),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load conversation stats: {exc}",
        )
