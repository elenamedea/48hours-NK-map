# Pipeline Data Flow

The pipeline runs as four sequential steps, each idempotent (safe to
re-run — upserts on a stable key rather than blind inserts). All four are
wired to buttons in `pipeline/gradio_app.py`
([reference](../reference/gradio-app.md)); `btn_run_full` runs steps 1–3
back to back.

## 1. Scraping the programme — `run_events()`

`pipeline/pipeline.py::run_events` →
[`scraper/programm.py::scrape`](../reference/scraper-programm.md) →
[`parsers/event_listing_parser.py::parse_items`](../reference/parsers-event-listing-parser.md)

Fetches the single `/en/programm` listing page (cached to disk via
[`cache.py`](../reference/cache.md), 24h TTL). `programm.py` also pulls
the canonical genre list from the page's discipline `<select>`.
`event_listing_parser.parse_items` walks each `eventplace__item` block and
extracts title, link, location, time range, genres, and
accessibility/toilet icons. Cross-day time ranges (e.g. `Fri 19:00 - Sun
19:00`) are expanded into one record per day by `_expand_days` — unless
the range ends at `00:00`, which is treated as ending at midnight on the
start day only. Results are upserted via
[`db.py::upsert_categories`](../reference/db.md) and
`db.py::upsert_events`.

## 2. Enriching with venue data — `run_enrich()`

`pipeline.py::run_enrich` →
[`scraper/venues.py::scrape`](../reference/scraper-venues.md) →
[`parsers/venue_parser.py::parse`](../reference/parsers-venue-parser.md) +
[`parsers/coord_parser.py::parse`](../reference/parsers-coord-parser.md)

Crawls `/en/programm/karte` for venue slugs, then each venue page.
`venue_parser.parse` extracts name, address, and the embedded Google Maps
link; `coord_parser.parse` pulls `lat,lng` out of that link's `query`
parameter and validates it against the Neukölln bounding box
(`config.BBOX`), tagging out-of-box coordinates `scraped_suspect`
instead of `scraped` ([ADR-018](../DECISIONS.md#adr-018)). Matching
events are patched by `location` name — there's no venue table to join
against ([ADR-022](../DECISIONS.md#adr-022) dropped it).

## 3. Geocoding fallback — `run_geocode()`

`pipeline.py::run_geocode` → [`geocoder.py::geocode_missing`](../reference/geocoder.md)

For events still missing coordinates after step 2, deduplicates by
`location` name and geocodes each unique address via Nominatim (1
req/second, per project rate-limit rules), tagging results `nominatim` or
`nominatim_suspect` depending on the bounding-box check. This is a
fallback only — scraped Google Maps coordinates are always preferred
([ADR-018](../DECISIONS.md#adr-018)).

## 4. Postprocessing days — `scripts/postprocess_days.py`

Run separately, not from Gradio. Converts the `Fri`/`Sat`/`Sun` day
abbreviations written by step 1 into full festival dates (`03.07.2026`
etc.). Re-running the full pipeline after postprocessing has already run
will reintroduce `Fri`/`Sat`/`Sun` rows and collide with the postprocess
step on next run — see [Running the Pipeline](running-the-pipeline.md#re-running-safely)
for the manual fix.

## Error handling and idempotency

- **Retries**: [`db.py::with_retry`](../reference/db.md) wraps every
  Supabase call, retrying up to 3 times with a 2s delay and resetting the
  cached client on failure.
- **Upsert keys**: `events` upserts on `(link, day)`
  ([ADR-022](../DECISIONS.md#adr-022)); `categories` upserts on `name`.
  Both are safe to re-run.
- **Duplicate-batch handling**: Postgres rejects `ON CONFLICT DO UPDATE`
  when the same `(link, day)` key appears twice in one batch, even with
  `ON CONFLICT` specified — `db.py::upsert_events` deduplicates
  client-side before batching.
- **Aggregation**: every step returns a `RunResult` (`success`, `counts`,
  `warnings`, `errors`); `run_full()` collects all three steps' results
  into one aggregate `RunResult` and never aborts early — a crash in one
  step is caught, logged as an error, and the remaining steps still run.
