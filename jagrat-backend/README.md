# Jagrat — Hackathon Backend

A single FastAPI backend for a reflective digital mentor. It combines the strongest parts of the two teammate implementations while following the revised hackathon scope:

- organiser-provided CSV is the canonical source of truth;
- Gemini is the reasoning/classification layer, never the source-authority layer;
- no login/signup for the hackathon;
- all six onboarding answers are required before Mentor starts, are passed into every mentor-generation context, and Gemini must explicitly trace all six dimensions in each tailored response;
- no vector database or embeddings required for the MVP;
- relevant journal memory only;
- safety path for chat, journal, and challenge input;
- Socratic Challenge My Thinking, capped at 3 rounds;
- observed reflection-theme frequencies rather than invented growth arrows;
- user-editable/deletable journal insights;
- weekly self-report check-ins + Gemini narrative report;
- lifetime five-factor progress series for the Growth Journey graph;
- Growth Journey dashboard metrics inspired by the demo: day streak, total reflections, factor cards, weekly anchor teaching, and weekly focus/report data;
- Honesty tab: transparent source, AI, journal-memory, growth, and safety disclosure;
- free deployment target: Render Web Service + Neon Postgres;
- browser SpeechSynthesis remains a frontend concern.

## Architecture

```text
Frontend
   |
   v
FastAPI
   |
   +-- Demo Profile / Onboarding
   +-- Journal -----> Gemini: risk + descriptive extraction
   |                      |
   |                      v
   |                 Journal Insight DB
   |                      |
   |          relevant memories only
   |
   +-- Mentor
   |      |
   |      +--> Gemini: risk + problem classification
   |      |
   |      +--> code-side tag retrieval
   |      |       |
   |      |       +--> <= 7 organiser CSV passages
   |      |
   |      +--> Gemini: mentor generation
   |              |
   |              +--> quote_id ONLY
   |                      |
   |                 candidate-ID guard
   |                      |
   |                 DB exact lookup
   |                      |
   |              exact CSV passage + source
   |
   +-- Challenge My Thinking (one Gemini call/round)
   +-- Theme-frequency Growth
   +-- Weekly self-report + Gemini narrative
   +-- Actions
```

### Trust boundary

```text
ORGANISER CSV
     ↓
CANONICAL TEACHING DATABASE
     ↓
BACKEND RETRIEVAL (5–7 candidates)
     ↓
GEMINI returns quote_id ONLY
     ↓
BACKEND checks: is this ID in the candidate set?
     ↓
BACKEND fetches exact stored passage + exact source metadata
     ↓
FRONTEND shows Trust Panel + AI interpretation separately
```

This means Gemini never gets the authority to create the quote that is displayed as a source passage.

## Team-facing CSV format

The exact specification is in [`data/CSV_FORMAT.md`](data/CSV_FORMAT.md).

Recommended header:

```text
id,text,themes,emotions,challenges,keywords,source_type,source_title,source_volume,source_chapter,source_page,source_section,source_url,context
```

### Important rule

One row is one **passage**, not necessarily one sentence. A passage may contain multiple paragraphs. Put the complete passage in the `text` field and preserve paragraph breaks. CSV quoted fields can contain newlines.

Required fields:

```text
id
text
source_type
source_title
```

`source_type` should normally be one of:

```text
book | speech | sermon | letter | interview | conversation | article | other
```

List fields use `|`:

```text
self_belief|resilience|fearlessness
```

Do not add `verified` or `verification_status`. Every record imported by the canonical importer is treated as organiser-provided source material.

## Gemini / free tier

The backend uses the official `google-genai` SDK and the Gemini Interactions API with structured JSON output. The default models are:

```text
gemini-3.8-flash       # main mentor reasoning
gemini-3.1-flash-lite  # lightweight classification/extraction
```

The current Gemini Developer API pricing page lists Gemini 3.8 Flash and Gemini 3.1 Flash-Lite with free standard-tier text input/output. Google also documents structured output for the Interactions API. Free-tier limits are quota-based and can change; check AI Studio before the demo. See:

- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/gemini-api/docs/interactions-overview
- https://ai.google.dev/gemini-api/docs/pricing

