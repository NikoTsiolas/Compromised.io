"""Storage: PostgreSQL access and SQL migrations. All queries are parameterised."""

import base64
import binascii
from datetime import date, datetime, timedelta
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
    conn.execute(
        "truncate article_previews, source_record_revisions, source_records, events, sources,"
        " enrichment_usage, kev_catalog_entries, kev_catalog"
        " restart identity cascade"
    )


# --- writes -----------------------------------------------------------------------------------


def upsert_source(conn: psycopg.Connection, source: Source) -> None:
    """Mirror a registry entry into the sources table, keeping its health columns."""
    conn.execute(
        "insert into sources (id, name, endpoint, tier, weight, interval_seconds, government,"
        " organization) values (%s, %s, %s, %s, %s, %s, %s, %s)"
        " on conflict (id) do update set name = excluded.name, endpoint = excluded.endpoint,"
        " tier = excluded.tier, weight = excluded.weight,"
        " interval_seconds = excluded.interval_seconds, government = excluded.government,"
        " organization = excluded.organization",
        (
            source.id,
            source.name,
            source.endpoint,
            str(source.tier),
            source.weight,
            source.interval_seconds,
            source.government,
            source.organization,
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
    """Whether this source already gave us this item (same canonical URL or same guid)."""
    row = conn.execute(
        "select 1 from source_records where source_id = %s"
        " and (canonical_url = %s or guid = %s) limit 1",
        (record.source_id, record.canonical_url, record.guid),
    ).fetchone()
    return row is not None


def event_with_canonical_url(conn: psycopg.Connection, canonical_url: str) -> int | None:
    """The event of the earliest stored record, from any source, with this canonical URL."""
    row = conn.execute(
        "select event_id from source_records where canonical_url = %s order by id limit 1",
        (canonical_url,),
    ).fetchone()
    return row[0] if row else None


def event_sharing_a_cve(
    conn: psycopg.Connection, *, cves: tuple[str, ...], published_at: datetime, window: timedelta
) -> int | None:
    """The event with a record naming one of ``cves`` published within ``window`` of
    ``published_at``; the nearest in time if several."""
    if not cves:
        return None
    row = conn.execute(
        "select event_id from source_records where cves && %s::text[]"
        " and published_at between %s and %s"
        " order by abs(extract(epoch from published_at - %s)), event_id limit 1",
        (list(cves), published_at - window, published_at + window, published_at),
    ).fetchone()
    return row[0] if row else None


def event_with_similar_headline(
    conn: psycopg.Connection,
    *,
    organization: str,
    source_id: str,
    headline: str,
    published_at: datetime,
    cves: tuple[str, ...],
    window: timedelta,
    threshold: float,
) -> int | None:
    """The event about this organization (catalog key or name) holding the headline most similar
    to ``headline``, if that similarity reaches ``threshold``, counting only records from other
    sources published within ``window`` of ``published_at``.

    An event whose records name CVEs, none of them in ``cves`` (when ``cves`` is not empty), is
    a different flaw and never matches."""
    row = conn.execute(
        "select r.event_id from source_records r join events e on e.id = r.event_id"
        " where lower(coalesce(e.organization_key, e.organization)) = lower(%s)"
        " and r.source_id <> %s and r.published_at between %s and %s and similarity(r.headline, %s) >= %s"
        " and (cardinality(%s::text[]) = 0 or not exists ("
        "   select 1 from source_records c where c.event_id = e.id and c.cves <> '{}'"
        "   having not bool_or(c.cves && %s::text[])))"
        " order by similarity(r.headline, %s) desc, r.event_id limit 1",
        (
            organization,
            source_id,
            published_at - window,
            published_at + window,
            headline,
            threshold,
            list(cves),
            list(cves),
            headline,
        ),
    ).fetchone()
    return row[0] if row else None


def record_event(conn: psycopg.Connection, record_id: int) -> int:
    row = conn.execute("select event_id from source_records where id = %s", (record_id,)).fetchone()
    if row is None:
        raise KeyError(record_id)
    return row[0]


def set_record_event(conn: psycopg.Connection, record_id: int, event_id: int) -> None:
    """Reassign a record. Its content stays as stored (the database refuses any other change)."""
    conn.execute("update source_records set event_id = %s where id = %s", (event_id, record_id))


def delete_event_if_empty(conn: psycopg.Connection, event_id: int) -> bool:
    deleted = conn.execute(
        "delete from events e where id = %s"
        " and not exists (select 1 from source_records where event_id = e.id)",
        (event_id,),
    ).rowcount
    return deleted > 0


def create_event(conn: psycopg.Connection, record: SourceRecord) -> int:
    row = conn.execute(
        "insert into events (title, published_at, first_seen_at, last_updated_at)"
        " values (%s, %s, %s, %s) returning id",
        (record.headline, record.published_at, record.fetched_at, record.fetched_at),
    ).fetchone()
    return row[0]


def refresh_event_header(conn: psycopg.Connection, event_id: int) -> None:
    """Re-derive an event's title and times from its records: the title is the earliest
    record's original headline, published_at that record's time, first_seen_at the earliest
    fetch and last_updated_at the latest."""
    conn.execute(
        "update events e set title = lead.headline, published_at = lead.published_at,"
        " first_seen_at = span.first_seen, last_updated_at = span.last_seen"
        " from (select headline, published_at from source_records where event_id = %s"
        "       order by published_at, id limit 1) lead,"
        "      (select min(fetched_at) first_seen, max(fetched_at) last_seen"
        "       from source_records where event_id = %s) span"
        " where e.id = %s",
        (event_id, event_id, event_id),
    )


def insert_record(conn: psycopg.Connection, record: SourceRecord, event_id: int) -> None:
    conn.execute(
        "insert into source_records (source_id, guid, canonical_url, original_url, headline,"
        " excerpt, published_at, fetched_at, metadata, cves, event_id, image_url)"
        " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
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
            list(record.cves),
            event_id,
            record.image_url,
        ),
    )


def append_record_revision(conn: psycopg.Connection, record: SourceRecord) -> int | None:
    """Append a revision to the stored record with the same source and guid, holding the
    metadata fields whose values differ from its effective metadata (``EFFECTIVE_METADATA``).

    The stored record itself is never changed. Returns the record's event id if a revision was
    appended, else None (nothing stored under that guid, or nothing changed).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            f"select r.id, r.event_id, {EFFECTIVE_METADATA} as metadata from source_records r"
            " where r.source_id = %s and r.guid = %s",
            (record.source_id, record.guid),
        ).fetchone()
    if row is None:
        return None
    changed = {k: v for k, v in record.metadata.items() if row["metadata"].get(k) != v}
    if not changed:
        return None
    revised_at = record.metadata.get("revised_at")
    conn.execute(
        "insert into source_record_revisions (record_id, fetched_at, revised_at, metadata)"
        " values (%s, %s, %s, %s)",
        (row["id"], record.fetched_at, revised_at, Jsonb(changed)),
    )
    return row["event_id"]


def record_revisions(conn: psycopg.Connection, record_id: int) -> list[dict]:
    """A record's revisions in the order they were appended: fetched_at, revised_at, metadata."""
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select fetched_at, revised_at, metadata from source_record_revisions"
            " where record_id = %s order by id",
            (record_id,),
        ).fetchall()


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


