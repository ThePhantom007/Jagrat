'use client';

interface StepperDotsProps {
  currentStep: number;
  totalSteps: number;
}

/**
 * StepperDots — Numbered circular nodes for onboarding
 * Completed = soft saffron, Current = solid saffron with glow, Future = muted
 * Label "Step X of Y" above
 */
export function StepperDots({ currentStep, totalSteps }: StepperDotsProps) {
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Step indicator text */}
      <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
        Step {currentStep} of {totalSteps} onboarding
      </p>

      {/* Dots */}
      <div className="flex items-center gap-2">
        {Array.from({ length: totalSteps }, (_, i) => {
          const step = i + 1;
          const isCompleted = step < currentStep;
          const isCurrent = step === currentStep;
          const isFuture = step > currentStep;

          return (
            <div
              key={step}
              className="flex items-center gap-2"
            >
              {/* Circular node */}
              <div
                className="flex items-center justify-center rounded-full transition-all duration-300 relative"
                style={{
                  width: isCurrent ? '44px' : '36px',
                  height: isCurrent ? '44px' : '36px',
                  background: isCurrent
                    ? 'var(--saffron)'
                    : isCompleted
                    ? 'var(--saffron-soft)'
                    : 'var(--card-surface)',
                  border: isCurrent
                    ? '2px solid var(--saffron)'
                    : isCompleted
                    ? '2px solid var(--saffron)'
                    : '2px solid var(--card-border)',
                  boxShadow: isCurrent ? '0 0 0 4px var(--saffron-glow)' : 'none',
                  color: isCurrent || isCompleted ? 'var(--on-saffron)' : 'var(--text-muted)',
                  fontSize: isCurrent ? '16px' : '14px',
                  fontWeight: isCurrent ? '700' : '600',
                }}
                aria-label={`Step ${step}${isCurrent ? ' (current)' : isCompleted ? ' (completed)' : ''}`}
              >
                {step}
              </div>

              {/* Connecting line (except after last) */}
              {step < totalSteps && (
                <div
                  className="h-0.5 transition-all duration-300"
                  style={{
                    width: '20px',
                    background: isCompleted ? 'var(--saffron)' : 'var(--card-border)',
                  }}
                  aria-hidden="true"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
