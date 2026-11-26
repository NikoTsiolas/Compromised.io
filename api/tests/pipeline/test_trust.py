"""Pipeline seam: verification status, reader-facing label and 0-100 score (#7).

Rules: docs/wiki/trust-labels-and-score.md. Expected numbers are the wiki's anchors written out
by hand (20, 50, +10 per extra outlet capped at 80, 90, 100, 10), never recomputed from the code.
Real captured samples come from tests/fixtures/real; synthetic inputs say so.
"""

import re
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import deduplicator, enricher, ingest, msrc
from compromised.sources import (
    CISA_ADVISORIES,
    CISA_KEV,
    RANSOMWARE_LIVE,
    REGISTRY,
    SECURITY_AFFAIRS,
    SECURITYWEEK,
)
from tests.pipeline.test_enrichment import FakeModel, valid_reply
from tests.samples import real_sample, sample_source, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
SAMPLE_FILES = {"cisa-kev": "cisa-kev.json"}  # every other sample is <source id>.xml

ONEPASSWORD_BC = "1Password customer data stolen after employee GitHub account breach"


def ingest_real(conn, *source_ids, fetched_at=FETCHED_AT):
    ratings = msrc.parse_ratings(real_sample("msrc-sug.json"))
    for source_id in source_ids:
        ingest(
            conn,
            sample_source(source_id),
            real_sample(SAMPLE_FILES.get(source_id, f"{source_id}.xml")),
            fetched_at=fetched_at,
            ratings=ratings,
        )


def event_with(conn, headline):
    events = storage.list_events(conn, limit=100).events
    [event] = [e for e in events if headline in {s.headline for s in e.sources}]
    return event


def trust(event):
    return (event.status, event.status_label, event.score, list(event.score_sources))


# --- press coverage -----------------------------------------------------------------------------


def test_three_outlets_on_one_breach_are_reported_by_three_and_score_seventy(conn):
    ingest_real(conn, "bleepingcomputer", "securityaffairs", "thehackernews")

    assert trust(event_with(conn, ONEPASSWORD_BC)) == (
        "reported",
        "Reported by 3 news outlets",
        70,
        ["BleepingComputer", "Security Affairs", "The Hacker News"],
    )


def test_one_outlet_alone_is_reported_by_one_and_scores_fifty(conn):
    ingest_real(conn, "securityaffairs")

    assert trust(event_with(conn, FLIGHT_CENTRE)) == (
        "reported",
        "Reported by 1 news outlet",
        50,
        ["Security Affairs"],
    )


# --- official sources: who confirmed what -------------------------------------------------------

FLIGHT_CENTRE = (
    "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details"
)
KEV_JUNIPER = (
    "Hewlett Packard Enterprise (HPE) Juniper Session Smart Conductor and Session Smart Router OS"
    " Command Injection Vulnerability (CVE-2026-103406) added to CISA's Known Exploited"
    " Vulnerabilities catalog"
)
KEV_DANFOSS_PREFIX = "Danfoss AK-SM 800A Series Improper Authentication Vulnerability"
MSRC_VISIO_PREFIX = "Microsoft Update Guide: Microsoft Office Visio Remote Code Execution"
UNIT42_NGINX = "NGINX HTTP/2 Use-After-Free: CVE-2026-123633"
CISA_ADDS_TEN = "CISA Adds 10 Known Exploited Vulnerabilities to Catalog"


def event_starting(conn, prefix):
    events = storage.list_events(conn, limit=100).events
    [event] = [e for e in events if e.title.startswith(prefix)]
    return event


def test_a_government_advisory_confirms_a_flaw_not_a_breach_and_scores_ninety(conn):
    ingest_real(conn, "cisa-kev")

    assert trust(event_starting(conn, KEV_DANFOSS_PREFIX)) == (
        "confirmed",
        "Flaw confirmed by a government agency",
        90,
        ["CISA Known Exploited Vulnerabilities"],
    )


def test_a_vendor_advisory_about_its_own_product_is_confirmed_by_the_company(conn):
    ingest_real(conn, "msrc-update-guide")

    assert trust(event_starting(conn, MSRC_VISIO_PREFIX)) == (
        "confirmed",
        "Flaw confirmed by the company",
        90,
        ["Microsoft Security Response Center"],
    )


def test_a_vendor_research_unit_writing_about_others_is_not_the_company(conn):
    ingest_real(conn, "unit42")

    status, label, score, names = trust(event_with(conn, UNIT42_NGINX))
    assert (status, label, score, names) == (
        "confirmed",
        "Confirmed by security researchers",
        90,
        ["Unit 42"],
    )
    assert "the company" not in label


