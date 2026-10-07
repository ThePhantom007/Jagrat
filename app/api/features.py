from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import InteractionRecord, Profile, ReflectionFeedback, SavedTeaching, Teaching
from app.schemas import ReflectionFeedbackRequest, ReflectionFeedbackResponse, SavedTeachingResponse, SourceResponse, TodaysReflectionResponse

router = APIRouter(tags=["engagement"])


def source_payload(t: Teaching) -> SourceResponse:
    return SourceResponse(type=t.source_type, title=t.source_title, volume=t.source_volume, chapter=t.source_chapter, page=t.source_page, section=t.source_section, url=t.source_url, authority="organizer_provided_json")


@router.post("/mentor/{conversation_id}/feedback", response_model=ReflectionFeedbackResponse)
def feedback(conversation_id: str, payload: ReflectionFeedbackRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    from app.models import Conversation
    conv = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    row = db.scalar(select(ReflectionFeedback).where(ReflectionFeedback.conversation_id == conversation_id, ReflectionFeedback.profile_id == profile.id))
    if row is None:
        row = ReflectionFeedback(profile_id=profile.id, conversation_id=conversation_id, helpful=payload.helpful, reason=payload.reason, note=payload.note)
        db.add(row)
    else:
        row.helpful = payload.helpful
        row.reason = payload.reason
        row.note = payload.note
        row.created_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return ReflectionFeedbackResponse(
        id=row.id, conversation_id=row.conversation_id, helpful=row.helpful, reason=row.reason,
        note=row.note, created_at=row.created_at
    )


@router.get("/mentor/{conversation_id}/feedback", response_model=ReflectionFeedbackResponse | None)
def get_feedback(conversation_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    row = db.scalar(select(ReflectionFeedback).where(ReflectionFeedback.conversation_id == conversation_id, ReflectionFeedback.profile_id == profile.id))
    if row is None:
        return None
    return ReflectionFeedbackResponse(
        id=row.id, conversation_id=row.conversation_id, helpful=row.helpful, reason=row.reason,
        note=row.note, created_at=row.created_at
    )


@router.get("/teachings/saved", response_model=list[SavedTeachingResponse])
def saved_teachings(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    rows = list(db.scalars(select(SavedTeaching).where(SavedTeaching.profile_id == profile.id).order_by(SavedTeaching.created_at.desc())).all())
    out = []
    for row in rows:
        teaching = db.get(Teaching, row.teaching_id)
        if teaching:
            out.append(SavedTeachingResponse(id=row.id, teaching_id=teaching.id, quote=teaching.quote, source=source_payload(teaching), saved_at=row.created_at))
    return out


@router.post("/teachings/{teaching_id}/save", response_model=SavedTeachingResponse)
def save_teaching(teaching_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    teaching = db.get(Teaching, teaching_id)
    if teaching is None:
        raise HTTPException(status_code=404, detail="Teaching not found")
    row = db.scalar(select(SavedTeaching).where(SavedTeaching.profile_id == profile.id, SavedTeaching.teaching_id == teaching_id))
    if row is None:
        row = SavedTeaching(profile_id=profile.id, teaching_id=teaching_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return SavedTeachingResponse(id=row.id, teaching_id=teaching.id, quote=teaching.quote, source=source_payload(teaching), saved_at=row.created_at)


@router.delete("/teachings/{teaching_id}/save", status_code=204)
def unsave_teaching(teaching_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    row = db.scalar(select(SavedTeaching).where(SavedTeaching.profile_id == profile.id, SavedTeaching.teaching_id == teaching_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Saved teaching not found")
    db.delete(row)
    db.commit()


PROMPTS = {
    "fear": "What would you do today if you stopped treating uncertainty as a reason to wait?",
    "self_doubt": "Which part of what you are facing is a skill you can practice rather than a verdict about you?",
    "comparison": "What changes when you measure today's effort against your own previous effort instead of someone else's result?",
    "failure": "What can this setback teach you about what to change next?",
    "discipline": "What is one small action you can complete today even without feeling motivated?",
    "purpose": "What matters enough to you that you are willing to take one concrete step toward it today?",
    "resilience": "What is one difficulty you have already handled that you can remember before facing today's difficulty?",
    "confidence": "What evidence from your own actions shows a capability you sometimes overlook?",
}


@router.get("/mentor/today-prompt", response_model=TodaysReflectionResponse)
def todays_reflection(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    from app.models import JournalInsight
    rows = list(db.scalars(select(JournalInsight.themes).where(JournalInsight.profile_id == profile.id).order_by(JournalInsight.created_at.desc()).limit(20)).all())
    counts = {}
    for themes in rows:
        for t in themes or []:
            key = str(t).lower().replace("-", "_")
            counts[key] = counts.get(key, 0) + 1
    theme = max(counts, key=counts.get) if counts else None
    prompt = PROMPTS.get(theme, "What is one thing on your mind today that deserves to be examined with honesty rather than judgment?")
    return TodaysReflectionResponse(prompt=prompt, theme=theme, source="curated_reflection_prompt")