def save_trust(conn: psycopg.Connection, event_id: int, assessment) -> None:
    """Store an event's verification status, label, score and the publishers the score counted
    (pipeline.verifier.Assessment), or clear all four when ``assessment`` is None: commentary is
    not an incident and carries no label or score."""
    if assessment is None:
        conn.execute(
            "update events set status = null, status_label = null, score = null,"
            " score_sources = '{}' where id = %s",
            (event_id,),
        )
        return
    conn.execute(
        "update events set status = %s, status_label = %s, score = %s, score_sources = %s"
        " where id = %s",
        (
            assessment.status,
            assessment.label,
            assessment.score,
            list(assessment.sources),
            event_id,
        ),
    )


def registered_sources(conn: psycopg.Connection, source_ids) -> dict[str, dict]:
    """The registry mirror's name, tier, weight, government flag and organization, by id."""
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            "select id, name, tier, weight, government, organization from sources"
            " where id = any(%s)",
            (list(source_ids),),
        ).fetchall()
    return {r["id"]: r for r in rows}


def save_action_line(conn: psycopg.Connection, event_id: int, action_line: str | None) -> None:
    conn.execute("update events set action_line = %s where id = %s", (action_line, event_id))


# --- enrichment (#8) --------------------------------------------------------------------------


def take_enrichment_call(conn: psycopg.Connection, day, cap: int) -> bool:
    """Count one model call against ``day``'s cap. False, and nothing counted, once it is reached."""
    if cap <= 0:
        return False
    row = conn.execute(
        "insert into enrichment_usage as u (day, calls) values (%s, 1)"
        " on conflict (day) do update set calls = u.calls + 1 where u.calls < %s"
        " returning calls",
        (day, cap),
    ).fetchone()
    return row is not None


def enrichment_calls(conn: psycopg.Connection, day) -> int:
    row = conn.execute("select calls from enrichment_usage where day = %s", (day,)).fetchone()
    return row[0] if row else 0


