"""Fetcher: downloads a source's registry endpoint, safely.

- Only hosts on the allow-list (the registry's endpoint hosts) are contacted, over HTTPS only.
  No URL taken from feed content is ever passed here.
- Redirects are followed by hand, a few at most, and each target is re-checked.
- Connect, read and whole-attempt timeouts; a per-source cap on the decoded body size.
- Conditional GET with the stored ETag and Last-Modified; a 304 returns no body.
- Transient failures (connection errors, timeouts, 429, 5xx) are retried with exponential
  backoff, never sooner than the source's crawl delay. Other failures are not retried.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from compromised.sources import Source

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
HEAD_END = re.compile(rb"</head\s*>|<body[\s>]", re.IGNORECASE)


class FetchError(Exception):
    """The source could not be fetched. ``transient`` failures are worth retrying."""

    def __init__(self, message: str, *, transient: bool = False):
        super().__init__(message)
        self.transient = transient


@dataclass(frozen=True)
class FetchPolicy:
    user_agent: str
    allowed_hosts: frozenset[str]
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0  # per attempt, so a slowly trickled body cannot hold a worker
    max_attempts: int = 3
    backoff_seconds: float = 2.0  # doubles after each failed attempt
    max_redirects: int = 3


@dataclass(frozen=True)
class Validators:
    """HTTP cache validators from a source's last full response."""

    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class FetchResult:
    body: bytes | None  # None when the source answered 304 Not Modified
    validators: Validators

    @property
    def not_modified(self) -> bool:
        return self.body is None


async def fetch(
    client: httpx.AsyncClient,
    source: Source,
    policy: FetchPolicy,
    validators: Validators = Validators(),
) -> FetchResult:
    _check_url(source.endpoint, policy, what="endpoint")
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await _feed_attempt(client, source, policy, validators)
        except FetchError as exc:
            if not exc.transient or attempt == policy.max_attempts:
                raise
        delay = policy.backoff_seconds * 2 ** (attempt - 1)
        await asyncio.sleep(max(delay, source.crawl_delay_seconds))
    raise AssertionError("unreachable")


async def fetch_page(
    client: httpx.AsyncClient, url: str, policy: FetchPolicy, *, max_bytes: int
) -> tuple[str, bytes]:
    """One GET of a page on an allow-listed host: a single attempt, never retried, reading only
    up to the end of the document head (or ``max_bytes``, whichever comes first).

    Returns the final URL (after re-checked redirects) and the bytes read.
    """
    _check_url(url, policy, what="page")

    async def read(response: httpx.Response, final_url: str) -> tuple[str, bytes]:
        if response.status_code != 200:
            raise FetchError(f"HTTP {response.status_code}")
        return final_url, await _read_head(response, max_bytes)

    return await _attempt(lambda: _follow(client, url, policy, {}, read), policy)


async def fetch_status_and_body(
    client: httpx.AsyncClient, url: str, policy: FetchPolicy, *, max_bytes: int
) -> tuple[int, bytes]:
    """One GET on an allow-listed host (a single attempt), returning the final status and up to
    ``max_bytes`` of the body. For small control files such as robots.txt."""
    _check_url(url, policy, what="url")

    async def read(response: httpx.Response, _url: str) -> tuple[int, bytes]:
        if response.status_code != 200:
            return response.status_code, b""
        return 200, await _read_capped(response, max_bytes)

    return await _attempt(lambda: _follow(client, url, policy, {}, read), policy)


async def _attempt[T](run: Callable[[], Awaitable[T]], policy: FetchPolicy) -> T:
    try:
        async with asyncio.timeout(policy.total_timeout):
            return await run()
    except TimeoutError:
        raise FetchError(
            f"total timeout ({policy.total_timeout:g}s) exceeded", transient=True
        ) from None
    except httpx.TransportError as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}", transient=True) from exc
    except httpx.HTTPError as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc


async def _feed_attempt(
    client: httpx.AsyncClient, source: Source, policy: FetchPolicy, validators: Validators
) -> FetchResult:
    headers = {}
    if validators.etag:
        headers["If-None-Match"] = validators.etag
    if validators.last_modified:
        headers["If-Modified-Since"] = validators.last_modified

    async def read(response: httpx.Response, _url: str) -> FetchResult:
        status = response.status_code
        if status == 304:
            return FetchResult(body=None, validators=validators)
        if status != 200:
            raise FetchError(f"HTTP {status}", transient=status == 429 or status >= 500)
        body = await _read_capped(response, source.max_bytes)
        return FetchResult(
            body=body,
            validators=Validators(
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
            ),
        )

    return await _attempt(lambda: _follow(client, source.endpoint, policy, headers, read), policy)


async def _follow[T](
    client: httpx.AsyncClient,
    url: str,
    policy: FetchPolicy,
    extra_headers: dict[str, str],
    read: Callable[[httpx.Response, str], Awaitable[T]],
) -> T:
    """GET ``url``, following redirects by hand and re-checking every target."""
    headers = {"User-Agent": policy.user_agent, **extra_headers}
    timeout = httpx.Timeout(policy.read_timeout, connect=policy.connect_timeout)
    for _ in range(policy.max_redirects + 1):
        request = client.build_request("GET", url, headers=headers, timeout=timeout)
        response = await client.send(request, stream=True, follow_redirects=False)
        try:
            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location:
                    raise FetchError(f"HTTP {response.status_code} redirect without a Location")
                url = urljoin(url, location)
                _check_url(url, policy, what="redirect target")
                continue
            return await read(response, url)
        finally:
            await response.aclose()
    raise FetchError(f"too many redirects (more than {policy.max_redirects})")


async def _read_head(response: httpx.Response, max_bytes: int) -> bytes:
    """Read until the document head has ended, stopping at ``max_bytes`` in any case."""
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body += chunk
        if HEAD_END.search(body) or len(body) >= max_bytes:
            break
    return bytes(body[:max_bytes])


async def _read_capped(response: httpx.Response, max_bytes: int) -> bytes:
    """Read the decoded body, refusing anything past the cap (also catches compression bombs)."""
    declared = response.headers.get("content-length", "")
    uncompressed = "content-encoding" not in response.headers
    if uncompressed and declared.isdigit() and int(declared) > max_bytes:
        raise FetchError(f"response of {declared} bytes is over the size cap ({max_bytes})")
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body += chunk
        if len(body) > max_bytes:
            raise FetchError(f"response is over the size cap ({max_bytes} bytes)")
    return bytes(body)


def _check_url(url: str, policy: FetchPolicy, *, what: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise FetchError(f"{what} is not HTTPS")
    if parts.username or parts.password or (parts.hostname or "") not in policy.allowed_hosts:
        raise FetchError(f"{what} host {parts.hostname!r} is not on the allow-list")
