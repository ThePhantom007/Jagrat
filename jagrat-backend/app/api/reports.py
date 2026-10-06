from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile
from app.schemas import WeeklyReportResponse
from app.services.gemini import GeminiService
from app.services.growth import current_factor_cards, calculate_day_streak, generate_report, lifetime_factor_trends, total_reflections, week_start, _weekly_anchor

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly/{date_value}", response_model=WeeklyReportResponse)
def weekly_report(date_value: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    try:
        parsed = datetime.fromisoformat(date_value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        start = week_start(parsed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="date must be ISO format, e.g. 2026-10-05") from exc
    row = generate_report(db, profile.id, GeminiService(), start)
    payload = row.report_json
    return WeeklyReportResponse(**payload, week_start=row.week_start, created_at=row.created_at, lifetime_factor_trends=lifetime_factor_trends(db, profile.id), day_streak=calculate_day_streak(db, profile.id), total_reflections=total_reflections(db, profile.id), factor_cards=current_factor_cards(db, profile.id), weekly_anchor=_weekly_anchor(db, profile.id, start))
