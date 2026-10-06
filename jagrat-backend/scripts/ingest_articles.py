import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select, update

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: F401
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Teaching
from app.services.retrieval import (
    RETRIEVAL_METADATA_VERSION,
    classify_source_type,
    infer_retrieval_lists,
    invalidate_teaching_index,
)


def sha256_record(*, text: str, source_title: str, source_volume: str | None, source_type: str) -> str:
    # The retrieval-metadata version is part of the record fingerprint so that a change to how retrieval
    # tags are derived refreshes stored tags on existing deployments. Source text is never altered.
    payload = "\n".join([text, source_title, source_volume or "", source_type, RETRIEVAL_METADATA_VERSION])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_article_id(title: str, volume: str, text: str) -> str:
    digest = hashlib.sha256(f"{title}\n{volume}\n{text}".encode("utf-8")).hexdigest()
    return digest[:16].upper()


def normalize_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").strip()


def split_into_passages(paragraphs: list[str], target_words: int = 900, max_paragraphs: int = 4) -> list[tuple[int, int, str]]:
    """Create contiguous multi-paragraph passages without changing source text."""
    clean = [normalize_text(p) for p in paragraphs if normalize_text(p)]
    passages: list[tuple[int, int, str]] = []
    start = 0
    current: list[str] = []
    words = 0

    for idx, para in enumerate(clean):
        para_words = len(para.split())
        if current and ((words + para_words > target_words and len(current) >= 2) or len(current) >= max_paragraphs):
            passages.append((start, idx - 1, "\n\n".join(current)))
            start = idx
            current = []
            words = 0
        current.append(para)
        words += para_words

    if current:
        passages.append((start, len(clean) - 1, "\n\n".join(current)))
    return passages


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    value = normalize_text(value)
    return [value] if value else []


def _read_paragraphs(raw: dict[str, Any], idx: int) -> list[str]:
    paragraphs = raw.get("paragraphs")
    if isinstance(paragraphs, list):
        clean = [normalize_text(p) for p in paragraphs if normalize_text(p)]
        if clean:
            return clean

    # Teammate exports sometimes use one `paragraph` field while embedding
    # paragraph boundaries as blank lines. Accept that shape as a compatibility
    # input, but store the canonical text only after deterministic splitting.
    paragraph = raw.get("paragraph")
    if isinstance(paragraph, str) and paragraph.strip():
        clean = [normalize_text(p) for p in paragraph.split("\n\n") if normalize_text(p)]
        if clean:
            return clean

    raise ValueError(f"Record {idx}: paragraphs must be a non-empty array or paragraph must contain text")


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
        slug = normalize_text(raw.get("slug")) or None
        if not title:
            raise ValueError(f"Record {idx}: missing title")
        clean_paragraphs = _read_paragraphs(raw, idx)
        full_text = "\n\n".join(clean_paragraphs)
        content_key = hashlib.sha256(f"{title}\n{volume}\n{full_text}".encode("utf-8")).hexdigest()
        if content_key in seen:
            duplicate_count += 1
            continue
        seen.add(content_key)

        explicit_themes = _as_list(raw.get("themes")) or _as_list(raw.get("theme"))
        explicit_emotions = _as_list(raw.get("emotions")) or _as_list(raw.get("emotion"))
        source_url = normalize_text(raw.get("source_url")) or normalize_text(raw.get("url")) or None
        unique.append(
            {
                "title": title,
                "slug": slug,
                "volume": volume or None,
                "paragraphs": clean_paragraphs,
                "source_type": normalize_text(raw.get("source_type")) or "source_document",
                "source_url": source_url,
                "context": normalize_text(raw.get("context")) or None,
                # These are retrieval hints only; canonical source text remains in paragraphs.
                "themes": explicit_themes,
                "emotions": explicit_emotions,
            }
        )
    if not unique:
        raise ValueError("The source JSON contains no usable unique articles")
    return unique, {"input_records": len(payload), "unique_articles": len(unique), "duplicates_removed": duplicate_count}


