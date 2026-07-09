# Architecture Decision Records — 48hours Neukölln Map

This file logs all architectural and operational decisions made in this project.
Never delete existing entries. Append new ones at the bottom.

---

## ADR-001
- Date: 2026-06-09
- Title: Inherit architecture from event-logging-map
- Context: The 48hours Neukölln map shares the same core requirements
  as event-logging-map: n8n scraping, emoji category tags, interactive
  map. Rebuilding from scratch would risk the hard deadline.
- Options considered:
  - Build from scratch: maximum flexibility, high time cost
  - Inherit from event-logging-map: faster, proven patterns, lower risk
- Decision: Inherit all patterns from event-logging-map. Only build
  what is genuinely different: festival scraping, frontend, data pipeline.
- Consequences: Any change to shared patterns must be checked against
  event-logging-map to avoid divergence. All inherited agents and skills
  referenced by path, not copied.

---

## ADR-002
- Date: 2026-06-09
- Title: PWA for mobile-first deployment
- Context: Original decision to build a PWA with offline support.
- Status: SUPERSEDED by ADR-010.

---

## ADR-003
- Date: 2026-06-09
- Title: Scrape once, cache in PostgreSQL, no live scraping
- Context: Live scraping during the festival would be unreliable and
  disrespectful to the festival website. Data should be scraped before
  July 3 and cached.
- Options considered:
  - Live scraping during festival: unreliable, hammers the website
  - Scrape once, cache in PostgreSQL: reliable, offline-compatible
  - Static JSON file: simplest, no database needed but less flexible
- Decision: Scrape once via Python pipeline before the festival, cache
  all results in Supabase (PostgreSQL). Scrape can be re-run manually
  for updates via Gradio UI on HuggingFace Spaces.
- Consequences: Scraping pipeline must be built and tested before the
  festival to allow time for verification. Supabase schema must support
  all event fields including coordinates.

---

## ADR-004
- Date: 2026-06-09
- Title: Categories extracted from scraped programme
- Context: Official festival categories are defined by 48hours Neukölln
  and must be used exactly. Extracting from the scrape avoids manual
  errors and keeps categories in sync with the official programme.
- Options considered:
  - Manual category list: error-prone, requires maintenance
  - Extract from scraped programme: automatic, always in sync
- Decision: Categories extracted directly from scraped festival programme.
  Each category assigned one emoji and one colour after extraction.
- Consequences: Emoji and colour assignment must happen after first
  successful scrape. Assignment logged in DECISIONS.md as a new ADR.

---

## ADR-005
- Date: 2026-06-09
- Title: Leaflet.js as preferred map library
- Status: SUPERSEDED by ADR-011.

---

## ADR-006
- Date: 2026-06-09
- Title: Deadline-first architecture — simplicity over features
- Context: Every decision must prioritise delivery over completeness.
  Non-critical features must be explicitly deferred.
- Options considered:
  - Full-featured app: risks deadline
  - MVP: scrape + map + categories + filtering — covers core use case
- Decision: Build MVP only. Core features: scraping, map with pins,
  category tags, day and category filtering. Everything else deferred.
- Consequences: Any feature request that risks July 3 must be flagged
  immediately and deferred to post-festival if needed.

---

## ADR-007
- Date: 2026-06-11
- Title: Python as primary language
- Context: Stack decision during spec refinement. The pipeline layer
  (scraping, geocoding, data processing) needed a clear language choice.
- Options considered:
  - Python: strong scraping ecosystem, native Supabase client, Gradio
    for admin UI, fast to prototype
  - Node.js: natural fit for n8n ecosystem but weaker scraping tooling
- Decision: Python (latest stable) for all pipeline and data processing.
  n8n retained as orchestrator only — coordinates pipeline steps but
  does not execute scraping logic itself.
- Consequences: Scraping, geocoding, and Supabase writes all implemented
  in Python. n8n triggers Python scripts via HTTP or subprocess.
- Status: PARTIALLY SUPERSEDED by ADR-015 (n8n dropped entirely).

---

## ADR-008
- Date: 2026-06-11
- Title: Supabase as database for prototype
- Context: Frontend is built in Lovable (React). Lovable has native
  Supabase integration. Self-hosted PostgreSQL would require an API
  proxy layer between the database and the frontend, adding complexity
  before the deadline.
- Options considered:
  - Supabase (managed PostgreSQL): native Lovable integration, zero
    config, free tier sufficient for festival data volume
  - Self-hosted PostgreSQL in Docker: more control, matches original
    architecture, but requires API proxy layer for Lovable frontend
