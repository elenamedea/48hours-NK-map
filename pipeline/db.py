"""Supabase upsert/query helpers, all wrapped with retry-on-failure."""

import logging
import time

from supabase import Client, create_client

from pipeline.config import (
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    TABLE_CATEGORIES,
    TABLE_EVENTS,
)

logger = logging.getLogger(__name__)

_db: Client | None = None


def _client() -> Client:
    global _db
    if _db is None:
        _db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _db


def with_retry(fn, retries: int = 3, delay: float = 2.0):
    """Call fn(), retrying on any exception up to `retries` times with `delay` seconds between attempts. Resets the cached client on failure."""
    global _db
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Supabase request failed (attempt %d/%d): %s", attempt, retries, exc
            )
            _db = None
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


def upsert_categories(names: list) -> dict:
    """Upsert canonical genres. Returns {name: id}."""
    rows = [{"name": n} for n in names]
    response = with_retry(
        lambda: _client().table(TABLE_CATEGORIES).upsert(rows, on_conflict="name").execute()
    )
    id_map = {row["name"]: row["id"] for row in response.data}
    logger.info("Upserted %d categories", len(id_map))
    return id_map


def upsert_events(records: list) -> tuple[int, int]:
    """Upsert event records in batches of 200. Returns (inserted, skipped)."""
    BATCH = 200
    rows: list[dict] = []
    skipped = 0
    for r in records:
        if not r.get("link") or not r.get("day"):
            logger.warning("Event %r missing link or day — skipped", r.get("title"))
            skipped += 1
            continue
        rows.append({
            "title":         r["title"],
            "link":          r["link"],
            "day":           r["day"],
            "start_time":    r.get("start_time"),
            "end_time":      r.get("end_time"),
            "location":      r.get("location"),
            "genres":        r.get("genres") or [],
            "accessibility": r.get("accessibility", False),
            "toilet":        r.get("toilet", False),
        })
    # Deduplicate by (link, day) — Postgres rejects duplicate constrained
    # values within the same batch even when ON CONFLICT is specified.
    seen_pairs: set = set()
    deduped: list[dict] = []
    for row in rows:
        key = (row["link"], row["day"])
        if key not in seen_pairs:
            seen_pairs.add(key)
            deduped.append(row)
    if len(deduped) < len(rows):
        logger.warning("Dropped %d duplicate (link, day) pairs", len(rows) - len(deduped))
    rows = deduped

    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        with_retry(
            lambda b=batch: _client()
            .table(TABLE_EVENTS)
            .upsert(b, on_conflict="link,day")
            .execute()
        )
        inserted += len(batch)
        logger.info(
            "Upserted rows %d–%d (%d in batch)", i, i + len(batch) - 1, len(batch)
        )
    logger.info("Events total: %d upserted, %d skipped", inserted, skipped)
    return inserted, skipped
