from datetime import datetime, timedelta, timezone
from app.models import InteractionRecord, JournalEntry, JournalInsight, Profile, WeeklyCheckIn
from app.services.growth import build_growth


def test_growth_uses_observed_theme_counts(db_session):
    profile = Profile(id="demo", display_name="Friend", answers={})
    db_session.add(profile)
    now = datetime.now(timezone.utc)
    entry = JournalEntry(profile_id="demo", text="wrote about exam comparison", created_at=now)
    db_session.add(entry)
    db_session.flush()
    db_session.add(JournalInsight(profile_id="demo", journal_entry_id=entry.id, observation="Wrote about comparing exams.", themes=["comparison", "academic_pressure"], tags=["comparison"], emotions=["fear"], created_at=now))
    db_session.add(InteractionRecord(profile_id="demo", themes=["comparison"], created_at=now))
    db_session.add(WeeklyCheckIn(profile_id="demo", week_start=now - timedelta(days=now.weekday()), self_belief=6, fear=5, discipline=7, clarity=6, resilience=6, note="self report"))
    db_session.commit()

    result = build_growth(db_session, "demo", days=30)
    comparison = next(item for item in result.reflection_themes_observed if item.theme == "comparison")
    assert comparison.total == 2
    assert result.weekly_check_ins[0]["self_belief"] == 6


def test_weekly_payload_is_strictly_scoped_to_requested_week(db_session):
    from datetime import datetime, timezone, timedelta
    from app.models import JournalEntry, JournalInsight, InteractionRecord
    from app.services.growth import weekly_payload

    profile_id = "weekly-test"
    start = datetime(2026, 9, 28, tzinfo=timezone.utc)
    inside = JournalEntry(profile_id=profile_id, text="inside", created_at=start + timedelta(days=2))
    db_session.add(inside)
    db_session.flush()
    db_session.add(JournalInsight(profile_id=profile_id, journal_entry_id=inside.id, observation="inside", tags=["fear"], themes=["fear"], emotions=["fear"]))
    outside = JournalEntry(profile_id=profile_id, text="outside", created_at=start - timedelta(days=10))
    db_session.add(outside)
    db_session.flush()
    db_session.add(JournalInsight(profile_id=profile_id, journal_entry_id=outside.id, observation="outside", tags=["comparison"], themes=["comparison"], emotions=["self_doubt"]))
    db_session.add(InteractionRecord(profile_id=profile_id, themes=["resilience"], created_at=start + timedelta(days=3)))
    db_session.commit()

    payload = weekly_payload(db_session, profile_id, start, start + timedelta(days=7))
    themes = {item["theme"]: item["total"] for item in payload["reflection_themes_observed"]}
    assert themes == {"fear": 1, "resilience": 1}
