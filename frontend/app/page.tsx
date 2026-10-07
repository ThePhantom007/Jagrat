'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Ear, BookOpen, BrainCircuit, ShieldCheck, ArrowRight, PhoneCall } from 'lucide-react';
import { HeroSection } from '@/components/HeroSection';
import { FloatingThemeToggle } from '@/components/FloatingThemeToggle';
import { useAppContext } from '@/components/ThemeProvider';
import { t } from '@/lib/i18n';

// ─────────────────────────────────────────────────────────────
// Three-Layer Shield Preview Cards
// ─────────────────────────────────────────────────────────────
const SHIELD_LAYERS = [
  {
    icon: <Ear className="w-5 h-5" aria-hidden="true" />,
    label: 'Layer 1 — Listening',
    title: 'The Mirror',
    accent: 'var(--text-muted)',
    accentBg: 'rgba(100,116,139,0.08)',
    accentBorder: 'rgba(100,116,139,0.25)',
    body: "I hear that you're carrying something heavy. Before exploring philosophy, let me ask: what is one thing you genuinely tried, even if it didn't work out?",
    tag: 'Socratic Empathy · No Toxic Positivity',
  },
  {
    icon: <BookOpen className="w-5 h-5" aria-hidden="true" />,
    label: 'Layer 2 — Documented',
    title: 'The Authentic Anchor',
    accent: 'var(--gold-accent)',
    accentBg: 'rgba(120,53,15,0.10)',
    accentBorder: 'rgba(245,158,11,0.35)',
    body: '"The greatest sin is to think yourself weak." — Swami Vivekananda',
    tag: '✓ Complete Works, Vol. II · p. 302',
    scripture: true,
  },
  {
    icon: <BrainCircuit className="w-5 h-5" aria-hidden="true" />,
    label: 'Layer 3 — AI Reflection',
    title: 'The Application',
    accent: 'var(--saffron)',
    accentBg: 'var(--saffron-soft)',
    accentBorder: 'rgba(232,102,46,0.25)',
    body: "Vivekananda's teaching isn't motivational fluff — it's a diagnosis. The habit of self-minimisation is the obstacle, not your intelligence. 🎯 Next Step: Write 3 moments you showed strength this month.",
    tag: 'Layer 3 — AI Interpretation',
  },
];

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────
export default function LandingPage() {
  const { lang } = useAppContext();

  return (
    <div className="flex flex-col">
      <FloatingThemeToggle />

      {/* ── HERO ── */}
      <HeroSection />

      {/* ── SEE HOW A REPLY IS BUILT ── */}
      <section className="py-20 px-4" aria-labelledby="shield-heading">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <motion.div
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest"
                style={{ background: 'var(--saffron-soft)', color: 'var(--saffron-strong)', border: '1px solid rgba(232,102,46,0.25)' }}>
                <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" /> See How a Reply Is Built
              </span>
            </motion.div>
            <motion.h2
              id="shield-heading"
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: 0.1, duration: 0.5 }}
              className="text-3xl sm:text-4xl font-extrabold" style={{ color: 'var(--text-primary)' }}
            >
              Every Response Has Three Layers
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }} whileInView={{ opacity: 1 }}
              viewport={{ once: true }} transition={{ delay: 0.2, duration: 0.5 }}
              className="text-base max-w-2xl mx-auto" style={{ color: 'var(--text-muted)' }}
            >
              Jagrat never conflates AI-generated content with authenticated Vivekananda teachings.
              Every response is structurally separated into three clearly labeled layers.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {SHIELD_LAYERS.map((layer, i) => (
              <motion.div
                key={layer.label}
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.12, duration: 0.5 }}
                className="rounded-2xl p-6 space-y-3 flex flex-col"
                style={{ background: layer.accentBg, border: `1px solid ${layer.accentBorder}`, boxShadow: 'var(--card-shadow)' }}
              >
                <div className="flex items-center gap-2" style={{ color: layer.accent }}>
                  {layer.icon}
                  <span className="text-xs font-bold uppercase tracking-widest">{layer.label}</span>
                </div>
                <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{layer.title}</h3>
                <p
                  className={`text-sm leading-relaxed flex-1 ${layer.scripture ? 'font-scripture italic text-base' : ''}`}
                  style={{ color: 'var(--text-primary)' }}
                >
                  {layer.body}
                </p>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full w-fit"
                  style={{ background: layer.accentBorder, color: layer.accent }}>
                  {layer.tag}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section className="py-24 px-4 text-center" aria-labelledby="final-cta-heading">
        <div className="max-w-2xl mx-auto space-y-6">
          <motion.h2 id="final-cta-heading"
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }}
            className="text-3xl sm:text-4xl font-extrabold" style={{ color: 'var(--text-primary)' }}>
            Ready to awaken?
          </motion.h2>
          <motion.p initial={{ opacity: 0 }} whileInView={{ opacity: 1 }}
            viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-base" style={{ color: 'var(--text-muted)' }}>
            A reflection space for students building inner strength through verified philosophy.
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full text-base font-bold transition-all hover:scale-[1.03] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
              style={{ background: 'var(--saffron)', color: 'var(--on-saffron)', boxShadow: '0 6px 24px var(--saffron-glow)' }}
            >
              ⚡ {t(lang, 'cta_begin')} <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link
              href="/app/chat"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full text-base font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
              style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)', boxShadow: 'var(--card-shadow)' }}
            >
              {t(lang, 'cta_guest')}
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="py-8 px-4" style={{ borderTop: '1px solid var(--card-border)' }}>
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t(lang, 'brand')} — {t(lang, 'brand_tagline')}
            </span>
            <span>·</span>
            <Link href="/app/honesty" className="hover:underline" style={{ color: 'var(--saffron-strong)' }}>
              {t(lang, 'honesty_title')}
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <a href="tel:14416" className="flex items-center gap-1 font-semibold" style={{ color: 'var(--danger)' }}>
              <PhoneCall className="w-3 h-3" aria-hidden="true" /> Tele-MANAS 14416
            </a>
          </div>
        </div>
        <p className="text-center text-xs mt-4" style={{ color: 'var(--text-muted)' }}>
          {t(lang, 'footer_disclaimer')}
        </p>
      </footer>

    </div>
  );
}
