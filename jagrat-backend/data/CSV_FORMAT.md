# Canonical teaching CSV format

The organiser-provided CSV is the **source of truth**. Every row imported into the teaching table is treated as a canonical source record; the backend does not independently authenticate, paraphrase, or rewrite it.

## One row = one passage

Do **not** force everything into one-sentence quotations. A record may contain a full multi-paragraph excerpt from a speech, sermon, book chapter, letter, or other organiser-approved source.

### Required columns

```text
id
text
source_type
source_title
```

### Recommended columns

```text
id,text,themes,emotions,challenges,keywords,source_type,source_title,source_volume,source_chapter,source_page,source_section,source_url,context
```

### Field rules

- `id`: stable unique ID such as `T001`, `S014`, etc. Never reuse an ID for a different passage.
- `text`: the exact passage from the organiser-provided source. Preserve punctuation and paragraph breaks. CSV supports quoted multi-line fields.
- `themes`: pipe-separated tags, e.g. `self_belief|fearlessness|resilience`.
- `emotions`: pipe-separated tags, e.g. `fear|self_doubt`.
- `challenges`: pipe-separated problem tags, e.g. `failure|comparison`.
- `keywords`: optional retrieval terms, e.g. `effort|strength|courage`.
- `source_type`: one of `book`, `speech`, `sermon`, `letter`, `interview`, `conversation`, `article`, `other`.
- `source_title`: exact source title supplied by the organisers.
- `source_volume`: volume number/name when applicable.
- `source_chapter`: chapter/section label when applicable.
- `source_page`: page or page range, e.g. `142-145`.
- `source_section`: additional locator such as a speech section or heading.
- `source_url`: organiser-provided source URL when available.
- `context`: optional surrounding context that helps Gemini understand the passage. This is not displayed as the quote.

### What not to add

Do not add a `verified` or `verification_status` column. The agreed trust rule is simpler: **the organiser-provided CSV is canonical**.

### Multi-paragraph example

```csv
T014,"First paragraph of the organiser-provided passage.

Second paragraph of the same passage.

Third paragraph of the same passage.",self_belief|strength,fear,failure,self_doubt|effort,speech,"Exact source title",I,"Chapter 3","142-145","Section heading","https://...","Optional source context"
```

Keep the whole passage inside the same CSV cell. Do not create separate rows merely because the passage contains multiple paragraphs.
