'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Zap, Mail, Lock, User, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { FloatingThemeToggle } from '@/components/FloatingThemeToggle';
import { useAppContext } from '@/components/ThemeProvider';
import { t } from '@/lib/i18n';
import { signup, login, createProfile, getProfileId } from '@/lib/api';

export default function LoginPage() {
  const { lang } = useAppContext();
  const router = useRouter();

  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) return;
    if (mode === 'signup' && !name.trim()) return;

    setLoading(true);
    setError(null);

    try {
      if (mode === 'signup') {
        await signup(email.trim(), password, name.trim());
      } else {
        await login(email.trim(), password);
      }
      router.push('/onboarding');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!getProfileId()) {
        await createProfile('Friend');
      }
    } catch { /* non-fatal */ }
    setLoading(false);
    router.push('/app/chat');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative w-full max-w-md"
      >
        <div
          className="rounded-3xl p-8 space-y-6"
          style={{
            background: 'var(--card-surface)',
            border: '1px solid var(--card-border)',
            boxShadow: 'var(--shadow-float)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
          }}
        >
          {/* Brand */}
          <div className="flex flex-col items-center gap-3 text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg"
              style={{ background: 'linear-gradient(135deg, var(--saffron-primary), var(--gold-accent))' }}
              aria-hidden="true"
            >
              <Zap className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {t(lang, 'brand')}
              </h1>
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                Step inside to awaken your inner potential.
              </p>
            </div>
          </div>

          {/* Tab switcher: Login | Sign Up */}
          <div
            className="flex rounded-xl p-1 gap-1"
            style={{ background: 'var(--bg-secondary)' }}
            role="tablist"
            aria-label="Authentication mode"
          >
            {(['login', 'signup'] as const).map(tab => (
              <button
                key={tab}
                role="tab"
                aria-selected={mode === tab}
                onClick={() => { setMode(tab); setError(null); }}
                className="flex-1 py-2 rounded-lg text-sm font-semibold transition-all focus:outline-none focus-visible:ring-2"
                style={{
                  background: mode === tab ? 'var(--saffron)' : 'transparent',
                  color: mode === tab ? 'var(--on-saffron)' : 'var(--text-muted)',
                }}
              >
                {tab === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          {/* Form */}
          <div className="space-y-3">
            {mode === 'signup' && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
                  Display Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Your name"
                    className="w-full pl-10 pr-4 py-3 rounded-xl text-sm focus:outline-none focus-visible:ring-2 transition-all"
                    style={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--card-border)',
                      color: 'var(--text-primary)',
                      caretColor: 'var(--saffron-primary)',
                    }}
                    aria-label="Display name"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm focus:outline-none focus-visible:ring-2 transition-all"
                  style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--text-primary)',
                    caretColor: 'var(--saffron-primary)',
                  }}
                  onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
                  aria-label="Email address"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
                Password {mode === 'signup' && <span style={{ color: 'var(--text-subtle)' }}>(min 8 chars)</span>}
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder={mode === 'signup' ? 'At least 8 characters' : 'Your password'}
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm focus:outline-none focus-visible:ring-2 transition-all"
                  style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--text-primary)',
                    caretColor: 'var(--saffron-primary)',
                  }}
                  onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
                  aria-label="Password"
                />
              </div>
            </div>

            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-2 px-4 py-2.5 rounded-xl text-sm"
                style={{ background: 'rgba(210,69,47,0.08)', border: '1px solid rgba(210,69,47,0.2)', color: 'var(--danger)' }}
                role="alert"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
                {error}
              </motion.div>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={loading || !email.trim() || !password.trim() || (mode === 'signup' && (!name.trim() || password.length < 8))}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all active:scale-[0.99] disabled:opacity-40 focus:outline-none focus-visible:ring-2"
              style={{
                background: 'var(--saffron)',
                color: 'var(--on-saffron)',
                boxShadow: '0 4px 16px var(--saffron-glow)',
              }}
            >
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                : <ArrowRight className="w-4 h-4" aria-hidden="true" />
              }
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: 'var(--card-border)' }} />
            <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>or</span>
            <div className="flex-1 h-px" style={{ background: 'var(--card-border)' }} />
          </div>

          {/* Guest access */}
          <button
            onClick={handleGuest}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all active:scale-[0.99] focus:outline-none focus-visible:ring-2"
            style={{
              background: 'var(--saffron-soft)',
              border: '1px solid rgba(252,108,38,0.25)',
              color: 'var(--saffron-primary)',
            }}
          >
            {t(lang, 'cta_guest')}
          </button>

          {/* Footer quote */}
          <p
            className="font-scripture text-center text-sm italic leading-relaxed pt-1"
            style={{ color: 'var(--text-subtle)' }}
          >
            &ldquo;All power is within you; you can do anything and everything.&rdquo;
          </p>
        </div>

        <p className="text-center text-xs mt-4" style={{ color: 'var(--text-subtle)' }}>
          <Link href="/" className="hover:underline focus:outline-none focus-visible:ring-2 rounded" style={{ color: 'var(--saffron-primary)' }}>
            ← Back to home
          </Link>
        </p>
      </motion.div>

      <FloatingThemeToggle />
    </div>
  );
}
