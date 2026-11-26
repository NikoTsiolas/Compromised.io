"""Article preview images: the picture a publisher declares on its own article page.

For a stored source record with no feed image, the article page is asked once, ever, for its
og:image (else twitter:image) address. Narrowly:

- Only when the article URL is https and its host is one the source's registry entry declares
  as an article host (``Source.article_hosts``). Redirects are re-checked against those hosts.
  Sources without declared hosts (structured and attacker-claim sources) are never fetched.
- Through the hardened fetcher: identifying user agent, timeouts, a single attempt, and only the
  document head is read (``PAGE_HEAD_CAP`` at most). robots.txt is honoured, and the source's
  crawl delay (at least ``MIN_DELAY_SECONDS``) separates pages from the same publisher.
- The HTML is parsed with the standard library's parser; nothing in it is executed or followed.
  Only an https address is stored. The image itself is never requested by our server: readers'
  browsers load it from the publisher.
- A failure is recorded and never retried, and never affects the record or its event.
"""

import asyncio
import logging
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib import robotparser
from urllib.parse import urljoin, urlsplit

import httpx
import psycopg

from compromised import storage
from compromised.pipeline.fetcher import (
    FetchError,
    FetchPolicy,
    fetch_page,
    fetch_status_and_body,
)
from compromised.pipeline.normalizer import IMAGE_URL_LIMIT
from compromised.sources import Source

log = logging.getLogger("compromised.previews")

PAGE_HEAD_CAP = 256 * 1024
ROBOTS_CAP = 256 * 1024
PER_PASS = 5  # pages per source per worker pass, so a busy feed is worked through politely
MIN_DELAY_SECONDS = 2.0


@dataclass(frozen=True)
class PreviewOutcome:
    attempted: int = 0
    found: int = 0


async def fill_previews(
    conn: psycopg.Connection,
    client: httpx.AsyncClient,
    policy: FetchPolicy,
    source: Source,
    *,
    limit: int = PER_PASS,
    delay_seconds: float | None = None,
) -> PreviewOutcome:
    """Ask up to ``limit`` of the source's unattempted records' article pages for a preview."""
    if not source.article_hosts or not source.publisher_images:
        return PreviewOutcome()
    # Article pages may be fetched from the declared article hosts only, never the feed list.
    page_policy = replace(policy, allowed_hosts=frozenset(source.article_hosts), max_attempts=1)
    delay = (
        delay_seconds
        if delay_seconds is not None
        else max(MIN_DELAY_SECONDS, float(source.crawl_delay_seconds))
    )
    robots: dict[str, robotparser.RobotFileParser | None] = {}
    attempted = found = 0
    for record_id, url in storage.records_awaiting_preview(conn, source.id, limit=limit):
        host = (urlsplit(url).hostname or "").lower()
        if urlsplit(url).scheme != "https" or host not in source.article_hosts:
            storage.save_preview(conn, record_id, None, "skipped", datetime.now(UTC))
            continue
        if host not in robots:
            robots[host] = await _robots(client, page_policy, url)
        rules = robots[host]
        if rules is None or not rules.can_fetch(policy.user_agent, url):
            storage.save_preview(conn, record_id, None, "skipped", datetime.now(UTC))
            continue
        if attempted:
            await asyncio.sleep(delay)
        attempted += 1
        try:
            final_url, head = await fetch_page(client, url, page_policy, max_bytes=PAGE_HEAD_CAP)
        except FetchError as exc:
            storage.save_preview(conn, record_id, None, "failed", datetime.now(UTC))
            log.info("preview failed", extra={"source": source.id, "error": str(exc)})
            continue
        image = preview_image(head, final_url)
        storage.save_preview(
            conn, record_id, image, "found" if image else "none", datetime.now(UTC)
        )
        found += image is not None
    return PreviewOutcome(attempted=attempted, found=found)


async def _robots(
    client: httpx.AsyncClient, policy: FetchPolicy, url: str
) -> robotparser.RobotFileParser | None:
    """The host's robots.txt rules. A missing file (4xx) allows everything; an unreachable or
    failing one (5xx, network error) allows nothing, as RFC 9309 asks."""
    parts = urlsplit(url)
    robots_url = f"https://{parts.netloc}/robots.txt"
    rules = robotparser.RobotFileParser(robots_url)
    try:
        status, body = await fetch_status_and_body(client, robots_url, policy, max_bytes=ROBOTS_CAP)
    except FetchError:
        return None
    if 400 <= status < 500:
        rules.parse([])
        return rules
    if status != 200:
        return None
    rules.parse(body.decode("utf-8", errors="replace").splitlines())
    return rules


def preview_image(head: bytes, page_url: str) -> str | None:
    """The page's og:image, else twitter:image, as an absolute https address, or None."""
    # html.parser is lenient by design: broken markup yields fewer tags, never an exception.
    parser = _MetaImages()
    parser.feed(head.decode("utf-8", errors="replace"))
    parser.close()
    for candidate in (parser.og, parser.twitter):
        if candidate:
            safe = _https_address(urljoin(page_url, candidate.strip()))
            if safe:
                return safe
    return None


def _https_address(url: str) -> str | None:
    if len(url) > IMAGE_URL_LIMIT or any(c.isspace() or c in "\"'<>\\" for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError:
        return None
    if parts.scheme != "https" or not host or host.endswith(".onion"):
        return None
    if parts.username or parts.password:
        return None
    return url


class _MetaImages(HTMLParser):
    """Collects the first og:image and twitter:image <meta> values, and nothing else."""

    OG = frozenset({"og:image", "og:image:secure_url", "og:image:url"})
    TWITTER = frozenset({"twitter:image", "twitter:image:src"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.og: str | None = None
        self.twitter: str | None = None

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        key = (a.get("property") or a.get("name") or "").strip().lower()
        content = a.get("content")
        if not content:
            return
        if key in self.OG and self.og is None:
            self.og = content
        elif key in self.TWITTER and self.twitter is None:
            self.twitter = content

    handle_startendtag = handle_starttag
