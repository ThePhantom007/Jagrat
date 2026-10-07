'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, BrainCircuit, BookOpen, Ear, PhoneCall, Info } from 'lucide-react';
import { SpeechButton } from './SpeechButton';
import { ChallengeCard } from './ChallengeCard';
import { t, type Language } from '@/lib/i18n';
import type { MentorResponse } from '@/lib/types';

interface ThreeLayerCardProps {
  response: MentorResponse;
  lang?: Language;
}

// Staggered reveal for the 3 cards
const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.45, ease: 'easeOut' },
  }),
};

export function ThreeLayerCard({ response, lang = 'en' }: ThreeLayerCardProps) {
  // If crisis is true, DON'T render this card at all
  if (response.crisis === true) {
    return null;
  }

  return (
    <div className="space-y-3 w-full">

      {/* ── Layer 1: Listening Card (The Mirror) ── */}
      <motion.div
        custom={0}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="p-5 rounded-r-2xl rounded-tl-2xl"
        style={{
          background: 'rgba(100,116,139,0.08)',
          borderTop: '1px solid rgba(100,116,139,0.2)',
          borderRight: '1px solid rgba(100,116,139,0.2)',
          borderBottom: '1px solid rgba(100,116,139,0.2)',
          borderLeft: '4px solid var(--slate-accent)',
        }}
        role="region"
        aria-label={t(lang, 'listening_title')}
      >
        <div className="flex items-center gap-2 mb-3">
          <Ear className="w-4 h-4 shrink-0" style={{ color: 'var(--slate-accent)' }} aria-hidden="true" />
          <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--slate-accent)' }}>
            {t(lang, 'listening_title')}
          </h3>
        </div>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
          {response.listening.summary}
        </p>
        {response.listening.question && (
          <p
            className="mt-3 text-sm italic leading-relaxed pl-3"
            style={{
              color: 'var(--text-muted)',
              borderLeft: '2px solid var(--card-border)',
            }}
          >
            {response.listening.question}
          </p>
        )}
      </motion.div>

      {/* ── Layer 2: Documented Teaching Card (The Authentic Anchor) ── */}
      {response.documented !== null ? (
        <motion.div
          custom={1}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          className="p-6 rounded-2xl"
          style={{
            background: 'rgba(120,53,15,0.12)',
            border: '1px solid rgba(245,158,11,0.35)',
            boxShadow: '0 4px 24px rgba(245,158,11,0.08)',
          }}
          role="region"
          aria-label={t(lang, 'documented_title')}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" style={{ color: 'var(--gold-accent)' }} aria-hidden="true" />
              <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--gold-accent)' }}>
                {t(lang, 'documented_title')}
              </h3>
            </div>
          </div>

          {/* Verbatim Quotation */}
          <blockquote
            className="font-scripture text-lg leading-[1.7] relative mb-4"
            style={{ color: 'var(--text-primary)' }}
          >
            <span
              className="absolute -left-2 -top-1 text-4xl leading-none font-scripture"
              style={{ color: 'var(--gold-accent)', opacity: 0.5 }}
              aria-hidden="true"
            >
              &ldquo;
            </span>
            {response.documented.quote}
          </blockquote>

          {/* Source footer */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3" style={{ borderTop: '1px solid rgba(245,158,11,0.2)' }}>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" style={{ color: 'var(--success)' }} aria-hidden="true" />
              <span className="text-xs font-semibold" style={{ color: 'var(--success)' }}>
                {t(lang, 'verified_badge')}
              </span>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                • {response.documented.source.work}
                {response.documented.source.volume ? `, ${response.documented.source.volume}` : ''}
                {response.documented.source.page ? `, p. ${response.documented.source.page}` : ''}
              </span>
            </div>
            <SpeechButton text={response.documented.quote} lang={lang} />
          </div>
        </motion.div>
      ) : (
        <motion.div
          custom={1}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          className="p-5 rounded-2xl flex gap-3"
          style={{
            background: 'var(--slate-soft)',
            border: '1px solid var(--card-border)',
          }}
          role="region"
        >
          <Info className="w-5 h-5 shrink-0" style={{ color: 'var(--slate-accent)' }} aria-hidden="true" />
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
            No documented teaching in our library matches closely enough. What follows is AI reflection only.
          </p>
        </motion.div>
      )}

      {/* ── Layer 3: AI Interpretation Card (The Application) ── */}
      <motion.div
        custom={2}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="p-5 rounded-2xl"
        style={{
          background: 'var(--card-surface)',
          border: '1px solid var(--card-border)',
          boxShadow: 'var(--shadow-card)',
        }}
        role="region"
        aria-label="AI Reflection"
      >
        {/* AI interpretation header */}
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="w-4 h-4" style={{ color: 'var(--saffron-primary)' }} aria-hidden="true" />
          <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--saffron-primary)' }}>
            Reflection
          </span>
        </div>

        <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-primary)' }}>
          {response.reflection.text}
        </p>

        {/* Next Step callout */}
        {response.reflection.nextStep && (
          <div
            className="p-4 rounded-xl"
            style={{
              background: 'linear-gradient(135deg, var(--saffron-soft), var(--gold-soft))',
              border: '1px solid var(--card-border)',
            }}
          >
            <p className="text-xs font-bold uppercase tracking-widest mb-1.5 flex items-center gap-1.5" style={{ color: 'var(--saffron-primary)' }}>
              🎯 {t(lang, 'next_step')}
            </p>
            <p className="text-sm font-medium leading-relaxed" style={{ color: 'var(--text-primary)' }}>
              {response.reflection.nextStep}
            </p>
          </div>
        )}
      </motion.div>

      {/* ── Challenge Card (conditional) ── */}
      {response.challenge && (
        <ChallengeCard challenge={response.challenge} lang={lang} />
      )}
    </div>
  );
}
