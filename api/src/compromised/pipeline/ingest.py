"""Runs the pipeline for one source response: parse, normalize, assign to events, classify and
scope them, store; then, after the events are committed, ask the enricher (if any) about each
new event. Enrichment never blocks or fails ingestion (see pipeline.enricher)."""

from dataclasses import dataclass
from datetime import datetime

import psycopg

from compromised import storage
from compromised.pipeline import deduplicator, scope
from compromised.pipeline.enricher import STOP_THE_PASS, Enricher
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import PARSERS
from compromised.sources import Source


@dataclass(frozen=True)
class IngestResult:
    items: int
    new_events: int
    enriched: int = 0


def ingest(
    conn: psycopg.Connection,
    source: Source,
    body: bytes,
    *,
    fetched_at: datetime,
    enricher: Enricher | None = None,
) -> IngestResult:
    items = PARSERS[source.format](body)
    new_ids: list[int] = []
    with conn.transaction():
        storage.upsert_source(conn, source)
        for item in items:
            record = normalize(item, source_id=source.id, fetched_at=fetched_at)
            if record is None:
                continue
            event_id = deduplicator.assign(conn, record)
            if event_id is not None:
                scope.refresh_event(conn, event_id)
                new_ids.append(event_id)
    enriched = 0
    if enricher is not None:
        for event_id in new_ids:
            outcome = enricher.enrich(conn, event_id)
            enriched += outcome.enriched
            if outcome.reason in STOP_THE_PASS:
                break  # the rest wait for a later pass (enricher.enrich_pending)
    return IngestResult(items=len(items), new_events=len(new_ids), enriched=enriched)
