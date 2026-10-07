'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar } from 'lucide-react';
import { JournalEditor } from '@/components/JournalEditor';
import { JournalHistoryPanel } from '@/components/JournalHistoryPanel';
import { GlassCard } from '@/components/ui/GlassCard';
import { useAppContext } from '@/components/ThemeProvider';
import type { JournalEntry, EmotionTag } from '@/lib/types';
import { getJournalEntries, saveJournalEntry } from '@/lib/api';

export default function JournalPage() {
  const { lang } = useAppContext();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load entries on mount
  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    try {
      const data = await getJournalEntries();
      setEntries(data);
    } catch (error) {
      console.error('Failed to load journal entries:', error);
    }
  };

  const handleSave = async (content: string, tags: EmotionTag[]) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const entry: JournalEntry = {
        id: `j-${Date.now()}`,
        date: new Date().toISOString().split('T')[0],
        text: content,
        tags,
      };
      
      const updated = await saveJournalEntry(entry);
      setEntries(updated);
      setSelectedEntry(null);
    } catch (error) {
      console.error('Failed to save journal entry:', error);
      alert('Failed to save entry. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEntry = (entry: JournalEntry) => {
    setSelectedEntry(entry);
  };

  const currentDate = new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">

        {/* ── Main Journal Card ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <GlassCard className="p-6">
            {/* Header with title and date pill */}
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                Journal
              </h1>
              
              {/* Date pill */}
              <button
                onClick={() => setShowDatePicker(!showDatePicker)}
                className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
                style={{
                  background: 'var(--pill-surface)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--text-primary)',
                  boxShadow: 'var(--card-shadow)',
                }}
                aria-label="Select date"
              >
                <Calendar className="w-4 h-4" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
                {currentDate}
              </button>
            </div>

            {/* Editor */}
            <div>
              <JournalEditor 
                lang={lang} 
                onSave={handleSave}
                initialContent={selectedEntry ? (selectedEntry.text || selectedEntry.content || '') : ''}
                disabled={loading}
              />
            </div>

            {/* Italic microcopy line below Save button */}
            <p className="text-center text-sm italic mt-4 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              &ldquo;The path of reflection is the royal road to realization.&rdquo;
            </p>
          </GlassCard>
        </motion.div>

        {/* ── History Panel (Right Sidebar) ── */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="lg:block hidden"
        >
          <div className="sticky top-20">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <span>History</span>
              <span
                className="text-sm px-2 py-0.5 rounded-full font-semibold"
                style={{ background: 'var(--saffron-soft)', color: 'var(--saffron)' }}
              >
                {entries.length}
              </span>
            </h2>
            <div className="max-h-[calc(100vh-12rem)] overflow-y-auto pr-2 scrollbar-thin">
              <JournalHistoryPanel entries={entries} onSelectEntry={handleSelectEntry} />
            </div>
          </div>
        </motion.div>

        {/* ── Mobile History (Bottom Sheet Trigger) ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="lg:hidden"
        >
          <button
            className="w-full py-3 rounded-xl text-sm font-semibold transition-all active:scale-[0.99] focus:outline-none focus-visible:ring-2"
            style={{
              background: 'var(--card-surface)',
              border: '1px solid var(--card-border)',
              color: 'var(--text-primary)',
              boxShadow: 'var(--card-shadow)',
            }}
          >
            View History ({entries.length} entries)
          </button>
          
          {/* History panel for mobile */}
          <div className="mt-4">
            <JournalHistoryPanel entries={entries} onSelectEntry={handleSelectEntry} />
          </div>
        </motion.div>

      </div>
    </div>
  );
}
