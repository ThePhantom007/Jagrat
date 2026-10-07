# Jagrat canonical teaching JSON

Use **one merged JSON file** as the canonical teaching bank. Put it at:

`data/articles.json`

The organiser-provided source text is the source of truth. Keep the passage text exactly as supplied; metadata may be used as retrieval hints but does not override the text.

Preferred record shape:

```json
[
  {
    "slug": "1-1-1-response-to-welcome",
    "title": "1.1.1 RESPONSE TO WELCOME",
    "volume": "VOLUME 1",
    "url": "https://englishbooks.rkmm.org/...",
    "paragraphs": [
      "At the World’s Parliament of Religions...",
      "Sisters and Brothers of America..."
    ],
    "theme": "resilience",
    "emotion": null
  }
]
```

Supported compatibility fields:

- `paragraphs`: preferred; an array of source paragraphs.
- `paragraph`: accepted for teammate exports that store the entire article in one field. Jagrat splits it deterministically on blank lines.
- `url` or `source_url`: accepted for the source link.
- `theme` / `emotion` or `themes` / `emotions`: optional retrieval hints. They are not treated as canonical source text.
- `source_type` and `context`: optional.

## Token policy

The complete JSON file stays local to the backend/database and is never sent wholesale to Gemini.

The backend deterministically retrieves 5–7 candidate passages and sends Gemini only compact exact-text excerpts. Gemini returns a candidate `quote_id`; the backend validates that ID and then fetches the exact canonical passage for display.

## Source-file rule

Do not ship `worthy_quotes.json` as the main source. It is a compact title/slug/volume/quote dataset and does not preserve the richer article structure needed by Jagrat.

Do not use the current `articles.json` from the old teammate export without auditing it first; a checked copy contained repeated identical records. Generate/obtain the complete final merged export, then save that single file as `data/articles.json`.
