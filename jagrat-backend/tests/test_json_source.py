from pathlib import Path
import json

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