TALOS_NEWSLETTER = "Oh, is it Thanksgiving? I hadn’t noticed!"
TALOS_PODCAST = "Securing Grandma's groceries with Pierre Cadieux"
TALOS_RESEARCH = "The Great Escape: Tradecraft insights from an agentic swarm"


def test_commentary_is_not_an_incident_and_gets_no_label_or_score(conn):
    # Real Cisco Talos posts: a weekly newsletter and a podcast episode. Neither reports an
    # incident, so neither may read "Confirmed by security researchers" with a score.
    ingest_real(conn, "cisco-talos")

    for headline in (TALOS_NEWSLETTER, TALOS_PODCAST):
        event = event_with(conn, headline)
        assert event.commentary
        assert trust(event) == (None, None, None, [])


def test_a_research_post_from_the_same_feed_keeps_its_label_and_score(conn):
    ingest_real(conn, "cisco-talos")

    assert trust(event_with(conn, TALOS_RESEARCH)) == (
        "confirmed",
        "Confirmed by security researchers",
        90,
        ["Cisco Talos"],
    )


def test_official_confirmation_plus_press_scores_one_hundred(conn):
    ingest_real(conn, "cisa-kev", "securityweek")

    assert trust(event_with(conn, KEV_JUNIPER)) == (
        "confirmed",
        "Flaw confirmed by a government agency",
        100,
        ["CISA Known Exploited Vulnerabilities", "SecurityWeek"],
    )


def test_a_cisa_advisory_joined_by_a_press_story_scores_one_hundred(conn):
    ingest_real(conn, "cisa-advisories", "securityaffairs")

    event = event_with(conn, CISA_ADDS_TEN)
    assert trust(event) == (
        "confirmed",
        "Flaw confirmed by a government agency",
        100,
        ["CISA", "Security Affairs"],
    )


def test_only_a_vendors_own_advisory_is_labelled_confirmed_by_the_company(conn):
    ingest_real(conn, *(s.id for s in REGISTRY))

    events = storage.list_events(conn, limit=100).events
    by_company = [e.title for e in events if "the company" in (e.status_label or "")]
    assert len(by_company) == 1
    assert by_company[0].startswith(MSRC_VISIO_PREFIX)


# --- more outlets, capped; one publisher counts once ------------------------------------------

# Synthetic: an item linking the real BleepingComputer 1Password article, ingested under other
# press sources so that each joins the same event by canonical URL.
SAME_URL = "[Synthetic test item] Reading list: this week's must-read story"


def add_synthetic_outlets(conn, *source_ids):
    for source_id in source_ids:
        ingest(
            conn,
            sample_source(source_id),
            synthetic_sample("same-canonical-url.xml"),
            fetched_at=FETCHED_AT,
        )


@pytest.mark.parametrize(
    ("extra_outlets", "label", "score"),
    [
        ((), "Reported by 3 news outlets", 70),
        (("securityweek",), "Reported by 4 news outlets", 80),
        (("securityweek", "darkreading"), "Reported by 5 news outlets", 80),
        (
            ("securityweek", "darkreading", "therecord", "krebsonsecurity"),
            "Reported by 7 news outlets",
            80,
        ),
    ],
)
def test_each_extra_outlet_adds_ten_up_to_eighty_without_official_confirmation(
    conn, extra_outlets, label, score
):
    ingest_real(conn, "bleepingcomputer", "securityaffairs", "thehackernews")
    add_synthetic_outlets(conn, *extra_outlets)

    status, got_label, got_score, names = trust(event_with(conn, ONEPASSWORD_BC))
    assert (status, got_label, got_score) == ("reported", label, score)
    assert len(names) == 3 + len(extra_outlets)


def test_two_outlets_score_sixty(conn):
    ingest_real(conn, "bleepingcomputer")
    add_synthetic_outlets(conn, "securityweek")

    assert trust(event_with(conn, ONEPASSWORD_BC)) == (
        "reported",
        "Reported by 2 news outlets",
        60,
        ["BleepingComputer", "SecurityWeek"],  # earliest first
    )


