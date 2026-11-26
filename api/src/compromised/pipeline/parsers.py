"""Parsers: raw response bytes -> parsed items. One adapter per registry ``format``."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser

from compromised.records import ParsedItem

# Byte-order mark, XML declaration, whitespace, comments and processing instructions, then a
# DOCTYPE. Matching stops at the first element, so a DOCTYPE quoted inside an article is fine.
DOCTYPE_IN_PROLOG = re.compile(
    rb"^(?:\xef\xbb\xbf)?(?:\s|<\?.*?\?>|<!--.*?-->)*<!DOCTYPE", re.DOTALL | re.IGNORECASE
)


class ParseError(Exception):
    """The response is not a feed this adapter can read safely."""


def parse_rss(body: bytes) -> list[ParsedItem]:
    """RSS/Atom via feedparser, which does not resolve external entities.

    As a second guard, a document type declaration in the prolog (where entities are declared)
    is refused outright: none of the registry's feeds sends one.
    """
    if DOCTYPE_IN_PROLOG.match(body):
        raise ParseError("document type declarations are not accepted")
    feed = feedparser.parse(body)
    if not feed.get("version"):
        reason = feed.get("bozo_exception") or "no RSS or Atom root element"
        raise ParseError(f"not a feed: {reason}")
    items = []
    for entry in feed.entries:
        metadata = {}
        if entry.get("author"):
            metadata["author"] = entry["author"]
        categories = [t["term"] for t in entry.get("tags", []) if t.get("term")]
        if categories:
            metadata["categories"] = categories
        items.append(
            ParsedItem(
                guid=entry.get("id"),
                link=entry.get("link"),
                title=entry.get("title", ""),
                summary_html=entry.get("summary", ""),
                published=_published(entry),
                metadata=metadata,
                image_url=_feed_image(entry),
            )
        )
    return items


def _feed_image(entry) -> str | None:
    """The image the publisher attached to the item: media:content, media:thumbnail, or an
    image enclosure, in that order. Only the URL is read; nothing is fetched."""
    for media in entry.get("media_content", []):
        medium = media.get("medium", "")
        kind = media.get("type", "")
        if media.get("url") and (medium == "image" or kind.startswith("image/")):
            return media["url"]
    for thumb in entry.get("media_thumbnail", []):
        if thumb.get("url"):
            return thumb["url"]
    for link in entry.get("links", []):
        is_image = link.get("type", "").startswith("image/")
        if link.get("rel") == "enclosure" and is_image and link.get("href"):
            return link["href"]
    return None


def _published(entry) -> datetime | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    # RFC 2822 "-0000" means "UTC, origin zone unknown" and parses as naive.
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


PARSERS: dict[str, Callable[[bytes], list[ParsedItem]]] = {"rss": parse_rss}
