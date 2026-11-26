"""HTTP API seam: search by each field type, filters, pagination and hostile input (#10)."""

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
ONEPASSWORD = "1Password customer data stolen after employee GitHub account breach"
FIFA = "FIFA says hackers accessed ‘limited set of personal and business information’"
DOTNET = "Attackers Target .NET Developers With Poisoned Job Assessments"
NGINX = "NGINX HTTP/2 Use-After-Free: CVE-2026-123633"
SALT_TYPHOON = "Microsoft: China’s Salt Typhoon hackers are using Artex"
CYPRUS = "Cyprus Becomes Espionage Target for Iranian Hackers"
WORDPRESS = (
    "WordPress Core Time-of-check Time-of-use (TOCTOU) Race Condition Vulnerability"
    " (CVE-2026-119977) added to CISA's Known Exploited Vulnerabilities catalog"
)
OROVA_TACORP = "Orova claims Technology Investment Joint Stock CompanyTACORP as a ransomware victim"
OROVA_E_XING = "Orova claims E Xing Precision Design as a ransomware victim"
WINDOWS_ZERO_DAY = "[Synthetic test item] Windows zero-day exploited in attacks"
CHROME_CRITICAL = "[Synthetic test item] Critical Chrome flaw fixed in security update"


@pytest.fixture(scope="module")
def client(database_url):
    """Real captures from eight sources plus the synthetic vulnerability-gate items. Read-only
    tests share it, so it is loaded once."""
    import psycopg

    from compromised import storage

    with psycopg.connect(database_url, autocommit=True) as conn:
        storage.reset_for_tests(conn)
        for source_id in (
            "bleepingcomputer",
            "therecord",
            "securityaffairs",
            "darkreading",
            "thehackernews",
            "unit42",
            "ransomware-live",
        ):
            ingest(
                conn,
                sample_source(source_id),
                real_sample(f"{source_id}.xml"),
                fetched_at=FETCHED_AT,
            )
        ingest(
            conn,
            sample_source("cisa-kev"),
            real_sample("cisa-kev-wordpress.json"),
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


def search(client, **params):
    response = client.get("/v1/search", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def titles(client, **params):
    return [e["title"] for e in search(client, **params)["events"]]


def event(client, title):
    [found] = [e for e in search(client, q=title)["events"] if e["title"] == title]
    return found


# --- each field type ----------------------------------------------------------------------------


def test_search_finds_an_organization_by_name(client):
    assert titles(client, q="1Password") == [ONEPASSWORD]
    assert titles(client, q="fifa") == [FIFA]


def test_search_finds_a_technology_by_product_name_and_by_its_vendor(client):
    assert titles(client, q="Chrome") == [CHROME_CRITICAL]
    # The catalog says Chrome is Google's; no source text says "Google".
    assert CHROME_CRITICAL in titles(client, q="Google")
    assert titles(client, q="WordPress") == [WORDPRESS]


def test_search_matches_cve_identifiers_exactly_in_any_case(client):
    assert titles(client, q="CVE-2026-123633") == [NGINX]
    assert titles(client, q="cve-2026-119977") == [WORDPRESS]
    # A prefix of an identifier is a different identifier.
    assert titles(client, q="CVE-2026-12363") == []


def test_search_finds_a_threat_actor_named_in_the_text_or_by_a_claim_source(client):
    assert titles(client, q="Salt Typhoon") == [SALT_TYPHOON]
    # Not in the catalog: named in the excerpt as 'a threat group called "Volant Manticore"'.
    assert titles(client, q="Volant Manticore") == [CYPRUS]
    # Ransomware.live's group field.
    assert titles(client, q="Orova") == [OROVA_TACORP, OROVA_E_XING]


def test_search_finds_an_attack_vector_the_text_describes_in_other_words(client):
    # The sources say the employee's GitHub account "was hacked"; none says "compromised".
    assert titles(client, q="compromised account") == [ONEPASSWORD]
    assert titles(client, q="supply chain") == [DOTNET]


def test_search_finds_any_keyword_in_the_sources_excerpts(client):
    assert titles(client, q="passport") == [FLIGHT_CENTRE]


def test_events_carry_their_cves_threat_actors_and_attack_vector(client):
    nginx = event(client, NGINX)
    assert nginx["cves"] == ["CVE-2026-123633"]
    assert nginx["attack_vector"] == "Memory corruption"
    salt = event(client, SALT_TYPHOON)
    assert salt["threat_actors"] == ["Salt Typhoon"]
    assert salt["cves"] == []
    assert event(client, ONEPASSWORD)["attack_vector"] == "Compromised account"
    assert event(client, OROVA_E_XING)["threat_actors"] == ["Orova"]


# --- filters, combined with search and with each other, paginated -------------------------------

BREACHES = [FLIGHT_CENTRE, ONEPASSWORD, FIFA]


def test_each_filter_narrows_the_results(client):
    assert titles(client, category="data_breach") == BREACHES
    assert titles(client, source="therecord", tab="breaches") == [FIFA]
    assert titles(client, status="claimed") == [
        "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim",
        OROVA_TACORP,
        OROVA_E_XING,
    ]
    # Both dates are inclusive UTC days; the synthetic items are dated 2 November at 11:00-12:00.
    assert titles(client, **{"from": "2026-11-01", "to": "2026-11-02"}) == [
        WINDOWS_ZERO_DAY,
        CHROME_CRITICAL,
    ]
    assert not {WINDOWS_ZERO_DAY, CHROME_CRITICAL} & set(titles(client, **{"from": "2026-11-03"}))


def test_filters_combine_with_each_other_and_with_search(client):
    # Two sources: OR within a field. A category with them: AND across fields.
    assert titles(client, source=["therecord", "thehackernews"], category="data_breach") == [
        ONEPASSWORD,
        FIFA,
    ]
    assert titles(client, q="hackers", category="data_breach") == [FIFA]
    assert titles(client, q="Orova", status="claimed", source="ransomware-live") == [
        OROVA_TACORP,
        OROVA_E_XING,
    ]
    assert titles(client, q="Orova", status="reported") == []
    assert titles(client, q="CVE-2026-119977", status="confirmed", tab="update-now") == [WORDPRESS]
    assert titles(client, q="1Password", **{"to": "2026-11-02"}) == []


def test_results_are_paginated_with_the_cursor_and_the_cursor_keeps_the_filters(client):
    first = search(client, category="data_breach", limit=2)
    assert [e["title"] for e in first["events"]] == BREACHES[:2]
    second = search(client, category="data_breach", limit=2, cursor=first["next_cursor"])
    assert [e["title"] for e in second["events"]] == BREACHES[2:]
    assert second["next_cursor"] is None


def test_the_filter_values_are_listed_with_reader_facing_labels(client):
    response = client.get("/v1/filters")
    assert response.status_code == 200
    options = response.json()
    assert {"id": "data_breach", "label": "Data breach"} in options["categories"]
    assert {"id": "therecord", "label": "The Record"} in options["sources"]
    assert [s["id"] for s in options["statuses"]] == [
        "confirmed",
        "reported",
        "investigating",
        "claimed",
        "disputed",
    ]
    assert "trending" not in [t["id"] for t in options["tabs"]]


@pytest.mark.parametrize(
    "params",
    [
        {"category": "not-a-category"},
        {"source": "bleepingcomputer' or '1'='1"},
        {"status": "hacked"},
        {"tab": "trending"},
        {"from": "yesterday"},
        {"to": "2026-13-01"},
        {"q": "x" * 201},
        {"limit": 0},
    ],
)
def test_values_outside_a_filters_list_are_refused(client, params):
    assert client.get("/v1/search", params=params).status_code == 422


# --- hostile input ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "'; drop table events; --",
        "1Password' OR '1'='1",
        "!(&|:*<-> ''",
        "\\\\ \\' \\\"",
        "% _ %%",
        "CVE-2026-123633'; select pg_sleep(5); --",
        "‮Salt Typhoon‬ 🔥",
        "x" * 200,
        "<script>alert(1)</script>",
    ],
)
def test_hostile_queries_are_searched_as_text(client, query):
    response = client.get("/v1/search", params={"q": query})
    assert response.status_code == 200, response.text
    # Never the whole table: at most the events whose own words match.
    assert len(response.json()["events"]) <= 2
    # And nothing was dropped.
    assert len(titles(client, category="data_breach")) == 3


def test_a_query_with_a_nul_byte_or_control_characters_still_searches(client):
    assert titles(client, q="1Password\x00") == [ONEPASSWORD]
    assert titles(client, q="\tFIFA\r\n") == [FIFA]


def test_a_query_with_only_operators_or_stop_words_finds_nothing(client):
    assert titles(client, q="&|!") == []
    assert titles(client, q="the and of") == []


@pytest.mark.parametrize(
    "cursor",
    ["not-base64!", "eHx5", "JzsgZHJvcCB0YWJsZSBldmVudHM7IC0t", "MjAyNi0xMS0yNnwx"],
)
def test_a_tampered_cursor_is_a_client_error(client, cursor):
    response = client.get("/v1/search", params={"q": "1Password", "cursor": cursor})
    assert response.status_code == 400
