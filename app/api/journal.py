from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import JournalEntry, JournalInsight, Profile
from app.schemas import (
    JournalCreateRequest,
    JournalInsightResponse,
    JournalInsightUpdateRequest,
    JournalResponse,
    JournalUpdateRequest,
    SafetyResponse,
)
from app.services.gemini import GeminiService
from app.services.journal import analyze_saved_entry, extract, make_response
from app.services.safety import local_risk_check, safety_message

router = APIRouter(prefix="/journal", tags=["journal"])


def gemini() -> GeminiService:
    return GeminiService()


def risk_is_blocking(level: str) -> bool:
    return level in {"high", "immediate"}


def _save_entry(db: Session, profile_id: str, text: str, *, risk_flag: bool = False) -> JournalEntry:
    entry = JournalEntry(profile_id=profile_id, text=text, risk_flag=risk_flag)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("", response_model=JournalResponse | SafetyResponse, status_code=201)
def create_journal(payload: JournalCreateRequest, response: Response, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    text = payload.text.strip()
    local = local_risk_check(text)
    if local and risk_is_blocking(local.risk_level):
        _save_entry(db, profile.id, text, risk_flag=True)
        return safety_message()

    # Persist first. A Gemini outage/quota error must never lose the user's diary entry.
    entry = _save_entry(db, profile.id, text)
    try:
        analysis = extract(gemini(), text)
    except RuntimeError:
        response.status_code = 202
        return make_response(entry)

    if risk_is_blocking(analysis.risk.risk_level):
        entry.risk_flag = True
        db.commit()
        return safety_message()

    extraction = analysis.extraction
    db.add(
        JournalInsight(
            profile_id=profile.id,
            journal_entry_id=entry.id,
            observation=extraction.observation,
            tags=extraction.tags,
            themes=extraction.themes,
            emotions=extraction.emotions,
        )
    )
    db.commit()
    db.refresh(entry)
    return make_response(entry)


@router.get("", response_model=list[JournalResponse])
def list_journal(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    entries = list(
        db.scalars(
            select(JournalEntry)
            .where(JournalEntry.profile_id == profile.id)
            .options(joinedload(JournalEntry.insight))
            .order_by(JournalEntry.created_at.desc())
            .limit(100)
        ).unique().all()
    )
    return [make_response(entry) for entry in entries]


@router.post("/{entry_id}/analyze", response_model=JournalResponse | SafetyResponse)
def retry_analysis(entry_id: str, response: Response, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    entry = db.scalar(
        select(JournalEntry)
        .where(JournalEntry.id == entry_id, JournalEntry.profile_id == profile.id)
        .options(joinedload(JournalEntry.insight))
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.risk_flag:
        return safety_message()
    if entry.insight is not None:
        return make_response(entry)
    try:
        assessment = analyze_saved_entry(db, entry, entry.text, gemini())
    except RuntimeError:
        response.status_code = 503
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable; the journal entry is saved and can be analyzed later.")
    if risk_is_blocking(assessment.risk.risk_level):
        return safety_message()
    return make_response(entry)


@router.patch("/{entry_id}", response_model=JournalResponse | SafetyResponse)
def update_journal(entry_id: str, payload: JournalUpdateRequest, response: Response, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    entry = db.scalar(
        select(JournalEntry)
        .where(JournalEntry.id == entry_id, JournalEntry.profile_id == profile.id)
        .options(joinedload(JournalEntry.insight))
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if payload.text is None or payload.text == entry.text:
        return make_response(entry)

    text = payload.text.strip()
    local = local_risk_check(text)
    entry.text = text
    if entry.insight is not None:
        db.delete(entry.insight)
    entry.insight = None
    if local and risk_is_blocking(local.risk_level):
        entry.risk_flag = True
        db.commit()
        return safety_message()

    # Persist edited text before calling Gemini so an outage cannot lose the edit.
    entry.risk_flag = False
    db.commit()
    db.refresh(entry)
    try:
        assessment = extract(gemini(), text)
    except RuntimeError:
        response.status_code = 202
        return make_response(entry)
    if risk_is_blocking(assessment.risk.risk_level):
        entry.risk_flag = True
        db.commit()
        return safety_message()
    extraction = assessment.extraction
    db.add(
        JournalInsight(
            profile_id=profile.id,
            journal_entry_id=entry.id,
            observation=extraction.observation,
            tags=extraction.tags,
            themes=extraction.themes,
            emotions=extraction.emotions,
        )
    )
    db.commit()
    db.refresh(entry)
    return make_response(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_journal(entry_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    entry = db.scalar(select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.profile_id == profile.id))
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()


@router.patch("/insights/{insight_id}", response_model=JournalInsightResponse)
def update_insight(insight_id: str, payload: JournalInsightUpdateRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    insight = db.scalar(select(JournalInsight).where(JournalInsight.id == insight_id, JournalInsight.profile_id == profile.id))
    if not insight:
        raise HTTPException(status_code=404, detail="Journal insight not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(insight, key, value)
    db.commit()
    db.refresh(insight)
    return insight


@router.delete("/insights/{insight_id}", status_code=204)
def delete_insight(insight_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    insight = db.scalar(select(JournalInsight).where(JournalInsight.id == insight_id, JournalInsight.profile_id == profile.id))
    if not insight:
        raise HTTPException(status_code=404, detail="Journal insight not found")
    db.delete(insight)
    db.commit()
