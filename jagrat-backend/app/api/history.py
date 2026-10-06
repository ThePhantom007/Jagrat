from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import ActionFollowUp, ActionItem, Conversation, JournalEntry, Profile, VivekanandaComparison, Teaching
from app.schemas import HistoryItem, HistoryResponse

router = APIRouter(prefix="/history", tags=["history"] )


@router.get("", response_model=HistoryResponse)
def history(limit: int = 50, item_type: str | None = None, q: str | None = None, theme: str | None = None, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    limit = max(10, min(limit, 100))

    journal = list(
        db.scalars(
            select(JournalEntry)
            .where(JournalEntry.profile_id == profile.id)
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
        ).all()
    )
    conversations = list(
        db.scalars(
            select(Conversation)
            .where(Conversation.profile_id == profile.id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        ).all()
    )
    actions = list(
        db.scalars(
            select(ActionItem)
            .where(ActionItem.profile_id == profile.id)
            .order_by(ActionItem.created_at.desc())
            .limit(limit)
        ).all()
    )
    comparisons = list(
        db.scalars(
            select(VivekanandaComparison)
            .where(VivekanandaComparison.profile_id == profile.id)
            .order_by(VivekanandaComparison.created_at.desc())
            .limit(limit)
        ).all()
    )

    items: list[HistoryItem] = []

    for entry in journal:
        insight = entry.insight
        items.append(
            HistoryItem(
                id=entry.id,
                type="journal",
                created_at=entry.created_at,
                title="Diary entry",
                summary=entry.text[:280],
                data={
                    "text": entry.text,
                    "risk_flag": entry.risk_flag,
                    "insight": insight.observation if insight else None,
                    "themes": insight.themes if insight else [],
                    "emotions": insight.emotions if insight else [],
                    "tags": insight.tags if insight else [],
                },
            )
        )

    for conversation in conversations:
        items.append(
            HistoryItem(
                id=conversation.id,
                type="mentor",
                created_at=conversation.created_at,
                title="Mentor reflection",
                summary=conversation.current_problem[:280],
                data={
                    "current_problem": conversation.current_problem,
                    "problem_analysis": conversation.problem_analysis,
                    "selected_teaching_id": conversation.selected_teaching_id,
                    "rounds_used": conversation.rounds_used,
                    "completed": conversation.completed_at is not None,
                    "risk_flag": conversation.risk_flag,
                },
            )
        )

    for action in actions:
        items.append(
            HistoryItem(
                id=action.id,
                type="action",
                created_at=action.created_at,
                title="Action",
                summary=action.text[:280],
                data={
                    "text": action.text,
                    "reason": action.reason,
                    "completed": action.completed_at is not None,
                    "completed_at": action.completed_at,
                    "conversation_id": action.conversation_id,
                    "follow_up": (lambda fu: {"outcome": fu.outcome, "note": fu.note, "created_at": fu.created_at} if fu else None)(
                        db.scalar(select(ActionFollowUp).where(ActionFollowUp.action_id == action.id, ActionFollowUp.profile_id == profile.id))
                    ),
                },
            )
        )

    for comparison in comparisons:
        selected = db.get(Teaching, comparison.selected_teaching_id) if comparison.selected_teaching_id else None
        result = comparison.result_json or {}
        items.append(
            HistoryItem(
                id=comparison.id,
                type="vivekananda_vs_me",
                created_at=comparison.created_at,
                title="Vivekananda vs Me",
                summary=comparison.user_view[:280],
                data={
                    "my_view": comparison.user_view,
                    "problem_analysis": comparison.problem_analysis,
                    "selected_teaching_id": comparison.selected_teaching_id,
                    "teaching_title": selected.source_title if selected else None,
                    "result": result,
                    "risk_flag": comparison.risk_flag,
                },
            )
        )

    items.sort(key=lambda item: item.created_at, reverse=True)

    normalized_q = q.strip().lower() if q else None
    normalized_theme = theme.strip().lower().replace("-", "_") if theme else None
    if item_type:
        allowed = {"journal", "mentor", "action", "vivekananda_vs_me"}
        if item_type not in allowed:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="item_type must be journal, mentor, action, or vivekananda_vs_me")
        items = [item for item in items if item.type == item_type]
    if normalized_q:
        items = [item for item in items if normalized_q in (item.title + " " + item.summary + " " + str(item.data)).lower()]
    if normalized_theme:
        items = [item for item in items if normalized_theme in {str(t).lower().replace("-", "_") for t in item.data.get("themes", [])}]

    return HistoryResponse(items=items[:limit])
