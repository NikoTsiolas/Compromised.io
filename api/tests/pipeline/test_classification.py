"""Pipeline seam: categories, the commentary flag, affected organizations and feed scope.

Every input here is a real captured sample (tests/fixtures/real) unless its name says synthetic.
Expected values come from reading each real headline and excerpt by hand.
"""

import json
from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import ingest, scope
from compromised.records import SourceRecord
from compromised.sources import BLEEPINGCOMPUTER
from tests.samples import real_sample, sample_source, synthetic_sample


def kev_record(entry) -> SourceRecord:
    """A CISA KEV entry as its adapter (#4) should hand it over: vendor and product as
    structured metadata, the vulnerability name as headline."""
    return SourceRecord(
        source_id="cisa-kev",
        guid=entry["cveID"],
        canonical_url=f"https://nvd.nist.gov/vuln/detail/{entry['cveID']}",
        original_url=f"https://nvd.nist.gov/vuln/detail/{entry['cveID']}",
        headline=entry["vulnerabilityName"],
        excerpt=entry["shortDescription"],
        published_at=datetime(2026, 11, 25, tzinfo=UTC),
        fetched_at=datetime(2026, 11, 26, tzinfo=UTC),
        metadata={"vendor": entry["vendorProject"], "product": entry["product"]},
    )


def test_structured_vendor_and_product_fields_name_the_affected_product():
    entries = json.loads(real_sample("cisa-kev.json"))["vulnerabilities"]

    facts = [scope.facts_for([kev_record(e)]) for e in entries]

    assert [(f.organization, f.organization_key, f.category, f.exploited) for f in facts] == [
        ("Juniper Networks", "juniper", "active_exploitation", True),
        ("Xen Orchestra", None, "active_exploitation", True),
        ("AK-SM 800A Series", None, "active_exploitation", True),
    ]
    # None of the three is a product on the "people use" list.
    assert [scope.tabs_for(f) for f in facts] == [frozenset()] * 3


FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)

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
    # Attacker claims: the victim comes from the headline template; Ransomware tab only.
    "ransomware-live": {
        "🏴‍☠️ Metaencryptor has just published a new victim : Exceptional Healthcare Inc.": (
            "ransomware",
            False,
            "Exceptional Healthcare Inc.",
            ["ransomware"],
        ),
        "🏴‍☠️ Orova has just published a new victim : Technology Investment Joint Stock"
        " CompanyTACORP": (
            "ransomware",
            False,
            "Technology Investment Joint Stock CompanyTACORP",
            ["ransomware"],
        ),
        "🏴‍☠️ Orova has just published a new victim : E Xing Precision Design": (
            "ransomware",
            False,
            "E Xing Precision Design",
            ["ransomware"],
        ),
    },
    # Products people use, but the feed states neither critical severity nor exploitation.
    "msrc-update-guide": {
        "CVE-2026-112732 Microsoft Office Visio Remote Code Execution Vulnerability": (
            "vulnerability",
            False,
            "Microsoft Office",
            NONE,
        ),
        "CVE-2026-69291 Windows Volume Manager Extension Driver Remote Code Execution"
        " Vulnerability": ("vulnerability", False, "Windows", NONE),
        "CVE-2026-78462 Visual Studio Code Security Feature Bypass Vulnerability": (
            "vulnerability",
            False,
            "Visual Studio Code",
            NONE,
        ),
        "CVE-2026-72965 Windows WebClient Service Elevation of Privilege Vulnerability": (
            "vulnerability",
            False,
            "Windows",
            NONE,
        ),
        "CVE-2026-87697 .NET Remote Code Execution Vulnerability": (
            "vulnerability",
            False,
            ".NET",
            NONE,
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
