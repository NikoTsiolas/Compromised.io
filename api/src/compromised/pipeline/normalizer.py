"""Normalizer: parsed item -> source record.

Canonical URL, HTML stripped to plain text, excerpt capped near 300 characters, timestamps in
UTC. Feed HTML never leaves this module. CVE extraction arrives with the tickets that use it.
"""

import html
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from compromised.records import ParsedItem, SourceRecord

EXCERPT_LIMIT = 300
TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
# Boilerplate tails publishers append to summaries: "[...]", "...", "The post X appeared first on Y."
BOILERPLATE_TAIL = re.compile(
    r"(\s*(\[(\.\.\.|…)\]|\.\.\.|…)\s*$)|(\s*The post .* appeared first on .*$)", re.DOTALL
)
# A tag left unterminated where a body was cut off ("... <a href="https://..."): the parser
# returns it as text. "<" followed by a space ("versions < 2.4") is not a tag and stays.
DANGLING_TAG = re.compile(r"<[A-Za-z!/?][^<>]*$")


def normalize(
    item: ParsedItem, *, source_id: str, fetched_at: datetime, images: bool = True
) -> SourceRecord | None:
    """Return the record to store, or None when the item has no usable link or headline.

    ``images=False`` drops the feed image (attacker-claim sources, whose images are screenshots
    of leak sites)."""
    canonical = canonical_url(item.link or "")
    headline = plain_text(item.title)
    if canonical is None or not headline:
        return None
    published = (item.published or fetched_at).astimezone(UTC)
    return SourceRecord(
        source_id=source_id,
        guid=item.guid,
        canonical_url=canonical,
        original_url=item.link.strip(),
        headline=headline,
        excerpt=excerpt(item.summary_html),
        published_at=published,
        fetched_at=fetched_at.astimezone(UTC),
        metadata={k: _plain_metadata(v) for k, v in item.metadata.items()},
        image_url=image_url(item.image_url) if images else None,
    )


def canonical_url(url: str) -> str | None:
    """Lower-case scheme and host, drop fragments and tracking parameters.

    Only http(s) URLs are kept; .onion hosts and anything else return None.
    """
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if scheme not in ("http", "https") or not host or host.endswith(".onion"):
        return None
    netloc = host if parts.port is None else f"{host}:{parts.port}"
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
        ]
    )
    return urlunsplit((scheme, netloc, parts.path or "/", query, ""))


IMAGE_URL_LIMIT = 2048


def image_url(url: str | None) -> str | None:
    """The feed image's URL if it is a plain https URL; anything else is dropped, not repaired.

    The browser loads it straight from the publisher, so http (mixed content), other schemes,
    .onion hosts, credentials in the URL and oversized values are all refused.
    """
    if not url:
        return None
    url = url.strip()
    if len(url) > IMAGE_URL_LIMIT or any(c.isspace() or c in "\"'<>" for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    if parts.scheme.lower() != "https" or not host or host.endswith(".onion"):
        return None
    if parts.username or parts.password:
        return None
    return urlunsplit(("https", parts.netloc.lower(), parts.path or "/", parts.query, ""))


def plain_text(fragment: str) -> str:
    """Strip tags, decode entities, collapse whitespace.

    Some feeds double-escape (Dark Reading wraps escaped text in CDATA), so entities are decoded
    a second time and any markup that decoding reveals is stripped again. A bare "<" that is not
    a tag ("versions < 2.4") survives as text.
    """
    text = _strip_tags(html.unescape(_strip_tags(fragment)))
    return " ".join(text.split())


def _strip_tags(fragment: str) -> str:
    stripper = _TextExtractor()
    stripper.feed(fragment)
    stripper.close()
    return DANGLING_TAG.sub("", stripper.text())


def excerpt(summary_html: str) -> str:
    text = BOILERPLATE_TAIL.sub("", plain_text(summary_html)).strip()
    if len(text) <= EXCERPT_LIMIT:
        return text
    cut = text[: EXCERPT_LIMIT - 1]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut.rstrip(" ,;:.-") + "…"


def _plain_metadata(value):
    if isinstance(value, str):
        return plain_text(value)
    if isinstance(value, list):
        return [_plain_metadata(v) for v in value]
    return value


class _TextExtractor(HTMLParser):
    _SKIP = frozenset({"script", "style"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skipping += 1
        self._parts.append(" ")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skipping:
            self._skipping -= 1
        self._parts.append(" ")

    def handle_data(self, data):
        if not self._skipping:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)
