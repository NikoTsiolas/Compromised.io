"""Runs the pipeline for one source response: parse, normalize, assign to events, classify and
scope them, store."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from compromised import storage
from compromised.pipeline import adapters, deduplicator, msrc, scope
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import parse_rss
from compromised.records import ParsedItem
from compromised.sources import Source

# Registry ``format`` -> adapter.
PARSERS: dict[str, Callable[[bytes], list[ParsedItem]]] = {
    "rss": parse_rss,
    "cisa-kev": adapters.parse_kev,
    "ransomware-live": adapters.parse_ransomware_live,
    "msrc": msrc.parse,
}


@dataclass(frozen=True)
class IngestResult:
    items: int
    new_events: int


def ingest(
    conn: psycopg.Connection,
    source: Source,
    body: bytes,
    *,
    fetched_at: datetime,
    ratings: dict[str, msrc.Rating] | None = None,
) -> IngestResult:
    """Store one response's items.

    ``ratings`` (MSRC only) are Microsoft's ratings from the SUG API (``msrc.lookup``); an MSRC
    entry without a rating that keeps it is not stored. A source with ``backfill_days`` never
    imports an item published longer ago than that before ``fetched_at``.
    """
    items = PARSERS[source.format](body)
    parsed = len(items)
    if source.backfill_days is not None:
        oldest = fetched_at - timedelta(days=source.backfill_days)
        items = [i for i in items if i.published is not None and i.published >= oldest]
    if source.format == "msrc":
        items = msrc.apply_ratings(items, ratings or {})
    new_events = 0
    with conn.transaction():
        storage.upsert_source(conn, source)
        for item in items:
            record = normalize(item, source_id=source.id, fetched_at=fetched_at)
            if record is None:
                continue
            event_id = deduplicator.assign(conn, record)
            if event_id is not None:
                scope.refresh_event(conn, event_id)
                new_events += 1
            elif source.format == "msrc":
                # A new revision may change Microsoft's rating of an entry already stored.
                changed = storage.update_record_metadata(conn, record)
                if changed is not None:
                    scope.refresh_event(conn, changed)
    return IngestResult(items=parsed, new_events=new_events)
