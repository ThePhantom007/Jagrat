from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import Conversation, JournalInsight, Message, Profile, Teaching
from app.services.retrieval import retrieve_journal_insights, retrieve_teachings, terms_from_analysis

MAX_CANDIDATE_TEXT_CHARS = 5000
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
                "text": t.quote[:MAX_CANDIDATE_TEXT_CHARS],
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
