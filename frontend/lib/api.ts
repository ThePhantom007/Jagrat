// ─────────────────────────────────────────────────────────────
// JAGRAT — API Client
// Matches the actual ThePhantom007/Jagrat backend endpoints exactly.
// Base URL: NEXT_PUBLIC_API_URL (default http://localhost:8000)
// Auth:     X-Profile-Token header, stored in localStorage after profile creation.
// ─────────────────────────────────────────────────────────────

import type {
  MentorResponse,
  JournalEntry,
  WeeklyReport,
  UserProfile,
  BackendMentorResponse,
  BackendSafetyResponse,
  BackendJournalResponse,
  BackendGrowthJourneyResponse,
  BackendChallengeResponse,
  BackendProfileResponse,
  BackendAuthResponse,
  BackendAuthMeResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

// ── Storage keys ─────────────────────────────────────────────
const TOKEN_KEY = 'jagrat_profile_token';
const PROFILE_ID_KEY = 'jagrat_profile_id';

// ── Token helpers ─────────────────────────────────────────────
function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

function storeToken(token: string, profileId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(PROFILE_ID_KEY, profileId);
}

export function getProfileId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(PROFILE_ID_KEY);
}

export function clearProfile(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(PROFILE_ID_KEY);
  localStorage.removeItem('jagrat_profile');
}

export function hasProfile(): boolean {
  return Boolean(getToken());
}

// ── Authenticated headers ─────────────────────────────────────
function authHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['X-Profile-Token'] = token;
  return headers;
}

// ── Core fetch wrapper with error handling ────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers ?? {}) },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────────────────────
// AUTH — signup, login, claim, me, logout
// ─────────────────────────────────────────────────────────────

