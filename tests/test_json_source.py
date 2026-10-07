from pathlib import Path
import json

from sqlalchemy import select

from scripts.ingest_articles import load_rows, read_articles
from app.services.context import build_retrieval_excerpt


def test_json_source_is_deduplicated_and_paragraph_aware(tmp_path):
    p = tmp_path / "articles.json"
    data = [
        {"title": "A", "volume": "V1", "paragraphs": ["One.", "Two.", "Three."]},
        {"title": "A", "volume": "V1", "paragraphs": ["One.", "Two.", "Three."]},
    ]
    p.write_text(json.dumps(data), encoding="utf-8")
    articles, stats = read_articles(p)
    rows, row_stats = load_rows(p)
    assert len(articles) == 1
    assert stats["duplicates_removed"] == 1
    assert row_stats["passages_created"] == len(rows)
    assert rows[0]["text"] == "One.\n\nTwo.\n\nThree."


def test_gemini_receives_compact_excerpt_not_full_passage():
    text = " ".join(["Fear and courage are connected."] * 400)
    excerpt = build_retrieval_excerpt(text, {"fear", "courage"}, 1800)
    assert len(excerpt) <= 1800

def test_source_audit_detects_duplicates(tmp_path):
    p = tmp_path / "articles.json"
    data = [
        {"title": "A", "volume": "V1", "paragraphs": ["One.", "Two."]},
        {"title": "A", "volume": "V1", "paragraphs": ["One.", "Two."]},
        {"title": "B", "volume": "V1", "paragraphs": ["Three.", "Four."]},
    ]
    p.write_text(json.dumps(data), encoding="utf-8")
    _, stats = read_articles(p)
    assert stats["input_records"] == 3
    assert stats["unique_articles"] == 2
    assert stats["duplicates_removed"] == 1


def test_import_sync_preserves_saved_teaching(monkeypatch, db_session, tmp_path):
    from app.models import SavedTeaching, Teaching
    import scripts.ingest_articles as ingest
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps([{"title":"A","volume":"V1","paragraphs":["One teaching about fear and courage."]}]), encoding="utf-8")
    second.write_text(json.dumps([
        {"title":"A","volume":"V1","paragraphs":["One teaching about fear and courage."]},
        {"title":"B","volume":"V1","paragraphs":["Another teaching about discipline."]},
    ]), encoding="utf-8")

    monkeypatch.setattr(ingest, "init_db", lambda: None)
    monkeypatch.setattr(ingest, "SessionLocal", lambda: db_session)
    ingest.import_json(first)
    original = db_session.scalar(select(Teaching).where(Teaching.is_active.is_(True)))
    original_id = original.id
    db_session.add(SavedTeaching(profile_id="demo", teaching_id=original_id))
    db_session.commit()
    ingest.import_json(second)

    saved = db_session.scalar(select(SavedTeaching).where(SavedTeaching.teaching_id == original_id))
    assert saved is not None
    assert db_session.get(Teaching, original_id) is not None
    assert len(db_session.query(Teaching).all()) == 2
