interface TagChipProps {
  label?: string;
  tag?: string;
  color?: string;
  bg?: string;
  size?: 'sm' | 'md';
}

export function TagChip({ label, tag, color, bg, size = 'md' }: TagChipProps) {
  const displayText = label || (tag ? tag.replace(/_/g, ' ') : '');
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';
  
  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold ${sizeClasses}`}
      style={{
        background: bg ?? 'var(--tag-bg)',
        color: color ?? 'var(--on-saffron)',
        border: `1px solid ${bg ? `${color}33` : 'transparent'}`,
      }}
    >
      {displayText}
    </span>
  );
}
