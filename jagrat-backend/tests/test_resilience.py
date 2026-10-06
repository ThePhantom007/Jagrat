from fastapi import Response
from fastapi.exceptions import HTTPException
from sqlalchemy import select

from app.api.journal import create_journal
from app.api.mentor import mentor
from app.models import Conversation, JournalEntry, Profile, Teaching
from app.schemas import JournalCreateRequest, MentorRequest, MentorResponse, SafetyResponse
from app.services.gemini import GeminiUnavailableError
import app.api.journal as journal_api
import app.api.mentor as mentor_api


class FailingGemini:
    def generate(self, **kwargs):
        raise GeminiUnavailableError("simulated provider failure")


def profile_with_onboarding():
    return Profile(
        id="demo",
        display_name="Demo",
        answers={
            "profession": "student",
            "age": 20,
            "matters_most": "studies",
            "troubling_most": "confidence",
            "problem_approach": "overthink",
            "improve": "discipline",
        },
    )


def test_journal_entry_is_persisted_when_gemini_fails(db_session, monkeypatch):
    profile = profile_with_onboarding()
    db_session.add(profile)
    db_session.commit()
    monkeypatch.setattr(journal_api, "gemini", lambda: FailingGemini())

    response = Response()
    result = create_journal(
        JournalCreateRequest(text="I am worried about my exam."),
        response=response,
        db=db_session,
        profile=profile,
    )

    assert response.status_code == 202
    assert result["analysis_status"] == "pending"
    assert db_session.scalar(select(JournalEntry).where(JournalEntry.profile_id == "demo")) is not None


def test_mentor_persists_retryable_conversation_when_gemini_fails(db_session, monkeypatch):
    profile = profile_with_onboarding()
    db_session.add(profile)
    teaching = Teaching(
        id="T001", quote="A canonical passage.", themes=["fear"], emotions=["fear"], challenges=["failure"], keywords=["courage"],
        source_type="speech", source_title="Source", source_volume="I", source_chapter=None, source_page=None,
        source_section=None, source_url=None, context=None, content_sha256="1" * 64,
    )
    db_session.add(teaching)
    db_session.commit()
    monkeypatch.setattr(mentor_api, "service", lambda: mentor_api.MentorService(FailingGemini()))

    try:
        mentor(
            MentorRequest(message="I am afraid I will fail my exam."),
            db=db_session,
            profile=profile,
        )
    except HTTPException as exc:
        assert exc.status_code == 503
        assert "retry the reflection" in str(exc.detail).lower()
    else:
        raise AssertionError("mentor should surface a 503 when Gemini is unavailable")

    row = db_session.scalar(select(Conversation).order_by(Conversation.created_at.desc()))
    assert row is not None
    assert row is not None
    assert row.problem_analysis["status"] == "pending"


def test_no_matching_teaching_is_a_normal_source_free_response(db_session):
    profile = profile_with_onboarding()
    db_session.add(profile)
    db_session.commit()

    class NullTeachingGemini:
        def generate(self, *, schema, **kwargs):
            from app.schemas import MentorGeneration, ProblemAnalysis, TextAssessment, TeachingSelection, ChallengePayload, ActionPayload
            if schema is TextAssessment:
                return TextAssessment(analysis=ProblemAnalysis(emotions=["fear"], challenges=["career"], themes=["purpose"], underlying_belief="I am lost"))
            if schema is MentorGeneration:
                return MentorGeneration(
                    understanding="This is difficult.",
                    teaching=TeachingSelection(quote_id=None),
                    interpretation="Focus on one decision you can make today.",
                    reflection_question="What is one part of this situation you can examine more clearly?",
                    challenge=ChallengePayload(assumption="I cannot know what to do", question="What evidence supports that?"),
                    action=ActionPayload(action="Write down one decision and one next step.", reason="Make the uncertainty concrete."),
                )
            raise AssertionError(schema)

    monkey = mentor_api.MentorService(NullTeachingGemini())
    result = monkey.create_turn(db_session, "demo", "I have a very unusual problem with no source match")
    assert result.teaching is None
    assert result.trust.quote_verified is False
    assert "No sufficiently relevant" in (result.trust.source_note or "")
