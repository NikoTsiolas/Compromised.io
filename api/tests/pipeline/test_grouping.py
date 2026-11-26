"""Pipeline seam: several outlets covering one incident become one event with several sources.

Merge and must-not-merge cases come from the real captured samples (fixtures/real/README.md:
every source captured on 2026-11-26 between 14:54:06 and 14:54:07 UTC). Cases no real capture
contains are built from synthetic fixtures and say so.
"""

from datetime import UTC, datetime
from itertools import permutations

import psycopg
import pytest

from compromised import storage
from compromised.pipeline import deduplicator, ingest
from tests.samples import SAMPLE_SOURCES, real_sample, sample_source, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)

# The 1Password breach, as each outlet headlined it (read by hand from the raw fixtures).
ONEPASSWORD_BC = "1Password customer data stolen after employee GitHub account breach"
ONEPASSWORD_SA = "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched"
ONEPASSWORD_THN = "1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach"


def ingest_real(conn, *source_ids, fetched_at=FETCHED_AT):
    for source_id in source_ids:
        ingest(
            conn, sample_source(source_id), real_sample(f"{source_id}.xml"), fetched_at=fetched_at
        )


def events_with(conn, headline):
    """Every stored event that has a source with this headline."""
    events = storage.list_events(conn, limit=100).events
    return [e for e in events if headline in {s.headline for s in e.sources}]


@pytest.mark.parametrize(
    "order", list(permutations(("bleepingcomputer", "securityaffairs", "thehackernews")))
)
def test_the_same_story_from_three_outlets_becomes_one_event_with_three_sources(conn, order):
    ingest_real(conn, *order)

    [event] = events_with(conn, ONEPASSWORD_BC)
    assert sorted(s.publisher for s in event.sources) == [
        "BleepingComputer",
        "Security Affairs",
        "The Hacker News",
    ]
    assert {s.headline for s in event.sources} == {ONEPASSWORD_BC, ONEPASSWORD_SA, ONEPASSWORD_THN}


# Two different Windows flaws MSRC published the same day: same organization, headline
# similarity 0.26 (above the threshold), but each names its own CVE.
WINDOWS_VOLUME_MANAGER = (
    "CVE-2026-69291 Windows Volume Manager Extension Driver Remote Code Execution Vulnerability"
)
WINDOWS_WEBCLIENT = "CVE-2026-72965 Windows WebClient Service Elevation of Privilege Vulnerability"
# A Dark Reading story and an MSRC advisory that both name .NET but are unrelated.
DOTNET_DEVELOPERS = "Attackers Target .NET Developers With Poisoned Job Assessments"
DOTNET_RCE = "CVE-2026-87697 .NET Remote Code Execution Vulnerability"


def test_two_different_incidents_at_the_same_organization_stay_separate_events(conn):
    ingest_real(conn, "msrc-update-guide", "darkreading")

    for headline in (WINDOWS_VOLUME_MANAGER, WINDOWS_WEBCLIENT, DOTNET_DEVELOPERS, DOTNET_RCE):
        [event] = events_with(conn, headline)
        assert [s.headline for s in event.sources] == [headline]
    assert events_with(conn, WINDOWS_VOLUME_MANAGER)[0].affected_organization == "Windows"
    assert events_with(conn, WINDOWS_WEBCLIENT)[0].affected_organization == "Windows"


# CISA's alert and Security Affairs' write-up of the same Known Exploited Vulnerabilities batch,
# 18 hours apart. Their headlines share no organization; both name CVE-2023-25914.
CISA_KEV_BATCH = "CISA Adds 10 Known Exploited Vulnerabilities to Catalog"
SECURITYAFFAIRS_KEV_BATCH = (
    "U.S. CISA adds HPE, Danfoss, Mitel MiCollab, and Vates Xen Orchestra flaws to its Known"
    " Exploited Vulnerabilities catalog"
)


def test_records_sharing_a_cve_within_the_window_become_one_event(conn):
    ingest_real(conn, "cisa-advisories", "securityaffairs")

    [event] = events_with(conn, CISA_KEV_BATCH)
    assert [(s.publisher, s.headline) for s in event.sources] == [
        ("CISA advisories", CISA_KEV_BATCH),
        ("Security Affairs", SECURITYAFFAIRS_KEV_BATCH),
    ]


CVE_OUTSIDE_WINDOW = "[Synthetic test item] New attacks exploit old Danfoss flaw CVE-2023-25914"


def test_a_shared_cve_outside_the_time_window_does_not_merge(conn):
    ingest_real(conn, "cisa-advisories", "securityaffairs")
    # Synthetic: dated 3 December, 7 days 6 hours after the later real record.
    ingest(
        conn,
        sample_source("securityweek"),
        synthetic_sample("cve-outside-window.xml"),
        fetched_at=datetime(2026, 12, 3, 12, 5, tzinfo=UTC),
    )

    [later] = events_with(conn, CVE_OUTSIDE_WINDOW)
    assert [s.headline for s in later.sources] == [CVE_OUTSIDE_WINDOW]
    [batch] = events_with(conn, CISA_KEV_BATCH)
    assert len(batch.sources) == 2