def save_enrichment(conn: psycopg.Connection, event_id: int, enrichment, *, at: datetime) -> None:
    """Store a checked model reply (pipeline.enricher.Enrichment). Touches enrichment columns only."""
    conn.execute(
        "update events set enrichment_state = 'enriched', enriched_at = %s, summary = %s,"
        " ai_category = %s, ai_commentary = %s, ai_organization = %s, ai_action_line = %s"
        " where id = %s",
        (
            at,
            enrichment.summary,
            enrichment.category,
            enrichment.commentary,
            enrichment.organization,
            enrichment.action_line,
            event_id,
        ),
    )


def record_rejected_enrichment(conn: psycopg.Connection, event_id: int) -> None:
    conn.execute(
        "update events set enrichment_attempts = enrichment_attempts + 1 where id = %s",
        (event_id,),
    )


def enrichment_of(conn: psycopg.Connection, event_id: int) -> dict | None:
    """The model's stored output for an event, or None if it was never enriched."""
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            "select ai_category as category, ai_commentary as commentary,"
            " ai_organization as organization, ai_action_line as action_line"
            " from events where id = %s and enrichment_state = 'enriched'",
            (event_id,),
        ).fetchone()
    return row


def awaiting_enrichment(conn: psycopg.Connection, limit: int, max_rejected: int) -> list[int]:
    """Events not yet enriched, newest first, skipping those whose replies keep being rejected."""
    rows = conn.execute(
        "select id from events where enrichment_state = 'awaiting'"
        " and enrichment_attempts < %s order by published_at desc, id desc limit %s",
        (max_rejected, limit),
    ).fetchall()
    return [r[0] for r in rows]


# --- reads ------------------------------------------------------------------------------------


# The only place that knows about revisions: the effective metadata of the source record ``r``
# is its own, overlaid with its revisions' changed fields in the order they were appended
# (jsonb_object_agg keeps the last value of a repeated key). Everything the pipeline derives
# from metadata (extractor, classifier, scope, the vulnerability gate, later #7) reads records
# through ``event_records`` / ``record_by_id`` and so sees the latest rating.
EFFECTIVE_METADATA = (
    "(r.metadata || coalesce((select jsonb_object_agg(e.key, e.value order by v.id)"
    " from source_record_revisions v cross join jsonb_each(v.metadata) e"
    " where v.record_id = r.id), '{}'::jsonb))"
)

_RECORD_COLUMNS = (
    "r.source_id, r.guid, r.canonical_url, r.original_url, r.headline, r.excerpt,"
    f" r.published_at, r.fetched_at, {EFFECTIVE_METADATA} as metadata, r.cves, r.image_url"
)


def event_records(conn: psycopg.Connection, event_id: int) -> list[SourceRecord]:
    """An event's source records, earliest first, with their effective metadata."""
    return _records(
        conn,
        f"select {_RECORD_COLUMNS} from source_records r where r.event_id = %s"
        " order by r.published_at, r.id",
        event_id,
    )


def record_by_id(conn: psycopg.Connection, record_id: int) -> SourceRecord:
    """A source record with its effective metadata."""
    [record] = _records(
        conn, f"select {_RECORD_COLUMNS} from source_records r where r.id = %s", record_id
    )
    return record


def _records(conn, query: str, *params) -> list[SourceRecord]:
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(query, params).fetchall()
    return [SourceRecord(**{**r, "cves": tuple(r["cves"])}) for r in rows]


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
            " organization_key, logo_key, tabs, summary, action_line, enrichment_state,"
            " status, status_label, score, score_sources"
            f" from events {where}"
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
            summary=r["summary"],
            action_line=r["action_line"],
            enrichment="ai" if r["enrichment_state"] == "enriched" else "rules",
            status=r["status"],
            status_label=r["status_label"],
            score=r["score"],
            score_sources=tuple(r["score_sources"]),
        )
        for r in rows
    ]
    next_cursor = _encode_cursor(rows[-1]["published_at"], rows[-1]["id"]) if has_more else None
    return EventPage(events=events, next_cursor=next_cursor)


