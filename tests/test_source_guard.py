from types import SimpleNamespace
import pytest

from app.services.mentor import teaching_payload, validate_quote_id, SourceGuardError


def test_canonical_teaching_keeps_exact_multiline_text():
    teaching = SimpleNamespace(
        id="Q001",
        quote="Paragraph one.\n\nParagraph two.",
        source_type="sermon",
        source_title="Complete Works",
        source_volume="I",
        source_chapter="3",
        source_page="10-12",
        source_section="Section A",
        source_url="https://example.com",
    )
    payload = teaching_payload(teaching)
    assert payload["quote"] == "Paragraph one.\n\nParagraph two."
    assert payload["source"]["authority"] == "organizer_provided_json"


def test_quote_id_must_be_in_candidate_set():
    assert validate_quote_id("Q001", {"Q001", "Q002"}) == "Q001"
    with pytest.raises(SourceGuardError):
        validate_quote_id("Q999", {"Q001", "Q002"})


def test_null_quote_id_is_allowed():
    assert validate_quote_id(None, {"Q001"}) is None
