"""HTTP API seam for the homepage widgets' figures (#15). Expected values were counted by hand
from the fixtures (see tests/pipeline/test_widget_data.py for the reasoning behind each)."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import ingest
from compromised.sources import by_id
from tests.samples import real_sample, synthetic_sample

CATALOG_FETCH = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
FEED_FETCH = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def client_at(database_url, now: datetime) -> TestClient:
    return TestClient(create_app(database_url=database_url, clock=lambda: now))


@pytest.fixture
def kev(conn):
    ingest(conn, by_id("cisa-kev"), synthetic_sample("kev-history.json"), fetched_at=CATALOG_FETCH)


def test_exploited_by_month_before_any_catalog_is_empty(conn, database_url):
    with client_at(database_url, CATALOG_FETCH) as client:
        response = client.get("/v1/widgets/exploited-by-month")

    assert response.status_code == 200
    assert response.json()["months"] == []
    assert response.json()["catalog"] is None


def test_exploited_by_month_gives_twelve_months_with_the_spike_and_its_notable_entries(
    kev, database_url
):
    with client_at(database_url, CATALOG_FETCH) as client:
        response = client.get("/v1/widgets/exploited-by-month")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=300"
    body = response.json()
    assert [(m["month"], m["count"], m["spike"]) for m in body["months"]] == [
        ("2025-07", 0, False),
        ("2025-08", 0, False),
        ("2025-09", 0, False),
        ("2025-10", 0, False),
        ("2025-11", 0, False),
        ("2025-12", 0, False),
        ("2026-01", 2, False),
        ("2026-02", 1, False),
        ("2026-03", 6, True),
        ("2026-04", 2, False),
        ("2026-05", 0, False),
        ("2026-06", 1, False),
    ]
    march = body["months"][8]
    assert march["notable"][0] == {
        "cve": "CVE-0000-0306",
        "title": "[Synthetic test entry] Microsoft Windows Use-After-Free Vulnerability",
        "organization": "Windows",
        "people_use": True,
        "ransomware": True,
    }
    assert [n["cve"] for n in march["notable"]] == [
        "CVE-0000-0306",
        "CVE-0000-0305",
        "CVE-0000-0303",
    ]
    assert body["spike_rule"].startswith("A month is a spike when its count is at least one")
    assert body["catalog"] == {
        "version": "0000.06.03",
        "declared_count": 13,
        "entries": 13,
        "fetched_at": "2026-06-15T12:00:00Z",
    }


def test_exploited_by_month_takes_a_number_of_months_within_bounds(kev, database_url):
    with client_at(database_url, CATALOG_FETCH) as client:
        longer = client.get("/v1/widgets/exploited-by-month", params={"months": 20})
        too_many = client.get("/v1/widgets/exploited-by-month", params={"months": 61})
        too_few = client.get("/v1/widgets/exploited-by-month", params={"months": 0})

    assert [m["month"] for m in longer.json()["months"]][:1] == ["2024-11"]
    assert sum(m["count"] for m in longer.json()["months"]) == 13
    assert too_many.status_code == 422
    assert too_few.status_code == 422


def test_recently_exploited_lists_flaws_in_products_people_use_newest_first(kev, database_url):
    with client_at(database_url, CATALOG_FETCH) as client:
        response = client.get("/v1/widgets/recently-exploited")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=300"
    assert response.json()["items"] == [
        {
            "cve": "CVE-0000-0601",
            "product": "Firefox",
            "logo_key": "firefox",
            "added_on": "2026-06-03",
        },
        {
            "cve": "CVE-0000-0306",
            "product": "Windows",
            "logo_key": "windows",
            "added_on": "2026-03-24",
        },
        {"cve": "CVE-0000-0303", "product": "iOS", "logo_key": "ios", "added_on": "2026-03-12"},
        {
            "cve": "CVE-0000-0302",
            "product": "Chrome",
            "logo_key": "chrome",
            "added_on": "2026-03-05",
        },
    ]


def test_recently_exploited_is_empty_before_any_catalog(conn, database_url):
    with client_at(database_url, CATALOG_FETCH) as client:
        assert client.get("/v1/widgets/recently-exploited").json() == {"items": []}


def test_most_reported_counts_reported_events_and_leaves_out_attacker_claims(conn, database_url):
    for source_id in ("bleepingcomputer", "securityaffairs", "ransomware-live"):
        ingest(conn, by_id(source_id), real_sample(f"{source_id}.xml"), fetched_at=FEED_FETCH)
    ingest(
        conn,
        by_id("bleepingcomputer"),
        synthetic_sample("most-reported.xml"),
        fetched_at=FEED_FETCH,
    )

    with client_at(database_url, datetime(2026, 11, 27, 12, 0, tzinfo=UTC)) as client:
        response = client.get("/v1/widgets/most-reported")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=60"
    body = response.json()
    assert body["window_days"] == 30
    # The three Ransomware.live claims in the real sample were reported by no one else.
    assert [(o["name"], o["count"]) for o in body["items"]] == [
        ("Contoso Pharmacy", 2),
        ("Flight Centre", 1),
        ("1Password", 1),
    ]
    assert body["items"][2] == {
        "name": "1Password",
        "key": "1password",
        "logo_key": "1password",
        "count": 1,
    }


def test_most_reported_is_empty_with_no_events(conn, database_url):
    with client_at(database_url, FEED_FETCH) as client:
        assert client.get("/v1/widgets/most-reported").json() == {"window_days": 30, "items": []}
