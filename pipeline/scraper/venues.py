import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

from pipeline import cache
from pipeline.config import BASE_URL, SCRAPE_DELAY
from pipeline.parsers import coord_parser, venue_parser

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "48hours-neukoelln-map/1.0 (+https://github.com/elenamedea/48-hours-nk-map)"
}
_KARTE_HREF = re.compile(r"^/en/programm/karte/([^/]+)$")


def _collect_slugs(client: httpx.Client) -> list:
    url  = f"{BASE_URL}/programm/karte"
    html = cache.get(url)
    if html is None:
        logger.info("Fetching venue index %s", url)
        html = cache.fetch(client, url)
        cache.put(url, html)
        time.sleep(SCRAPE_DELAY)
    soup  = BeautifulSoup(html, "lxml")
    slugs: list = []
    seen:  set  = set()
    for a in soup.find_all("a", href=True):
        m = _KARTE_HREF.match(a["href"])
        if m:
            slug = m.group(1)
            if slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def scrape() -> tuple:
    """Scrape all venue pages.
    Returns (records, errors). Each record has: slug, name, address, lat, lng, geocode_source."""
    errors:  list = []
    records: list = []

    with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=30) as client:
        slugs = _collect_slugs(client)
        logger.info("Venue index: %d slugs", len(slugs))

        for slug in slugs:
            url = f"{BASE_URL}/programm/karte/{slug}"
            try:
                html = cache.get(url)
                if html is None:
                    html = cache.fetch(client, url)
                    cache.put(url, html)
                    time.sleep(SCRAPE_DELAY)
                parsed = venue_parser.parse(html, slug)
                coords = (
                    coord_parser.parse(parsed["maps_url"])
                    if parsed.get("maps_url")
                    else None
                )
                records.append({
                    "slug":           parsed["slug"],
                    "name":           parsed["name"],
                    "address":        parsed.get("address"),
                    "lat":            coords[0] if coords else None,
                    "lng":            coords[1] if coords else None,
                    "geocode_source": coords[2] if coords else None,
                })
            except Exception as exc:
                msg = f"Venue {slug}: {exc}"
                logger.warning(msg)
                errors.append(msg)

    logger.info("Venues: %d ok, %d errors", len(records), len(errors))
    return records, errors
