'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Brain, Target, Lightbulb, Search, TrendingUp, Loader2, Flame, BookOpen, Plus, X, Check, Edit2 } from 'lucide-react';
import { BentoCard } from '@/components/BentoCard';
import { MetricTile } from '@/components/ui/MetricTile';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { GlassCard } from '@/components/ui/GlassCard';
import { useAppContext } from '@/components/ThemeProvider';
import { getGrowthJourney, getReflectionGoal, upsertReflectionGoal, deleteReflectionGoal, saveCheckIn, type BackendReflectionGoal } from '@/lib/api';
import type { BackendGrowthJourneyResponse, BackendGrowthFactorSnapshot } from '@/lib/types';

// ── Trend helper ──────────────────────────────────────────────
function trendOf(
  cards: BackendGrowthFactorSnapshot[],
  key: string,
  inverse = false,
): 'up' | 'down' | 'steady' {
  const card = cards.find(c => c.key === key);
  if (!card || card.change == null) return 'steady';
  if (inverse) return card.change > 0 ? 'down' : card.change < 0 ? 'up' : 'steady';
  return card.change > 0 ? 'up' : card.change < 0 ? 'down' : 'steady';
}

// ── Sparkline data from lifetime_factor_trends ────────────────
function sparkValues(journey: BackendGrowthJourneyResponse, key: string): number[] {
  const trends = journey.lifetime_factor_trends as Array<Record<string, unknown>>;
  if (!Array.isArray(trends) || trends.length === 0) {
    return [30, 45, 40, 60, 55, 70, 65];
  }
  const last7 = trends.slice(-7);
  return last7.map(t => {
    const v = t[key];
    return typeof v === 'number' ? (v / 10) * 100 : 50;
  });
}

