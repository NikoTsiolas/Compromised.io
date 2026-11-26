"""HTTP API seam: FastAPI test client against the test database."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import ingest
from compromised.sources import BLEEPINGCOMPUTER

from .conftest import real_sample


@pytest.fixture
def client(conn, database_url):
    ingest(
        conn,
        BLEEPINGCOMPUTER,
        real_sample("bleepingcomputer.xml"),
        fetched_at=datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC),
    )
    with TestClient(create_app(database_url=database_url)) as test_client:
        yield test_client


def test_events_are_listed_newest_first_and_the_cursor_reaches_the_rest(client):
    first = client.get("/v1/events", params={"limit": 2})
    assert first.status_code == 200
    page = first.json()
    assert [e["title"] for e in page["events"]] == [
        "SYS010 malware abuses browser management to spy on Gmail, Outlook",
        "Palo Alto Networks warns of Fragnesia flaw exploited in PAN-OS attacks",
    ]
    assert page["events"][0]["published_at"] == "2026-11-26T11:50:17Z"
    assert page["events"][0]["sources"][0]["publisher"] == "BleepingComputer"
    assert page["events"][0]["sources"][0]["url"].startswith(
        "https://www.bleepingcomputer.com/news/security/sys010-"
    )

    second = client.get("/v1/events", params={"limit": 2, "cursor": page["next_cursor"]}).json()
    assert [e["title"] for e in second["events"]] == [
        "1Password customer data stolen after employee GitHub account breach"
    ]
    assert second["next_cursor"] is None


def test_a_malformed_cursor_is_a_client_error(client):
    response = client.get("/v1/events", params={"cursor": "not-a-cursor"})
    assert response.status_code == 400


def test_page_size_is_bounded(client):
    assert client.get("/v1/events", params={"limit": 0}).status_code == 422
    assert client.get("/v1/events", params={"limit": 101}).status_code == 422
