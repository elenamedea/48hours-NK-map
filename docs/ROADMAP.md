# Roadmap — 48hours Neukölln Map

## Current phase: Post-festival

---

## Phase 1 — Specification and Setup
Goal: Define full spec, resolve all open questions, lock the stack.

- [x] Create project folder structure
- [x] Write initial SPEC.md
- [x] Write initial DECISIONS.md
- [x] Resolve OQ-002: MapLibre GL JS confirmed (ADR-011)
- [x] Resolve OQ-003: offline/tile caching dropped for prototype (ADR-010)
- [x] Resolve OQ-004: Lovable for frontend, HF Spaces for pipeline (ADR-014)
- [x] Confirm language: Python for pipeline (ADR-007)
- [x] Confirm database: Supabase, flat 2-table schema (ADR-008, ADR-022)
- [x] Confirm basemap: basemap.de Beta Nachtstyle (ADR-012)
- [x] Confirm admin UI: Gradio on HuggingFace Spaces (ADR-013)
- [x] Initialise GitHub repository
- [x] Create Supabase project and apply schema
- [x] Configure HuggingFace Space with Supabase secrets
- [x] Create Lovable project, enable GitHub sync

Status: Complete

---

## Phase 2 — Scraping and Data
Goal: Build Python scraping pipeline, populate Supabase via Gradio.

Note: Implemented as flat listing-page scraper (ADR-022), not venue-first crawl
as originally planned. All outcomes achieved with a simpler approach.

- [x] Inspect https://48-stunden-neukoelln.de/en/programm page structure
- [x] Build Python scraper (httpx + BeautifulSoup)
  - [x] Scrape /en/programm listing page: all event×day records inline
  - [x] Parse title, time, location, genres, accessibility per event item
  - [x] Handle multi-day events (e.g. "Fri 19:00 - Sun 19:00") — expand to one row per day
  - [x] Scrape venue pages for address and coordinates (Google Maps link)
  - [x] Rate-limit requests (min 2s between requests)
  - [x] Cache raw HTML to disk (24h TTL, gitignored)
  - [x] Deduplicate by (link, day) — upsert with ON CONFLICT
- [x] Build Python geocoder (geopy + Nominatim) — fallback only
  - [x] Scraped Google Maps coordinates as primary source (ADR-018)
  - [x] Nominatim fallback for venues missing coordinates
  - [x] Bounding box validation (Neukölln lat 52.43–52.50, lng 13.39–13.47)
  - [x] Suspect coordinate flagging and manual review via Gradio preview
  - [x] 7 venues manually corrected; 0 suspect coords at launch
- [x] Category extraction
  - [x] 18 categories extracted from /en/programm genre filter
  - [x] Emoji and colour assigned per category (see DECISIONS.md)
  - [x] Written to Supabase categories table
- [x] Build Gradio admin UI on HuggingFace Spaces
  - [x] Scrape events, Enrich with coords, Geocode missing, Run full pipeline
  - [x] Preview panel: event count, geocoding coverage, suspect coords, day breakdown
- [x] Run full pipeline end-to-end
- [x] Verify data: 1387 events, 18 categories, 100% geocoded, 0 suspect coords

Status: Complete

---

## Phase 3 — Frontend Map
Goal: Build interactive map in Lovable, connected to Supabase.

- [x] Set up Lovable project with Supabase integration (anon key, read-only)
- [x] Initialise MapLibre GL JS map
  - [x] Centred on Neukölln (lat 52.481, lng 13.435, zoom 14)
  - [x] basemap.de Beta Nachtstyle as primary basemap
  - [x] basemap.de Grau as fallback basemap
  - [x] © GeoBasis-DE / BKG (CC BY 4.0) attribution always visible
