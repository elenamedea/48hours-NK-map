import re
from bs4 import BeautifulSoup


def parse(html: str, slug: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else None

    # Address block uses <br> separators. Some venue pages print the Maps
    # link as plain visible text inside the same block — exclude URL-looking
    # lines so they don't pollute the address sent to Nominatim fallback.
    address = None
    for p in soup.find_all("p"):
        if p.find("br"):
            parts = [
                s.strip()
                for s in p.get_text(separator="\n").splitlines()
                if s.strip() and not s.strip().startswith(("http://", "https://"))
            ]
            if parts:
                address = ", ".join(parts)
                break

    maps_url = None
    for a in soup.find_all("a", href=True):
        if "google.com/maps" in a["href"]:
            maps_url = a["href"]
            break

    accessibility = []
    for tag in soup.find_all(string=re.compile(r"barrier.free|barrierefreie|dgs|sign.language", re.I)):
        text = tag.strip()
        if text and text not in accessibility:
            accessibility.append(text)

    # Event slugs: /en/programm/{slug} links but not /karte/ links
    event_slugs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"/programm/(?!karte/)[^/]+$", href):
            event_slug = href.rstrip("/").split("/")[-1]
            if event_slug and event_slug not in event_slugs:
                event_slugs.append(event_slug)

    return {
        "slug": slug,
        "name": name,
        "address": address,
        "maps_url": maps_url,
        "accessibility": accessibility,
        "event_slugs": event_slugs,
    }
