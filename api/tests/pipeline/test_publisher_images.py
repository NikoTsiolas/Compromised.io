"""Pipeline seam: the image a publisher puts in its own feed, kept as one https URL per record.

Expected URLs were read by hand from the raw fixture files. Only the URL is stored: the image is
never downloaded, and no article page is fetched to look for one.
"""

from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import ingest
from compromised.sources import BLEEPINGCOMPUTER, by_id
from tests.samples import real_sample, sample_source

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)


def _image_of(conn, headline: str) -> str | None:
    for event in storage.list_events(conn, limit=50).events:
        for source in event.sources:
            if source.headline == headline:
                return source.image_url
    raise AssertionError(f"no source record headed {headline!r}")


@pytest.mark.parametrize(
    ("source_id", "headline", "image_url"),
    [
        (
            # media:content (and an identical media:thumbnail)
            "darkreading",
            "Cyprus Becomes Espionage Target for Iranian Hackers",
            (
                "https://eu-images.contentstack.com/v3/assets/blt6d90778a997de1cd/"
                "blt08316e419aab95b8/6b071dfb870042f8e04904af/cyprus-tunart-GettyImages-961759390.jpg"
                "?width=720&quality=80&disable=upscale"
            ),
        ),
        (
            # media:content only
            "cisco-talos",
            "Oh, is it Thanksgiving? I hadn’t noticed!",
            (
                "https://storage.ghost.io/c/af/a0/afa04ee3-414f-4481-8d23-7e7c146f192e/content/"
                "images/2026/11/threat_source-3.jpg"
            ),
        ),
        (
            # an image enclosure
            "unit42",
            "The AI Threat Horizon: Why Speed, Edge AI and Baselines Are Our Best Defense",
            (
                "https://unit42.paloaltonetworks.com/wp-content/uploads/2026/11/"
                "05_Opinion_Category_1505x922.jpg"
            ),
        ),
    ],
)
def test_a_publishers_own_feed_image_is_kept_as_its_url(conn, source_id, headline, image_url):
    ingest(conn, by_id(source_id), real_sample(f"{source_id}.xml"), fetched_at=FETCHED_AT)

    assert _image_of(conn, headline) == image_url


def test_images_offered_over_plain_http_are_kept_in_their_https_form(conn):
    # The Record's enclosures are http://cms.therecord.media/... in the captured feed. The browser
    # loads the https form; if the publisher does not serve it, the page falls back to the tile.
    ingest(conn, by_id("therecord"), real_sample("therecord.xml"), fetched_at=FETCHED_AT)

    assert _image_of(
        conn, "UK’s long-awaited National Cyber Action Plan delayed until December"
    ) == (
        "https://cms.therecord.media/uploads/westminster_alexander_martin_the_record_133745e9ba.jpg"
    )


def test_a_feed_without_images_stores_none(conn):
    ingest(conn, BLEEPINGCOMPUTER, real_sample("bleepingcomputer.xml"), fetched_at=FETCHED_AT)

    events = storage.list_events(conn, limit=10).events
    assert [s.image_url for e in events for s in e.sources] == [None, None, None]


def test_attacker_claim_sources_never_provide_an_image(conn):
    # Ransomware.live's enclosures are screenshots of criminals' leak sites.
    ingest(
        conn,
        sample_source("ransomware-live"),
        real_sample("ransomware-live.xml"),
        fetched_at=FETCHED_AT,
    )

    stored = conn.execute("select image_url from source_records").fetchall()
    assert stored and all(url is None for (url,) in stored)


def test_a_non_image_enclosure_or_hostile_url_is_not_kept(conn):
    body = real_sample("unit42.xml").replace(
        b'<enclosure url="https://unit42.paloaltonetworks.com/wp-content/uploads/2026/11/'
        b'05_Opinion_Category_1505x922.jpg" type="image/jpeg"',
        b'<enclosure url="javascript:alert(1)" type="image/jpeg"',
        1,
    )
    ingest(conn, by_id("unit42"), body, fetched_at=FETCHED_AT)

    assert (
        _image_of(
            conn, "The AI Threat Horizon: Why Speed, Edge AI and Baselines Are Our Best Defense"
        )
        is None
    )
