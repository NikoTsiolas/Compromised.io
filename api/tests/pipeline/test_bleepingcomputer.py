"""Pipeline seam: given a source and its raw response bytes, which events exist afterwards."""

from datetime import UTC, datetime

from compromised import storage
from compromised.pipeline import ingest
from compromised.sources import BLEEPINGCOMPUTER
from tests.samples import real_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def test_real_bleepingcomputer_sample_becomes_one_event_per_item_newest_first(conn):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)

    events = storage.list_events(conn, limit=10).events

    assert [e.title for e in events] == [
        "SYS010 malware abuses browser management to spy on Gmail, Outlook",
        "Palo Alto Networks warns of Fragnesia flaw exploited in PAN-OS attacks",
        "1Password customer data stolen after employee GitHub account breach",
    ]
    newest = events[0]
    assert newest.published_at == datetime(2026, 11, 26, 11, 50, 17, tzinfo=UTC)
    assert [(s.publisher, s.url) for s in newest.sources] == [
        (
            "BleepingComputer",
            (
                "https://www.bleepingcomputer.com/news/security/"
                "sys010-malware-abuses-browser-management-to-spy-on-gmail-outlook/"
            ),
        )
    ]


def test_ingesting_the_same_response_twice_creates_no_duplicates(conn):
    body = real_sample("bleepingcomputer.xml")
    first = ingest(conn, BLEEPINGCOMPUTER, body, fetched_at=FETCHED_AT)
    second = ingest(conn, BLEEPINGCOMPUTER, body, fetched_at=FETCHED_AT)

    assert (first.new_events, second.new_events) == (3, 0)
    assert len(storage.list_events(conn, limit=10).events) == 3


def test_excerpt_is_the_plain_text_summary_without_the_publishers_tail(conn):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)

    oldest = storage.list_events(conn, limit=10).events[-1]

    assert oldest.sources[0].excerpt == (
        "1Password has disclosed a data breach after a an employee's corporate GitHub account"
        " was hacked and used to deploy malicious code to the company's backend services to"
        " steal customer data."
    )


def test_stored_records_hold_no_feed_html(conn):
    hostile = real_sample("bleepingcomputer.xml").replace(
        b"<![CDATA[A new version",
        b"<![CDATA[<p><b>A</b> <script>alert(1)</script><img src=x onerror=alert(2)>new version",
    )
    ingest(conn, BLEEPINGCOMPUTER, hostile, fetched_at=FETCHED_AT)

    stored = conn.execute(
        "select headline, excerpt, original_url, canonical_url, metadata::text from source_records"
    ).fetchall()
    assert len(stored) == 3
    for row in stored:
        for value in row:
            assert "<" not in value and ">" not in value and "alert" not in value
    newest = storage.list_events(conn, limit=1).events[0]
    assert newest.sources[0].excerpt.startswith("A new version of the SYS01 infostealer")


def test_markup_in_headlines_is_removed_even_when_double_escaped_but_plain_symbols_stay(conn):
    body = real_sample("bleepingcomputer.xml").replace(
        b"<title>SYS010 malware",
        b"<title>&amp;lt;img src=x onerror=alert(1)&amp;gt;&lt;b&gt;Builds &lt; 2.4 &amp; AT&amp;T"
        b"&lt;/b&gt; SYS010 malware",
    )
    ingest(conn, BLEEPINGCOMPUTER, body, fetched_at=FETCHED_AT)

    assert storage.list_events(conn, limit=1).events[0].title == (
        "Builds < 2.4 & AT&T SYS010 malware abuses browser management to spy on Gmail, Outlook"
    )


def test_long_summaries_are_cut_near_300_characters_on_a_word_boundary(conn):
    long_summary = b"Attackers stole records from the vendor. " * 20
    body = real_sample("bleepingcomputer.xml").replace(
        b"<![CDATA[A new version", b"<![CDATA[" + long_summary + b"A new version"
    )
    ingest(conn, BLEEPINGCOMPUTER, body, fetched_at=FETCHED_AT)

    excerpt = storage.list_events(conn, limit=1).events[0].sources[0].excerpt
    assert 250 <= len(excerpt) <= 300
    assert excerpt.endswith("…")
    assert excerpt.startswith("Attackers stole records from the vendor. Attackers stole")
    assert excerpt[:-1].split()[-1] in {"Attackers", "stole", "records", "from", "the", "vendor"}


def test_items_whose_link_is_not_http_or_is_an_onion_address_are_dropped(conn):
    body = (
        real_sample("bleepingcomputer.xml")
        .replace(
            b"<link>https://www.bleepingcomputer.com/news/security/sys010",
            b"<link>http://leaksite4xyz.onion/news/security/sys010",
        )
        .replace(
            b"<link>https://www.bleepingcomputer.com/news/security/palo-alto",
            b"<link>javascript:alert(1)//news/security/palo-alto",
        )
    )
    ingest(conn, BLEEPINGCOMPUTER, body, fetched_at=FETCHED_AT)

    titles = [e.title for e in storage.list_events(conn, limit=10).events]
    assert titles == ["1Password customer data stolen after employee GitHub account breach"]