export async function signup(email: string, password: string, displayName: string): Promise<BackendAuthResponse> {
  const data = await apiFetch<BackendAuthResponse>('/api/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
  storeToken(data.access_token, data.profile.id);
  return data;
}

export async function login(email: string, password: string): Promise<BackendAuthResponse> {
  const data = await apiFetch<BackendAuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  storeToken(data.access_token, data.profile.id);
  return data;
}

export async function getAuthMe(): Promise<BackendAuthMeResponse | null> {
  try {
    return await apiFetch<BackendAuthMeResponse>('/api/auth/me');
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  try {
    await apiFetch('/api/auth/logout', { method: 'POST' });
  } catch { /* ignore */ }
  clearProfile();
}

// ─────────────────────────────────────────────────────────────
// PROFILE (anonymous — still works for guest mode)
// ─────────────────────────────────────────────────────────────

export async function createProfile(displayName: string): Promise<BackendProfileResponse> {
  const data = await apiFetch<BackendProfileResponse & { access_token: string }>('/api/profile', {
    method: 'POST',
    body: JSON.stringify({ display_name: displayName }),
  });
  storeToken(data.access_token, data.id);
  return data;
}

export async function getProfile(): Promise<BackendProfileResponse> {
  return apiFetch<BackendProfileResponse>('/api/profile');
}

// ── Onboarding ── maps frontend UserProfile → backend OnboardingRequest
// Backend expects these exact Literal values:
//   profession: student | working | business | homemaker | other
//   age: number
//   matters_most: studies | career | family | relationships | health | money | personal_growth
//   troubling_most: stress | fear | confidence | motivation | relationships | career | feeling_lost | other
//   problem_approach: face_them | overthink | avoid | ask_others | depends
//   improve: confidence | focus | discipline | courage | patience | peace | decision_making | other

const PROFESSION_MAP: Record<string, string> = {
  student: 'student',
  working: 'working',
  business: 'business',
  homemaker: 'homemaker',
  other: 'other',
};

const MATTERS_MAP: Record<string, string> = {
  academic_growth: 'studies',
  mental_focus: 'personal_growth',
  inner_strength: 'personal_growth',
  studies: 'studies',
  career: 'career',
  family: 'family',
  relationships: 'relationships',
  health: 'health',
  money: 'money',
  personal_growth: 'personal_growth',
};

const TROUBLING_MAP: Record<string, string> = {
  exam_failure: 'stress',
  self_doubt: 'confidence',
  fear: 'fear',
  overcoming_fear: 'fear',
  decision_hesitation: 'motivation',
  discipline: 'motivation',
  stress: 'stress',
  confidence: 'confidence',
  motivation: 'motivation',
  relationships: 'relationships',
  career: 'career',
  feeling_lost: 'feeling_lost',
  other: 'other',
};

const APPROACH_MAP: Record<string, string> = {
  overthinking: 'overthink',
  withdrawal: 'avoid',
  quick_reset: 'face_them',
  face_them: 'face_them',
  overthink: 'overthink',
  avoid: 'avoid',
  ask_others: 'ask_others',
  depends: 'depends',
};

const IMPROVE_MAP: Record<string, string> = {
  inner_strength: 'confidence',
  discipline: 'discipline',
  clear_goal: 'focus',
  overcome_fear: 'courage',
  academic_growth: 'focus',
  mental_focus: 'focus',
  confidence: 'confidence',
  focus: 'focus',
  courage: 'courage',
  patience: 'patience',
  peace: 'peace',
  decision_making: 'decision_making',
  other: 'other',
};

export async function saveOnboarding(profile: UserProfile): Promise<void> {
  const profession = PROFESSION_MAP[profile.profession ?? 'student'] ?? 'student';
  const matters_most = MATTERS_MAP[profile.primaryGoal ?? 'personal_growth'] ?? 'personal_growth';
  const troubling_most = TROUBLING_MAP[profile.primaryChallenge ?? 'stress'] ?? 'stress';
  const problem_approach = APPROACH_MAP[profile.failureResponse ?? 'depends'] ?? 'depends';
  const improve = IMPROVE_MAP[profile.focusArea ?? 'confidence'] ?? 'confidence';

  await apiFetch('/api/profile/onboarding', {
    method: 'PUT',
    body: JSON.stringify({
      profession,
      age: profile.age ?? 20,
      matters_most,
      troubling_most,
      problem_approach,
      improve,
    }),
  });
}

// ─────────────────────────────────────────────────────────────
// MENTOR
// ─────────────────────────────────────────────────────────────

/** Send a new mentor message. Returns null on safety trigger. */
export async function sendMentorMessage(
  message: string,
  conversationId?: string | null,
): Promise<MentorResponse> {
  if (USE_MOCK) {
    const { DEMO_MENTOR_RESPONSES, DEMO_CRISIS_RESPONSE } = await import('./mock/mentor');
    const CRISIS_KEYWORDS = ['suicide', 'kill myself', 'end my life', 'want to die'];
    if (CRISIS_KEYWORDS.some(k => message.toLowerCase().includes(k))) {
      return { ...DEMO_CRISIS_RESPONSE };
    }
    await new Promise(r => setTimeout(r, 1200 + Math.random() * 600));
    const responses = DEMO_MENTOR_RESPONSES;
    return { ...responses[Math.floor(Math.random() * responses.length)] };
  }

  const endpoint = conversationId
    ? `/api/mentor/${conversationId}/continue`
    : '/api/mentor';

  const raw = await apiFetch<BackendMentorResponse | BackendSafetyResponse>(endpoint, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });

  return transformMentorResponse(raw);
}

/** Retry a pending (Gemini-failed) reflection. */
export async function retryReflection(conversationId: string): Promise<MentorResponse> {
  const raw = await apiFetch<BackendMentorResponse | BackendSafetyResponse>(
    `/api/mentor/${conversationId}/retry`,
    { method: 'POST' },
  );
  return transformMentorResponse(raw);
}

/** Submit a Socratic challenge response. */
export async function submitChallenge(
  conversationId: string,
  userResponse: string,
): Promise<BackendChallengeResponse | null> {
  const raw = await apiFetch<BackendChallengeResponse | BackendSafetyResponse>(
    `/api/mentor/${conversationId}/challenge`,
    { method: 'POST', body: JSON.stringify({ user_response: userResponse }) },
  );
  if ('status' in raw && raw.status === 'safety') return null;
  return raw as BackendChallengeResponse;
}

/** List active/completed mentor sessions. */
export async function getMentorSessions(
  status: 'active' | 'completed' | 'all' = 'active',
) {
  return apiFetch<unknown[]>(`/api/mentor/sessions?status=${status}`);
}

// ── Transform backend MentorResponse → frontend MentorResponse ──
function transformMentorResponse(raw: BackendMentorResponse | BackendSafetyResponse): MentorResponse {
  if ('status' in raw && raw.status === 'safety') {
    return {
      listening: { summary: '', question: '' },
      documented: null,
      reflection: { text: (raw as BackendSafetyResponse).message, nextStep: '' },
      crisis: true,
      conversationId: undefined,
    };
  }

  const data = raw as BackendMentorResponse;
  return {
    listening: {
      summary: data.understanding ?? '',
      question: data.reflection_question ?? '',
    },
    documented: data.teaching
      ? {
          id: data.teaching.id,
          quote: data.teaching.quote,
          source: {
            work: data.teaching.source.title,
            volume: data.teaching.source.volume ?? undefined,
            page: data.teaching.source.page ?? undefined,
            url: data.teaching.source.url ?? undefined,
          },
          verified: true,
        }
      : null,
    reflection: {
      text: data.interpretation ?? '',
      nextStep: data.action?.action ?? '',
    },
    challenge: data.challenge
      ? {
          belief: '',
          assumption: data.challenge.assumption ?? '',
          pivot: data.challenge.question ?? '',
        }
      : undefined,
    conversationId: data.conversation_id,
  };
}

// ─────────────────────────────────────────────────────────────
// JOURNAL
// ─────────────────────────────────────────────────────────────

export async function getJournalEntries(): Promise<JournalEntry[]> {
  if (USE_MOCK) {
    if (typeof window === 'undefined') return [];
    try {
      const raw = localStorage.getItem('jagrat_journal');
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  }

  try {
    const data = await apiFetch<BackendJournalResponse[]>('/api/journal');
    return data.map(backendEntryToFrontend);
  } catch (err) {
    console.error('Failed to fetch journal entries:', err);
    return [];
  }
}

export async function saveJournalEntry(entry: JournalEntry): Promise<JournalEntry[]> {
  if (USE_MOCK) {
    const entries = await getJournalEntries();
    const updated = [entry, ...entries.filter(e => e.id !== entry.id)];
    try { localStorage.setItem('jagrat_journal', JSON.stringify(updated)); } catch { /* full */ }
    return updated;
  }

  await apiFetch<BackendJournalResponse | BackendSafetyResponse>('/api/journal', {
    method: 'POST',
    body: JSON.stringify({ text: entry.text }),
  });
  return getJournalEntries();
}

export async function deleteJournalEntry(id: string): Promise<JournalEntry[]> {
  if (USE_MOCK) {
    const entries = (await getJournalEntries()).filter(e => e.id !== id);
    try { localStorage.setItem('jagrat_journal', JSON.stringify(entries)); } catch { /* ignore */ }
    return entries;
  }

  await apiFetch(`/api/journal/${id}`, { method: 'DELETE' });
  return getJournalEntries();
}

function backendEntryToFrontend(entry: BackendJournalResponse): JournalEntry {
  return {
    id: entry.id,
    date: new Date(entry.created_at).toISOString().split('T')[0],
    text: entry.text,
    tags: (entry.insight?.tags ?? []) as JournalEntry['tags'],
  };
}

// ─────────────────────────────────────────────────────────────
// GROWTH JOURNEY
// ─────────────────────────────────────────────────────────────

export async function getGrowthJourney(): Promise<BackendGrowthJourneyResponse | null> {
  if (USE_MOCK) return null;
  try {
    return await apiFetch<BackendGrowthJourneyResponse>('/api/growth-journey');
  } catch (err) {
    console.error('Failed to fetch growth journey:', err);
    return null;
  }
}

export async function getWeeklyReport(): Promise<WeeklyReport | null> {
  if (USE_MOCK) {
    return {
      metrics: { selfBelief: 'up', fear: 'down', discipline: 'steady', purpose: 'up' },
      narrative: 'Continue your reflection journey to unlock insights.',
      pattern: 'Build your practice by writing in your journal regularly.',
      focus: 'Engage deeply with each reflection.',
      isDemo: true,
    };
  }

  try {
    const journey = await getGrowthJourney();
    if (!journey) return null;

    // Derive trend directions from factor_cards
    const card = (key: string) =>
      journey.factor_cards?.find(c => c.key === key);
    const trend = (key: string, inverse = false): 'up' | 'down' | 'steady' => {
      const c = card(key);
      if (!c || c.change == null) return 'steady';
      if (inverse) return c.change > 0 ? 'down' : c.change < 0 ? 'up' : 'steady';
      return c.change > 0 ? 'up' : c.change < 0 ? 'down' : 'steady';
    };

    const report = journey.weekly_report;
    return {
      metrics: {
        selfBelief: trend('self_belief'),
        fear: trend('fear', true),
        discipline: trend('discipline'),
        purpose: trend('clarity'),
      },
      narrative: (report as any)?.summary ?? journey.note ?? 'Keep reflecting.',
      pattern: (report as any)?.recurring_themes?.join(', ') ?? '',
      focus: (report as any)?.next_week_focus ?? '',
      isDemo: false,
    };
  } catch (err) {
    console.error('Failed to build weekly report:', err);
    return null;
  }
}

// ─────────────────────────────────────────────────────────────
// GROWTH CHECK-IN
// ─────────────────────────────────────────────────────────────

export interface CheckInPayload {
  week_start: string; // ISO datetime string
  self_belief: number;
  fear: number;
  discipline: number;
  clarity: number;
  resilience: number;
  note?: string;
}

export async function saveCheckIn(payload: CheckInPayload): Promise<void> {
  await apiFetch('/api/growth/check-in', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

// ─────────────────────────────────────────────────────────────
// VIVEKANANDA VS ME
// ─────────────────────────────────────────────────────────────

export async function submitVsMe(view: string) {
  return apiFetch('/api/vivekananda-vs-me', {
    method: 'POST',
    body: JSON.stringify({ view }),
  });
}

// ─────────────────────────────────────────────────────────────
// HEALTH CHECK
// ─────────────────────────────────────────────────────────────

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}

// ─────────────────────────────────────────────────────────────
// ACTIONS
// ─────────────────────────────────────────────────────────────

export interface BackendActionItem {
  id: string;
  text: string;
  reason: string;
  completed: boolean;
  created_at: string;
  completed_at: string | null;
  follow_up_outcome: 'completed' | 'partially_completed' | 'not_completed' | null;
  follow_up_note: string | null;
}

export async function getActions(): Promise<BackendActionItem[]> {
  try { return await apiFetch<BackendActionItem[]>('/api/actions'); }
  catch { return []; }
}

export async function completeAction(id: string): Promise<BackendActionItem> {
  return apiFetch<BackendActionItem>(`/api/actions/${id}/complete`, { method: 'POST' });
}

export async function followUpAction(
  id: string,
  outcome: 'completed' | 'partially_completed' | 'not_completed',
  note = '',
): Promise<void> {
  await apiFetch(`/api/actions/${id}/follow-up`, {
    method: 'POST',
    body: JSON.stringify({ outcome, note }),
  });
}

// ─────────────────────────────────────────────────────────────
// HISTORY
// ─────────────────────────────────────────────────────────────

export interface BackendHistoryItem {
  id: string;
  type: string;
  created_at: string;
  title: string;
  summary: string;
  data: Record<string, unknown>;
}

export async function getHistory(params?: {
  limit?: number;
  item_type?: string;
  q?: string;
  theme?: string;
}): Promise<BackendHistoryItem[]> {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set('limit', String(params.limit));
  if (params?.item_type) qs.set('item_type', params.item_type);
  if (params?.q) qs.set('q', params.q);
  if (params?.theme) qs.set('theme', params.theme);
  const query = qs.toString();
  try {
    const data = await apiFetch<{ items: BackendHistoryItem[] }>(`/api/history${query ? '?' + query : ''}`);
    return data.items;
  } catch { return []; }
}

// ─────────────────────────────────────────────────────────────
// TEACHINGS
// ─────────────────────────────────────────────────────────────

export interface BackendTeachingListItem {
  id: string;
  quote: string;
  themes: string[];
  source: {
    type: string;
    title: string;
    volume: string | null;
    chapter: string | null;
    page: string | null;
    section: string | null;
    url: string | null;
    authority: string;
  };
}

export async function getTeachings(query?: string): Promise<BackendTeachingListItem[]> {
  const qs = query ? `?query=${encodeURIComponent(query)}` : '';
  try { return await apiFetch<BackendTeachingListItem[]>(`/api/teachings${qs}`); }
  catch { return []; }
}

export async function saveTeaching(teachingId: string): Promise<void> {
  await apiFetch(`/api/teachings/${teachingId}/save`, { method: 'POST' });
}

export async function unsaveTeaching(teachingId: string): Promise<void> {
  await apiFetch(`/api/teachings/${teachingId}/save`, { method: 'DELETE' });
}

export async function getSavedTeachings() {
  try { return await apiFetch<unknown[]>('/api/teachings/saved'); }
  catch { return []; }
}

// ─────────────────────────────────────────────────────────────
// REFLECTION GOAL
// ─────────────────────────────────────────────────────────────

export interface BackendReflectionGoal {
  id: string;
  goal_key: string;
  goal_text: string;
  created_at: string;
  updated_at: string;
}

export async function getReflectionGoal(): Promise<BackendReflectionGoal | null> {
  try { return await apiFetch<BackendReflectionGoal>('/api/growth/goal'); }
  catch { return null; }
}

export async function upsertReflectionGoal(goalKey: string, goalText: string): Promise<BackendReflectionGoal> {
  return apiFetch<BackendReflectionGoal>('/api/growth/goal', {
    method: 'PUT',
    body: JSON.stringify({ goal_key: goalKey, goal_text: goalText }),
  });
}

export async function deleteReflectionGoal(): Promise<void> {
  await apiFetch('/api/growth/goal', { method: 'DELETE' });
}

// ─────────────────────────────────────────────────────────────
// REFLECTION FEEDBACK
// ─────────────────────────────────────────────────────────────

export async function submitFeedback(
  conversationId: string,
  helpful: boolean,
  reason?: string,
  note = '',
): Promise<void> {
  await apiFetch(`/api/mentor/${conversationId}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ helpful, reason: reason ?? null, note }),
  });
}

// ─────────────────────────────────────────────────────────────
// TODAY'S PROMPT
// ─────────────────────────────────────────────────────────────

export interface TodaysPrompt {
  prompt: string;
  theme: string | null;
  source: string;
}

export async function getTodaysPrompt(): Promise<TodaysPrompt | null> {
  try { return await apiFetch<TodaysPrompt>('/api/mentor/today-prompt'); }
  catch { return null; }
}
