'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Save, Trash2, Tag } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';
import type { EmotionTag } from '@/lib/types';

// ── Keyword → Tag mapping ──────────────────────────────────
const TAG_KEYWORDS: Record<EmotionTag, string[]> = {
  self_doubt:        ['doubt', 'not good enough', 'stupid', 'dumb', 'worthless', 'useless', 'failure', 'inadequate', 'योग्य नहीं', 'संदेह'],
  academic_pressure: ['exam', 'marks', 'grade', 'study', 'syllabus', 'assignment', 'test', 'board', 'score', 'rank', 'परीक्षा'],
  peer_comparison:   ['friends', 'others', 'classmate', 'compare', 'better than me', 'everyone else', 'they are', 'peers'],
  fear_of_failure:   ['afraid', 'scared', 'fear', 'fail', 'failing', 'terror', 'nightmare', 'डर', 'भय'],
  motivation:        ['inspire', 'motivat', 'goal', 'dream', 'want to', 'going to', 'will do', 'determined', 'लक्ष्य'],
  gratitude:         ['grateful', 'thankful', 'blessed', 'appreciate', 'thank', 'धन्यवाद', 'आभार'],
  confusion:         ['confused', 'unsure', "don't know", 'lost', 'unclear', 'what to do', 'directionless'],
  resilience:        ['bounce back', 'keep going', 'try again', 'won\'t give up', 'persist', 'strong', 'resilient', 'हिम्मत'],
  anxiety:           ['anxious', 'anxiety', 'panic', 'nervous', 'worry', 'overthink', 'stress', 'restless', 'घबराहट'],
  hope:              ['hope', 'hopeful', 'optimistic', 'better tomorrow', 'believe', 'someday', 'will be okay', 'उम्मीद'],
};

const TAG_COLORS: Record<EmotionTag, { bg: string; text: string; border: string }> = {
  self_doubt:        { bg: 'rgba(239,68,68,0.08)',   text: '#EF4444', border: 'rgba(239,68,68,0.25)'   },
  academic_pressure: { bg: 'rgba(59,130,246,0.08)',  text: '#3B82F6', border: 'rgba(59,130,246,0.25)'  },
  peer_comparison:   { bg: 'rgba(168,85,247,0.08)',  text: '#A855F7', border: 'rgba(168,85,247,0.25)'  },
  fear_of_failure:   { bg: 'rgba(249,115,22,0.08)',  text: '#F97316', border: 'rgba(249,115,22,0.25)'  },
  motivation:        { bg: 'rgba(34,197,94,0.08)',   text: '#22C55E', border: 'rgba(34,197,94,0.25)'   },
  gratitude:         { bg: 'rgba(245,158,11,0.10)',  text: '#F59E0B', border: 'rgba(245,158,11,0.25)'  },
  confusion:         { bg: 'rgba(100,116,139,0.08)', text: '#64748B', border: 'rgba(100,116,139,0.25)' },
  resilience:        { bg: 'rgba(20,184,166,0.08)',  text: '#14B8A6', border: 'rgba(20,184,166,0.25)'  },
  anxiety:           { bg: 'rgba(236,72,153,0.08)',  text: '#EC4899', border: 'rgba(236,72,153,0.25)'  },
  hope:              { bg: 'rgba(252,108,38,0.10)',  text: '#FC6C26', border: 'rgba(252,108,38,0.25)'  },
};

const TAG_LABELS: Record<EmotionTag, string> = {
  self_doubt:        'self_doubt',
  academic_pressure: 'academic_pressure',
  peer_comparison:   'peer_comparison',
  fear_of_failure:   'fear_of_failure',
  motivation:        'motivation',
  gratitude:         'gratitude',
  confusion:         'confusion',
  resilience:        'resilience',
  anxiety:           'anxiety',
  hope:              'hope',
};

function extractTags(text: string): EmotionTag[] {
  const lower = text.toLowerCase();
  const found: EmotionTag[] = [];
  for (const [tag, keywords] of Object.entries(TAG_KEYWORDS) as [EmotionTag, string[]][]) {
    if (keywords.some(kw => lower.includes(kw))) {
      found.push(tag);
    }
  }
  return found;
}

interface JournalEditorProps {
  lang?: Language;
  onSave?: (content: string, tags: EmotionTag[]) => void;
  initialContent?: string;
  disabled?: boolean;
}

