import pytest
from app.services.safety import local_risk_check


@pytest.mark.parametrize(
    "text",
    [
        "I don't want to live anymore",
        "I want to end it all",
        "mujhe nahi jeena hai",
        "main jeena nahi chahta hoon",
        "zindagi khatam karna chahta hoon",
        "khud ko khatam kar doon",
        "khudkhushi",
    ],
)
def test_expanded_high_signal_safety_phrases(text):
    result = local_risk_check(text)
    assert result is not None
    assert result.risk_level == "immediate"


def test_figurative_die_expression_is_not_flagged():
    assert local_risk_check("I'm going to die of embarrassment") is None
