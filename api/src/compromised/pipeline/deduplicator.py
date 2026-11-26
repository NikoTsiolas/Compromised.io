"""Deduplicator: assigns each new source record to an event.

Walking skeleton rule: a record already stored (same canonical URL, or same source and guid) is
skipped; every other record gets a new event of its own. Grouping across outlets is #5.
"""

import psycopg

from compromised import storage
from compromised.records import SourceRecord


def assign(conn: psycopg.Connection, record: SourceRecord) -> int | None:
    """Store the record under an event. Returns the event id, or None if already stored."""
    if storage.record_exists(conn, record):
        return None
    event_id = storage.create_event(conn, record)
    storage.insert_record(conn, record, event_id)
    return event_id
