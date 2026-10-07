'use client';

import { type ReactNode } from 'react';
import { motion } from 'framer-motion';

interface BentoCardProps {
  /** Card title shown in the header */
  title: string | ReactNode;
  /** Optional emoji / icon prefix for the title */
  icon?: string;
  /** Column span on the grid (1 or 2) */
  colSpan?: 1 | 2;
  /** Row span on the grid (1 or 2) */
  rowSpan?: 1 | 2;
  /** Accent colour key: 'saffron' | 'gold' | 'slate' | 'success' | 'danger' */
  accent?: 'saffron' | 'gold' | 'slate' | 'success' | 'danger';
  /** Stagger animation index */
  index?: number;
  className?: string;
  children: ReactNode;
}

const ACCENT_STYLES = {
  saffron: {
    headerColor: 'var(--saffron-primary)',
    border: 'rgba(252,108,38,0.3)',
    topBar: 'var(--saffron-primary)',
  },
  gold: {
    headerColor: 'var(--gold-accent)',
    border: 'rgba(245,158,11,0.3)',
    topBar: 'var(--gold-accent)',
  },
  slate: {
    headerColor: 'var(--slate-accent)',
    border: 'rgba(100,116,139,0.25)',
    topBar: 'var(--slate-accent)',
  },
  success: {
    headerColor: 'var(--success)',
    border: 'rgba(22,163,74,0.3)',
    topBar: 'var(--success)',
  },
  danger: {
    headerColor: 'var(--danger)',
    border: 'rgba(220,38,38,0.3)',
    topBar: 'var(--danger)',
  },
};

export function BentoCard({
  title,
  icon,
  colSpan = 1,
  rowSpan = 1,
  accent = 'saffron',
  index = 0,
  className = '',
  children,
}: BentoCardProps) {
  const styles = ACCENT_STYLES[accent];

  const colClass = colSpan === 2 ? 'md:col-span-2' : 'col-span-1';
  const rowClass = rowSpan === 2 ? 'md:row-span-2' : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.1, duration: 0.45, ease: 'easeOut' }}
      className={`relative rounded-2xl overflow-hidden flex flex-col ${colClass} ${rowClass} ${className}`}
      style={{
        background: 'var(--card-surface)',
        border: `1px solid ${styles.border}`,
        boxShadow: 'var(--shadow-card)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      {/* Accent top bar */}
      <div
        className="absolute top-0 left-0 right-0 h-0.5"
        style={{ background: styles.topBar }}
        aria-hidden="true"
      />

      {/* Header */}
      <div
        className="px-5 pt-5 pb-3 flex items-center gap-2"
        style={{ borderBottom: `1px solid ${styles.border}` }}
      >
        {icon && (
          <span className="text-lg leading-none" aria-hidden="true">
            {icon}
          </span>
        )}
        <h2
          className="text-xs font-bold uppercase tracking-widest"
          style={{ color: styles.headerColor }}
        >
          {title}
        </h2>
      </div>

      {/* Content */}
      <div className="flex-1 px-5 py-4">{children}</div>
    </motion.div>
  );
}
