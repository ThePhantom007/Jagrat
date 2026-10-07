'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, Moon, Sun, Globe, Menu, X } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { toggleTheme, getStoredTheme, type Theme } from '@/lib/theme';
import { LANGUAGES, t, type Language } from '@/lib/i18n';

interface NavbarProps {
  lang: Language;
  onLangChange: (lang: Language) => void;
}

const NAV_LINKS = [
  { href: '/app/chat',      labelKey: 'nav_mentor'    },
  { href: '/app/journal',   labelKey: 'nav_journal'   },
  { href: '/app/growth',    labelKey: 'nav_growth'    },
  { href: '/app/vs-me',     labelKey: 'nav_vsme'      },
  { href: '/app/actions',   labelKey: 'nav_actions'   },
  { href: '/app/teachings', labelKey: 'nav_teachings' },
  { href: '/app/history',   labelKey: 'nav_history'   },
];

export function Navbar({ lang, onLangChange }: NavbarProps) {
  const pathname = usePathname();
  const [theme, setTheme] = useState<Theme>('light');
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setTheme(getStoredTheme());
  }, []);

  const handleToggleTheme = useCallback(() => {
    setTheme(prev => toggleTheme(prev));
  }, []);

  const links = NAV_LINKS;
  // Active if pathname starts with the link href (handles /app/chat, /app/journal etc.)
  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/');

  return (
    <header
      className="sticky top-0 z-50 glass-nav"
      role="banner"
    >
      <nav
        className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4"
        aria-label="Main navigation"
      >
        {/* ── Brand Logo ── */}
        <Link
          href="/"
          className="flex items-center gap-2 shrink-0 group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded-md"
          aria-label="Jagrat — Home"
        >
          <span
            className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-sm font-bold transition-transform group-hover:scale-105"
            style={{ background: 'var(--saffron-primary)' }}
            aria-hidden="true"
          >
            <Zap className="w-4 h-4" />
          </span>
          <span
            className="text-lg font-bold tracking-tight leading-none"
            style={{ color: 'var(--text-primary)' }}
          >
            {t(lang, 'brand')}
          </span>
        </Link>

        {/* ── Desktop Nav Links ── */}
        <ul className="hidden md:flex items-center gap-1" role="list">
          {links.map(({ href, labelKey }) => {
            const active = isActive(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1"
                  style={{
                    color: active ? 'var(--saffron-primary)' : 'var(--text-muted)',
                    background: active ? 'var(--saffron-soft)' : 'transparent',
                    fontWeight: active ? 600 : 500,
                  }}
                  aria-current={active ? 'page' : undefined}
                >
                  {t(lang, labelKey)}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* ── Controls ── */}
        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors focus:outline-none focus-visible:ring-2"
                style={{
                  color: 'var(--text-muted)',
                  background: 'var(--saffron-soft)',
                }}
                aria-label="Select language"
              >
                <Globe className="w-3.5 h-3.5" aria-hidden="true" />
                <span className="hidden sm:inline">
                  {LANGUAGES.find(l => l.code === lang)?.nativeLabel ?? 'EN'}
                </span>
              </button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="z-[100] min-w-[160px] rounded-xl p-1.5 shadow-lg glass border"
                style={{
                  background: 'var(--card-surface)',
                  borderColor: 'var(--card-border)',
                  boxShadow: 'var(--shadow-float)',
                }}
                sideOffset={8}
                align="end"
              >
                {LANGUAGES.map(({ code, nativeLabel, label }) => (
                  <DropdownMenu.Item
                    key={code}
                    onSelect={() => onLangChange(code)}
                    className="flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer outline-none transition-colors"
                    style={{
                      color: lang === code ? 'var(--saffron-primary)' : 'var(--text-primary)',
                      background: lang === code ? 'var(--saffron-soft)' : 'transparent',
                      fontWeight: lang === code ? 600 : 400,
                    }}
                    onMouseEnter={e => {
                      if (lang !== code) (e.currentTarget as HTMLElement).style.background = 'var(--slate-soft)';
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.background = lang === code ? 'var(--saffron-soft)' : 'transparent';
                    }}
                  >
                    <span>{nativeLabel}</span>
                    <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>{label}</span>
                  </DropdownMenu.Item>
                ))}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>

          {/* Theme Toggle */}
          <button
            onClick={handleToggleTheme}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-2"
            style={{
              color: 'var(--text-muted)',
              background: 'var(--saffron-soft)',
            }}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark'
              ? <Sun className="w-4 h-4" aria-hidden="true" />
              : <Moon className="w-4 h-4" aria-hidden="true" />
            }
          </button>

          {/* Mobile Menu Toggle */}
          <button
            className="md:hidden w-8 h-8 rounded-lg flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-2"
            style={{ color: 'var(--text-muted)', background: 'var(--saffron-soft)' }}
            onClick={() => setMobileOpen(v => !v)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </nav>

      {/* ── Mobile Menu ── */}
      {mobileOpen && (
        <div
          className="md:hidden px-4 pb-4 pt-1 flex flex-col gap-1"
          style={{ borderTop: '1px solid var(--card-border)' }}
        >
          {links.map(({ href, labelKey }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{
                  color: active ? 'var(--saffron-primary)' : 'var(--text-muted)',
                  background: active ? 'var(--saffron-soft)' : 'transparent',
                  fontWeight: active ? 600 : 500,
                }}
                aria-current={active ? 'page' : undefined}
              >
                {t(lang, labelKey)}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}