### Free-tier call budget

Normal mentor request:

```text
1 Gemini call  = safety + problem classification
1 Gemini call  = mentor generation
```

Journal create/update:

```text
1 Gemini call  = safety + journal extraction
```

Challenge response:

```text
1 Gemini call  = safety + Socratic generation
```

Weekly report:

```text
1 Gemini call
```

There is no Gemini call for deterministic teaching retrieval.

`store=false` is used because the application owns its own persistence. This does **not** change the Gemini free-tier data-use policy; Google currently states that free-tier content may be used to improve its products. The team explicitly accepted that trade-off for this hackathon. Do not reuse this setup for sensitive real-world production data without reviewing Google's current terms/policy.

## Local setup

### SQLite

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# Put your GEMINI_API_KEY in .env

uvicorn app.main:app --reload
```

API docs:

```text
http://localhost:8000/docs
```

### Docker + PostgreSQL

```bash
docker compose up --build
```

## Canonical CSV ingestion

Put the organiser-provided CSV here:

```text
data/teachings.csv
```

The backend will automatically ingest it on startup when the table is empty and `AUTO_INGEST_TEACHINGS=true`.

Manual ingestion:

```bash
python scripts/ingest_teachings.py data/teachings.csv --replace
```

The importer:

- rejects missing required columns;
- rejects empty passages;
- rejects duplicate IDs;
- validates `source_type`;
- preserves the full multi-paragraph text;
- records a SHA-256 content hash for exact-record auditing.

## Demo data

The backend seeds a demo profile and one week of journal/check-in data automatically on startup by default. This makes the demo dashboard useful immediately after a fresh Neon deployment without requiring Render shell access.

Configuration:

```text
SEED_DEMO_ON_STARTUP=true
AUTO_INGEST_TEACHINGS=true
TEACHINGS_CSV_PATH=data/teachings.csv
```

Demo profile ID:

```text
demo
```

For local multi-profile testing, send:

```http
X-Profile-Id: another-profile-id
```

## API surface

### Profile / onboarding

```http
GET /api/profile
PUT /api/profile
PUT /api/profile/onboarding
```

### Journal

```http
POST   /api/journal
GET    /api/journal
PATCH  /api/journal/{entry_id}
DELETE /api/journal/{entry_id}
PATCH  /api/journal/insights/{insight_id}
DELETE /api/journal/insights/{insight_id}
```

Every create/update goes through the safety gate. A blocking risk result means no normal journal insight is generated.

### Mentor

```http
POST /api/mentor
GET  /api/mentor/{conversation_id}
POST /api/mentor/{conversation_id}/challenge
```

Request:

```json
{
  "message": "I failed my exam and now I think I'm not capable."
}
```

Normal response contains:

```json
{
  "status": "ok",
  "conversation_id": "...",
  "round": 1,
  "understanding": "...",
  "teaching": {
    "id": "T012",
    "quote": "EXACT MULTI-PARAGRAPH TEXT FROM CANONICAL CSV",
    "source": {
      "type": "speech",
      "title": "...",
      "volume": "...",
      "chapter": "...",
      "page": "...",
      "section": "...",
      "url": "...",
      "authority": "organizer_provided_csv"
    }
  },
  "interpretation": "AI-written interpretation",
  "reflection_question": "...",
  "challenge": {
    "assumption": "...",
    "question": "..."
  },
  "action": {
    "action": "...",
    "reason": "..."
  },
  "trust": {
    "quote_verified": true,
    "quote_id": "T012",
    "candidate_count": 7,
    "quote_authority": "organizer_provided_csv",
    "rendered_from_backend": true,
    "ai_written_sections": [
      "understanding",
      "interpretation",
      "reflection_question",
      "challenge",
      "action"
    ]
  }
}
```

### Safety response

The frontend receives this shape instead of the mentor/challenge format when the safety path fires:

```json
{
  "status": "safety",
  "message": "...",
  "helplines": [
    {"name": "Tele-MANAS", "number": "14416"},
    {"name": "Tele-MANAS toll-free", "number": "1800-89-14416"},
    {"name": "Emergency Response Support System", "number": "112"}
  ],
  "challenge_available": false
}
```

### Growth

```http
GET /api/growth?days=30
PUT /api/growth/check-in
```

The growth API returns:

```text
reflection_themes_observed
weekly_check_ins
lifetime_factor_trends
```

`lifetime_factor_trends` is the frontend-ready data for the five-factor lifetime graph. Each point is one weekly self-report (1–10) and includes point-to-point raw changes for `self_belief`, `fear`, `discipline`, `clarity`, and `resilience`. The backend does not interpret a change as inherently good or bad; the graph should simply show the values over time. The report should label this as **Weekly self-reflection ratings over time** or similar. The first point has `null` changes because there is no previous check-in.

The mentor response does not expose the retrieved diary excerpts. Diary content is used internally to personalize the solution and only the final interpretation/reflection/action are returned to the UI.

It does not claim that chat text objectively measures fear, confidence, self-belief, or any clinical construct.

### Weekly report

```http
GET /api/reports/weekly/2026-10-05
```

A report is generated once per week and persisted, avoiding repeated Gemini calls for the same period.

### Actions

```http
GET  /api/actions
POST /api/actions/{action_id}/complete
```

### Teaching search

```http
GET /api/teachings?query=fear
```

This is a backend data-exploration endpoint. The mentor pipeline still uses the structured Gemini classification + deterministic candidate retrieval flow.

## Deployment: Render + Neon

### Recommended free architecture

```text
Frontend
   ↓
