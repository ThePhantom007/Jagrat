// ─────────────────────────────────────────────────────────────
// JAGRAT — Theme Management
// Vanilla Cloud (light) ↔ Obsidian Night (dark)
// ─────────────────────────────────────────────────────────────

const THEME_KEY = 'jagrat_theme';

export type Theme = 'light' | 'dark';

/**
 * Reads the persisted theme from localStorage, falling back to
 * system preference if nothing is stored.
 */
export function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'light';
  try {
    const stored = localStorage.getItem(THEME_KEY) as Theme | null;
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // localStorage not available (e.g. private browsing)
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Applies the theme class to <html> and persists the choice.
 */
export function applyTheme(theme: Theme): void {
  if (typeof window === 'undefined') return;
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // ignore
  }
}

/**
 * Toggles between light and dark, applies, and returns the new value.
 */
export function toggleTheme(current: Theme): Theme {
  const next: Theme = current === 'light' ? 'dark' : 'light';
  applyTheme(next);
  return next;
}

/**
 * Injects a blocking <script> snippet into <head> to prevent FOUC.
 * Call this as a Server Component script or inline in layout.
 */
export const themeInitScript = `
(function() {
  try {
    var t = localStorage.getItem('jagrat_theme');
    if (t === 'dark') { document.documentElement.classList.add('dark'); return; }
    if (t === 'light') return;
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.classList.add('dark');
    }
  } catch(e) {}
})();
`.trim();
