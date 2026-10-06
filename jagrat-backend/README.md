# Jagrat Backend

FastAPI backend for Jagrat — a source-grounded AI reflection and mentoring application.

## Canonical source

The organiser-provided JSON teaching bank is the source of truth. Canonical passages are stored exactly as supplied. Gemini never writes the displayed source passage; it returns a `quote_id` chosen from backend-provided candidates.

## JSON source format

Place the organiser file at:

`data/articles.json`

See `data/JSON_FORMAT.md`.

## Token-efficient teaching pipeline

```text
JSON source (local)
  -> backend ingestion/chunking
  -> deterministic retrieval
  -> 5–7 candidate passages
  -> compact exact-text excerpts to Gemini
  -> Gemini returns quote_id only
  -> candidate-ID validation
  -> backend fetches full exact passage
  -> personalised interpretation / reflection / action
```

Full canonical passages are never sent to Gemini unless they happen to be shorter than the excerpt ceiling. This keeps the free Gemini API usage focused on reasoning instead of repeatedly transmitting the entire source bank.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

## Import/check the source

```bash
python scripts/ingest_articles.py data/articles.json --replace
```

The importer deduplicates exact duplicate article records and preserves every unique source passage exactly. If a large number of duplicates are detected, treat that as a source-export warning rather than silently assuming the missing content exists.

## Test

```bash
python -m compileall app tests scripts
pytest -q
```

## Audit the JSON source

Before ingestion, run:

```bash
python scripts/audit_articles.py data/articles.json
```

The audit reports input records, unique articles, duplicate records, and resulting passages. Exact duplicates are removed at ingestion because they do not add source content. A large duplicate count should be treated as a likely export problem and checked with the source-data owner.


## Continue a reflection later

A mentor reflection is persisted as soon as it is created. The frontend can call:

- `GET /api/mentor/sessions?status=active` to render a "Continue Reflection" section.
- `GET /api/mentor/{conversation_id}` to restore the full conversation state.
- `POST /api/mentor/{conversation_id}/continue` to add another turn to the same reflection.

Session summaries include a status (`active`, `completed`, or `safety`), a preview, last activity timestamp, and a `resumable` flag. Completed or safety-flagged reflections cannot be continued. No duplicate conversation is created when resuming.

## Engagement additions

- Reflection helpful/not helpful feedback
- Resume a saved mentor conversation later
- Action follow-up outcomes: completed / partially completed / not completed
- Saved canonical teachings / personal Teaching Library
- Optional active personal reflection goal used by Mentor when relevant
- History search/filtering by type, text, and theme
- A deterministic Today's Reflection prompt
- Internal AI request tracing via `scripts/audit_traces.py` (not exposed as a public endpoint)

No separate “Why this teaching?” feature is included.

## Personal reflection goal

The user may set one active goal from `/api/growth/goal`. The goal is stored separately from onboarding and is provided to Mentor as optional context. It should sharpen the framing or concrete action when relevant, without appearing as a hidden-profile dump in the response.

## Teaching Library

Saved canonical teachings are available under `/api/teachings/saved` and are also included in `/api/growth-journey` as `saved_teachings` so the Growth Journey frontend can render a "My Teachings" section without another fetch.
