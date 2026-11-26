"""Pipeline seam: the preview image a publisher declares on its own article page.

For a stored record with no feed image, the article page is fetched once, only from the source's
declared article hosts, honouring robots.txt, reading no more than the document head, and only
the og:image (else twitter:image) address is kept, if it is https. The pages here are synthetic,
served by the local HTTPS stub server; nothing touches a real site.
"""

from datetime import UTC, datetime

import pytest

from compromised import storage
from compromised.pipeline import ingest
from compromised.pipeline.fetcher import FetchPolicy
from compromised.pipeline.previews import fill_previews
from compromised.sources import REGISTRY, Source, Tier
from tests.stub_server import Reply, StubServer

FETCHED_AT = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
UA = "CompromisedBot/test (+https://example.com/bot)"


@pytest.fixture
def stub():
    with StubServer() as server:
        yield server


def press_source(stub: StubServer, **kwargs) -> Source:
    return Source(
        id="stub-press",
        name="Stub Press",
        endpoint=stub.url("/feed"),
        format="rss",
        tier=Tier.PRESS,
        interval_seconds=60,
        article_hosts=("localhost",),
        **kwargs,
    )


def policy() -> FetchPolicy:
    return FetchPolicy(
        user_agent=UA,
        allowed_hosts=frozenset(),  # previews use the source's article hosts, never this list
        connect_timeout=2.0,
        read_timeout=2.0,
        total_timeout=5.0,
        backoff_seconds=0.05,
    )


def feed(*links: str, image: str | None = None) -> bytes:
    """A synthetic RSS feed whose items link to the given article URLs."""
    items = "".join(
        f"""<item><title>[Synthetic test item] Breach story {i}</title>
        <link>{link}</link><guid>{link}</guid>
        <pubDate>Thu, 26 Nov 2026 1{i}:00:00 +0000</pubDate>
        <description>Synthetic excerpt.</description>
        {f'<media:content url="{image}" medium="image"/>' if image else ""}</item>"""
        for i, link in enumerate(links)
    )
    return f"""<?xml version="1.0"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>
<title>Synthetic test feed</title><link>https://example.com/</link>
<description>Synthetic test data</description>{items}</channel></rss>""".encode()


def page(head: str, body: str = "<p>Synthetic article.</p>") -> bytes:
    return f"<!doctype html><html><head><title>Synthetic</title>{head}</head><body>{body}</body></html>".encode()


def images(conn) -> list[str | None]:
    """Each stored source's picture as the feed shows it, newest first."""
    events = storage.list_events(conn, limit=50).events
    sources = sorted(
        (s for e in events for s in e.sources), key=lambda s: s.published_at, reverse=True
    )
    return [s.image_url for s in sources]


async def run(conn, stub, source, *, passes: int = 1):
    async with stub.client() as client:
        for _ in range(passes):
            await fill_previews(conn, client, policy(), source, delay_seconds=0)


async def test_the_og_image_of_an_article_on_the_publishers_own_host_is_kept(conn, stub):
    source = press_source(stub)
    stub.reply(
        "/a/1",
        Reply(200, page('<meta property="og:image" content="https://cdn.example.com/1.jpg">')),
    )
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == ["https://cdn.example.com/1.jpg"]
    article = next(r for r in stub.requests if r.path == "/a/1")
    assert article.headers["user-agent"] == UA


async def test_twitter_image_is_the_fallback_and_relative_addresses_resolve(conn, stub):
    source = press_source(stub)
    stub.reply("/a/1", Reply(200, page('<meta name="twitter:image" content="/img/1.png">')))
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == [stub.url("/img/1.png")]
    # The image itself is never requested by us.
    assert "/img/1.png" not in stub.paths()


