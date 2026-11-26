"""Storage: PostgreSQL access and SQL migrations. All queries are parameterised."""

import base64
import binascii
from datetime import datetime
from importlib import resources

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from compromised.records import Event, EventPage, EventSource, SourceRecord
from compromised.sources import Source

MAX_PAGE_SIZE = 100


class InvalidCursor(ValueError):
    pass


# --- migrations -------------------------------------------------------------------------------


def migrate(database_url: str) -> list[str]:
    """Apply pending migrations from storage/migrations in name order. Returns those applied."""
    files = sorted(
        (
            f
            for f in resources.files(__package__).joinpath("migrations").iterdir()
            if f.name.endswith(".sql")
        ),
        key=lambda f: f.name,
    )
    applied = []
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "create table if not exists schema_migrations ("
            " version text primary key, applied_at timestamptz not null default now())"
        )
        conn.commit()
        done = {row[0] for row in conn.execute("select version from schema_migrations")}
        for f in files:
            version = f.name.removesuffix(".sql")
            if version in done:
                continue
            with conn.transaction():
                conn.execute(f.read_text())
                conn.execute("insert into schema_migrations (version) values (%s)", (version,))
            applied.append(version)
    return applied


def reset_for_tests(conn: psycopg.Connection) -> None:
    conn.execute("truncate source_records, events, sources restart identity cascade")


# --- writes -----------------------------------------------------------------------------------


def upsert_source(conn: psycopg.Connection, source: Source) -> None:
    """Mirror a registry entry into the sources table, keeping its health columns."""
    conn.execute(
        "insert into sources (id, name, endpoint, tier, weight, interval_seconds)"
        " values (%s, %s, %s, %s, %s, %s)"
        " on conflict (id) do update set name = excluded.name, endpoint = excluded.endpoint,"
        " tier = excluded.tier, weight = excluded.weight,"
        " interval_seconds = excluded.interval_seconds",
        (
            source.id,
            source.name,
            source.endpoint,
            str(source.tier),
            source.weight,
            source.interval_seconds,
        ),
    )


def stored_validators(conn: psycopg.Connection, source_id: str) -> tuple[str | None, str | None]:
    """(ETag, Last-Modified) of the source's last stored full response."""
    row = conn.execute(
        "select etag, last_modified from sources where id = %s", (source_id,)
    ).fetchone()
    return (row[0], row[1]) if row else (None, None)


def record_success(
    conn: psycopg.Connection,
    source_id: str,
    at: datetime,
    *,
    etag: str | None,
    last_modified: str | None,
) -> None:
    conn.execute(
        "update sources set last_attempt_at = %s, last_success_at = %s,"
        " consecutive_failures = 0, etag = %s, last_modified = %s where id = %s",
        (at, at, etag, last_modified, source_id),
    )


def record_failure(conn: psycopg.Connection, source_id: str, at: datetime, error: str) -> None:
    conn.execute(
        "update sources set last_attempt_at = %s, last_error = %s, last_error_at = %s,"
        " consecutive_failures = consecutive_failures + 1 where id = %s",
        (at, error[:500], at, source_id),
    )


def source_rows(conn: psycopg.Connection, source_ids: list[str]) -> dict[str, dict]:
    """Stored health columns by source id; sources never checked are absent."""
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            "select id, last_attempt_at, last_success_at, last_error, last_error_at,"
            " consecutive_failures from sources where id = any(%s)",
            (source_ids,),
        ).fetchall()
    return {r["id"]: r for r in rows}


def record_exists(conn: psycopg.Connection, record: SourceRecord) -> bool:
    row = conn.execute(
        "select 1 from source_records where canonical_url = %s"
        " or (source_id = %s and guid = %s) limit 1",
        (record.canonical_url, record.source_id, record.guid),
    ).fetchone()
    return row is not None


def create_event(conn: psycopg.Connection, record: SourceRecord) -> int:
    row = conn.execute(
        "insert into events (title, published_at, first_seen_at, last_updated_at)"
        " values (%s, %s, %s, %s) returning id",
        (record.headline, record.published_at, record.fetched_at, record.fetched_at),
    ).fetchone()
    return row[0]


