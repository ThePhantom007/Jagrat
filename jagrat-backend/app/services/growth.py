from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversation, InteractionRecord, JournalEntry, Teaching, WeeklyCheckIn, WeeklyReport
from app.schemas import AnchorTeaching, FactorTrendPoint, GrowthFactorSnapshot, GrowthJourneyResponse, GrowthResponse, ThemeCount, WeeklyReportGeneration
from app.services.gemini import GeminiService, compact_json
from app.services.prompts import WEEKLY_SYSTEM


def week_start(dt: datetime) -> datetime:
    dt = dt.astimezone(timezone.utc)
    monday = dt - timedelta(days=dt.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)



FACTOR_FIELDS = ("self_belief", "fear", "discipline", "clarity", "resilience")


FACTOR_LABELS = {
    "self_belief": "Self-belief",
    "fear": "Fear Level",
    "discipline": "Mental Discipline",
    "clarity": "Clarity",
    "resilience": "Resilience",
}


def _activity_dates(db: Session, profile_id: str) -> set:
    dates = set()
    journals = db.scalars(select(JournalEntry.created_at).where(JournalEntry.profile_id == profile_id)).all()
    conversations = db.scalars(select(Conversation.created_at).where(Conversation.profile_id == profile_id)).all()
    for dt in [*journals, *conversations]:
        dates.add(dt.astimezone(timezone.utc).date())
    return dates


def calculate_day_streak(db: Session, profile_id: str) -> int:
    dates = _activity_dates(db, profile_id)
    if not dates:
        return 0
    today = datetime.now(timezone.utc).date()
    cursor = today if today in dates else today - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def total_reflections(db: Session, profile_id: str) -> int:
    return len(list(db.scalars(select(Conversation.id).where(Conversation.profile_id == profile_id)).all()))


def current_factor_cards(db: Session, profile_id: str) -> list[GrowthFactorSnapshot]:
    rows = list(db.scalars(select(WeeklyCheckIn).where(WeeklyCheckIn.profile_id == profile_id).order_by(WeeklyCheckIn.week_start.desc())).all())
    latest = rows[0] if rows else None
    previous = rows[1] if len(rows) > 1 else None
    cards = []
    for field in FACTOR_FIELDS:
        value = getattr(latest, field) if latest else None
        change = None if not latest or not previous else value - getattr(previous, field)
        cards.append(GrowthFactorSnapshot(key=field, label=FACTOR_LABELS[field], value=value, change=change))
    return cards


def _weekly_anchor(db: Session, profile_id: str, start: datetime) -> AnchorTeaching | None:
    end = start + timedelta(days=7)
    rows = list(db.scalars(
        select(Conversation)
        .where(Conversation.profile_id == profile_id, Conversation.created_at >= start, Conversation.created_at < end, Conversation.selected_teaching_id.is_not(None))
        .order_by(Conversation.created_at.desc())
    ).all())
    counts = Counter(r.selected_teaching_id for r in rows if r.selected_teaching_id)
    if not counts:
        return None
    teaching_id = counts.most_common(1)[0][0]
    teaching = db.get(Teaching, teaching_id)
    if teaching is None:
        return None
    return AnchorTeaching(
        id=teaching.id,
        quote=teaching.quote,
        source={
            "type": teaching.source_type,
            "title": teaching.source_title,
            "volume": teaching.source_volume,
            "chapter": teaching.source_chapter,
            "page": teaching.source_page,
            "section": teaching.source_section,
            "url": teaching.source_url,
            "authority": "organizer_provided_csv",
        },
    )


def build_growth_journey(db: Session, profile_id: str) -> GrowthJourneyResponse:
    now = datetime.now(timezone.utc)
    start = week_start(now)
    end = start + timedelta(days=7)
    period = _build_growth_period(db, profile_id, start, end)
    report = db.scalar(select(WeeklyReport).where(WeeklyReport.profile_id == profile_id, WeeklyReport.week_start == start))
    report_json = report.report_json if report else None
    return GrowthJourneyResponse(
        day_streak=calculate_day_streak(db, profile_id),
        total_reflections=total_reflections(db, profile_id),
        factor_cards=current_factor_cards(db, profile_id),
        reflection_themes_observed=period.reflection_themes_observed,
        lifetime_factor_trends=lifetime_factor_trends(db, profile_id),
        weekly_report=report_json,
        weekly_anchor=_weekly_anchor(db, profile_id, start),
        note="Theme frequencies are observed reflection themes. Factor values are explicit self-reported weekly check-ins, not clinical measurements.",
    )