def test_two_records_from_one_publisher_count_as_one_outlet(conn):
    ingest_real(conn, "bleepingcomputer")
    onepassword = event_with(conn, ONEPASSWORD_BC)
    other = event_with(conn, "SYS010 malware abuses browser management to spy on Gmail, Outlook")

    # A grouping correction puts a second BleepingComputer record into the event.
    deduplicator.move_record(conn, other.sources[0].record_id, onepassword.id)

    event = event_with(conn, ONEPASSWORD_BC)
    assert len(event.sources) == 2
    assert trust(event) == ("reported", "Reported by 1 news outlet", 50, ["BleepingComputer"])


# --- attacker claims: upgraded only when press or an official source joins ----------------------

CLAIM = "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim"
OTHER_CLAIM = "Orova claims E Xing Precision Design as a ransomware victim"
CLAIMED = ("claimed", "Claimed by attackers, not confirmed", 20, ["Ransomware.live"])


def ingest_claims(conn, **kwargs):
    ingest(
        conn, RANSOMWARE_LIVE, real_sample("ransomware-live.xml"), fetched_at=FETCHED_AT, **kwargs
    )


def press_joins_the_claim(conn, source=SECURITYWEEK):
    # Synthetic: a later item naming the claimed victim, which joins the claim's event.
    return ingest(
        conn,
        source,
        synthetic_sample("press-on-a-ransomware-claim.xml"),
        fetched_at=datetime(2026, 11, 26, 16, 5, tzinfo=UTC),
    )


def test_an_attacker_claim_alone_is_labelled_a_claim_and_scores_twenty(conn):
    ingest_claims(conn)

    events = storage.list_events(conn, limit=100).events
    assert len(events) == 3
    assert all(trust(e) == CLAIMED for e in events)


def test_a_second_claim_in_the_same_event_does_not_upgrade_it(conn):
    ingest_claims(conn)
    claim = event_with(conn, CLAIM)
    other = event_with(conn, OTHER_CLAIM)

    deduplicator.move_record(conn, other.sources[0].record_id, claim.id)

    assert trust(event_with(conn, CLAIM)) == CLAIMED


def test_a_claim_is_upgraded_to_reported_when_a_press_story_joins_its_event(conn):
    ingest_claims(conn)
    assert trust(event_with(conn, CLAIM)) == CLAIMED

    result = press_joins_the_claim(conn)

    assert result.grouped == 1
    assert trust(event_with(conn, CLAIM)) == (
        "reported",
        "Reported by 1 news outlet",
        50,
        ["SecurityWeek"],
    )


def test_a_claim_is_upgraded_to_confirmed_when_an_official_source_joins_its_event(conn):
    ingest_claims(conn)

    press_joins_the_claim(conn, source=CISA_ADVISORIES)

    assert trust(event_with(conn, CLAIM)) == (
        "confirmed",
        "Confirmed by a government agency",
        90,
        ["CISA"],
    )


def test_the_model_cannot_upgrade_a_claim(conn):
    # Synthetic reply: the model calls the claim a confirmed data breach at a named company.
    model = FakeModel(lambda item: valid_reply(category="data_breach"))

    ingest_claims(conn, enricher=enricher.Enricher(model))

    event = event_with(conn, CLAIM)
    assert (event.enrichment, event.category) == ("ai", "data_breach")
    assert trust(event) == CLAIMED


# --- per-source weights -------------------------------------------------------------------------


def test_a_heavier_outlet_alone_scores_its_weight(conn):
    ingest(
        conn,
        replace(SECURITY_AFFAIRS, weight=70),
        real_sample("securityaffairs.xml"),
        fetched_at=FETCHED_AT,
    )

    assert trust(event_with(conn, FLIGHT_CENTRE))[1:3] == ("Reported by 1 news outlet", 70)


def test_a_lighter_extra_outlet_adds_in_proportion_to_its_weight(conn):
    ingest_real(conn, "bleepingcomputer")
    # Half the press default weight: adds 5 instead of 10.
    ingest(
        conn,
        replace(SECURITYWEEK, weight=25),
        synthetic_sample("same-canonical-url.xml"),
        fetched_at=FETCHED_AT,
    )

    assert trust(event_with(conn, ONEPASSWORD_BC))[1:3] == ("Reported by 2 news outlets", 55)


def test_weights_never_lift_press_coverage_past_eighty(conn):
    ingest(
        conn,
        replace(SECURITY_AFFAIRS, weight=95),
        real_sample("securityaffairs.xml"),
        fetched_at=FETCHED_AT,
    )

    assert trust(event_with(conn, FLIGHT_CENTRE))[2] == 80


