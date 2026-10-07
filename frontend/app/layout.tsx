import type { Metadata, Viewport } from 'next';
import localFont from 'next/font/local';
import './globals.css';
import { themeInitScript } from '@/lib/theme';
import { ClientShell } from './ClientShell';
import { AmbientBackground } from '@/components/background/AmbientBackground';

// ─────────────────────────────────────────────────────────────
// Self-hosted fonts (offline-safe, no Google Fonts CDN)
// ─────────────────────────────────────────────────────────────
const jakarta = localFont({
  src: [
    { path: '../public/fonts/jakarta-400.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/jakarta-600.woff2', weight: '600', style: 'normal' },
    { path: '../public/fonts/jakarta-700.woff2', weight: '700', style: 'normal' },
    { path: '../public/fonts/jakarta-800.woff2', weight: '800', style: 'normal' },
  ],
  variable: '--font-jakarta',
  display: 'swap',
  preload: true,
});

const playfair = localFont({
  src: [
    { path: '../public/fonts/playfair-400.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/playfair-400i.woff2', weight: '400', style: 'italic' },
    { path: '../public/fonts/playfair-600.woff2', weight: '600', style: 'normal' },
    { path: '../public/fonts/playfair-700.woff2', weight: '700', style: 'normal' },
  ],
  variable: '--font-playfair',
  display: 'swap',
  preload: false,
});

const notoDevanagari = localFont({
  src: [
    { path: '../public/fonts/noto-devanagari-400.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/noto-devanagari-600.woff2', weight: '600', style: 'normal' },
    { path: '../public/fonts/noto-devanagari-700.woff2', weight: '700', style: 'normal' },
  ],
  variable: '--font-devanagari',
  display: 'swap',
  preload: false,
});

// ─────────────────────────────────────────────────────────────
// Metadata
// ─────────────────────────────────────────────────────────────
export const metadata: Metadata = {
  title: 'Jagrat — The Awakened',
  description:
    'Jagrat is an AI-powered reflection tool inspired by the teachings of Swami Vivekananda. Build mental strength, clarity, and purpose.',
  manifest: '/manifest.json',
  keywords: ['Swami Vivekananda', 'mental wellness', 'AI mentor', 'reflection', 'jagrat'],
  openGraph: {
    title: 'Jagrat — The Awakened',
    description: 'AI-powered reflection guided by the philosophy of Swami Vivekananda.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FFF7EA' },
    { media: '(prefers-color-scheme: dark)',  color: '#0B0D13' },
  ],
  width: 'device-width',
  initialScale: 1,
};

// ─────────────────────────────────────────────────────────────
// Root Layout
// ─────────────────────────────────────────────────────────────
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* FOUC prevention — runs before paint */}
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      {/* suppressHydrationWarning prevents false positives from browser extensions */}
      <body
        className={`${jakarta.variable} ${playfair.variable} ${notoDevanagari.variable} min-h-screen flex flex-col antialiased`}
        suppressHydrationWarning
      >
        <AmbientBackground />
        <ClientShell>{children}</ClientShell>
      </body>
    </html>
  );
}
