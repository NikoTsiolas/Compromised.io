"""Ingestion worker process.

uv run python -m compromised.worker          # poll every source on its own interval, forever
uv run python -m compromised.worker --once   # one pass over every source, then exit

Each source is due ``interval_seconds`` after its last check (stored in the database, so a
restart does not re-poll everything). Due sources are fetched concurrently and stored one by
one. A source that fails to fetch or parse is recorded as failing and never stops the others.
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import psycopg

from compromised import config, storage
from compromised.pipeline import ParseError, ingest, msrc
from compromised.pipeline.fetcher import FetchError, FetchPolicy, FetchResult, Validators, fetch
from compromised.sources import REGISTRY, Source, allowed_hosts

log = logging.getLogger("compromised.worker")

TICK_SECONDS = 15


@dataclass(frozen=True)
class Fetched:
    result: FetchResult
    ratings: dict[str, msrc.Rating] | None = None  # MSRC only: Microsoft's ratings (SUG API)


@dataclass(frozen=True)
class PollOutcome:
    error: str | None = None
    not_modified: bool = False
    items: int | None = None  # None when nothing was parsed
    new_events: int = 0
    grouped: int = 0  # records that joined an event already stored


def due(conn: psycopg.Connection, sources: tuple[Source, ...], *, now: datetime) -> list[Source]:
    """Sources never checked, or whose last check is at least one interval old."""
    rows = storage.source_rows(conn, [s.id for s in sources])
    out = []
    for source in sources:
        last = rows.get(source.id, {}).get("last_attempt_at")
        if last is None or now - last >= timedelta(seconds=source.interval_seconds):
            out.append(source)
    return out


async def run_once(
    conn: psycopg.Connection,
    *,
    client: httpx.AsyncClient,
    policy: FetchPolicy,
    sources: tuple[Source, ...] | list[Source] = REGISTRY,
    now: datetime | None = None,
) -> dict[str, PollOutcome]:
    """Fetch and store each source once, recording its health."""
    now = now or datetime.now(UTC)
    validators = {}
    for source in sources:
        storage.upsert_source(conn, source)
        validators[source.id] = Validators(*storage.stored_validators(conn, source.id))
    rows = storage.source_rows(conn, [s.id for s in sources])
    fetched = await asyncio.gather(
        *(
            _fetch(
                client,
                s,
                policy,
                validators[s.id],
                _rate_window(s, rows.get(s.id, {}).get("last_success_at"), now),
            )
            for s in sources
        )
    )
    return {
        source.id: _store(conn, source, result, now)
        for source, result in zip(sources, fetched, strict=True)
    }


@dataclass(frozen=True)
class RateWindow:
    """MSRC entries first published since ``released_after`` (the backfill window) and revised
    since ``since`` (the last successful check, or the window on a first run) are looked up."""

    since: datetime
    released_after: datetime


def _rate_window(source: Source, last_success: datetime | None, now: datetime) -> RateWindow:
    oldest = now - timedelta(days=source.backfill_days or 30)
    return RateWindow(
        since=max(last_success, oldest) if last_success else oldest, released_after=oldest
    )


async def _fetch(client, source, policy, validators, window: RateWindow) -> Fetched | FetchError:
    try:
        result = await fetch(client, source, policy, validators)
        if source.format != "msrc" or result.not_modified:
            return Fetched(result)
        try:
            cves = msrc.cves_to_rate(
                msrc.parse(result.body), since=window.since, released_after=window.released_after
            )
        except ParseError:
            return Fetched(result)  # ingest reports the parse error
        return Fetched(result, await msrc.lookup(client, policy, cves))
    except FetchError as exc:
        return exc


def _store(
    conn: psycopg.Connection, source: Source, fetched: Fetched | FetchError, now: datetime
) -> PollOutcome:
    if isinstance(fetched, FetchError):
        return _failed(conn, source, now, str(fetched))
    result = fetched.result
    if result.not_modified:
        storage.record_success(
            conn,
            source.id,
            now,
            etag=result.validators.etag,
            last_modified=result.validators.last_modified,
        )
        log.info("not modified", extra={"source": source.id})
        return PollOutcome(not_modified=True)
    try:
        ingested = ingest(conn, source, result.body, fetched_at=now, ratings=fetched.ratings)
    except ParseError as exc:
        return _failed(conn, source, now, str(exc))
    except Exception as exc:  # one source's bad data must not stop the others
        log.exception("ingest failed", extra={"source": source.id})
        return _failed(conn, source, now, f"ingest failed: {type(exc).__name__}")
    storage.record_success(
        conn,
        source.id,
        now,
        etag=result.validators.etag,
        last_modified=result.validators.last_modified,
    )
    log.info(
        "ingested",
        extra={
            "source": source.id,
            "items": ingested.items,
            "new_events": ingested.new_events,
            "grouped": ingested.grouped,
        },
    )
    return PollOutcome(
        items=ingested.items, new_events=ingested.new_events, grouped=ingested.grouped
    )


def _failed(conn: psycopg.Connection, source: Source, now: datetime, error: str) -> PollOutcome:
    storage.record_failure(conn, source.id, now, error)
    log.warning("source failed", extra={"source": source.id, "error": error})
    return PollOutcome(error=error)


def policy_from(settings: config.Settings) -> FetchPolicy:
    return FetchPolicy(user_agent=settings.user_agent, allowed_hosts=allowed_hosts())


async def run_forever(settings: config.Settings) -> None:
    policy = policy_from(settings)
    async with httpx.AsyncClient() as client:
        while True:
            try:
                with psycopg.connect(settings.database_url, autocommit=True) as conn:
                    sources = due(conn, REGISTRY, now=datetime.now(UTC))
                    if sources:
                        await run_once(conn, client=client, policy=policy, sources=sources)
            except Exception:
                log.exception("pass failed")
            await asyncio.sleep(TICK_SECONDS)


class JsonFormatter(logging.Formatter):
    _STANDARD = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message"}

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in self._STANDARD})
        return json.dumps(payload, default=str)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="compromised.worker")
    parser.add_argument("--once", action="store_true", help="one pass over every source")
    args = parser.parse_args(argv)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = config.load()
    if args.once:

        async def once():
            async with httpx.AsyncClient() as client:
                with psycopg.connect(settings.database_url, autocommit=True) as conn:
                    await run_once(conn, client=client, policy=policy_from(settings))

        asyncio.run(once())
    else:
        asyncio.run(run_forever(settings))


if __name__ == "__main__":
    main()
