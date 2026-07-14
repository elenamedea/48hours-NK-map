"""Pipeline-wide constants: URLs, bounding box, rate limits, cache TTL, table names."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://48-stunden-neukoelln.de/en"

BBOX = {
    "lat_min": 52.43,
    "lat_max": 52.50,
    "lng_min": 13.39,
    "lng_max": 13.47,
}

SCRAPE_DELAY    = 2.0
NOMINATIM_DELAY = 1.0

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_TTL = 60 * 60 * 24

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

TABLE_EVENTS     = "events"
TABLE_CATEGORIES = "categories"
