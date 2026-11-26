"""HTTP API seam for event pages (#11): one event by its stable id."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import deduplicator, ingest
from tests.samples import real_sample, sample_source

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
ONEPASSWORD = "1Password customer data stolen after employee GitHub account breach"
FIFA = "FIFA says hackers accessed ‘limited set of personal and business information’"
CISA_KEV_BATCH = "CISA Adds 10 Known Exploited Vulnerabilities to Catalog"


def ingest_real(conn, *source_ids):
    for source_id in source_ids:
        ingest(
            conn, sample_source(source_id), real_sample(f"{source_id}.xml"), fetched_at=FETCHED_AT
        )


@pytest.fixture
def api(database_url):
    with TestClient(create_app(database_url=database_url)) as test_client:
        yield test_client


def event_id(api, title):
    events = api.get("/v1/events", params={"limit": 100}).json()["events"]
    return next(e["id"] for e in events if e["title"] == title)


def test_an_event_is_served_by_its_id_with_every_source_in_publication_order(conn, api):
    ingest_real(conn, "bleepingcomputer", "securityaffairs", "thehackernews")

    response = api.get(f"/v1/events/{event_id(api, ONEPASSWORD)}")

    assert response.status_code == 200
    event = response.json()
    assert event["title"] == ONEPASSWORD
    assert event["affected_organization"] == "1Password"
    assert event["trust"]["label"] == "Reported by 3 news outlets"
    assert [(s["publisher"], s["published_at"]) for s in event["sources"]] == [
        ("BleepingComputer", "2026-11-25T21:33:33Z"),
        ("Security Affairs", "2026-11-26T09:42:47Z"),
        ("The Hacker News", "2026-11-26T10:57:25Z"),
    ]


def test_an_event_keeps_its_id_as_more_sources_report_it(conn, api):
    ingest_real(conn, "bleepingcomputer")
    first = event_id(api, ONEPASSWORD)

    ingest_real(conn, "securityaffairs", "thehackernews")

    assert event_id(api, ONEPASSWORD) == first
    assert api.get(f"/v1/events/{first}").json()["source_count"] == 3


def test_an_event_lists_the_cve_identifiers_its_sources_name(conn, api):
    ingest_real(conn, "securityaffairs", "cisa-advisories")
    # CISA's batch is about enterprise products, so it is in no feed tab; its page still exists.
    [[kev_batch]] = conn.execute("select id from events where title = %s", (CISA_KEV_BATCH,))

    event = api.get(f"/v1/events/{kev_batch}").json()

    assert event["cves"] == ["CVE-2023-25914"]
    assert [s["publisher"] for s in event["sources"]] == ["CISA", "Security Affairs"]


def test_an_unknown_event_is_not_found(conn, api):
    assert api.get("/v1/events/999999").status_code == 404
    assert api.get("/v1/events/not-a-number").status_code == 422


def test_an_event_emptied_by_regrouping_redirects_to_where_its_record_went(conn, api):
    ingest_real(conn, "bleepingcomputer", "therecord")
    onepassword, fifa = event_id(api, ONEPASSWORD), event_id(api, FIFA)
    [fifa_record] = [s["record_id"] for s in api.get(f"/v1/events/{fifa}").json()["sources"]]

    # Split off into an event of its own, then joined to 1Password: FIFA's original event and the
    # intermediate one are both deleted, and both old addresses lead to where the record is now.
    split = deduplicator.move_record(conn, fifa_record)
    deduplicator.move_record(conn, fifa_record, onepassword)

    for old in (fifa, split):
        response = api.get(f"/v1/events/{old}", follow_redirects=False)
        assert response.status_code == 308
        assert response.headers["location"] == f"/v1/events/{onepassword}"
    assert api.get(f"/v1/events/{fifa}").json()["id"] == onepassword
