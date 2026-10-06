"""Retrieval behaviour: stemming, vocabulary bridge, diversity, exclusions, relevance gate."""
import json

from app.models import Teaching
from app.schemas import ProblemAnalysis
from app.services.retrieval import (
    MAX_PASSAGES_PER_ARTICLE,
    RetrievalTerms,
    build_query_terms,
    classify_source_type,
    infer_source_metadata,
    invalidate_teaching_index,
    retrieve_teachings,
    stem_word,
    terms_from_analysis,
    tokenize,
)


def make(id, quote, title="Source", source_type="source_document", themes=None, emotions=None):
    return Teaching(
        id=id, quote=quote, themes=themes or [], emotions=emotions or [], challenges=[], keywords=[],
        source_type=source_type, source_title=title, source_volume=None, source_chapter=None,
        source_page=None, source_section=None, source_url=None, context=None, content_sha256="0" * 64,
    )


FILLER = "The mind moves among many objects and the days pass in work and rest and thought. "


def corpus(db, extra):
    """A >200-passage corpus so BM25 statistics and the relevance rules are active (as in production)."""
    invalidate_teaching_index()
    db.add_all([make(f"F{i:03d}", FILLER * 8 + f" filler number {i} concerns river stone and field.", title=f"Filler {i}") for i in range(260)])
    db.add_all(extra)
    db.commit()


def test_stemming_matches_inflections():
    assert stem_word("failed") == stem_word("failing") == stem_word("fails") == "fail"
    assert "fail" in tokenize("I failed my exam")


def test_underscore_tag_names_do_not_inject_generic_self():
    terms = build_query_terms(["self_belief"])
    assert "self_belief" in terms.terms
    assert "self" not in terms.terms
    assert terms.weight("belief") < 1.0  # components of tag names are weaker evidence than whole words


def test_bridge_maps_modern_wording_to_teaching_vocabulary():
    terms = terms_from_analysis(ProblemAnalysis(
        emotions=["self_doubt"], challenges=["failure"], themes=[], underlying_belief="I am not capable",
    ))
    assert {stem_word("weakness"), "faith", "fearless"} <= terms.terms
    assert terms.weight(stem_word("weakness")) < 1.0 <= terms.weight("failure")  # expansions never outrank the user's own words
    assert terms.grounded is True


def test_query_without_a_recognised_concern_is_not_grounded():
    terms = terms_from_analysis(ProblemAnalysis(
        emotions=[], challenges=["laptop battery drains fast"], themes=["technology"], underlying_belief="my charger broke",
    ))
    assert terms.grounded is False


def test_relevant_passage_is_found_through_the_bridge(db_session):
    corpus(db_session, [make(
        "GOLD",
        "Weakness is death. Have faith in yourselves and be fearless; the failure of today is the strength of tomorrow. " * 3,
        title="On strength",
    )])
    analysis = ProblemAnalysis(emotions=["self_doubt"], challenges=["failure"], themes=["self_belief"],
                               underlying_belief="I failed and I am not capable")
    ids = [t.id for t in retrieve_teachings(db_session, terms_from_analysis(analysis), 7)]
    assert ids and ids[0] == "GOLD"


def test_candidates_come_from_different_articles(db_session):
    corpus(db_session, [
        make(f"S{i}", "Fear is conquered by courage; be fearless and never fear. " * 4, title="Same article")
        for i in range(6)
    ] + [make("OTHER", "Be fearless; fear is weakness and courage is strength. " * 4, title="Another article")])
    terms = terms_from_analysis(ProblemAnalysis(emotions=["fear"], challenges=[], themes=["fearlessness"], underlying_belief=""))
    rows = retrieve_teachings(db_session, terms, 7)
    from collections import Counter
    per_article = Counter(r.source_title for r in rows)
    assert max(per_article.values()) <= MAX_PASSAGES_PER_ARTICLE
    assert "OTHER" in {r.id for r in rows}


def test_front_matter_and_fragments_are_never_offered(db_session):
    text = "Fear and fearlessness, courage against fear; be fearless. " * 4
    corpus(db_session, [
        make("COVER1", text, title="COVER", source_type="front_matter"),
        make("FRAG1", text, title="Tiny", source_type="fragment"),
        make("REAL", text, title="Real teaching"),
    ])
    terms = terms_from_analysis(ProblemAnalysis(emotions=["fear"], challenges=[], themes=["fearlessness"], underlying_belief=""))
    ids = {t.id for t in retrieve_teachings(db_session, terms, 7)}
    assert "REAL" in ids
    assert not ids & {"COVER1", "FRAG1"}


