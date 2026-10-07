from pathlib import Path
import hashlib
import logging

from sqlalchemy import select

from app.config import get_settings
from app.models import Teaching

logger = logging.getLogger("jagrat.bootstrap")


def _active_db_fingerprint(db) -> str:
    rows = list(db.execute(select(Teaching.id, Teaching.content_sha256).where(Teaching.is_active.is_(True))).all())
    parts = sorted(f"{row[0]}:{row[1]}" for row in rows)
    payload = "\n".join(parts) + ("\n" if parts else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def warn_about_deployment_config(settings) -> list[str]:
    """Log (and return) configuration that is legal but almost certainly wrong for production."""
    problems: list[str] = []
    if settings.environment == "production":
        if settings.database_url.startswith("sqlite"):
            problems.append(
                "DATABASE_URL is SQLite in production: hosted disks are ephemeral, so profiles, journals and "
                "reflections will be lost on redeploy or restart. Use a persistent Postgres database."
            )
        if all(o.startswith("http://localhost") or o.startswith("http://127.0.0.1") for o in settings.cors_origins):
            problems.append("CORS_ORIGINS only allows localhost in production; the deployed frontend will be blocked.")
    if not settings.gemini_api_key:
        problems.append("GEMINI_API_KEY is not set: mentor, journal and Vivekananda-vs-Me requests will return 503.")
    for message in problems:
        logger.warning(message)
    return problems


def bootstrap() -> None:
    from app.db.init_db import init_db
    from app.db.session import SessionLocal

    settings = get_settings()
    warn_about_deployment_config(settings)
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
