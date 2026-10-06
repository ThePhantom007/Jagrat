# Jagrat canonical teaching JSON

The organiser-provided JSON is the canonical source of truth.

Expected input is an array of objects:

```json
[
  {
    "title": "3.1.2 THE FREE SOUL",
    "volume": "VOLUME 3",
    "paragraphs": [
      "Paragraph one...",
      "Paragraph two..."
    ]
  }
]
```

Optional fields supported: `source_type`, `source_url`, and `context`.

Do not modify the source text. Jagrat preserves each passage exactly in its database. The ingestion layer may add stable IDs and derived retrieval metadata, but it never rewrites canonical text.

## Token policy

The complete JSON file remains local to the backend/database. It is **never sent wholesale to Gemini**.

The backend retrieves 5–7 relevant canonical passages and sends Gemini only a compact exact-text `excerpt` from each candidate. The frontend receives the full exact passage only after Gemini returns a candidate `quote_id`.
