"""Parses event×day records out of the /en/programm listing page HTML."""

import re
from bs4 import BeautifulSoup

# Same-day: "Fri 19:00 - 21:00"
_TIME_RE = re.compile(
    r"(Fri|Sat|Sun)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})"
)
# Cross-day: "Fri 19:00 - Sun 19:00"
_MULTIDAY_RE = re.compile(
    r"(Fri|Sat|Sun)\s+(\d{1,2}:\d{2})\s*-\s*(Fri|Sat|Sun)\s+(\d{1,2}:\d{2})"
)
_DAY_ORDER = {"Fri": 0, "Sat": 1, "Sun": 2}
_DAYS      = ["Fri", "Sat", "Sun"]


def _expand_days(base, start_day, start_time, end_day, end_time):
    """Return one record per day for a cross-day time range.
    If end_time is 00:00 the event ends at midnight — one row for start_day only."""
    if end_time == "00:00":
        return [{**base, "day": start_day,
                 "start_time": start_time, "end_time": end_time}]
    days = _DAYS[_DAY_ORDER[start_day] : _DAY_ORDER[end_day] + 1]
    result = []
    for i, day in enumerate(days):
        result.append({
            **base,
            "day":        day,
            "start_time": start_time if i == 0            else None,
            "end_time":   end_time   if i == len(days) - 1 else None,
        })
    return result


def parse_items(html: str, canonical: set) -> list[dict]:
    """Parse all eventplace__item elements from /en/programm."""
    soup    = BeautifulSoup(html, "lxml")
    records = []

    for item in soup.find_all(class_="eventplace__item"):
        title_el = item.find(class_=lambda c: c and "eventplace__title" in c)
        if not title_el:
            continue
        a = title_el.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        link  = a.get("href", "")
        if not title or not link:
            continue

        time_el  = item.find(class_=lambda c: c and "eventplace__time" in c)
        time_raw = time_el.get_text(" ", strip=True) if time_el else ""

        loc_el   = item.find(class_=lambda c: c and "eventplace__location" in c)
        location = loc_el.get_text(strip=True) if loc_el else None

        genres_el = item.find(class_=lambda c: c and "eventplace__genres" in c)
        genres: list = []
        seen_g: set = set()
        if genres_el:
            for text in genres_el.get_text("\n").split("\n"):
                t = text.strip()
                if t and t in canonical and t not in seen_g:
                    seen_g.add(t)
                    genres.append(t)

        icons_el      = item.find(class_=lambda c: c and "eventplace__icons" in c)
        accessibility = False
        toilet        = False
        if icons_el:
            accessibility = bool(
                icons_el.find(class_=lambda c: c and "icon--accessibility" in c)
            )
            toilet = bool(
                icons_el.find(class_=lambda c: c and "icon--toilet" in c)
            )

        base = {
            "title":         title,
            "link":          link,
            "location":      location,
            "genres":        genres,
            "accessibility": accessibility,
            "toilet":        toilet,
        }

        m_single = _TIME_RE.search(time_raw)
        if m_single:
            records.append({**base, "day": m_single.group(1),
                            "start_time": m_single.group(2),
                            "end_time":   m_single.group(3)})
            continue

        m_multi = _MULTIDAY_RE.search(time_raw)
        if m_multi:
            records.extend(_expand_days(
                base,
                m_multi.group(1), m_multi.group(2),
                m_multi.group(3), m_multi.group(4),
            ))

    return records
