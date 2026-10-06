import app.models  # noqa: F401
from sqlalchemy import inspect, text

from app.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Profile


def _ensure_compat_schema() -> None:
    """Apply tiny, idempotent compatibility migrations for hackathon deployments.

    SQLAlchemy create_all() does not add columns to an already-existing database.
    This keeps the one small schema evolution we need safe for existing SQLite/Postgres
    databases without introducing a full migration tool for the hackathon.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "teachings" in tables:
        columns = {c["name"] for c in inspector.get_columns("teachings")}
        if "is_active" not in columns:
            with engine.begin() as conn:
                if engine.dialect.name == "postgresql":
                    conn.execute(text("ALTER TABLE teachings ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
                elif engine.dialect.name == "sqlite":
                    conn.execute(text("ALTER TABLE teachings ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
                else:
                    conn.execute(text("ALTER TABLE teachings ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))

    if "profiles" in tables:
        profile_columns = {c["name"] for c in inspector.get_columns("profiles")}
        if "access_token_hash" not in profile_columns:
            with engine.begin() as conn:
                if engine.dialect.name == "postgresql":
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS access_token_hash VARCHAR(64)"))
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_profiles_access_token_hash ON profiles (access_token_hash)"))
                elif engine.dialect.name == "sqlite":
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN access_token_hash VARCHAR(64)"))
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_profiles_access_token_hash ON profiles (access_token_hash)"))
                else:
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN access_token_hash VARCHAR(64)"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_compat_schema()
    settings = get_settings()
    if settings.demo_mode:
        with SessionLocal() as db:
            if db.get(Profile, settings.demo_user_id) is None:
                db.add(Profile(id=settings.demo_user_id, display_name="Demo User", answers={}))
                db.commit()
