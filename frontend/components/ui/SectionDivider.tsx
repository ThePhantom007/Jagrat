/** Line–diamond–line divider. No floral motifs. */
export function SectionDivider({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 py-6 ${className}`} aria-hidden="true">
      <div className="flex-1 h-px" style={{ background: 'var(--card-border)' }} />
      <div
        className="w-2 h-2 rotate-45"
        style={{ background: 'var(--saffron)', opacity: 0.6 }}
      />
      <div className="flex-1 h-px" style={{ background: 'var(--card-border)' }} />
    </div>
  );
}
