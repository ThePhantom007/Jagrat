import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import JournalInsight, Teaching

STOPWORDS = {
    "the", "a", "an", "i", "me", "my", "am", "is", "are", "to", "of", "for", "and", "or", "in", "on",
    "it", "this", "that", "with", "be", "not", "feel", "think", "about", "now", "just", "very", "really",
}
ALIASES = {
    "failure": {"fail", "failed", "failure", "failing", "mistake", "mistakes"},
    "self_doubt": {"doubt", "doubting", "insecure", "insecurity", "incapable", "good enough"},
    "fear": {"afraid", "scared", "fear", "worried", "worry", "anxious", "anxiety"},
    "comparison": {"compare", "comparison", "comparing", "peers", "friends", "others"},
    "confidence": {"confident", "confidence", "capable", "ability", "intelligent"},
    "discipline": {"discipline", "procrastination", "consistency", "routine", "lazy"},
    "purpose": {"purpose", "meaning", "direction", "future"},
    "resilience": {"persistent", "persistence", "resilience", "keep going", "continue"},
    "academic_pressure": {"exam", "exams", "college", "grades", "marks", "study", "studying"},
    "relationships": {"relationship", "partner", "friendship", "family", "parents"},
    "loneliness": {"lonely", "loneliness", "alone", "isolated"},
    "grief": {"loss", "grief", "grieving", "died", "death"},
}


@dataclass(frozen=True)
class RetrievalTerms:
    terms: set[str]


def tokenize(text: str) -> set[str]:
    lower = text.lower()
    raw = set(re.findall(r"[a-z0-9_]+", lower)) - STOPWORDS
    expanded = set(raw)
    for canonical, variants in ALIASES.items():
        if any(v in raw for v in variants if " " not in v):
            expanded.add(canonical)
        if any(v in lower for v in variants if " " in v):
            expanded.add(canonical)
    return expanded


def terms_from_analysis(analysis) -> RetrievalTerms:
    values = list(analysis.emotions) + list(analysis.challenges) + list(analysis.themes) + [analysis.underlying_belief]
    terms: set[str] = set()
    for value in values:
        terms |= tokenize(value)
    return RetrievalTerms(terms)


def _field_terms(values) -> set[str]:
    out: set[str] = set()
    for value in values or []:
        out |= tokenize(value)
    return out


def teaching_score(teaching: Teaching, terms: set[str]) -> tuple[int, int, int]:
    metadata = _field_terms([
        *(teaching.themes or []),
        *(teaching.emotions or []),
        *(teaching.challenges or []),
        *(teaching.keywords or []),
    ])
    text = tokenize(f"{teaching.quote} {teaching.context or ''}")
    metadata_overlap = len(metadata & terms)
    text_overlap = len(text & terms)
    # Metadata matters most because it is explicitly curated by the CSV owner.
    return (metadata_overlap * 5 + text_overlap, metadata_overlap, text_overlap)


def retrieve_teachings(db: Session, terms: RetrievalTerms, limit: int = 7) -> list[Teaching]:
    # Deliberately deterministic/cost-free retrieval. All rows in this table are organiser-CSV records.
    rows = list(db.scalars(select(Teaching)).all())
    ranked = sorted(rows, key=lambda t: teaching_score(t, terms.terms), reverse=True)
    matched = [row for row in ranked if teaching_score(row, terms.terms)[0] > 0]
    return matched[:limit]


def journal_score(row: JournalInsight, terms: set[str]) -> int:
    row_terms = _field_terms([*(row.tags or []), *(row.themes or []), *(row.emotions or []), row.observation])
    return len(row_terms & terms)


def retrieve_journal_insights(db: Session, profile_id: str, terms: RetrievalTerms, limit: int = 5) -> list[JournalInsight]:
    rows = list(
        db.scalars(
            select(JournalInsight)
            .where(JournalInsight.profile_id == profile_id)
            .options(joinedload(JournalInsight.entry))
            .order_by(JournalInsight.created_at.desc())
            .limit(50)
        ).all()
    )
    ranked = sorted(rows, key=lambda row: (journal_score(row, terms.terms), row.created_at), reverse=True)
    return [row for row in ranked if journal_score(row, terms.terms) > 0][:limit]
