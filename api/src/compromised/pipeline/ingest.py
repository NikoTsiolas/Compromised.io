"""Runs the pipeline for one source response: parse, normalize, assign to events, classify and
scope them, store."""

from dataclasses import dataclass
from datetime import datetime

import psycopg

from compromised import storage
from compromised.pipeline import deduplicator, scope
from compromised.pipeline.normalizer import normalize
from compromised.pipeline.parsers import PARSERS
from compromised.sources import Source


@dataclass(frozen=True)
class IngestResult:
    items: int
    new_events: int
    grouped: int = 0  # records that joined an event already stored


def ingest(
    conn: psycopg.Connection, source: Source, body: bytes, *, fetched_at: datetime
) -> IngestResult:
    items = PARSERS[source.format](body)
    new_events = grouped = 0
    with conn.transaction():
        storage.upsert_source(conn, source)
        for item in items:
            record = normalize(item, source_id=source.id, fetched_at=fetched_at)
            if record is None:
                continue
            assignment = deduplicator.assign(conn, record)
            if assignment is None:
                continue
            scope.refresh_event(conn, assignment.event_id)
            if assignment.created:
                new_events += 1
            else:
                grouped += 1
    return IngestResult(items=len(items), new_events=new_events, grouped=grouped)
