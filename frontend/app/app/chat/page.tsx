'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { ThreeLayerCard } from '@/components/ThreeLayerCard';
import { CrisisCard } from '@/components/CrisisCard';
import { SectionDivider } from '@/components/ui/SectionDivider';
import { useAppContext } from '@/components/ThemeProvider';
import { t } from '@/lib/i18n';
import type { ChatMessage } from '@/lib/types';
import { sendMentorMessage, retryReflection } from '@/lib/api';

const STARTERS = [
  "I failed my exam and I feel like I'm not smart enough.",
  "I keep comparing myself to my classmates and feel left behind.",
  "I want to study but I can't seem to focus for more than 10 minutes.",
];

export default function ChatPage() {
  const { lang } = useAppContext();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  // Track the current backend conversation_id for multi-turn
  const conversationIdRef = useRef<string | null>(null);
  // Track if the last mentor turn failed (shows retry button)
  const [lastFailedConvId, setLastFailedConvId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const appendAssistant = useCallback((response: Awaited<ReturnType<typeof sendMentorMessage>>) => {
    // Store the conversation_id for subsequent turns
    if (response.conversationId) {
      conversationIdRef.current = response.conversationId;
    }
    setMessages(prev => [
      ...prev,
      {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        mentorResponse: response,
      },
    ]);
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setLastFailedConvId(null);

    try {
      // Pass existing conversationId for multi-turn (continue) flow
      const response = await sendMentorMessage(trimmed, conversationIdRef.current);
      appendAssistant(response);
    } catch (err) {
      console.error('Mentor API error:', err);
      // Surface a retry option if we have a conversation to retry
      if (conversationIdRef.current) {
        setLastFailedConvId(conversationIdRef.current);
      }
      // Show an error message in the thread
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          mentorResponse: {
            listening: { summary: '', question: '' },
            documented: null,
            reflection: {
              text: err instanceof Error ? err.message : 'Something went wrong. Please try again.',
              nextStep: '',
            },
            crisis: false,
          },
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [loading, appendAssistant]);

  const handleRetry = useCallback(async () => {
    if (!lastFailedConvId || loading) return;
    setLoading(true);
    setLastFailedConvId(null);
    // Remove the last error message
    setMessages(prev => prev.filter(m => !m.id.startsWith('err-')));
    try {
      const response = await retryReflection(lastFailedConvId);
      appendAssistant(response);
    } catch (err) {
      console.error('Retry failed:', err);
      setLastFailedConvId(lastFailedConvId);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [lastFailedConvId, loading, appendAssistant]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col min-h-[calc(100vh-7rem)]">

      {/* Page Title */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-center mb-4" style={{ color: 'var(--text-primary)' }}>
          Spiritual Guidance Session
        </h1>
        <SectionDivider />
      </div>

      {/* Empty state */}
      {messages.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="flex-1 flex flex-col items-center justify-center text-center gap-6 py-12"
        >
          <div
            className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl"
            style={{ background: 'linear-gradient(135deg, var(--saffron), var(--saffron-hover))' }}
            aria-hidden="true"
          >⚡</div>
          <div className="space-y-3">
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
              Welcome to Your Reflection Space
            </h2>
            <p className="text-sm max-w-md leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              Share what is on your mind. I will listen, anchor your reflection in verified teachings
              of Swami Vivekananda, and help you find your next step.
            </p>
          </div>
          <div className="flex flex-col gap-2 w-full max-w-md">
            <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>
              Try one of these:
            </p>
            {STARTERS.map((s, i) => (
              <button
                key={i} onClick={() => sendMessage(s)}
                className="text-left px-4 py-3 rounded-xl text-sm transition-all hover:scale-[1.01] active:scale-[0.99] focus:outline-none focus-visible:ring-2"
                style={{
                  background: 'var(--card-surface)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--text-muted)',
                  boxShadow: 'var(--card-shadow)',
                }}
              >
                <Sparkles className="w-3.5 h-3.5 inline-block mr-2 mb-0.5" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
                {s}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Message thread */}
      {messages.length > 0 && (
        <div className="flex-1 space-y-6 pb-6">
          <AnimatePresence initial={false}>
            {messages.map(msg => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
              >
                {msg.role === 'user' ? (
                  <div className="flex justify-end">
                    <div
                      className="max-w-[75%] px-5 py-3 rounded-2xl rounded-br-sm text-sm leading-relaxed"
                      style={{
                        background: 'var(--saffron)',
                        color: 'var(--on-saffron)',
                        boxShadow: '0 3px 14px var(--saffron-glow)',
                      }}
                    >
                      {msg.content}
                    </div>
                  </div>
                ) : msg.mentorResponse ? (
                  msg.mentorResponse.crisis ? (
                    <CrisisCard lang={lang} />
                  ) : (
                    <ThreeLayerCard response={msg.mentorResponse} lang={lang} />
                  )
                ) : null}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          <AnimatePresence>
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="flex items-center gap-3 px-5 py-4 rounded-2xl w-fit"
                style={{ background: 'var(--card-surface)', border: '1px solid var(--card-border)' }}
                role="status" aria-label="Thinking"
              >
                <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--saffron)' }} aria-hidden="true" />
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Reflecting deeply…</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Retry button when a generation failed */}
          <AnimatePresence>
            {lastFailedConvId && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="flex justify-center"
              >
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2"
                  style={{
                    background: 'var(--saffron-soft)',
                    border: '1px solid var(--saffron)',
                    color: 'var(--saffron)',
                  }}
                >
                  <RefreshCw className="w-4 h-4" aria-hidden="true" />
                  Retry Reflection
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={bottomRef} aria-hidden="true" />
        </div>
      )}

      {/* Sticky input bar */}
      <div
        className="sticky bottom-0 pt-4 pb-3"
        style={{ background: 'linear-gradient(to bottom, transparent, var(--bg-from) 20%)' }}
      >
        <p className="text-center text-sm italic mb-3 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          Engage and reflect — this is a space for your inner work.
        </p>
        <div
          className="flex items-end gap-2 p-3 rounded-full"
          style={{
            background: 'var(--card-surface)',
            border: '1px solid var(--card-border)',
            boxShadow: 'var(--shadow-float)',
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your current challenge…"
            rows={1}
            className="flex-1 resize-none bg-transparent px-3 py-2 text-base focus:outline-none leading-relaxed"
            style={{ color: 'var(--text-primary)', maxHeight: '100px', overflowY: 'auto' }}
            aria-label="Message input"
            disabled={loading}
            data-gramm="false"
            data-gramm_editor="false"
            data-enable-grammarly="false"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-full flex items-center justify-center shrink-0 transition-all active:scale-90 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2"
            style={{
              background: input.trim() ? 'var(--saffron)' : 'var(--pill-surface)',
              color: input.trim() ? 'var(--on-saffron)' : 'var(--text-muted)',
              boxShadow: input.trim() ? '0 4px 16px var(--saffron-glow)' : 'none',
            }}
            aria-label="Send message"
          >
            {loading
              ? <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
              : <Send className="w-5 h-5" aria-hidden="true" />
            }
          </button>
        </div>
      </div>
    </div>
  );
}
