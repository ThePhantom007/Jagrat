from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), default="Friend")
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    # Opaque anonymous-session credential. Only its SHA-256 hash is stored.
    access_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ReflectionGoal(Base):
    __tablename__ = "reflection_goals"
    __table_args__ = (UniqueConstraint("profile_id", name="uq_reflection_goal_profile"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    goal_key: Mapped[str] = mapped_column(String(60))
    goal_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Teaching(Base):
    __tablename__ = "teachings"

    # Canonical records imported from the organiser-provided JSON.
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    quote: Mapped[str] = mapped_column(Text)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    emotions: Mapped[list] = mapped_column(JSON, default=list)
    challenges: Mapped[list] = mapped_column(JSON, default=list)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    source_type: Mapped[str] = mapped_column(String(40))
    source_title: Mapped[str] = mapped_column(Text)
    source_volume: Mapped[str | None] = mapped_column(String(100))
    source_chapter: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[str | None] = mapped_column(String(100))
    source_section: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class VivekanandaComparison(Base):
    __tablename__ = "vivekananda_comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    user_view: Mapped[str] = mapped_column(Text)
    problem_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_teaching_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teachings.id", ondelete="SET NULL"))
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    profile: Mapped[Profile] = relationship()
    insight: Mapped["JournalInsight | None"] = relationship(back_populates="entry", uselist=False, cascade="all, delete-orphan")


class JournalInsight(Base):
    __tablename__ = "journal_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    journal_entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), unique=True)
    observation: Mapped[str] = mapped_column(Text)
    emotions: Mapped[list] = mapped_column(JSON, default=list)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    entry: Mapped[JournalEntry] = relationship(back_populates="insight")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    current_problem: Mapped[str] = mapped_column(Text)
    problem_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_teaching_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teachings.id", ondelete="SET NULL"))
    rounds_used: Mapped[int] = mapped_column(Integer, default=1)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    challenge_rounds: Mapped[list["ChallengeRound"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="ChallengeRound.round_number")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class ChallengeRound(Base):
    __tablename__ = "challenge_rounds"
    __table_args__ = (UniqueConstraint("conversation_id", "round_number", name="uq_challenge_round"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    round_number: Mapped[int] = mapped_column(Integer)
    belief: Mapped[str] = mapped_column(Text)
    assumption: Mapped[str] = mapped_column(Text)
    challenge_question: Mapped[str] = mapped_column(Text)
    user_response: Mapped[str | None] = mapped_column(Text)
    reflection: Mapped[str | None] = mapped_column(Text)
    next_step: Mapped[str | None] = mapped_column(Text)
    teaching_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teachings.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    conversation: Mapped[Conversation] = relationship(back_populates="challenge_rounds")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"))
    text: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, default="")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class InteractionRecord(Base):
    __tablename__ = "interaction_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"))
    themes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class WeeklyCheckIn(Base):
    __tablename__ = "weekly_checkins"
    __table_args__ = (UniqueConstraint("profile_id", "week_start", name="uq_checkin_profile_week"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    self_belief: Mapped[int] = mapped_column(Integer)
    fear: Mapped[int] = mapped_column(Integer)
    discipline: Mapped[int] = mapped_column(Integer)
    clarity: Mapped[int] = mapped_column(Integer)
    resilience: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (UniqueConstraint("profile_id", "week_start", name="uq_report_profile_week"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    report_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReflectionFeedback(Base):
    __tablename__ = "reflection_feedback"
    __table_args__ = (UniqueConstraint("profile_id", "conversation_id", name="uq_feedback_profile_conversation"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    helpful: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ActionFollowUp(Base):
    __tablename__ = "action_follow_ups"
    __table_args__ = (UniqueConstraint("profile_id", "action_id", name="uq_followup_profile_action"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    action_id: Mapped[str] = mapped_column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), index=True)
    outcome: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SavedTeaching(Base):
    __tablename__ = "saved_teachings"
    __table_args__ = (UniqueConstraint("profile_id", "teaching_id", name="uq_saved_profile_teaching"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    teaching_id: Mapped[str] = mapped_column(String(100), ForeignKey("teachings.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AIRequestTrace(Base):
    __tablename__ = "ai_request_traces"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), index=True)
    operation: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str | None] = mapped_column(String(120))
    candidate_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_quote_id: Mapped[str | None] = mapped_column(String(100))
    safety_status: Mapped[str | None] = mapped_column(String(30))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
