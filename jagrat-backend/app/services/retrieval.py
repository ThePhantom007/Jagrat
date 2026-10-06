from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import JournalInsight, Teaching

STOPWORDS = {
    "the", "a", "an", "i", "me", "my", "am", "is", "are", "to", "of", "for", "and", "or", "in", "on",
    "it", "this", "that", "with", "be", "not", "feel", "think", "about", "now", "just", "very", "really",
    "as", "by", "from", "into", "your", "you", "we", "our", "they", "their", "them", "he", "she", "his", "her",
    "was", "were", "been", "being", "can", "could", "would", "should", "will", "do", "does", "did", "have", "has",
}

ALIASES = {
    "failure": {"fail", "failed", "failure", "failing", "mistake", "mistakes", "setback", "setbacks"},
    "self_doubt": {"doubt", "doubting", "insecure", "insecurity", "incapable", "unworthy", "good enough"},
    "fear": {"afraid", "scared", "fear", "worried", "worry", "anxious", "anxiety", "fearless", "fearlessness"},
    "comparison": {"compare", "comparison", "comparing", "peers", "friends", "others", "competition", "compete"},
    "confidence": {"confident", "confidence", "capable", "ability", "intelligent", "strength", "strong"},
    "discipline": {"discipline", "procrastination", "consistency", "routine", "lazy", "practice", "habit"},
    "purpose": {"purpose", "meaning", "direction", "future", "duty", "goal", "aim"},
    "resilience": {"persistent", "persistence", "resilience", "persevere", "perseverance", "overcome", "struggle", "endure", "courage"},
    "academic_pressure": {"exam", "exams", "college", "grades", "marks", "study", "studying", "school", "education"},
    "relationships": {"relationship", "partner", "friendship", "family", "parents", "marriage"},
    "loneliness": {"lonely", "loneliness", "alone", "isolated", "isolation"},
    "grief": {"loss", "grief", "grieving", "died", "death", "dead"},
    "service": {"service", "serve", "helping", "humanity", "work for others"},
    "knowledge": {"knowledge", "learn", "learning", "reason", "truth", "wisdom", "jnana"},
    "devotion": {"devotion", "devotional", "worship", "bhakti", "love"},
    "detachment": {"detachment", "attachment", "renunciation", "desire", "desires"},
    "freedom": {"freedom", "free", "liberation", "liberate", "bound", "bondage"},
}

# Internal retrieval metadata. These tags do not alter or claim to authenticate the source text.
INFERRED_TAGS = {
    "themes": {
        "self_belief": ("confidence", "strength", "capable", "ability", "perfect", "self"),
        "fear": ("fear", "fearless", "afraid", "scared", "courage"),
        "failure": ("failure", "fail", "mistake", "setback", "fall"),
        "resilience": ("resilience", "persevere", "overcome", "struggle", "endure", "courage"),
        "discipline": ("discipline", "practice", "control", "steadiness", "work", "effort"),
        "purpose": ("purpose", "duty", "meaning", "goal", "work"),
        "comparison": ("compare", "comparison", "others", "competition"),
        "academic_pressure": ("exam", "study", "education", "college", "school", "student"),
        "knowledge": ("knowledge", "reason", "truth", "wisdom", "jnana"),
        "devotion": ("devotion", "worship", "bhakti", "love"),
        "detachment": ("detachment", "attachment", "renunciation", "desire"),
        "freedom": ("freedom", "free", "liberation", "bondage"),
        "service": ("service", "humanity", "serve", "help"),
        "relationships": ("family", "friend", "friendship", "relationship", "marriage"),
    },
    "emotions": {
        "fear": ("fear", "afraid", "scared", "worried", "anxiety", "anxious"),
        "self_doubt": ("doubt", "incapable", "insecure", "unworthy"),
        "hope": ("hope", "hopeful", "optimism", "bright", "future"),
        "joy": ("joy", "bliss", "happiness", "happy", "delight"),
        "sadness": ("sorrow", "sad", "misery", "grief"),
        "anger": ("anger", "angry", "rage"),
        "loneliness": ("lonely", "alone", "isolated"),
        "grief": ("grief", "loss", "death", "died"),
        "confusion": ("confused", "confusion", "uncertain", "doubt"),
    },
    "challenges": {
        "failure": ("failure", "fail", "mistake", "setback"),
        "stress": ("stress", "pressure", "strain", "burden"),
        "motivation": ("motivation", "motivated", "discouraged", "inspiration"),
        "comparison": ("compare", "comparison", "others", "competition"),
        "academic_pressure": ("exam", "study", "marks", "grades", "college", "school"),
        "career": ("career", "profession", "job", "work", "future"),
        "relationships": ("relationship", "family", "partner", "friendship", "marriage"),
        "feeling_lost": ("lost", "direction", "purpose", "meaning"),
        "decision_making": ("decision", "choice", "choose", "decide"),
        "discipline": ("discipline", "procrastination", "routine", "consistency", "habit"),
        "confidence": ("confidence", "capable", "ability", "self_doubt"),
    },
}


@dataclass(frozen=True)
class RetrievalTerms:
    terms: set[str]


@dataclass(frozen=True)
class _TeachingIndexRow:
    teaching_id: str
    metadata_terms: frozenset[str]
    body_terms: frozenset[str]


