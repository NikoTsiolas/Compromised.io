"""Load captured feed samples into a database for browser tests.

    uv run python -m compromised.seed --reset bleepingcomputer=tests/fixtures/real/bleepingcomputer.xml

    --sample-enrichment tests/fixtures/synthetic/enrichment-replies.json

Test data only: refuses to run when ENVIRONMENT=production. The model is never called: with
``--sample-enrichment`` the enricher replays stand-in replies keyed by headline, and events with
none stay on rules.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from compromised import config, sources, storage
from compromised.pipeline import enricher, ingest


class ReplayModel:
    """Replays stored replies by headline; any other item finds the model unavailable."""

    def __init__(self, replies: dict[str, dict]):
        self.replies = replies

    def complete(self, item: enricher.UntrustedItem) -> str:
        if item.headline not in self.replies:
            raise enricher.ModelUnavailable("no sample reply")
        return json.dumps(self.replies[item.headline])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="compromised.seed")
    parser.add_argument("samples", nargs="+", metavar="SOURCE_ID=PATH")
    parser.add_argument("--reset", action="store_true", help="empty the event tables first")
    parser.add_argument(
        "--sample-enrichment", metavar="PATH", help="stand-in model replies keyed by headline"
    )
    args = parser.parse_args(argv)

    settings = config.load()
    if settings.environment == "production":
        raise SystemExit("refusing to load test samples into a production database")

    storage.migrate(settings.database_url)
    replay = None
    if args.sample_enrichment:
        replies = json.loads(Path(args.sample_enrichment).read_text())
        replies.pop("_comment", None)
        replay = enricher.Enricher(ReplayModel(replies))
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if args.reset:
            storage.reset_for_tests(conn)
        for sample in args.samples:
            source_id, _, path = sample.partition("=")
            now = datetime.now(UTC)
            result = ingest(conn, sources.by_id(source_id), Path(path).read_bytes(), fetched_at=now)
            # Loading a sample stands in for one successful check of that source.
            storage.record_success(conn, source_id, now, etag=None, last_modified=None)
            print(f"{path}: {result.new_events} new event(s)")
        if replay is not None:
            # After every sample, so an item never waits behind another's "unavailable".
            enriched = sum(replay.enrich(conn, i).enriched for i in storage.all_event_ids(conn))
            print(f"{enriched} event(s) given sample enrichment")


if __name__ == "__main__":
    main()
