import argparse
import sys
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any

from sqlalchemy import delete

import app.models  # noqa: F401
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Teaching


def sha256_record(*, text: str, source_title: str, source_volume: str | None, source_type: str) -> str:
    payload = "\n".join([text, source_title, source_volume or "", source_type])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_article_id(title: str, volume: str, text: str) -> str:
    digest = hashlib.sha256(f"{title}\n{volume}\n{text}".encode("utf-8")).hexdigest()
    return digest[:16].upper()


def normalize_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").strip()


def split_into_passages(paragraphs: list[str], target_words: int = 900, max_paragraphs: int = 4) -> list[tuple[int, int, str]]:
    """Create contiguous, multi-paragraph passages without changing source text.

    A very long paragraph is kept intact rather than silently truncating canonical content.
    The downstream Gemini prompt uses a compact relevance excerpt, while the DB retains the full passage.
    """
    clean = [normalize_text(p) for p in paragraphs if normalize_text(p)]
    passages: list[tuple[int, int, str]] = []
    start = 0
    current: list[str] = []
    words = 0

    for idx, para in enumerate(clean):
        para_words = len(para.split())
        # Prefer at least two paragraphs per passage when possible, but don't merge beyond a reasonable size.
        if current and (words + para_words > target_words and len(current) >= 2) or (current and len(current) >= max_paragraphs):
            passages.append((start, idx - 1, "\n\n".join(current)))
            start = idx
            current = []
            words = 0
        current.append(para)
        words += para_words

    if current:
        passages.append((start, len(clean) - 1, "\n\n".join(current)))
    return passages


def read_articles(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Expected a JSON array of article objects")

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    duplicate_count = 0

    for idx, raw in enumerate(payload):
        if not isinstance(raw, dict):
            raise ValueError(f"Record {idx}: expected an object")
        title = normalize_text(raw.get("title"))
        volume = normalize_text(raw.get("volume"))
        paragraphs = raw.get("paragraphs")
        if not title:
            raise ValueError(f"Record {idx}: missing title")
        if not isinstance(paragraphs, list) or not paragraphs:
            raise ValueError(f"Record {idx}: paragraphs must be a non-empty array")
        clean_paragraphs = [normalize_text(p) for p in paragraphs if normalize_text(p)]
        full_text = "\n\n".join(clean_paragraphs)
        content_key = hashlib.sha256(f"{title}\n{volume}\n{full_text}".encode("utf-8")).hexdigest()
        if content_key in seen:
            duplicate_count += 1
            continue
        seen.add(content_key)
        unique.append({
            "title": title,
            "volume": volume or None,
            "paragraphs": clean_paragraphs,
            "source_type": normalize_text(raw.get("source_type")) or "source_document",
            "source_url": normalize_text(raw.get("source_url")) or None,
            "context": normalize_text(raw.get("context")) or None,
        })
    return unique, {"input_records": len(payload), "unique_articles": len(unique), "duplicates_removed": duplicate_count}


def article_to_rows(article: dict[str, Any]) -> list[dict[str, Any]]:
    title = article["title"]
    volume = article["volume"]
    source_type = article["source_type"]
    passages = split_into_passages(article["paragraphs"])
    article_full = "\n\n".join(article["paragraphs"])
    article_id = stable_article_id(title, volume or "", article_full)
    rows = []
    for number, (start, end, text) in enumerate(passages, start=1):
        teaching_id = f"{article_id}-{number:02d}"
        rows.append({
            "id": teaching_id,
            "text": text,
            "themes": [],
            "emotions": [],
            "challenges": [],
            "keywords": [title.lower(), volume.lower()] if volume else [title.lower()],
            "source_type": source_type,
            "source_title": title,
            "source_volume": volume,
            "source_chapter": f"Paragraphs {start + 1}-{end + 1}",
            "source_page": None,
            "source_section": None,
            "source_url": article["source_url"],
            "context": article["context"],
            "content_sha256": sha256_record(text=text, source_title=title, source_volume=volume, source_type=source_type),
        })
    return rows


def load_rows(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    articles, stats = read_articles(path)
    rows: list[dict[str, Any]] = []
    for article in articles:
        rows.extend(article_to_rows(article))
    stats["passages_created"] = len(rows)
    return rows, stats


def dataset_fingerprint(path: Path) -> str:
    rows, _ = load_rows(path)
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda r: r["id"]):
        digest.update(f"{row['id']}:{row['content_sha256']}\n".encode("utf-8"))
    return digest.hexdigest()


def import_json(path: Path, replace: bool = False) -> tuple[int, dict[str, int]]:
    rows, stats = load_rows(path)
    init_db()
    with SessionLocal() as db:
        if replace:
            db.execute(delete(Teaching))
        for row in rows:
            db.merge(Teaching(
                id=row["id"], quote=row["text"], themes=row["themes"], emotions=row["emotions"],
                challenges=row["challenges"], keywords=row["keywords"], source_type=row["source_type"],
                source_title=row["source_title"], source_volume=row["source_volume"], source_chapter=row["source_chapter"],
                source_page=row["source_page"], source_section=row["source_section"], source_url=row["source_url"],
                context=row["context"], content_sha256=row["content_sha256"],
            ))
        db.commit()
    return len(rows), stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import organiser-provided canonical teaching JSON")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    count, stats = import_json(args.json_path, replace=args.replace)
    print(f"Imported {count} canonical passages. Stats: {json.dumps(stats, ensure_ascii=False)}")
