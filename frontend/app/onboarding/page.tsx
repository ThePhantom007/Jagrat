'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { useAppContext } from '@/components/ThemeProvider';
import { FloatingThemeToggle } from '@/components/FloatingThemeToggle';
import { t } from '@/lib/i18n';
import { StepperDots } from '@/components/ui/StepperDots';
import { PillOption } from '@/components/ui/PillOption';
import { GlassCard } from '@/components/ui/GlassCard';
import { SaffronButton } from '@/components/ui/SaffronButton';
import type { UserProfile } from '@/lib/types';

// ─────────────────────────────────────────────────────────────
// 7-Step onboarding per master plan
// ─────────────────────────────────────────────────────────────
interface Option { value: string; emoji: string; label: string; }

const FOCUS_OPTIONS: Option[] = [
  { value: 'inner_strength', emoji: '💪', label: 'Inner strength & resilience' },
  { value: 'discipline', emoji: '⏰', label: 'Consistent discipline' },
  { value: 'clear_goal', emoji: '🎯', label: 'Clear, meaningful goal' },
  { value: 'overcome_fear', emoji: '🦁', label: 'Overcoming fear & hesitation' },
  { value: 'other', emoji: '✨', label: 'Other (Please describe your unique focus)' },
];

const CHALLENGE_OPTIONS: Option[] = [
  { value: 'exam_failure', emoji: '📚', label: 'Exam failure' },
  { value: 'self_doubt', emoji: '🌀', label: 'Self-doubt' },
  { value: 'fear', emoji: '😰', label: 'Fear' },
  { value: 'decision_hesitation', emoji: '⚖️', label: 'Decision hesitation' },
  { value: 'discipline', emoji: '⏰', label: 'Discipline' },
];

const FAILURE_OPTIONS: Option[] = [
  { value: 'overthinking', emoji: '🌊', label: 'Overthinking' },
  { value: 'withdrawal', emoji: '🐚', label: 'Withdrawal' },
  { value: 'quick_reset', emoji: '⚡', label: 'Quick reset' },
];

const GOAL_OPTIONS: Option[] = [
  { value: 'academic_growth', emoji: '🎓', label: 'Academic growth' },
  { value: 'mental_focus', emoji: '🧘', label: 'Mental focus' },
  { value: 'inner_strength', emoji: '🔥', label: 'Inner strength' },
];

const TOTAL_STEPS = 7;

// Verified quotes from the corpus for rotation
const QUOTES = [
  "Arise, awake, and stop not till the goal is reached.",
  "Take up one idea. Make that one idea your life.",
  "The greatest sin is to think yourself weak.",
  "All the powers in the universe are already ours.",
  "You cannot believe in God until you believe in yourself.",
];

