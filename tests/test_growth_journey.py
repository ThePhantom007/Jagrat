from datetime import datetime, timedelta, timezone

from app.models import Conversation, Profile, Teaching, WeeklyCheckIn
from app.services.growth import build_growth_journey


def teaching(**overrides):
    data = dict(
        id="T001",
        quote="First paragraph.\n\nSecond paragraph.",
        themes=["self_belief"],
        emotions=["fear"],
        challenges=["failure"],
        keywords=["strength"],
        source_type="speech",
        source_title="Organizer Source",
        source_volume="III",
        source_chapter=None,
        source_page=None,
        source_section=None,
        source_url=None,
        context=None,
        content_sha256="0" * 64,
    )
    data.update(overrides)
    return Teaching(**data)


def test_growth_journey_exposes_demo_inspired_features(db_session):
    profile = Profile(id="demo", display_name="Jagrat Demo", answers={})
    db_session.add(profile)
    db_session.add(teaching())
    now = datetime.now(timezone.utc)
    for days_ago in [0, 1, 2]:
        db_session.add(Conversation(
            profile_id="demo",
            current_problem="I am worried about failing.",
            problem_analysis={"themes": ["fear"]},
            selected_teaching_id="T001",
            created_at=now - timedelta(days=days_ago),
        ))
    start = now - timedelta(days=now.weekday())
    db_session.add_all([
        WeeklyCheckIn(profile_id="demo", week_start=start - timedelta(days=7), self_belief=5, fear=7, discipline=6, clarity=5, resilience=5),
        WeeklyCheckIn(profile_id="demo", week_start=start, self_belief=7, fear=5, discipline=8, clarity=6, resilience=7),
    ])
    db_session.commit()

    result = build_growth_journey(db_session, "demo")
    assert result.product == "Jagrat"
    assert result.day_streak == 3
    assert result.total_reflections == 3
    assert len(result.factor_cards) == 5
    assert result.factor_cards[0].change == 2
    assert result.lifetime_factor_trends[-1].fear == 5
    assert result.weekly_anchor is not None
    assert result.weekly_anchor.id == "T001"
