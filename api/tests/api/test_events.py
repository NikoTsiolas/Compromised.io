"""HTTP API seam: FastAPI test client against the test database."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import ingest
from tests.samples import real_sample, sample_source, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
FLIGHT_CENTRE = (
    "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details"
)
ONEPASSWORD_SA = "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched"
ONEPASSWORD_BC = "1Password customer data stolen after employee GitHub account breach"
FIFA = "FIFA says hackers accessed ‘limited set of personal and business information’"
DOTNET = "Attackers Target .NET Developers With Poisoned Job Assessments"
WINDOWS_ZERO_DAY = "[Synthetic test item] Windows zero-day exploited in attacks"
CHROME_CRITICAL = "[Synthetic test item] Critical Chrome flaw fixed in security update"


@pytest.fixture
def client(conn, database_url):
    for source_id in ("bleepingcomputer", "therecord", "securityaffairs", "darkreading"):
        body = real_sample(f"{source_id}.xml")
        ingest(conn, sample_source(source_id), body, fetched_at=FETCHED_AT)
    ingest(
        conn,
        sample_source("ransomware-live"),
        real_sample("ransomware-live.xml"),
        fetched_at=FETCHED_AT,
    )
    ingest(
        conn,
        sample_source("securityweek"),
        synthetic_sample("vulnerability-gate.xml"),
        fetched_at=FETCHED_AT,
    )
    with TestClient(create_app(database_url=database_url)) as test_client:
        yield test_client


def titles(response):
    assert response.status_code == 200, response.text
    return [e["title"] for e in response.json()["events"]]


def test_the_default_listing_is_the_all_tab_newest_first_and_the_cursor_keeps_the_tab(client):
    first = client.get("/v1/events", params={"limit": 2})
    # The 1Password event takes the time and headline of its earliest source.
    assert titles(first) == [FLIGHT_CENTRE, ONEPASSWORD_BC]

    second = client.get("/v1/events", params={"limit": 2, "cursor": first.json()["next_cursor"]})
    assert titles(second) == [FIFA, DOTNET]

    third = client.get("/v1/events", params={"limit": 2, "cursor": second.json()["next_cursor"]})
    # The synthetic items are dated 2 November, older than every real one.
    assert titles(third) == [WINDOWS_ZERO_DAY, CHROME_CRITICAL]
    assert titles(client.get("/v1/events", params={"tab": "all"})) == [
        FLIGHT_CENTRE,
        ONEPASSWORD_BC,
        FIFA,
        DOTNET,
        WINDOWS_ZERO_DAY,
        CHROME_CRITICAL,
    ]


def test_each_tab_filters_the_feed(client):
    def tab(name):
        return titles(client.get("/v1/events", params={"tab": name}))

    assert tab("breaches") == [FLIGHT_CENTRE, ONEPASSWORD_BC, FIFA]
    assert tab("ransomware") == [
        "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim",
        "Orova claims Technology Investment Joint Stock CompanyTACORP as a ransomware victim",
        "Orova claims E Xing Precision Design as a ransomware victim",
    ]
    assert tab("under-attack") == [WINDOWS_ZERO_DAY]
    assert tab("update-now") == [WINDOWS_ZERO_DAY, CHROME_CRITICAL]
    assert tab("research") == [
        "SYS010 malware abuses browser management to spy on Gmail, Outlook",
        "Cyprus Becomes Espionage Target for Iranian Hackers",
        "Microsoft: China’s Salt Typhoon hackers are using Artex",
    ]
    # Ranked by its own ticket (#10); empty until then.
    assert tab("trending") == []


def test_commentary_appears_in_no_tab(client):
    commentary = {
        "UK’s long-awaited National Cyber Action Plan delayed until December",
        "It's a Bot World. We're Just Living in It",
    }
    for tab in ("all", "breaches", "ransomware", "under-attack", "update-now", "research"):
        assert not commentary & set(titles(client.get("/v1/events", params={"tab": tab})))


def test_events_carry_category_commentary_flag_organization_and_logo_key(client):
    [event] = [
        e
        for e in client.get("/v1/events", params={"tab": "breaches"}).json()["events"]
        if e["title"] == ONEPASSWORD_BC
    ]
    assert {
        k: event[k]
        for k in event
        if k not in {"id", "sources", "source_count", "published_at", "trust"}
    } == {
        "title": ONEPASSWORD_BC,
        "first_seen_at": "2026-11-26T14:54:07Z",
        "category": "data_breach",
        "category_label": "Data breach",
        "commentary": False,
        "affected_organization": "1Password",
        "organization_key": "1password",
        "logo_key": "1password",
        "tabs": ["all", "breaches"],
        # Ingested without an enricher (rules only, #8).
        "summary": None,
        "action_line": None,
        "enrichment": "rules",
    }

    claim = client.get("/v1/events", params={"tab": "ransomware", "limit": 1}).json()["events"][0]
    assert (claim["affected_organization"], claim["organization_key"], claim["logo_key"]) == (
        "Exceptional Healthcare Inc.",
        None,
        None,
    )


def test_an_event_lists_every_source_earliest_first_with_its_count(client):
    [event] = [e for e in client.get("/v1/events").json()["events"] if e["title"] == ONEPASSWORD_BC]

    assert event["source_count"] == 2
    assert [
        {k: s[k] for k in ("publisher", "url", "headline", "published_at")}
        for s in event["sources"]
    ] == [
        {
            "publisher": "BleepingComputer",
            "url": (
                "https://www.bleepingcomputer.com/news/security/"
                "1password-customer-data-stolen-after-employee-github-account-breach/"
            ),
            "headline": ONEPASSWORD_BC,
            "published_at": "2026-11-25T21:33:33Z",
        },
        {
            "publisher": "Security Affairs",
            "url": (
                "https://securityaffairs.com/204031/cyber-crime/"
                "1password-hacked-customer-names-and-emails-copied-vaults-untouched.html"
            ),
            "headline": ONEPASSWORD_SA,
            "published_at": "2026-11-26T09:42:47Z",
        },
    ]
    assert all(isinstance(s["record_id"], int) for s in event["sources"])


def test_the_tabs_are_listed_in_reading_order_with_their_labels(client):
    response = client.get("/v1/tabs")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "all", "label": "All"},
        {"id": "breaches", "label": "Breaches"},
        {"id": "ransomware", "label": "Ransomware"},
        {"id": "under-attack", "label": "Under attack"},
        {"id": "update-now", "label": "Update now"},
        {"id": "research", "label": "Research"},
        {"id": "trending", "label": "Trending"},
    ]


def test_an_unknown_tab_is_a_client_error(client):
    assert client.get("/v1/events", params={"tab": "everything"}).status_code == 422


def test_a_malformed_cursor_is_a_client_error(client):
    response = client.get("/v1/events", params={"cursor": "not-a-cursor"})
    assert response.status_code == 400


def test_page_size_is_bounded(client):
    assert client.get("/v1/events", params={"limit": 0}).status_code == 422
    assert client.get("/v1/events", params={"limit": 101}).status_code == 422


# --- trust (#7) ---------------------------------------------------------------------------------


def test_every_event_carries_its_label_score_and_source_names_together(client):
    events = client.get("/v1/events", params={"limit": 100, "tab": "all"}).json()["events"]
    events += client.get("/v1/events", params={"tab": "ransomware"}).json()["events"]

    assert "score" not in events[0]  # never a bare top-level score
    for event in events:
        trust = event["trust"]
        assert set(trust) == {"status", "label", "score", "sources"}
        assert trust["label"] and trust["sources"] and 0 <= trust["score"] <= 100


def test_an_events_trust_is_its_status_label_score_and_the_outlets_counted(client):
    by_title = {
        e["title"]: e for e in client.get("/v1/events", params={"limit": 100}).json()["events"]
    }

    assert by_title[ONEPASSWORD_BC]["trust"] == {
        "status": "reported",
        "label": "Reported by 2 news outlets",
        "score": 60,
        "sources": ["BleepingComputer", "Security Affairs"],
    }
    claim = client.get("/v1/events", params={"tab": "ransomware", "limit": 1}).json()["events"][0]
    assert claim["trust"] == {
        "status": "claimed",
        "label": "Claimed by attackers, not confirmed",
        "score": 20,
        "sources": ["Ransomware.live"],
    }


def test_the_scoring_rules_state_the_formulas_numbers_and_every_sources_weight(client):
    response = client.get("/v1/scoring")

    assert response.status_code == 200
    rules = response.json()
    # The anchors agreed in docs/wiki/trust-labels-and-score.md.
    assert {k: v for k, v in rules.items() if k != "sources"} == {
        "claim_only": 20,
        "one_outlet": 50,
        "per_extra_outlet": 10,
        "press_cap": 80,
        "official": 90,
        "official_and_press": 100,
        "disputed": 10,
    }
    assert len(rules["sources"]) == 14
    assert {"name": "Ransomware.live", "tier": "attacker_claim", "weight": 20} in rules["sources"]
    assert {"name": "The Record", "tier": "press", "weight": 50} in rules["sources"]
    assert {"name": "CISA", "tier": "official", "weight": 90} in rules["sources"]
