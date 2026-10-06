from fastapi import APIRouter, Depends, HTTPException
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
from app.services.journal import extract, make_response
from app.services.safety import local_risk_check, safety_message

router = APIRouter(prefix="/journal", tags=["journal"])


def gemini() -> GeminiService:
    return GeminiService()


def risk_is_blocking(level: str) -> bool:
    return level in {"high", "immediate"}


@router.post("", response_model=JournalResponse | SafetyResponse, status_code=201)
def create_journal(payload: JournalCreateRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    local = local_risk_check(payload.text)
    if local and risk_is_blocking(local.risk_level):
        entry = JournalEntry(profile_id=profile.id, text=payload.text, risk_flag=True)
        db.add(entry)
        db.commit()
        return safety_message()

    assessment = extract(gemini(), payload.text)
    if risk_is_blocking(assessment.risk.risk_level):
        entry = JournalEntry(profile_id=profile.id, text=payload.text, risk_flag=True)
        db.add(entry)
        db.commit()
        return safety_message()

    entry = JournalEntry(profile_id=profile.id, text=payload.text)
    db.add(entry)
    db.flush()
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


@router.patch("/{entry_id}", response_model=JournalResponse | SafetyResponse)
def update_journal(entry_id: str, payload: JournalUpdateRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    entry = db.scalar(
        select(JournalEntry)
        .where(JournalEntry.id == entry_id, JournalEntry.profile_id == profile.id)
        .options(joinedload(JournalEntry.insight))
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if payload.text is None or payload.text == entry.text:
        return make_response(entry)

    local = local_risk_check(payload.text)
    if local and risk_is_blocking(local.risk_level):
        entry.text = payload.text
        entry.risk_flag = True
        if entry.insight is not None:
            db.delete(entry.insight)
        db.commit()
        return safety_message()

    assessment = extract(gemini(), payload.text)
    entry.text = payload.text
    if risk_is_blocking(assessment.risk.risk_level):
        entry.risk_flag = True
        if entry.insight is not None:
            db.delete(entry.insight)
        db.commit()
        return safety_message()

    entry.risk_flag = False
    extraction = assessment.extraction
    if entry.insight is None:
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
    else:
        entry.insight.observation = extraction.observation
        entry.insight.tags = extraction.tags
        entry.insight.themes = extraction.themes
        entry.insight.emotions = extraction.emotions
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