export function JournalEditor({ lang = 'en', onSave, initialContent = '', disabled = false }: JournalEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [tags, setTags] = useState<EmotionTag[]>([]);
  const [saved, setSaved] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  // Update content when initialContent changes
  useEffect(() => {
    setContent(initialContent);
    setTags(extractTags(initialContent));
  }, [initialContent]);

  // Debounced live tag extraction
  const handleChange = useCallback((value: string) => {
    setContent(value);
    setSaved(false);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setTags(extractTags(value));
    }, 400);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const handleSave = () => {
    if (!content.trim()) return;
    onSave?.(content.trim(), tags);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleClear = () => {
    setContent('');
    setTags([]);
    setSaved(false);
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* ── Textarea ── */}
      <div
        className="relative rounded-2xl overflow-hidden transition-all"
        style={{
          border: '1px solid var(--card-border)',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        <textarea
          value={content}
          onChange={e => handleChange(e.target.value)}
          placeholder={t(lang, 'journal_placeholder')}
          rows={12}
          className="w-full resize-none px-6 py-5 text-base leading-relaxed focus:outline-none transition-colors"
          style={{
            background: 'var(--input-surface)',
            color: 'var(--text-primary)',
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            caretColor: 'var(--saffron)',
          }}
          aria-label="Journal entry text area"
          aria-describedby="journal-tag-preview"
          data-gramm="false"
          data-gramm_editor="false"
          data-enable-grammarly="false"
        />

        {/* Word count overlay */}
        <div
          className="absolute bottom-3 right-4 text-xs pointer-events-none"
          style={{ color: 'var(--text-subtle)' }}
          aria-live="polite"
          aria-atomic="true"
        >
          {t(lang, 'journal_word_count').replace('{count}', String(wordCount))}
        </div>
      </div>

      {/* ── Live Tag Pills ── */}
      <AnimatePresence>
        {tags.length > 0 && (
          <motion.div
            id="journal-tag-preview"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="flex flex-wrap items-center gap-2"
            aria-label={t(lang, 'journal_tags_label')}
          >
            <div className="flex items-center gap-1.5 mr-1">
              <Tag className="w-3.5 h-3.5" style={{ color: 'var(--text-subtle)' }} aria-hidden="true" />
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-subtle)' }}>
                {t(lang, 'journal_tags_label')}
              </span>
            </div>
            {tags.map(tag => {
              const colors = TAG_COLORS[tag];
              return (
                <motion.span
                  key={tag}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.85 }}
                  transition={{ duration: 0.2 }}
                  className="px-2.5 py-1 rounded-full text-xs font-semibold"
                  style={{
                    background: colors.bg,
                    color: colors.text,
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  [ {TAG_LABELS[tag]} ]
                </motion.span>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Actions ── */}
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={handleClear}
          disabled={!content}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
          style={{
            background: 'var(--slate-soft)',
            color: 'var(--text-muted)',
            border: '1px solid var(--card-border)',
          }}
          aria-label={t(lang, 'journal_clear')}
        >
          <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
          {t(lang, 'journal_clear')}
        </button>

        <div className="flex items-center gap-2">
          <AnimatePresence>
            {saved && (
              <motion.span
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                className="text-xs font-medium"
                style={{ color: 'var(--success)' }}
                role="status"
                aria-live="polite"
              >
                ✓ {t(lang, 'journal_saved')}
              </motion.span>
            )}
          </AnimatePresence>
          <button
            onClick={handleSave}
            disabled={!content.trim() || disabled}
            className="flex items-center gap-1.5 px-6 py-3 rounded-full text-base font-bold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
            style={{
              background: (content.trim() && !disabled) ? 'var(--saffron)' : 'var(--pill-surface)',
              color: (content.trim() && !disabled) ? 'var(--on-saffron)' : 'var(--text-muted)',
              boxShadow: (content.trim() && !disabled) ? '0 4px 16px var(--saffron-glow)' : 'none',
            }}
            aria-label={t(lang, 'journal_save')}
          >
            <Save className="w-4 h-4" aria-hidden="true" />
            {disabled ? 'Saving...' : t(lang, 'journal_save')}
          </button>
        </div>
      </div>
    </div>
  );
}
