'use client';

import { useState, useEffect, useCallback } from 'react';
import { Moon, Sun } from 'lucide-react';
import { toggleTheme, getStoredTheme, type Theme } from '@/lib/theme';

/**
 * FloatingThemeToggle - A floating button for theme switching
 * Shows on pages without Navbar (landing, login, onboarding)
 */
export function FloatingThemeToggle() {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    setTheme(getStoredTheme());
  }, []);

  const handleToggleTheme = useCallback(() => {
    setTheme(prev => toggleTheme(prev));
  }, []);

  return (
    <button
      onClick={handleToggleTheme}
      className="fixed top-4 right-4 z-50 w-11 h-11 rounded-full flex items-center justify-center transition-all hover:scale-105 active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
      style={{
        background: 'var(--card-surface)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--shadow-float)',
        backdropFilter: 'blur(12px)',
        color: 'var(--saffron)',
      }}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark'
        ? <Sun className="w-5 h-5" aria-hidden="true" />
        : <Moon className="w-5 h-5" aria-hidden="true" />
      }
    </button>
  );
}