def article_to_rows(article: dict[str, Any], with_metadata: bool = True) -> list[dict[str, Any]]:
    title = article["title"]
    volume = article["volume"]
    declared_type = article["source_type"]
    passages = split_into_passages(article["paragraphs"])
    article_full = "\n\n".join(article["paragraphs"])
    article_id = stable_article_id(title, volume or "", article_full)
    rows = []
    for number, (start, end, text) in enumerate(passages, start=1):
        # Cover metadata and tiny fragments stay in the database (nothing is deleted) but are flagged so
        # retrieval never offers them as a teaching.
        source_type = classify_source_type(title=title, text=text, declared=declared_type)
        if with_metadata:
            metadata = infer_retrieval_lists(title=title, volume=volume, text=text, context=article["context"])
            # Teammate-supplied tags are optional retrieval hints. Deterministic inference remains the
            # fallback and canonical source text is never changed by these fields.
            metadata["themes"] = list(dict.fromkeys([*article.get("themes", []), *metadata["themes"]]))[:6]
            metadata["emotions"] = list(dict.fromkeys([*article.get("emotions", []), *metadata["emotions"]]))[:6]
        else:
            # Fingerprinting only needs ids and content hashes; skip the (slow) tag inference at startup.
            metadata = {"themes": [], "emotions": [], "challenges": [], "keywords": []}
        rows.append(
            {
                "id": f"{article_id}-{number:02d}",
                "text": text,
                **metadata,
                "source_type": source_type,
                "source_title": title,
                "source_volume": volume,
                "source_chapter": f"Paragraphs {start + 1}-{end + 1}",
                "source_page": None,
                "source_section": None,
                "source_url": article["source_url"],
                "context": article["context"],
                "content_sha256": sha256_record(text=text, source_title=title, source_volume=volume, source_type=source_type),
            }
        )
    return rows


def load_rows(path: Path, with_metadata: bool = True) -> tuple[list[dict[str, Any]], dict[str, int]]:
    articles, stats = read_articles(path)
    rows: list[dict[str, Any]] = []
    for article in articles:
        rows.extend(article_to_rows(article, with_metadata=with_metadata))
    stats["passages_created"] = len(rows)
    return rows, stats


def dataset_fingerprint(path: Path) -> str:
    rows, _ = load_rows(path, with_metadata=False)
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda r: r["id"]):
        digest.update(f"{row['id']}:{row['content_sha256']}\n".encode("utf-8"))
    return digest.hexdigest()


def import_json(path: Path, replace: bool = False) -> tuple[int, dict[str, int]]:
    """Synchronize canonical JSON without deleting historical teachings.

    `replace` is retained for CLI compatibility but now means "deactivate missing rows"
    rather than destructive deletion. This preserves saved teachings and historical references.
    """
    rows, stats = load_rows(path)
    init_db()
    current_ids = {row["id"] for row in rows}
    with SessionLocal() as db:
        # Never physically delete canonical records; historical references and saved teachings remain valid.
        db.execute(update(Teaching).values(is_active=False))
        inserted = 0
        updated = 0
        # One query for all existing rows instead of one round trip per passage: against a remote
        # Postgres (Neon/Render) the per-row lookup made the first import take minutes.
        existing_by_id = {t.id: t for t in db.scalars(select(Teaching)).all()}
        for row in rows:
            existing = existing_by_id.get(row["id"])
            if existing is None:
                db.add(
                    Teaching(
                        id=row["id"], quote=row["text"], themes=row["themes"], emotions=row["emotions"],
                        challenges=row["challenges"], keywords=row["keywords"], source_type=row["source_type"],
                        source_title=row["source_title"], source_volume=row["source_volume"], source_chapter=row["source_chapter"],
                        source_page=row["source_page"], source_section=row["source_section"], source_url=row["source_url"],
                        context=row["context"], content_sha256=row["content_sha256"], is_active=True,
                    )
                )
                inserted += 1
            else:
                existing.quote = row["text"]
                existing.themes = row["themes"]
                existing.emotions = row["emotions"]
                existing.challenges = row["challenges"]
                existing.keywords = row["keywords"]
                existing.source_type = row["source_type"]
                existing.source_title = row["source_title"]
                existing.source_volume = row["source_volume"]
                existing.source_chapter = row["source_chapter"]
                existing.source_page = row["source_page"]
                existing.source_section = row["source_section"]
                existing.source_url = row["source_url"]
                existing.context = row["context"]
                existing.content_sha256 = row["content_sha256"]
                existing.is_active = True
                updated += 1
        db.commit()
    invalidate_teaching_index()
    stats["inserted"] = inserted
    stats["updated"] = updated
    stats["active_passages"] = len(current_ids)
    return len(rows), stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize organiser-provided canonical teaching JSON")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--replace", action="store_true", help="Compatibility flag; missing rows are deactivated, not deleted")
    args = parser.parse_args()
    count, stats = import_json(args.json_path, replace=args.replace)
    print(f"Synchronized {count} canonical passages. Stats: {json.dumps(stats, ensure_ascii=False)}")
