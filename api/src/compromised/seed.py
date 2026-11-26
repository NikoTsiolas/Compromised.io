"""Load captured feed samples into a database for browser tests.

    uv run python -m compromised.seed --reset bleepingcomputer=tests/fixtures/real/bleepingcomputer.xml

Test data only: refuses to run when ENVIRONMENT=production.
"""

import argparse
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from compromised import config, sources, storage
from compromised.pipeline import ingest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="compromised.seed")
    parser.add_argument("samples", nargs="+", metavar="SOURCE_ID=PATH")
    parser.add_argument("--reset", action="store_true", help="empty the event tables first")
    args = parser.parse_args(argv)

    settings = config.load()
    if settings.environment == "production":
        raise SystemExit("refusing to load test samples into a production database")

    storage.migrate(settings.database_url)
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if args.reset:
            storage.reset_for_tests(conn)
        for sample in args.samples:
            source_id, _, path = sample.partition("=")
            result = ingest(
                conn,
                sources.by_id(source_id),
                Path(path).read_bytes(),
                fetched_at=datetime.now(UTC),
            )
            print(f"{path}: {result.new_events} new event(s)")


if __name__ == "__main__":
    main()
