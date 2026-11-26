"""The MSRC Update Guide feed, and Microsoft's own severity for it from the MSRC SUG API.

The feed (about 5,800 items over two months) has no severity or exploited field and repeats a
guid for each revision of a CVE. So:

1. ``parse`` reads the feed, one item per CVE (its newest revision), titled by a fixed template.
2. ``cves_to_rate`` picks the CVEs whose product is on the curated "people use" list and that
   were revised since the last check: only those are looked up.
3. ``lookup`` asks the SUG API for their ``severity`` and ``exploited`` fields, in batches,
   through the fetcher (so the same allow-list, timeouts and size cap apply).
4. ``ingest`` (pipeline.ingest) keeps an entry only when its product is listed and Microsoft
   rates it Critical or reports it exploited.

Decision recorded in docs/wiki/feed-scope-and-sources.md, "Findings from the feed capture".
"""

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime
from urllib.parse import quote

import httpx

from compromised import catalog
from compromised.pipeline.fetcher import FetchPolicy, fetch
from compromised.pipeline.parsers import ParseError, parse_rss
from compromised.records import ParsedItem
from compromised.sources import MSRC_SUG

TITLE = "Microsoft Update Guide: {name} ({cve})"
# "CVE-… <name>", or for Edge pickups of Chrome flaws "Chromium CVE-… …" / "Chromium: CVE-… …".
FEED_TITLE = re.compile(r"^(?P<chromium>Chromium:? )?(?P<cve>CVE-\d{4}-\d{4,})\s+(?P<name>.+)$")
IMPACT = re.compile(
    r"\s+(?:Remote Code Execution|Elevation of Privilege|Security Feature Bypass"
    r"|Information Disclosure|Denial of Service|Spoofing|Tampering)\s+Vulnerability$"
)
EDGE = "Microsoft Edge (Chromium-based)"
CVE_ID = re.compile(r"^CVE-\d{4}-\d{4,}$")
BATCH = 15  # CVEs per SUG request, to keep the URL short


@dataclass(frozen=True)
class Rating:
    """Microsoft's own rating of a CVE, from the SUG API."""

    severity: str  # "Critical", "Important", ... or "" when not rated
    exploited: bool
    product: str  # the SUG ``tag``, e.g. "Microsoft Office Visio"

    @property
    def keep(self) -> bool:
        return self.exploited or self.severity.casefold() == "critical"


def parse(body: bytes) -> list[ParsedItem]:
    """One item per CVE: its newest revision. ADV advisories and unrecognised titles are skipped."""
    newest: dict[str, ParsedItem] = {}
    for item in parse_rss(body):
        match = FEED_TITLE.match(" ".join(item.title.split()))
        if not match:
            continue
        cve, name = match["cve"], match["name"]
        product = EDGE if match["chromium"] else IMPACT.sub("", name)
        parsed = ParsedItem(
            guid=cve,
            link=item.link,
            title=TITLE.format(name=name, cve=cve),
            summary_html="",  # the feed's description is a revision note, not a summary
            published=item.published,
            metadata={"cve": cve, "vendor": "Microsoft", "product": product},
        )
        current = newest.get(cve)
        if current is None or _later(parsed, current):
            newest[cve] = parsed
    return list(newest.values())


def listed(item: ParsedItem) -> bool:
    """Whether the item's product is on the curated list of products people use."""
    cat = catalog.load()
    product = item.metadata.get("product", "")
    entry = cat.by_name(product) or cat.first_in(product)
    return bool(entry and entry.people_use)


def cves_to_rate(items: list[ParsedItem], *, since: datetime) -> list[str]:
    """CVEs of listed products revised at or after ``since``, sorted."""
    return sorted(
        i.metadata["cve"]
        for i in items
        if listed(i) and i.published is not None and i.published >= since
    )


def apply_ratings(items: list[ParsedItem], ratings: dict[str, Rating]) -> list[ParsedItem]:
    """Keep listed items that Microsoft rates Critical or reports exploited, with the rating."""
    kept = []
    for item in items:
        rating = ratings.get(item.metadata.get("cve", ""))
        if rating is None or not rating.keep or not listed(item):
            continue
        metadata = dict(item.metadata, exploited=rating.exploited)
        if rating.severity:
            metadata["severity"] = rating.severity
        if rating.product and item.metadata.get("product") != EDGE:
            metadata["product"] = rating.product
        kept.append(replace(item, metadata=metadata))
    return kept


def parse_ratings(body: bytes) -> dict[str, Rating]:
    """CVE -> rating from a SUG API response."""
    try:
        values = json.loads(body)["value"]
    except (ValueError, TypeError, KeyError) as exc:
        raise ParseError(f"not an MSRC SUG answer: {type(exc).__name__}") from None
    if not isinstance(values, list):
        raise ParseError("not an MSRC SUG answer: value is not a list")
    ratings = {}
    for v in values:
        if not isinstance(v, dict) or not isinstance(v.get("cveNumber"), str):
            continue
        ratings[v["cveNumber"].strip()] = Rating(
            severity=_str(v.get("severity")),
            exploited=_str(v.get("exploited")).casefold() == "yes",
            product=_str(v.get("tag")),
        )
    return ratings


def sug_url(cves: list[str]) -> str:
    query = " or ".join(f"cveNumber eq '{cve}'" for cve in cves)
    return f"{MSRC_SUG.endpoint}?$filter={quote(query, safe='')}"


async def lookup(
    client: httpx.AsyncClient, policy: FetchPolicy, cves: list[str]
) -> dict[str, Rating]:
    """Ratings for ``cves`` from the SUG API, in batches. A failed request raises FetchError."""
    ratings: dict[str, Rating] = {}
    for start in range(0, len(cves), BATCH):
        batch = [c for c in cves[start : start + BATCH] if CVE_ID.match(c)]
        if not batch:
            continue
        result = await fetch(client, replace(MSRC_SUG, endpoint=sug_url(batch)), policy)
        ratings.update(parse_ratings(result.body or b'{"value": []}'))
    return ratings


def _later(a: ParsedItem, b: ParsedItem) -> bool:
    return a.published is not None and (b.published is None or a.published > b.published)


def _str(value) -> str:
    return value.strip() if isinstance(value, str) else ""
