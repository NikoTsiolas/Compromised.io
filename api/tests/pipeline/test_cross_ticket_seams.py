"""Pipeline seam: behaviour that needs structured sources (#4), grouping (#5) and enrichment (#8)
together, so none of the three branches could test it alone.

Real captured samples come from tests/fixtures/real; synthetic inputs say so.
"""

from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import enricher, ingest
from compromised.sources import CISA_KEV, RANSOMWARE_LIVE, SECURITYWEEK
from tests.pipeline.test_enrichment import FakeModel, valid_reply
from tests.samples import real_sample, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)

# The real KEV entry and SecurityWeek story that both name CVE-2026-103406.
KEV_JUNIPER = (
    "Hewlett Packard Enterprise (HPE) Juniper Session Smart Conductor and Session Smart Router OS"
    " Command Injection Vulnerability (CVE-2026-103406) added to CISA's Known Exploited"
    " Vulnerabilities catalog"
)
SECURITYWEEK_JUNIPER = "Critical Juniper Session Smart Conductor Flaw Exploited in Attacks"
# The real requiredAction field's first clause (see test_enrichment.KEV_ACTION).
KEV_ACTION = "Apply mitigations in accordance with vendor instructions."


def ingest_kev(conn, **kwargs):
    return ingest(conn, CISA_KEV, real_sample("cisa-kev.json"), fetched_at=FETCHED_AT, **kwargs)


def ingest_securityweek(conn, **kwargs):
    return ingest(
        conn, SECURITYWEEK, real_sample("securityweek.xml"), fetched_at=FETCHED_AT, **kwargs
    )


def events_with(conn, headline):
    events = storage.list_events(conn, limit=100).events
    return [e for e in events if headline in {s.headline for s in e.sources}]


# --- a KEV entry's required action reaches the event ------------------------------------------


def test_the_kev_adapters_required_action_becomes_the_events_action_line(conn):
    ingest_kev(conn)

    events = storage.list_events(conn, limit=100).events
    assert len(events) == 3
    assert {e.action_line for e in events} == {KEV_ACTION}


@pytest.mark.parametrize("kev_first", [True, False])
def test_a_kev_action_line_survives_grouping_with_a_press_story(conn, kev_first):
    steps = [ingest_kev, ingest_securityweek]
    for step in steps if kev_first else reversed(steps):
        step(conn)

    [event] = events_with(conn, KEV_JUNIPER)
    assert SECURITYWEEK_JUNIPER in {s.headline for s in event.sources}
    assert event.action_line == KEV_ACTION


def test_enrichment_neither_rewrites_a_kev_title_nor_replaces_its_stated_action(conn):
    model = FakeModel(
        lambda item: valid_reply(
            category="active_exploitation",
            action_line="Synthetic: do something else.",
            action_quote=item.excerpt[:40],
        )
    )
    ingest_kev(conn, enricher=enricher.Enricher(model))

    [event] = events_with(conn, KEV_JUNIPER)
    assert event.enrichment == "ai"
    assert event.title == KEV_JUNIPER  # the fixed template, never model prose
    assert event.action_line == KEV_ACTION
    # The model saw the template headline and the KEV short description, nothing else.
    assert KEV_JUNIPER in {item.headline for item in model.sent}


# --- structured sources' CVEs reach grouping ----------------------------------------------------


@pytest.mark.parametrize("kev_first", [True, False])
def test_a_kev_entry_and_a_press_story_sharing_a_cve_become_one_event(conn, kev_first):
    steps = [ingest_kev, ingest_securityweek]
    for step in steps if kev_first else reversed(steps):
        step(conn)

    [event] = events_with(conn, KEV_JUNIPER)
    assert sorted(s.publisher for s in event.sources) == [
        "CISA Known Exploited Vulnerabilities",
        "SecurityWeek",
    ]
    # The CVE came from the KEV adapter's single-string metadata["cve"] (and its title).
    cves = conn.execute(
        "select cves from source_records where source_id = 'cisa-kev' and guid = 'CVE-2026-103406'"
    ).fetchone()[0]
    assert cves == ["CVE-2026-103406"]


def test_each_enriched_once_a_grouped_event_is_not_enriched_again(conn):
    model = FakeModel()
    ingest_securityweek(conn, enricher=enricher.Enricher(model))
    sent = len(model.sent)

    ingest_kev(conn, enricher=enricher.Enricher(model))

    # Two KEV entries start events of their own; the Juniper entry joins SecurityWeek's.
    assert len(model.sent) == sent + 2
    assert KEV_JUNIPER not in {item.headline for item in model.sent}


# --- attacker claims never get a model action line, even once grouped ---------------------------

CLAIM = "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim"
PRESS_ON_CLAIM = (
    "[Synthetic test item] Exceptional Healthcare Inc. ransomware attack claimed by Metaencryptor"
)


def test_an_attacker_claim_gets_no_model_action_line_even_after_a_press_story_joins_it(conn):
    # Synthetic reply: the model "quotes" the claim headline, so the quote check passes.
    model = FakeModel(
        lambda item: valid_reply(
            category="ransomware",
            action_line="Synthetic: contact the group.",
            action_quote=item.headline,
        )
    )
    ingest(
        conn,
        RANSOMWARE_LIVE,
        real_sample("ransomware-live.xml"),
        fetched_at=FETCHED_AT,
        enricher=enricher.Enricher(model),
    )
    [claim] = events_with(conn, CLAIM)
    assert (claim.enrichment, claim.action_line) == ("ai", None)

    # Synthetic: a press story on the same victim joins the claim's event.
    result = ingest(
        conn,
        SECURITYWEEK,
        synthetic_sample("press-on-a-ransomware-claim.xml"),
        fetched_at=datetime(2026, 11, 26, 16, 5, tzinfo=UTC),
    )

    assert (result.new_events, result.grouped) == (0, 1)
    [event] = events_with(conn, CLAIM)
    assert [s.headline for s in event.sources] == [CLAIM, PRESS_ON_CLAIM]
    assert event.action_line is None
