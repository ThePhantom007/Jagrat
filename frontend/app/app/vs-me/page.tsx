'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Swords, BookOpen, CheckCircle2, AlertCircle, HelpCircle,
  FlaskConical, Loader2, RotateCcw, Send, ChevronDown, ChevronUp,
} from 'lucide-react';
import { SpeechButton } from '@/components/SpeechButton';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { GlassCard } from '@/components/ui/GlassCard';
import { CrisisCard } from '@/components/CrisisCard';
import { useAppContext } from '@/components/ThemeProvider';
import { submitVsMe } from '@/lib/api';
import type { BackendSafetyResponse } from '@/lib/types';

// ── Backend response shape ────────────────────────────────────
interface VsMeTeaching {
  id: string;
  quote: string;
  source: {
    title: string;
    volume: string | null;
    page: string | null;
    url: string | null;
    authority: string;
  };
}

interface VsMeResult {
  status: 'ok';
  comparison_id: string;
  my_view: string;
  teaching: VsMeTeaching | null;
  where_they_align: string;
  where_they_differ: string;
  what_to_examine: string;
  questions_for_me: string[];
  experiment: string;
  conclusion: string;
}

// ── Starter prompts ───────────────────────────────────────────
const STARTERS = [
  'Hard work alone is enough to succeed — talent is overrated.',
  'I should prioritise my own happiness above everyone else\'s.',
  'Failure means I am not good enough and should give up.',
  'Comparing yourself to others is the best way to grow.',
];

// ── Section component ─────────────────────────────────────────
function ResultSection({
  icon,
  label,
  color,
  bg,
  border,
  children,
  index,
}: {
  icon: React.ReactNode;
  label: string;
  color: string;
  bg: string;
  border: string;
  children: React.ReactNode;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.12, duration: 0.4 }}
      className="rounded-2xl p-5"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span style={{ color }}>{icon}</span>
        <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color }}>
          {label}
        </h3>
      </div>
      {children}
    </motion.div>
  );
}

