"""Search and filters over published events (#10). All queries are parameterised.

Scope: only events that appear in at least one feed tab, so search never surfaces what the feed
rules keep out (commentary, unknown organization, gated vulnerabilities). Results are newest
first and paginated with the feed's cursor (publication time, id).
"""

import re
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from compromised.records import EventPage
from compromised.storage import (
    EVENT_COLUMNS,
    MAX_PAGE_SIZE,
    decode_cursor,
    encode_cursor,
    events_from_rows,
)

CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
MAX_QUERY_LENGTH = 200


@dataclass(frozen=True)
class Filters:
    """Every field is optional; given fields combine with AND, values within one field with OR."""

    query: str = ""
    tab: str | None = None
    categories: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()  # source registry ids; an event matches if any record is from one
    statuses: tuple[str, ...] = ()  # verification status
    since: datetime | None = None  # publication time, inclusive
    until: datetime | None = None  # publication time, exclusive


def clean_query(raw: str) -> str:
    """The query as searched: control characters (NUL among them, which PostgreSQL refuses in
    text) become spaces and runs of whitespace collapse."""
    return " ".join("".join(c if c.isprintable() else " " for c in raw).split())


def search(
    conn: psycopg.Connection, filters: Filters, *, limit: int = 20, cursor: str | None = None
) -> EventPage:
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    conditions = ["cardinality(tabs) > 0"]
    params: list = []

    query = clean_query(filters.query)
    cves = sorted({c.upper() for c in CVE.findall(query)})
    words = CVE.sub(" ", query)
    if cves:
        # Exact identifiers: the event names at least one of them.
        conditions.append("cves && %s::text[]")
        params.append(cves)
    if re.search(r"\w", words):
        # websearch_to_tsquery accepts any text without raising: quotes, "or" and "-" have their
        # web-search meaning and every other operator character is ignored.
        conditions.append("search_vector @@ websearch_to_tsquery('english', %s)")
        params.append(words)
    if filters.tab is not None:
        conditions.append("tabs @> array[%s]::text[]")
        params.append(filters.tab)
    if filters.categories:
        conditions.append("category = any(%s)")
        params.append(list(filters.categories))
    if filters.statuses:
        conditions.append("status = any(%s)")
        params.append(list(filters.statuses))
    if filters.sources:
        conditions.append(
            "exists (select 1 from source_records r where r.event_id = events.id"
            " and r.source_id = any(%s))"
        )
        params.append(list(filters.sources))
    if filters.since is not None:
        conditions.append("published_at >= %s")
        params.append(filters.since)
    if filters.until is not None:
        conditions.append("published_at < %s")
        params.append(filters.until)
    if cursor is not None:
        published_at, event_id = decode_cursor(cursor)
        conditions.append("(published_at, id) < (%s, %s)")
        params += [published_at, event_id]

    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            f"select {EVENT_COLUMNS} from events where {' and '.join(conditions)}"
            " order by published_at desc, id desc limit %s",
            [*params, limit + 1],
        ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        events = events_from_rows(cur, rows)
    next_cursor = encode_cursor(rows[-1]["published_at"], rows[-1]["id"]) if has_more else None
    return EventPage(events=events, next_cursor=next_cursor)
