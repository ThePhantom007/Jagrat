'use client';

import { type ReactNode, type ButtonHTMLAttributes } from 'react';

interface SaffronButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  children: ReactNode;
}

export function SaffronButton({
  variant = 'primary',
  size = 'md',
  pulse = false,
  children,
  className = '',
  ...props
}: SaffronButtonProps) {
  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base font-semibold',
    lg: 'px-8 py-4 text-lg font-bold',
  };

  const variantStyles = {
    primary: {
      background: 'var(--saffron)',
      color: 'var(--on-saffron)',
      boxShadow: '0 6px 24px var(--saffron-glow)',
    },
    outline: {
      background: 'transparent',
      color: 'var(--saffron)',
      border: '2px solid var(--saffron)',
    },
    ghost: {
      background: 'var(--saffron-soft)',
      color: 'var(--saffron-strong)',
      border: '1px solid rgba(232,102,46,0.25)',
    },
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full transition-all duration-200 hover:scale-[1.03] active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed ${sizeClasses[size]} ${pulse ? 'animate-pulse' : ''} ${className}`}
      style={variantStyles[variant]}
      {...props}
    >
      {children}
    </button>
  );
}
