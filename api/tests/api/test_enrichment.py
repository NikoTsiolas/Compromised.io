"""HTTP API seam: the enricher's summary and action line, as an API client sees them.

Model replies come from a fake client and are synthetic; feed samples are real.
"""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import enricher, ingest
from compromised.sources import BLEEPINGCOMPUTER
from tests.samples import real_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
ONEPASSWORD = "1Password customer data stolen after employee GitHub account breach"


class FakeModel:
    def complete(self, item):
        stated = item.headline == ONEPASSWORD
        return json.dumps(
            {
                "category": "data_breach",
                "affected_organization": None,
                "commentary": False,
                "summary": f"Synthetic summary of: {item.headline}",
                "action_line": "Synthetic: watch for word from 1Password." if stated else None,
                "action_quote": "1Password has disclosed a data breach" if stated else None,
            }
        )


def events_by_title(client) -> dict:
    response = client.get("/v1/events", params={"tab": "all"})
    assert response.status_code == 200, response.text
    return {e["title"]: e for e in response.json()["events"]}


def test_enriched_events_carry_the_ai_summary_and_a_stated_action_line(conn, database_url):
    ingest(
        conn,
        BLEEPINGCOMPUTER,
        real_sample("bleepingcomputer.xml"),
        fetched_at=FETCHED_AT,
        enricher=enricher.Enricher(FakeModel()),
    )
    with TestClient(create_app(database_url=database_url)) as client:
        events = events_by_title(client)

    onepassword = events[ONEPASSWORD]
    assert onepassword["summary"] == f"Synthetic summary of: {ONEPASSWORD}"
    assert onepassword["enrichment"] == "ai"
    assert onepassword["action_line"] == "Synthetic: watch for word from 1Password."


def test_rules_only_events_have_no_summary_and_no_action_line(conn, database_url):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)
    with TestClient(create_app(database_url=database_url)) as client:
        onepassword = events_by_title(client)[ONEPASSWORD]

    assert (onepassword["summary"], onepassword["action_line"], onepassword["enrichment"]) == (
        None,
        None,
        "rules",
    )
