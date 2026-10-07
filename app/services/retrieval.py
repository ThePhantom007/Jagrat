from __future__ import annotations

import math
import re
import unicodedata
from array import array
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import JournalInsight, Teaching

# Bump when tokenisation, tag inference or the retrieval lexicon changes in a way that should
# refresh stored retrieval metadata. It is mixed into the per-record fingerprint at ingestion so
# existing deployments re-synchronise their (non-source) retrieval tags on the next startup.
RETRIEVAL_METADATA_VERSION = "retrieval-v2"

# Rows with these source types are kept in the database but are never offered as teachings.
NON_RETRIEVABLE_SOURCE_TYPES = frozenset({"front_matter", "fragment"})
MIN_TEACHING_WORDS = 30  # shorter passages are headers/salutations/stray lines, not teachings

STOPWORDS = {
    "the", "a", "an", "i", "me", "my", "am", "is", "are", "to", "of", "for", "and", "or", "in", "on",
    "it", "this", "that", "with", "be", "not", "feel", "think", "about", "now", "just", "very", "really",
    "as", "by", "from", "into", "your", "you", "we", "our", "they", "their", "them", "he", "she", "his", "her",
    "was", "were", "been", "being", "can", "could", "would", "should", "will", "do", "does", "did", "have", "has",
    "what", "when", "where", "which", "who", "how", "why", "than", "then", "there", "here", "also", "but", "if",
    "so", "at", "its", "too", "any", "all", "some", "more", "most", "such", "no", "nor", "only", "own", "same",
    "am", "im", "ive", "dont", "cant", "wont", "get", "got", "make", "made", "want", "need", "like", "much",
    "feeling", "feels", "felt", "thing", "things", "something", "someone", "always", "never", "still", "even",
}

# Word variants that signal a concept. When one is present, the canonical name (used by stored
# retrieval tags) and the sibling variants are added to the query at reduced weight.
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

