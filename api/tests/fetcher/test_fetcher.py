"""Fetcher seam: network safety, tested against a local HTTPS stub server (never real sources)."""

import gzip
import time

import pytest

from compromised.pipeline.fetcher import FetchError, FetchPolicy, Validators, fetch
from compromised.sources import Source, Tier
from tests.stub_server import Reply, StubServer

UA = "CompromisedBot/test (+https://example.com/bot)"


@pytest.fixture
def stub():
    with StubServer() as server:
        yield server


def source_at(url: str, **kwargs) -> Source:
    return Source(
        id="stub",
        name="Stub",
        endpoint=url,
        format="rss",
        tier=Tier.PRESS,
        interval_seconds=60,
        **kwargs,
    )


def policy(**overrides) -> FetchPolicy:
    settings = {
        "user_agent": UA,
        "allowed_hosts": frozenset({"localhost"}),
        "connect_timeout": 2.0,
        "read_timeout": 2.0,
        "total_timeout": 5.0,
        "max_attempts": 3,
        "backoff_seconds": 0.05,
    }
    settings.update(overrides)
    return FetchPolicy(**settings)


async def test_an_allow_listed_https_endpoint_is_fetched_with_the_identifying_user_agent(stub):
    stub.reply("/feed", Reply(200, b"<rss/>"))

    async with stub.client() as client:
        result = await fetch(client, source_at(stub.url("/feed")), policy())

    assert result.body == b"<rss/>"
    assert stub.paths() == ["/feed"]
    assert stub.requests[0].headers["user-agent"] == UA


async def test_an_endpoint_whose_host_is_not_on_the_allow_list_is_never_requested(stub):
    stub.reply("/feed", Reply(200, b"<rss/>"))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="not on the allow-list"):
            await fetch(client, source_at(stub.url("/feed", host="127.0.0.1")), policy())

    assert stub.requests == []


async def test_a_plain_http_endpoint_is_never_requested(stub):
    async with stub.client() as client:
        with pytest.raises(FetchError, match="not HTTPS"):
            await fetch(client, source_at(f"http://localhost:{stub.port}/feed"), policy())

    assert stub.requests == []


async def test_a_redirect_to_an_allow_listed_https_url_is_followed(stub):
    stub.reply("/feed", Reply(301, headers={"Location": "/new-feed"}))
    stub.reply("/new-feed", Reply(200, b"<rss/>"))

    async with stub.client() as client:
        result = await fetch(client, source_at(stub.url("/feed")), policy())

    assert result.body == b"<rss/>"
    assert stub.paths() == ["/feed", "/new-feed"]
    assert stub.requests[1].headers["user-agent"] == UA


@pytest.mark.parametrize(
    "location",
    [
        "https://127.0.0.1:{port}/elsewhere",  # host not on the allow-list
        "http://localhost:{port}/elsewhere",  # downgrade to plain HTTP
        "https://evil.example/elsewhere",  # someone else's host
    ],
)
async def test_a_redirect_off_the_allow_list_is_refused_without_following_it(stub, location):
    stub.reply("/feed", Reply(302, headers={"Location": location.format(port=stub.port)}))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="redirect"):
            await fetch(client, source_at(stub.url("/feed")), policy())

    assert stub.paths() == ["/feed"]


async def test_redirect_chains_are_limited(stub):
    for n in range(5):
        stub.reply(f"/r{n}", Reply(302, headers={"Location": f"/r{n + 1}"}))
    stub.reply("/r5", Reply(200, b"<rss/>"))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="too many redirects"):
            await fetch(client, source_at(stub.url("/r0")), policy(max_redirects=3))

    assert stub.paths() == ["/r0", "/r1", "/r2", "/r3"]


@pytest.mark.parametrize("chunked", [False, True], ids=["content-length", "chunked"])
async def test_a_response_over_the_sources_size_cap_is_refused(stub, chunked):
    stub.reply("/feed", Reply(200, b"x" * 5000, chunked=chunked))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="size cap"):
            await fetch(client, source_at(stub.url("/feed"), max_bytes=4096), policy())

    assert stub.paths() == ["/feed"]  # not retried


async def test_the_size_cap_applies_to_the_decompressed_body(stub):
    bomb = gzip.compress(b"\0" * 1_000_000)
    assert len(bomb) < 4096
    stub.reply("/feed", Reply(200, bomb, headers={"Content-Encoding": "gzip"}))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="size cap"):
            await fetch(client, source_at(stub.url("/feed"), max_bytes=4096), policy())


