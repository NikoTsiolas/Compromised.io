"""HTTP API seam: source health and overall ingestion status."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from compromised import storage
from compromised.api import create_app
from compromised.sources import REGISTRY


@pytest.fixture
def client(conn, database_url):
    for source in REGISTRY:
        storage.upsert_source(conn, source)
    with TestClient(create_app(database_url=database_url)) as test_client:
        yield test_client


def checked(conn, source_id: str, at: datetime) -> None:
    storage.record_success(conn, source_id, at, etag=None, last_modified=None)


def iso(at: datetime) -> str:
    return at.astimezone(UTC).isoformat().replace("+00:00", "Z")


def test_before_any_check_ingestion_is_starting_and_every_source_is_pending(client):
    body = client.get("/v1/status").json()

    assert body["status"] == "starting"
    assert body["last_success_at"] is None
    assert [s["name"] for s in body["sources"]] == [s.name for s in REGISTRY]
    assert {s["state"] for s in body["sources"]} == {"pending"}


def test_each_source_shows_its_last_successful_check(client, conn):
    now = datetime.now(UTC).replace(microsecond=0)
    checked(conn, "therecord", now - timedelta(minutes=2))
    checked(conn, "krebsonsecurity", now - timedelta(minutes=20))

    body = client.get("/v1/status").json()

    assert body["status"] == "live"
    assert body["last_success_at"] == iso(now - timedelta(minutes=2))
    sources = {s["id"]: s for s in body["sources"]}
    assert sources["therecord"] == {
        "id": "therecord",
        "name": "The Record",
        "tier": "press",
        "interval_seconds": 300,
        "state": "ok",
        "last_attempt_at": iso(now - timedelta(minutes=2)),
        "last_success_at": iso(now - timedelta(minutes=2)),
        "consecutive_failures": 0,
    }
    assert sources["krebsonsecurity"]["state"] == "ok"
    assert sources["unit42"]["state"] == "pending"
    assert sources["unit42"]["tier"] == "official"


def test_a_failing_source_makes_ingestion_degraded_without_exposing_the_error(client, conn):
    now = datetime.now(UTC)
    checked(conn, "therecord", now)
    storage.record_failure(conn, "darkreading", now, "ConnectError: [Errno 61] 10.0.0.5")

    body = client.get("/v1/status").json()

    assert body["status"] == "degraded"
    darkreading = next(s for s in body["sources"] if s["id"] == "darkreading")
    assert (darkreading["state"], darkreading["consecutive_failures"]) == ("failing", 1)
    assert darkreading["last_success_at"] is None
    assert "10.0.0.5" not in client.get("/v1/status").text


def test_when_the_worker_has_stopped_sources_go_stale_and_ingestion_is_down(client, conn):
    hours_ago = datetime.now(UTC) - timedelta(hours=4)
    checked(conn, "therecord", hours_ago)  # polled every 5 minutes
    checked(conn, "google-threat-intelligence", hours_ago)  # polled hourly

    body = client.get("/v1/status").json()

    assert body["status"] == "down"
    states = {s["id"]: s["state"] for s in body["sources"]}
    assert (states["therecord"], states["google-threat-intelligence"]) == ("stale", "stale")


def test_status_is_short_lived_in_caches(client):
    response = client.get("/v1/status")

    assert response.headers["cache-control"] == "public, max-age=15"