- Decision: Supabase for the prototype. Python pipeline writes to
  Supabase via supabase-py. Lovable frontend reads from Supabase natively.
- Consequences: Supabase credentials must be stored in .env. Migration
  to self-hosted PostgreSQL is the documented upgrade path post-festival.
  Schema design must remain portable (standard PostgreSQL, no
  Supabase-specific features unless explicitly approved).

---

## ADR-009
- Date: 2026-06-11
- Title: Supabase schema — events and categories tables
- Context: Schema must support all event fields, coordinates, per-day
  opening times, and category assignment.
- Decision: Two tables as follows.

  events:
    id              uuid primary key default gen_random_uuid()
    venue_number    integer not null
    name            text not null
    address         text not null
    lat             numeric(9,6)
    lng             numeric(9,6)
    category_id     uuid references categories(id)
    description     text
    opening_fri     text
    opening_sat     text
    opening_sun     text
    scraped_at      timestamptz default now()
    updated_at      timestamptz default now()

  categories:
    id              uuid primary key default gen_random_uuid()
    name            text not null unique
    emoji           text
    colour          text
    created_at      timestamptz default now()

- Consequences: Emoji and colour fields on categories are nullable until
  first scrape completes and assignments are made. Assignment must be
  logged as a new ADR at that time.
- Status: SUPERSEDED by ADR-016.

---

## ADR-010
- Date: 2026-06-11
- Title: Drop PWA and offline support for prototype — pure mobile web
- Context: ADR-002 mandated a PWA with service worker and offline
  tile caching. With Lovable as the frontend builder and the deadline
  at July 3, implementing a full service worker and offline tile cache
  adds significant complexity and risk.
- Options considered:
  - Full PWA with service worker: offline support, installable, high
    complexity, real deadline risk
  - Mobile-responsive web app only: works on mobile browser, no
    offline support, fast to build
- Decision: Drop PWA and offline support entirely for the prototype.
  Deliver a mobile-responsive web app accessible via browser link.
  Offline support deferred to post-festival production upgrade.
- Consequences: ADR-002 is superseded. No service worker, no manifest,
  no offline indicator. Users need a connection to use the app.
  Post-festival upgrade path must include PWA evaluation.

---

## ADR-011
- Date: 2026-06-11
- Title: MapLibre GL JS as map library
- Context: ADR-005 (Leaflet.js) was decided before the frontend
  builder was chosen. With Lovable generating a React/TypeScript
  frontend, the map runs in the browser. MapLibre GL JS is the
  preferred library for vector tile basemaps and is explicitly
  listed as fully supported by basemap.de Web Vektor.
- Options considered:
  - MapLibre GL JS: open source, vector tiles, full basemap.de
    support, excellent mobile performance, no API key required
  - Leaflet.js: simpler, but raster-only, weaker vector tile support,
    less suited to the dark basemap style
  - Mapbox GL JS: polished but requires paid API key above free tier
- Decision: MapLibre GL JS. ADR-005 is superseded.
- Consequences: Lovable must be prompted to use maplibre-gl npm package.
  Map initialisation must reference the basemap.de style JSON URL
  directly (see ADR-012).

---

## ADR-012
- Date: 2026-06-11
- Title: basemap.de Beta Nachtstyle as basemap
- Context: The festival is used on mobile, outdoors, often at night.
  A dark basemap reduces eye strain, saves battery, and makes
  coloured category pins stand out more clearly (glow effect).
  basemap.de is produced by German federal and state authorities,
  is CC BY 4.0, requires no API key, and explicitly supports
  MapLibre GL JS.
- Options considered:
  - basemap.de Beta Nachtstyle (dark): ideal for night mobile use,
    no key, CC BY 4.0, MapLibre-native, German official data
  - basemap.de Grau (grey): more neutral, stable (not beta)
  - OpenFreeMap Positron: clean, no key, but light style
- Decision: basemap.de Beta Nachtstyle as primary.
  Style URL: https://basemap.de/data/produkte/web_vektor/styles/bm_web_drk.json
  Fallback (if beta endpoint is unavailable): basemap.de Grau
  URL: https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json
- Consequences: Style is in beta — URL or behaviour may change before
  July 3. Fallback must be implemented as a one-line config swap.
  Attribution © GeoBasis-DE / BKG must appear on every map view
  (CC BY 4.0 requirement).

---