# Bridge from how people describe a problem today to the vocabulary Vivekananda uses when
# teaching about it. These only widen the *query*; they never change or invent source text.
# Each entry is (trigger words, expansion words). Expansion words starting with "*" are core
# vocabulary that characterises the teaching on that concern; the rest are weaker supporting words.
BRIDGE: list[tuple[set[str], list[str]]] = [
    ({"capable", "incapable", "inferior", "worthless", "useless", "doubt", "insecure", "inadequate", "stupid",
      "weak", "hopeless", "unworthy", "confidence", "self_belief", "self_doubt", "talent", "intelligent"},
     ["*weakness", "*strength", "*faith", "*yourselves", "*yourself", "*manhood", "*arise", "*awake", "*fearless",
      "*infinite", "*divine", "*destiny", "*potentially", "strong", "believe", "power", "will", "energy", "courage"]),
    ({"fail", "failed", "failure", "exam", "exams", "marks", "grades", "result", "rejected", "rejection",
      "setback", "mistake", "defeat", "resilience", "perseverance"},
     ["*failure", "*struggle", "*perseverance", "*persevere", "*defeat", "*victory", "*patience", "effort", "fall",
      "rise", "success", "experience", "lesson", "courage", "bravely", "weakness", "strength"]),
    ({"fear", "afraid", "scared", "anxious", "anxiety", "worry", "worried", "panic", "nervous", "terror",
      "dread", "fearless", "fearlessness"},
     ["*fearless", "*fearlessness", "*fear", "*coward", "*brave", "*bold", "*courage", "death", "danger",
      "strength", "timid"]),
    ({"decision", "decide", "decision_making", "choice", "choose", "confused", "confusion", "dilemma", "career",
      "crossroads", "uncertain", "unsure", "options", "indecision"},
     ["*duty", "*discrimination", "*ideal", "*selfless", "*unselfish", "*motive", "choose", "judgment", "reason",
      "purpose", "path", "guide", "calm", "clear", "mind"]),
    ({"compare", "comparison", "comparing", "envy", "jealous", "jealousy", "peers", "competition", "behind", "others"},
     ["*envy", "*jealousy", "*rivalry", "*humble", "own", "place", "great", "duty", "individual", "each"]),
    ({"procrastination", "lazy", "laziness", "discipline", "consistency", "habit", "routine", "focus", "concentrate",
      "concentration", "distracted", "motivation", "motivated", "unmotivated"},
     ["*laziness", "*inertia", "*tamas", "*concentration", "*habit", "*practice", "energy", "control", "mind",
      "steady", "regular", "persistent", "will", "activity"]),
    ({"anger", "angry", "stress", "stressed", "overwhelmed", "pressure", "burnout", "tension", "irritated",
      "frustrated", "frustration"},
     ["*anger", "*calm", "*patience", "*peace", "*equanimity", "mind", "control", "serene", "balance", "detach",
      "tranquil", "restless"]),
    ({"lonely", "loneliness", "alone", "isolated", "sad", "sadness", "grief", "loss", "depressed", "empty",
      "hurt", "sorrow", "grieving"},
     ["*sorrow", "*misery", "*grief", "*comfort", "*immortal", "*suffering", "soul", "friend", "love", "hope",
      "cheerful", "happiness", "bliss"]),
    ({"purpose", "meaning", "meaningless", "lost", "aimless", "goal", "direction", "future", "calling", "passion",
      "feeling_lost"},
     ["*ideal", "*goal", "*purpose", "*mission", "*duty", "*selfless", "*highest", "life", "work", "service",
      "realise", "aim"]),
    ({"parents", "family", "relationship", "relationships", "friendship", "marriage", "partner", "betrayal", "trust",
      "breakup", "conflict"},
     ["*love", "*forgive", "*selfless", "*unselfish", "*kindness", "*sacrifice", "family", "duty", "help", "mother",
      "father", "respect"]),
    ({"ego", "pride", "arrogant", "proud", "vanity"},
     ["*ego", "*pride", "*egoism", "*humility", "*vanity", "*selfish", "*humble"]),
    ({"guilt", "guilty", "shame", "ashamed", "regret", "remorse", "forgive", "forgiveness", "disappointment",
      "disappointed", "discouraged", "discouragement", "despair", "hopelessness", "acceptance"},
     ["*forgive", "*sin", "*weakness", "*repent", "*strength", "*hope", "*courage", "regret", "past", "rise",
      "purity", "bravely", "failure"]),
    ({"stuck", "stagnant", "hesitate", "hesitation", "start", "begin", "motivation"},
     ["*arise", "*awake", "*action", "*dare", "*boldly", "energy", "begin", "rise", "work", "stand"]),
]

_CORE_WEIGHT = 0.7
_SUPPORT_WEIGHT = 0.4
# Components of tag-style names (self_belief -> self, belief) are weak evidence on their own; "self" is
# so common in this corpus (Self/Atman) that it is dropped entirely.
_TAG_PART_WEIGHT = 0.6
_DROP_TAG_PARTS = frozenset({"self"})

# Words that describe the *kind* of tag rather than a concept; never useful as a retrieval tag.
GENERIC_TAGS = frozenset({"reflection"})

