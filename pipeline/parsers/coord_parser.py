"""Extracts (lat, lng) from a venue page's Google Maps link."""

from urllib.parse import urlparse, parse_qs
from pipeline.config import BBOX


def parse(maps_url: str) -> tuple[float, float, str] | None:
    """Parse a Google Maps `?query=lat,lng` URL. Returns (lat, lng, source) with source 'scraped' or 'scraped_suspect' if outside the Neukölln bounding box, or None if unparseable."""
    try:
        qs = parse_qs(urlparse(maps_url).query)
        lat_str, lng_str = qs["query"][0].split(",", 1)
        lat, lng = float(lat_str.strip()), float(lng_str.strip())
    except (KeyError, ValueError, IndexError):
        return None
    in_bbox = (
        BBOX["lat_min"] <= lat <= BBOX["lat_max"]
        and BBOX["lng_min"] <= lng <= BBOX["lng_max"]
    )
    return lat, lng, "scraped" if in_bbox else "scraped_suspect"
