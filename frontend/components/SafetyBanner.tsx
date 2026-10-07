'use client';

import { AlertTriangle } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';

interface SafetyBannerProps {
  lang: Language;
}

export function SafetyBanner({ lang }: SafetyBannerProps) {
  return (
    <div
      role="alert"
      aria-live="polite"
      className="w-full px-4 py-2.5 flex items-center justify-between gap-3 text-sm"
      style={{
        background: 'linear-gradient(90deg, rgba(252,108,38,0.12) 0%, rgba(245,158,11,0.10) 100%)',
        borderBottom: '1px solid var(--card-border)',
      }}
    >
      <div className="flex items-center gap-2.5 flex-1 min-w-0">
        <AlertTriangle
          className="w-4 h-4 shrink-0"
          style={{ color: 'var(--saffron-primary)' }}
          aria-hidden="true"
        />
        <p
          className="text-xs leading-relaxed truncate"
          style={{ color: 'var(--text-muted)' }}
        >
          <span
            className="font-semibold mr-1"
            style={{ color: 'var(--saffron-primary)' }}
          >
            ⚠️
          </span>
          {t(lang, 'safety_banner')}
        </p>
      </div>
    </div>
  );
}
