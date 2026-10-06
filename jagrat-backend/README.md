# Jagrat Backend

FastAPI backend for Jagrat — a source-grounded AI reflection and mentoring application.

## Canonical source

The organiser-provided JSON teaching bank is the source of truth. Canonical passages are stored exactly as supplied. Gemini never writes the displayed source passage; it returns a `quote_id` chosen from backend-provided candidates.

Use one merged source file at `data/articles.json`. The importer accepts teammate records using `paragraph` instead of `paragraphs`, and `url` instead of `source_url`. For multiple teammate exports, merge them once into the canonical file rather than importing separate files one after another.

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

## Build the canonical source file

Use the richer `paragraphs[]` + `url` export as the text/URL base, then merge optional themes/emotions from the other export. The repo includes a conservative merge utility:

```bash
python scripts/merge_source_json.py source_with_paragraphs.json source_with_tags.json -o data/articles.json
```

It accepts JSON arrays, single JSON objects, or NDJSON. Exact duplicates are collapsed; source-text conflicts for the same slug/title/volume stop the merge unless you explicitly use `--prefer-longest` after reviewing the conflict. The script never rewrites source text.

## Import/check the source

```bash
python scripts/audit_articles.py data/articles.json
python scripts/ingest_articles.py data/articles.json --replace
```

The importer deduplicates exact duplicate article records and preserves every unique source passage exactly. If a large number of duplicates are detected, treat that as a source-export warning rather than silently assuming the missing content exists.


## Reliability and deployment safeguards

- `CORS_ORIGINS` is marked with `NoDecode` so comma-separated environment variables load correctly under `pydantic-settings`.
- Gemini/provider failures surface as HTTP 503 rather than 500. Requests and journal text are persisted before provider calls so users can retry after quota/outage errors.
- Journal entries that cannot yet be analysed return a `202` with `analysis_status: pending`; the frontend can call `POST /api/journal/{entry_id}/analyze` later.
- Mentor reflections that fail during generation remain resumable/retryable; `POST /api/mentor/{conversation_id}/retry` retries the initial generation.
- Canonical source sync is non-destructive. Missing/changed records are marked inactive; historical conversations and saved teachings are not physically deleted.
- Demo seeding is opt-in (`SEED_DEMO_ON_STARTUP=false` by default). Render production configuration disables it.
- Anonymous profiles use an opaque access token returned once by `POST /api/profile`. Send it using `X-Profile-Token: <token>` or `Authorization: Bearer <token>`. No password/login flow is required. Legacy `X-Profile-Id` access is disabled by default.
- Mentor AI-written text is scanned for source attribution/long quoted text. A violating model response is discarded and a correction generation is attempted; if both fail, the user receives a 502 and no unsafe response is persisted.
- If no sufficiently relevant canonical teaching is found, Mentor returns a normal response with `teaching: null` and an explicit Trust Panel note instead of raising an error or inventing a source.

## Testing provider failures

The test suite includes simulated Gemini failures for Mentor and Journal flows. Run `pytest -q` to verify the failure behavior without consuming Gemini quota.

## Test

```bash
PYTHONPATH=. python -m compileall app tests scripts
PYTHONPATH=. python -m pytest -q
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

## Vivekananda vs Me

The Mentor area now includes a separate `Vivekananda vs Me` reflection mode. The user writes their own view or belief; deterministic retrieval supplies relevant organiser-provided passages; Gemini compares the user's position with the retrieved teaching; and the backend renders the exact canonical passage selected by `quote_id`. AI-written fields contain no source quotation or invented Vivekananda attribution.

API:

- `POST /api/vivekananda-vs-me` — create a comparison.
- `GET /api/vivekananda-vs-me/{comparison_id}` — restore a saved comparison.
- `GET /api/history?item_type=vivekananda_vs_me` — include comparisons in History.

The comparison also contributes its observed themes to Growth Journey and counts as a reflection.

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
