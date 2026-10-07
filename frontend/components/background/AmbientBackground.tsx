import {OmWatermark} from "./OmWatermark";
import {SunBurst} from "./SunBurst";
import {Sparkle} from "./Sparkle";

/**
 * Mount ONCE in app/layout.tsx, as the first child of <body>.
 * Layers: gradient (on body) > translucent Om (centre) > suns (corners) > sparkles.
 * No floral, lotus or mandala shapes. Do not add any.
 */
export function AmbientBackground() {
  return (
    <div className="jg-ambient" aria-hidden="true">
      <OmWatermark />
      <SunBurst corner="tl" size="clamp(300px, 40vw, 640px)" />
      <SunBurst corner="tr" size="clamp(220px, 26vw, 420px)" rays={32} />
      <SunBurst corner="bl" size="clamp(220px, 26vw, 420px)" rays={32} desktopOnly />
      <SunBurst corner="br" size="clamp(300px, 40vw, 640px)" desktopOnly />
      <Sparkle top="22%" left="17%" size={26} />
      <Sparkle top="30%" left="85%" size={20} delay={1.2} />
      <Sparkle top="78%" left="6%" size={22} delay={2.4} />
      <Sparkle top="88%" left="74%" size={24} delay={0.6} />
      <Sparkle top="12%" left="52%" size={14} delay={1.8} />
    </div>
  );
}
