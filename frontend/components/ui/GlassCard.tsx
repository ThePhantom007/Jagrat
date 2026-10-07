'use client';

import { type ReactNode } from 'react';
import { motion, type MotionProps } from 'framer-motion';

interface GlassCardProps {
  variant?: 'default' | 'accent' | 'muted';
  className?: string;
  children: ReactNode;
  animate?: boolean;
  index?: number;
}

const VARIANTS = {
  default: {
    background: 'var(--card-surface)',
    border: '1px solid var(--card-border)',
    boxShadow: 'var(--card-shadow)',
  },
  accent: {
    background: 'linear-gradient(135deg, rgba(232,102,46,0.08), rgba(245,158,11,0.06))',
    border: '1px solid rgba(232,102,46,0.25)',
    boxShadow: '0 4px 24px rgba(232,102,46,0.08)',
  },
  muted: {
    background: 'var(--card-surface)',
    border: '1px solid var(--card-border)',
    boxShadow: 'none',
  },
};

export function GlassCard({ variant = 'default', className = '', children, animate = true, index = 0 }: GlassCardProps) {
  const style = VARIANTS[variant];
  const motionProps: MotionProps = animate
    ? {
        initial: { opacity: 0, y: 16 },
        animate: { opacity: 1, y: 0 },
        transition: { delay: index * 0.1, duration: 0.4, ease: 'easeOut' },
      }
    : {};

  return (
    <motion.div
      {...motionProps}
      className={`rounded-2xl p-6 backdrop-blur-[14px] ${className}`}
      style={{
        ...style,
        WebkitBackdropFilter: 'blur(14px) saturate(180%)',
        backdropFilter: 'blur(14px) saturate(180%)',
      }}
    >
      {children}
    </motion.div>
  );
}
