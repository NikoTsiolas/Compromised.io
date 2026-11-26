"""Pipeline seam: malformed and malicious responses are rejected safely and store nothing."""

import time
from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import ParseError, ingest
from compromised.sources import SECURITYWEEK
from tests.samples import real_sample

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def stored_text(conn) -> str:
    rows = conn.execute(
        "select headline || excerpt || original_url || metadata::text from source_records"
    ).fetchall()
    return "".join(r[0] for r in rows)


def test_xml_external_entities_are_not_resolved(conn, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET-MARKER")
    body = (
        real_sample("securityweek.xml")
        .replace(
            b"<rss ",
            b'<!DOCTYPE rss [<!ENTITY xxe SYSTEM "' + secret.as_uri().encode() + b'">]>\n<rss ',
            1,
        )
        .replace(b"<title>Critical Juniper", b"<title>&xxe; Critical Juniper", 1)
    )

    with pytest.raises(ParseError):
        ingest(conn, SECURITYWEEK, body, fetched_at=FETCHED_AT)

    assert "TOP-SECRET-MARKER" not in stored_text(conn)
    assert storage.list_events(conn).events == []


def test_entity_expansion_bombs_are_refused_quickly(conn):
    lol = b'<!ENTITY a0 "lol">' + b"".join(
        b'<!ENTITY a%d "%s">' % (n, b"&a%d;" % (n - 1) * 10) for n in range(1, 10)
    )
    body = (
        real_sample("securityweek.xml")
        .replace(b"<rss ", b"<!DOCTYPE rss [" + lol + b"]>\n<rss ", 1)
        .replace(b"<title>Critical Juniper", b"<title>&a9; Critical Juniper", 1)
    )

    started = time.monotonic()
    with pytest.raises(ParseError):
        ingest(conn, SECURITYWEEK, body, fetched_at=FETCHED_AT)

    assert time.monotonic() - started < 2.0
    assert storage.list_events(conn).events == []


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body><h1>Just a moment...</h1></body></html>",  # a challenge page, not a feed
        b"",
        b"\x00\x01\x02 not xml at all",
        b'{"items": []}',
    ],
    ids=["html-page", "empty", "binary", "json"],
)
def test_a_response_that_is_not_a_feed_is_a_parse_error(conn, body):
    with pytest.raises(ParseError):
        ingest(conn, SECURITYWEEK, body, fetched_at=FETCHED_AT)

    assert storage.list_events(conn).events == []


def test_a_feed_with_no_items_is_not_an_error(conn):
    sample = real_sample("securityweek.xml")
    body = sample[: sample.index(b"<item>")] + b"</channel></rss>"

    result = ingest(conn, SECURITYWEEK, body, fetched_at=FETCHED_AT)

    assert (result.items, result.new_events) == (0, 0)
