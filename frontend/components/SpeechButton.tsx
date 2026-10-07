'use client';

import { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';

interface SpeechButtonProps {
  text: string;
  lang?: Language;
  /** Optional language code for SpeechSynthesis (e.g. 'hi-IN', 'en-IN') */
  speechLang?: string;
}

const SPEECH_LANG_MAP: Record<Language, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  bn: 'bn-IN',
  mr: 'mr-IN',
  ta: 'ta-IN',
  te: 'te-IN',
};

export function SpeechButton({ text, lang = 'en', speechLang }: SpeechButtonProps) {
  const [speaking, setSpeaking] = useState(false);
  const [supported, setSupported] = useState(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setSupported(false);
    }
    // Cancel speech on unmount
    return () => {
      if (utteranceRef.current) {
        window.speechSynthesis?.cancel();
      }
    };
  }, []);

  if (!supported) return null;

  const toggleSpeech = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;      // Calm, deliberate pace
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = speechLang ?? SPEECH_LANG_MAP[lang];

    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
  };

  return (
    <button
      onClick={toggleSpeech}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 active:scale-95"
      style={{
        background: speaking ? 'var(--saffron)' : 'var(--gold-soft)',
        color: speaking ? 'var(--on-saffron)' : 'var(--gold-accent)',
        border: '1px solid',
        borderColor: speaking ? 'var(--saffron)' : 'rgba(245,158,11,0.3)',
      }}
      aria-label={speaking ? t(lang, 'stop_btn') : t(lang, 'listen_btn')}
      aria-pressed={speaking}
    >
      {speaking
        ? <VolumeX className="w-3.5 h-3.5" aria-hidden="true" />
        : <Volume2 className="w-3.5 h-3.5" aria-hidden="true" />
      }
      <span>{speaking ? t(lang, 'stop_btn') : t(lang, 'listen_btn')}</span>
    </button>
  );
}
