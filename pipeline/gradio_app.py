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
    """Wrap a button handler so a crash shows in the UI instead of killing the app."""
    @wraps(fn)
    def wrapper():
        try:
            return fn()
        except Exception as exc:
            logger.exception("%s crashed", fn.__name__)
            return f"✗ {fn.__name__} crashed: {exc}"
    return wrapper


def _fmt(result: pl.RunResult) -> str:
    """Render a RunResult as plain text for the Gradio output box."""
    lines = ["✓ Success" if result.success else "✗ Completed with errors"]
    for k, v in result.counts.items():
        lines.append(f"  {k}: {v}")
    if result.warnings:
        lines.append(f"\nWarnings ({len(result.warnings)}):")
        lines.extend(f"  {w}" for w in result.warnings[:50])
    if result.errors:
        lines.append(f"\nErrors ({len(result.errors)}):")
        lines.extend(f"  {e}" for e in result.errors[:50])
        if len(result.errors) > 50:
            lines.append(f"  ... and {len(result.errors) - 50} more")
    return "\n".join(lines)


@_safe
def btn_scrape_events() -> str:
    return _fmt(pl.run_events())


@_safe
def btn_enrich() -> str:
    return _fmt(pl.run_enrich())


@_safe
def btn_geocode() -> str:
    return _fmt(pl.run_geocode())


@_safe
def btn_run_full() -> str:
    return _fmt(pl.run_full())


@_safe
def btn_preview() -> str:
    """Pull events + categories from Supabase and report coverage stats."""
    client = db._client()

    all_event_rows = []
    offset = 0
    PAGE = 1000
    while True:
        batch = db.with_retry(
            lambda o=offset: client
            .table(TABLE_EVENTS)
            .select("day, genres, lat, geocode_source")
            .range(o, o + PAGE - 1)
            .execute()
        ).data
        all_event_rows.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
    event_rows = all_event_rows

    cat_rows = db.with_retry(
        lambda: client.table(TABLE_CATEGORIES).select("id,name").execute()
    ).data

    total    = len(event_rows)
    geocoded = sum(1 for r in event_rows if r.get("lat") is not None)
    pct      = round(100 * geocoded / total) if total else 0
    suspect  = sum(
        1 for r in event_rows
        if (r.get("geocode_source") or "").endswith("_suspect")
    )

    day_counts: Counter = Counter(r.get("day") for r in event_rows)
    genre_counts: Counter = Counter()
    for r in event_rows:
        for g in (r.get("genres") or []):
            genre_counts[g] += 1

    lines = [
        f"Events:             {total}",
        f"Categories:         {len(cat_rows)}",
        f"Geocoding coverage: {geocoded}/{total} ({pct}%)",
        f"Suspect coords:     {suspect}",
        "",
        "Events by day:",
        f"  Fri 03.07: {day_counts.get('03.07.2026', 0)}",
        f"  Sat 04.07: {day_counts.get('04.07.2026', 0)}",
        f"  Sun 05.07: {day_counts.get('05.07.2026', 0)}",
    ]
    if genre_counts:
        lines.append("")
        lines.append("Top genres:")
        for name, count in genre_counts.most_common(10):
            lines.append(f"  {name}: {count}")

    return "\n".join(lines)


with gr.Blocks(title="48hours Neukölln — Pipeline Admin") as demo:
    gr.Markdown("# 48hours Neukölln — Pipeline Admin")
    with gr.Row():
        b_events = gr.Button("Scrape events")
        b_enrich = gr.Button("Enrich venues")
        b_geo    = gr.Button("Geocode missing")
        b_full   = gr.Button("Run full pipeline", variant="primary")
        b_prev   = gr.Button("Preview data")
    output = gr.Textbox(label="Result", lines=20, interactive=False)
    b_events.click(fn=btn_scrape_events, outputs=output)
    b_enrich.click(fn=btn_enrich,        outputs=output)
    b_geo.click(   fn=btn_geocode,       outputs=output)
    b_full.click(  fn=btn_run_full,      outputs=output)
    b_prev.click(  fn=btn_preview,       outputs=output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
