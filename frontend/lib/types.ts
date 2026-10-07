// ─────────────────────────────────────────────────────────────
// JAGRAT — TypeScript Interfaces
// Frontend types + backend API response shapes (ThePhantom007/Jagrat)
// ─────────────────────────────────────────────────────────────

import type { Language } from './i18n';

// ── User Profile ──────────────────────────────────────────────
export type PrimaryChallenge =
  | 'inner_strength'
  | 'discipline'
  | 'clear_goal'
  | 'overcoming_fear'
  | 'exam_failure'
  | 'self_doubt'
  | 'fear'
  | 'decision_hesitation'
  | 'other';

export type FailureResponse = 'overthinking' | 'withdrawal' | 'quick_reset';

export type PrimaryGoal =
  | 'academic_growth'
  | 'mental_focus'
  | 'inner_strength';

export interface UserProfile {
  name?: string;
  focusArea: string | null;
  primaryChallenge: PrimaryChallenge | null;
  failureResponse: FailureResponse | null;
  confidenceLevel: number; // 1–10
  primaryGoal: PrimaryGoal | null;
  preferredTime?: string;
  language: Language;
  onboardingComplete: boolean;
  // extra fields used for backend onboarding mapping
  profession?: string;
  age?: number;
}

// ── Quote Source ───────────────────────────────────────────────
export interface QuoteSource {
  work: string;            // e.g. "Complete Works of Swami Vivekananda"
  volume?: string;         // only if confirmed in the corpus entry
  page?: string;           // only if confirmed in the corpus entry
  url?: string;            // official link (Belur Math / RKM publications)
}

// ── Documented Teaching ───────────────────────────────────────
export interface DocumentedTeaching {
  id: string;              // corpus entry id
  quote: string;           // verbatim, from data/corpus.json via the guard, never LLM-written
  source: QuoteSource;
  verified: true;          // present only when the guard confirmed the match
}

// ── Mentor Response ───────────────────────────────────────────
export interface MentorResponse {
  listening: { summary: string; question: string };
  documented: DocumentedTeaching | null;  // null => render the no-match card
  reflection: { text: string; nextStep: string };
  challenge?: { belief: string; assumption: string; pivot: string };
  crisis?: boolean;                        // true => render CrisisCard, hide everything else
  conversationId?: string;                 // present on real backend responses; use for multi-turn
}

// ── Chat ──────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  mentorResponse?: MentorResponse;
}

// ── Challenge Card ────────────────────────────────────────────
export interface ChallengeData {
  belief: string;
  assumption: string;
  pivot: string;
}

// ── Journal ───────────────────────────────────────────────────
export type EmotionTag =
  | 'self_doubt'
  | 'academic_pressure'
  | 'peer_comparison'
  | 'fear_of_failure'
  | 'motivation'
  | 'gratitude'
  | 'confusion'
  | 'resilience'
  | 'anxiety'
  | 'hope';

export interface JournalEntry {
  id: string;
  date: string;
  text: string;
  tags: EmotionTag[];
  /** @deprecated use tags.length or text-based word count */
  wordCount?: number;
  /** @deprecated use date */
  timestamp?: number;
  /** @deprecated use text */
  content?: string;
  /** @deprecated use tags */
  extractedTags?: EmotionTag[];
}

// ── Growth Dashboard ──────────────────────────────────────────
export type Trend = 'up' | 'down' | 'steady';
/** @deprecated use Trend */
export type TrendDirection = Trend | 'stable';

export interface GrowthMetric {
  label: string;
  value: number; // 0–100
  trend: Trend;
  delta: number; // change from last week
}

export interface WeeklyReport {
  metrics: {
    selfBelief: Trend;
    fear: Trend;
    discipline: Trend;
    purpose: Trend;
  };
  narrative: string;
  pattern: string;
  focus: string;
  isDemo: boolean;       // true => show a "Demo data" label
}

/** @deprecated use WeeklyReport */
export interface WeeklyGrowthData {
  weekStart: string;
  metrics: GrowthMetric[];
  weeklyNarrative: string;
  focusNextWeek: string;
  totalReflections: number;
  streakDays: number;
  isDemo?: boolean;
}

// ── Quote Verifier (kept for internal guard) ──────────────────
export type VerificationStatus = 'verified' | 'unverified' | 'paraphrased' | 'idle' | 'loading';

export interface QuoteVerificationResult {
  status: VerificationStatus;
  inputQuote: string;
  matchedQuote?: string;
  source?: QuoteSource;
  confidence?: number;
  note?: string;
}

