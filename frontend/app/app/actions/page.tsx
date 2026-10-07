'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Clock, Loader2, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { GlassCard } from '@/components/ui/GlassCard';
import { getActions, completeAction, followUpAction, type BackendActionItem } from '@/lib/api';

type Outcome = 'completed' | 'partially_completed' | 'not_completed';

const OUTCOME_LABELS: Record<Outcome, string> = {
  completed: '✅ Completed',
  partially_completed: '🔶 Partially done',
  not_completed: '❌ Not completed',
};

const OUTCOME_COLORS: Record<Outcome, string> = {
  completed: 'var(--success)',
  partially_completed: 'var(--gold-accent)',
  not_completed: 'var(--danger)',
};

function ActionCard({ item, onUpdate }: { item: BackendActionItem; onUpdate: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [selectedOutcome, setSelectedOutcome] = useState<Outcome | null>(
    (item.follow_up_outcome as Outcome) ?? null
  );
  const [note, setNote] = useState(item.follow_up_note ?? '');
  const [saving, setSaving] = useState(false);

  const isCompleted = item.completed;

  const handleComplete = async () => {
    setSaving(true);
    try { await completeAction(item.id); onUpdate(); }
    catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const handleFollowUp = async () => {
    if (!selectedOutcome) return;
    setSaving(true);
    try { await followUpAction(item.id, selectedOutcome, note); onUpdate(); }
    catch { /* ignore */ }
    finally { setSaving(false); }
  };

  return (
    <GlassCard className="p-4">
      <div className="flex items-start gap-3">
        <button
          onClick={isCompleted ? undefined : handleComplete}
          disabled={isCompleted || saving}
          className="shrink-0 mt-0.5 transition-all focus:outline-none focus-visible:ring-2 rounded-full disabled:cursor-default"
          aria-label={isCompleted ? 'Completed' : 'Mark as complete'}
        >
          {saving ? (
            <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--saffron)' }} />
          ) : isCompleted ? (
            <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--success)' }} />
          ) : (
            <Circle className="w-5 h-5 hover:text-saffron transition-colors" style={{ color: 'var(--text-muted)' }} />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-medium leading-relaxed"
            style={{
              color: 'var(--text-primary)',
              textDecoration: isCompleted ? 'line-through' : 'none',
              opacity: isCompleted ? 0.6 : 1,
            }}
          >
            {item.text}
          </p>

          {item.reason && (
            <p className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              {item.reason}
            </p>
          )}

          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              <Clock className="w-3 h-3 inline mr-1" aria-hidden="true" />
              {new Date(item.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
            </span>

            {item.follow_up_outcome && (
              <span className="text-xs font-semibold" style={{ color: OUTCOME_COLORS[item.follow_up_outcome as Outcome] }}>
                {OUTCOME_LABELS[item.follow_up_outcome as Outcome]}
              </span>
            )}

            {isCompleted && !item.follow_up_outcome && (
              <button
                onClick={() => setExpanded(v => !v)}
                className="text-xs font-semibold flex items-center gap-1 focus:outline-none focus-visible:ring-2"
                style={{ color: 'var(--saffron)' }}
              >
                How did it go?
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
          </div>

          {/* Follow-up form */}
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 space-y-2 overflow-hidden"
              >
                <div className="flex gap-2 flex-wrap">
                  {(Object.keys(OUTCOME_LABELS) as Outcome[]).map(o => (
                    <button
                      key={o}
                      onClick={() => setSelectedOutcome(o)}
                      className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all focus:outline-none focus-visible:ring-2"
                      style={{
                        background: selectedOutcome === o ? OUTCOME_COLORS[o] : 'var(--card-surface)',
                        color: selectedOutcome === o ? '#fff' : 'var(--text-muted)',
                        border: `1px solid ${selectedOutcome === o ? OUTCOME_COLORS[o] : 'var(--card-border)'}`,
                      }}
                    >
                      {OUTCOME_LABELS[o]}
                    </button>
                  ))}
                </div>
                <textarea
                  value={note}
                  onChange={e => setNote(e.target.value)}
                  placeholder="Any notes? (optional)"
                  rows={2}
                  className="w-full px-3 py-2 rounded-xl text-xs resize-none focus:outline-none focus-visible:ring-2"
                  style={{ background: 'var(--input-surface)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}
                />
                <button
                  onClick={handleFollowUp}
                  disabled={!selectedOutcome || saving}
                  className="px-4 py-1.5 rounded-full text-xs font-semibold disabled:opacity-40 focus:outline-none focus-visible:ring-2 transition-all"
                  style={{ background: 'var(--saffron)', color: 'var(--on-saffron)' }}
                >
                  {saving ? 'Saving…' : 'Save follow-up'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </GlassCard>
  );
}

export default function ActionsPage() {
  const [actions, setActions] = useState<BackendActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');

  const load = async () => {
    setLoading(true);
    const data = await getActions();
    setActions(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const filtered = actions.filter(a => {
    if (filter === 'pending') return !a.completed;
    if (filter === 'completed') return a.completed;
    return true;
  });

  const pending = actions.filter(a => !a.completed).length;
  const done = actions.filter(a => a.completed).length;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
          Action Items
        </h1>
        <p className="text-sm text-center mb-4" style={{ color: 'var(--text-muted)' }}>
          Concrete steps from your reflections. Take them one at a time.
        </p>
        <SectionDivider />
      </motion.div>

      {/* Stats + filter */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex gap-3 text-sm">
          <span className="font-semibold" style={{ color: 'var(--saffron)' }}>{pending} pending</span>
          <span style={{ color: 'var(--text-muted)' }}>·</span>
          <span className="font-semibold" style={{ color: 'var(--success)' }}>{done} done</span>
        </div>
        <div className="flex gap-1.5">
          {(['all', 'pending', 'completed'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all focus:outline-none focus-visible:ring-2 capitalize"
              style={{
                background: filter === f ? 'var(--saffron)' : 'var(--card-surface)',
                color: filter === f ? 'var(--on-saffron)' : 'var(--text-muted)',
                border: `1px solid ${filter === f ? 'var(--saffron)' : 'var(--card-border)'}`,
              }}>
              {f}
            </button>
          ))}
          <button onClick={load} className="text-xs px-2 py-1.5 rounded-full transition-all focus:outline-none focus-visible:ring-2"
            style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)', color: 'var(--text-muted)' }}>
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </motion.div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-7 h-7 animate-spin" style={{ color: 'var(--saffron)' }} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {filter === 'pending' ? 'No pending actions — great work!' : filter === 'completed' ? 'No completed actions yet.' : 'No actions yet. Complete a mentor reflection to get your first action.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {filtered.map((a, i) => (
              <motion.div key={a.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <ActionCard item={a} onUpdate={load} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
