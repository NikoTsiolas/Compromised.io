"""Pipeline seam: categories, the commentary flag, affected organizations and feed scope.

Every input here is a real captured sample (tests/fixtures/real) unless its name says synthetic.
Expected values come from reading each real headline and excerpt by hand.
"""

from datetime import UTC, datetime

import pytest

from compromised import sources, storage
from compromised.pipeline import ingest, scope
from compromised.sources import BLEEPINGCOMPUTER
from tests.samples import real_sample, sample_source, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def test_structured_vendor_and_product_fields_name_the_affected_product(conn):
    ingest(conn, sources.CISA_KEV, real_sample("cisa-kev.json"), fetched_at=FETCHED_AT)

    events = sorted(storage.list_events(conn, limit=100).events, key=lambda e: e.id)

    assert [(e.affected_organization, e.organization_key, e.category) for e in events] == [
        ("Juniper Networks", "juniper", "active_exploitation"),
        ("Xen Orchestra", None, "active_exploitation"),
        ("AK-SM 800A Series", None, "active_exploitation"),
    ]
    # None of the three is a product on the "people use" list.
    assert [e.tabs for e in events] == [()] * 3


NONE: list[str] = []
ALL_AND_BREACHES = ["all", "breaches"]
RESEARCH = ["research"]

# source id -> {real headline: (category, commentary, affected organization, tabs)}
EXPECTED = {
    "therecord": {
        # Policy news: no incident in it.
        "UK’s long-awaited National Cyber Action Plan delayed until December": (
            "espionage",
            True,
            "unknown",
            NONE,
        ),
        # Microsoft is the speaker; the subject is a state-linked group.
        "Microsoft: China’s Salt Typhoon hackers are using Artex": (
            "espionage",
            False,
            "unknown",
            RESEARCH,
        ),
        "FIFA says hackers accessed ‘limited set of personal and business information’": (
            "data_breach",
            False,
            "FIFA",
            ALL_AND_BREACHES,
        ),
    },
    "securityweek": {
        "Critical Juniper Session Smart Conductor Flaw Exploited in Attacks": (
            "active_exploitation",
            False,
            "Juniper Networks",
            NONE,
        ),
        "Mitel MiCollab Zero-Days Exploited in Suspected AI-Assisted Attacks": (
            "zero_day",
            False,
            "Mitel MiCollab",
            NONE,
        ),
        "Drupal Installer Patch Left a Gap Attackers Are Already Exploiting": (
            "active_exploitation",
            False,
            "Drupal",
            NONE,
        ),
    },
    "thehackernews": {
        # A vendor's own marketing post ("At Push Security, we measure...").
        "Most Wanted: The Phishing Kits and Techniques Getting Past Security Controls": (
            "other",
            True,
            "unknown",
            NONE,
        ),
        "1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach": (
            "data_breach",
            False,
            "1Password",
            ALL_AND_BREACHES,
        ),
        "Drupal Warns of New Highly Critical Site Takeover Vulnerability Under Active Exploitation": (
            "active_exploitation",
            False,
            "Drupal",
            NONE,
        ),
    },
    "darkreading": {
        "Cyprus Becomes Espionage Target for Iranian Hackers": (
            "espionage",
            False,
            "unknown",
            RESEARCH,
        ),
        "Attackers Target .NET Developers With Poisoned Job Assessments": (
            "supply_chain",
            False,
            ".NET",
            ["all"],
        ),
        "It's a Bot World. We're Just Living in It": ("other", True, "unknown", NONE),
    },
    "securityaffairs": {
        "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details": (
            "data_breach",
            False,
            "Flight Centre",
            ALL_AND_BREACHES,
        ),
        "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched": (
            "data_breach",
            False,
            "1Password",
            ALL_AND_BREACHES,
        ),
        "U.S. CISA adds HPE, Danfoss, Mitel MiCollab, and Vates Xen Orchestra flaws to its Known"
        " Exploited Vulnerabilities catalog": (
            "active_exploitation",
            False,
            "Hewlett Packard Enterprise",
            NONE,
        ),
    },
    "krebsonsecurity": {
        "CTO of ‘RansomwareHelp’ Indicted for Wire Fraud": ("other", False, "unknown", NONE),
        "Attackers Used Optimizely to A/B Test Malware on Top Websites": (
            "malware",
            False,
            "Optimizely",
            RESEARCH,
        ),
        # Qilin is the gang, not a victim.
        "Who Runs the Ransomware Group Qilin?": ("ransomware", False, "unknown", NONE),
    },
    "cisa-advisories": {
        "CISA Adds 10 Known Exploited Vulnerabilities to Catalog": (
            "active_exploitation",
            False,
            "unknown",
            NONE,
        ),
        "AutomationDirect C-More EA9 Programming Software": (
            "vulnerability",
            False,
            "unknown",
            NONE,
        ),
        "CISA Adds Three Known Exploited Vulnerabilities to Catalog": (
            "active_exploitation",
            False,
            "unknown",
            NONE,
        ),
    },
    "cisco-talos": {
        "Oh, is it Thanksgiving? I hadn’t noticed!": ("research", True, "unknown", NONE),
        "The Great Escape: Tradecraft insights from an agentic swarm": (
            "research",
            False,
            "unknown",
            RESEARCH,
        ),
        "Securing Grandma's groceries with Pierre Cadieux": ("research", True, "unknown", NONE),
    },
    "unit42": {
        "The AI Threat Horizon: Why Speed, Edge AI and Baselines Are Our Best Defense": (
            "research",
            True,
            "unknown",
            NONE,
        ),
        "NGINX HTTP/2 Use-After-Free: CVE-2026-123633": ("research", False, "NGINX", RESEARCH),
        "Recent Trends and Tactics of Agentic AI Attacks": (
            "research",
            False,
            "unknown",
            RESEARCH,
        ),
    },
    "google-threat-intelligence": {
        "ARMORY CASTLE Exploits vSphere": ("research", False, "VMware vSphere", RESEARCH),
        "COLD RELIC: A Case Study in Impersonation and Compromise": (
            "espionage",
            False,
            "unknown",
            RESEARCH,
        ),
        "GTIG AI Threat Tracker: Agentic Threat Activity Crosses a Significant Threshold": (
            "research",
            False,
            "unknown",
            RESEARCH,
        ),
    },
    # Attacker claims: the victim comes from the adapter's structured field; Ransomware tab only.
    # (MSRC entries need Microsoft's rating first: see test_structured_sources.py.)
    "ransomware-live": {
        "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim": (
            "ransomware",
            False,
            "Exceptional Healthcare Inc.",
            ["ransomware"],
        ),
        "Orova claims Technology Investment Joint Stock CompanyTACORP as a ransomware victim": (
            "ransomware",
            False,
            "Technology Investment Joint Stock CompanyTACORP",
            ["ransomware"],
        ),
        "Orova claims E Xing Precision Design as a ransomware victim": (
            "ransomware",
            False,
            "E Xing Precision Design",
            ["ransomware"],
        ),
    },
}


