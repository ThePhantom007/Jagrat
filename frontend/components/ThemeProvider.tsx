'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { getStoredTheme, applyTheme, type Theme } from '@/lib/theme';
import { type Language } from '@/lib/i18n';

// ─────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────
interface AppContextValue {
  theme: Theme;
  toggleTheme: () => void;
  lang: Language;
  setLang: (lang: Language) => void;
}

const AppContext = createContext<AppContextValue>({
  theme: 'light',
  toggleTheme: () => {},
  lang: 'en',
  setLang: () => {},
});

export const useAppContext = () => useContext(AppContext);

// ─────────────────────────────────────────────────────────────
// Provider
// ─────────────────────────────────────────────────────────────
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  const [lang, setLangState] = useState<Language>('en');

  // Hydrate from localStorage on mount
  useEffect(() => {
    const stored = getStoredTheme();
    setTheme(stored);
    applyTheme(stored);

    const storedLang = localStorage.getItem('jagrat_lang') as Language | null;
    if (storedLang) setLangState(storedLang);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const next: Theme = prev === 'light' ? 'dark' : 'light';
      applyTheme(next);
      return next;
    });
  }, []);

  const setLang = useCallback((l: Language) => {
    setLangState(l);
    try { localStorage.setItem('jagrat_lang', l); } catch { /* ignore */ }
  }, []);

  return (
    <AppContext.Provider value={{ theme, toggleTheme, lang, setLang }}>
      {children}
    </AppContext.Provider>
  );
}
