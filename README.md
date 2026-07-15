# 🗺️ 48hours Neukölln Map 🗺️

Hi people! 

Since 2013 I am a regular visitor of the 48h NK festival, a definite summer highlight for me. My experience during the festival is quiet similar to a treasure hunt and a min. of 15K steps per day is guaranteed.

The last couple of years I was really missing a mobile-first festival interactive map and even scraped the programme previously, but did not managed to finalise the map. Apparently 2026 was the year to implement it and navigate conveniently through my screen.

<div align="center">
*(fun fact: 2026 was also the first year that the festival collaborate with [WALLS](https://walls.link/en) on an interactive map)*
</div>

It is a rather simple implemention consisting of scraping all the events through the 3 days of the festival from the official programme, geocoding venue locations, and plotting them under a [dark-mode map](https://basemap.de/beta/beta-styles/) with day, genre, and open-now filtering (*cf*. screen record).

<div align="center">
https://github.com/user-attachments/assets/2cd346ba-4d6d-454a-9308-c48bcca24715
</div>

For each event its category and accessibility status is presented and by clicking it you redirect under the respective page of the official festival's website.

The app is aimed for any visitor willing to scroll around the lively neighbourhood of Neukölln and enjoy art, connect with people, discover purposeful communities, challenge their horizons, or just spice up their weekend by *"hunting the NK-gems 💎"*.

Feel free to share any feedback with me; I will come back with an updated version for 2027 festival, and who knows which else similar use case. ;)

<div align="right">
*Anthropic models (Sonnet 4.6, 5 and Fable 5) assisted me in planning and implementation*
</div>
---

## Live app

https://nk-48hours-map.lovable.app

<video src="https://raw.githubusercontent.com/elenamedea/48hours-NK-map/main/48hours-NK-map-04072026.mp4" controls width="600"></video>

---

## What this repo contains

The data pipeline that powers the map:

| Path | Contents |
|------|----------|
| `pipeline/` | Scraper, parsers, geocoder, Supabase client, Gradio admin UI |
| `supabase/schema.sql` | PostgreSQL schema (2 tables: events, categories) |
| `scripts/postprocess_days.py` | Converts day abbreviations to date strings post-scrape |
| `docs/` | SPEC, DECISIONS (ADR log), ROADMAP |
| `Dockerfile` + `docker-compose.dev.yml` | Local dev environment |

The frontend (React/TypeScript, MapLibre GL JS) is maintained separately
in a [Lovable](https://lovable.dev) project.

---

## Architecture

Python pipeline → Supabase (PostgreSQL) → React/MapLibre frontend (Lovable)

| Layer | Stack |
|-------|-------|
| Scraping | Python, httpx, BeautifulSoup/lxml |
| Geocoding | Scraped Google Maps coords (primary), geopy/Nominatim (fallback) |
| Database | Supabase — 2 tables: `events`, `categories` |
| Admin UI | Gradio on HuggingFace Spaces |
| Frontend | React/TypeScript, MapLibre GL JS, basemap.de dark style |

### Database schema

**`events`** — one row per event×day, unique on `(link, day)`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | primary key |
| title | text | |
| day | text | e.g. `03.07.2026` |
| start_time / end_time | text | HH:MM |
| location | text | venue name |
| address | text | |
| lat / lng | float | |
| geocode_source | text | scraped / nominatim / manual + _suspect variants |
| genres | text[] | official festival categories |
| pin_colour | text | `#000000` for multi-genre events |
| link | text | relative path on festival site |
| accessibility | bool | wheelchair accessible |
| toilet | bool | accessible toilet on site |

**`categories`** — genre lookup

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | |
| name | text | official category name |
| emoji | text | |
| colour | text | `#FA6AEB` (Exhibitions) or `#FB9130` (Interactive) |

---

## Setup

### Requirements

- Python 3.12+
- A [Supabase](https://supabase.com) project with the schema applied

### Install

```bash
pip install -r pipeline/requirements.txt
cp .env.example .env
# Fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

### Apply the schema

Run `supabase/schema.sql` in the Supabase SQL Editor.

### Run the admin UI locally

```bash
python -m pipeline.gradio_app
```

Or with Docker:
```bash
docker compose -f docker-compose.dev.yml up
```

### Building the docs

```bash
pip install -r requirements-docs.txt
mkdocs build --strict
mkdocs serve
```

### Pipeline steps

Run in order via the Gradio UI buttons:

1. Scrape events — fetches /en/programm, upserts all event×day rows
2. Enrich venues — scrapes venue pages, patches address + coordinates
3. Geocode missing — Nominatim fallback for remaining null coordinates
4. postprocess_days.py — converts Fri/Sat/Sun to date strings

```bash
python scripts/postprocess_days.py
```

---
### Deploy to HuggingFace Spaces

1. Create a new Space (Gradio SDK, Python 3.12)
2. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as Space secrets
3. Push this repo to the Space's git remote

---
### Technical notes

- Multi-day events: time ranges like `Fri 19:00 - Sun 19:00` are expanded
  into one DB row per day by `event_listing_parser.py`
- Supabase row cap: PostgREST returns max 1000 rows regardless of `.limit()`;
  use `.range()` pagination to fetch all rows
- Upsert deduplication: Postgres rejects `ON CONFLICT` when the same key
  appears twice in one batch; deduplicate `(link, day)` client-side before upserting
- Coordinate validation: all scraped coords validated against Neukölln
  bounding box (lat 52.43–52.50, lng 13.39–13.47); outliers flagged as `_suspect`

---
### License

See MIT license.

## Feedback

Used the app during the festival? I would love to hear from you.
Submit pain points, missing features, or general suggestions here:
[https://github.com/elenamedea/48hours-NK-map/issues/16](https://github.com/elenamedea/48hours-NK-map/issues/16)
