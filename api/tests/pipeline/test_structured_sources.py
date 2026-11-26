"""Pipeline seam for the structured sources (#4): CISA KEV, CISA advisories, the MSRC Update
Guide (with severity from the MSRC SUG API) and Ransomware.live.

Every input is a real captured sample (tests/fixtures/real) unless its name says synthetic.
Expected values were read by hand from the raw fixture files.
"""

from datetime import UTC, datetime, timedelta

import psycopg
import pytest

from compromised import storage
from compromised.pipeline import ParseError, ingest, msrc
from compromised.sources import by_id
from tests.samples import real_sample, synthetic_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def events_by_title(conn):
    return {e.title: e for e in storage.list_events(conn, limit=100).events}


def metadata_by_title(conn):
    return {
        e.title: storage.event_records(conn, e.id)[0].metadata
        for e in storage.list_events(conn, limit=100).events
    }


def test_kev_entries_get_a_fixed_title_and_carry_vendor_product_cve_action_and_date(conn):
    ingest(conn, by_id("cisa-kev"), real_sample("cisa-kev.json"), fetched_at=FETCHED_AT)

    metadata = metadata_by_title(conn)

    hpe = (
        "Hewlett Packard Enterprise (HPE) Juniper Session Smart Conductor and Session Smart"
        " Router OS Command Injection Vulnerability (CVE-2026-103406) added to CISA's Known"
        " Exploited Vulnerabilities catalog"
    )
    assert sorted(metadata) == sorted(
        [
            hpe,
            (
                "Vates Xen Orchestra Improper Validation of Specified Type of Input Vulnerability"
                " (CVE-2026-133469) added to CISA's Known Exploited Vulnerabilities catalog"
            ),
            (
                "Danfoss AK-SM 800A Series Improper Authentication Vulnerability (CVE-2025-41450)"
                " added to CISA's Known Exploited Vulnerabilities catalog"
            ),
        ]
    )
    assert metadata[hpe] == {
        "cve": "CVE-2026-103406",
        "vendor": "Hewlett Packard Enterprise (HPE)",
        "product": "Juniper Session Smart Conductor and Session Smart Router",
        "date_added": "2026-11-25",
        "due_date": "2026-11-28",
        "required_action": (
            "Apply mitigations in accordance with vendor instructions, ensuring compliance with"
            " CISA’s BOD 26-04 Prioritizing Security Updates Based on Risk (see URL in Notes)"
            " guidance and CISA’s “Forensics Triage Requirements” (see URL in Notes). Follow"
            " applicable BOD 26-04 guidance for cloud services or discontinue use of the product"
            " if mitigations are unavailable. Stakeholders are responsible for evaluating each"
            " asset's internet exposure and ensuring adherence to BOD 26-04 patching guidelines."
        ),
        "known_ransomware_use": "Unknown",
        "exploited": True,
    }
    [record] = storage.event_records(conn, events_by_title(conn)[hpe].id)
    assert record.published_at == datetime(2026, 11, 25, tzinfo=UTC)
    assert record.original_url == (
        "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
        "?search_api_fulltext=CVE-2026-103406"
    )
    assert record.excerpt.startswith(
        "Hewlett Packard Enterprise (HPE) Juniper Session Smart Conductor and Session Smart"
        " Router contain an OS command injection vulnerability"
    )


def stored_text(conn) -> str:
    """Every stored source record and event, as text, to prove something is nowhere in them."""
    rows = conn.execute(
        "select row_to_json(r)::text from source_records r"
        " union all select row_to_json(e)::text from events e"
    ).fetchall()
    return "\n".join(r[0] for r in rows)


