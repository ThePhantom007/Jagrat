from app.models import Teaching
from app.services.retrieval import RetrievalTerms, teaching_score, retrieve_teachings


def base_teaching(**kwargs):
    data = dict(
        id="T1",
        quote="Stay strong",
        themes=["self_belief"],
        emotions=["fear"],
        challenges=[],
        keywords=["strength"],
        source_type="speech",
        source_title="Organiser source",
        source_volume=None,
        source_chapter=None,
        source_page=None,
        source_section=None,
        source_url=None,
        context=None,
        content_sha256="0" * 64,
    )
    data.update(kwargs)
    return Teaching(**data)


def test_teaching_score_rewards_metadata_match():
    teaching = base_teaching()
    score = teaching_score(teaching, {"self_belief", "fear"})
    assert score[0] > 0
    assert score[1] == 2


def test_retrieval_uses_only_canonical_database_rows(db_session):
    db_session.add_all([
        base_teaching(id="GOOD", quote="Canonical one"),
        base_teaching(id="OTHER", quote="Canonical two", themes=["discipline"], emotions=[]),
    ])
    db_session.commit()
    rows = retrieve_teachings(db_session, RetrievalTerms({"fear"}), limit=7)
    assert [r.id for r in rows] == ["GOOD"]
