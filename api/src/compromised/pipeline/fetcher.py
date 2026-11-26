"""Fetcher: downloads a source's registry endpoint.

Walking skeleton only: HTTPS registry endpoint, identifying user agent, timeouts, no redirects
followed. The allow-list, size cap, conditional GET, retries and source health are #3.
"""

import httpx

from compromised.sources import Source

TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class FetchError(Exception):
    pass


async def fetch(client: httpx.AsyncClient, source: Source, *, user_agent: str) -> bytes:
    if not source.endpoint.startswith("https://"):
        raise FetchError(f"{source.id}: endpoint is not HTTPS")
    try:
        response = await client.get(
            source.endpoint,
            headers={"User-Agent": user_agent},
            timeout=TIMEOUT,
            follow_redirects=False,
        )
    except httpx.HTTPError as exc:
        raise FetchError(f"{source.id}: {type(exc).__name__}") from exc
    if response.status_code != 200:
        raise FetchError(f"{source.id}: HTTP {response.status_code}")
    return response.content
