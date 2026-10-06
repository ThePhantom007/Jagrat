from datetime import datetime, timezone
from app.models import JournalEntry, JournalInsight, Profile, Conversation
from app.services.context import build_context
from app.schemas import ProblemAnalysis


def test_context_contains_relevant_raw_diary_text(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    entry = JournalEntry(profile_id="demo", text="I keep comparing my exam marks with my friends.")
    db_session.add(entry)
    db_session.flush()
    db_session.add(JournalInsight(
        profile_id="demo", journal_entry_id=entry.id, observation="Wrote about comparison.",
        tags=["comparison"], themes=["comparison"], emotions=["fear"]
    ))
    conversation = Conversation(profile_id="demo", current_problem="I am afraid of failing.", problem_analysis={})
    db_session.add(conversation)
    db_session.flush()
    analysis = ProblemAnalysis(emotions=["fear"], challenges=["failure"], themes=["comparison"], underlying_belief="I will fail")
    context = build_context(db_session, profile_id="demo", current_problem=conversation.current_problem, analysis=analysis, conversation=conversation)
    assert context["relevant_journal_memory"]
    assert context["relevant_journal_memory"][0]["diary_excerpt"] == entry.text


def test_context_exposes_all_six_onboarding_dimensions(db_session):
    profile = Profile(
        id="demo2",
        display_name="Demo",
        answers={
            "profession": "student",
            "profession_other": None,
            "age": 20,
            "matters_most": "studies",
            "troubling_most": "confidence",
            "troubling_other": None,
            "problem_approach": "overthink",
            "improve": "discipline",
            "improve_other": None,
        },
    )
    db_session.add(profile)
    db_session.flush()
    conversation = Conversation(profile_id="demo2", current_problem="I cannot focus.", problem_analysis={})
    db_session.add(conversation)
    db_session.flush()
    analysis = ProblemAnalysis(emotions=["self_doubt"], challenges=["discipline"], themes=["focus"], underlying_belief="I cannot stay focused")
    context = build_context(db_session, profile_id="demo2", current_problem=conversation.current_problem, analysis=analysis, conversation=conversation)
    assert set(context["profile"]["onboarding"]) == {
        "profession", "profession_other", "age", "matters_most",
        "troubling_most", "troubling_other", "problem_approach", "improve", "improve_other"
    }
    assert context["profile"]["onboarding"]["age"] == 20
