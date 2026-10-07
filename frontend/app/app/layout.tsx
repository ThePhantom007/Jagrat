import type { Metadata } from 'next';
import { AppShell } from './AppShell';

export const metadata: Metadata = {
  title: { template: '%s | Jagrat', default: 'Jagrat — The Awakened' },
};

/**
 * Protected app shell layout — wraps all /app/* routes.
 * Renders the Navbar, sticky SafetyBanner, and the page content.
 * Kept as a Server Component; client interaction lives in AppShell.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
