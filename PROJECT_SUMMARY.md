# Jagrat (जाग्रत) - Project Summary

## 🎯 Project Overview

**Jagrat** is a full-stack spiritual guidance and reflection application that integrates Swami Vivekananda's teachings with modern AI technology. The application provides personalized mentorship, journaling, and growth tracking for personal development.

## 📂 Project Structure

```
kasukabe/
├── jagrat-frontend/          # Next.js 15 frontend application
│   ├── app/                  # Next.js app router pages
│   │   ├── page.tsx          # Landing page with Om + suns + sparkles
│   │   ├── login/            # Login page (OTP/Google/Guest)
│   │   ├── onboarding/       # 7-step onboarding wizard
│   │   └── app/              # Protected application routes
│   │       ├── chat/         # Mentor chat interface
│   │       ├── journal/      # Daily journal with AI insights
│   │       ├── growth/       # Growth dashboard (bento grid)
│   │       └── honesty/      # Vivekananda vs Me comparisons
│   ├── components/           # React components
│   │   ├── ui/               # UI primitives (GlassCard, SaffronButton, etc.)
│   │   ├── ThreeLayerCard    # 3-layer mentor response card
│   │   ├── JournalEditor     # Rich journal editor with live tags
│   │   ├── FloatingThemeToggle # Theme switcher (all pages)
│   │   └── ...
│   ├── lib/                  # Utilities and API client
│   │   ├── api.ts            # Backend API integration
│   │   ├── types.ts          # TypeScript interfaces
│   │   ├── theme.ts          # Theme configuration
│   │   └── i18n.ts           # Internationalization
│   ├── public/               # Static assets
│   ├── styles/               # Global styles + ambient.css
│   ├── .env.local            # Environment variables
│   └── package.json
│
├── jagrat-backend/           # FastAPI backend application
│   ├── app/                  # Backend application code
│   │   ├── api/              # API route handlers
│   │   │   ├── mentor.py     # Mentor conversation endpoints
│   │   │   ├── journal.py    # Journal CRUD endpoints
│   │   │   ├── growth.py     # Growth metrics endpoints
│   │   │   ├── profile.py    # User profile endpoints
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── gemini.py     # Google Gemini AI service
│   │   │   ├── mentor.py     # Mentor service
│   │   │   ├── retrieval.py  # Teaching retrieval (BM25)
│   │   │   └── safety.py     # Crisis detection
│   │   ├── db/               # Database layer
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   └── main.py           # FastAPI app entry
│   ├── data/                 # Teaching corpus
│   │   ├── articles.json     # Vivekananda teachings
│   │   └── JSON_FORMAT.md
│   ├── tests/                # Backend tests
│   ├── scripts/              # Utility scripts
│   ├── .env                  # Backend environment
│   ├── requirements.txt      # Python dependencies
│   └── README.md
│
├── INTEGRATION_COMPLETE.md   # Integration documentation
├── TEST_INTEGRATION.md       # Test checklist
└── PROJECT_SUMMARY.md        # This file
```

## 🎨 Design System ("Nurturing Saffron")

### Color Palette

