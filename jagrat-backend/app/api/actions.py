from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_profile
from app.db.session import get_db
from app.models import ActionFollowUp, ActionItem, Profile
from app.schemas import ActionFollowUpRequest, ActionFollowUpResponse, ActionResponse

router = APIRouter(prefix="/actions", tags=["actions"])


def response(row: ActionItem, db: Session | None = None, profile_id: str | None = None) -> ActionResponse:
    follow_up = None
    if db is not None and profile_id is not None:
        follow_up = db.scalar(select(ActionFollowUp).where(ActionFollowUp.action_id == row.id, ActionFollowUp.profile_id == profile_id))
    return ActionResponse(
        id=row.id, text=row.text, reason=row.reason, completed=row.completed_at is not None,
        created_at=row.created_at, completed_at=row.completed_at,
        follow_up_outcome=follow_up.outcome if follow_up else None,
        follow_up_note=follow_up.note if follow_up else None,
    )


@router.get("", response_model=list[ActionResponse])
def list_actions(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    rows = list(db.scalars(select(ActionItem).where(ActionItem.profile_id == profile.id).order_by(ActionItem.created_at.desc()).limit(50)).all())
    return [response(x, db, profile.id) for x in rows]


@router.post("/{action_id}/complete", response_model=ActionResponse)
def complete(action_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    row = db.scalar(select(ActionItem).where(ActionItem.id == action_id, ActionItem.profile_id == profile.id))
    if not row:
        raise HTTPException(status_code=404, detail="Action not found")
    row.completed_at = row.completed_at or datetime.now(timezone.utc)
    db.commit()
    return response(row, db, profile.id)


@router.post("/{action_id}/follow-up", response_model=ActionFollowUpResponse)
def follow_up(action_id: str, payload: ActionFollowUpRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    action = db.scalar(select(ActionItem).where(ActionItem.id == action_id, ActionItem.profile_id == profile.id))
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    row = db.scalar(select(ActionFollowUp).where(ActionFollowUp.action_id == action_id, ActionFollowUp.profile_id == profile.id))
    if row is None:
        row = ActionFollowUp(profile_id=profile.id, action_id=action_id, outcome=payload.outcome, note=payload.note)
        db.add(row)
    else:
        row.outcome = payload.outcome
        row.note = payload.note
        row.created_at = datetime.now(timezone.utc)
    if payload.outcome == "completed" and action.completed_at is None:
        action.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return ActionFollowUpResponse(id=row.id, action_id=row.action_id, outcome=row.outcome, note=row.note, created_at=row.created_at)
