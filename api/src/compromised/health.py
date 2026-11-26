"""Source health and overall ingestion status, as shown to readers.

Per source:
  pending  never checked yet
  ok       the last check succeeded (a 304 counts) within 3 polling intervals
  failing  the last check failed
  stale    the last success is older than 3 polling intervals (the worker is not running)

Overall:
  starting no source has been checked successfully yet
  live     every source checked so far is ok
  degraded some sources are ok and some are failing or stale
  down     sources have been checked but none is ok
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from compromised import storage
from compromised.sources import Source, Tier

STALE_AFTER_INTERVALS = 3


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    name: str
    tier: Tier
    interval_seconds: int
    state: str
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    last_error_at: datetime | None
    consecutive_failures: int


@dataclass(frozen=True)
class IngestionStatus:
    status: str
    last_success_at: datetime | None
    sources: list[SourceHealth]


def source_health(
    conn: psycopg.Connection, sources: tuple[Source, ...], *, now: datetime
) -> list[SourceHealth]:
    rows = storage.source_rows(conn, [s.id for s in sources])
    return [_health(source, rows.get(source.id, {}), now) for source in sources]


def ingestion_status(
    conn: psycopg.Connection, sources: tuple[Source, ...], *, now: datetime
) -> IngestionStatus:
    healths = source_health(conn, sources, now=now)
    states = {h.state for h in healths} - {"pending"}
    if not any(h.last_success_at for h in healths):
        status = "starting"
    elif states == {"ok"}:
        status = "live"
    elif "ok" in states:
        status = "degraded"
    else:
        status = "down"
    successes = [h.last_success_at for h in healths if h.last_success_at]
    return IngestionStatus(
        status=status, last_success_at=max(successes, default=None), sources=healths
    )


def _health(source: Source, row: dict, now: datetime) -> SourceHealth:
    failures = row.get("consecutive_failures") or 0
    last_attempt = row.get("last_attempt_at")
    last_success = row.get("last_success_at")
    if last_attempt is None:
        state = "pending"
    elif failures:
        state = "failing"
    elif last_success and now - last_success > timedelta(
        seconds=STALE_AFTER_INTERVALS * source.interval_seconds
    ):
        state = "stale"
    else:
        state = "ok"
    return SourceHealth(
        source_id=source.id,
        name=source.name,
        tier=source.tier,
        interval_seconds=source.interval_seconds,
        state=state,
        last_attempt_at=last_attempt,
        last_success_at=last_success,
        last_error=row.get("last_error"),
        last_error_at=row.get("last_error_at"),
        consecutive_failures=failures,
    )
