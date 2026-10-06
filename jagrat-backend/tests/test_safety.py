from app.services.safety import local_risk_check, safety_message


def test_high_signal_self_harm_phrase_is_immediate():
    result = local_risk_check("I want to kill myself")
    assert result is not None
    assert result.risk_level == "immediate"


def test_high_signal_harm_to_other_is_immediate():
    result = local_risk_check("I want to hurt someone")
    assert result is not None
    assert result.risk_level == "immediate"


def test_safety_message_contains_india_support():
    payload = safety_message()
    numbers = {item["number"] for item in payload["helplines"]}
    assert "14416" in numbers
    assert "112" in numbers
    assert payload["challenge_available"] is False
