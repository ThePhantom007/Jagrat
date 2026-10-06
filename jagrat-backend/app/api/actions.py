from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_profile
from app.db.session import get_db
from app.models import ActionItem, Profile
from app.schemas import ActionResponse

router = APIRouter(prefix="/actions", tags=["actions"])


def response(row: ActionItem) -> ActionResponse:
    return ActionResponse(id=row.id, text=row.text, reason=row.reason, completed=row.completed_at is not None, created_at=row.created_at, completed_at=row.completed_at)


@router.get("", response_model=list[ActionResponse])
def list_actions(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    rows = list(db.scalars(select(ActionItem).where(ActionItem.profile_id == profile.id).order_by(ActionItem.created_at.desc()).limit(50)).all())
    return [response(x) for x in rows]


@router.post("/{action_id}/complete", response_model=ActionResponse)
def complete(action_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    row = db.scalar(select(ActionItem).where(ActionItem.id == action_id, ActionItem.profile_id == profile.id))
    if not row:
        raise HTTPException(status_code=404, detail="Action not found")
    row.completed_at = row.completed_at or datetime.now(timezone.utc)
    db.commit()
    return response(row)
