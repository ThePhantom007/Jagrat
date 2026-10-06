from datetime import datetime, timezone

from app.models import ActionFollowUp, ActionItem, Conversation, Profile, ReflectionFeedback, ReflectionGoal, SavedTeaching, Teaching
from app.api.history import history
from app.api.features import todays_reflection


def teaching_row():
    return Teaching(
        id="T001", quote="Paragraph one.\n\nParagraph two.", themes=["fear"], emotions=["fear"], challenges=["failure"],
        keywords=["courage"], source_type="speech", source_title="Source", source_volume="I", source_chapter=None,
        source_page=None, source_section=None, source_url=None, context=None, content_sha256="1" * 64
    )


def test_saved_teaching_and_feedback_tables_work(db_session):
    db_session.add(Profile(id="demo", display_name="Demo", answers={}))
    db_session.add(teaching_row())
    db_session.flush()
    conv = Conversation(profile_id="demo", current_problem="Fear", problem_analysis={"themes": ["fear"]})
    db_session.add(conv)
    db_session.flush()
    db_session.add(SavedTeaching(profile_id="demo", teaching_id="T001"))
    db_session.add(ReflectionFeedback(profile_id="demo", conversation_id=conv.id, helpful=True, reason=None, note="Useful"))
    db_session.commit()
    assert db_session.query(SavedTeaching).count() == 1
    assert db_session.query(ReflectionFeedback).count() == 1


def test_action_followup_records_outcome(db_session):
    db_session.add(Profile(id="demo", display_name="Demo", answers={}))
    action = ActionItem(profile_id="demo", text="Study for 20 minutes", reason="Test")
    db_session.add(action)
    db_session.flush()
    db_session.add(ActionFollowUp(profile_id="demo", action_id=action.id, outcome="partially_completed", note="Did 10 minutes"))
    db_session.commit()
    row = db_session.query(ActionFollowUp).one()
    assert row.outcome == "partially_completed"


def test_history_filters_by_type_and_query(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    db_session.add(Conversation(profile_id="demo", current_problem="Exam failure", problem_analysis={"themes": ["failure"]}))
    db_session.add(ActionItem(profile_id="demo", text="Review exam mistakes", reason="Test"))
    db_session.commit()
    result = history(
        limit=50, item_type="mentor", q="exam", theme=None, db=db_session, profile=profile
    )
    assert len(result.items) == 1
    assert result.items[0].type == "mentor"


def test_todays_reflection_uses_top_recent_theme(db_session):
    from app.models import JournalEntry, JournalInsight
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    for idx in range(2):
        entry = JournalEntry(profile_id="demo", text=f"Fear entry {idx}", created_at=datetime.now(timezone.utc))
        db_session.add(entry)
        db_session.flush()
        db_session.add(JournalInsight(profile_id="demo", journal_entry_id=entry.id, observation="Wrote about fear", themes=["fear"], emotions=["fear"], tags=["fear"]))
    db_session.commit()
    result = todays_reflection(db_session, profile)
    assert result.theme == "fear"
    assert result.prompt


def test_active_reflection_goal_crud(db_session):
    from app.api.growth import delete_reflection_goal, get_reflection_goal, upsert_reflection_goal
    from app.schemas import ReflectionGoalRequest

    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    db_session.commit()

    created = upsert_reflection_goal(
        ReflectionGoalRequest(goal_key="discipline", goal_text="Build consistent study habits"),
        db=db_session, profile=profile,
    )
    assert created.goal_key == "discipline"
    assert created.goal_text == "Build consistent study habits"

    updated = upsert_reflection_goal(
        ReflectionGoalRequest(goal_key="confidence", goal_text="Speak with more confidence"),
        db=db_session, profile=profile,
    )
    assert updated.id == created.id
    assert updated.goal_key == "confidence"

    fetched = get_reflection_goal(db=db_session, profile=profile)
    assert fetched.id == created.id
    assert fetched.goal_text == "Speak with more confidence"

    delete_reflection_goal(db=db_session, profile=profile)
    assert get_reflection_goal(db=db_session, profile=profile) is None


def test_saved_teachings_are_available_in_growth_journey(db_session):
    from app.services.growth import build_growth_journey

    profile = Profile(id="demo", display_name="Demo", answers={})
    teaching = teaching_row()
    db_session.add_all([profile, teaching])
    db_session.flush()
    db_session.add(SavedTeaching(profile_id="demo", teaching_id="T001"))
    db_session.commit()

    result = build_growth_journey(db_session, "demo")
    assert len(result.saved_teachings) == 1
    assert result.saved_teachings[0].teaching_id == "T001"
    assert result.saved_teachings[0].quote == teaching.quote
    assert result.active_goal is None


def test_growth_journey_exposes_active_goal_and_saved_teaching(db_session):
    from app.services.growth import build_growth_journey

    profile = Profile(id="demo", display_name="Demo", answers={})
    teaching = teaching_row()
    goal = ReflectionGoal(profile_id="demo", goal_key="discipline", goal_text="Build consistency")
    db_session.add_all([profile, teaching, goal])
    db_session.flush()
    db_session.add(SavedTeaching(profile_id="demo", teaching_id="T001"))
    db_session.commit()

    result = build_growth_journey(db_session, "demo")
    assert result.active_goal is not None
    assert result.active_goal.goal_key == "discipline"
    assert result.saved_teachings[0].teaching_id == "T001"