# Specific, word-boundary phrases (stems) used to infer retrieval tags from passage text. Generic
# words ("self", "work", "free", "control", "love") are deliberately excluded: they match nearly
# every passage and previously made the tags meaningless.
INFERRED_TAGS = {
    "themes": {
        "self_belief": ("confidence", "faith in yourself", "faith in ourselves", "believe in yourself", "weakness",
                        "strength", "manhood", "infinite power", "divine"),
        "fear": ("fear", "fearless", "afraid", "coward", "courage", "terror"),
        "failure": ("failure", "fail", "mistake", "defeat", "defeated"),
        "resilience": ("perseverance", "persevere", "patience", "overcome", "struggle", "endure", "courage"),
        "discipline": ("discipline", "practice", "concentration", "steadiness", "self-control", "habit"),
        "purpose": ("purpose", "duty", "ideal", "goal", "mission"),
        "comparison": ("jealousy", "envy", "rivalry", "competition", "compare"),
        "academic_pressure": ("examination", "exam", "college", "school", "student", "education"),
        "knowledge": ("knowledge", "reason", "truth", "wisdom", "jnana"),
        "devotion": ("devotion", "worship", "bhakti"),
        "detachment": ("detachment", "attachment", "renunciation", "non-attachment"),
        "freedom": ("freedom", "liberation", "bondage"),
        "service": ("service", "humanity", "serve", "serving"),
        "relationships": ("family", "friend", "friendship", "relationship", "marriage", "mother", "father"),
    },
    "emotions": {
        "fear": ("fear", "afraid", "frightened", "terror", "coward"),
        "self_doubt": ("doubt", "incapable", "insecure", "unworthy", "weakness"),
        "hope": ("hope", "hopeful", "optimism", "bright future"),
        "joy": ("joy", "bliss", "happiness", "delight", "cheerful"),
        "sadness": ("sorrow", "misery", "sadness", "weeping"),
        "anger": ("anger", "angry", "rage", "hatred"),
        "loneliness": ("lonely", "loneliness", "forsaken", "friendless"),
        "grief": ("grief", "mourning", "bereaved", "death of"),
        "confusion": ("confused", "confusion", "perplexed", "uncertain"),
    },
    "challenges": {
        "failure": ("failure", "fail", "mistake", "defeat"),
        "stress": ("stress", "worry", "anxiety", "burden"),
        "motivation": ("discouraged", "despondent", "inspiration", "enthusiasm"),
        "comparison": ("jealousy", "envy", "rivalry", "compare"),
        "academic_pressure": ("examination", "exam", "college", "school"),
        "career": ("career", "profession", "livelihood", "occupation"),
        "relationships": ("family", "friendship", "relationship", "marriage"),
        "feeling_lost": ("lost", "aimless", "purpose", "meaning of life"),
        "decision_making": ("decision", "choose", "choice", "decide"),
        "discipline": ("discipline", "procrastination", "laziness", "habit"),
        "confidence": ("confidence", "self-reliance", "weakness", "faith in yourself"),
    },
}