class TeachingSearchIndex:
    """In-memory inverted index built once per process from active teachings.

    This avoids loading/tokenizing a multi-million-word corpus on every request.
    The index is invalidated after canonical JSON ingestion.
    """

    def __init__(self, db: Session) -> None:
        self.bind_id = id(db.get_bind())
        self.rows: dict[str, _TeachingIndexRow] = {}
        self.metadata_postings: dict[str, list[str]] = defaultdict(list)
        self.body_postings: dict[str, list[str]] = defaultdict(list)
        self._build(db)

    def _build(self, db: Session) -> None:
        rows = db.execute(
            select(
                Teaching.id,
                Teaching.quote,
                Teaching.context,
                Teaching.themes,
                Teaching.emotions,
                Teaching.challenges,
                Teaching.keywords,
                Teaching.source_title,
                Teaching.source_volume,
            ).where(Teaching.is_active.is_(True))
        ).all()
        for row in rows:
            combined = " ".join(
                filter(
                    None,
                    [row.quote, row.context, row.source_title, row.source_volume, " ".join(row.keywords or [])],
                )
            )
            inferred = infer_source_metadata(combined)
            metadata_terms = _field_terms([
                *(row.themes or []), *(row.emotions or []), *(row.challenges or []), *(row.keywords or []),
                *inferred["themes"], *inferred["emotions"], *inferred["challenges"],
            ])
            body_terms = tokenize(f"{row.quote} {row.context or ''}")
            indexed = _TeachingIndexRow(row.id, frozenset(metadata_terms), frozenset(body_terms))
            self.rows[row.id] = indexed
            for term in metadata_terms:
                self.metadata_postings[term].append(row.id)
            for term in body_terms:
                self.body_postings[term].append(row.id)


_INDEX: TeachingSearchIndex | None = None
_INDEX_BIND_ID: int | None = None


def invalidate_teaching_index() -> None:
    global _INDEX, _INDEX_BIND_ID
    _INDEX = None
    _INDEX_BIND_ID = None


def _get_index(db: Session) -> TeachingSearchIndex:
    global _INDEX, _INDEX_BIND_ID
    bind_id = id(db.get_bind())
    if _INDEX is None or _INDEX_BIND_ID != bind_id:
        _INDEX = TeachingSearchIndex(db)
        _INDEX_BIND_ID = bind_id
    return _INDEX


def warm_teaching_index(db: Session) -> int:
    index = _get_index(db)
    return len(index.rows)


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


def _field_terms(values: list[Any]) -> set[str]:
    out: set[str] = set()
    for value in values or []:
        out |= tokenize(str(value))
    return out


def infer_source_metadata(text: str) -> dict[str, list[str]]:
    lower = text.lower()
    result: dict[str, list[str]] = {category: [] for category in INFERRED_TAGS}
    for category, mapping in INFERRED_TAGS.items():
        scores: list[tuple[int, str]] = []
        for tag, phrases in mapping.items():
            score = sum(1 for phrase in phrases if phrase in lower)
            if score:
                scores.append((score, tag))
        result[category] = [tag for _, tag in sorted(scores, key=lambda x: (-x[0], x[1]))[:6]]
    return result


def infer_retrieval_lists(*, title: str, volume: str | None, text: str, context: str | None = None) -> dict[str, list[str]]:
    combined = " ".join(filter(None, [title, volume, text, context]))
    inferred = infer_source_metadata(combined)
    keywords = list(dict.fromkeys([title.lower(), *(filter(None, [volume.lower() if volume else None])), *inferred["themes"], *inferred["emotions"], *inferred["challenges"]]))
    return {
        "themes": inferred["themes"][:6],
        "emotions": inferred["emotions"][:6],
        "challenges": inferred["challenges"][:6],
        "keywords": keywords[:18],
    }



def teaching_score(teaching: Teaching, terms: set[str]) -> tuple[int, int, int]:
    """Return (weighted_score, metadata_overlap, body_overlap) for ranking tests and diagnostics."""
    metadata = _field_terms([*(teaching.themes or []), *(teaching.emotions or []), *(teaching.challenges or []), *(teaching.keywords or [])])
    metadata_overlap = len(metadata & terms)
    body_overlap = len(tokenize(f"{teaching.quote} {teaching.context or ''}") & terms)
    return (metadata_overlap * 5 + body_overlap, metadata_overlap, body_overlap)

def retrieve_teachings(db: Session, terms: RetrievalTerms, limit: int = 7) -> list[Teaching]:
    if limit <= 0 or not terms.terms:
        return []
    index = _get_index(db)
    scores: dict[str, tuple[int, int, int]] = {}
    for term in terms.terms:
        for teaching_id in index.metadata_postings.get(term, ()):
            score, meta_overlap, text_overlap = scores.get(teaching_id, (0, 0, 0))
            scores[teaching_id] = (score + 5, meta_overlap + 1, text_overlap)
        for teaching_id in index.body_postings.get(term, ()):
            score, meta_overlap, text_overlap = scores.get(teaching_id, (0, 0, 0))
            scores[teaching_id] = (score + 1, meta_overlap, text_overlap + 1)

    ranked_ids = sorted(
        scores,
        key=lambda teaching_id: (scores[teaching_id][0], scores[teaching_id][1], scores[teaching_id][2], teaching_id),
        reverse=True,
    )[:limit]
    if not ranked_ids:
        return []

    rows = list(db.scalars(select(Teaching).where(Teaching.id.in_(ranked_ids), Teaching.is_active.is_(True))).all())
    by_id = {row.id: row for row in rows}
    return [by_id[teaching_id] for teaching_id in ranked_ids if teaching_id in by_id]


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
