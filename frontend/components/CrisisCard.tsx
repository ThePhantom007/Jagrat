'use client';

import { motion } from 'framer-motion';
import { PhoneCall, Heart } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';

interface CrisisCardProps {
  lang?: Language;
}

/**
 * Renders when the backend returns crisis: true.
 * Replaces the entire mentor response with a calm, supportive card.
 * Must always show Tele-MANAS 14416.
 */
export function CrisisCard({ lang = 'en' }: CrisisCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-full rounded-2xl p-6 space-y-4"
      style={{
        background: 'linear-gradient(135deg, rgba(220,38,38,0.06), rgba(220,38,38,0.02))',
        border: '1px solid rgba(220,38,38,0.25)',
      }}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(220,38,38,0.1)' }}
          aria-hidden="true"
        >
          <Heart className="w-5 h-5" style={{ color: 'var(--danger)' }} />
        </div>
        <div>
          <h3 className="text-base font-bold" style={{ color: 'var(--danger)' }}>
            {t(lang, 'crisis_title')}
          </h3>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            You are not alone. Help is available right now.
          </p>
        </div>
      </div>

      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
        {t(lang, 'crisis_text')}
      </p>

      <a
        href="tel:14416"
        className="flex items-center justify-center gap-3 w-full py-3.5 rounded-xl text-base font-bold text-white transition-all active:scale-95 focus:outline-none focus-visible:ring-2"
        style={{ background: 'var(--danger)' }}
        aria-label="Call Tele-MANAS crisis helpline: 14416"
      >
        <PhoneCall className="w-5 h-5" aria-hidden="true" />
        Call Tele-MANAS — 14416
      </a>

      <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
        Free · Confidential · Available 24/7 in 20+ languages
      </p>
    </motion.div>
  );
}
