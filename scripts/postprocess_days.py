#!/usr/bin/env python3
"""Convert Fri/Sat/Sun day abbreviations to full festival dates."""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL              = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

DAY_MAP = {
    "Fri": "03.07.2026",
    "Sat": "04.07.2026",
    "Sun": "05.07.2026",
}

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

for abbr, date in DAY_MAP.items():
    result = (
        client.table("events")
        .update({"day": date})
        .eq("day", abbr)
        .execute()
    )
    print(f"  {abbr} → {date}: {len(result.data)} rows updated")

print("Done.")
