from pathlib import Path
import hashlib

from sqlalchemy import select

from app.config import get_settings
from app.models import Teaching


def _active_db_fingerprint(db) -> str:
    rows = list(db.execute(select(Teaching.id, Teaching.content_sha256).where(Teaching.is_active.is_(True))).all())
    parts = sorted(f"{row[0]}:{row[1]}" for row in rows)
    payload = "\n".join(parts) + ("\n" if parts else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bootstrap() -> None:
    from app.db.init_db import init_db
    from app.db.session import SessionLocal

    settings = get_settings()
    init_db()
    json_path = Path(settings.teachings_json_path)

    if settings.auto_ingest_teachings and json_path.exists():
        from scripts.ingest_articles import dataset_fingerprint, import_json
        expected_fingerprint = dataset_fingerprint(json_path)
        with SessionLocal() as db:
            actual_digest = _active_db_fingerprint(db)
        if actual_digest != expected_fingerprint:
            import_json(json_path, replace=True)

        # Warm the cached inverted index once at startup, rather than on the first user request.
        with SessionLocal() as db:
            from app.services.retrieval import warm_teaching_index
            warm_teaching_index(db)

    # Demo data is opt-in and intended only for local/dev demonstrations.
    if settings.seed_demo_on_startup and settings.environment != "production":
        from app.db.session import SessionLocal
        from scripts.seed_demo import seed_demo
        with SessionLocal() as db:
            seed_demo(db)
            db.commit()