// ── Teaching card ─────────────────────────────────────────────
function TeachingCard({ teaching }: { teaching: VsMeTeaching }) {
  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: 'rgba(120,53,15,0.12)',
        border: '1px solid rgba(245,158,11,0.35)',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4" style={{ color: 'var(--gold-accent)' }} aria-hidden="true" />
          <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--gold-accent)' }}>
            Vivekananda's Teaching
          </span>
        </div>
        <SpeechButton text={teaching.quote} />
      </div>
      <blockquote
        className="font-scripture text-base leading-relaxed mb-4 relative pl-4"
        style={{ color: 'var(--text-primary)', borderLeft: '3px solid var(--gold-accent)' }}
      >
        {teaching.quote}
      </blockquote>
      <div className="flex items-center gap-1.5 flex-wrap">
        <CheckCircle2 className="w-3.5 h-3.5" style={{ color: 'var(--success)' }} aria-hidden="true" />
        <span className="text-xs font-semibold" style={{ color: 'var(--success)' }}>Source Verified</span>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          · {teaching.source.title}
          {teaching.source.volume ? `, ${teaching.source.volume}` : ''}
          {teaching.source.page ? `, p. ${teaching.source.page}` : ''}
        </span>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function VsMePage() {
  const { lang } = useAppContext();
  const [view, setView] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VsMeResult | null>(null);
  const [crisis, setCrisis] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showQuestions, setShowQuestions] = useState(true);

  const handleSubmit = async () => {
    const trimmed = view.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setCrisis(false);

    try {
      const raw = await submitVsMe(trimmed) as VsMeResult | BackendSafetyResponse;
      if ('status' in raw && raw.status === 'safety') {
        setCrisis(true);
      } else {
        setResult(raw as VsMeResult);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setCrisis(false);
    setError(null);
    setView('');
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8 text-center"
      >
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-4"
          style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)', border: '1px solid rgba(232,102,46,0.25)' }}>
          <Swords className="w-3.5 h-3.5" aria-hidden="true" />
          Vivekananda vs Me
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          Challenge Your Beliefs
        </h1>
        <p className="text-sm leading-relaxed max-w-xl mx-auto" style={{ color: 'var(--text-muted)' }}>
          Share a view or belief you hold. See how it aligns or contrasts with a relevant teaching
          from Swami Vivekananda's verified writings — then examine it for yourself.
        </p>
        <div className="mt-4"><SectionDivider /></div>
      </motion.div>

      {/* Crisis */}
      {crisis && (
        <div className="mb-6">
          <CrisisCard lang={lang} />
          <div className="flex justify-center mt-4">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold focus:outline-none focus-visible:ring-2"
              style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)', color: 'var(--text-muted)' }}
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" /> Start Over
            </button>
          </div>
        </div>
      )}

      {/* Input form — show when no result yet */}
      {!result && !crisis && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <GlassCard className="p-6 space-y-5">
            <div>
              <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                What do you believe?
              </label>
              <textarea
                value={view}
                onChange={e => setView(e.target.value)}
                placeholder="e.g. I think failure is a sign that I'm not capable enough…"
                rows={4}
                className="w-full px-4 py-3 rounded-xl text-sm resize-none focus:outline-none focus-visible:ring-2 transition-all"
                style={{
                  background: 'var(--input-surface)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--text-primary)',
                }}
                disabled={loading}
                aria-label="Your belief or view"
              />
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-muted)' }}>
                {view.length} / 12000 characters
              </p>
            </div>

            {/* Error */}
            {error && (
              <div
                className="flex items-start gap-2 px-4 py-2.5 rounded-xl text-sm"
                style={{ background: 'rgba(210,69,47,0.08)', border: '1px solid rgba(210,69,47,0.2)', color: 'var(--danger)' }}
                role="alert"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={!view.trim() || loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all active:scale-[0.99] disabled:opacity-40 focus:outline-none focus-visible:ring-2"
              style={{
                background: 'var(--saffron)',
                color: 'var(--on-saffron)',
                boxShadow: view.trim() ? '0 4px 16px var(--saffron-glow)' : 'none',
              }}
            >
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Comparing…</>
                : <><Send className="w-4 h-4" aria-hidden="true" /> Compare with Vivekananda</>
              }
            </button>

            {/* Starters */}
            {!loading && (
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Try one of these:
                </p>
                {STARTERS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setView(s)}
                    className="w-full text-left px-4 py-2.5 rounded-xl text-sm transition-all hover:scale-[1.005] active:scale-[0.99] focus:outline-none focus-visible:ring-2"
                    style={{
                      background: 'var(--card-surface)',
                      border: '1px solid var(--card-border)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    "{s}"
                  </button>
                ))}
              </div>
            )}
          </GlassCard>
        </motion.div>
      )}

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* My view recap */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="px-5 py-4 rounded-2xl"
              style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)' }}
            >
              <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted)' }}>
                Your View
              </p>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                "{result.my_view}"
              </p>
            </motion.div>

            {/* Teaching */}
            {result.teaching && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <TeachingCard teaching={result.teaching} />
              </motion.div>
            )}

            {/* Where they align */}
            <ResultSection
              index={2}
              icon={<CheckCircle2 className="w-4 h-4" />}
              label="Where You Align"
              color="var(--success)"
              bg="rgba(63,125,78,0.08)"
              border="rgba(63,125,78,0.25)"
            >
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {result.where_they_align}
              </p>
            </ResultSection>

            {/* Where they differ */}
            <ResultSection
              index={3}
              icon={<Swords className="w-4 h-4" />}
              label="Where You Differ"
              color="var(--saffron)"
              bg="var(--saffron-soft)"
              border="rgba(232,102,46,0.25)"
            >
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {result.where_they_differ}
              </p>
            </ResultSection>

            {/* What to examine */}
            <ResultSection
              index={4}
              icon={<HelpCircle className="w-4 h-4" />}
              label="What to Examine"
              color="var(--gold-accent)"
              bg="rgba(120,53,15,0.08)"
              border="rgba(245,158,11,0.25)"
            >
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {result.what_to_examine}
              </p>
            </ResultSection>

            {/* Questions */}
            {result.questions_for_me.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 5 * 0.12 }}
                className="rounded-2xl p-5"
                style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)' }}
              >
                <button
                  className="w-full flex items-center justify-between focus:outline-none focus-visible:ring-2"
                  onClick={() => setShowQuestions(v => !v)}
                  aria-expanded={showQuestions}
                >
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4" style={{ color: 'var(--slate-accent)' }} aria-hidden="true" />
                    <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--slate-accent)' }}>
                      Questions for You
                    </span>
                  </div>
                  {showQuestions
                    ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                    : <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                  }
                </button>
                <AnimatePresence>
                  {showQuestions && (
                    <motion.ol
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-3 space-y-2 list-none overflow-hidden"
                    >
                      {result.questions_for_me.map((q, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                          <span
                            className="shrink-0 w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center mt-0.5"
                            style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)' }}
                            aria-hidden="true"
                          >
                            {i + 1}
                          </span>
                          {q}
                        </li>
                      ))}
                    </motion.ol>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Experiment */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 6 * 0.12 }}
              className="rounded-2xl p-5 flex items-start gap-4"
              style={{
                background: 'linear-gradient(135deg, var(--saffron-soft), var(--saffron-soft))',
                border: '2px solid var(--saffron)',
                boxShadow: '0 4px 20px var(--saffron-glow)',
              }}
            >
              <div
                className="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ background: 'var(--saffron)', color: 'var(--on-saffron)' }}
                aria-hidden="true"
              >
                <FlaskConical className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest mb-1.5" style={{ color: 'var(--saffron)' }}>
                  Your Experiment
                </p>
                <p className="text-sm font-medium leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                  {result.experiment}
                </p>
              </div>
            </motion.div>

            {/* Conclusion */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 7 * 0.12 }}
              className="rounded-2xl p-5"
              style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)' }}
            >
              <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted)' }}>
                Conclusion
              </p>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {result.conclusion}
              </p>
            </motion.div>

            {/* Try another */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 8 * 0.12 }}
              className="flex justify-center pt-2"
            >
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
                style={{
                  background: 'var(--card-surface)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--text-muted)',
                  boxShadow: 'var(--card-shadow)',
                }}
              >
                <RotateCcw className="w-4 h-4" aria-hidden="true" />
                Compare Another Belief
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
