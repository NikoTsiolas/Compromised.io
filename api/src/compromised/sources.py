"""Source registry: one declarative entry per source.

Endpoints and intervals come from docs/wiki/feed-scope-and-sources.md; tiers and default weights
from docs/wiki/trust-labels-and-score.md. The fetcher only ever requests hosts named here.
To change how often a source is polled, edit its ``interval_seconds``.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlsplit

MIN = 60
MB = 1024 * 1024


class Tier(StrEnum):
    OFFICIAL = "official"  # vendor and government sources
    PRESS = "press"  # established press
    ATTACKER_CLAIM = "attacker_claim"  # attacker-claim aggregators


# A source's weight defaults to its tier's base score in the confidence formula.
TIER_WEIGHT = {Tier.OFFICIAL: 90, Tier.PRESS: 50, Tier.ATTACKER_CLAIM: 20}


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    endpoint: str
    format: str  # parser adapter key, see pipeline.parsers
    tier: Tier
    interval_seconds: int
    max_bytes: int = 2 * MB  # response size cap, measured after decompression
    crawl_delay_seconds: int = 0  # minimum wait between requests (robots.txt Crawl-Delay)
    weight: int = field(default=-1)
    # Items published more than this many days before a fetch are never imported, so a first
    # run backfills only that far (structured sources hold months or years of entries).
    backfill_days: int | None = None

    def __post_init__(self):
        if self.weight < 0:
            object.__setattr__(self, "weight", TIER_WEIGHT[self.tier])

    @property
    def host(self) -> str:
        return urlsplit(self.endpoint).hostname or ""


def _rss(id, name, endpoint, tier, minutes, **kwargs) -> Source:
    return Source(
        id=id,
        name=name,
        endpoint=endpoint,
        format="rss",
        tier=tier,
        interval_seconds=minutes * MIN,
        **kwargs,
    )


THE_RECORD = _rss("therecord", "The Record", "https://therecord.media/feed", Tier.PRESS, 5)
BLEEPINGCOMPUTER = _rss(
    "bleepingcomputer",
    "BleepingComputer",
    "https://www.bleepingcomputer.com/feed/",
    Tier.PRESS,
    10,
)
SECURITYWEEK = _rss(
    "securityweek", "SecurityWeek", "https://www.securityweek.com/feed/", Tier.PRESS, 10
)
THE_HACKER_NEWS = _rss(
    "thehackernews",
    "The Hacker News",
    "https://feeds.feedburner.com/TheHackersNews",
    Tier.PRESS,
    15,
)
DARK_READING = _rss(
    "darkreading", "Dark Reading", "https://www.darkreading.com/rss.xml", Tier.PRESS, 15
)
SECURITY_AFFAIRS = _rss(
    "securityaffairs", "Security Affairs", "https://securityaffairs.com/feed", Tier.PRESS, 15
)
KREBS = _rss(
    "krebsonsecurity",
    "Krebs on Security",
    "https://krebsonsecurity.com/feed/",
    Tier.PRESS,
    30,
    crawl_delay_seconds=35,
)
CISCO_TALOS = _rss(
    "cisco-talos",
    "Cisco Talos",
    "https://blog.talosintelligence.com/rss/",
    Tier.OFFICIAL,
    30,
    max_bytes=4 * MB,  # full text in feed, 1.1 MB on 2026-11-26
)
UNIT_42 = _rss("unit42", "Unit 42", "https://unit42.paloaltonetworks.com/feed/", Tier.OFFICIAL, 30)
GOOGLE_THREAT_INTEL = _rss(
    "google-threat-intelligence",
    "Google Threat Intelligence",
    "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v",
    Tier.OFFICIAL,
    60,
    max_bytes=6 * MB,  # full articles in feed, up to 90 KB each across 20 items
)

CISA_KEV = Source(
    id="cisa-kev",
    name="CISA Known Exploited Vulnerabilities",
    endpoint="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    format="cisa-kev",
    tier=Tier.OFFICIAL,
    interval_seconds=60 * MIN,
    max_bytes=8 * MB,  # the whole catalog, 1.9 MB on 2026-11-26
    backfill_days=30,
)

RANSOMWARE_LIVE = Source(
    id="ransomware-live",
    name="Ransomware.live",
    endpoint="https://www.ransomware.live/rss.xml",
    format="ransomware-live",
    tier=Tier.ATTACKER_CLAIM,
    interval_seconds=30 * MIN,
    crawl_delay_seconds=5,
    backfill_days=30,
)

CISA_ADVISORIES = _rss(
    "cisa-advisories",
    "CISA",
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    Tier.OFFICIAL,
    30,
    backfill_days=30,
)
MSRC_UPDATE_GUIDE = Source(
    id="msrc-update-guide",
    name="Microsoft Security Response Center",
    endpoint="https://api.msrc.microsoft.com/update-guide/rss",
    format="msrc",
    tier=Tier.OFFICIAL,
    interval_seconds=60 * MIN,
    max_bytes=16 * MB,  # about 5,800 items, 3.3 MB on 2026-11-26
    backfill_days=30,
)

REGISTRY: tuple[Source, ...] = (
    THE_RECORD,
    BLEEPINGCOMPUTER,
    SECURITYWEEK,
    THE_HACKER_NEWS,
    DARK_READING,
    SECURITY_AFFAIRS,
    KREBS,
    CISCO_TALOS,
    UNIT_42,
    GOOGLE_THREAT_INTEL,
    CISA_ADVISORIES,
    RANSOMWARE_LIVE,
    CISA_KEV,
    MSRC_UPDATE_GUIDE,
)

# Endpoints the worker queries for detail about a registry source's entries; never polled on
# their own. Their hosts are allowed deliberately, alongside the registry's.
MSRC_SUG = Source(
    id="msrc-sug",
    name="MSRC Security Update Guide API",
    endpoint="https://api.msrc.microsoft.com/sug/v2.0/en-US/vulnerability",
    format="msrc-sug",
    tier=Tier.OFFICIAL,
    interval_seconds=60 * MIN,
    max_bytes=2 * MB,  # about 3.4 KB per CVE; at most msrc.BATCH CVEs per request
)
LOOKUPS: tuple[Source, ...] = (MSRC_SUG,)


def allowed_hosts(sources: tuple[Source, ...] = REGISTRY + LOOKUPS) -> frozenset[str]:
    """The only hosts the fetcher may contact: the registry's and lookup endpoints' hosts."""
    return frozenset(s.host for s in sources)


def by_id(source_id: str) -> Source:
    for source in REGISTRY:
        if source.id == source_id:
            return source
    raise KeyError(source_id)