async def test_a_response_within_the_size_cap_is_returned_whole(stub):
    stub.reply("/feed", Reply(200, b"x" * 4096, chunked=True))

    async with stub.client() as client:
        result = await fetch(client, source_at(stub.url("/feed"), max_bytes=4096), policy())

    assert result.body == b"x" * 4096


async def test_a_server_that_does_not_answer_in_time_is_abandoned(stub):
    stub.reply("/feed", Reply(200, b"<rss/>", delay=3.0))

    started = time.monotonic()
    async with stub.client() as client:
        with pytest.raises(FetchError, match="Timeout"):
            await fetch(
                client, source_at(stub.url("/feed")), policy(read_timeout=0.3, max_attempts=1)
            )

    assert time.monotonic() - started < 2.0


async def test_a_body_trickled_slowly_is_abandoned_at_the_total_timeout(stub):
    # Each byte arrives inside the read timeout, but the whole would take ~10 seconds.
    stub.reply("/feed", Reply(200, b"x" * 200, drip=0.05))

    started = time.monotonic()
    async with stub.client() as client:
        with pytest.raises(FetchError, match="total timeout"):
            await fetch(
                client,
                source_at(stub.url("/feed")),
                policy(read_timeout=1.0, total_timeout=0.5, max_attempts=1),
            )

    assert time.monotonic() - started < 2.0


async def test_an_error_status_is_a_fetch_error(stub):
    stub.reply("/feed", Reply(404, b"not here"))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="HTTP 404"):
            await fetch(client, source_at(stub.url("/feed")), policy())

    assert stub.paths() == ["/feed"]  # a client error is not retried


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_transient_failures_are_retried_with_growing_backoff(stub, status):
    stub.reply("/feed", Reply(status), Reply(status), Reply(200, b"<rss/>"))

    async with stub.client() as client:
        result = await fetch(
            client, source_at(stub.url("/feed")), policy(backoff_seconds=0.1, max_attempts=3)
        )

    assert result.body == b"<rss/>"
    first, second, third = (r.at for r in stub.requests)
    assert second - first >= 0.1
    assert third - second >= 0.2


async def test_retries_stop_after_the_last_attempt(stub):
    stub.reply("/feed", Reply(503))

    async with stub.client() as client:
        with pytest.raises(FetchError, match="HTTP 503"):
            await fetch(client, source_at(stub.url("/feed")), policy(max_attempts=3))

    assert stub.paths() == ["/feed"] * 3


async def test_a_timeout_is_retried(stub):
    stub.reply("/feed", Reply(200, b"slow", delay=1.0), Reply(200, b"<rss/>"))

    async with stub.client() as client:
        result = await fetch(
            client, source_at(stub.url("/feed")), policy(read_timeout=0.3, max_attempts=2)
        )

    assert result.body == b"<rss/>"


async def test_backoff_is_never_shorter_than_the_sources_crawl_delay(stub):
    stub.reply("/feed", Reply(503), Reply(200, b"<rss/>"))

    async with stub.client() as client:
        await fetch(
            client,
            source_at(stub.url("/feed"), crawl_delay_seconds=1),
            policy(backoff_seconds=0.01, max_attempts=2),
        )

    first, second = (r.at for r in stub.requests)
    assert second - first >= 1.0


async def test_stored_validators_are_sent_and_a_304_returns_no_body(stub):
    stub.reply("/feed", Reply(304, headers={"ETag": '"v1"'}))

    async with stub.client() as client:
        result = await fetch(
            client,
            source_at(stub.url("/feed")),
            policy(),
            Validators(etag='"v1"', last_modified="Thu, 26 Nov 2026 14:00:00 GMT"),
        )

    assert result.not_modified and result.body is None
    assert result.validators == Validators(
        etag='"v1"', last_modified="Thu, 26 Nov 2026 14:00:00 GMT"
    )
    headers = stub.requests[0].headers
    assert headers["if-none-match"] == '"v1"'
    assert headers["if-modified-since"] == "Thu, 26 Nov 2026 14:00:00 GMT"


async def test_a_full_response_returns_its_new_validators(stub):
    stub.reply(
        "/feed",
        Reply(
            200,
            b"<rss/>",
            headers={"ETag": '"v2"', "Last-Modified": "Thu, 26 Nov 2026 15:00:00 GMT"},
        ),
    )

    async with stub.client() as client:
        result = await fetch(client, source_at(stub.url("/feed")), policy(), Validators())

    assert not result.not_modified
    assert result.validators == Validators(
        etag='"v2"', last_modified="Thu, 26 Nov 2026 15:00:00 GMT"
    )
    assert "if-none-match" not in stub.requests[0].headers
    assert "if-modified-since" not in stub.requests[0].headers
