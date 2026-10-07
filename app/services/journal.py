from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import JournalEntry, JournalInsight
from app.schemas import JournalAssessment
from app.services.gemini import GeminiService
from app.services.prompts import JOURNAL_SYSTEM


def extract(gemini: GeminiService, text: str) -> JournalAssessment:
    return gemini.generate(
        system_instruction=JOURNAL_SYSTEM,
        prompt=f"JOURNAL ENTRY:\n{text}",
        schema=JournalAssessment,
        fast=True,
    )


def make_response(entry: JournalEntry) -> dict:
    insight = entry.insight
    return {
        "id": entry.id,
        "text": entry.text,
        "risk_flag": entry.risk_flag,
        "analysis_status": "ready" if insight is not None and not entry.risk_flag else "pending",
        "created_at": entry.created_at,
        "insight": None if insight is None else {
            "id": insight.id,
            "journal_entry_id": insight.journal_entry_id,
            "observation": insight.observation,
            "tags": insight.tags,
            "themes": insight.themes,
            "emotions": insight.emotions,
            "created_at": insight.created_at,
        },
    }


def analyze_saved_entry(db: Session, entry: JournalEntry, text: str, gemini: GeminiService) -> JournalAssessment:
    """Analyze an already-persisted entry; callers can safely retry after provider failures."""
    assessment = extract(gemini, text)
    if assessment.risk.risk_level in {"high", "immediate"}:
        entry.risk_flag = True
        if entry.insight is not None:
            db.delete(entry.insight)
        db.commit()
        return assessment

    entry.risk_flag = False
    extraction = assessment.extraction
    if entry.insight is None:
        db.add(
            JournalInsight(
                profile_id=entry.profile_id,
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
    return assessment
