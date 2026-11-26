"""Deduplicator: assigns each new source record to an event.

Order of evidence (spec #1, "Deduplicator"), first hit wins:
1. An identical canonical URL: another source already gave a record for the same article.
2. A shared CVE identifier: the record names a CVE that a record of the event names, published
   within ``Grouping.cve_window_days`` of it.
3. Same organization and similar headline: the record names the organization an event is
   about, and its headline's trigram similarity to one of that event's headlines reaches
   ``Grouping.headline_similarity``, published within ``organization_window_hours`` by another
   source (one feed's own items about one organization are separate stories). Records
   that name CVEs never join an event whose records name only other CVEs: those are different
   flaws in one product, and their headlines are often near-identical templates.
Otherwise the record starts an event of its own. An event's title is always its earliest
record's original headline. The same organization alone never merges.
"""

from dataclasses import dataclass
from datetime import timedelta

import psycopg

from compromised import config, storage
from compromised.pipeline import scope
from compromised.pipeline.extractor import extract
from compromised.records import SourceRecord


@dataclass(frozen=True)
class Assignment:
    event_id: int
    created: bool  # True when the record started a new event


def assign(
    conn: psycopg.Connection, record: SourceRecord, rules: config.Grouping | None = None
) -> Assignment | None:
    """Store the record under an event. Returns None if the record is already stored."""
    rules = rules or config.Grouping.from_env()
    if storage.record_exists(conn, record):
        return None
    event_id = _matching_event(conn, record, rules)
    created = event_id is None
    if created:
        event_id = storage.create_event(conn, record)
    storage.insert_record(conn, record, event_id)
    storage.refresh_event_header(conn, event_id)
    return Assignment(event_id=event_id, created=created)


def _matching_event(conn, record: SourceRecord, rules: config.Grouping) -> int | None:
    by_url = storage.event_with_canonical_url(conn, record.canonical_url)
    if by_url is not None:
        return by_url
    by_cve = storage.event_sharing_a_cve(
        conn,
        cves=record.cves,
        published_at=record.published_at,
        window=timedelta(days=rules.cve_window_days),
    )
    if by_cve is not None:
        return by_cve
    affected = extract(record)
    if affected is not None:
        window = timedelta(hours=rules.organization_window_hours)
        return storage.event_with_similar_headline(
            conn,
            organization=affected.key or affected.name,
            source_id=record.source_id,
            headline=record.headline,
            published_at=record.published_at,
            cves=record.cves,
            window=window,
            threshold=rules.headline_similarity,
        )
    return None


def move_record(conn: psycopg.Connection, record_id: int, to_event_id: int | None = None) -> int:
    """Move a stored record to another event, or to a new event of its own when
    ``to_event_id`` is None, to correct a grouping mistake. Returns the record's event id.

    The record's content is never changed. Both events' titles, times, facts and tabs are
    recomputed; an event left without records is removed, and its address redirects to
    the record's new event.
    """
    with conn.transaction():
        from_event_id = storage.record_event(conn, record_id)
        if to_event_id is None:
            to_event_id = storage.create_event(conn, storage.record_by_id(conn, record_id))
        if to_event_id == from_event_id:
            return to_event_id
        storage.set_record_event(conn, record_id, to_event_id)
        for event_id in (from_event_id, to_event_id):
            if storage.delete_event_if_empty(conn, event_id):
                # The emptied event's page address now leads to where its record went (#11).
                storage.redirect_event(conn, event_id, to_event_id)
            else:
                storage.refresh_event_header(conn, event_id)
                scope.refresh_event(conn, event_id)
    return to_event_id
