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
