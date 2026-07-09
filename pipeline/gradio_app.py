import logging
from collections import Counter
from functools import wraps

import gradio as gr

from pipeline import db
from pipeline import pipeline as pl
from pipeline.config import TABLE_CATEGORIES, TABLE_EVENTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _safe(fn):
    @wraps(fn)
    def wrapper():
        try:
            return fn()
        except Except
            logger.exception("%s crashed", fn.__name__)
            return f"
    return wrapper


def _fmt(result: pl.R
    lines = ["✓ Success" if result.success else "✗ Completed with
errors"]
    for k, v in result.counts.items():
        lines.append(
    if result.warnings:
        lines.append(nings)}):")
        lines.extend(f"  {w}" for w in result.warnings[:50])
    if result.errors:
        lines.append(f"\nErrors ({len(result.errors)}):")
        lines.extend(rs[:50])
        if len(result.errors) > 50:
            lines.apprrors) - 50} more")
    return "\n".join(lines)


@_safe
def btn_scrape_events() -> str:
    return _fmt(pl.ru


@_safe
def btn_enrich() -> s
    return _fmt(pl.run_enrich())


@_safe
def btn_geocode() -> str:
    return _fmt(pl.ru


@_safe
def btn_run_full() ->
    return _fmt(pl.run_full())


@_safe
def btn_preview() -> str:
    client = db._clie

    all_event_rows =
    offset = 0
    PAGE = 1000
    while True:
        batch = db.wi
            lambda o=offset: client
            .table(TA
            .select("day, genres, lat, geocode_source")
            .range(o,
            .execute()
        ).data
        all_event_rows.extend(batch)
        if len(batch)
            break
        offset += PAG
    event_rows = all_event_rows

    cat_rows = db.with_retry(
        lambda: clienect("id,name").execute()
    ).data

    total    = len(ev
    geocoded = sum(1 for r in event_rows if r.get("lat") is not None)
    pct      = round(tal else 0
    suspect  = sum(
        1 for r in ev
        if (r.get("geocode_source") or "").endswith("_suspect")
    )

    day_counts: Count r in event_rows)
    genre_counts: Counter = Counter()
    for r in event_ro
        for g in (r.get("genres") or []):
            genre_cou

    lines = [
        f"Events:             {total}",
        f"Categories:
        f"Geocoding coverage: {geocoded}/{total} ({pct}%)",
        f"Suspect coo
        "",
        "Events by da
        f"  Fri 03.07: {day_counts.get('03.07.2026', 0)}",
        f"  Sat 04.07', 0)}",
        f"  Sun 05.07: {day_counts.get('05.07.2026', 0)}",
    ]
    if genre_counts:
        lines.append(
        lines.append("Top genres:")
        for name, coun(10):
            lines.append(f"  {name}: {count}")

    return "\n".join(lines)


with gr.Blocks(title=as demo:
    gr.Markdown("# 48hours Neukölln — Pipeline Admin")
    with gr.Row():
        b_events = gr.Button("Scrape events")
        b_enrich = gr
        b_geo    = gr.Button("Geocode missing")
        b_full   = grvariant="primary")
        b_prev   = gr.Button("Preview data")
    output = gr.Textbinteractive=False)
    b_events.click(fn=btn_scrape_events, outputs=output)
    b_enrich.click(fnutput)
    b_geo.click(   fn=btn_geocode,       outputs=output)
    b_full.click(  fnutput)
    b_prev.click(  fn=btn_preview,       outputs=output)

if __name__ == "__main__":
    demo.launch(servelse)
