from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

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