def test_ransomware_live_claims_carry_victim_and_group_are_marked_as_claims_and_keep_no_text(
    conn,
):
    ingest(
        conn, by_id("ransomware-live"), real_sample("ransomware-live.xml"), fetched_at=FETCHED_AT
    )

    events = events_by_title(conn)
    metadata = metadata_by_title(conn)

    healthcare = "Metaencryptor claims Exceptional Healthcare Inc. as a ransomware victim"
    assert sorted(events) == sorted(
        [
            healthcare,
            "Orova claims Technology Investment Joint Stock CompanyTACORP as a ransomware victim",
            "Orova claims E Xing Precision Design as a ransomware victim",
        ]
    )
    assert metadata[healthcare] == {
        "victim": "Exceptional Healthcare Inc.",
        "group": "Metaencryptor",
        "group_key": "metaencryptor",
        "country": "US",
        "attacker_claim": True,
    }
    assert metadata["Orova claims E Xing Precision Design as a ransomware victim"]["group_key"] == (
        "orova"
    )
    event = events[healthcare]
    assert (event.affected_organization, event.tabs, event.category) == (
        "Exceptional Healthcare Inc.",
        ("ransomware",),
        "ransomware",
    )
    [source] = event.sources
    assert source.url == (
        "https://www.ransomware.live/id/RXhjZXB0aW9uYWwgSGVhbHRoY2FyZSBJbmMuQG1ldGFlbmNyeXB0b3I"
    )
    # Descriptions are attacker-supplied text (contacts, URLs): never stored.
    assert {s.excerpt for e in events.values() for s in e.sources} == {""}
    assert "Data size" not in stored_text(conn)
    assert "images.ransomware.live" not in stored_text(conn)


def test_no_leak_site_or_onion_link_from_ransomware_live_is_ever_stored(conn):
    ingest(
        conn,
        by_id("ransomware-live"),
        synthetic_sample("ransomware-live-hostile.xml"),
        fetched_at=FETCHED_AT,
    )

    events = events_by_title(conn)

    # One: its link is an .onion address, so the Ransomware.live group page stands in.
    # Two: neither link nor guid is on Ransomware.live, so nothing of it is kept.
    # Three: an ordinary item.
    assert sorted(events) == [
        "Synthetictestgroup claims Synthetic Victim One as a ransomware victim",
        "Synthetictestgroup claims Synthetic Victim Three as a ransomware victim",
    ]
    assert [s.url for e in events.values() for s in e.sources] == [
        "https://www.ransomware.live/group/synthetictestgroup?11111111111111111111111111111111",
        "https://www.ransomware.live/id/U3ludGhldGljIFZpY3RpbSBUaHJlZUBzeW50aGV0aWN0ZXN0Z3JvdXA",
    ]
    text = stored_text(conn)
    for trace in (".onion", "leaks.example.com", "synthetic-attacker", "Synthetic Victim Two"):
        assert trace not in text


VISIO = (
    "Microsoft Update Guide: Microsoft Office Visio Remote Code Execution Vulnerability"
    " (CVE-2026-112732)"
)
WEBCLIENT = (
    "Microsoft Update Guide: Windows WebClient Service Elevation of Privilege Vulnerability"
    " (CVE-2026-72965)"
)


def ingest_msrc(conn, ratings_body: bytes, fetched_at=FETCHED_AT):
    return ingest(
        conn,
        by_id("msrc-update-guide"),
        real_sample("msrc-update-guide.xml"),
        fetched_at=fetched_at,
        ratings=msrc.parse_ratings(ratings_body),
    )


def test_msrc_entries_are_kept_only_for_listed_products_rated_critical_or_exploited(conn):
    # Real SUG answer for the three entries whose product is on the list (Office, Windows x2):
    # Visio is Critical; both Windows flaws are Important and not exploited. Visual Studio Code
    # and .NET are not on the list, so they are never looked up.
    ingest_msrc(conn, real_sample("msrc-sug.json"))

    events = events_by_title(conn)

    assert list(events) == [VISIO]
    assert metadata_by_title(conn)[VISIO] == {
        "cve": "CVE-2026-112732",
        "vendor": "Microsoft",
        "product": "Microsoft Office Visio",
        "severity": "Critical",
        "exploited": False,
        "revised_at": "2026-11-24T16:00:00+00:00",
    }
    visio = events[VISIO]
    assert (visio.affected_organization, visio.category, visio.tabs) == (
        "Microsoft Office",
        "vulnerability",
        ("all", "update-now"),
    )
    [source] = visio.sources
    assert source.url == "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-112732"
    assert source.published_at == datetime(2026, 11, 24, 16, 0, tzinfo=UTC)  # 08:00 -0800


