from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpsertRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    answers: dict = Field(default_factory=dict)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    display_name: str
    answers: dict
    created_at: datetime
    updated_at: datetime


class OnboardingRequest(BaseModel):
    profession: Literal["student", "working", "business", "homemaker", "other"]
    profession_other: str | None = Field(default=None, min_length=1, max_length=120)
    age: int = Field(ge=1, le=120)
    matters_most: Literal["studies", "career", "family", "relationships", "health", "money", "personal_growth"]
    troubling_most: Literal["stress", "fear", "confidence", "motivation", "relationships", "career", "feeling_lost", "other"]
    troubling_other: str | None = Field(default=None, min_length=1, max_length=500)
    problem_approach: Literal["face_them", "overthink", "avoid", "ask_others", "depends"]
    improve: Literal["confidence", "focus", "discipline", "courage", "patience", "peace", "decision_making", "other"]
    improve_other: str | None = Field(default=None, min_length=1, max_length=500)

    def model_post_init(self, __context):
        if self.profession == "other" and not self.profession_other:
            raise ValueError("profession_other is required when profession is 'other'")
        if self.profession != "other" and self.profession_other:
            raise ValueError("profession_other should be empty unless profession is 'other'")
        if self.troubling_most == "other" and not self.troubling_other:
            raise ValueError("troubling_other is required when troubling_most is 'other'")
        if self.troubling_most != "other" and self.troubling_other:
            raise ValueError("troubling_other should be empty unless troubling_most is 'other'")
        if self.improve == "other" and not self.improve_other:
            raise ValueError("improve_other is required when improve is 'other'")
        if self.improve != "other" and self.improve_other:
            raise ValueError("improve_other should be empty unless improve is 'other'")


class RiskResult(BaseModel):
    risk_level: Literal["none", "low", "high", "immediate"] = "none"
    reason: str = Field(default="", max_length=500)


class ProblemAnalysis(BaseModel):
    emotions: list[str] = Field(default_factory=list, max_length=8)
    challenges: list[str] = Field(default_factory=list, max_length=8)
    themes: list[str] = Field(default_factory=list, max_length=8)
    underlying_belief: str = Field(default="", max_length=700)


class TextAssessment(BaseModel):
    risk: RiskResult = Field(default_factory=RiskResult)
    analysis: ProblemAnalysis = Field(default_factory=ProblemAnalysis)


class JournalExtraction(BaseModel):
    emotions: list[str] = Field(default_factory=list, max_length=8)
    themes: list[str] = Field(default_factory=list, max_length=8)
    tags: list[str] = Field(default_factory=list, max_length=10)
    observation: str = Field(min_length=1, max_length=800)


class JournalAssessment(BaseModel):
    risk: RiskResult = Field(default_factory=RiskResult)
    extraction: JournalExtraction


class ChallengeAssessment(BaseModel):
    risk: RiskResult = Field(default_factory=RiskResult)
    generation: "ChallengeGeneration"


class JournalCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class JournalUpdateRequest(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=12000)


class JournalInsightUpdateRequest(BaseModel):
    observation: str | None = Field(default=None, min_length=1, max_length=800)
    tags: list[str] | None = Field(default=None, max_length=10)
    themes: list[str] | None = Field(default=None, max_length=8)
    emotions: list[str] | None = Field(default=None, max_length=8)


class JournalInsightResponse(BaseModel):
    id: str
    journal_entry_id: str
    observation: str
    tags: list[str]
    themes: list[str]
    emotions: list[str]
    created_at: datetime


class JournalResponse(BaseModel):
    id: str
    text: str
    risk_flag: bool
    created_at: datetime
    insight: JournalInsightResponse | None


class TeachingSelection(BaseModel):
    quote_id: str | None = Field(default=None, max_length=100)
    reason: str = Field(default="", max_length=1000)


class ChallengePayload(BaseModel):
    assumption: str = Field(min_length=1, max_length=700)
    question: str = Field(min_length=1, max_length=900)


class ActionPayload(BaseModel):
    action: str = Field(min_length=1, max_length=800)
    reason: str = Field(default="", max_length=800)


class MentorGeneration(BaseModel):
    understanding: str = Field(min_length=1, max_length=1500)
    teaching: TeachingSelection
    interpretation: str = Field(min_length=1, max_length=1800)
    reflection_question: str = Field(min_length=1, max_length=900)
    challenge: ChallengePayload
    action: ActionPayload
    # Internal trace used to ensure all six onboarding dimensions were considered.
    personalization_trace: list[Literal[
        "profession",
        "age",
        "matters_most",
        "troubling_most",
        "problem_approach",
        "improve",
    ]] = Field(min_length=6, max_length=6)


class MentorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


class SourceResponse(BaseModel):
    type: str
    title: str
    volume: str | None
    chapter: str | None
    page: str | None
    section: str | None
    url: str | None
    authority: str


class TeachingResponse(BaseModel):
    id: str
    quote: str
    source: SourceResponse


class TrustPanel(BaseModel):
    quote_verified: bool
    quote_id: str | None
    candidate_count: int
    quote_authority: str
    rendered_from_backend: bool
    ai_written_sections: list[str]


class SafetyResponse(BaseModel):
    status: Literal["safety"] = "safety"
    message: str
    helplines: list[dict]
    challenge_available: bool = False


class MentorResponse(BaseModel):
    status: Literal["ok"] = "ok"
    conversation_id: str
    round: int
    understanding: str
    teaching: TeachingResponse | None
    interpretation: str
    reflection_question: str
    challenge: ChallengePayload
    action: ActionPayload
    trust: TrustPanel


class ChallengeRequest(BaseModel):
    user_response: str = Field(min_length=1, max_length=6000)


class ChallengeGeneration(BaseModel):
    assumption: str = Field(min_length=1, max_length=700)
    question: str = Field(min_length=1, max_length=900)
    reflection: str = Field(min_length=1, max_length=1200)
    next_step: str = Field(min_length=1, max_length=800)


ChallengeAssessment.model_rebuild()


class ChallengeResponse(BaseModel):
    status: Literal["ok"] = "ok"
    conversation_id: str
    round: int
    assumption: str
    question: str
    reflection: str
    next_step: str
    action: ActionPayload | None
    completed: bool
    trust: TrustPanel | None = None


class ActionResponse(BaseModel):
    id: str
    text: str
    reason: str
    completed: bool
    created_at: datetime
    completed_at: datetime | None


class CheckInRequest(BaseModel):
    week_start: datetime
    self_belief: int = Field(ge=1, le=10)
    fear: int = Field(ge=1, le=10)
    discipline: int = Field(ge=1, le=10)
    clarity: int = Field(ge=1, le=10)
    resilience: int = Field(ge=1, le=10)
    note: str = Field(default="", max_length=1000)


class ThemeCount(BaseModel):
    theme: str
    total: int
    daily: dict[str, int]


class FactorTrendPoint(BaseModel):
    week_start: datetime
    self_belief: int
    fear: int
    discipline: int
    clarity: int
    resilience: int
    changes: dict[str, int | None] = Field(default_factory=dict)


class GrowthResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    reflection_themes_observed: list[ThemeCount]
    weekly_check_ins: list[dict]
    lifetime_factor_trends: list[FactorTrendPoint] = Field(default_factory=list)
    note: str


class WeeklyReportGeneration(BaseModel):
    summary: str
    recurring_themes: list[str] = Field(default_factory=list, max_length=10)
    positive_changes: list[str] = Field(default_factory=list, max_length=10)
    areas_to_reflect_on: list[str] = Field(default_factory=list, max_length=10)
    next_week_focus: str
    encouragement: str


class HistoryItem(BaseModel):
    id: str
    type: str
    created_at: datetime
    title: str
    summary: str
    data: dict = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class GrowthFactorSnapshot(BaseModel):
    key: str
    label: str
    value: int | None
    change: int | None


class AnchorTeaching(BaseModel):
    id: str
    quote: str
    source: SourceResponse


class GrowthJourneyResponse(BaseModel):
    product: str = "Jagrat"
    day_streak: int
    total_reflections: int
    factor_cards: list[GrowthFactorSnapshot]
    reflection_themes_observed: list[ThemeCount]
    lifetime_factor_trends: list[FactorTrendPoint]
    weekly_report: dict | None
    weekly_anchor: AnchorTeaching | None
    note: str


class WeeklyReportResponse(WeeklyReportGeneration):
    week_start: datetime
    created_at: datetime
    lifetime_factor_trends: list[FactorTrendPoint] = Field(default_factory=list)
    day_streak: int = 0
    total_reflections: int = 0
    factor_cards: list[GrowthFactorSnapshot] = Field(default_factory=list)
    weekly_anchor: AnchorTeaching | None = None