// ─────────────────────────────────────────────────────────────
// Slide animation variants
// ─────────────────────────────────────────────────────────────
const slideVariants = {
  enter: (dir: number) => ({ x: dir > 0 ? 40 : -40, opacity: 0 }),
  center: { x: 0, opacity: 1, transition: { duration: 0.25, ease: 'easeOut' as const } },
  exit: (dir: number) => ({ x: dir > 0 ? -40 : 40, opacity: 0, transition: { duration: 0.2 } }),
};

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const { lang } = useAppContext();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState(1);
  const [profile, setProfile] = useState({
    focusArea: null as string | null,
    focusOther: '',
    primaryChallenge: null as string | null,
    failureResponse: null as string | null,
    confidenceLevel: 5,
    primaryGoal: null as string | null,
    language: lang,
    preferredTime: 'evening',
  });

  const goNext = () => { setDirection(1); setStep(s => s + 1); };
  const goPrev = () => { setDirection(-1); setStep(s => s - 1); };

  const canProceed = () => {
    if (step === 1) return profile.focusArea && (profile.focusArea !== 'other' || profile.focusOther.trim());
    if (step === 2) return !!profile.primaryChallenge;
    if (step === 3) return !!profile.failureResponse;
    if (step === 4) return true; // slider always has value
    if (step === 5) return !!profile.primaryGoal;
    if (step === 6) return true; // preferences always valid
    return true; // step 7 review
  };

  const handleFinish = async () => {
    const finalProfile: UserProfile = {
      name: 'Friend',
      focusArea: profile.focusArea === 'other' ? profile.focusOther : profile.focusArea,
      primaryChallenge: profile.primaryChallenge as any,
      failureResponse: profile.failureResponse as any,
      confidenceLevel: profile.confidenceLevel,
      primaryGoal: profile.primaryGoal as any,
      language: lang,
      onboardingComplete: true,
      // These map to backend OnboardingRequest fields
      profession: 'student',
      age: 20,
    };

    try {
      // Always persist locally first so offline mode works
      localStorage.setItem('jagrat_profile', JSON.stringify(finalProfile));

      const { createProfile, saveOnboarding, getProfileId } = await import('@/lib/api');

      // Create a backend profile if we don't already have one
      if (!getProfileId()) {
        await createProfile('Friend');
      }

      // Push all six onboarding dimensions to the backend
      await saveOnboarding(finalProfile);
    } catch (error) {
      console.error('Failed to sync profile to backend:', error);
      // Continue in offline mode — the local profile is saved above
    }

    router.push('/app/chat');
  };

  const currentQuote = QUOTES[Math.min(step - 1, QUOTES.length - 1)];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">

        {/* ── StepperDots ── */}
        <div className="mb-8">
          <StepperDots currentStep={step} totalSteps={TOTAL_STEPS} />
        </div>

        {/* ── "Tap a path below" hint ── */}
        {(step === 1 || step === 2 || step === 3 || step === 5) && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-sm mb-4"
            style={{ color: 'var(--text-muted)' }}
          >
            Tap a path below
          </motion.p>
        )}

        {/* ── Main Card ── */}
        <GlassCard className="p-8 min-h-[400px] flex flex-col">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex flex-col gap-6 flex-1"
            >

              {/* Step 1 — Primary area of focus */}
              {step === 1 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug" style={{ color: 'var(--text-primary)' }}>
                    What is your primary area of focus<br />for personal growth right now?
                  </h2>
                  <div role="radiogroup" className="flex flex-col gap-3">
                    {FOCUS_OPTIONS.slice(0, 4).map(o => (
                      <PillOption
                        key={o.value}
                        emoji={o.emoji}
                        label={o.label}
                        selected={profile.focusArea === o.value}
                        onClick={() => setProfile(p => ({ ...p, focusArea: o.value, focusOther: '' }))}
                      />
                    ))}
                    {/* "Other" with text field */}
                    <PillOption
                      emoji={FOCUS_OPTIONS[4].emoji}
                      label={FOCUS_OPTIONS[4].label}
                      selected={profile.focusArea === 'other'}
                      onClick={() => setProfile(p => ({ ...p, focusArea: 'other' }))}
                    />
                    {profile.focusArea === 'other' && (
                      <motion.input
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        type="text"
                        value={profile.focusOther}
                        onChange={e => setProfile(p => ({ ...p, focusOther: e.target.value }))}
                        placeholder="Describe your unique focus..."
                        className="w-full px-5 py-3 rounded-xl text-sm focus:outline-none focus-visible:ring-2 transition-all"
                        style={{
                          background: 'var(--input-surface)',
                          border: '1px solid var(--card-border)',
                          color: 'var(--text-primary)',
                        }}
                        autoFocus
                      />
                    )}
                  </div>
                </>
              )}

              {/* Step 2 — Biggest challenge */}
              {step === 2 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug" style={{ color: 'var(--text-primary)' }}>
                    What is your biggest challenge?
                  </h2>
                  <div role="radiogroup" className="flex flex-col gap-3">
                    {CHALLENGE_OPTIONS.map(o => (
                      <PillOption
                        key={o.value}
                        emoji={o.emoji}
                        label={o.label}
                        selected={profile.primaryChallenge === o.value}
                        onClick={() => setProfile(p => ({ ...p, primaryChallenge: o.value }))}
                      />
                    ))}
                  </div>
                </>
              )}

              {/* Step 3 — Failure response */}
              {step === 3 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug" style={{ color: 'var(--text-primary)' }}>
                    How do you respond to failure?
                  </h2>
                  <div role="radiogroup" className="flex flex-col gap-3">
                    {FAILURE_OPTIONS.map(o => (
                      <PillOption
                        key={o.value}
                        emoji={o.emoji}
                        label={o.label}
                        selected={profile.failureResponse === o.value}
                        onClick={() => setProfile(p => ({ ...p, failureResponse: o.value }))}
                      />
                    ))}
                  </div>
                </>
              )}

              {/* Step 4 — Current confidence (1-10 slider) */}
              {step === 4 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug" style={{ color: 'var(--text-primary)' }}>
                    Current confidence
                  </h2>
                  <div className="flex flex-col items-center gap-6 py-8">
                    <div
                      className="w-28 h-28 rounded-full flex items-center justify-center text-5xl font-bold border-4 transition-all"
                      style={{
                        borderColor: 'var(--saffron)',
                        background: 'var(--saffron-soft)',
                        color: 'var(--saffron)',
                        boxShadow: '0 0 24px var(--saffron-glow)',
                      }}
                      aria-live="polite"
                      aria-atomic="true"
                    >
                      {profile.confidenceLevel}
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={profile.confidenceLevel}
                      onChange={e => setProfile(p => ({ ...p, confidenceLevel: Number(e.target.value) }))}
                      className="w-full h-3 rounded-full appearance-none cursor-pointer focus:outline-none focus-visible:ring-2"
                      style={{
                        background: `linear-gradient(to right, var(--saffron) 0%, var(--saffron) ${(profile.confidenceLevel - 1) * 11.11}%, var(--card-border) ${(profile.confidenceLevel - 1) * 11.11}%, var(--card-border) 100%)`,
                      }}
                      aria-label="Confidence level slider 1 to 10"
                    />
                    <div className="flex justify-between w-full text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                      <span>1 — Very Low</span>
                      <span>10 — Very High</span>
                    </div>
                  </div>
                </>
              )}

              {/* Step 5 — Primary goal */}
              {step === 5 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug" style={{ color: 'var(--text-primary)' }}>
                    Primary goal
                  </h2>
                  <div role="radiogroup" className="flex flex-col gap-3">
                    {GOAL_OPTIONS.map(o => (
                      <PillOption
                        key={o.value}
                        emoji={o.emoji}
                        label={o.label}
                        selected={profile.primaryGoal === o.value}
                        onClick={() => setProfile(p => ({ ...p, primaryGoal: o.value }))}
                      />
                    ))}
                  </div>
                </>
              )}

              {/* Step 6 — Preferences (language + reflection time) */}
              {step === 6 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug mb-2" style={{ color: 'var(--text-primary)' }}>
                    Preferences
                  </h2>
                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
                        Preferred language
                      </label>
                      <select
                        value={profile.language}
                        onChange={e => setProfile(p => ({ ...p, language: e.target.value as any }))}
                        className="w-full px-4 py-3 rounded-xl text-base focus:outline-none focus-visible:ring-2 transition-all"
                        style={{
                          background: 'var(--input-surface)',
                          border: '1px solid var(--card-border)',
                          color: 'var(--text-primary)',
                        }}
                      >
                        <option value="en">English</option>
                        <option value="hi">हिन्दी (Hindi)</option>
                        <option value="bn">বাংলা (Bengali)</option>
                        <option value="mr">मराठी (Marathi)</option>
                        <option value="ta">தமிழ் (Tamil)</option>
                        <option value="te">తెలుగు (Telugu)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
                        Preferred reflection time
                      </label>
                      <select
                        value={profile.preferredTime}
                        onChange={e => setProfile(p => ({ ...p, preferredTime: e.target.value }))}
                        className="w-full px-4 py-3 rounded-xl text-base focus:outline-none focus-visible:ring-2 transition-all"
                        style={{
                          background: 'var(--input-surface)',
                          border: '1px solid var(--card-border)',
                          color: 'var(--text-primary)',
                        }}
                      >
                        <option value="morning">Morning</option>
                        <option value="afternoon">Afternoon</option>
                        <option value="evening">Evening</option>
                        <option value="night">Night</option>
                      </select>
                    </div>
                  </div>
                </>
              )}

              {/* Step 7 — Review and begin */}
              {step === 7 && (
                <>
                  <h2 className="text-2xl font-bold text-center leading-snug mb-4" style={{ color: 'var(--text-primary)' }}>
                    Review and begin
                  </h2>
                  <div className="space-y-3 text-sm" style={{ color: 'var(--text-muted)' }}>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Focus:</strong> {profile.focusArea === 'other' ? profile.focusOther : FOCUS_OPTIONS.find(o => o.value === profile.focusArea)?.label}</p>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Challenge:</strong> {CHALLENGE_OPTIONS.find(o => o.value === profile.primaryChallenge)?.label}</p>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Failure response:</strong> {FAILURE_OPTIONS.find(o => o.value === profile.failureResponse)?.label}</p>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Confidence:</strong> {profile.confidenceLevel}/10</p>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Goal:</strong> {GOAL_OPTIONS.find(o => o.value === profile.primaryGoal)?.label}</p>
                    <p><strong style={{ color: 'var(--text-primary)' }}>Language:</strong> {profile.language.toUpperCase()}</p>
                  </div>
                  <div className="mt-6 pt-6 border-t" style={{ borderColor: 'var(--card-border)' }}>
                    <SaffronButton onClick={handleFinish} className="w-full text-lg font-bold py-4">
                      ⚡ Start my journey
                    </SaffronButton>
                  </div>
                </>
              )}

            </motion.div>
          </AnimatePresence>
        </GlassCard>

        {/* ── Quote beneath card ── */}
        {step < 7 && (
          <motion.blockquote
            key={currentQuote}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center mt-6 font-scripture text-base italic leading-relaxed"
            style={{ color: 'var(--text-primary)' }}
          >
            &ldquo;{currentQuote}&rdquo;
          </motion.blockquote>
        )}

        {/* ── Navigation Buttons (only show if not on step 7) ── */}
        {step < 7 && (
          <div className="flex items-center justify-between mt-8 gap-4">
            <button
              onClick={goPrev}
              disabled={step === 1}
              className="flex items-center gap-1.5 px-5 py-3 rounded-full text-sm font-semibold transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
              style={{
                background: 'var(--card-surface)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-muted)',
                boxShadow: 'var(--card-shadow)',
              }}
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
              Back
            </button>

            <button
              onClick={goNext}
              disabled={!canProceed()}
              className="flex items-center gap-1.5 px-6 py-3 rounded-full text-base font-bold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
              style={{
                background: canProceed() ? 'var(--saffron)' : 'var(--pill-surface)',
                color: canProceed() ? 'var(--on-saffron)' : 'var(--text-muted)',
                boxShadow: canProceed() ? '0 4px 16px var(--saffron-glow)' : 'var(--card-shadow)',
              }}
            >
              Next
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}

      </div>

      {/* ── Floating Theme Toggle ── */}
      <FloatingThemeToggle />
    </div>
  );
}
