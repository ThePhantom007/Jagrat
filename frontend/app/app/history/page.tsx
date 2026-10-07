'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Loader2, BookOpen, MessageCircle, Zap, BarChart2, FileText, Bookmark, Star } from 'lucide-react';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { GlassCard } from '@/components/ui/GlassCard';
import { getHistory, type BackendHistoryItem } from '@/lib/api';

const TYPE_META: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  journal:              { label: 'Journal',        icon: <FileText className="w-4 h-4" />,       color: 'var(--slate-accent)',  bg: 'rgba(100,116,139,0.10)' },
  mentor:               { label: 'Reflection',     icon: <MessageCircle className="w-4 h-4" />,  color: 'var(--saffron)',       bg: 'var(--saffron-soft)' },
  action:               { label: 'Action',         icon: <Zap className="w-4 h-4" />,            color: 'var(--success)',       bg: 'rgba(63,125,78,0.08)' },
  vivekananda_vs_me:    { label: 'Vs Me',          icon: <BookOpen className="w-4 h-4" />,       color: 'var(--gold-accent)',   bg: 'rgba(120,53,15,0.08)' },
  growth_checkin:       { label: 'Check-in',       icon: <BarChart2 className="w-4 h-4" />,      color: 'var(--saffron)',       bg: 'var(--saffron-soft)' },
  weekly_report:        { label: 'Weekly Report',  icon: <BarChart2 className="w-4 h-4" />,      color: 'var(--gold-accent)',   bg: 'rgba(120,53,15,0.08)' },
  saved_teaching:       { label: 'Saved Teaching', icon: <Bookmark className="w-4 h-4" />,       color: 'var(--gold-accent)',   bg: 'rgba(120,53,15,0.08)' },
  feedback:             { label: 'Feedback',       icon: <Star className="w-4 h-4" />,           color: 'var(--slate-accent)',  bg: 'rgba(100,116,139,0.10)' },
};

const FILTER_TYPES = [
  { value: '',                  label: 'All' },
  { value: 'journal',           label: 'Journal' },
  { value: 'mentor',            label: 'Reflections' },
  { value: 'action',            label: 'Actions' },
  { value: 'vivekananda_vs_me', label: 'Vs Me' },
  { value: 'growth_checkin',    label: 'Check-ins' },
  { value: 'saved_teaching',    label: 'Saved' },
];

function HistoryCard({ item }: { item: BackendHistoryItem }) {
  const meta = TYPE_META[item.type] ?? { label: item.type, icon: <FileText className="w-4 h-4" />, color: 'var(--text-muted)', bg: 'var(--card-surface)' };
  const date = new Date(item.created_at);
  const [expanded, setExpanded] = useState(false);

  // Build tags from data
  const themes: string[] = (item.data.themes as string[]) ?? [];
  const emotions: string[] = (item.data.emotions as string[]) ?? [];

  return (
    <GlassCard className="p-4">
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mt-0.5"
          style={{ background: meta.bg, color: meta.color }}>
          {meta.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: meta.color }}>
              {meta.label}
            </span>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            </span>
          </div>
          <p className="text-sm leading-relaxed mt-1 line-clamp-2" style={{ color: 'var(--text-primary)' }}>
            {item.summary}
          </p>

          {/* Emotion/theme chips */}
          {(themes.length > 0 || emotions.length > 0) && (
            <div className="flex flex-wrap gap-1 mt-2">
              {themes.slice(0, 3).map(t => (
                <span key={t} className="text-xs px-2 py-0.5 rounded-full"
                  style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)' }}>
                  {t}
                </span>
              ))}
              {emotions.slice(0, 3).map(e => (
                <span key={e} className="text-xs px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(100,116,139,0.10)', color: 'var(--slate-accent)' }}>
                  {e}
                </span>
              ))}
            </div>
          )}

          {/* Special data for check-ins */}
          {item.type === 'growth_checkin' && (
            <div className="flex gap-3 mt-2 text-xs flex-wrap" style={{ color: 'var(--text-muted)' }}>
              {(['self_belief','fear','discipline','clarity','resilience'] as const).map(k => (
                <span key={k}>
                  <span className="capitalize">{k.replace('_',' ')}</span>: <strong style={{ color: 'var(--text-primary)' }}>{(item.data as any)[k]}/10</strong>
                </span>
              ))}
            </div>
          )}

          {/* Expand full text for journal/mentor */}
          {(item.type === 'journal' || item.type === 'mentor') && item.summary.length >= 279 && (
            <button onClick={() => setExpanded(v => !v)}
              className="text-xs mt-1 focus:outline-none focus-visible:ring-2" style={{ color: 'var(--saffron)' }}>
              {expanded ? 'Show less' : 'Read more'}
            </button>
          )}
          {expanded && (
            <p className="text-sm leading-relaxed mt-2" style={{ color: 'var(--text-primary)' }}>
              {(item.data.text as string) || (item.data.current_problem as string) || item.summary}
            </p>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

export default function HistoryPage() {
  const [items, setItems] = useState<BackendHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setLoading(true);
    getHistory({ limit: 100, item_type: typeFilter || undefined, q: debouncedSearch || undefined })
      .then(data => { setItems(data); setLoading(false); });
  }, [typeFilter, debouncedSearch]);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
          Your History
        </h1>
        <p className="text-sm text-center mb-4" style={{ color: 'var(--text-muted)' }}>
          Everything you have reflected on, journaled, and acted upon.
        </p>
        <SectionDivider />
      </motion.div>

      {/* Search + type filter */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="space-y-3 mb-5">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search your history…"
            className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm focus:outline-none focus-visible:ring-2"
            style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}
            aria-label="Search history" />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {FILTER_TYPES.map(f => (
            <button key={f.value} onClick={() => setTypeFilter(f.value)}
              className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all focus:outline-none focus-visible:ring-2"
              style={{
                background: typeFilter === f.value ? 'var(--saffron)' : 'var(--card-surface)',
                color: typeFilter === f.value ? 'var(--on-saffron)' : 'var(--text-muted)',
                border: `1px solid ${typeFilter === f.value ? 'var(--saffron)' : 'var(--card-border)'}`,
              }}>
              {f.label}
            </button>
          ))}
        </div>
      </motion.div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-7 h-7 animate-spin" style={{ color: 'var(--saffron)' }} />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Nothing found. Start reflecting to build your history.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item, i) => (
            <motion.div key={item.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
              <HistoryCard item={item} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