- [x] Load all 1387 events from Supabase with pagination (bypasses 1000-row cap)
- [x] Display events as location pins (351 unique locations)
  - [x] Native MapLibre clustering for dense areas
  - [x] Pins colour-coded: single genre uses category colour, multi-genre uses black
  - [x] Emoji on pin: category emoji or 🍥 for multi-genre
  - [x] 44×44px touch targets
- [x] Event detail bottom sheet on pin tap
  - [x] All events at location, sorted by title then day
  - [x] Day labels: Fri 3 Jul / Sat 4 Jul / Sun 5 Jul
  - [x] Start and end times
  - [x] Genre chips with emoji
  - [x] ♿ / ♿🚾 / 🚾 accessibility markers
  - [x] Event link opens festival site in new tab
- [x] Foldable legend (Interactive / Artsy / 🍥 Multiple genres)
- [x] Festival theme info button (OUT/SIDE/IN)
- [x] Compass (MapLibre NavigationControl)
- [x] Mobile-first layout: full viewport, bottom bar filters, safe-area aware
- [x] Tested on Android Chrome during festival weekend

Status: Complete

---

## Phase 4 — Filtering
Goal: Add day, category, and open-now filtering.

- [x] Genre filter chips (18 categories with emoji)
- [x] Day filter (Fri 3 Jul / Sat 4 Jul / Sun 5 Jul)
- [x] Open now filter (device time vs event start/end time, festival dates only)
- [x] Combined filters (all active filters apply together)
- [x] Clear all filters button

Status: Complete

---

## Phase 5 — QA and Launch
Goal: Verify data, test on device, share link before festival opens.

- [x] Run final pipeline and verify data completeness in Supabase
- [ ] Full end-to-end test on iOS Safari
- [x] Full end-to-end test on Android Chrome
- [x] Verify basemap.de attribution visible
- [x] Verify all filters work correctly with real data
- [x] Share Lovable app link: https://nk-48hours-map.lovable.app
- [x] App used successfully across full festival weekend (3–5 July 2026)

Status: Complete (iOS Safari test deferred to post-festival)

---

## Post-festival — Open tickets

### Data quality
- [ ] Coordinate accuracy audit: cross-check ~362 venue pins against
      Google Maps search by name; a small portion appear slightly offset

### Frontend enhancements
- [ ] Google Maps navigation link per event: open
      `https://www.google.com/maps/dir/?api=1&destination={location}, Berlin, Germany`
      in new tab from event bottom sheet
- [ ] Route planning: allow users to select multiple venues and generate
      a walking route; evaluate MapLibre routing (OSRM)
- [ ] iOS Safari QA: full end-to-end test (pins, bottom sheet, filters,
      open-now, attribution, navigation link)

### Infrastructure
- [ ] Migrate Supabase to self-hosted PostgreSQL on VPS
- [ ] Deploy frontend to custom domain (Netlify or VPS)
- [ ] Evaluate PWA and offline support for next edition
- [ ] Evaluate Lovable → custom React codebase if significant changes needed
- [ ] Evaluate Docker containerisation for full local stack

### Documentation
- [ ] Run OpenWiki on final codebase
- [ ] Create public GitHub repo (pipeline, parsers, schema, specs)
- [ ] Write README for current repo (technical + lessons learned)
- [ ] Write README for public repo

### Frontend improvements (post-festival backlog)
- [ ] Multi-select category filter: allow selecting more than one genre
      simultaneously; pins shown if they match any selected genre
- [ ] Remove emojis from category filter chip labels; keep emoji only
      on pins and in the legend
- [ ] Rename legend colour group "Artsy" (#FA6AEB) → "Exhibitions"
      (update ADR-023 accordingly)
- [ ] Theme info button: replace festival logo fetch with a styled button —
      black circular background, white "i" character, white circle outline
- [ ] Google Maps navigation link in bottom sheet: add a "Navigate →"
      link directly under the location name (once per location, not per
      event) opening https://www.google.com/maps/dir/?api=1&destination=
      {location},+Berlin,+Germany in a new tab