def test_the_event_title_is_the_earliest_sources_original_headline(conn):
    # BleepingComputer published first (25 Nov 21:33 UTC) but is fetched last here.
    ingest_real(conn, "thehackernews", "securityaffairs", "bleepingcomputer")

    [event] = events_with(conn, ONEPASSWORD_BC)
    assert event.title == ONEPASSWORD_BC
    assert event.published_at == datetime(2026, 11, 25, 21, 33, 33, tzinfo=UTC)
    assert [s.publisher for s in event.sources] == [
        "BleepingComputer",
        "Security Affairs",
        "The Hacker News",
    ]


def test_merging_never_alters_a_source_record(conn):
    ingest_real(conn, "bleepingcomputer")
    [alone] = events_with(conn, ONEPASSWORD_BC)
    [before] = alone.sources

    ingest_real(conn, "securityaffairs", "thehackernews")

    [merged] = events_with(conn, ONEPASSWORD_BC)
    assert merged.id == alone.id
    assert before in merged.sources


def test_a_record_can_be_moved_to_another_event_and_back(conn):
    ingest_real(conn, "bleepingcomputer", "securityaffairs", "thehackernews")
    [event] = events_with(conn, ONEPASSWORD_BC)
    bleeping = next(s for s in event.sources if s.headline == ONEPASSWORD_BC)

    # Out to an event of its own: the remaining event takes its next-earliest headline.
    new_event_id = deduplicator.move_record(conn, bleeping.record_id)
    [moved] = events_with(conn, ONEPASSWORD_BC)
    [rest] = events_with(conn, ONEPASSWORD_SA)
    assert moved.id == new_event_id != rest.id
    assert moved.sources == [bleeping]
    assert moved.title == ONEPASSWORD_BC
    assert rest.title == ONEPASSWORD_SA
    assert len(rest.sources) == 2

    # Back into the original event.
    assert deduplicator.move_record(conn, bleeping.record_id, rest.id) == rest.id
    [back] = events_with(conn, ONEPASSWORD_BC)
    assert back.id == rest.id
    assert back.title == ONEPASSWORD_BC
    assert bleeping in back.sources
    # The emptied event is gone; the record itself never was.
    assert all(e.id != new_event_id for e in storage.list_events(conn, limit=100).events)


def test_the_database_refuses_to_edit_or_delete_a_source_record(conn):
    ingest_real(conn, "bleepingcomputer")
    with pytest.raises(psycopg.errors.RaiseException, match="never altered"):
        conn.execute("update source_records set headline = 'changed'")
    with pytest.raises(psycopg.errors.RaiseException, match="never deleted"):
        conn.execute("delete from source_records")


SAME_URL = "[Synthetic test item] Reading list: this week's must-read story"


def test_a_record_with_an_identical_canonical_url_from_another_source_joins_that_event(conn):
    ingest_real(conn, "bleepingcomputer")
    # Synthetic: another source linking the same article, under an unrelated headline.
    result = ingest(
        conn,
        sample_source("securityweek"),
        synthetic_sample("same-canonical-url.xml"),
        fetched_at=FETCHED_AT,
    )

    assert (result.new_events, result.grouped) == (0, 1)
    [event] = events_with(conn, ONEPASSWORD_BC)
    assert [s.headline for s in event.sources] == [ONEPASSWORD_BC, SAME_URL]


def test_one_feeds_own_items_about_the_same_organization_are_not_linked_by_headline(conn):
    # Synthetic: two different Windows flaws from one feed, no CVEs; their shared
    # "[Synthetic test item] Windows ..." wording gives a similarity of 0.39.
    ingest(
        conn,
        sample_source("securityweek"),
        synthetic_sample("vulnerability-gate.xml"),
        fetched_at=FETCHED_AT,
    )

    for headline in (
        "[Synthetic test item] Windows zero-day exploited in attacks",
        "[Synthetic test item] Windows flaw fixed in security update",
    ):
        [event] = events_with(conn, headline)
        assert len(event.sources) == 1


def test_every_real_sample_together_groups_into_exactly_the_stories_several_outlets_covered(
    conn,
):
    ingest_real(conn, "bleepingcomputer", *sorted(SAMPLE_SOURCES))

    events = storage.list_events(conn, limit=100).events
    assert sum(len(e.sources) for e in events) == 41
    assert len(events) == 38
    assert {e.title: len(e.sources) for e in events if len(e.sources) > 1} == {
        ONEPASSWORD_BC: 3,
        CISA_KEV_BATCH: 2,
    }
    # Known miss: SecurityWeek and The Hacker News on one Drupal flaw. Their headlines share
    # little wording (similarity 0.13) and only The Hacker News names the CVE.
    assert (
        len(events_with(conn, "Drupal Installer Patch Left a Gap Attackers Are Already Exploiting"))
        == 1
    )
