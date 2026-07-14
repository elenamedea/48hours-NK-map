# Running the Pipeline

## Prerequisites

- Python 3.12 (matches the HuggingFace Space runtime, per
  [ADR-020](../DECISIONS.md#adr-020))
- A Supabase project with `supabase/schema.sql` applied
- `.env` with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (copy from
  `.env.example`)

## Local install

```bash
pip install -r pipeline/requirements.txt
cp .env.example .env   # fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

## Running via Gradio

```bash
python -m pipeline.gradio_app
```

Opens the admin UI locally with five buttons: **Scrape events**,
**Enrich venues**, **Geocode missing**, **Run full pipeline**, **Preview
data**. See [Pipeline Data Flow](data-flow.md) for what each one does.

## Running via Docker

```bash
docker compose -f docker-compose.dev.yml up
```

Serves the same Gradio app on `localhost:7860` inside a container pinned
to the same Python version as the deployed Space
([ADR-020](../DECISIONS.md#adr-020)).

## Re-running safely

Steps 1–3 (`run_events`, `run_enrich`, `run_geocode`) all upsert on a
stable key and can be re-run freely. `scripts/postprocess_days.py` is the
one exception: running it twice, or re-scraping after it's already run
once, reintroduces `Fri`/`Sat`/`Sun` rows that collide with the converted
date rows on the next postprocess pass. Delete the converted rows first:

```sql
DELETE FROM events WHERE day IN ('03.07.2026', '04.07.2026', '05.07.2026');
```

## Deploying to HuggingFace Spaces

This repo doesn't include a deploy script — bring your own Space:

1. Create a new Space (Gradio SDK, Python 3.12, per
   [ADR-013](../DECISIONS.md#adr-013))
2. Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` as Space secrets
3. Push this repo (or just `pipeline/` + `requirements.txt`) to the
   Space's git remote
