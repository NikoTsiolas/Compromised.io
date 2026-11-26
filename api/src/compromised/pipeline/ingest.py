"""Runs the pipeline for one source response: parse, normalize, assign to events, classify and
scope them, store."""

from dataclasses import dataclass
from datetime import datetime

import psycopg

from compromised import storage
from compromised.pipeline import deduplicator, scope
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import PARSERS
from compromised.sources import Source, Tier


@dataclass(frozen=True)
class IngestResult:
    items: int
    new_events: int


def ingest(
    conn: psycopg.Connection, source: Source, body: bytes, *, fetched_at: datetime
) -> IngestResult:
    items = PARSERS[source.format](body)
    new_events = 0
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
            event_id = deduplicator.assign(conn, record)
            if event_id is not None:
                scope.refresh_event(conn, event_id)
                new_events += 1
    return IngestResult(items=len(items), new_events=new_events)
