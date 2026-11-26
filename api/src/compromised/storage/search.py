"""Search, filters and Trending (#10). All queries are parameterised.

Search scope (decided for Niko at the merge of #10, #11, #15 and #16): every stored event that
is an incident, that is, not commentary, including those the feed rules keep out of every tab
(unknown organization, flaws outside the "people use" list). Each result carries its tabs, so
one in no tab can say it is not shown in the feed. Commentary is never a search result. Results
are newest first and paginated with the feed's cursor (publication time, id). Trending ranks
only events shown in a tab.
"""

import base64
import binascii
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

from compromised.records import EventPage
from compromised.storage import (
    EVENT_COLUMNS,
    MAX_PAGE_SIZE,
    InvalidCursor,
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
    conditions = ["not commentary"]
    params: list = []

    query = clean_query(filters.query)
    cves = sorted({c.upper() for c in CVE.findall(query)})
    words = CVE.sub(" ", query)
    if cves:
        # Exact identifiers: the event names at least one of them.
        conditions.append("cves && %s::text[]")
        params.append(cves)
    if query and not cves and not re.search(r"\w", words):
        # Only punctuation or operators: there is nothing to search for, so nothing matches.
        conditions.append("false")
    elif re.search(r"\w", words):
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


# --- trending -----------------------------------------------------------------------------------

# Trending score: every distinct news or official source that reported the event within the
# window adds 0.5 ^ (hours since that source's latest report on it / half-life). Attacker-claim
# sources add nothing and claim-only events never trend. Only events shown in a tab are ranked.
# Nothing else enters the score: no views, clicks or any other engagement, which does not exist.
TRENDING_WINDOW = timedelta(hours=72)
TRENDING_HALF_LIFE_HOURS = 24
_SCORE_DIGITS = 9  # the score is rounded, so a cursor compares exactly


def trending(
    conn: psycopg.Connection, *, now: datetime, limit: int = 20, cursor: str | None = None
) -> EventPage:
    """Published events by trending score, highest first (ties: newest id first).

    The cursor carries the time the first page was ranked at, so later pages continue the same
    ranking instead of one that has decayed since."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    as_of, after = now, None
    if cursor is not None:
        as_of, after = _decode_trending_cursor(cursor)
    page_condition = ""
    params: dict = {
        "as_of": as_of,
        "since": as_of - TRENDING_WINDOW,
        "half_life": TRENDING_HALF_LIFE_HOURS,
        "digits": _SCORE_DIGITS,
        "limit": limit + 1,
    }
    if after is not None:
        page_condition = "and (s.trend_score, e.id) < (%(after_score)s, %(after_id)s)"
        params |= {"after_score": after[0], "after_id": after[1]}
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            "with coverage as ("
            "  select r.event_id, r.source_id, max(r.published_at) as reported_at"
            "  from source_records r join sources src on src.id = r.source_id"
            "  where src.tier <> 'attacker_claim'"
            "  group by r.event_id, r.source_id),"
            " scored as ("
            "  select event_id, round(sum(power(0.5, greatest(extract(epoch from"
            "    %(as_of)s - reported_at), 0) / 3600.0 / %(half_life)s))::numeric,"
            "    %(digits)s) as trend_score"
            "  from coverage where reported_at > %(since)s group by event_id)"
            f" select {_prefixed('e', EVENT_COLUMNS)}, s.trend_score"
            " from events e join scored s on s.event_id = e.id"
            f" where cardinality(e.tabs) > 0 and not e.claim_only {page_condition}"
            " order by s.trend_score desc, e.id desc limit %(limit)s",
            params,
        ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        events = events_from_rows(cur, rows)
    next_cursor = None
    if has_more:
        next_cursor = _encode_trending_cursor(as_of, rows[-1]["trend_score"], rows[-1]["id"])
    return EventPage(events=events, next_cursor=next_cursor)


def _prefixed(alias: str, columns: str) -> str:
    return ", ".join(f"{alias}.{c.strip()}" for c in columns.split(","))


def _encode_trending_cursor(as_of: datetime, score: Decimal, event_id: int) -> str:
    raw = f"trending|{as_of.isoformat()}|{score}|{event_id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_trending_cursor(cursor: str) -> tuple[datetime, tuple[Decimal, int]]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        kind, stamp, score, event_id = raw.split("|")
        as_of = datetime.fromisoformat(stamp)
        if kind != "trending" or as_of.tzinfo is None:
            raise ValueError(cursor)
        value = Decimal(score)
        if not value.is_finite():
            raise ValueError(cursor)
        return as_of, (value, int(event_id))
    except (binascii.Error, UnicodeDecodeError, ValueError, ArithmeticError) as exc:
        raise InvalidCursor(cursor) from exc