def test_salutation_letters_are_down_ranked_not_removed(db_session):
    body = "Fear is conquered by courage; be fearless and have no fear in your heart. " * 4
    corpus(db_session, [
        make("LETTER", "MY DEAR FRIEND, " + body + " Yours ever affectionately, Vivekananda", title="A letter"),
        make("TALK", body, title="A talk"),
    ])
    terms = terms_from_analysis(ProblemAnalysis(emotions=["fear"], challenges=[], themes=["fearlessness"], underlying_belief=""))
    ids = [t.id for t in retrieve_teachings(db_session, terms, 7)]
    assert ids.index("TALK") < ids.index("LETTER")


def test_unrelated_query_returns_no_teaching(db_session):
    corpus(db_session, [make("T", "Be fearless and conquer fear through courage. " * 4, title="Fear")])
    terms = terms_from_analysis(ProblemAnalysis(
        emotions=[], challenges=["laptop battery drains fast"], themes=["technology"], underlying_belief="my charger broke",
    ))
    assert retrieve_teachings(db_session, terms, 7) == []


def test_common_words_alone_do_not_make_a_passage_relevant(db_session):
    corpus(db_session, [make("T", "The mind and the work and the life of man. " * 6, title="Common words")])
    terms = RetrievalTerms({"mind", "work", "life"}, {"mind": 0.4, "work": 0.4, "life": 0.4}, grounded=True)
    assert retrieve_teachings(db_session, terms, 7) == []


def test_tag_inference_requires_whole_words_and_frequency():
    # "himself" / "worker" must not trigger a theme; one stray mention in a long passage is not enough.
    assert infer_source_metadata("He found himself among the workers of the field. " * 5)["themes"] == []
    long_text = ("The river runs. " * 100) + "Once he spoke of fear."
    assert "fear" not in infer_source_metadata(long_text)["emotions"]
    assert "fear" in infer_source_metadata("Fear and more fear. " * 3)["emotions"]


def test_classify_source_type():
    assert classify_source_type(title="COVER", text="x " * 100, declared="source_document") == "front_matter"
    assert classify_source_type(title="A", text="Too short.", declared="source_document") == "fragment"
    assert classify_source_type(title="A", text="word " * 40, declared="source_document") == "source_document"
    assert classify_source_type(title="A", text="Short.", declared="speech") == "speech"  # explicit types are respected


def test_ingest_flags_but_never_drops_rows_and_keeps_text_exact(tmp_path):
    from scripts.ingest_articles import load_rows
    p = tmp_path / "a.json"
    body = " ".join(["Be fearless and have faith in yourselves."] * 10)
    p.write_text(json.dumps([
        {"title": "COVER", "volume": "COVER", "paragraphs": [body]},
        {"title": "1.1 STUB", "volume": "V1", "paragraphs": ["(Original and Translated)"]},
        {"title": "1.2 TALK", "volume": "V1", "paragraphs": [body, body]},
    ]), encoding="utf-8")
    rows, _ = load_rows(p)
    by_title = {r["source_title"]: r for r in rows}
    assert by_title["COVER"]["source_type"] == "front_matter"
    assert by_title["1.1 STUB"]["source_type"] == "fragment"
    assert by_title["1.2 TALK"]["source_type"] == "source_document"
    assert by_title["1.2 TALK"]["text"] == body + "\n\n" + body  # canonical text is untouched
    assert by_title["1.1 STUB"]["text"] == "(Original and Translated)"


def test_record_fingerprint_changes_with_retrieval_metadata_version(monkeypatch):
    import scripts.ingest_articles as ingest
    before = ingest.sha256_record(text="t", source_title="a", source_volume="v", source_type="x")
    monkeypatch.setattr(ingest, "RETRIEVAL_METADATA_VERSION", "retrieval-vNEXT")
    after = ingest.sha256_record(text="t", source_title="a", source_volume="v", source_type="x")
    assert before != after  # existing deployments re-sync stored tags on the next startup


def test_excerpt_prefers_the_users_own_terms_over_bridge_words():
    from app.services.context import build_retrieval_excerpt
    filler = "The work of the mind goes on and on in life. " * 60
    key = "When failure comes, do not be afraid of it. "
    text = filler + key + filler
    terms = RetrievalTerms({"failure", "work", "mind", "life"}, {"failure": 1.0, "work": 0.4, "mind": 0.4, "life": 0.4})
    assert key.strip() in build_retrieval_excerpt(text, terms, 400)
