from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.api.mentor import get_conversation, sessions
from app.models import Conversation, Message, Profile


def test_active_reflection_session_is_listed_as_resumable(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    conversation = Conversation(
        profile_id="demo",
        current_problem="I keep postponing an important application because I am afraid of rejection.",
        problem_analysis={"themes": ["fear"]},
    )
    db_session.add(conversation)
    db_session.flush()
    db_session.add(Message(
        conversation_id=conversation.id,
        role="user",
        content="I keep postponing an important application because I am afraid of rejection.",
    ))
    db_session.commit()

    result = sessions(status="active", db=db_session, profile=profile)

    assert len(result) == 1
    assert result[0].id == conversation.id
    assert result[0].status == "active"
    assert result[0].resumable is True
    assert result[0].preview.startswith("I keep postponing")
    assert result[0].last_activity_at >= conversation.created_at


def test_completed_reflection_is_not_resumable(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    conversation = Conversation(
        profile_id="demo",
        current_problem="A completed reflection",
        problem_analysis={},
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(conversation)
    db_session.commit()

    active = sessions(status="active", db=db_session, profile=profile)
    completed = sessions(status="completed", db=db_session, profile=profile)

    assert active == []
    assert len(completed) == 1
    assert completed[0].status == "completed"
    assert completed[0].resumable is False


def test_safety_reflection_is_not_resumable(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    db_session.add(Conversation(
        profile_id="demo",
        current_problem="Safety case",
        problem_analysis={},
        risk_flag=True,
    ))
    db_session.commit()

    all_rows = sessions(status="all", db=db_session, profile=profile)

    assert len(all_rows) == 1
    assert all_rows[0].status == "safety"
    assert all_rows[0].resumable is False


def test_get_conversation_exposes_resume_state(db_session):
    profile = Profile(id="demo", display_name="Demo", answers={})
    db_session.add(profile)
    conversation = Conversation(
        profile_id="demo",
        current_problem="I want to finish this reflection later.",
        problem_analysis={"themes": ["discipline"]},
    )
    db_session.add(conversation)
    db_session.commit()

    result = get_conversation(conversation.id, db=db_session, profile=profile)

    assert result["status"] == "active"
    assert result["resumable"] is True
