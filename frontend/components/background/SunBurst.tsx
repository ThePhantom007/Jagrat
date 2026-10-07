type Corner = "tl" | "tr" | "bl" | "br";

interface SunBurstProps {
  corner: Corner;
  /** Rendered diameter. Any CSS length, e.g. "clamp(280px, 38vw, 620px)". */
  size: string;
  /** Number of rays. Default 40. */
  rays?: number;
  /** Hide on small screens (used for the lower two suns). */
  desktopOnly?: boolean;
}

const f = (n: number) => n.toFixed(2); // fixed precision keeps server/client markup identical

/** Corner sun: a pale disc with rounded rays, centred on (and cropped by) the screen corner. */
export function SunBurst({corner, size, rays = 40, desktopOnly = false}: SunBurstProps) {
  const lines = Array.from({length: rays}, (_, i) => {
    const a = ((i + 0.5) / rays) * Math.PI * 2; // half-step offset: no ray lies along the screen edge
    const inner = 128;
    const len = i % 2 === 0 ? 80 : 48; // alternating long/short rays
    const outer = inner + len;
    return (
      <line
        key={i}
        x1={f(Math.cos(a) * inner)}
        y1={f(Math.sin(a) * inner)}
        x2={f(Math.cos(a) * outer)}
        y2={f(Math.sin(a) * outer)}
      />
    );
  });

  return (
    <svg
      className={`jg-sun jg-sun-${corner}${desktopOnly ? " jg-desktop-only" : ""}`}
      style={{width: size, height: size}}
      viewBox="-220 -220 440 440"
      aria-hidden="true"
      focusable="false"
    >
      <circle className="jg-sun-disc" r="100" />
      <g className="jg-sun-rays">{lines}</g>
    </svg>
  );
}