#### Light Mode
- **Background**: Peach-cream gradient (#FFF7EA → #F8C9A2)
- **Saffron Primary**: #FC6C26
- **Saffron Hover**: #E85D1F
- **Saffron Soft**: rgba(252,108,38,0.10)
- **Text Primary**: #1B1007 (dark brown)
- **Text Muted**: #6B5646
- **Card Surface**: rgba(255,255,255,0.80)
- **On Saffron**: #FFFFFF (white text on saffron)

#### Dark Mode
- **Background**: Dark gradient (#0B0D13 → #161A26)
- **Saffron Primary**: #FC6C26
- **Saffron Hover**: #FD844A
- **Saffron Soft**: rgba(252,108,38,0.12)
- **Text Primary**: #F5E6D3
- **Text Muted**: #9B8B7A
- **Card Surface**: rgba(30,30,40,0.85)
- **On Saffron**: #1B1007 (dark text on saffron)

### Typography
- **Primary Font**: Geist Sans (system default)
- **Scripture Font**: Playfair Display (Vivekananda quotes)
- **Code Font**: Geist Mono

### Components
- **GlassCard**: Semi-transparent cards with blur effect
- **SaffronButton**: Primary action buttons with saffron glow
- **PillOption**: Rounded selection pills for onboarding
- **StepperDots**: Numbered progress indicators
- **MetricTile**: Growth dashboard metric cards
- **TagChip**: Emotional tags with color-coding
- **SectionDivider**: Decorative dividers with Om symbol

### Ambient Background
- **Om Watermark**: Centered, large, subtle opacity
- **Sun Bursts**: 3-4 animated sun rays (rotating)
- **Sparkles**: 4-point sparkles scattered across background
- **No Floral Elements**: Confirmed removed from entire codebase

## 🚀 Key Features

### 1. Onboarding (7 Steps)
1. **Primary focus area**: inner_strength, discipline, clear_goal, overcome_fear, other
2. **Biggest challenge**: exam_failure, self_doubt, fear, decision_hesitation, discipline
3. **Failure response**: overthinking, withdrawal, quick_reset
4. **Confidence level**: 1-10 slider with animated display
5. **Primary goal**: academic_growth, mental_focus, inner_strength
6. **Preferences**: Language (EN/HI/BN) + reflection time
7. **Review**: Summary with "Start my journey" button

### 2. Mentor Chat (Spiritual Guidance)
- **Three-Layer Card** response structure:
  - **Layer 1 (Listening)**: AI understanding + clarifying question
  - **Layer 2 (Documented Teaching)**: Verified Vivekananda quote with source
  - **Layer 3 (AI Reflection)**: Interpretation + next step + challenge
- **Crisis Detection**: Automatic safety response with helplines
- **Starter Prompts**: Suggested reflection topics
- **Conversation History**: Resume previous sessions
- **Challenge Mode**: Deep questioning for assumptions

### 3. Journal
- **Rich Editor**: Live tag extraction as you type
- **Emotion Tags**: 10 categories (self_doubt, anxiety, hope, etc.)
- **History Panel**: Past entries with date + preview + tags
- **Backend Persistence**: Real-time sync with database
- **AI Insights**: Optional analysis with Gemini

### 4. Growth Dashboard (Bento Grid)
- **"Your Week" Metrics** (2x2 grid):
  - Self-belief ↑
  - Fear ↓
  - Discipline →
  - Purpose ↑
- **"Insights: What Changed?"**: Weekly narrative
- **"Pattern Recognition"**: Behavioral patterns + sparkline
- **"Focus for next week"**: Actionable suggestion banner
- **Backend-Driven**: Real data from reflection history

### 5. Teaching Library
- Save favorite Vivekananda quotes
- Filter by theme, emotion, or keyword
- Export to PDF/text

### 6. Vivekananda vs Me
- Write your personal belief
- Get relevant Vivekananda quote
- AI comparison highlighting alignment/differences
- Thought-provoking questions
- Suggested experiment

## 🔧 Technical Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **Animation**: Framer Motion
- **State**: React Context API
- **Theme**: CSS Custom Properties
- **Icons**: Lucide React
- **Build**: Turbopack (dev), Next.js (prod)

### Backend
- **Framework**: FastAPI 0.142+
- **Language**: Python 3.12+
- **Database**: SQLAlchemy 2.1 (SQLite/PostgreSQL)
- **AI**: Google Gemini 2.x (gemini-3.8-flash)
- **Retrieval**: BM25 (deterministic, local)
- **Auth**: Token-based (X-Profile-Token header)
- **CORS**: Configured for localhost + production

### Database Schema
- **Profile**: User profile + onboarding answers
- **Conversation**: Mentor chat sessions
- **Message**: Individual chat messages
- **ChallengeRound**: Challenge Q&A rounds
- **JournalEntry**: Daily journal entries
- **JournalInsight**: AI-extracted tags/themes/emotions
- **Article**: Vivekananda teaching corpus
- **SavedTeaching**: User's saved teachings
- **Action**: Reflection actions + follow-ups
- **ReflectionGoal**: Active personal goal

## 📡 API Integration

### Authentication Flow
1. User completes onboarding
2. Frontend calls `POST /api/profile` with `display_name`
3. Backend returns `{ id, access_token }`
4. Frontend stores token in `localStorage`
5. All subsequent requests include `X-Profile-Token` header

### Key Endpoints

#### Profile
- `POST /api/profile` - Create anonymous profile
- `POST /api/profile/onboarding` - Save onboarding answers
- `GET /api/profile` - Get profile details

#### Mentor
- `POST /api/mentor` - Start new reflection
- `POST /api/mentor/{id}/continue` - Continue conversation
- `POST /api/mentor/{id}/challenge` - Respond to challenge
- `GET /api/mentor/sessions` - List active sessions

#### Journal
- `POST /api/journal` - Create entry
- `GET /api/journal` - List entries
- `POST /api/journal/{id}/analyze` - Trigger AI analysis

#### Growth
- `GET /api/growth-journey` - Get weekly metrics
- `POST /api/growth/goal` - Set reflection goal

### Error Handling
- **503**: Gemini API unavailable (graceful degradation)
- **409**: Onboarding incomplete or conflict
- **502**: Source guard violated (AI attribution error)
- **404**: Resource not found
- **422**: Validation error

## 🛠️ Development Workflow

### Setup

```bash
# Frontend
cd jagrat-frontend
npm install
cp .env.example .env.local
npm run dev

# Backend
cd jagrat-backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Environment Variables

**Frontend (`.env.local`)**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=false
```

**Backend (`.env`)**:
```env
DATABASE_URL=sqlite:///./mentor.db
GEMINI_API_KEY=your_key_here
CORS_ORIGINS=http://localhost:3000
```

### Testing

```bash
# Frontend
npm run build
npm run lint

# Backend
pytest -q
python scripts/audit_articles.py data/articles.json
python scripts/ingest_articles.py data/articles.json --replace
```

## 📊 Current Status

### ✅ Completed
- [x] Backend cloned and set up
- [x] Frontend connected to backend APIs
- [x] Profile creation + onboarding flow
- [x] Mentor chat integration
- [x] Journal CRUD with backend persistence
- [x] Growth dashboard with real data
- [x] FloatingThemeToggle on all pages
- [x] All UI components match master plan
- [x] "Nurturing Saffron" theme implemented
- [x] Om + suns + sparkles background (no floral)
- [x] --on-saffron contrast fixed
- [x] Both servers running successfully
- [x] Environment configuration complete
- [x] Documentation complete

### ⚠️ Requires Gemini API Key
- Mentor AI responses
- Journal AI analysis
- Vivekananda vs Me comparisons
- Growth narrative generation

Without the key, these features return HTTP 503, but the application remains functional in mock mode or with cached data.

### 🚧 Future Enhancements
- Email/SMS notifications
- Streak tracking with reminders
- Community features (anonymous reflection sharing)
- Multi-language teaching corpus
- Voice input for journal/chat
- Offline PWA support
- Export reflection history
- Custom themes

## 🔒 Security & Privacy

- **Anonymous Profiles**: No email or personal data required
- **Token-Based Auth**: Secure access tokens
- **Crisis Detection**: Local + AI-based safety nets
- **Source Guard**: Prevents AI hallucination of quotes
- **CORS Protection**: Configured for specific origins
- **Input Validation**: Pydantic schemas on backend
- **XSS Prevention**: React auto-escaping

## 📈 Performance

- **Frontend**: Static generation + ISR where possible
- **Backend**: FastAPI async/await
- **Database**: Indexed queries, connection pooling
- **Caching**: Teaching corpus loaded at startup
- **CDN-Ready**: Static assets optimized for CDN

## 🌍 Internationalization

- **Supported Languages**: English, Hindi, Bengali
- **UI Translations**: All user-facing text
- **Teaching Corpus**: English + romanized Hinglish
- **RTL Support**: Not yet implemented

## 📝 License & Attribution

- **Teaching Source**: Swami Vivekananda's Complete Works (public domain)
- **Code**: [Specify your license]
- **Design**: Original "Nurturing Saffron" design system

## 🙏 Acknowledgments

- Ramakrishna Mission for preserving Vivekananda's teachings
- Google Gemini for AI capabilities
- Next.js, FastAPI, and open-source community

---

## Quick Start Commands

```bash
# Start backend
cd jagrat-backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Start frontend (new terminal)
cd jagrat-frontend
npm run dev

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Project Status**: ✅ **Integration Complete & Ready for Testing**

