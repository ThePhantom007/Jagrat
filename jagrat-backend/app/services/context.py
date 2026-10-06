from sqlalchemy import select
import re
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import Conversation, JournalInsight, Message, Profile, ReflectionGoal, Teaching
from app.services.retrieval import retrieve_journal_insights, retrieve_teachings, stem_tokens, terms_from_analysis

MAX_CANDIDATE_TEXT_CHARS = 1800
MAX_CONTEXT_MESSAGE_CHARS = 3000
MAX_JOURNAL_EXCERPT_CHARS = 1800

REQUIRED_ONBOARDING_FIELDS = (
    "profession",
    "age",
    "matters_most",
    "troubling_most",
    "problem_approach",
    "improve",
)


def onboarding_complete(profile) -> bool:
    answers = (profile.answers if profile else {}) or {}
    if not all(answers.get(field) not in (None, "") for field in REQUIRED_ONBOARDING_FIELDS):
        return False
    if answers.get("profession") == "other" and not answers.get("profession_other"):
        return False
    if answers.get("troubling_most") == "other" and not answers.get("troubling_other"):
        return False
    if answers.get("improve") == "other" and not answers.get("improve_other"):
        return False
    return True


def build_retrieval_excerpt(text: str, terms, max_chars: int = 1800) -> str:
    """Return a compact exact-text excerpt for Gemini; full canonical text stays in the database.

    Selects the best sentence window by lexical overlap, then clips to a hard character ceiling.
    The excerpt is never rendered as the canonical teaching in the UI.
    """
    if len(text) <= max_chars:
        return text
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return text[:max_chars]
    # `terms` is a RetrievalTerms (weighted) or a plain set of words. Compare stems on both sides so
    # 'failed' in the text matches 'fail' in the query, and let high-weight (the user's own) terms
    # outweigh vocabulary-bridge expansions when choosing which sentence to show Gemini.
    raw_terms = terms.terms if hasattr(terms, "terms") else terms
    weight_of = terms.weight if hasattr(terms, "weight") else (lambda _t: 1.0)
    term_weights: dict[str, float] = {}
    for t in raw_terms:
        for stem in set(stem_tokens(t)) | {t.lower()}:
            term_weights[stem] = max(term_weights.get(stem, 0.0), weight_of(t))
    scored = []
    for i, sentence in enumerate(sentences):
        words = set(stem_tokens(sentence))
        # Squared weights: one strong term outweighs several weak/common ones.
        score = sum(term_weights[w] ** 2 for w in words if w in term_weights)
        scored.append((score, i, sentence))
    best_score, best_i, best_sentence = max(scored, key=lambda x: (x[0], -x[1]))
    chosen = [best_sentence]
    budget = max_chars - len(best_sentence)
    left = best_i - 1
    right = best_i + 1
    while budget > 80 and (left >= 0 or right < len(sentences)):
        candidates = []
        if left >= 0:
            candidates.append((sentences[left], left))
        if right < len(sentences):
            candidates.append((sentences[right], right))
        if not candidates:
            break
        sent, idx = min(candidates, key=lambda item: (len(item[0]), abs(item[1]-best_i)))
        if len(sent) + 1 > budget:
            break
        if idx < best_i:
            chosen.insert(0, sent)
        else:
            chosen.append(sent)
        budget -= len(sent) + 1
        if idx < best_i:
            left -= 1
        else:
            right += 1
    return " ".join(chosen)[:max_chars]


def build_context(db: Session, *, profile_id: str, current_problem: str, analysis, conversation: Conversation):
    settings = get_settings()
    profile = db.get(Profile, profile_id)
    terms = terms_from_analysis(analysis)
    journal = retrieve_journal_insights(db, profile_id, terms, limit=settings.journal_memory_limit)
    teachings = retrieve_teachings(db, terms, limit=settings.teaching_candidate_limit)

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(settings.max_conversation_messages)
        ).all()
    )
    messages.reverse()

    answers = (profile.answers if profile else {}) or {}
    active_goal = db.scalar(
        select(ReflectionGoal).where(ReflectionGoal.profile_id == profile_id)
    )
    onboarding_profile = {
        "profession": answers.get("profession"),
        "profession_other": answers.get("profession_other"),
        "age": answers.get("age"),
        "matters_most": answers.get("matters_most"),
        "troubling_most": answers.get("troubling_most"),
        "troubling_other": answers.get("troubling_other"),
        "problem_approach": answers.get("problem_approach"),
        "improve": answers.get("improve"),
        "improve_other": answers.get("improve_other"),
    }

    return {
        "profile": {
            "display_name": profile.display_name if profile else "Friend",
            "onboarding": onboarding_profile,
            "active_reflection_goal": {
                "goal_key": active_goal.goal_key,
                "goal_text": active_goal.goal_text,
            } if active_goal else None,
        },
        "relevant_journal_memory": [
            {
                "observation": j.observation,
                "tags": j.tags,
                "themes": j.themes,
                "emotions": j.emotions,
                # Raw diary text is included only for the small, relevance-ranked set.
                # This preserves nuance while avoiding the user's entire diary being sent to Gemini.
                "diary_excerpt": (j.entry.text[:MAX_JOURNAL_EXCERPT_CHARS] if j.entry else ""),
                "written_at": j.entry.created_at.isoformat() if j.entry else None,
            }
            for j in journal
        ],
        "conversation_history": [
            {"role": m.role, "content": (m.content or "")[:MAX_CONTEXT_MESSAGE_CHARS]}
            for m in messages
        ],
        "current_problem": current_problem,
        "analysis": analysis.model_dump(),
        "candidate_teachings": [
            {
                "id": t.id,
                "excerpt": build_retrieval_excerpt(t.quote, terms, settings.max_candidate_excerpt_chars),
                "themes": t.themes,
                "emotions": t.emotions,
                "challenges": t.challenges,
                "keywords": t.keywords,
                "context": t.context,
                "source_title": t.source_title,
                "source_type": t.source_type,
            }
            for t in teachings
        ],
    }
