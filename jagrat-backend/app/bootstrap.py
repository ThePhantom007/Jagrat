from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import InteractionRecord, JournalEntry, JournalInsight, Profile, Teaching, WeeklyCheckIn

DEMO_ENTRIES = [
    ("I studied for an exam today, but I kept comparing my progress with my friends.", ["comparison", "academic_pressure"], ["fear", "self_doubt"]),
    ("I made a study plan and followed most of it. I still worried that one bad result means I am not capable.", ["failure", "self_belief"], ["fear"]),
    ("I avoided one difficult topic because I was afraid of getting it wrong.", ["fear", "academic_pressure"], ["self_doubt"]),
    ("I asked a friend for help instead of pretending I understood everything.", ["self_belief", "resilience"], ["uncertainty"]),
    ("I finished the questions I had been postponing and felt more in control.", ["discipline", "resilience"], ["relief"]),
    ("I caught myself comparing marks again, then focused on what I could improve next.", ["comparison", "failure"], ["self_doubt"]),
    ("I want next week to be about consistency rather than proving myself in one exam.", ["discipline", "self_belief"], ["hope"]),
]


def seed_demo(db: Session) -> None:
    settings = get_settings()
    profile = db.get(Profile, settings.demo_user_id)
    if profile is None:
        profile = Profile(
            id=settings.demo_user_id,
            display_name="Demo User",
            answers={
                "profession": "student",
                "profession_other": None,
                "age": 20,
                "matters_most": "studies",
                "troubling_most": "confidence",
                "troubling_other": None,
                "problem_approach": "overthink",
                "improve": "discipline",
                "improve_other": None,
            },
        )
        db.add(profile)
        db.flush()

    has_journal = db.scalar(select(JournalEntry.id).where(JournalEntry.profile_id == profile.id).limit(1))
    if has_journal is not None:
        return

    now = datetime.now(timezone.utc)
    for idx, (text, themes, emotions) in enumerate(DEMO_ENTRIES):
        created = now - timedelta(days=6 - idx)
        entry = JournalEntry(profile_id=profile.id, text=text, created_at=created)
        db.add(entry)
        db.flush()
        db.add(
            JournalInsight(
                profile_id=profile.id,
                journal_entry_id=entry.id,
                observation="Wrote about " + ", ".join(t.replace("_", " ") for t in themes) + ".",
                tags=themes,
                themes=themes,
                emotions=emotions,
                created_at=created,
            )
        )
        db.add(InteractionRecord(profile_id=profile.id, themes=themes, created_at=created))

    week_start = now - timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    db.add(
        WeeklyCheckIn(
            profile_id=profile.id,
            week_start=week_start,
            self_belief=6,
            fear=5,
            discipline=7,
            clarity=6,
            resilience=6,
            note="Trying to focus on consistency rather than comparison.",
        )
    )


def bootstrap() -> None:
    from app.db.init_db import init_db
    from app.db.session import SessionLocal

    settings = get_settings()
    init_db()
    if settings.environment == "test":
        return

    csv_path = Path(settings.teachings_csv_path)
    if settings.auto_ingest_teachings and csv_path.exists():
        # Compare the committed CSV against database record hashes. This keeps fresh Render
        # deploys synchronized with a changed organiser CSV without requiring Render shell access.
        from scripts.ingest_teachings import canonical_dataset_fingerprint, import_csv

        expected_fingerprint = canonical_dataset_fingerprint(csv_path)
        with SessionLocal() as db:
            rows = list(db.execute(select(Teaching.id, Teaching.content_sha256)).all())
            db_fingerprint_parts = sorted(f"{row[0]}:{row[1]}" for row in rows)
            import hashlib
            actual_digest = hashlib.sha256(("\n".join(db_fingerprint_parts) + ("\n" if db_fingerprint_parts else "")).encode("utf-8")).hexdigest()

        if actual_digest != expected_fingerprint:
            # Import as a separate transaction; validation occurs before mutation, and the transaction rolls back on error.
            import_csv(csv_path, replace=True)

    if settings.seed_demo_on_startup:
        with SessionLocal() as db:
            seed_demo(db)
            db.commit()
