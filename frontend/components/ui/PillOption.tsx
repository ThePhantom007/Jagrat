'use client';

import { CheckCircle2 } from 'lucide-react';

interface PillOptionProps {
  emoji: string;
  label: string;
  selected: boolean;
  onClick: () => void;
}

/**
 * PillOption — Onboarding choice pill
 * Unselected: --pill-surface + subtle shadow
 * Selected: --saffron + white text + glow ring
 * role="radio" inside a radiogroup, keyboard arrow navigation
 */
export function PillOption({ emoji, label, selected, onClick }: PillOptionProps) {
  return (
    <button
      role="radio"
      aria-checked={selected}
      onClick={onClick}
      className="relative flex items-center justify-center gap-3 px-6 py-4 rounded-full text-left transition-all duration-200 active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 w-full sm:w-auto min-w-[200px]"
      style={{
        background: selected ? 'var(--saffron)' : 'var(--pill-surface)',
        border: selected ? '2px solid var(--saffron)' : '1px solid var(--card-border)',
        boxShadow: selected ? '0 0 0 3px var(--saffron-glow), var(--card-shadow)' : 'var(--card-shadow)',
        color: selected ? 'var(--on-saffron)' : 'var(--text-primary)',
      }}
    >
      <span className="text-2xl shrink-0" aria-hidden="true">{emoji}</span>
      <span className="text-base font-semibold leading-snug">{label}</span>
      {selected && (
        <CheckCircle2
          className="w-5 h-5 absolute right-4 top-1/2 -translate-y-1/2"
          style={{ color: 'var(--on-saffron)' }}
          aria-hidden="true"
        />
      )}
    </button>
  );
}
