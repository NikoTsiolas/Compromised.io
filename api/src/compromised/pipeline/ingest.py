"""Runs the pipeline for one source response: parse, normalize, assign to events, store."""

from dataclasses import dataclass
from datetime import datetime

import psycopg

from compromised import storage
from compromised.pipeline import deduplicator
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import PARSERS
from compromised.sources import Source


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
            record = normalize(item, source_id=source.id, fetched_at=fetched_at)
            if record is not None and deduplicator.assign(conn, record) is not None:
                new_events += 1
    return IngestResult(items=len(items), new_events=new_events)