Render Free Web Service (FastAPI)
   ↓
Neon Free Postgres
   ↓
Gemini Developer API (free tier)
```

Do **not** use Render's Free Postgres for this project. Render currently documents that its Free Postgres instances expire after 30 days. Neon currently advertises a Free plan with 1 GB Postgres storage per project and 100 CU-hours/month. Therefore:

- Render = API hosting
- Neon = persistent Postgres database
- Gemini = model API

Render documentation:

- https://render.com/docs/free
- https://render.com/docs/web-services
- https://render.com/docs/health-checks

Neon documentation/announcement:

- https://neon.com/blog/neon-free-plan-1-gb-per-project

### Render settings

The repository already contains [`render.yaml`](render.yaml).

Create a Render Web Service from the repository or use the Blueprint.

The important settings are:

```text
Runtime: Python
Region: Singapore
Plan: Free
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check: /health
```

The Singapore region is chosen to keep the app relatively close to India, and the same-region Neon database is preferable when available.

Set these environment variables in Render:

```text
DATABASE_URL=<Neon connection string>
GEMINI_API_KEY=<Google AI Studio API key>
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FAST_MODEL=gemini-3.1-flash-lite
CORS_ORIGINS=<your frontend URL>
DEMO_USER_ID=demo
SEED_DEMO_ON_STARTUP=true
AUTO_INGEST_TEACHINGS=true
TEACHINGS_CSV_PATH=data/teachings.csv
```

The code normalizes a standard `postgresql://...` Neon URL to the psycopg v3 SQLAlchemy driver automatically.

### Keep Render warm

Render says Free Web Services spin down after 15 minutes without inbound traffic and restart on the next request. UptimeRobot's current Free plan checks monitors every 5 minutes. A monitor against:

```text
https://YOUR-SERVICE.onrender.com/health
```

will normally keep the service receiving traffic. Render's Free workspace allocation is 750 web-service instance hours/month; a single service kept awake for a 31-day month is 744 hours, so it fits narrowly within that allowance.

UptimeRobot:

- https://uptimerobot.com/pricing/
- https://help.uptimerobot.com/en/articles/11360876-what-is-a-monitoring-interval

### Neon connection choice

Paste the pooled/serverless-safe connection string supplied by Neon into `DATABASE_URL`. The backend intentionally keeps its local SQLAlchemy pool small because Render Free has limited RAM and the demo workload is tiny.

## Testing

```bash
pytest -q
```

The included tests cover:

- metadata-based retrieval;
- candidate-ID source guard;
- exact multi-paragraph source rendering;
- local crisis-language detection;
- India helpline presence;
- profile-scoped journal insight editing/deletion;
- observed theme-frequency growth;
- no generated psychological arrows.

For the hackathon audit slide:

