"""The shapes passed between pipeline stages and returned by storage."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ParsedItem:
    """One feed item as the parser saw it. May still contain HTML; never stored."""

    guid: str | None
    link: str | None
    title: str
    summary_html: str
    published: datetime | None  # timezone-aware
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceRecord:
    """One normalized item from one source. Plain text only."""

    source_id: str
    guid: str | None
    canonical_url: str
    original_url: str
    headline: str
    excerpt: str
    published_at: datetime  # UTC
    fetched_at: datetime  # UTC
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventSource:
    publisher: str
    url: str
    headline: str
    excerpt: str
    published_at: datetime


@dataclass(frozen=True)
class Event:
    id: int
    title: str
    published_at: datetime
    first_seen_at: datetime
    sources: list[EventSource]


@dataclass(frozen=True)
class EventPage:
    events: list[Event]
    next_cursor: str | None