## ADR-013
- Date: 2026-06-11
- Title: HuggingFace Spaces + Gradio as pipeline admin UI
- Context: The scraping pipeline runs once per year (festival
  programme is published annually). A lightweight admin UI is needed
  to trigger manual scrape runs and inspect results without a full
  backend deployment.
- Options considered:
  - HuggingFace Spaces + Gradio: free, fast to deploy, Python-native,
    no infrastructure to maintain, sufficient for annual manual runs
  - Custom FastAPI admin panel: more control, more work to build
    and host
- Decision: Gradio on HuggingFace Spaces. Provides: manual scrape
  trigger, geocoding trigger, data preview, and error log display.
  All pipeline logic remains in Python; Gradio is UI only.
- Consequences: HuggingFace Spaces must have Supabase credentials
  configured as Space secrets. Gradio app is not public-facing —
  it is an internal tool for pipeline management only.

---

## ADR-014
- Date: 2026-06-11
- Title: Lovable as frontend builder and prototype host
- Context: The frontend needs to be a React/TypeScript app with
  MapLibre GL JS and Supabase integration. Lovable generates this
  stack from prompts, includes native Supabase integration, and
  provides free hosting on a lovable.app subdomain — sufficient
  for the prototype and festival use.
- Options considered:
  - Lovable: AI-generated React, native Supabase, free hosting,
    fast to prototype, GitHub sync for code ownership
  - Build React app manually: full control, higher time cost
  - Streamlit/Gradio with Python map: simpler stack but limited
    map interactivity and no Lovable-grade UI
- Decision: Lovable for the prototype. Frontend hosted on
  lovable.app subdomain. GitHub sync enabled from day one so
  code is owned and portable.
- Consequences: Frontend language is TypeScript/React, not Python.
  Python is pipeline-only. Lovable credit usage must be managed
  (avoid cosmetic iteration cycles that burn credits). Post-festival
  upgrade path is: export from Lovable → deploy to custom domain
  via Netlify or VPS.

---

## ADR-015
- Date: 2026-06-11
- Title: Drop n8n entirely
- Context: n8n was inherited from event-logging-map as a pipeline
  orchestrator. In this project the pipeline is three sequential Python
  scripts (scrape → geocode → extract categories) run once per year
  manually. There is no scheduling, no recurring trigger, and no
  multi-system coordination that would justify a dedicated orchestrator.
  n8n would add infrastructure complexity with no corresponding benefit.
- Options considered:
  - Keep n8n as orchestrator: adds a service to maintain, deploy, and
    credential-manage for zero functional gain over running scripts directly
  - Drop n8n, run Python scripts directly via Gradio: simpler stack,
    fewer moving parts, easier to maintain
- Decision: Drop n8n entirely. Pipeline steps are triggered manually
  via Gradio UI on HuggingFace Spaces. Each step (scrape, geocode,
  categories) is a standalone Python script callable from Gradio.
- Consequences: ADR-007 is partially superseded. n8n-workflow agent
  and n8n-integration skill are retired. docs/workflows/ directory
  is no longer needed. event-logging-map n8n patterns are no longer
  inherited by this project.

---

## ADR-016
- Date: 2026-06-12
- Title: Four-table schema: venues, events, categories, event_categories
  (supersedes ADR-009)
- Context: Live site inspection on 2026-06-12 revealed three facts
  that invalidate the ADR-009 schema: (a) the 2026 festival assigns no
  venue numbers — the number field does not exist on the site; (b) events
  carry multiple official categories, not a single category_id; (c) the
  site separates venues from events — many events are hosted per venue,
  and coordinates are held at venue level, not event level.
- Options considered:
  - Junction table (chosen): correct relational model, enforces FK
    integrity, PostgREST supports nested-select for Lovable queries
  - uuid[] array column on events: no FK enforcement, awkward filtering
    via PostgREST, loses referential integrity
  - Primary-category heuristic (one category per event): drops official
    multi-category data silently, incorrect representation of programme
- Decision: Four tables as follows.

  venues:
    id               uuid primary key default gen_random_uuid()
    slug             text not null unique
    name             text not null
    address          text not null
    lat              numeric(9,6)
    lng              numeric(9,6)
    geocode_source   text
    accessibility    text[]
    scraped_at       timestamptz default now()
    updated_at       timestamptz default now()

  events:
    id               uuid primary key default gen_random_uuid()
    slug             text not null unique
    venue_id         uuid not null references venues(id)
    title            text not null
    description      text
    artist_names     text[]
    opening_fri      text
    opening_sat      text
    opening_sun      text
    scraped_at       timestamptz default now()
    updated_at       timestamptz default now()

  categories:
    id               uuid primary key default gen_random_uuid()
    name             text not null unique
    emoji            text
    colour           text
    created_at       timestamptz default now()

  event_categories:
    event_id         uuid not null references events(id)
    category_id      uuid not null references categories(id)
    primary key (event_id, category_id)