def test_a_flaw_reaches_the_feed_only_in_a_product_people_use_and_only_if_critical_or_exploited(
    conn,
):
    # Synthetic: no real sample holds a critical or exploited flaw in a listed product.
    ingest(
        conn,
        sample_source("securityweek"),
        synthetic_sample("vulnerability-gate.xml"),
        fetched_at=FETCHED_AT,
    )

    events = by_title(conn)

    assert summary(events["[Synthetic test item] Windows zero-day exploited in attacks"]) == (
        "zero_day",
        False,
        "Windows",
        ["all", "under-attack", "update-now"],
    )
    assert summary(
        events["[Synthetic test item] Critical Chrome flaw fixed in security update"]
    ) == ("vulnerability", False, "Chrome", ["all", "update-now"])
    assert summary(events["[Synthetic test item] Windows flaw fixed in security update"]) == (
        "vulnerability",
        False,
        "Windows",
        [],
    )


@pytest.mark.parametrize("source_id", sorted(EXPECTED))
def test_real_samples_are_classified_extracted_and_scoped(conn, source_id):
    source = sample_source(source_id)
    ingest(conn, source, real_sample(f"{source_id}.xml"), fetched_at=FETCHED_AT)

    actual = {title: summary(e) for title, e in by_title(conn).items()}

    assert actual == {
        title: (category, commentary, organization, sorted(tabs))
        for title, (category, commentary, organization, tabs) in EXPECTED[source_id].items()
    }


def summary(event):
    return (event.category, event.commentary, event.affected_organization, sorted(event.tabs))


def by_title(conn):
    return {e.title: e for e in storage.list_events(conn, limit=100).events}


def test_every_bleepingcomputer_event_gets_a_category_a_commentary_flag_and_an_organization(conn):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)

    events = by_title(conn)

    assert summary(
        events["1Password customer data stolen after employee GitHub account breach"]
    ) == (
        "data_breach",
        False,
        "1Password",
        ["all", "breaches"],
    )
    # A flaw in an enterprise firewall: exploited, but not a product on the "people use" list.
    assert summary(
        events["Palo Alto Networks warns of Fragnesia flaw exploited in PAN-OS attacks"]
    ) == ("active_exploitation", False, "Palo Alto Networks", [])
    # Malware analysis belongs under Research only.
    assert summary(events["SYS010 malware abuses browser management to spy on Gmail, Outlook"]) == (
        "malware",
        False,
        "Gmail",
        ["research"],
    )


def test_events_stored_before_classification_existed_are_classified_by_a_refresh(conn):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)
    # What migration 002 leaves on events the walking skeleton stored.
    conn.execute(
        "update events set category = 'other', organization = null, organization_key = null,"
        " logo_key = null, tabs = '{}'"
    )
    assert storage.list_events(conn, tab="all").events == []

    assert scope.refresh_all(conn) == 3

    [event] = storage.list_events(conn, tab="all").events
    assert (event.title, event.organization_key, event.logo_key) == (
        "1Password customer data stolen after employee GitHub account breach",
        "1password",
        "1password",
    )


def test_a_country_is_never_the_affected_organization(conn):
    # Real Security Affairs story, 25 Nov 2026: the headline opens with "Switzerland Confirms"
    # and the publisher tags it "Switzerland". Switzerland reports the attacks; the victims are
    # unnamed Swiss organisations, so the organization is unknown.
    ingest(
        conn,
        sample_source("securityaffairs"),
        real_sample("securityaffairs-switzerland.xml"),
        fetched_at=FETCHED_AT,
    )

    event = by_title(conn)[
        "Switzerland Confirms First AI-Agent Cyberattacks on Local Organisations"
    ]

    assert event.affected_organization == "unknown"
    assert "all" not in event.tabs
