'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, BookOpen, CheckCircle2, Bookmark, BookmarkCheck, Loader2 } from 'lucide-react';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { SpeechButton } from '@/components/SpeechButton';
import { getTeachings, saveTeaching, unsaveTeaching, type BackendTeachingListItem } from '@/lib/api';

function TeachingCard({ t, saved, onSaveToggle }: {
  t: BackendTeachingListItem;
  saved: boolean;
  onSaveToggle: (id: string, saved: boolean) => void;
}) {
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      if (saved) { await unsaveTeaching(t.id); onSaveToggle(t.id, false); }
      else { await saveTeaching(t.id); onSaveToggle(t.id, true); }
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-5"
      style={{ background: 'rgba(120,53,15,0.08)', border: '1px solid rgba(245,158,11,0.25)' }}
    >
      {/* Quote */}
      <blockquote className="font-scripture text-base leading-relaxed relative pl-4 mb-4"
        style={{ color: 'var(--text-primary)', borderLeft: '3px solid var(--gold-accent)' }}>
        {t.quote.length > 400 ? t.quote.slice(0, 400) + '…' : t.quote}
      </blockquote>

      {/* Source */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          <CheckCircle2 className="w-3.5 h-3.5" style={{ color: 'var(--success)' }} aria-hidden="true" />
          <span className="text-xs font-semibold" style={{ color: 'var(--success)' }}>Verified</span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            · {t.source.title}
            {t.source.volume ? `, ${t.source.volume}` : ''}
            {t.source.page ? `, p. ${t.source.page}` : ''}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <SpeechButton text={t.quote} />
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all focus:outline-none focus-visible:ring-2 active:scale-95"
            style={{
              background: saved ? 'var(--gold-soft)' : 'var(--card-surface)',
              color: saved ? 'var(--gold-accent)' : 'var(--text-muted)',
              border: `1px solid ${saved ? 'rgba(245,158,11,0.3)' : 'var(--card-border)'}`,
            }}
            aria-label={saved ? 'Unsave teaching' : 'Save teaching'}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
              saved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </div>

      {/* Themes */}
      {t.themes.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {t.themes.slice(0, 5).map(th => (
            <span key={th} className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)' }}>
              {th}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

export default function TeachingsPage() {
  const [teachings, setTeachings] = useState<BackendTeachingListItem[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 450);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setLoading(true);
    getTeachings(debouncedSearch || undefined).then(data => {
      setTeachings(data);
      setLoading(false);
    });
  }, [debouncedSearch]);

  const handleSaveToggle = (id: string, nowSaved: boolean) => {
    setSavedIds(prev => {
      const next = new Set(prev);
      nowSaved ? next.add(id) : next.delete(id);
      return next;
    });
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-4"
          style={{ background: 'rgba(120,53,15,0.10)', color: 'var(--gold-accent)', border: '1px solid rgba(245,158,11,0.25)' }}>
          <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
          Source-Verified Library
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          Teachings of Vivekananda
        </h1>
        <p className="text-sm leading-relaxed max-w-xl mx-auto mb-4" style={{ color: 'var(--text-muted)' }}>
          Every quote is drawn from verified sources — Complete Works, letters, and authenticated publications.
          No paraphrasing, no fabrications.
        </p>
        <SectionDivider />
      </motion.div>

      {/* Search */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mb-6">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by theme, keyword, or phrase…"
            className="w-full pl-9 pr-4 py-3 rounded-xl text-sm focus:outline-none focus-visible:ring-2"
            style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}
            aria-label="Search teachings"
          />
        </div>
        {!loading && (
          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
            {teachings.length} teaching{teachings.length !== 1 ? 's' : ''} {debouncedSearch ? `matching "${debouncedSearch}"` : 'in the library'}
          </p>
        )}
      </motion.div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-7 h-7 animate-spin" style={{ color: 'var(--saffron)' }} />
        </div>
      ) : teachings.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {debouncedSearch ? `No teachings found for "${debouncedSearch}". Try a different term.` : 'No teachings available yet.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {teachings.map((t, i) => (
            <motion.div key={t.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
              <TeachingCard t={t} saved={savedIds.has(t.id)} onSaveToggle={handleSaveToggle} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
