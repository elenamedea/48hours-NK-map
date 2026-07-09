# Specification — 48hours Neukölln Map

## Overview
A mobile-first web app that scrapes all events from the 48hours Neukölln
festival (July 3-4-5 2026), tags them with the official festival categories,
and displays them on an interactive map of Neukölln. Users can filter by
category, day, and opening status, and view event details on mobile.

The app is split into two layers:
- Pipeline layer: Python scraping and data processing, hosted on
  HuggingFace Spaces (Gradio), writing to Supabase (PostgreSQL)
- Frontend layer: React/TypeScript app built in Lovable, reading from
  Supabase, hosted on Lovable for the prototype

## Users
- Elena and anyone she shares the app link with
- Primary use: on mobile during the festival in Neukölln

## Core features

### 1. Event scraping
- Scrape all festival events from https://48-stunden-neukoelln.de/en/programm
- Run manually once before the festival via Gradio UI on HuggingFace Spaces
- Acceptance criteria:
  - All events scraped from the official English-language festival website
  - Each event includes: title, venue, address, one or more categories,
    description, opening times per day; coordinates held at venue level
  - Duplicates detected and removed (slug-based dedup)
  - Scraping is rate-limited and respectful (min 2s between requests)
  - Results stored in Supabase — no live scraping during festival
  - Scrape can be re-run manually to catch updates before July 3

### 2. Geocoding
- Primary coordinate source: lat/lng scraped from venue pages via
  Google Maps link (format: ?query=lat,lng). These are festival-authoritative
  coordinates accurate to courtyards and rear buildings.
- Fallback: OpenStreetMap Nominatim for venues where the Google Maps link
  is missing or malformed.
- Acceptance criteria:
  - Every venue has lat/lng stored in Supabase
  - Primary source is the Google Maps link on the venue page (ADR-018)
  - Nominatim fallback used only when primary source is absent or malformed
  - Nominatim queries use Berlin, Germany context; rate-limited to 1 req/s
  - All coordinates validated against Neukölln bounding box
    (lat 52.43–52.50, lng 13.39–13.47); out-of-bounds flagged as suspect
  - Coordinate provenance tracked in venues.geocode_source
    (scraped | nominatim | manual, plus _suspect variants)
  - Suspect and null coordinates surfaced in Gradio preview for manual review

### 3. Interactive map
- Display all festival venues as pins on a map of Neukölln
- Map library: MapLibre GL JS
- Basemap: basemap.de Beta Nachtstyle (dark, mobile-optimised)
  - Primary: https://basemap.de/data/produkte/web_vektor/styles/bm_web_drk.json
  - Fallback: https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json
  - Attribution: © GeoBasis-DE / BKG (CC BY 4.0) — must appear on map
- Acceptance criteria:
  - All venues displayed as pins centred on Neukölln district
  - Pins colour-coded and emoji-tagged by official festival category
  - Clicking a pin shows: venue name, address, opening times,
    description, and categories with emoji and colour
  - Map includes foldable legend showing emoji and colour per category
  - Map is mobile-friendly (touch zoom, tap targets)

### 4. Official category tags
- Tags extracted directly from the scraped festival programme
- Each category assigned one emoji and one colour after first scrape
- Acceptance criteria:
  - Category list extracted automatically from scraped programme
  - One emoji and one colour per category, no exceptions
  - Foldable legend displays all categories with emoji on colour background
  - No custom or invented categories
  - Assignments logged in DECISIONS.md as a new ADR after first scrape

### 5. Filtering
- Filter events by category, day, and opening status
- Acceptance criteria:
  - Filter by official festival category
  - Filter by day (Friday July 3 / Saturday July 4 / Sunday July 5)
  - Filter by opening status (open now — uses device time)
  - Filters can be combined
  - Clear all filters in one tap

## Out of scope (prototype)
- PWA / service worker / offline support — deferred to production upgrade
- User accounts or personalisation
- Favouriting or saving venues
- Routing or navigation between venues
- Real-time updates during the festival
- Multi-language support
- Docker containerisation of deployment — all targets are managed
  platforms; a local dev container for the pipeline is in scope (ADR-020)

## Out of scope (permanently)
- Native iOS/Android app

## Upgrade path (post-festival)
- Migrate from Supabase to self-hosted PostgreSQL on VPS
- Migrate frontend hosting from Lovable to custom domain
- Evaluate PWA/offline support at that stage
- Evaluate Docker containerisation at that stage

## Tech stack

### Pipeline
- Language: Python (latest stable)
- Scraping: httpx + BeautifulSoup / lxml
- Geocoding: geopy + Nominatim (OpenStreetMap) — fallback only (ADR-018)
- Database client: supabase-py
- Admin UI: Gradio on HuggingFace Spaces (manual run trigger)

### Database
- Supabase (managed PostgreSQL)
- Schema: four tables — venues, events, categories, event_categories
  (see DECISIONS.md ADR-016)

### Frontend
- Builder: Lovable (AI-generated React/TypeScript)
- Map: MapLibre GL JS
- Basemap: basemap.de Beta Nachtstyle
- Hosting: Lovable (yourapp.lovable.app subdomain for prototype)
- Data source: Supabase (read-only from frontend)

## Rules
- All secrets in .env — never hardcoded, never committed
- Scraping must be rate-limited — no hammering the festival website
- Festival categories must mirror official programme exactly
- basemap.de attribution must appear on every map view
