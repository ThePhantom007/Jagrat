'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sword, ChevronDown, ChevronUp, Send } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';
import type { ChallengeData } from '@/lib/types';

interface ChallengeCardProps {
  challenge: ChallengeData;
  lang?: Language;
  onReflectionSubmit?: (reflection: string) => void;
}

export function ChallengeCard({
  challenge,
  lang = 'en',
  onReflectionSubmit,
}: ChallengeCardProps) {
  const [expanded, setExpanded] = useState(true);
  const [reflection, setReflection] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!reflection.trim()) return;
    onReflectionSubmit?.(reflection.trim());
    setSubmitted(true);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="rounded-2xl overflow-hidden"
      style={{
        border: '1px solid rgba(239,68,68,0.3)',
        background: 'rgba(239,68,68,0.04)',
        boxShadow: '0 4px 24px rgba(239,68,68,0.06)',
      }}
    >
      {/* ── Header ── */}
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset"
        aria-expanded={expanded}
        aria-controls="challenge-body"
      >
        <div className="flex items-center gap-2.5">
          <span
            className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs"
            style={{ background: 'linear-gradient(135deg, #EF4444, #F97316)' }}
            aria-hidden="true"
          >
            <Sword className="w-3.5 h-3.5" />
          </span>
          <span className="text-sm font-bold uppercase tracking-widest" style={{ color: '#EF4444' }}>
            ⚔️ {t(lang, 'challenge_title')}
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
        }
      </button>

      {/* ── Body ── */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id="challenge-body"
            key="challenge-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div className="px-5 pb-5 space-y-4">
              {/* Stated Belief */}
              <div
                className="p-4 rounded-xl space-y-1"
                style={{ background: 'var(--slate-soft)', border: '1px solid var(--card-border)' }}
              >
                <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-subtle)' }}>
                  {t(lang, 'your_belief')}
                </p>
                <p className="text-sm italic font-medium" style={{ color: 'var(--text-primary)' }}>
                  &ldquo;{challenge.belief}&rdquo;
                </p>
              </div>

              {/* Underlying Assumption */}
              <div
                className="p-4 rounded-xl space-y-1"
                style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)' }}
              >
                <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-subtle)' }}>
                  {t(lang, 'assumption')}
                </p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {challenge.assumption}
                </p>
              </div>

              {/* Socratic Pivot */}
              <div
                className="p-4 rounded-xl space-y-2"
                style={{
                  background: 'linear-gradient(135deg, rgba(252,108,38,0.08), rgba(245,158,11,0.08))',
                  border: '1px solid var(--card-border)',
                }}
              >
                <p className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5" style={{ color: 'var(--saffron-primary)' }}>
                  💬 {t(lang, 'socratic_pivot')}
                </p>
                <p className="text-sm leading-relaxed font-medium" style={{ color: 'var(--text-primary)' }}>
                  &ldquo;{challenge.pivot}&rdquo;
                </p>
              </div>

              {/* Reflection Input */}
              {!submitted ? (
                <div className="flex gap-2">
                  <textarea
                    value={reflection}
                    onChange={e => setReflection(e.target.value)}
                    placeholder={t(lang, 'reflection_placeholder')}
                    rows={2}
                    className="flex-1 resize-none rounded-xl px-4 py-3 text-sm focus:outline-none focus-visible:ring-2 transition-all"
                    style={{
                      background: 'var(--card-surface)',
                      border: '1px solid var(--card-border)',
                      color: 'var(--text-primary)',
                    }}
                    aria-label="Your reflection"
                    onKeyDown={e => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit();
                    }}
                    data-gramm="false"
                    data-gramm_editor="false"
                    data-enable-grammarly="false"
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={!reflection.trim()}
                    className="self-end px-4 py-3 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
                    style={{
                      background: reflection.trim() ? 'var(--saffron)' : 'var(--slate-soft)',
                      color: reflection.trim() ? 'var(--on-saffron)' : 'var(--text-muted)',
                    }}
                    aria-label={t(lang, 'submit_reflection')}
                  >
                    <Send className="w-4 h-4" aria-hidden="true" />
                  </button>
                </div>
              ) : (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm px-4 py-3 rounded-xl"
                  style={{
                    background: 'rgba(22,163,74,0.08)',
                    border: '1px solid rgba(22,163,74,0.25)',
                    color: 'var(--success)',
                  }}
                >
                  ✓ Reflection submitted. Keep questioning.
                </motion.p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
