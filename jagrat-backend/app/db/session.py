from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def normalize_database_url(url: str) -> str:
    # Neon commonly supplies postgresql://...; this app uses psycopg v3.
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


settings = get_settings()
database_url = normalize_database_url(settings.database_url)

if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    # Keep the Render free instance and Neon connection footprint small.
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
