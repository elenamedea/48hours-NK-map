# API Reference

Generated from docstrings via [mkdocstrings](https://mkdocstrings.github.io/).
See [Pipeline Data Flow](../wiki/data-flow.md) for how these modules chain
together at runtime.

- [`config`](config.md) — constants: URLs, bounding box, rate limits, table names
- [`db`](db.md) — Supabase upsert/query helpers, retry wrapper
- [`cache`](cache.md) — disk HTML cache
- [`geocoder`](geocoder.md) — Nominatim fallback geocoding
- [`pipeline`](pipeline.md) — orchestration, `RunResult`
- [`gradio_app`](gradio-app.md) — admin UI
- [`scraper.programm`](scraper-programm.md) — programme listing scrape
- [`scraper.venues`](scraper-venues.md) — venue page scrape
- [`parsers.event_listing_parser`](parsers-event-listing-parser.md) — listing page parsing
- [`parsers.coord_parser`](parsers-coord-parser.md) — Google Maps link → coordinates
- [`parsers.venue_parser`](parsers-venue-parser.md) — venue page parsing
