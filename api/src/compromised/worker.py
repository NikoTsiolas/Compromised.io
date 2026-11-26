"""Ingestion worker process.

uv run python -m compromised.worker          # poll every source on its interval, forever
uv run python -m compromised.worker --once   # one pass over every source, then exit
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import UTC, datetime

import httpx
import psycopg

from compromised import config
from compromised.pipeline import IngestResult, ingest
from compromised.pipeline.fetcher import FetchError, fetch
from compromised.sources import REGISTRY

log = logging.getLogger("compromised.worker")


async def run_once(
    conn: psycopg.Connection, *, client: httpx.AsyncClient, user_agent: str, sources=REGISTRY
) -> dict[str, IngestResult | None]:
    """Fetch and ingest each source once. A failing source is logged and does not stop others."""
    results: dict[str, IngestResult | None] = {}
    for source in sources:
        try:
            body = await fetch(client, source, user_agent=user_agent)
            result = ingest(conn, source, body, fetched_at=datetime.now(UTC))
        except FetchError as exc:
            log.warning("fetch failed", extra={"source": source.id, "error": str(exc)})
            results[source.id] = None
            continue
        log.info(
            "ingested",
            extra={"source": source.id, "items": result.items, "new_events": result.new_events},
        )
        results[source.id] = result
    return results


async def run_forever(settings: config.Settings) -> None:
    next_due = {source.id: 0.0 for source in REGISTRY}
    async with httpx.AsyncClient() as client:
        while True:
            now = time.monotonic()
            due = [s for s in REGISTRY if next_due[s.id] <= now]
            if due:
                with psycopg.connect(settings.database_url, autocommit=True) as conn:
                    await run_once(conn, client=client, user_agent=settings.user_agent, sources=due)
                for source in due:
                    next_due[source.id] = now + source.interval_seconds
            await asyncio.sleep(max(1.0, min(next_due.values()) - time.monotonic()))


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

    settings = config.load()
    if args.once:

        async def once():
            async with httpx.AsyncClient() as client:
                with psycopg.connect(settings.database_url, autocommit=True) as conn:
                    await run_once(conn, client=client, user_agent=settings.user_agent)

        asyncio.run(once())
    else:
        asyncio.run(run_forever(settings))


if __name__ == "__main__":
    main()
