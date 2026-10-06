import pytest
from sqlalchemy import select

from app.models import InteractionRecord, Profile, Teaching, VivekanandaComparison
from app.schemas import ProblemAnalysis, RiskResult, TextAssessment, TeachingSelection, VivekanandaVsMeGeneration
from app.services.mentor import SourceGuardError
from app.services.vs_me import VivekanandaVsMeService


class FakeGemini:
    def __init__(self, generation):
        self.generation = generation

    def generate(self, **kwargs):
        schema = kwargs.get("schema")
        return self.generation


def assessment():
    return TextAssessment(
        risk=RiskResult(risk_level="none"),
        analysis=ProblemAnalysis(
            emotions=["fear"],
            challenges=["confidence"],
            themes=["self_belief"],
            underlying_belief="I may not be capable enough",
        ),
    )


def add_profile_and_teaching(db_session):
    profile = Profile(
        id="p1",
        display_name="Me",
        answers={
            "profession": "student",
            "age": 20,
            "matters_most": "career",
            "troubling_most": "confidence",
            "problem_approach": "overthink",
            "improve": "courage",
        },
    )
    teaching = Teaching(
        id="T001",
        quote="Canonical exact teaching text about courage and self-belief.",
        themes=["self_belief", "fear"],
        emotions=["fear"],
        challenges=["confidence"],
        keywords=["courage"],
        source_type="speech",
        source_title="Source Speech",
        source_volume="VOLUME 1",
        source_chapter="Paragraphs 1-2",
        source_page=None,
        source_section=None,
        source_url="https://example.com/source",
        context=None,
        content_sha256="1" * 64,
    )
    db_session.add_all([profile, teaching])
    db_session.commit()
    return profile, teaching


def valid_generation(quote_id="T001"):
    return VivekanandaVsMeGeneration(
        teaching=TeachingSelection(quote_id=quote_id),
        where_they_align="Your view values capability and the teaching also points toward inner strength.",
        where_they_differ="Your view treats confidence as something you must first obtain; the teaching invites you to examine that assumption.",
        what_to_examine="Examine whether your current evidence really proves that you lack the capacity to act.",
        questions_for_me=[
            "What evidence shows that you are incapable rather than simply inexperienced?",
            "Would you act differently if confidence were allowed to follow action?",
        ],
        experiment="Take one small task you have been avoiding and complete it before evaluating yourself.",
        conclusion="Use the comparison as a test of your assumption, not as a verdict about your worth.",
    )


def test_creates_comparison_and_renders_exact_canonical_teaching(db_session):
    profile, teaching = add_profile_and_teaching(db_session)
    result = VivekanandaVsMeService(FakeGemini(valid_generation())).create(
        db_session, profile.id, "I think I am not capable enough to take on harder work.", assessment()
    )

    assert result.comparison_id
    assert result.my_view.startswith("I think I am not capable")
    assert result.teaching.quote == teaching.quote
    assert result.teaching.quote != result.where_they_align
    assert result.trust.quote_verified is True
    assert result.trust.rendered_from_backend is True
    assert db_session.scalar(select(VivekanandaComparison)) is not None
    assert db_session.scalar(select(InteractionRecord)) is not None


def test_rejects_model_quote_id_not_in_candidates(db_session):
    profile, _ = add_profile_and_teaching(db_session)
    bad = valid_generation("NOT-A-CANDIDATE")
    with pytest.raises(SourceGuardError):
        VivekanandaVsMeService(FakeGemini(bad)).create(
            db_session, profile.id, "My view", assessment()
        )
    assert db_session.scalar(select(VivekanandaComparison)) is None


def test_blocks_safety_assessment(db_session):
    profile, _ = add_profile_and_teaching(db_session)
    risky = TextAssessment(
        risk=RiskResult(risk_level="high", reason="risk"),
        analysis=ProblemAnalysis(),
    )
    with pytest.raises(RuntimeError, match="SAFETY_TRIGGERED"):
        VivekanandaVsMeService(FakeGemini(valid_generation())).create(
            db_session, profile.id, "I am in danger", risky
        )


def test_can_complete_without_a_teaching(db_session):
    profile = Profile(id="p1", display_name="Me", answers={})
    db_session.add(profile)
    db_session.commit()
    generation = valid_generation(None)
    result = VivekanandaVsMeService(FakeGemini(generation)).create(
        db_session, profile.id, "My view is that I should wait until I feel ready.", assessment()
    )
    assert result.teaching is None
    assert result.trust.quote_verified is False
    assert result.trust.rendered_from_backend is False
    assert result.trust.source_note


def test_merge_source_exports_preserves_richer_fields(tmp_path):
    import json
    from scripts.merge_source_json import merge_records, read_records

    first = tmp_path / "paragraph.json"
    first.write_text(json.dumps([{
        "title": "Same",
        "slug": "same",
        "volume": "VOLUME 1",
        "paragraph": "First paragraph.\n\nSecond paragraph.",
        "theme": "courage",
        "emotion": "fear",
    }]), encoding="utf-8")
    second = tmp_path / "paragraphs.ndjson"
    second.write_text(json.dumps({
        "title": "Same",
        "slug": "same",
        "volume": "VOLUME 1",
        "url": "https://example.com/same",
        "paragraphs": ["First paragraph.", "Second paragraph."],
    }) + "\n", encoding="utf-8")

    merged, stats = merge_records(read_records(first) + read_records(second))
    assert len(merged) == 1
    assert merged[0]["paragraphs"] == ["First paragraph.", "Second paragraph."]
    assert merged[0]["url"] == "https://example.com/same"
    assert merged[0]["themes"] == ["courage"]
    assert merged[0]["emotions"] == ["fear"]
    assert stats["text_conflicts"] == 0
