"""Pipeline seam for every news and research source, using each source's real captured sample.

Expected titles and times were read by hand from the raw fixture files (see
fixtures/real/README.md); times are the feed's pubDate converted to UTC.
"""

from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import ingest
from compromised.sources import by_id
from tests.samples import real_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)

CASES = {
    "therecord": (
        "therecord.xml",
        "The Record",
        datetime(2026, 11, 26, 0, 0, 0, tzinfo=UTC),
        [
            "UK’s long-awaited National Cyber Action Plan delayed until December",
            "Microsoft: China’s Salt Typhoon hackers are using Artex",
            "FIFA says hackers accessed ‘limited set of personal and business information’",
        ],
    ),
    "bleepingcomputer": (
        "bleepingcomputer.xml",
        "BleepingComputer",
        datetime(2026, 11, 26, 11, 50, 17, tzinfo=UTC),
        [
            "SYS010 malware abuses browser management to spy on Gmail, Outlook",
            "Palo Alto Networks warns of Fragnesia flaw exploited in PAN-OS attacks",
            "1Password customer data stolen after employee GitHub account breach",
        ],
    ),
    "securityweek": (
        "securityweek.xml",
        "SecurityWeek",
        datetime(2026, 11, 26, 13, 4, 6, tzinfo=UTC),
        [
            "Critical Juniper Session Smart Conductor Flaw Exploited in Attacks",
            "Mitel MiCollab Zero-Days Exploited in Suspected AI-Assisted Attacks",
            "Drupal Installer Patch Left a Gap Attackers Are Already Exploiting",
        ],
    ),
    "thehackernews": (
        "thehackernews.xml",
        "The Hacker News",
        datetime(2026, 11, 26, 10, 57, 55, tzinfo=UTC),  # 16:27:55 +0530
        [
            "Most Wanted: The Phishing Kits and Techniques Getting Past Security Controls",
            "1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach",
            (
                "Drupal Warns of New Highly Critical Site Takeover Vulnerability Under Active"
                " Exploitation"
            ),
        ],
    ),
    "darkreading": (
        "darkreading.xml",
        "Dark Reading",
        datetime(2026, 11, 26, 8, 0, 0, tzinfo=UTC),
        [
            "Cyprus Becomes Espionage Target for Iranian Hackers",
            "Attackers Target .NET Developers With Poisoned Job Assessments",
            "It's a Bot World. We're Just Living in It",
        ],
    ),
    "securityaffairs": (
        "securityaffairs.xml",
        "Security Affairs",
        datetime(2026, 11, 26, 11, 51, 11, tzinfo=UTC),
        [
            "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details",
            "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched",
            (
                "U.S. CISA adds HPE, Danfoss, Mitel MiCollab, and Vates Xen Orchestra flaws to its"
                " Known Exploited Vulnerabilities catalog"
            ),
        ],
    ),
    "krebsonsecurity": (
        "krebsonsecurity.xml",
        "Krebs on Security",
        datetime(2026, 11, 21, 0, 36, 39, tzinfo=UTC),
        [
            "CTO of ‘RansomwareHelp’ Indicted for Wire Fraud",
            "Attackers Used Optimizely to A/B Test Malware on Top Websites",
            "Who Runs the Ransomware Group Qilin?",
        ],
    ),
    "ciscotalos": (
        "cisco-talos.xml",
        "Cisco Talos",
        datetime(2026, 11, 25, 19, 0, 0, tzinfo=UTC),
        [
            "Oh, is it Thanksgiving? I hadn’t noticed!",
            # The next two share a publication time; ties list the later-stored event first.
            "Securing Grandma's groceries with Pierre Cadieux",
            "The Great Escape: Tradecraft insights from an agentic swarm",
        ],
    ),
    "unit42": (
        "unit42.xml",
        "Unit 42",
        datetime(2026, 11, 25, 15, 0, 9, tzinfo=UTC),
        [
            "The AI Threat Horizon: Why Speed, Edge AI and Baselines Are Our Best Defense",
            "NGINX HTTP/2 Use-After-Free: CVE-2026-123633",
            "Recent Trends and Tactics of Agentic AI Attacks",
        ],
    ),
    "googlethreatintel": (
        "google-threat-intelligence.xml",
        "Google Threat Intelligence",
        datetime(2026, 11, 19, 14, 0, 0, tzinfo=UTC),
        [
            "ARMORY CASTLE Exploits vSphere",
            "COLD RELIC: A Case Study in Impersonation and Compromise",
            "GTIG AI Threat Tracker: Agentic Threat Activity Crosses a Significant Threshold",
        ],
    ),
}


@pytest.mark.parametrize("source_id", list(CASES))
def test_real_sample_becomes_one_event_per_item_newest_first(conn, source_id):
    fixture, publisher, newest_published, titles = CASES[source_id]

    result = ingest(conn, by_id(source_id), real_sample(fixture), fetched_at=FETCHED_AT)

    events = storage.list_events(conn, limit=10).events
    assert result.new_events == 3
    assert [e.title for e in events] == titles
    assert events[0].published_at == newest_published
    assert {s.publisher for e in events for s in e.sources} == {publisher}


@pytest.mark.parametrize("source_id", list(CASES))
def test_real_sample_is_stored_as_short_plain_text(conn, source_id):
    fixture = CASES[source_id][0]
    ingest(conn, by_id(source_id), real_sample(fixture), fetched_at=FETCHED_AT)

    stored = conn.execute("select headline, excerpt, metadata::text from source_records").fetchall()
    assert len(stored) == 3
    for headline, excerpt, metadata in stored:
        assert excerpt and len(excerpt) <= 300
        for value in (headline, excerpt, metadata):
            for markup in ("<", ">", "&lt;", "&gt;", "&quot;", "&amp;", "&#"):
                assert markup not in value, (source_id, value)


def test_a_tag_cut_off_mid_way_through_the_body_is_dropped_not_kept_as_text(conn):
    # The capture cut Google's escaped-HTML body inside an <a href=...> tag.
    ingest(
        conn,
        by_id("googlethreatintel"),
        real_sample("google-threat-intelligence.xml"),
        fetched_at=FETCHED_AT,
    )

    excerpt = storage.list_events(conn, limit=1).events[0].sources[0].excerpt
    assert excerpt.startswith("Written by: Jayson Frost, Bryce Greathouse")
    assert excerpt.endswith("Google Threat Intelligence Group (GTIG)")