```bash
python scripts/source_audit.py T001 T002 T003
```

The script checks whether the selected database records still match their stored source hashes. For a meaningful judging metric, run an actual evaluation suite after the organiser CSV is loaded and report the resulting percentage; do not use a placeholder number.

## Project priorities

### P0

1. Canonical CSV import + retrieval
2. Mentor response with strict `quote_id` guard
3. Journal → relevant context
4. Safety path

### P1

1. Onboarding
2. Challenge My Thinking
3. Weekly check-in/report
4. Demo data

### P2

1. Read aloud in frontend
2. UI polish
3. Optional performance refinements

Do not add vector search, authentication, web search, multi-agent orchestration, or a separate TTS backend unless the team has finished the core flow and still has time.


## Product tabs and data flow

The application navigation has four tabs: **Mentor**, **Journal**, **Growth Journey**, and **Honesty**.

Diary entries are stored once in `journal_entries`; they are not duplicated into a second history table. The `/api/history` endpoint surfaces diary entries, mentor reflections, and actions as one chronological timeline for the History / Progress tab.

For a new problem, the backend uses the current problem to retrieve only relevant journal insights **and the corresponding small set of raw diary excerpts**. Those are passed to Gemini alongside the user profile, recent conversation, and organiser-provided teaching candidates. This keeps the diary useful for personalization without sending the entire diary to Gemini.

### Teaching-grounded solution rule

A mentor solution is valid only when it is grounded in a relevant record from the organiser-provided CSV. Gemini receives 5--7 backend-selected candidates and returns only a `quote_id`. The backend rejects IDs outside the candidate set and fetches the exact canonical passage itself. Gemini's `interpretation` is instructed to explicitly apply the selected teaching to the user's specific problem, and its `action` operationalizes that teaching. If no sufficiently relevant teaching can be retrieved, the backend refuses to fabricate a Vivekananda-based solution and returns a no-source error instead.

## Frontend navigation contract

The visible product tabs are:

1. **Mentor** — problem reflection, teaching-backed tailored solution, Challenge My Thinking, and action.
2. **Journal** — diary entries and editable descriptive insights.
3. **Growth Journey** — streak, total reflections, five-factor lifetime graph, observed theme frequencies, weekly check-in, weekly report, and weekly anchor.
4. **Honesty** — explain exactly what is source material, what is AI-written, how journal context is used, and how growth/safety work.

### Additional endpoints

```text
GET  /api/growth-journey
GET  /api/honesty
```

The Growth Journey endpoint is intentionally frontend-friendly and returns the data needed to render the demo-inspired cards and lifetime five-factor chart in one request.


The Honesty endpoint is deterministic and never calls Gemini.

## Onboarding contract

The onboarding experience is a single welcome screen followed by six focused question cards. The frontend should present one question per card, with a progress indicator and Back/Continue navigation. On the final question, submit the complete payload to `PUT /api/profile/onboarding`.

Questions:

1. **What profession are you in?**
   - Student / Working / Business / Homemaker / Other
   - `profession_other` is required when Other is selected.
2. **How old are you?**
   - Numeric age (`1`–`120`).
3. **What matters most to you right now?**
   - Studies / Career / Family / Relationships / Health / Money / Personal growth
4. **What's troubling you the most right now?**
   - Stress / Fear / Confidence / Motivation / Relationships / Career / Feeling lost / Other
   - `troubling_other` is required when Other is selected.
5. **How do you usually deal with problems?**
   - I face them / I overthink / I avoid them / I ask others / Depends
6. **What would you like to improve about yourself?**
   - Confidence / Focus / Discipline / Courage / Patience / Peace / Decision-making / Other
   - `improve_other` is required when Other is selected.

Recommended frontend behavior:

- Use a centered card similar to the provided onboarding reference.
- One question per screen/card; do not show all six questions at once.
- Use selectable option boxes for fixed answers.
- When Other is selected, reveal a text field directly below the options.
- Keep Continue disabled until the current question has a valid answer.
- Preserve answers when navigating Back.
- Submit only after question 6; the backend stores the answers in the user's profile.
- Do not ask for the five growth sliders during onboarding; those belong to the weekly check-in in Growth Journey.