def test_an_exploited_msrc_entry_is_kept_even_when_not_critical(conn):
    # Synthetic SUG answer: no real response marked a listed product as exploited.
    ingest_msrc(conn, synthetic_sample("msrc-sug-exploited.json"))

    events = events_by_title(conn)

    assert sorted(events) == sorted([VISIO, WEBCLIENT])
    assert (events[WEBCLIENT].affected_organization, events[WEBCLIENT].tabs) == (
        "Windows",
        ("all", "under-attack", "update-now"),
    )


def test_a_stored_msrc_entry_whose_rating_changes_is_rescoped(conn):
    ingest_msrc(conn, real_sample("msrc-sug.json"))
    assert events_by_title(conn)[VISIO].tabs == ("all", "update-now")

    # Synthetic: a later revision reports Visio as exploited.
    ingest_msrc(conn, synthetic_sample("msrc-sug-exploited.json"))

    events = events_by_title(conn)
    assert events[VISIO].tabs == ("all", "under-attack", "update-now")
    assert metadata_by_title(conn)[VISIO]["exploited"] is True
    assert len(events[VISIO].sources) == 1


def stored_row(conn, guid) -> str:
    """The stored source record exactly as the database holds it, every column."""
    return conn.execute(
        "select row_to_json(r)::text from source_records r where guid = %s", (guid,)
    ).fetchone()[0]


def test_a_re_rating_is_appended_and_the_original_record_never_changes(conn):
    ingest_msrc(conn, real_sample("msrc-sug.json"))
    before = stored_row(conn, "CVE-2026-112732")

    # Synthetic: a later fetch reports Visio as exploited.
    later = FETCHED_AT + timedelta(hours=1)
    ingest_msrc(conn, synthetic_sample("msrc-sug-exploited.json"), fetched_at=later)
    # The same rating again appends nothing.
    ingest_msrc(conn, synthetic_sample("msrc-sug-exploited.json"), fetched_at=later)

    assert stored_row(conn, "CVE-2026-112732") == before
    record_id = conn.execute(
        "select id from source_records where guid = 'CVE-2026-112732'"
    ).fetchone()[0]
    original = conn.execute(
        "select metadata from source_records where id = %s", (record_id,)
    ).fetchone()[0]
    revisions = storage.record_revisions(conn, record_id)
    # Both ratings, in order: the original's, then the revision's.
    assert (original["severity"], original["exploited"]) == ("Critical", False)
    assert [(r["fetched_at"], r["metadata"]) for r in revisions] == [(later, {"exploited": True})]
    # The database refuses to change or remove a revision.
    with pytest.raises(psycopg.errors.RaiseException, match="never altered or deleted"):
        conn.execute("update source_record_revisions set metadata = '{}'")
    with pytest.raises(psycopg.errors.RaiseException, match="never altered or deleted"):
        conn.execute("delete from source_record_revisions")


def test_only_msrc_entries_for_listed_products_are_sent_for_rating():
    items = msrc.parse(real_sample("msrc-update-guide.xml"))

    window = datetime(2026, 10, 27, tzinfo=UTC)
    assert msrc.cves_to_rate(items, since=window, released_after=window) == [
        "CVE-2026-112732",
        "CVE-2026-69291",
        "CVE-2026-72965",
    ]
    # Entries last revised before ``since`` were rated when they first appeared.
    since = datetime(2026, 11, 24, tzinfo=UTC)
    assert msrc.cves_to_rate(items, since=since, released_after=window) == ["CVE-2026-112732"]


def test_ratings_are_read_from_a_real_single_cve_sug_answer():
    assert msrc.parse_ratings(real_sample("msrc-sug-CVE-2026-70197.json")) == {
        "CVE-2026-70197": msrc.Rating(severity="Important", exploited=False, product=".NET")
    }


def test_cisa_advisories_keep_their_own_headlines(conn):
    ingest(
        conn, by_id("cisa-advisories"), real_sample("cisa-advisories.xml"), fetched_at=FETCHED_AT
    )

    events = events_by_title(conn)

    assert sorted(events) == [
        "AutomationDirect C-More EA9 Programming Software",
        "CISA Adds 10 Known Exploited Vulnerabilities to Catalog",
        "CISA Adds Three Known Exploited Vulnerabilities to Catalog",
    ]
    assert {s.publisher for e in events.values() for s in e.sources} == {"CISA"}
    # A two-digit year in pubDate ("Wed, 25 Nov 26 12:00:00 +0000").
    assert events["CISA Adds 10 Known Exploited Vulnerabilities to Catalog"].published_at == (
        datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    )


