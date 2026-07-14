"""Orchestrates the pipeline steps: scrape -> enrich -> geocode, each returning a RunResult."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pipeline import db, geocoder
from pipeline.config import TABLE_EVENTS
from pipeline.scraper import programm as programm_scraper
from pipeline.scraper import venues as venue_scraper

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    success: bool
    counts: dict
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_events() -> RunResult:
    """Scrape /en/programm listing; upsert categories + events (no coords yet)."""
    records, genres, errors = programm_scraper.scrape()
    db.upsert_categories(genres)
    inserted, skipped = db.upsert_events(records)
    warnings = []
    if skipped:
        warnings.append(f"{skipped} event(s) skipped — missing link or day.")
    return RunResult(
        success=len(errors) == 0,
        counts={
            "categories": len(genres),
            "events_inserted": inserted,
            "events_skipped": skipped,
        },
        warnings=warnings,
        errors=errors,
    )


def run_enrich() -> RunResult:
    """Scrape venue pages; patch events rows with address + coords by location name."""
    records, errors = venue_scraper.scrape()
    client = db._client()
    updated = 0
    for r in records:
        name = r.get("name")
        if not name:
            continue
        payload: dict = {}
        if r.get("address"):
            payload["address"] = r["address"]
        if r.get("lat") is not None:
            payload["lat"]            = r["lat"]
            payload["lng"]            = r["lng"]
            payload["geocode_source"] = r.get("geocode_source", "google_maps")
        if not payload:
            continue
        db.with_retry(
            lambda n=name, p=payload: client
            .table(TABLE_EVENTS)
            .update(p)
            .eq("location", n)
            .execute()
        )
        updated += 1
    logger.info("Enrich: updated %d venue locations", updated)
    return RunResult(
        success=len(errors) == 0,
        counts={"venues_scraped": len(records), "locations_updated": updated},
        errors=errors,
    )


def run_geocode() -> RunResult:
    """Nominatim fallback for events still missing coordinates."""
    geocoded, failed, errors = geocoder.geocode_missing()
    return RunResult(
        success=failed == 0,
        counts={"geocoded": geocoded, "failed": failed},
        errors=errors,
    )


def run_full() -> RunResult:
    """Run events → enrich → geocode in sequence; crash-protected."""
    all_errors: list[str] = []
    all_warnings: list[str] = []
    all_counts: dict = {}
    for step in (run_events, run_enrich, run_geocode):
        try:
            r = step()
            all_errors.extend(r.errors)
            all_warnings.extend(r.warnings)
            all_counts.update(r.counts)
        except Exception as exc:
            logger.exception("%s crashed", step.__name__)
            all_errors.append(f"{step.__name__} crashed: {exc}")
    return RunResult(
        success=len(all_errors) == 0,
        counts=all_counts,
        warnings=all_warnings,
        errors=all_errors,
    )
