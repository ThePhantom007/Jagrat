import argparse
import csv
import hashlib
from pathlib import Path

from sqlalchemy import delete

import app.models  # noqa: F401
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Teaching

SOURCE_TYPES = {"book", "speech", "sermon", "letter", "interview", "conversation", "article", "other"}


def read_canonical_rows(path: Path) -> list[dict[str, object]]:
    """Validate and normalize the canonical CSV without mutating the database."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {"id", "text", "source_type", "source_title"}
        missing = required - fields
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        rows: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            teaching_id = (row.get("id") or "").strip()
            text = row.get("text") or ""
            source_type = (row.get("source_type") or "").strip().lower()
            source_title = (row.get("source_title") or "").strip()
            if not teaching_id:
                raise ValueError(f"Row {row_number}: id is required")
            if teaching_id in seen_ids:
                raise ValueError(f"Row {row_number}: duplicate id {teaching_id!r}")
            if not text.strip():
                raise ValueError(f"Row {row_number}: text is empty")
            if not source_title:
                raise ValueError(f"Row {row_number}: source_title is required")
            if source_type not in SOURCE_TYPES:
                raise ValueError(
                    f"Row {row_number}: unsupported source_type {source_type!r}; expected one of {sorted(SOURCE_TYPES)}"
                )

            source_volume = (row.get("source_volume") or "").strip() or None
            source_chapter = (row.get("source_chapter") or "").strip() or None
            source_page = (row.get("source_page") or "").strip() or None
            source_section = (row.get("source_section") or "").strip() or None
            source_url = (row.get("source_url") or "").strip() or None
            themes = split_pipe(row.get("themes")) or split_pipe(row.get("theme"))
            rows.append({
                "id": teaching_id,
                "text": text,
                "themes": themes,
                "emotions": split_pipe(row.get("emotions")),
                "challenges": split_pipe(row.get("challenges")),
                "keywords": split_pipe(row.get("keywords")),
                "source_type": source_type,
                "source_title": source_title,
                "source_volume": source_volume,
                "source_chapter": source_chapter,
                "source_page": source_page,
                "source_section": source_section,
                "source_url": source_url,
                "context": (row.get("context") or "").strip() or None,
                "content_sha256": sha256_record(
                    text=text, source_type=source_type, source_title=source_title,
                    source_volume=source_volume, source_chapter=source_chapter,
                    source_page=source_page, source_section=source_section, source_url=source_url,
                ),
            })
            seen_ids.add(teaching_id)
    return rows


def canonical_dataset_fingerprint(path: Path) -> str:
    rows = read_canonical_rows(path)
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: str(item["id"])):
        digest.update(f"{row['id']}:{row['content_sha256']}\n".encode("utf-8"))
    return digest.hexdigest()


def split_pipe(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().lower().replace("-", "_") for item in value.split("|") if item.strip()]


def sha256_record(*, text: str, source_type: str, source_title: str, source_volume: str | None, source_chapter: str | None, source_page: str | None, source_section: str | None, source_url: str | None) -> str:
    # Hash the exact stored source text plus normalized source metadata, excluding derived tags.
    parts = [
        text, source_type, source_title, source_volume or "", source_chapter or "",
        source_page or "", source_section or "", source_url or "",
    ]
    canonical = "\x1f".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def import_csv(path: Path, replace: bool = False) -> int:
    init_db()
    rows = read_canonical_rows(path)
    with SessionLocal() as db:
        if replace:
            db.execute(delete(Teaching))
        for row in rows:
            teaching = Teaching(
                id=row["id"],
                quote=row["text"],
                themes=row["themes"],
                emotions=row["emotions"],
                challenges=row["challenges"],
                keywords=row["keywords"],
                source_type=row["source_type"],
                source_title=row["source_title"],
                source_volume=row["source_volume"],
                source_chapter=row["source_chapter"],
                source_page=row["source_page"],
                source_section=row["source_section"],
                source_url=row["source_url"],
                context=row["context"],
                content_sha256=row["content_sha256"],
            )
            db.merge(teaching)
        db.commit()
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import the organiser-provided canonical teaching CSV")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--replace", action="store_true", help="Replace all existing teaching records")
    args = parser.parse_args()
    print(f"Imported {import_csv(args.csv_path, replace=args.replace)} canonical teaching records.")
