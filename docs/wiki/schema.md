# Database Schema

Flat 2-table schema ([ADR-022](../DECISIONS.md#adr-022), superseding an
earlier 4-table `venues`/`events`/`categories`/`event_categories` design
from [ADR-016](../DECISIONS.md#adr-016)). Source of truth:
`supabase/schema.sql`.

## `events`

One row per event **×** day — a 3-day multi-day event produces 3 rows.
`UNIQUE (link, day)` is the upsert key.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `title` | text | |
| `day` | text | `Fri`/`Sat`/`Sun` right after scraping, converted to `03.07.2026` etc. by `scripts/postprocess_days.py` |
| `start_time`, `end_time` | text | `HH:MM`; may be null for the non-boundary day of a multi-day event |
| `location` | text | venue name as printed on the listing page — the join key used to patch in address/coords during `run_enrich()`, since there's no `venues` table |
| `address` | text | patched in during enrich, from the venue page |
| `lat`, `lng` | double precision | nullable until enrich/geocode fills them |
| `geocode_source` | text | provenance — one of `scraped`, `scraped_suspect`, `nominatim`, `nominatim_suspect`, or null. The `_suspect` suffix means the coordinate fell outside the Neukölln bounding box (`config.BBOX`) and needs manual review ([ADR-018](../DECISIONS.md#adr-018)) |
| `genres` | text[] | official festival categories, verbatim — see [ADR-023](../DECISIONS.md#adr-023) for the emoji/colour rule; empty array if the listing page had no genre tag |
| `emoji` | text[] | |
| `link` | text | half of the upsert key |
| `accessibility`, `toilet` | boolean | default false |
| `scraped_at`, `updated_at` | timestamptz | |

**Multi-genre pin rule** ([ADR-023](../DECISIONS.md#adr-023)): events
with more than one genre get pin colour `#000000` and emoji `🍥` instead
of a genre colour, to stay visually distinct on the map rather than
picking one genre arbitrarily.

## `categories`

Genre lookup only — not a foreign key target from `events` (`genres` is a
plain `text[]`, no join).

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `name` | text | unique, matches the values inside `events.genres` |
| `emoji` | text | one per category |
| `colour` | text | one of two palette values per [ADR-023](../DECISIONS.md#adr-023): `#FA6AEB` or `#FB9130` |

Both tables have row-level security enabled with a public-read policy —
no auth required to read, writes go through the service-role key only
(pipeline-side).
