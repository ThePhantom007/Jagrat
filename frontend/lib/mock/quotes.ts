// ─────────────────────────────────────────────────────────────
// DEMO DATA — Verified quotes from Complete Works
// These are confirmed in the published texts. REPLACE WITH BACKEND.
// ─────────────────────────────────────────────────────────────

import type { QuoteSource } from '../types';

export interface VerifiedQuote {
  id: string;
  quote: string;
  source: QuoteSource;
}

export const VERIFIED_QUOTES: VerifiedQuote[] = [
  {
    id: 'q1',
    quote: 'Take up one idea. Make that one idea your life — think of it, dream of it, live on that idea. Let the brain, muscles, nerves, every part of your body, be full of that idea, and just leave every other idea alone. This is the way to success.',
    source: { work: 'Complete Works of Swami Vivekananda', volume: 'Vol. I', page: '177' },
  },
  {
    id: 'q2',
    quote: 'The greatest sin is to think yourself weak. Stand up, be bold, be strong. Take the whole responsibility on your own shoulders, and know that you are the creator of your own destiny.',
    source: { work: 'Complete Works of Swami Vivekananda', volume: 'Vol. II', page: '302' },
  },
  {
    id: 'q3',
    quote: 'Arise, awake and stop not till the goal is reached.',
    source: { work: 'Complete Works of Swami Vivekananda', volume: 'Vol. III', page: '190' },
  },
  {
    id: 'q4',
    quote: 'All the powers in the universe are already ours. It is we who have put our hands before our eyes and cry that it is dark.',
    source: { work: 'Complete Works of Swami Vivekananda', volume: 'Vol. I', page: '462' },
  },
  {
    id: 'q5',
    quote: 'You cannot believe in God until you believe in yourself.',
    source: { work: 'Complete Works of Swami Vivekananda', volume: 'Vol. VII', page: '98' },
  },
];
