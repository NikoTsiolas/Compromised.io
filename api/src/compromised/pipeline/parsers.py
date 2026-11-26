"""Parsers: raw response bytes -> parsed items. One adapter per registry ``format``."""

from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser

from compromised.records import ParsedItem


def parse_rss(body: bytes) -> list[ParsedItem]:
    feed = feedparser.parse(body)
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
            )
        )
    return items


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
