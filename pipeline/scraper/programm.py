import logging
import time

import httpx
from bs4 import BeautifulSoup

from pipeline import cache
from pipeline.config import BASE_URL, SCRAPE_DELAY
from pipeline.parsers import event_listing_parser

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "48hours-neukoelln-map/1.0 "
        "(+https://github.com/elenamedea/48-hours-nk-map)"
    )
}


def _extract_genres(soup: BeautifulSoup) -> list:
    canonical = []
    seen:  set = set()
    sel = soup.find(
        "select",
        attrs={"data-drupal-selector": "edit-genre"},
    )
    if not sel:
        logger.warning("Genre select not found on programme page")
        return []
    for opt in sel.find_all("option"):
        text = opt.get_text(strip=True)
        val  = opt.get("value", "")
        if val and text.lower() not in ("", "- any -", "all"):
            if text not in seen:
                seen.add(text)
                canonical.append(text)
    if "Perspective" not in seen:
        canonical.append("Perspective")
    return canonical


def scrape() -> tuple:
    """Fetch /en/programm listing page.
    Returns (event_records, canonical_genres, errors)."""
    url  = f"{BASE_URL}/programm"
    html = cache.get(url)
    if html is None:
        logger.info("Fetching programme listing %s", url)
        with httpx.Client(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=30,
        ) as client:
            html = cache.fetch(client, url)
        cache.put(url, html)
        time.sleep(SCRAPE_DELAY)

    soup    = BeautifulSoup(html, "lxml")
    genres  = _extract_genres(soup)
    records = event_listing_parser.parse_items(html, set(genres))
    logger.info(
        "Programme: %d event-day records, %d genres",
        len(records), len(genres),
    )
    return records, genres, []
