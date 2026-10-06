import argparse
import hashlib

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models import Teaching


def record_hash(teaching: Teaching) -> str:
    parts = [
        teaching.quote,
        teaching.source_type,
        teaching.source_title,
        teaching.source_volume or "",
        teaching.source_chapter or "",
        teaching.source_page or "",
        teaching.source_section or "",
        teaching.source_url or "",
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def main(ids: list[str]) -> None:
    with SessionLocal() as db:
        rows = [db.get(Teaching, item_id) for item_id in ids]
        missing = [item_id for item_id, row in zip(ids, rows) if row is None]
        tampered = [row.id for row in rows if row is not None and record_hash(row) != row.content_sha256]
        print(f"records_checked={len(ids)}")
        print(f"missing_ids={len(missing)}")
        print(f"hash_mismatches={len(tampered)}")
        print(f"exact_source_records={len(ids) - len(missing) - len(tampered)}")
        if missing:
            print("missing:", ",".join(missing))
        if tampered:
            print("hash_mismatches:", ",".join(tampered))
        print("Authority: organiser_provided_csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit exact source records for the demo slide")
    parser.add_argument("ids", nargs="+", help="Teaching IDs to check")
    main(parser.parse_args().ids)
