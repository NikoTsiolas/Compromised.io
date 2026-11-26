"""Runs the pipeline for one source response: parse, normalize, assign to events, classify and
scope them, store; then, after the events are committed, ask the enricher (if any) about each
new event. Enrichment never blocks or fails ingestion (see pipeline.enricher)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from compromised import storage
from compromised.pipeline import adapters, deduplicator, msrc, scope
from compromised.pipeline.enricher import STOP_THE_PASS, Enricher
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import parse_rss
from compromised.records import ParsedItem
from compromised.sources import Source, Tier

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
    grouped: int = 0  # records that joined an event already stored
    enriched: int = 0


def ingest(
    conn: psycopg.Connection,
    source: Source,
    body: bytes,
    *,
    fetched_at: datetime,
    ratings: dict[str, msrc.Rating] | None = None,
    enricher: Enricher | None = None,
) -> IngestResult:
    """Store one response's items.

    ``ratings`` (MSRC only) are Microsoft's ratings from the SUG API (``msrc.lookup``); an MSRC
    entry without a rating that keeps it is not stored. A source with ``backfill_days`` never
    imports an item published longer ago than that before ``fetched_at``.

    Only events this response created are offered to the enricher: an event is enriched once,
    from its earliest record. A record that joins a stored event leaves its enrichment as it is
    (an event still awaiting enrichment is retried by ``enricher.enrich_pending``).
    """
    items = PARSERS[source.format](body)
    parsed = len(items)
    if source.backfill_days is not None:
        oldest = fetched_at - timedelta(days=source.backfill_days)
        items = [i for i in items if i.published is not None and i.published >= oldest]
    if source.format == "msrc":
        items = msrc.apply_ratings(items, ratings or {})
    new_ids: list[int] = []
    grouped = 0
    with conn.transaction():
        storage.upsert_source(conn, source)
        for item in items:
            record = normalize(
                item,
                source_id=source.id,
                fetched_at=fetched_at,
                images=source.tier != Tier.ATTACKER_CLAIM,
            )
            if record is None:
                continue
            assignment = deduplicator.assign(conn, record)
            if assignment is None:
                if source.format == "msrc":
                    # A new revision may change Microsoft's rating of an entry already stored:
                    # appended as a revision, the stored record itself never changes.
                    changed = storage.append_record_revision(conn, record)
                    if changed is not None:
                        scope.refresh_event(conn, changed)
                continue
            scope.refresh_event(conn, assignment.event_id)
            if assignment.created:
                new_ids.append(assignment.event_id)
            else:
                grouped += 1
    enriched = 0
    if enricher is not None:
        for event_id in new_ids:
            outcome = enricher.enrich(conn, event_id)
            enriched += outcome.enriched
            if outcome.reason in STOP_THE_PASS:
                break  # the rest wait for a later pass (enricher.enrich_pending)
    return IngestResult(items=parsed, new_events=len(new_ids), grouped=grouped, enriched=enriched)
