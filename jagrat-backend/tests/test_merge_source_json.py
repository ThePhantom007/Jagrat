import json
import pytest

from scripts.merge_source_json import merge_records, read_records


def test_conflicting_same_identity_fails_without_override():
    records = [
        {"slug":"x","title":"X","volume":"V1","paragraphs":["A"]},
        {"slug":"x","title":"X","volume":"V1","paragraphs":["B"]},
    ]
    with pytest.raises(ValueError, match="Conflicting source text"):
        merge_records(records)


def test_ndjson_and_paragraph_aliases_are_supported(tmp_path):
    p = tmp_path / "mixed.ndjson"
    p.write_text(
        json.dumps({"title":"A","volume":"V1","paragraph":"One.\n\nTwo."}) + "\n"
        + json.dumps({"title":"B","volume":"V1","paragraphs":["Three.","Four."],"source_url":"https://example.com/b"}) + "\n",
        encoding="utf-8",
    )
    rows = read_records(p)
    assert len(rows) == 2
    assert rows[0]["paragraphs"] == ["One.", "Two."]
    assert rows[1]["url"] == "https://example.com/b"


def test_empty_structural_records_are_skipped(tmp_path):
    p = tmp_path / "headings.ndjson"
    p.write_text(
        json.dumps({"title":"A","slug":"a","volume":"V1","paragraphs":[]}) + "\n"
        + json.dumps({"title":"B","slug":"b","volume":"V1","paragraphs":["Body"]}) + "\n",
        encoding="utf-8",
    )
    rows = read_records(p)
    assert len(rows) == 1
    assert rows[0]["slug"] == "b"
