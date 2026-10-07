'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Zap, Shield, BookOpen, Brain } from 'lucide-react';
import { useAppContext } from '@/components/ThemeProvider';
import { t } from '@/lib/i18n';

// ─────────────────────────────────────────────────────────────
// Per-language accent word
// ─────────────────────────────────────────────────────────────
const ACCENT_WORD: Record<string, string> = {
  en: 'Perfection',
  hi: 'पूर्णता',
  bn: 'পূর্ণতাকে',
  mr: 'पूर्णत्वाला',
  ta: 'பூர்ணத்தை',
  te: 'పరిపూర్ణతను',
};

function HeadlineWithAccent({ lang }: { lang: string }) {
  const title = t(lang as any, 'landing_title');
  const accent = ACCENT_WORD[lang] ?? ACCENT_WORD['en'];
  const parts = title.split(accent);

  if (parts.length < 2) return <>{title}</>;

  return (
    <>
      {parts[0]}
      <span className="relative inline-block" style={{ color: 'var(--saffron)' }}>
        {accent}
        <motion.span
          className="absolute bottom-0 left-0 h-0.5 rounded-full"
          style={{ background: 'var(--saffron)', width: '100%' }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 0.9, duration: 0.5, ease: 'easeOut' }}
          aria-hidden="true"
        />
      </span>
      {parts.slice(1).join(accent)}
    </>
  );
}

const BADGE_ITEMS = [
  { icon: <Shield className="w-3.5 h-3.5" />,  text: 'Three-Layer Response Architecture' },
  { icon: <BookOpen className="w-3.5 h-3.5" />, text: 'Source-Verified Teachings' },
  { icon: <Brain className="w-3.5 h-3.5" />,    text: 'Socratic, Not Prescriptive' },
];

export function HeroSection() {
  const { lang } = useAppContext();

  return (
    <section
      className="relative min-h-screen flex flex-col items-center justify-center px-4 pt-20 pb-16 overflow-hidden"
      aria-label="Hero — Jagrat home"
    >
      {/* ── Content — NO scroll-driven opacity, so buttons are always visible ── */}
      <div className="relative z-10 max-w-4xl mx-auto text-center space-y-8">

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight"
          style={{ color: 'var(--text-primary)' }}
        >
          <HeadlineWithAccent lang={lang} />
        </motion.h1>

        {/* Sub-headline */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.5 }}
          className="text-base sm:text-lg max-w-2xl mx-auto leading-relaxed"
          style={{ color: 'var(--text-muted)' }}
        >
          {t(lang, 'landing_subtitle')}
        </motion.p>

        {/* ── CTAs — animate not whileInView; they are above the fold ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <Link
            href="/login"
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-full text-base font-bold transition-all hover:scale-[1.03] active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
            style={{
              background: 'var(--saffron)',
              color: 'var(--on-saffron)',
              boxShadow: '0 6px 24px var(--saffron-glow)',
            }}
          >
            <Zap className="w-4 h-4" aria-hidden="true" />
            {t(lang, 'cta_begin')}
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
          </Link>

          <Link
            href="/app/chat"
            className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
            style={{
              background: 'var(--card-surface)',
              border: '1px solid var(--card-border)',
              color: 'var(--text-primary)',
              boxShadow: 'var(--card-shadow)',
            }}
          >
            {t(lang, 'cta_guest')}
          </Link>
        </motion.div>

        {/* Feature badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="flex flex-wrap justify-center gap-2 pt-2"
        >
          {BADGE_ITEMS.map((b, i) => (
            <motion.span
              key={b.text}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.8 + i * 0.1, duration: 0.3 }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
              style={{
                background: 'var(--card-surface)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-muted)',
                boxShadow: 'var(--card-shadow)',
              }}
            >
              <span style={{ color: 'var(--saffron)' }} aria-hidden="true">{b.icon}</span>
              {b.text}
            </motion.span>
          ))}
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        aria-hidden="true"
      >
        <div className="w-px h-8 rounded-full" style={{ background: 'var(--card-border)' }} />
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--saffron)' }} />
      </motion.div>
    </section>
  );
}
