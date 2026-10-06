import pytest
from sqlalchemy import select

import app.api.mentor as mentor_api
from app.api.mentor import mentor
from app.models import Conversation, Profile
from app.schemas import MentorRequest, ProblemAnalysis, RiskResult, TextAssessment
from app.services.mentor import (
    SourceGuardError,
    _preview,
    has_long_unsourced_quote,
    validate_ai_written_text,
)
from app.services.safety import local_risk_check


def _profile():
    return Profile(
        id="demo",
        display_name="Demo",
        answers={
            "profession": "student", "age": 20, "matters_most": "studies",
            "troubling_most": "confidence", "problem_approach": "overthink", "improve": "discipline",
        },
    )


class RiskyGemini:
    """Model flags risk even though no local pattern matches."""

    def generate(self, *, schema, **kwargs):
        if schema is TextAssessment:
            return TextAssessment(
                risk=RiskResult(risk_level="high", reason="indirect crisis language"),
                analysis=ProblemAnalysis(emotions=["hopeless"], challenges=[], themes=[], underlying_belief=""),
            )
        raise AssertionError("mentor generation must not run for a safety-flagged first message")


def test_first_mentor_message_honours_model_risk_assessment(db_session, monkeypatch):
    profile = _profile()
    db_session.add(profile)
    db_session.commit()
    monkeypatch.setattr(mentor_api, "service", lambda: mentor_api.MentorService(RiskyGemini()))

    result = mentor(MentorRequest(message="Nothing feels worth it and I am so tired of everything."), db=db_session, profile=profile)

    assert result["status"] == "safety"
    assert any(h["number"] == "14416" for h in result["helplines"])
    conversation = db_session.scalar(select(Conversation))
    assert conversation.risk_flag is True


@pytest.mark.parametrize(
    "text",
    [
        "I want to die", "i wanna die", "I want to take my own life", "I'm thinking of ending my life",
        "everyone would be better off without me", "there is no point in living",
        "I don't want to be alive anymore",
    ],
)
def test_common_direct_crisis_phrases_are_flagged_locally(text):
    assert local_risk_check(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "I failed my exam and feel I'm not capable", "I want to die of embarrassment",
        "I can't keep going to this coaching class", "I'm dying of embarrassment",
    ],
)
def test_ordinary_distress_wording_is_not_flagged_locally(text):
    assert local_risk_check(text) is None


def test_quoted_user_words_are_allowed():
    user = "I failed my examination and feel that I am not capable"
    validate_ai_written_text(f'You said "{user}" and that is heavy.', user_text=user)


def test_two_short_quoted_words_are_not_mistaken_for_one_long_quote():
    validate_ai_written_text('Separate the word "failure" from the event, and treat "capable" as something that grows.')


def test_invented_long_quote_is_still_rejected_even_with_user_text():
    with pytest.raises(SourceGuardError):
        validate_ai_written_text('A teaching says "Strength is life and weakness is death for everyone".', user_text="I failed")
    assert has_long_unsourced_quote("It says \u201cStrength is life and weakness is death for everyone\u201d.")


def test_preview_is_a_prefix_of_the_exact_text_and_short_texts_are_unchanged():
    short = "A short passage."
    assert _preview(short) == short
    long = " ".join(f"Sentence number {i} ends here." for i in range(80))
    preview = _preview(long)
    assert preview.endswith("…")
    assert long.startswith(preview[:-2].rstrip())
