"""Merge organiser/team source exports into one canonical articles.json.

Supported input shapes:
- JSON array of objects
- JSON object
- NDJSON (one JSON object per line)

The merge is deliberately conservative:
- exact duplicate content is merged once;
- richer metadata is combined (paragraphs + URL + tags);
- conflicting source text for the same slug/title/volume fails unless --prefer-longest is used;
- records with no source text are skipped as non-source structural headings.
- no source text is rewritten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").strip()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(x) for x in value if normalize_text(x)]
    text = normalize_text(value)
    return [text] if text else []


def read_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").replace("\u00a0", " ").strip()
    if not text:
        return []

    try:
        payload = json.loads(text)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = [payload]
        else:
            raise ValueError("top-level JSON value must be an object or array")
    except json.JSONDecodeError:
        # Teammate exports may be NDJSON. Parse non-empty lines independently.
        records = []
        for line_no, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: not valid JSON/NDJSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected an object")
            records.append(value)

    out: list[dict[str, Any]] = []
    for idx, raw in enumerate(records):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: record {idx} is not an object")
        title = normalize_text(raw.get("title"))
        volume = normalize_text(raw.get("volume"))
        slug = normalize_text(raw.get("slug"))
        if not title and not slug:
            raise ValueError(f"{path}: record {idx} is missing title and slug")

        paragraphs = as_list(raw.get("paragraphs"))
        if not paragraphs:
            paragraphs = [p for p in normalize_text(raw.get("paragraph")).split("\n\n") if normalize_text(p)]
        if not paragraphs:
            # Some organiser exports contain structural headings with no body text
            # (for example a section heading followed by child records). These are
            # not usable source records and should not block the merge. If another
            # input contains the same record with actual source text, that richer
            # record will still be included.
            continue

        out.append({
            "slug": slug or None,
            "title": title or slug,
            "volume": volume or None,
            "url": normalize_text(raw.get("url")) or normalize_text(raw.get("source_url")) or None,
            "paragraphs": paragraphs,
            "themes": as_list(raw.get("themes")) or as_list(raw.get("theme")),
            "emotions": as_list(raw.get("emotions")) or as_list(raw.get("emotion")),
            "source_type": normalize_text(raw.get("source_type")) or "source_document",
            "context": normalize_text(raw.get("context")) or None,
        })
    return out


def identity(record: dict[str, Any]) -> tuple[str, str, str]:
    return (record.get("slug") or "", record.get("title") or "", record.get("volume") or "")


def source_text(record: dict[str, Any]) -> str:
    return "\n\n".join(record["paragraphs"])


def merge_records(records: list[dict[str, Any]], *, prefer_longest: bool = False) -> tuple[list[dict[str, Any]], dict[str, int]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    exact_duplicates = 0
    metadata_merges = 0
    text_conflicts = 0

    for record in records:
        key = identity(record)
        existing = merged.get(key)
        if existing is None:
            merged[key] = record.copy()
            merged[key]["paragraphs"] = list(record["paragraphs"])
            merged[key]["themes"] = list(record.get("themes", []))
            merged[key]["emotions"] = list(record.get("emotions", []))
            continue

        existing_text = source_text(existing)
        incoming_text = source_text(record)
        if existing_text != incoming_text:
            text_conflicts += 1
            if not prefer_longest:
                raise ValueError(
                    "Conflicting source text for the same record identity "
                    f"slug={key[0]!r}, title={key[1]!r}, volume={key[2]!r}. "
                    "Re-run with --prefer-longest only after checking the source export."
                )
            if len(incoming_text) > len(existing_text):
                existing["paragraphs"] = list(record["paragraphs"])

        before = json.dumps(existing, ensure_ascii=False, sort_keys=True)
        if record.get("url") and not existing.get("url"):
            existing["url"] = record["url"]
        if record.get("context") and not existing.get("context"):
            existing["context"] = record["context"]
        if record.get("source_type") and existing.get("source_type") == "source_document":
            existing["source_type"] = record["source_type"]
        existing["themes"] = list(dict.fromkeys([*existing.get("themes", []), *record.get("themes", [])]))
        existing["emotions"] = list(dict.fromkeys([*existing.get("emotions", []), *record.get("emotions", [])]))
        after = json.dumps(existing, ensure_ascii=False, sort_keys=True)
        if before == after:
            exact_duplicates += 1
        else:
            metadata_merges += 1

    ordered = sorted(merged.values(), key=lambda r: (r.get("volume") or "", r.get("title") or "", r.get("slug") or ""))
    output: list[dict[str, Any]] = []
    for r in ordered:
        item = {
            "slug": r.get("slug"),
            "title": r["title"],
            "volume": r.get("volume"),
            "url": r.get("url"),
            "paragraphs": r["paragraphs"],
        }
        if r.get("themes"):
            item["themes"] = r["themes"]
        if r.get("emotions"):
            item["emotions"] = r["emotions"]
        if r.get("source_type") and r["source_type"] != "source_document":
            item["source_type"] = r["source_type"]
        if r.get("context"):
            item["context"] = r["context"]
        output.append(item)

    return output, {
        "input_records": len(records),
        "output_records": len(output),
        "exact_duplicate_records_merged": exact_duplicates,
        "metadata_merges": metadata_merges,
        "text_conflicts": text_conflicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge organiser-provided Vivekananda JSON source exports")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--prefer-longest", action="store_true", help="On conflicting text for the same identity, retain the longer source text after manual review")
    args = parser.parse_args()

    all_records: list[dict[str, Any]] = []
    for path in args.inputs:
        all_records.extend(read_records(path))

    merged, stats = merge_records(all_records, prefer_longest=args.prefer_longest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
