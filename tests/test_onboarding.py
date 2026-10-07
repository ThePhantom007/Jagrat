from pydantic import ValidationError
import pytest

from app.schemas import OnboardingRequest


def valid_payload(**overrides):
    payload = {
        "profession": "student",
        "age": 20,
        "matters_most": "studies",
        "troubling_most": "confidence",
        "problem_approach": "overthink",
        "improve": "discipline",
    }
    payload.update(overrides)
    return payload


def test_onboarding_accepts_standard_answers():
    data = OnboardingRequest(**valid_payload())
    assert data.profession == "student"
    assert data.age == 20
    assert data.matters_most == "studies"
    assert data.troubling_most == "confidence"
    assert data.problem_approach == "overthink"
    assert data.improve == "discipline"


def test_onboarding_accepts_other_text_for_profession_trouble_and_improvement():
    data = OnboardingRequest(**valid_payload(
        profession="other",
        profession_other="Artist",
        troubling_most="other",
        troubling_other="Feeling directionless after graduation",
        improve="other",
        improve_other="Public speaking",
    ))
    assert data.profession_other == "Artist"
    assert data.troubling_other == "Feeling directionless after graduation"
    assert data.improve_other == "Public speaking"


@pytest.mark.parametrize(
    "field, value, required_field",
    [
        ("profession", "other", "profession_other"),
        ("troubling_most", "other", "troubling_other"),
        ("improve", "other", "improve_other"),
    ],
)
def test_other_requires_text(field, value, required_field):
    payload = valid_payload(**{field: value})
    with pytest.raises(ValidationError):
        OnboardingRequest(**payload)


def test_non_other_rejects_other_text():
    with pytest.raises(ValidationError):
        OnboardingRequest(**valid_payload(profession_other="Designer"))


def test_onboarding_has_exactly_six_personalization_dimensions():
    data = OnboardingRequest(**valid_payload())
    assert set(data.model_dump().keys()) >= {
        "profession", "age", "matters_most", "troubling_most",
        "problem_approach", "improve"
    }