// ── App State ─────────────────────────────────────────────────
export interface AppState {
  theme: 'light' | 'dark';
  language: Language;
  profile: UserProfile | null;
  chatHistory: ChatMessage[];
  journalEntries: JournalEntry[];
  growthData: WeeklyReport | null;
}

// ── Onboarding Wizard ─────────────────────────────────────────
export interface OnboardingStep {
  step: number;
  total: number;
  question: string;
  type: 'pills' | 'slider' | 'text' | 'preferences' | 'review';
  options?: OnboardingOption[];
  sliderMin?: number;
  sliderMax?: number;
}

export interface OnboardingOption {
  value: string;
  label: string;
  emoji?: string;
  description?: string;
}

// ─────────────────────────────────────────────────────────────
// BACKEND API RESPONSE SHAPES
// These mirror the Pydantic schemas in jagrat-backend/app/schemas.py
// and are used internally by lib/api.ts. Pages use the frontend
// types above (MentorResponse, JournalEntry, WeeklyReport, etc.).
// ─────────────────────────────────────────────────────────────

export interface BackendSourceResponse {
  type: string;
  title: string;
  volume: string | null;
  chapter: string | null;
  page: string | null;
  section: string | null;
  url: string | null;
  authority: string;
}

export interface BackendTeachingResponse {
  id: string;
  quote: string;
  source: BackendSourceResponse;
  word_count: number;
  preview: string;
  is_letter: boolean;
}

export interface BackendTrustPanel {
  quote_verified: boolean;
  quote_id: string | null;
  candidate_count: number;
  quote_authority: string;
  rendered_from_backend: boolean;
  ai_written_sections: string[];
  source_note: string | null;
}

export interface BackendChallengePayload {
  assumption: string;
  question: string;
}

export interface BackendActionPayload {
  action: string;
  reason: string;
}

export interface BackendMentorResponse {
  status: 'ok';
  conversation_id: string;
  round: number;
  understanding: string;
  teaching: BackendTeachingResponse | null;
  interpretation: string;
  reflection_question: string;
  challenge: BackendChallengePayload;
  action: BackendActionPayload;
  trust: BackendTrustPanel;
}

export interface BackendSafetyResponse {
  status: 'safety';
  message: string;
  helplines: Array<{ name: string; number: string; url?: string }>;
  challenge_available: boolean;
}

export interface BackendChallengeResponse {
  status: 'ok';
  conversation_id: string;
  round: number;
  assumption: string;
  question: string;
  reflection: string;
  next_step: string;
  action: BackendActionPayload | null;
  completed: boolean;
  trust: BackendTrustPanel | null;
}

export interface BackendJournalInsightResponse {
  id: string;
  journal_entry_id: string;
  observation: string;
  tags: string[];
  themes: string[];
  emotions: string[];
  created_at: string;
}

export interface BackendJournalResponse {
  id: string;
  text: string;
  risk_flag: boolean;
  analysis_status: 'ready' | 'pending';
  created_at: string;
  insight: BackendJournalInsightResponse | null;
}

export interface BackendProfileResponse {
  id: string;
  display_name: string;
  answers: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // only present on POST /api/profile (create)
  access_token?: string;
}

// ── Auth types ────────────────────────────────────────────────
export interface BackendProfileSnapshot {
  id: string;
  display_name: string;
  email: string;
  answers: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface BackendAuthResponse {
  access_token: string;
  token_type: 'bearer';
  account_id: string;
  profile: BackendProfileSnapshot;
}

export interface BackendAuthMeResponse {
  account_id: string;
  profile: BackendProfileSnapshot;
  storage: Record<string, number>;
}

export interface BackendGrowthFactorSnapshot {
  key: string;
  label: string;
  value: number | null;
  change: number | null;
}

export interface BackendThemeCount {
  theme: string;
  total: number;
  daily: Record<string, number>;
}

export interface BackendReflectionGoalResponse {
  id: string;
  goal_key: string;
  goal_text: string;
  created_at: string;
  updated_at: string;
}

export interface BackendGrowthJourneyResponse {
  product: string;
  day_streak: number;
  total_reflections: number;
  active_goal: BackendReflectionGoalResponse | null;
  saved_teachings: unknown[];
  factor_cards: BackendGrowthFactorSnapshot[];
  reflection_themes_observed: BackendThemeCount[];
  lifetime_factor_trends: unknown[];
  weekly_report: Record<string, unknown> | null;
  weekly_anchor: unknown | null;
  note: string;
}

export interface BackendMentorSessionSummary {
  id: string;
  current_problem: string;
  preview: string;
  status: 'active' | 'completed' | 'safety';
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  completed: boolean;
  challenge_rounds: number;
  resumable: boolean;
}
