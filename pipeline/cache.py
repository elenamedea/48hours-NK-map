import hashlib
import logging
import time
from pathlib import Path

import httpx

from pipeline.config import CACHE_DIR, CACHE_TTL

logger = logging.getLogger(__name__)


def _path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def get(url: str) -> str | None:
    p = _path(url)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > CACHE_TTL:
        return None
    return p.read_text(encoding="utf-8")


def put(url: str, html: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _path(url).write_text(html, encoding="utf-8")


def clear() -> None:
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.html"):
            f.unlink()


def fetch(client: httpx.Client, url: str, retries: int = 3, delay: float = 3.0) -> str:
    """GET a URL with retries on transient network errors (timeouts,
    connection resets). A single one-shot page fetch (e.g. the programme
    index) has no per-page fallback to absorb a flaky request otherwise."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return client.get(url).text
        except httpx.HTTPError as exc:
            last_exc = exc
            logger.warning("Fetch failed (attempt %d/%d) %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(delay)
    raise last_exc