def insert_record(conn: psycopg.Connection, record: SourceRecord, event_id: int) -> None:
    conn.execute(
        "insert into source_records (source_id, guid, canonical_url, original_url, headline,"
        " excerpt, published_at, fetched_at, metadata, event_id)"
        " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            record.source_id,
            record.guid,
            record.canonical_url,
            record.original_url,
            record.headline,
            record.excerpt,
            record.published_at,
            record.fetched_at,
            Jsonb(record.metadata),
            event_id,
        ),
    )


def save_classification(conn: psycopg.Connection, event_id: int, facts, tabs) -> None:
    """Store an event's classification facts (pipeline.scope.EventFacts) and its tabs."""
    conn.execute(
        "update events set category = %s, commentary = %s, organization = %s,"
        " organization_key = %s, logo_key = %s, people_use = %s, exploited = %s,"
        " critical = %s, claim_only = %s, tabs = %s where id = %s",
        (
            facts.category,
            facts.commentary,
            facts.organization,
            facts.organization_key,
            facts.logo,
            facts.people_use,
            facts.exploited,
            facts.critical,
            facts.claim_only,
            sorted(tabs),
            event_id,
        ),
    )


# --- reads ------------------------------------------------------------------------------------


def event_records(conn: psycopg.Connection, event_id: int) -> list[SourceRecord]:
    """An event's source records, earliest first."""
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            "select source_id, guid, canonical_url, original_url, headline, excerpt,"
            " published_at, fetched_at, metadata from source_records"
            " where event_id = %s order by published_at, id",
            (event_id,),
        ).fetchall()
    return [SourceRecord(**r) for r in rows]


def all_event_ids(conn: psycopg.Connection) -> list[int]:
    return [row[0] for row in conn.execute("select id from events order by id")]


def list_events(
    conn: psycopg.Connection,
    *,
    limit: int = 20,
    cursor: str | None = None,
    tab: str | None = None,
) -> EventPage:
    """Events newest first (by publication time, then id), keyset-paginated by an opaque cursor.

    ``tab`` keeps only events in that feed tab; None lists every stored event.
    """
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    params: list = []
    conditions = []
    if cursor is not None:
        published_at, event_id = _decode_cursor(cursor)
        conditions.append("(published_at, id) < (%s, %s)")
        params += [published_at, event_id]
    if tab is not None:
        conditions.append("tabs @> array[%s]::text[]")
        params.append(tab)
    where = f"where {' and '.join(conditions)}" if conditions else ""
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            "select id, title, published_at, first_seen_at, category, commentary, organization,"
            f" organization_key, logo_key, tabs from events {where}"
            " order by published_at desc, id desc limit %s",
            [*params, limit + 1],
        ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        sources = _sources_for(cur, [r["id"] for r in rows])
    events = [
        Event(
            id=r["id"],
            title=r["title"],
            published_at=r["published_at"],
            first_seen_at=r["first_seen_at"],
            sources=sources.get(r["id"], []),
            category=r["category"],
            commentary=r["commentary"],
            affected_organization=r["organization"] or "unknown",
            organization_key=r["organization_key"],
            logo_key=r["logo_key"],
            tabs=tuple(r["tabs"]),
        )
        for r in rows
    ]
    next_cursor = _encode_cursor(rows[-1]["published_at"], rows[-1]["id"]) if has_more else None
    return EventPage(events=events, next_cursor=next_cursor)


def _sources_for(cur, event_ids: list[int]) -> dict[int, list[EventSource]]:
    if not event_ids:
        return {}
    rows = cur.execute(
        "select r.event_id, s.name, r.original_url, r.headline, r.excerpt, r.published_at"
        " from source_records r join sources s on s.id = r.source_id"
        " where r.event_id = any(%s) order by r.published_at, r.id",
        (event_ids,),
    ).fetchall()
    out: dict[int, list[EventSource]] = {}
    for r in rows:
        out.setdefault(r["event_id"], []).append(
            EventSource(
                publisher=r["name"],
                url=r["original_url"],
                headline=r["headline"],
                excerpt=r["excerpt"],
                published_at=r["published_at"],
            )
        )
    return out


def _encode_cursor(published_at: datetime, event_id: int) -> str:
    raw = f"{published_at.isoformat()}|{event_id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        stamp, event_id = raw.split("|")
        published_at = datetime.fromisoformat(stamp)
        if published_at.tzinfo is None:
            raise ValueError("naive timestamp")
        return published_at, int(event_id)
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise InvalidCursor(cursor) from exc