- Consequences: venue_number is dropped — it does not exist in 2026.
  Slug is the natural dedup and upsert key for both venues and events.
  Frontend query pattern is:
    events?select=*,venues(*),event_categories(categories(*))
  Emoji and colour on categories remain nullable until first scrape
  completes and assignments are made (same as ADR-009 consequence).
  Assignment must be logged in DECISIONS.md as a new ADR at that time.

---

## ADR-017
- Date: 2026-06-12
- Title: Scrape strategy — English-only, venue-first crawl with HTML cache
- Context: Site inspection confirmed: (a) the canonical domain is
  https://48-stunden-neukoelln.de (previous docs had the wrong domain
  without "oe" which refuses connections); (b) the 2026 programme is
  published; (c) all content is server-side rendered; (d) English pages
  at /en/ are complete and include venue coordinates; (e) venue count
  is ~500+, not ~300 as previously estimated.
- Options considered:
  - Scrape German pages: unnecessary — English pages are complete
  - Scrape live during festival: ruled out by ADR-003
  - Scrape without caching: re-runs hit the server repeatedly,
    wasteful and disrespectful
  - HTML cache to disk (chosen): idempotent re-runs, 24h TTL,
    respectful to the festival site
- Decision: Canonical scrape source is https://48-stunden-neukoelln.de/en/.
  The crawl is entirely English — no German pages needed.
  Crawl order:
    1. /en/programm index — collect event slugs; seed canonical
       category list from discipline filter
    2. /en/programm/karte — collect venue slugs
    3. Each /en/programm/karte/{slug} — extract venue name, address,
       lat/lng from Google Maps link
       (format: https://www.google.com/maps/search/?api=1&query=52.45074,13.435603),
       accessibility, and list of hosted events
    4. Each /en/programm/{slug} — extract title, description,
       categories, artists, per-day opening times
  Tooling: httpx + BeautifulSoup, minimum 2s between requests.
  Runtime estimate: ~500 venue pages + ~300-500 event pages at 2s/request
  ≈ 35-45 minutes total. Acceptable for a one-off annual run.
  Raw HTML cached to disk keyed by URL path (24h TTL, gitignored).
  Re-runs parse from cache. Upserts keyed on slug (idempotent).
  Errors logged per page; run never aborted on a single-page failure.
- Consequences: Domain corrected in all project docs. Cache directory
  must be added to .gitignore. Pipeline module layout defined in ADR-019.

---

## ADR-018
- Date: 2026-06-12
- Title: Geocoding demoted to fallback-only
- Context: Venue pages embed festival-authoritative coordinates via
  Google Maps links (format: ?query=lat,lng). These coordinates are
  more accurate than address geocoding — especially for courtyards,
  rear buildings, and unlisted entrances common in Berlin Neukölln.
  Nominatim geocoding would introduce unnecessary error where the site
  already provides precise coordinates.
- Options considered:
  - Nominatim as primary (original plan): lower accuracy, rate-limited,
    unnecessary when coordinates are already present
  - Scraped coordinates as primary, Nominatim as fallback (chosen):
    highest accuracy for venues that have the link; Nominatim only for
    exceptions; provenance tracked per venue
- Decision: Primary coordinate source is the scraped Google Maps link
  on each venue page. Nominatim (geopy, 1 req/s, "Berlin, Germany"
  context) is used only when the link is missing or malformed.
  All coordinates validated against the Neukölln bounding box:
    lat 52.43–52.50, lng 13.39–13.47
  Coordinates outside the bounding box are flagged with a _suspect suffix.
  Provenance tracked in venues.geocode_source with values:
    scraped | nominatim | manual (and _suspect variants for each)
  Suspect and null coordinates are surfaced in the Gradio preview
  panel for manual review before launch.
- Consequences: Nominatim rate-limit rule (1 req/s) still applies for
  fallback cases. The geocoder.py module must implement the two-tier
  logic and bounding-box validation. Gradio preview must include a
  geocoding coverage report and suspect coordinate count.

---

## ADR-019
- Date: 2026-06-12
- Title: Python pipeline module layout and Gradio trigger buttons
- Context: With scrape strategy (ADR-017) and schema (ADR-016) confirmed,
  the pipeline package structure and Gradio interface can be defined
  precisely. A clear module layout prevents ad-hoc growth and ensures
  each step is independently testable and triggerable.
- Decision: Pipeline package layout:

  pipeline/
    config.py          — constants: base URL, bounding box, rate limits,
                         cache TTL, Supabase table names
    cache.py           — disk cache: read/write raw HTML keyed by URL path,
                         24h TTL check, gitignored cache/ directory
    scraper/
      index.py         — crawl /en/programm index: event slugs,
                         seed category list
      venues.py        — crawl /en/programm/karte and each venue slug page
      events.py        — crawl each /en/programm/{slug} event page
    parsers/
      venue_parser.py  — extract name, address, Google Maps coords,
                         accessibility, hosted event slugs from venue HTML
      event_parser.py  — extract title, description, categories,
                         artists, per-day times from event HTML
      coord_parser.py  — parse Google Maps query string to (lat, lng) float pair
    geocoder.py        — two-tier geocoding per ADR-018: scraped primary,
                         Nominatim fallback, bounding-box validation,
                         geocode_source assignment
    db.py              — supabase-py upsert helpers for venues, events,
                         categories, event_categories; all operations idempotent
    pipeline.py        — orchestration: calls scraper → parsers → geocoder → db;
                         returns RunResult dataclass
                         (fields: success bool, counts dict, warnings list,
                         errors list)
    gradio_app.py      — Gradio interface: button triggers and preview panels

  Gradio buttons:
    - Scrape venues       — runs scraper/venues.py + venue_parser.py + db.py
    - Scrape events       — runs scraper/events.py + event_parser.py + db.py
    - Geocode missing     — runs geocoder.py for venues where lat/lng is null
    - Preview data        — shows: event and venue counts, geocoding coverage %,
                            category distribution, suspect coordinate list
    - Run full pipeline   — runs all steps in order with streaming log output

  Each step is idempotent (upsert on slug). Any step can be re-run safely.
- Consequences: gradio_app.py is the only entry point deployed to
  HuggingFace Spaces. pipeline.py is the internal orchestrator.
  RunResult dataclass enables Gradio to display structured results
  without parsing log strings. Module boundaries mean each parser
  can be unit-tested independently of network or database.

---

## ADR-020
- Date: 2026-06-12
- Title: Local dev Docker container for the Python pipeline
- Context: Version and software consistency across machines is required
  for pipeline development. All deployment targets are managed cloud
  platforms (Supabase, HuggingFace Spaces, Lovable), so there is no
  self-managed production environment to containerise — Docker can only
  apply to local development. SPEC previously listed Docker as fully
  out of scope for the prototype.
- Options considered:
  - Docker-free with pinned requirements.txt + Python version file:
    lightest, but no isolation from host Python/system packages
  - Local dev container for the pipeline (chosen): one Dockerfile +
    docker-compose.dev.yml, Python version pinned to match HuggingFace
    Spaces; cheap insurance against version drift
  - Full local stack including local Supabase (supabase CLI in Docker):
    maximum parity but heaviest setup, real deadline risk
- Decision: Single dev container for the Python pipeline. Dockerfile +
  docker-compose.dev.yml only. No docker-compose.prod.yml — production
  is managed platforms (deliberate deviation from the global convention
  of maintaining dev and prod compose files, as no prod target exists).
  Python version in the Dockerfile must match the HuggingFace Spaces
  runtime to guarantee dev/deploy parity.
- Consequences: SPEC out-of-scope entry amended (deployment remains
  containerless; local dev container is in scope). .env consumed by
  compose for Supabase credentials. Post-festival full Docker
  evaluation remains on the upgrade path unchanged.

---

## ADR-021
- Date: 2026-06-21
- Title: HuggingFace Space deployed via separate synced clone, not direct
  push from the main repo
- Context: Pushing the main repo's `main` branch directly to the Space's
  git remote requires `--force` every time, because the Space auto-
  initialises its own repo (with a `.gitattributes` for LFS and its own
  README) with unrelated history. Force-pushing repeatedly overwrites
  that initial state and, during initial setup, coincided with the Space
  becoming stuck indefinitely in Building/Starting across multiple
  recreated Spaces — never conclusively proven as the root cause (a
  clean Space recreation without any further force-push resolved it),
  but the practice itself is fragile and not worth repeating regardless.
- Options considered:
  - Force-push main branch directly to the `space` remote (original
    approach): simplest, but destroys the Space's own git history and
    `.gitattributes` on every deploy
  - Separate synced clone with a deploy script (chosen): Space repo
    keeps its own clean, linear history; main repo stays the source of
    truth; a script copies only the deployable files across
- Decision: The Space is cloned once into
  `~/Documents/claude-projects/48hours-neukoelln-pipeline` (sibling to
  this repo, outside version control here). `scripts/deploy_to_hf_space.sh`
  in this repo copies `app.py`, `requirements.txt`, and `pipeline/`
  (stripping `__pycache__`/`*.pyc`) into that clone, commits, and pushes
  normally — no force ever required. The `space` git remote is removed
  from this repo entirely to prevent accidental direct force-pushes.
- Consequences: Every pipeline deploy after a code change requires
  running `scripts/deploy_to_hf_space.sh` followed by `git push` from
  the Space clone (the script does not currently auto-push if a prior
  push attempt silently failed — must verify with `git status -sb`
  showing no `ahead` count after running it). Secrets
  (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) must be re-added under
  the Space's Settings on each fresh Space creation — they do not
  carry over from a deleted Space.

---

## ADR-022
- Date: 2026-06-28
- Title: Flat 2-table schema — events + categories (supersedes ADR-016)
- Context: The 4-table schema (ADR-016) required a two-phase crawl: venue
  pages for coordinates and structure, then individual event pages for
  details. In 2026 the /en/programm listing page renders all event×day
  records inline: title, time, location, genres, and accessibility icons.
  Individual event page scraping is no longer needed. The venues table
  added a layer of indirection with no frontend benefit — the Lovable
  frontend reads flat event rows, not nested venue→events structures.
- Options considered:
  - Keep 4-table schema: preserves relational purity, but venues table
    becomes a staging layer with no query-time purpose; event_categories
    junction adds a JOIN on every frontend request
  - Flat 2-table schema (chosen): all event×day data in one row, genres
    as TEXT[], coordinates directly on the event row; categories table
    retained as a name lookup for emoji/colour assignment
- Decision: Two tables:
    events — one row per event×day; UNIQUE (link, day) as upsert key;
             day stored as full date string (03.07.2026 etc.) after
             postprocess_days.py converts Fri/Sat/Sun abbreviations;
             genres as TEXT[]; lat/lng directly on the row
    categories — id, name, emoji, colour (genre lookup only)
- Consequences: venues and event_categories tables dropped. Scraping
  simplified to one pass over /en/programm + one pass over venue pages
  for coordinates. Multi-day events (e.g. "Fri 19:00 - Sun 19:00")
  expanded into one row per day by the parser. Supabase 1000-row server
  cap bypassed by paginating with .range() in the Gradio preview.
  ADR-016 is superseded.

---

## ADR-023
- Date: 2026-07-03
- Title: Category visual design — two-colour palette, emoji, and multi-genre pin rule
- Context: 18 official categories needed a visual identity for map pins,
  filter chips, and the legend. A dark basemap (ADR-012) means pin colours
  must be high-contrast and distinct without creating visual noise across
  351 location pins. A per-category unique colour would be unreadable at
  map scale; a two-colour semantic grouping keeps the map scannable.
- Options considered:
  - Unique colour per category (18 colours): too many competing colours on
    a dark basemap; legend becomes unreadable; not useful for navigation
  - Two-colour semantic palette (chosen): groups categories into two
    families; immediately communicates type without reading the label;
    high contrast on dark background
  - Single accent colour: loses all category differentiation
- Decision: Two-colour palette:
    #FA6AEB ("Artsy") — Visual Art, Installation, Photography, Digital Art,
      Film & Video, Public Art, Interdisciplinary Project, Literature &
      Poetry, Perspective, Other
    #FB9130 ("Interactive") — Performance Art, Dance, Music, Workshop,
      Theater, Tour, Art Education, Intervention
  Each category assigned one emoji (see categories table).
  Multi-genre events (genres array length > 1): pin colour #000000 (black),
  emoji 🍥 — visually distinct from both colour families, signals complexity.
  Events with no genre assigned default to "Other" (🧶, #FB9130).
- Consequences: categories.emoji and categories.colour columns populated
  in Supabase. events.pin_colour set to '#000000' and events.emoji to
  '{🍥}' for 643 multi-genre events. Legend groups labelled "Artsy" and
  "Interactive" with a "🍥 Multiple genres" entry at top.