def _sources_for(cur, event_ids: list[int]) -> dict[int, list[EventSource]]:
    if not event_ids:
        return {}
    rows = cur.execute(
        "select r.event_id, r.id, s.id as source_id, s.name, r.original_url, r.headline,"
        " r.excerpt, r.published_at, coalesce(r.image_url, p.image_url) as image_url"
        " from source_records r join sources s on s.id = r.source_id"
        " left join article_previews p on p.record_id = r.id"
        " where r.event_id = any(%s) order by r.published_at, r.id",
        (event_ids,),
    ).fetchall()
    out: dict[int, list[EventSource]] = {}
    for r in rows:
        out.setdefault(r["event_id"], []).append(
            EventSource(
                record_id=r["id"],
                publisher=r["name"],
                url=r["original_url"],
                headline=r["headline"],
                excerpt=r["excerpt"],
                published_at=r["published_at"],
                image_url=r["image_url"],
                source_id=r["source_id"],
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


# --- article previews (pipeline.previews) ------------------------------------------------------


def records_awaiting_preview(
    conn: psycopg.Connection, source_id: str, *, limit: int
) -> list[tuple[int, str]]:
    """The source's newest records with no image that have never been asked for a preview."""
    rows = conn.execute(
        "select r.id, r.original_url from source_records r"
        " left join article_previews p on p.record_id = r.id"
        " where r.source_id = %s and r.image_url is null and p.record_id is null"
        " order by r.published_at desc, r.id desc limit %s",
        (source_id, limit),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def save_preview(
    conn: psycopg.Connection, record_id: int, image_url: str | None, state: str, at: datetime
) -> None:
    """Record the one attempt at a record's article preview (the record itself never changes)."""
    conn.execute(
        "insert into article_previews (record_id, state, image_url, attempted_at)"
        " values (%s, %s, %s, %s) on conflict (record_id) do nothing",
        (record_id, state, image_url, at),
    )


# --- the KEV catalog behind the widgets (#15) ---------------------------------------------------


def replace_kev_catalog(conn: psycopg.Connection, catalog, *, fetched_at: datetime) -> None:
    """Replace the stored catalog with ``catalog`` (adapters.KevCatalog), in one transaction."""
    with conn.transaction():
        conn.execute("delete from kev_catalog_entries")
        with conn.cursor() as cur:
            cur.executemany(
                "insert into kev_catalog_entries (cve, vendor, product, name, date_added,"
                " known_ransomware_use) values (%s, %s, %s, %s, %s, %s)",
                [
                    (e.cve, e.vendor, e.product, e.name, e.date_added, e.known_ransomware_use)
                    for e in catalog.entries
                ],
            )
        conn.execute(
            "insert into kev_catalog (version, declared_count, entries, fetched_at)"
            " values (%s, %s, %s, %s) on conflict (id) do update set version = excluded.version,"
            " declared_count = excluded.declared_count, entries = excluded.entries,"
            " fetched_at = excluded.fetched_at",
            (catalog.version, catalog.declared_count, len(catalog.entries), fetched_at),
        )


def kev_catalog_info(conn: psycopg.Connection) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select version, declared_count, entries, fetched_at from kev_catalog"
        ).fetchone()


def kev_monthly_counts(conn: psycopg.Connection, first: date, last: date) -> dict[date, int]:
    """Entries added per calendar month (keyed by the month's first day), ``first`` to ``last``."""
    rows = conn.execute(
        "select date_trunc('month', date_added)::date, count(*) from kev_catalog_entries"
        " where date_added >= %s and date_added < (%s::date + interval '1 month')"
        " group by 1",
        (first, last),
    ).fetchall()
    return {month: count for month, count in rows}


def kev_entries(
    conn: psycopg.Connection, *, since: date | None = None, before: date | None = None
) -> list[dict]:
    """Stored catalog entries, newest added first (then by CVE), optionally within dates."""
    conditions, params = [], []
    if since is not None:
        conditions.append("date_added >= %s")
        params.append(since)
    if before is not None:
        conditions.append("date_added < %s")
        params.append(before)
    where = f"where {' and '.join(conditions)}" if conditions else ""
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select cve, vendor, product, name, date_added, known_ransomware_use"
            f" from kev_catalog_entries {where} order by date_added desc, cve desc",
            params,
        ).fetchall()


def events_per_organisation(
    conn: psycopg.Connection, *, since: datetime, until: datetime, limit: int
) -> list[dict]:
    """Distinct All-tab events per organisation published in [since, until], most first.

    Grouped by catalog key, else by the name case-folded; the name shown is the one on the most
    recent event. All-tab events exclude commentary, research and claim-only events by the
    scope rules (pipeline.scope.tabs_for); ``not claim_only`` restates the claims rule here.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select (array_agg(organization order by published_at desc, id desc))[1] as name,"
            " min(organization_key) as key,"
            " (array_agg(logo_key order by published_at desc, id desc))[1] as logo_key,"
            " count(*)::int as count"
            " from events"
            " where tabs @> array['all']::text[] and not commentary and not claim_only"
            " and organization is not null and published_at >= %s and published_at <= %s"
            " group by coalesce(organization_key, lower(organization))"
            " order by count(*) desc, max(published_at) desc, 1 limit %s",
            (since, until, limit),
        ).fetchall()