async def test_an_article_link_off_the_declared_hosts_is_never_requested(conn, stub):
    source = press_source(stub)
    stub.reply(
        "/a/1",
        Reply(200, page('<meta property="og:image" content="https://cdn.example.com/1.jpg">')),
    )
    # Same server, but addressed as 127.0.0.1, which the source does not declare.
    ingest(conn, source, feed(stub.url("/a/1", host="127.0.0.1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == [None]
    assert "/a/1" not in stub.paths()


async def test_a_redirect_off_the_declared_hosts_is_not_followed(conn, stub):
    source = press_source(stub)
    stub.reply("/a/1", Reply(302, headers={"Location": stub.url("/b/1", host="127.0.0.1")}))
    stub.reply(
        "/b/1",
        Reply(200, page('<meta property="og:image" content="https://cdn.example.com/1.jpg">')),
    )
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == [None]
    assert "/b/1" not in stub.paths()


async def test_robots_txt_disallowing_the_article_is_honoured(conn, stub):
    source = press_source(stub)
    stub.reply("/robots.txt", Reply(200, b"User-agent: *\nDisallow: /a/\n"))
    stub.reply(
        "/a/1",
        Reply(200, page('<meta property="og:image" content="https://cdn.example.com/1.jpg">')),
    )
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == [None]
    assert "/a/1" not in stub.paths()


async def test_only_the_document_head_is_read_from_an_oversized_page(conn, stub):
    source = press_source(stub)
    padding = "<!-- " + "x" * 600_000 + " -->"
    stub.reply(
        "/a/1",
        Reply(
            200,
            page(padding + '<meta property="og:image" content="https://cdn.example.com/late.jpg">'),
            chunked=True,
        ),
    )
    stub.reply(
        "/a/2",
        Reply(
            200,
            page(
                '<meta property="og:image" content="https://cdn.example.com/2.jpg">',
                body="y" * 900_000,
            ),
        ),
    )
    ingest(conn, source, feed(stub.url("/a/1"), stub.url("/a/2")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    # The first page's tag sits past the cap; the second's head is small and its huge body unread.
    assert images(conn) == ["https://cdn.example.com/2.jpg", None]


async def test_a_page_without_preview_tags_stores_nothing_and_is_not_fetched_again(conn, stub):
    source = press_source(stub)
    stub.reply("/a/1", Reply(200, page('<meta name="description" content="No image here">')))
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source, passes=2)

    assert images(conn) == [None]
    assert stub.paths().count("/a/1") == 1


async def test_a_failing_page_gets_one_attempt_ever_and_never_blocks_the_record(conn, stub):
    source = press_source(stub)
    stub.reply("/a/1", Reply(503))
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source, passes=3)

    assert stub.paths().count("/a/1") == 1
    assert [e.title for e in storage.list_events(conn, limit=5).events] == [
        "[Synthetic test item] Breach story 0"
    ]


@pytest.mark.parametrize(
    "tag",
    [
        '<meta property="og:image" content="http://cdn.example.com/1.jpg">',
        '<meta property="og:image" content="javascript:alert(1)">',
        '<meta property="og:image" content="https://cdn.example.com/a.jpg&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;">',
        '<meta property="og:image" content="https://user:pw@cdn.example.com/1.jpg">',
        '<meta property="og:image" content="data:image/png;base64,AAAA">',
    ],
)
async def test_unsafe_or_plain_http_preview_addresses_are_not_kept(conn, stub, tag):
    source = press_source(stub)
    stub.reply("/a/1", Reply(200, page(tag)))
    ingest(conn, source, feed(stub.url("/a/1")), fetched_at=FETCHED_AT)

    await run(conn, stub, source)

    assert images(conn) == [None]


async def test_records_that_already_have_a_feed_image_are_never_fetched(conn, stub):
    source = press_source(stub)
    ingest(
        conn,
        source,
        feed(stub.url("/a/1"), image="https://cdn.example.com/feed.jpg"),
        fetched_at=FETCHED_AT,
    )

    await run(conn, stub, source)

    assert images(conn) == ["https://cdn.example.com/feed.jpg"]
    assert "/a/1" not in stub.paths()


async def test_a_pass_fetches_at_most_a_handful_of_pages_per_source(conn, stub):
    source = press_source(stub)
    links = [stub.url(f"/a/{i}") for i in range(8)]
    for i in range(8):
        stub.reply(f"/a/{i}", Reply(200, page("")))
    ingest(conn, source, feed(*links), fetched_at=FETCHED_AT)

    async with stub.client() as client:
        await fill_previews(conn, client, policy(), source, limit=3, delay_seconds=0)

    assert len([p for p in stub.paths() if p.startswith("/a/")]) == 3


def test_only_sources_with_declared_article_hosts_get_page_fetches():
    hosts = {s.id: s.article_hosts for s in REGISTRY}
    # Feed hosts are never article hosts.
    assert "feeds.feedburner.com" not in {h for hs in hosts.values() for h in hs}
    assert hosts["thehackernews"] == ("thehackernews.com",)
    assert hosts["therecord"] == ("therecord.media",)
    for source in REGISTRY:
        if source.tier == Tier.ATTACKER_CLAIM or source.format != "rss":
            assert source.article_hosts == ()