def test_an_official_sources_weight_sets_its_score_until_press_joins(conn):
    ingest(conn, replace(CISA_KEV, weight=80), real_sample("cisa-kev.json"), fetched_at=FETCHED_AT)
    assert trust(event_with(conn, KEV_JUNIPER))[2] == 80

    ingest_real(conn, "securityweek")
    assert trust(event_with(conn, KEV_JUNIPER))[2] == 100


def test_a_claim_sources_weight_sets_a_claims_score(conn):
    ingest(
        conn,
        replace(RANSOMWARE_LIVE, weight=10),
        real_sample("ransomware-live.xml"),
        fetched_at=FETCHED_AT,
    )

    assert trust(event_with(conn, CLAIM))[2] == 10


# --- "Disputed": only explicit retraction or denial wording in a later source's headline --------


def later_press_item(conn, headline, excerpt="Synthetic excerpt.", source=SECURITYWEEK):
    """Synthetic: one hand-written press item about the claimed victim, published after the
    real claim, tagged with the victim's name so that it joins the claim's event."""
    slug = re.sub(r"[^a-z0-9]+", "-", headline.lower()).strip("-")
    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<!-- SYNTHETIC TEST DATA, built by tests/pipeline/test_trust.py. Not a real incident. -->
<rss version="2.0"><channel><title>Synthetic test feed</title><link>https://example.com/</link>
<description>Synthetic test data</description>
<item>
  <title>[Synthetic test item] {headline}</title>
  <link>https://example.com/synthetic-{slug}</link>
  <guid>https://example.com/synthetic-{slug}</guid>
  <category>Exceptional Healthcare Inc.</category>
  <pubDate>Fri, 27 Nov 2026 09:00:00 +0000</pubDate>
  <description>{excerpt}</description>
</item></channel></rss>"""
    return ingest(
        conn,
        source,
        feed.encode(),
        fetched_at=datetime(2026, 11, 27, 9, 5, tzinfo=UTC),
    )


@pytest.fixture
def claim(conn):
    ingest_claims(conn)
    return conn


@pytest.mark.parametrize(
    "headline",
    [
        "Exceptional Healthcare Inc. denies Metaencryptor ransomware attack claims",
        "Exceptional Healthcare Inc. disputes Metaencryptor ransomware claim",
        "Exceptional Healthcare Inc. says Metaencryptor ransomware claim is false",
        "Report of Metaencryptor ransomware attack on Exceptional Healthcare Inc. retracted",
        "No evidence of a breach at Exceptional Healthcare Inc. after Metaencryptor ransomware claim",
    ],
)
def test_a_later_source_denying_or_retracting_in_its_headline_marks_the_event_disputed(
    claim, headline
):
    result = later_press_item(claim, headline)

    assert result.grouped == 1
    assert trust(event_with(claim, CLAIM)) == (
        "disputed",
        "Disputed",
        10,
        ["Ransomware.live", "SecurityWeek"],
    )


@pytest.mark.parametrize(
    ("headline", "excerpt"),
    [
        # Negated denial.
        ("Exceptional Healthcare Inc. does not deny Metaencryptor ransomware attack", ""),
        # A denial of something other than the incident.
        ("Exceptional Healthcare Inc. confirms ransomware attack, denies paying Metaencryptor", ""),
        # Denial wording only in the excerpt: not explicit enough.
        (
            "Exceptional Healthcare Inc. ransomware attack claimed by Metaencryptor: update",
            "Synthetic excerpt: the company denies the breach.",
        ),
    ],
)
def test_other_wording_never_marks_the_event_disputed(claim, headline, excerpt):
    result = later_press_item(claim, headline, excerpt or "Synthetic excerpt.")

    assert result.grouped == 1
    assert trust(event_with(claim, CLAIM))[0] == "reported"


def test_denial_wording_in_the_events_own_first_record_is_not_a_later_dispute(conn):
    headline = "Exceptional Healthcare Inc. denies Metaencryptor ransomware attack claims"

    later_press_item(conn, headline)

    assert trust(event_with(conn, f"[Synthetic test item] {headline}"))[:3] == (
        "reported",
        "Reported by 1 news outlet",
        50,
    )


def test_no_real_sample_is_disputed(conn):
    ingest_real(conn, *(s.id for s in REGISTRY))

    events = storage.list_events(conn, limit=100).events
    statuses = {e.status for e in events if not e.commentary}
    assert statuses == {"confirmed", "reported", "claimed"}
    # Commentary carries no status at all (not an incident), so it cannot be disputed either.
    assert {e.status for e in events if e.commentary} == {None}
