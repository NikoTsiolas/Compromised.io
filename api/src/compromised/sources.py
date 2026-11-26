"""Source registry: one declarative entry per source.

Endpoints and intervals come from docs/wiki/feed-scope-and-sources.md. Only the fields the
walking skeleton uses are defined; tier, weight and the per-source size cap arrive with #3 and #7.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    endpoint: str
    format: str  # parser adapter key, see pipeline.parsers
    interval_seconds: int

    @property
    def host(self) -> str:
        return urlsplit(self.endpoint).hostname or ""


BLEEPINGCOMPUTER = Source(
    id="bleepingcomputer",
    name="BleepingComputer",
    endpoint="https://www.bleepingcomputer.com/feed/",
    format="rss",
    interval_seconds=10 * 60,
)

REGISTRY: tuple[Source, ...] = (BLEEPINGCOMPUTER,)


def by_id(source_id: str) -> Source:
    for source in REGISTRY:
        if source.id == source_id:
            return source
    raise KeyError(source_id)