# --------------------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _fold(text: str) -> str:
    """Lower-case and strip diacritics so 'Vedānta' and 'Vedanta' index identically."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def stem_word(word: str) -> str:
    """Very light, dependency-free suffix stripping (fail/failed/failing -> fail)."""
    w = word
    if len(w) <= 3 or "_" in w:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    for suffix in ("ingly", "edly", "ness", "ing", "ed", "ly"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[: -len(suffix)]
    if w.endswith("es") and len(w) > 4 and w[-3] in "sxz":
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def stem_tokens(text: str) -> list[str]:
    """Ordered stems for `text`, without stopwords or very short tokens."""
    out: list[str] = []
    for raw in _WORD_RE.findall(_fold(text)):
        if raw in STOPWORDS:
            continue
        parts = [raw]
        if "_" in raw:  # canonical tags such as self_doubt also match their component words
            parts += [p for p in raw.split("_") if p and p not in STOPWORDS]
        for part in parts:
            if len(part) < 3 and "_" not in part:
                continue
            out.append(stem_word(part))
    return out


_ALIAS_STEMS: dict[str, frozenset[str]] = {
    canonical: frozenset(stem_word(v) for v in variants if " " not in v)
    for canonical, variants in ALIASES.items()
}
_ALIAS_PHRASES: dict[str, tuple[str, ...]] = {
    canonical: tuple(v for v in variants if " " in v) for canonical, variants in ALIASES.items()
}
_BRIDGE_COMPILED: list[tuple[frozenset[str], dict[str, float]]] = [
    (
        frozenset(stem_word(t) for t in triggers),
        {
            stem_word(w.lstrip("*")): (_CORE_WEIGHT if w.startswith("*") else _SUPPORT_WEIGHT)
            for w in reversed(expansion)  # reversed so a core entry wins over a duplicate support entry
        },
    )
    for triggers, expansion in BRIDGE
]


def _alias_canonicals(stems: set[str], lowered: str) -> set[str]:
    found = {canonical for canonical, variants in _ALIAS_STEMS.items() if stems & variants}
    for canonical, phrases in _ALIAS_PHRASES.items():
        if any(p in lowered for p in phrases):
            found.add(canonical)
    return found


def tokenize(text: str) -> set[str]:
    """Stems plus canonical concept names (e.g. 'failed' -> {'fail', 'failure'})."""
    stems = set(stem_tokens(text))
    return stems | _alias_canonicals(stems, _fold(text))


@dataclass(frozen=True)
class RetrievalTerms:
    """Query terms. `terms` is the stem set; `weights` (optional) down-weights inferred expansions."""

    terms: set[str]
    weights: dict[str, float] | None = None
    # True when the query contains a recognised human concern (an alias or bridge concept). Hand-built
    # term sets (tests, tools) are treated as grounded.
    grounded: bool = True

    def weight(self, term: str) -> float:
        if self.weights is None:
            return 1.0
        return self.weights.get(term, 1.0)


def _query_stems(text: str) -> dict[str, float]:
    """Stems for a query string with weights: whole words 1.0, parts of tag names (self_belief) lower."""
    out: dict[str, float] = {}
    for raw in _WORD_RE.findall(_fold(text)):
        if raw in STOPWORDS:
            continue
        if "_" in raw:
            out[raw] = max(out.get(raw, 0.0), 1.0)  # matches stored tag names exactly
            for part in raw.split("_"):
                if part and part not in STOPWORDS and part not in _DROP_TAG_PARTS and len(part) >= 3:
                    stem = stem_word(part)
                    out[stem] = max(out.get(stem, 0.0), _TAG_PART_WEIGHT)
        elif len(raw) >= 3 and raw not in _DROP_TAG_PARTS:
            stem = stem_word(raw)
            out[stem] = max(out.get(stem, 0.0), 1.0)
    return out


def build_query_terms(direct_text: list[str], context_text: str = "") -> RetrievalTerms:
    """Build weighted query terms.

    direct_text: short, high-signal strings (emotions, challenges, themes) at full weight.
    context_text: longer free text (e.g. the user's stated belief) at reduced weight.
    Then widen with alias canonicals and the Vivekananda-vocabulary bridge at lower weights.
    """
    weights: dict[str, float] = {}
    direct: set[str] = set()
    for value in direct_text:
        for stem, w in _query_stems(value).items():
            direct.add(stem)
            weights[stem] = max(weights.get(stem, 0.0), w)
    if context_text:
        for stem in _query_stems(context_text):
            direct.add(stem)
            weights[stem] = max(weights.get(stem, 0.0), 0.7)

    lowered = _fold(" ".join([*direct_text, context_text]))
    grounded = False
    for canonical in _alias_canonicals(direct, lowered):
        grounded = True
        weights[canonical] = max(weights.get(canonical, 0.0), 0.8)
        for variant in _ALIAS_STEMS[canonical]:
            weights[variant] = max(weights.get(variant, 0.0), 0.5)
    for triggers, expansion in _BRIDGE_COMPILED:
        if direct & triggers:
            grounded = True
            for stem, w in expansion.items():
                weights[stem] = max(weights.get(stem, 0.0), w)
    return RetrievalTerms(set(weights), weights, grounded)


def terms_from_analysis(analysis) -> RetrievalTerms:
    direct = [*analysis.emotions, *analysis.challenges, *analysis.themes]
    return build_query_terms(direct, analysis.underlying_belief or "")


def _field_terms(values: list[Any]) -> set[str]:
    out: set[str] = set()
    for value in values or []:
        out |= tokenize(str(value))
    return out


# --------------------------------------------------------------------------------------
# Retrieval-tag inference (ingestion-time metadata; never alters source text)
# --------------------------------------------------------------------------------------

_TAG_PHRASE_STEMS: dict[str, dict[str, tuple[tuple[str, ...], tuple[str, ...]]]] = {}
for _category, _mapping in INFERRED_TAGS.items():
    _TAG_PHRASE_STEMS[_category] = {
        _tag: (
            tuple(stem_word(p) for p in _phrases if " " not in p and "-" not in p),
            tuple(p for p in _phrases if " " in p or "-" in p),
        )
        for _tag, _phrases in _mapping.items()
    }


def infer_source_metadata(text: str) -> dict[str, list[str]]:
    """Infer coarse tags using whole-word matching and a frequency floor.

    A tag needs two mentions in a long passage (one in a short one). Previously tags were assigned by
    raw substring match on any occurrence, which tagged almost every passage with almost every theme.
    """
    folded = _fold(text)
    counts = Counter(stem_tokens(text))
    floor = 2 if len(folded.split()) >= 150 else 1
    result: dict[str, list[str]] = {category: [] for category in INFERRED_TAGS}
    for category, mapping in _TAG_PHRASE_STEMS.items():
        scored: list[tuple[int, str]] = []
        for tag, (stems, phrases) in mapping.items():
            score = sum(counts.get(s, 0) for s in stems) + sum(folded.count(p) for p in phrases)
            if score >= floor:
                scored.append((score, tag))
        result[category] = [tag for _, tag in sorted(scored, key=lambda x: (-x[0], x[1]))[:6]]
    return result


def infer_retrieval_lists(*, title: str, volume: str | None, text: str, context: str | None = None) -> dict[str, list[str]]:
    # Infer from the passage itself (plus any supplied context). The article title is a short, high-signal
    # hint but the volume label is bibliographic and must not influence tags.
    combined = " ".join(filter(None, [title, text, context]))
    inferred = infer_source_metadata(combined)
    keywords = list(dict.fromkeys([
        title.lower(),
        *(filter(None, [volume.lower() if volume else None])),
        *inferred["themes"], *inferred["emotions"], *inferred["challenges"],
    ]))
    return {
        "themes": inferred["themes"][:6],
        "emotions": inferred["emotions"][:6],
        "challenges": inferred["challenges"][:6],
        "keywords": keywords[:18],
    }


def classify_source_type(*, title: str, text: str, declared: str | None) -> str:
    """Mark rows that cannot work as a teaching so retrieval skips them (rows are never deleted)."""
    if declared and declared != "source_document":
        return declared
    if title.strip().upper() == "COVER":
        return "front_matter"
    if len(text.split()) < MIN_TEACHING_WORDS:
        return "fragment"
    return declared or "source_document"


# --------------------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------------------

_BM25_K1 = 1.2
_BM25_B = 0.6
_TAG_BONUS = 0.8
_TAG_BONUS_CAP = 3
_LETTER_FACTOR = 0.75  # salutation/sign-off passages are down-ranked, not excluded
MAX_PASSAGES_PER_ARTICLE = 2
_MIN_SCORE = 2.5
_UNGROUNDED_MIN_SCORE = 18.0
_INFORMATIVE_IDF = 2.8  # terms in more than ~6% of windows (work, mind, life...) do not count as evidence
_RELATIVE_FLOOR = 0.35  # drop candidates scoring far below the best one

_SALUTATION_RE = re.compile(r"\b(?:my dear|dearest|dear|beloved)\b")
_SIGNOFF_RE = re.compile(r"(?:yours(?: ever)?(?: affectionately| in the lord| lovingly)?|ever yours|affectionately)\W*(?:\w+\W*){0,3}$")


def _looks_like_letter(text: str) -> bool:
    head = _fold(text[:240])
    tail = _fold(text[-160:])
    return bool(_SALUTATION_RE.search(head) or _SIGNOFF_RE.search(tail))


def looks_like_letter(text: str) -> bool:
    """Public wrapper so the API can tell the frontend a passage is a personal letter."""
    return _looks_like_letter(text or "")


class TeachingSearchIndex:
    """Compact in-memory BM25 index over active, retrievable teachings.

    Each passage (up to ~900 words) is indexed as several small windows of roughly 60-150 words, and a
    passage is ranked by its best-matching window. Scoring the whole passage diluted focused matches
    inside long, multi-topic passages. The displayed teaching is still the full canonical passage.

    Postings use typed arrays (about 6 bytes per posting) so the corpus fits comfortably on a 512 MB
    host. The index is invalidated after canonical JSON ingestion.
    """

    UNIT_MIN_WORDS = 60

    def __init__(self, db: Session) -> None:
        self.bind_id = id(db.get_bind())
        self.ids: list[str] = []            # passage ids
        self.articles: list[str] = []       # source article per passage
        self.letter: list[bool] = []
        self.unit_passage: array = array("I")  # window -> passage index
        self.unit_len: array = array("I")
        self.postings: dict[str, tuple[array, array]] = {}
        self.tag_postings: dict[str, array] = defaultdict(lambda: array("I"))
        self.avg_len = 1.0
        self.term_idf: dict[str, float] = {}
        self._build(db)

    @classmethod
    def _windows(cls, text: str) -> list[str]:
        windows: list[str] = []
        current: list[str] = []
        words = 0
        for para in (p for p in re.split(r"\n{2,}", text) if p.strip()):
            current.append(para)
            words += len(para.split())
            if words >= cls.UNIT_MIN_WORDS:
                windows.append(" ".join(current))
                current, words = [], 0
        if current:
            if windows and words < cls.UNIT_MIN_WORDS // 2:
                windows[-1] += " " + " ".join(current)
            else:
                windows.append(" ".join(current))
        return windows or [text]

    def _build(self, db: Session) -> None:
        rows = db.execute(
            select(
                Teaching.id, Teaching.quote, Teaching.context, Teaching.themes, Teaching.emotions,
                Teaching.challenges, Teaching.keywords, Teaching.source_title, Teaching.source_type,
            ).where(Teaching.is_active.is_(True))
        ).all()
        total_len = 0
        for row in rows:
            if row.source_type in NON_RETRIEVABLE_SOURCE_TYPES:
                continue
            passage = len(self.ids)
            self.ids.append(row.id)
            self.articles.append(row.source_title or row.id)
            self.letter.append(_looks_like_letter(row.quote or ""))
            extra = f"{row.context or ''} {row.source_title or ''}"
            for window in self._windows(row.quote or ""):
                counts = Counter(stem_tokens(f"{window} {extra}"))
                length = max(sum(counts.values()), 1)
                unit = len(self.unit_passage)
                self.unit_passage.append(passage)
                self.unit_len.append(length)
                total_len += length
                for term, tf in counts.items():
                    entry = self.postings.get(term)
                    if entry is None:
                        entry = (array("I"), array("H"))
                        self.postings[term] = entry
                    entry[0].append(unit)
                    entry[1].append(min(tf, 65535))
            tags = _field_terms([
                t for t in [*(row.themes or []), *(row.emotions or []), *(row.challenges or [])]
                if t not in GENERIC_TAGS
            ])
            for tag in tags:
                self.tag_postings[tag].append(passage)
        self.avg_len = (total_len / len(self.unit_passage)) if self.unit_passage else 1.0
        self.term_idf = {term: self.idf(len(entry[0])) for term, entry in self.postings.items()}

    def __len__(self) -> int:
        return len(self.ids)

    def idf(self, doc_freq: int) -> float:
        n = len(self.unit_passage)
        return math.log(1.0 + (n - doc_freq + 0.5) / (doc_freq + 0.5))

    def rank(self, query: RetrievalTerms, limit: int) -> list[str]:
        if not self.ids or limit <= 0:
            return []
        small = len(self.ids) < 200  # tests/demos: BM25 statistics and coverage rules are meaningless
        unit_score: dict[int, float] = defaultdict(float)
        unit_terms: dict[int, set[str]] = defaultdict(set)

        for term in query.terms:
            entry = self.postings.get(term)
            if entry is None:
                continue
            weight = query.weight(term)
            docs, tfs = entry
            idf = self.idf(len(docs))
            for unit, tf in zip(docs, tfs):
                norm = _BM25_K1 * (1 - _BM25_B + _BM25_B * self.unit_len[unit] / self.avg_len)
                unit_score[unit] += weight * idf * (tf * (_BM25_K1 + 1)) / (tf + norm)
                unit_terms[unit].add(term)

        # Reduce windows to passages: best window plus a small credit for a second matching window.
        # A window only qualifies when it matches enough *informative* terms; ubiquitous words such as
        # "work" or "mind" raise the score a little but are never evidence of relevance on their own.
        best: dict[int, list[float]] = defaultdict(list)
        for unit, score in unit_score.items():
            matched = unit_terms[unit]
            if not small:
                informative = [t for t in matched if self.term_idf.get(t, 0.0) >= _INFORMATIVE_IDF]
                strong = sum(1 for t in informative if query.weight(t) >= 0.8)
                if len(informative) < 2 or (strong < 1 and len(informative) < 3):
                    continue
            best[self.unit_passage[unit]].append(score)

        passage_score: dict[int, float] = {}
        for passage, scores in best.items():
            scores.sort(reverse=True)
            passage_score[passage] = scores[0] + (0.15 * scores[1] if len(scores) > 1 else 0.0)

        # Stored retrieval tags give a small bonus (and, only for tiny corpora, can qualify a passage).
        tag_hits: dict[int, int] = defaultdict(int)
        for term in query.terms:
            for passage in self.tag_postings.get(term, ()):
                if tag_hits[passage] < _TAG_BONUS_CAP and (passage in passage_score or small):
                    tag_hits[passage] += 1
                    passage_score[passage] = passage_score.get(passage, 0.0) + query.weight(term) * _TAG_BONUS

        scored = [
            (score * (_LETTER_FACTOR if self.letter[p] else 1.0), p) for p, score in passage_score.items()
        ]
        if not scored:
            return []
        scored.sort(key=lambda x: (-x[0], self.ids[x[1]]))
        top = scored[0][0]
        if not query.grounded and not small and top < _UNGROUNDED_MIN_SCORE:
            # No recognised human concern in the query (e.g. a question about a laptop): only very strong
            # lexical evidence may produce a teaching. Otherwise return nothing and let the caller say so.
            return []
        if top < _min_score_for(len(self.ids)):
            return []

        chosen: list[str] = []
        per_article: Counter[str] = Counter()
        for score, passage in scored:
            if score < top * _RELATIVE_FLOOR:
                break
            article = self.articles[passage]
            if per_article[article] >= MAX_PASSAGES_PER_ARTICLE:
                continue
            per_article[article] += 1
            chosen.append(self.ids[passage])
            if len(chosen) >= limit:
                break
        return chosen


def _min_score_for(corpus_size: int) -> float:
    # BM25 scores scale with IDF, which is tiny for very small corpora (tests, demos).
    return _MIN_SCORE if corpus_size >= 200 else 0.0


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
    return len(_get_index(db))


def teaching_score(teaching: Teaching, terms: set[str]) -> tuple[int, int, int]:
    """Return (weighted_score, metadata_overlap, body_overlap) for ranking tests and diagnostics."""
    metadata = _field_terms([*(teaching.themes or []), *(teaching.emotions or []), *(teaching.challenges or []), *(teaching.keywords or [])])
    metadata_overlap = len(metadata & terms)
    body_overlap = len(tokenize(f"{teaching.quote} {teaching.context or ''}") & terms)
    return (metadata_overlap * 5 + body_overlap, metadata_overlap, body_overlap)


def retrieve_teachings(db: Session, terms: RetrievalTerms, limit: int = 7) -> list[Teaching]:
    """Return up to `limit` relevant, article-diverse teachings, or [] when nothing is relevant."""
    if limit <= 0 or not terms.terms:
        return []
    ranked_ids = _get_index(db).rank(terms, limit)
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
    # Journal matching uses only the user's own (high-weight) terms, not the teaching-vocabulary expansions.
    own = {t for t in terms.terms if terms.weight(t) >= 0.8}
    ranked = sorted(rows, key=lambda row: (journal_score(row, own), row.created_at), reverse=True)
    return [row for row in ranked if journal_score(row, own) > 0][:limit]
