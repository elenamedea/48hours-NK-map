"""Nominatim fallback geocoding for events missing scraped coordinates (ADR-018)."""

import logging
import time

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from pipeline import db
from pipeline.config import BBOX, NOMINATIM_DELAY, TABLE_EVENTS

logger = logging.getLogger(__name__)

_geolocator = Nominatim(
    user_agent="48hours-neukoelln-map/1.0 (+https://github.com/elenamedea/48-hours-nk-map)"
)


def _in_bbox(lat: float, lng: float) -> bool:
    return (
        BBOX["lat_min"] <= lat <= BBOX["lat_max"]
        and BBOX["lng_min"] <= lng <= BBOX["lng_max"]
    )


def _geocode_address(address: str) -> tuple[float, float, str] | None:
    try:
        location = _geolocator.geocode(f"{address}, Berlin, Germany", timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        logger.warning("Nominatim error for %r: %s", address, exc)
        return None
    finally:
        time.sleep(NOMINATIM_DELAY)

    if location is None:
        return None

    lat, lng = location.latitude, location.longitude
    source = "nominatim" if _in_bbox(lat, lng) else "nominatim_suspect"
    return lat, lng, source


def geocode_missing() -> tuple[int, int, list[str]]:
    """Geocode events with null lat via Nominatim; deduplicated by location name.
    Returns (locations_geocoded, locations_failed, errors)."""
    client = db._client()
    rows = db.with_retry(
        lambda: client.table(TABLE_EVENTS)
        .select("location, address")
        .is_("lat", "null")
        .execute()
    ).data
    logger.info("Events missing coordinates: %d rows", len(rows))

    by_location: dict[str, str] = {}
    for row in rows:
        loc  = row.get("location")
        addr = row.get("address")
        if loc and addr and loc not in by_location:
            by_location[loc] = addr

    geocoded = 0
    failed   = 0
    errors: list[str] = []

    for location, address in by_location.items():
        result = _geocode_address(address)
        if result is None:
            msg = f"Location {location!r}: no result for address {address!r}"
            logger.warning(msg)
            errors.append(msg)
            failed += 1
            continue

        lat, lng, source = result
        db.with_retry(
            lambda loc=location, la=lat, ln=lng, s=source: client
            .table(TABLE_EVENTS)
            .update({"lat": la, "lng": ln, "geocode_source": s})
            .eq("location", loc)
            .execute()
        )
        logger.info("Geocoded %r → %.6f, %.6f [%s]", location, lat, lng, source)
        geocoded += 1

    logger.info("Geocoding done: %d geocoded, %d failed", geocoded, failed)
    return geocoded, failed, errors
