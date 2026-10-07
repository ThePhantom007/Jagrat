'use client';

/**
 * ClientShell — root client wrapper.
 * Provides ThemeProvider to the entire app, registers the SW,
 * and keeps <html lang> in sync with the user's language choice.
 */

import { useEffect } from 'react';
import { ThemeProvider, useAppContext } from '@/components/ThemeProvider';

/** Syncs the html[lang] attribute to the active language — helps screen readers and bots. */
function LangSyncer() {
  const { lang } = useAppContext();
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return null;
}

function ServiceWorkerRegistrar() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;

    // In development, unregister all service workers to prevent stale chunk caching
    if (process.env.NODE_ENV === 'development') {
      navigator.serviceWorker.getRegistrations().then(regs => {
        regs.forEach(reg => reg.unregister());
      });
      return;
    }

    navigator.serviceWorker.register('/sw.js').catch(() => {
      // SW registration failure is non-fatal — app works without it
    });
  }, []);
  return null;
}

export function ClientShell({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <LangSyncer />
      <ServiceWorkerRegistrar />
      {/* suppressHydrationWarning prevents false positives from browser extensions
          (e.g. Bitdefender's bis_skin_checked) injecting attributes into divs */}
      <div suppressHydrationWarning>
        {children}
      </div>
    </ThemeProvider>
  );
}
