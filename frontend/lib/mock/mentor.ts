// ─────────────────────────────────────────────────────────────
// DEMO DATA, REPLACE WITH BACKEND
// Mock mentor responses for development and demo purposes.
// ─────────────────────────────────────────────────────────────

import type { MentorResponse } from '../types';
import { VERIFIED_QUOTES } from './quotes';

export const DEMO_MENTOR_RESPONSES: MentorResponse[] = [
  {
    listening: {
      summary: "I hear that you're carrying the weight of a recent exam result and questioning your own capability. That kind of pain is real — and it takes courage to sit with it rather than run from it.",
      question: "Before we explore Swami Vivekananda's perspective — what is one specific thing you did prepare well, even if the outcome didn't reflect it?",
    },
    documented: {
      id: VERIFIED_QUOTES[0].id,
      quote: VERIFIED_QUOTES[0].quote,
      source: VERIFIED_QUOTES[0].source,
      verified: true,
    },
    reflection: {
      text: "Swami Vivekananda is pointing to something counterintuitive: the problem isn't your intelligence — it's diffusion of focus. When we fear failure, we fragment our attention across worry, comparison, and regret. The teaching asks you to collapse all of that into a single, burning point of concentration.",
      nextStep: 'Identify the ONE subject or topic that, if mastered this week, would move your confidence the most. Write it down and spend 45 focused minutes on it tomorrow morning.',
    },
    challenge: {
      belief: "I failed because I'm not smart enough.",
      assumption: 'Failure = Lack of intrinsic capability.',
      pivot: 'What objective evidence tells you that an exam score measures your intelligence rather than your current preparation method?',
    },
  },
  {
    listening: {
      summary: "You're describing a persistent loop of self-doubt that keeps you from starting. That paralysis before action is one of the most common — and most painful — experiences for any serious student.",
      question: 'When in your life did you begin something without feeling fully ready, and it still went better than expected?',
    },
    documented: {
      id: VERIFIED_QUOTES[1].id,
      quote: VERIFIED_QUOTES[1].quote,
      source: VERIFIED_QUOTES[1].source,
      verified: true,
    },
    reflection: {
      text: "Vivekananda identifies weakness — not ignorance, not circumstance — as the root obstacle. The 'sin' he refers to is the habit of self-minimisation. Every time you say 'I can't,' you train your mind to accept limitation as identity. This teaching is a direct challenge to rewrite that internal script.",
      nextStep: 'Write down three times in the past month when you showed genuine strength — academic, social, or personal. Read them aloud before you open your books tomorrow.',
    },
  },
  {
    listening: {
      summary: "It sounds like you're struggling with the gap between where you are and where you want to be. That awareness itself is a sign of growth — many people never even notice the gap.",
      question: 'What would it look like if you were already making progress, even if it was small?',
    },
    documented: null, // No-match state: no corpus quote fits
    reflection: {
      text: "Sometimes the most honest thing a mentor can do is acknowledge that no single teaching perfectly addresses your specific situation. What matters is that you're asking the right questions. The willingness to reflect is itself the beginning of change.",
      nextStep: 'Write down one small action you can take today that moves you even 1% closer to your goal. Do it before the day ends.',
    },
  },
];

/** Crisis response — replaces the entire mentor response */
export const DEMO_CRISIS_RESPONSE: MentorResponse = {
  listening: {
    summary: '',
    question: '',
  },
  documented: null,
  reflection: {
    text: '',
    nextStep: '',
  },
  crisis: true,
};
