import pytest

from app.services.mentor import SourceGuardError, validate_ai_written_text


def test_ai_attribution_is_rejected():
    with pytest.raises(SourceGuardError):
        validate_ai_written_text('As Swami Vivekananda said, "Failure is only a stepping stone to success."')


def test_long_fabricated_quote_is_rejected():
    with pytest.raises(SourceGuardError):
        validate_ai_written_text('"A long invented quotation that sounds like a source passage."')


def test_normal_ai_text_is_allowed():
    validate_ai_written_text("This response applies the teaching to the user's present situation without presenting source text as a quote.")
