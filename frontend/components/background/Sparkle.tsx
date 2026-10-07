interface SparkleProps {
  top: string;
  left: string;
  size?: number;
  delay?: number; // seconds
}

/** Small four-point star (not floral). Twinkles slowly; disabled under reduced motion. */
export function Sparkle({top, left, size = 22, delay = 0}: SparkleProps) {
  return (
    <svg
      className="jg-sparkle"
      style={{top, left, width: size, height: size, animationDelay: `${delay}s`}}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M12 0C12 6.6 17.4 12 24 12C17.4 12 12 17.4 12 24C12 17.4 6.6 12 0 12C6.6 12 12 6.6 12 0Z" />
    </svg>
  );
}