export default function GrowthPage() {
  const { lang } = useAppContext();
  const [journey, setJourney] = useState<BackendGrowthJourneyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reflection goal state
  const [goal, setGoal] = useState<BackendReflectionGoal | null>(null);
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [goalKey, setGoalKey] = useState('personal_growth');
  const [goalText, setGoalText] = useState('');
  const [savingGoal, setSavingGoal] = useState(false);

  // Weekly check-in state
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [checkIn, setCheckIn] = useState({ self_belief: 5, fear: 5, discipline: 5, clarity: 5, resilience: 5, note: '' });
  const [savingCheckIn, setSavingCheckIn] = useState(false);
  const [checkInSaved, setCheckInSaved] = useState(false);

  const GOAL_KEYS = ['confidence','discipline','fear','clarity','courage','focus','resilience','decision_making','personal_growth','custom'];

  useEffect(() => {
    Promise.all([
      getGrowthJourney().then(d => { setJourney(d); }).catch(() => setError('Could not load growth data.')),
      getReflectionGoal().then(g => setGoal(g)),
    ]).finally(() => setLoading(false));
  }, []);

  const handleSaveGoal = async () => {
    if (!goalText.trim()) return;
    setSavingGoal(true);
    try {
      const saved = await upsertReflectionGoal(goalKey, goalText.trim());
      setGoal(saved);
      setShowGoalForm(false);
    } catch { /* ignore */ }
    finally { setSavingGoal(false); }
  };

  const handleDeleteGoal = async () => {
    setSavingGoal(true);
    try { await deleteReflectionGoal(); setGoal(null); }
    catch { /* ignore */ }
    finally { setSavingGoal(false); }
  };

  const handleCheckIn = async () => {
    setSavingCheckIn(true);
    try {
      const weekStart = new Date();
      weekStart.setDate(weekStart.getDate() - weekStart.getDay());
      weekStart.setHours(0, 0, 0, 0);
      await saveCheckIn({ week_start: weekStart.toISOString(), ...checkIn });
      setCheckInSaved(true);
      setTimeout(() => { setShowCheckIn(false); setCheckInSaved(false); }, 1500);
    } catch { /* ignore */ }
    finally { setSavingCheckIn(false); }
  };

  // ── Derived display values ─────────────────────────────────
  const cards = journey?.factor_cards ?? [];
  const report = journey?.weekly_report as Record<string, unknown> | null ?? null;
  const themes = journey?.reflection_themes_observed ?? [];

  const narrative: string =
    (report?.summary as string) ||
    journey?.note ||
    'Keep reflecting to unlock your weekly insights.';

  const patternText: string =
    themes.length > 0
      ? `Themes observed this period: ${themes.slice(0, 4).map(t => t.theme).join(', ')}.`
      : 'Write more reflections to surface your recurring patterns.';

  const focusNextWeek: string =
    (report?.next_week_focus as string) ||
    'Continue building a daily reflection habit to strengthen your inner growth.';

  const sparkData = journey ? sparkValues(journey, 'self_belief') : [30, 45, 40, 60, 55, 70, 65];

  const isDemo = !journey || journey.total_reflections === 0;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">

      {/* ── Page Header ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
          Growth Journey &amp; Weekly Dashboard
        </h1>
        <p className="text-sm text-center mb-4" style={{ color: 'var(--text-muted)' }}>
          Track your inner growth, recognise patterns, and take mindful steps forward.
        </p>
        <SectionDivider />
      </motion.div>

      {/* ── Loading ── */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading your journey…</p>
        </div>
      )}

      {/* ── Error ── */}
      {!loading && error && (
        <div className="text-center py-12">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{error}</p>
        </div>
      )}

      {/* ── Content ── */}
      {!loading && !error && (
        <>
          {/* ── Reflection Goal + Check-in row ── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
            className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">

            {/* Goal card */}
            <GlassCard className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--saffron)' }}>
                  🎯 Reflection Goal
                </span>
                <div className="flex gap-1.5">
                  {goal && (
                    <button onClick={handleDeleteGoal} disabled={savingGoal}
                      className="text-xs px-2 py-1 rounded-lg focus:outline-none focus-visible:ring-2"
                      style={{ color: 'var(--danger)', background: 'rgba(210,69,47,0.08)' }}>
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button onClick={() => { setShowGoalForm(v => !v); if (goal) { setGoalKey(goal.goal_key); setGoalText(goal.goal_text); } }}
                    className="text-xs px-2 py-1 rounded-lg focus:outline-none focus-visible:ring-2"
                    style={{ color: 'var(--saffron)', background: 'var(--saffron-soft)' }}>
                    {goal ? <Edit2 className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
              {goal ? (
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>{goal.goal_text}</p>
              ) : (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No active goal — set one to sharpen your reflections.</p>
              )}
              <AnimatePresence>
                {showGoalForm && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-2 overflow-hidden">
                    <select value={goalKey} onChange={e => setGoalKey(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl text-xs focus:outline-none focus-visible:ring-2"
                      style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}>
                      {GOAL_KEYS.map(k => <option key={k} value={k}>{k.replace(/_/g,' ')}</option>)}
                    </select>
                    <textarea value={goalText} onChange={e => setGoalText(e.target.value)} rows={2} placeholder="Describe your goal…"
                      className="w-full px-3 py-2 rounded-xl text-xs resize-none focus:outline-none focus-visible:ring-2"
                      style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }} />
                    <button onClick={handleSaveGoal} disabled={!goalText.trim() || savingGoal}
                      className="w-full py-2 rounded-xl text-xs font-semibold disabled:opacity-40 focus:outline-none focus-visible:ring-2"
                      style={{ background: 'var(--saffron)', color: 'var(--on-saffron)' }}>
                      {savingGoal ? 'Saving…' : 'Save Goal'}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </GlassCard>

            {/* Weekly check-in card */}
            <GlassCard className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--saffron)' }}>
                  📊 Weekly Check-in
                </span>
                <button onClick={() => setShowCheckIn(v => !v)}
                  className="text-xs px-2 py-1 rounded-lg focus:outline-none focus-visible:ring-2"
                  style={{ color: 'var(--saffron)', background: 'var(--saffron-soft)' }}>
                  {showCheckIn ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Rate your five growth factors this week.</p>
              <AnimatePresence>
                {showCheckIn && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-2 overflow-hidden">
                    {(['self_belief','fear','discipline','clarity','resilience'] as const).map(k => (
                      <div key={k} className="flex items-center gap-2">
                        <span className="text-xs w-24 capitalize shrink-0" style={{ color: 'var(--text-muted)' }}>{k.replace('_',' ')}</span>
                        <input type="range" min={1} max={10} value={checkIn[k]}
                          onChange={e => setCheckIn(p => ({ ...p, [k]: Number(e.target.value) }))}
                          className="flex-1 h-2 rounded-full appearance-none cursor-pointer" />
                        <span className="text-xs font-bold w-4" style={{ color: 'var(--saffron)' }}>{checkIn[k]}</span>
                      </div>
                    ))}
                    <textarea value={checkIn.note} onChange={e => setCheckIn(p => ({ ...p, note: e.target.value }))}
                      placeholder="Any notes? (optional)" rows={2}
                      className="w-full px-3 py-2 rounded-xl text-xs resize-none focus:outline-none focus-visible:ring-2"
                      style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }} />
                    <button onClick={handleCheckIn} disabled={savingCheckIn}
                      className="w-full py-2 rounded-xl text-xs font-semibold disabled:opacity-40 focus:outline-none focus-visible:ring-2 flex items-center justify-center gap-2"
                      style={{ background: 'var(--saffron)', color: 'var(--on-saffron)' }}>
                      {savingCheckIn ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : checkInSaved ? <Check className="w-3.5 h-3.5" /> : null}
                      {checkInSaved ? 'Saved!' : savingCheckIn ? 'Saving…' : 'Submit Check-in'}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </GlassCard>
          </motion.div>

          {/* Streak + reflections strip */}
          {journey && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="flex gap-3 mb-6 flex-wrap"
            >
              <div
                className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)', border: '1px solid rgba(232,102,46,0.25)' }}
              >
                <Flame className="w-4 h-4" aria-hidden="true" />
                {journey.day_streak} day streak
              </div>
              <div
                className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                style={{ background: 'var(--card-surface)', color: 'var(--text-muted)', border: '1px solid var(--card-border)' }}
              >
                <BookOpen className="w-4 h-4" aria-hidden="true" />
                {journey.total_reflections} total reflections
              </div>
              {journey.active_goal && (
                <div
                  className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                  style={{ background: 'var(--card-surface)', color: 'var(--text-muted)', border: '1px solid var(--card-border)' }}
                >
                  <Target className="w-4 h-4" aria-hidden="true" />
                  Goal: {journey.active_goal.goal_text}
                </div>
              )}
            </motion.div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

            {/* Your Week — Metrics */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="lg:col-span-7"
            >
              <BentoCard title="📊 Your Week" accent="saffron" index={0}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <MetricTile
                    icon={Heart}
                    label="Self-belief"
                    trend={trendOf(cards, 'self_belief')}
                    description={trendOf(cards, 'self_belief') === 'up' ? 'Improving' : trendOf(cards, 'self_belief') === 'down' ? 'Needs focus' : 'Steady'}
                  />
                  <MetricTile
                    icon={Brain}
                    label="Fear"
                    trend={trendOf(cards, 'fear', true)}
                    description={trendOf(cards, 'fear', true) === 'up' ? 'Easing' : trendOf(cards, 'fear', true) === 'down' ? 'Rising' : 'Steady'}
                  />
                  <MetricTile
                    icon={Target}
                    label="Discipline"
                    trend={trendOf(cards, 'discipline')}
                    description={trendOf(cards, 'discipline') === 'up' ? 'Improving' : trendOf(cards, 'discipline') === 'down' ? 'Slipping' : 'Steady'}
                  />
                  <MetricTile
                    icon={Lightbulb}
                    label="Clarity"
                    trend={trendOf(cards, 'clarity')}
                    description={trendOf(cards, 'clarity') === 'up' ? 'Improving' : trendOf(cards, 'clarity') === 'down' ? 'Foggy' : 'Steady'}
                  />
                </div>
              </BentoCard>
            </motion.div>

            {/* Insights: What Changed? */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="lg:col-span-5"
            >
              <BentoCard title="💡 Insights: What Changed?" accent="gold" index={1}>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                  {narrative}
                </p>
                {Array.isArray(report?.recurring_themes) && (report.recurring_themes as string[]).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {(report.recurring_themes as string[]).map((theme: string) => (
                      <span
                        key={theme}
                        className="text-xs px-2.5 py-1 rounded-full font-medium"
                        style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)' }}
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                )}
              </BentoCard>
            </motion.div>

            {/* Pattern Recognition */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.4 }}
              className="lg:col-span-12"
            >
              <BentoCard
                title={
                  <div className="flex items-center gap-2">
                    <Search className="w-5 h-5" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
                    <span>Pattern Recognition</span>
                  </div>
                }
                accent="slate"
                index={2}
              >
                <div className="flex flex-col sm:flex-row gap-4 items-start">
                  <div className="flex-1">
                    <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
                      {patternText}
                    </p>
                    {/* Sparkline from real self_belief trend data */}
                    <div className="flex items-end gap-1 h-12" aria-hidden="true">
                      {sparkData.map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 rounded-t-sm transition-all"
                          style={{
                            height: `${height}%`,
                            background: 'var(--saffron)',
                            opacity: 0.5 + (i / sparkData.length) * 0.5,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  {themes.length > 0 && (
                    <div className="shrink-0 space-y-1.5">
                      {themes.slice(0, 5).map(t => (
                        <div key={t.theme} className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ background: 'var(--saffron)' }}
                            aria-hidden="true"
                          />
                          {t.theme} <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>×{t.total}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </BentoCard>
            </motion.div>

            {/* Focus for next week */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.4 }}
              className="lg:col-span-12"
            >
              <div
                className="rounded-2xl p-6 flex items-start gap-4"
                style={{
                  background: 'linear-gradient(135deg, var(--saffron-soft), var(--saffron-soft))',
                  border: '2px solid var(--saffron)',
                  boxShadow: '0 4px 20px var(--saffron-glow)',
                }}
              >
                <div
                  className="shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ background: 'var(--saffron)', color: 'var(--on-saffron)' }}
                  aria-hidden="true"
                >
                  <Target className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3
                    className="text-sm font-bold uppercase tracking-wider mb-2 flex items-center gap-2"
                    style={{ color: 'var(--saffron)' }}
                  >
                    <TrendingUp className="w-4 h-4" aria-hidden="true" />
                    Focus for next week
                  </h3>
                  <p className="text-base leading-relaxed font-medium" style={{ color: 'var(--text-primary)' }}>
                    {focusNextWeek}
                  </p>
                  {typeof report?.encouragement === 'string' && (
                    <p className="text-sm mt-2 italic" style={{ color: 'var(--text-muted)' }}>
                      {report.encouragement as string}
                    </p>
                  )}
                </div>
              </div>
            </motion.div>

          </div>

          {/* Demo / unlock notice */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-center text-xs mt-6 italic"
            style={{ color: 'var(--text-subtle)' }}
          >
            {isDemo
              ? 'Demo data • Write 3 journal entries and complete a reflection to unlock your weekly report'
              : `Last updated from ${journey?.total_reflections} reflections`}
          </motion.p>
        </>
      )}
    </div>
  );
}
