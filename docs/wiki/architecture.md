# Architecture Overview

## Three layers

```
Python pipeline  →  Supabase (PostgreSQL)  →  React/MapLibre frontend
   (this repo)         (managed DB)             (Lovable, separate repo)
```

- **Pipeline** (`pipeline/`) — scrapes the festival programme, geocodes
  venues, writes to Supabase. Python, run manually once per year when the
  programme is published. See [ADR-007](../DECISIONS.md#adr-007) for why
  Python, and [Pipeline Data Flow](data-flow.md) for how the steps chain
  together.
- **Database** — Supabase (managed PostgreSQL), chosen for native Lovable
  integration ([ADR-008](../DECISIONS.md#adr-008)). Two tables, flat
  schema ([ADR-022](../DECISIONS.md#adr-022)) — see [Database Schema](schema.md).
- **Frontend** — React/TypeScript, MapLibre GL JS, built and hosted via
  Lovable ([ADR-014](../DECISIONS.md#adr-014)), dark basemap.de basemap
  ([ADR-012](../DECISIONS.md#adr-012)).

## This repo is pipeline-only

There is no frontend source here — no `package.json`, no `.tsx`/`.ts`
files. The frontend lives entirely in Lovable and is GitHub-synced from
Lovable's side, not committed to this repo. If you're looking for map/UI
code, it isn't in this tree.

## Admin UI

The pipeline is triggered manually through a small Gradio app
(`pipeline/gradio_app.py`), deployed to a HuggingFace Space
([ADR-013](../DECISIONS.md#adr-013)). It exposes five buttons — scrape
events, enrich venues, geocode missing, run full pipeline, preview data —
and is an internal tool, not public-facing.

## Where to look next

- [Pipeline Data Flow](data-flow.md) — the four-step run, module by module
- [Database Schema](schema.md) — what's in `events` and `categories`
- [Running the Pipeline](running-the-pipeline.md) — local setup and deploy
- [API Reference](../reference/index.md) — exact function signatures
