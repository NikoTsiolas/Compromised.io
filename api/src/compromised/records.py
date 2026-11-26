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
    # The image the publisher attached to the item in its own feed, unchecked.
    image_url: str | None = None


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
    # The publisher's own feed image: https only, never downloaded, None when there is none.
    image_url: str | None = None


@dataclass(frozen=True)
class EventSource:
    publisher: str
    url: str
    headline: str
    excerpt: str
    published_at: datetime
    image_url: str | None = None
    source_id: str = ""


@dataclass(frozen=True)
class Event:
    id: int
    title: str
    published_at: datetime
    first_seen_at: datetime
    sources: list[EventSource]
    category: str = "other"
    commentary: bool = False
    affected_organization: str = "unknown"  # "unknown" when no organization is known
    organization_key: str | None = None
    logo_key: str | None = None
    tabs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventPage:
    events: list[Event]
    next_cursor: str | None
