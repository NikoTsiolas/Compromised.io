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
