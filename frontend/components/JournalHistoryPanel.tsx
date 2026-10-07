'use client';

import { Brain } from 'lucide-react';
import { TagChip } from './ui/TagChip';
import type { JournalEntry, EmotionTag } from '@/lib/types';

interface JournalHistoryPanelProps {
  entries: JournalEntry[];
  onSelectEntry: (entry: JournalEntry) => void;
}

/** Safe tags accessor — handles both old extractedTags and new tags field */
function getTags(entry: JournalEntry): EmotionTag[] {
  return entry.tags ?? entry.extractedTags ?? [];
}

/** Safe content */
function getText(entry: JournalEntry): string {
  return entry.text ?? entry.content ?? '';
}

function formatDate(timestamp: number | string): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp);
  const month = date.toLocaleDateString('en-US', { month: 'short' });
  const day = date.getDate();
  return `${month} ${day}`;
}

/**
 * JournalHistoryPanel — Right sidebar showing past entries
 * Shows date, first line truncated, tag chips, brain icon
 * On mobile: becomes a bottom sheet
 */
export function JournalHistoryPanel({ entries, onSelectEntry }: JournalHistoryPanelProps) {
  if (entries.length === 0) {
    return (
      <div
        className="rounded-2xl p-6 text-center"
        style={{
          background: 'var(--card-surface)',
          border: '1px solid var(--card-border)',
          boxShadow: 'var(--card-shadow)',
        }}
      >
        <Brain className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Your past entries will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {entries.map((entry) => {
        const firstLine = getText(entry).split('\n')[0].trim();
        const truncated = firstLine.length > 40 ? firstLine.slice(0, 40) + '…' : firstLine;
        const entryTags = getTags(entry);
        const date = entry.date || entry.timestamp || Date.now();

        return (
          <button
            key={entry.id}
            onClick={() => onSelectEntry(entry)}
            className="w-full text-left p-4 rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
            style={{
              background: 'var(--card-surface)',
              border: '1px solid var(--card-border)',
              boxShadow: 'var(--card-shadow)',
            }}
          >
            <div className="flex items-start gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
                  {formatDate(date)}
                </p>
                <p className="text-sm leading-snug truncate" style={{ color: 'var(--text-primary)' }}>
                  {truncated || 'Untitled entry'}
                </p>
              </div>
              <Brain className="w-4 h-4 shrink-0 mt-0.5" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
            </div>

            {entryTags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {entryTags.slice(0, 2).map(tag => (
                  <TagChip key={tag} tag={tag} size="sm" />
                ))}
                {entryTags.length > 2 && (
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--pill-surface)', color: 'var(--text-muted)' }}>
                    +{entryTags.length - 2}
                  </span>
                )}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