def lifetime_factor_trends(db: Session, profile_id: str) -> list[FactorTrendPoint]:
    """Return all weekly self-report points for the lifetime progress graph.

    Changes are raw point-to-point differences, not good/bad judgments.
    """
    rows = list(
        db.scalars(
            select(WeeklyCheckIn)
            .where(WeeklyCheckIn.profile_id == profile_id)
            .order_by(WeeklyCheckIn.week_start.asc())
        ).all()
    )
    previous = None
    points: list[FactorTrendPoint] = []
    for row in rows:
        current = {field: getattr(row, field) for field in FACTOR_FIELDS}
        changes = {field: (None if previous is None else current[field] - previous[field]) for field in FACTOR_FIELDS}
        points.append(FactorTrendPoint(week_start=row.week_start, **current, changes=changes))
        previous = current
    return points


def _add_theme(bucket, theme: str, date_key: str):
    bucket[theme][date_key] += 1


def _build_growth_period(db: Session, profile_id: str, start: datetime, end: datetime) -> GrowthResponse:
    journals = list(db.scalars(select(JournalEntry).where(JournalEntry.profile_id == profile_id, JournalEntry.created_at >= start, JournalEntry.created_at < end)).all())
    interactions = list(db.scalars(select(InteractionRecord).where(InteractionRecord.profile_id == profile_id, InteractionRecord.created_at >= start, InteractionRecord.created_at < end)).all())
    daily = defaultdict(Counter)
    total = Counter()

    for entry in journals:
        themes = entry.insight.themes if entry.insight else []
        key = entry.created_at.astimezone(timezone.utc).date().isoformat()
        for theme in themes:
            normalized = theme.strip().lower().replace("-", "_")
            if normalized:
                total[normalized] += 1
                _add_theme(daily, normalized, key)
    for record in interactions:
        key = record.created_at.astimezone(timezone.utc).date().isoformat()
        for theme in record.themes or []:
            normalized = theme.strip().lower().replace("-", "_")
            if normalized:
                total[normalized] += 1
                _add_theme(daily, normalized, key)

    checkins = list(db.scalars(select(WeeklyCheckIn).where(WeeklyCheckIn.profile_id == profile_id, WeeklyCheckIn.week_start >= start, WeeklyCheckIn.week_start < end).order_by(WeeklyCheckIn.week_start)).all())
    return GrowthResponse(
        period_start=start,
        period_end=end,
        reflection_themes_observed=[
            ThemeCount(theme=theme, total=count, daily=dict(sorted(daily[theme].items())))
            for theme, count in total.most_common(12)
        ],
        weekly_check_ins=[
            {
                "week_start": c.week_start,
                "self_belief": c.self_belief,
                "fear": c.fear,
                "discipline": c.discipline,
                "clarity": c.clarity,
                "resilience": c.resilience,
                "note": c.note,
            }
            for c in checkins
        ],
        lifetime_factor_trends=lifetime_factor_trends(db, profile_id),
        note="Reflection themes observed from journal/mentor activity. Slider values are self-reported check-ins, not clinical measurements.",
    )


def build_growth(db: Session, profile_id: str, days: int = 30) -> GrowthResponse:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return _build_growth_period(db, profile_id, start, end)


def weekly_payload(db: Session, profile_id: str, start: datetime, end: datetime) -> dict:
    # Scope evidence strictly to the requested Monday-to-Monday reporting window.
    growth = _build_growth_period(db, profile_id, start, end)
    growth_themes = [x.model_dump() for x in growth.reflection_themes_observed]
    checkins = list(db.scalars(select(WeeklyCheckIn).where(WeeklyCheckIn.profile_id == profile_id, WeeklyCheckIn.week_start >= start, WeeklyCheckIn.week_start < end).order_by(WeeklyCheckIn.week_start)).all())
    return {
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "reflection_themes_observed": growth_themes,
        "self_reported_checkins": [
            {"week_start": c.week_start.isoformat(), "self_belief": c.self_belief, "fear": c.fear, "discipline": c.discipline, "clarity": c.clarity, "resilience": c.resilience, "note": c.note}
            for c in checkins
        ],
    }


def generate_report(db: Session, profile_id: str, gemini: GeminiService, start: datetime) -> WeeklyReport:
    end = start + timedelta(days=7)
    existing = db.scalar(select(WeeklyReport).where(WeeklyReport.profile_id == profile_id, WeeklyReport.week_start == start))
    if existing:
        return existing
    payload = weekly_payload(db, profile_id, start, end)
    generated = gemini.generate(
        system_instruction=WEEKLY_SYSTEM,
        prompt="Generate the weekly report from this evidence:\n" + compact_json(payload),
        schema=WeeklyReportGeneration,
    )
    row = WeeklyReport(profile_id=profile_id, week_start=start, report_json=generated.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