def ingest_all_structured(conn, fetched_at):
    for source_id, sample in (
        ("cisa-kev", "cisa-kev.json"),
        ("cisa-advisories", "cisa-advisories.xml"),
        ("ransomware-live", "ransomware-live.xml"),
    ):
        ingest(conn, by_id(source_id), real_sample(sample), fetched_at=fetched_at)
    ingest_msrc(conn, real_sample("msrc-sug.json"), fetched_at=fetched_at)


def events_per_source(conn) -> dict[str, int]:
    rows = conn.execute("select source_id, count(*) from source_records group by 1").fetchall()
    return dict(rows)


@pytest.mark.parametrize(
    ("fetched_at", "expected"),
    [
        # The capture itself: everything is recent.
        (
            FETCHED_AT,
            {"cisa-kev": 3, "cisa-advisories": 3, "ransomware-live": 3, "msrc-update-guide": 1},
        ),
        # 30 days later, 12:00:01: the two advisories of 24 Nov 12:00 are just too old; the
        # Visio entry (24 Nov 16:00) and KEV entries (added 25 Nov) are just young enough.
        (
            datetime(2026, 12, 24, 12, 0, 1, tzinfo=UTC),
            {"cisa-kev": 3, "cisa-advisories": 1, "ransomware-live": 3, "msrc-update-guide": 1},
        ),
        # A day later, only the Ransomware.live claims of 26 Nov are within 30 days.
        (datetime(2026, 12, 25, 13, 0, tzinfo=UTC), {"ransomware-live": 3}),
    ],
)
def test_a_first_run_imports_no_structured_entry_older_than_30_days(conn, fetched_at, expected):
    ingest_all_structured(conn, fetched_at)

    assert events_per_source(conn) == expected


@pytest.mark.parametrize(
    ("source_id", "body"),
    [
        # Synthetic malformed answers.
        ("cisa-kev", b"<html>Access denied</html>"),
        ("cisa-kev", b'{"vulnerabilities": "none"}'),
        ("ransomware-live", b"<html><body>Just a moment...</body></html>"),
        ("msrc-update-guide", b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x "y">]><rss/>'),
    ],
)
def test_a_malformed_structured_response_is_refused_and_stores_nothing(conn, source_id, body):
    with pytest.raises(ParseError):
        ingest(conn, by_id(source_id), body, fetched_at=FETCHED_AT)

    assert storage.list_events(conn).events == []


def test_a_malformed_sug_answer_is_refused():
    with pytest.raises(ParseError):
        msrc.parse_ratings(b"<html>Service unavailable</html>")


def test_an_msrc_cve_first_published_over_30_days_ago_is_not_imported_however_recently_revised(
    conn,
):
    # Synthetic: two Windows CVEs, both revised on 23 Nov and both rated Critical. One was first
    # published on 13 Oct (44 days before the fetch), the other on 10 Nov.
    body = synthetic_sample("msrc-revisions.xml")
    items = msrc.parse(body)
    since = FETCHED_AT - timedelta(days=30)
    assert msrc.cves_to_rate(items, since=since, released_after=since) == ["CVE-2026-90002"]

    ingest(
        conn,
        by_id("msrc-update-guide"),
        body,
        fetched_at=FETCHED_AT,
        ratings=msrc.parse_ratings(synthetic_sample("msrc-sug-revisions.json")),
    )

    [event] = storage.list_events(conn).events
    assert event.title == (
        "Microsoft Update Guide: Windows Synthetic Test Service Elevation of Privilege"
        " Vulnerability (CVE-2026-90002)"
    )
    # Dated by its first publication; the newest revision is kept as metadata.
    assert event.published_at == datetime(2026, 11, 10, 16, 0, tzinfo=UTC)
    assert metadata_by_title(conn)[event.title]["revised_at"] == "2026-11-23T16:00:00+00:00"
