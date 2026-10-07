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
  -> backend ingestion/chunking (cover metadata and tiny fragments flagged, never deleted)
  -> deterministic retrieval (BM25 over small windows + Vivekananda-vocabulary bridge)
  -> 5–7 candidate passages from different articles
  -> compact exact-text excerpts to Gemini
  -> Gemini returns quote_id only
  -> candidate-ID validation
  -> backend fetches full exact passage
  -> personalised interpretation / reflection / action
```

Full canonical passages are never sent to Gemini unless they happen to be shorter than the excerpt ceiling. This keeps the free Gemini API usage focused on reasoning instead of repeatedly transmitting the entire source bank.

## How retrieval works

Retrieval is deterministic and local (no embeddings, no extra API calls):

- **Windows, not whole passages.** Each canonical passage (up to ~900 words) is indexed as 60–150-word windows and ranked by its best window, so a focused teaching inside a long multi-topic lecture is not diluted. The user is still shown the full canonical passage.
- **BM25 with light stemming** (`fail`/`failed`/`failing`), so rare, meaningful words count more than common ones (`work`, `mind`, `life`).
- **Vocabulary bridge.** Modern wording ("I failed my exam, I'm not capable") is widened with the words Vivekananda actually uses on those concerns (weakness, strength, faith, fearless, arise, awake, …) at a lower weight than the user's own words. This only widens the *query*; it never alters or invents source text. The lexicon lives in `app/services/retrieval.py` (`BRIDGE`) and is easy to extend.
- **Informative-term coverage.** A window only qualifies if it matches enough informative (rare) query terms; ubiquitous words alone never make a passage relevant.
- **Relevance gate.** A query with no recognised human concern (e.g. a laptop question) needs very strong lexical evidence, otherwise Mentor returns `teaching: null` with the Trust Panel note.
- **Diversity.** At most 2 candidates per source article.
- **Down-ranked, not removed:** salutation/sign-off letters. **Flagged and never offered:** the COVER metadata (`source_type = front_matter`) and passages under 30 words (`fragment`). They stay in the database.
- **Stored tags** are inferred with whole-word matching and a frequency floor (previously raw substring matching tagged almost every passage with almost every theme). Changing `RETRIEVAL_METADATA_VERSION` refreshes stored tags on the next startup of an existing deployment.

All JSON passages are treated as authentic organiser-provided teachings; retrieval makes no authorship judgements.

Known limit: this is lexical retrieval. It cannot match meaning when the user's words and the corpus share no vocabulary, so the Gemini step still decides whether a candidate genuinely fits and may return `null`. Embedding-based re-ranking is the natural next upgrade.

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

- **Render/Postgres:** set `DATABASE_URL` to a persistent Postgres database (Neon or Render Postgres); `postgres://` and `postgresql://` URLs are converted to the psycopg3 driver automatically. `render.yaml` pins Python 3.12 and sets `ENVIRONMENT=production`. On startup the app logs warnings for SQLite in production (ephemeral disk), a missing `GEMINI_API_KEY`, and localhost-only `CORS_ORIGINS`.
- The canonical import loads existing rows in one query and commits once; startup skips the import entirely when the data and retrieval-metadata version are unchanged (about 4 s warm start, ~130 MB RAM).
- **Safety scope:** the local crisis patterns intentionally cover English and romanised Hinglish only (enforced by a test).

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

## Patch notes (post-review)

- **First-message safety:** `POST /api/mentor` now honours the model's `risk` assessment (previously only continue/retry/challenge/vs-me/journal did). A flagged first message marks the conversation `risk_flag` and returns the safety response. Local patterns were extended (e.g. "I want to die", "take my own life", "better off without me", "no point in living"), and "I can't keep going to/with …" no longer triggers.
- **Source guard:** quoted text is now detected as properly paired quotes (two short quoted words no longer look like one long quote), and a quotation that is the user's own wording is allowed. Invented/attributed quotations are still rejected. Mentor and challenge prompts now tell the model not to use quotation marks.
- **Teaching payload:** `teaching` now also carries `word_count`, `preview` (first ~90 words of the exact text) and `is_letter`, so the frontend can collapse long passages. `quote` is still the full, unmodified canonical passage.
- New tests: `tests/test_first_message_safety_and_quote_guard.py`. These changes were validated with stubbed unit checks only; run `pytest -q` before deploying.

## Verification scripts

- `python scripts/smoke_http.py` — zero-token HTTP smoke test (Gemini key forced empty, throwaway SQLite DB).
- `python scripts/live_gemini_check.py sdk|mentor|vs` — call-capped live Gemini check (use a separate test key; `MAX_CALLS` env var, default 4).
