'use client';

import { useAppContext } from '@/components/ThemeProvider';
import { Navbar } from '@/components/Navbar';
import { SafetyBanner } from '@/components/SafetyBanner';

/**
 * Client component that renders Navbar + SafetyBanner for all /app/* routes.
 * SafetyBanner shown on all app routes (dismissible per-session).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { lang, setLang } = useAppContext();

  return (
    <>
      <Navbar lang={lang} onLangChange={setLang} />
      <SafetyBanner lang={lang} />
      <main id="main-content" className="flex-1 bg-mesh">
        {children}
      </main>
    </>
  );
}
