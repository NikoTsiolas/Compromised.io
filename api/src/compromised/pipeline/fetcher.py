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
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from compromised.sources import Source

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


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
            return await _attempt(client, source, policy, validators)
        except FetchError as exc:
            if not exc.transient or attempt == policy.max_attempts:
                raise
        delay = policy.backoff_seconds * 2 ** (attempt - 1)
        await asyncio.sleep(max(delay, source.crawl_delay_seconds))
    raise AssertionError("unreachable")


async def _attempt(
    client: httpx.AsyncClient, source: Source, policy: FetchPolicy, validators: Validators
) -> FetchResult:
    try:
        async with asyncio.timeout(policy.total_timeout):
            return await _follow(client, source, policy, validators)
    except TimeoutError:
        raise FetchError(
            f"total timeout ({policy.total_timeout:g}s) exceeded", transient=True
        ) from None
    except httpx.TransportError as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}", transient=True) from exc
    except httpx.HTTPError as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc


async def _follow(
    client: httpx.AsyncClient, source: Source, policy: FetchPolicy, validators: Validators
) -> FetchResult:
    url = source.endpoint
    headers = {"User-Agent": policy.user_agent}
    if validators.etag:
        headers["If-None-Match"] = validators.etag
    if validators.last_modified:
        headers["If-Modified-Since"] = validators.last_modified
    timeout = httpx.Timeout(policy.read_timeout, connect=policy.connect_timeout)
    for _ in range(policy.max_redirects + 1):
        request = client.build_request("GET", url, headers=headers, timeout=timeout)
        response = await client.send(request, stream=True, follow_redirects=False)
        try:
            status = response.status_code
            if status in REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location:
                    raise FetchError(f"HTTP {status} redirect without a Location")
                url = urljoin(url, location)
                _check_url(url, policy, what="redirect target")
                continue
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
        finally:
            await response.aclose()
    raise FetchError(f"too many redirects (more than {policy.max_redirects})")


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
