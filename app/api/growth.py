from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile, ReflectionGoal, WeeklyCheckIn
from app.schemas import CheckInRequest, GrowthResponse, ReflectionGoalRequest, ReflectionGoalResponse
from app.services.growth import build_growth

router = APIRouter(prefix="/growth", tags=["growth"])


@router.get("", response_model=GrowthResponse)
def growth(days: int = 30, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    days = max(7, min(days, 180))
    return build_growth(db, profile.id, days)


@router.put("/check-in")
def save_checkin(payload: CheckInRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    from sqlalchemy import select
    existing = db.scalar(select(WeeklyCheckIn).where(WeeklyCheckIn.profile_id == profile.id, WeeklyCheckIn.week_start == payload.week_start))
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        row = existing
    else:
        row = WeeklyCheckIn(profile_id=profile.id, **payload.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "week_start": row.week_start,
        "self_belief": row.self_belief,
        "fear": row.fear,
        "discipline": row.discipline,
        "clarity": row.clarity,
        "resilience": row.resilience,
        "note": row.note,
    }


@router.get("/goal", response_model=ReflectionGoalResponse | None)
def get_reflection_goal(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    return db.scalar(select(ReflectionGoal).where(ReflectionGoal.profile_id == profile.id))


@router.put("/goal", response_model=ReflectionGoalResponse)
def upsert_reflection_goal(payload: ReflectionGoalRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    goal = db.scalar(select(ReflectionGoal).where(ReflectionGoal.profile_id == profile.id))
    if goal is None:
        goal = ReflectionGoal(profile_id=profile.id, goal_key=payload.goal_key, goal_text=payload.goal_text.strip())
        db.add(goal)
    else:
        goal.goal_key = payload.goal_key
        goal.goal_text = payload.goal_text.strip()
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/goal", status_code=204)
def delete_reflection_goal(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    goal = db.scalar(select(ReflectionGoal).where(ReflectionGoal.profile_id == profile.id))
    if goal is None:
        return
    db.delete(goal)
    db.commit()
