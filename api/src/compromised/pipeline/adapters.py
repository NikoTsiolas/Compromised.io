"""Adapters for the structured sources: raw response bytes -> parsed items.

Structured entries have no headline of their own, or one written by an attacker, so each gets
a fixed factual title template filled only with the source's own field values (no generated
prose). Fields the rest of the pipeline reads go into metadata under the keys the extractor and
classifier expect: ``victim``, ``vendor``, ``product``, ``exploited``, ``severity``.
See docs/wiki/feed-scope-and-sources.md for the field notes behind each adapter.
"""

import html
import json
import re
from datetime import UTC, date, datetime
from urllib.parse import urlsplit

from compromised.pipeline.parsers import ParseError, parse_rss
from compromised.records import ParsedItem

KEV_TITLE = "{name} ({cve}) added to CISA's Known Exploited Vulnerabilities catalog"
KEV_LINK = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search_api_fulltext={cve}"


def parse_kev(body: bytes) -> list[ParsedItem]:
    """The CISA KEV catalog (JSON). One item per vulnerability, dated by ``dateAdded``."""
    try:
        catalog = json.loads(body)
        entries = catalog["vulnerabilities"]
    except (ValueError, TypeError, KeyError) as exc:
        raise ParseError(f"not a KEV catalog: {type(exc).__name__}") from None
    if not isinstance(entries, list):
        raise ParseError("not a KEV catalog: vulnerabilities is not a list")
    items = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cve = _str(entry.get("cveID"))
        name = _str(entry.get("vulnerabilityName"))
        added = _date(entry.get("dateAdded"))
        if not (cve and name and added):
            continue
        items.append(
            ParsedItem(
                guid=cve,
                link=KEV_LINK.format(cve=cve),
                title=KEV_TITLE.format(name=name, cve=cve),
                summary_html=_str(entry.get("shortDescription")),
                published=added,
                metadata=_present(
                    cve=cve,
                    vendor=_str(entry.get("vendorProject")),
                    product=_str(entry.get("product")),
                    date_added=added.date().isoformat(),
                    due_date=_str(entry.get("dueDate")),
                    required_action=_str(entry.get("requiredAction")),
                    known_ransomware_use=_str(entry.get("knownRansomwareCampaignUse")),
                    exploited=True,
                ),
            )
        )
    return items


CLAIM_TITLE = "{group} claims {victim} as a ransomware victim"
# "<emoji> <group> has just published a new victim : <victim>"; the emoji is a ZWJ sequence.
RANSOMWARE_LIVE_TITLE = re.compile(
    r"^\S+ (?P<group>.+?) has just published a new victim : (?P<victim>.+)$"
)
RANSOMWARE_LIVE_HOSTS = frozenset({"www.ransomware.live", "ransomware.live"})
GROUP_PATH = re.compile(r"^/group/(?P<slug>[^/?#]+)")


def parse_ransomware_live(body: bytes) -> list[ParsedItem]:
    """Ransomware.live RSS: attacker claims relayed by a third party.

    Only the victim, group, country and claim date are kept. The description is attacker-supplied
    text (contact addresses, messenger IDs, victim URLs) and is never kept, nor is the
    enclosure. The only link kept is one on Ransomware.live itself (the item link, else the
    group page in the guid); an item with neither is dropped, so no leak-site or .onion link
    can be stored.
    """
    items = []
    for item in parse_rss(body):
        match = RANSOMWARE_LIVE_TITLE.match(" ".join(html.unescape(item.title).split()))
        link = next((u for u in (item.link, item.guid) if _on_ransomware_live(u)), None)
        if not match or link is None:
            continue
        group, victim = match["group"].strip(), match["victim"].strip()
        slug = (
            GROUP_PATH.match(urlsplit(item.guid).path) if _on_ransomware_live(item.guid) else None
        )
        country = next(iter(item.metadata.get("categories", [])), "")
        items.append(
            ParsedItem(
                guid=item.guid if _on_ransomware_live(item.guid) else link,
                link=link,
                title=CLAIM_TITLE.format(group=group, victim=victim),
                summary_html="",
                published=item.published,
                metadata=_present(
                    victim=victim,
                    group=group,
                    group_key=slug["slug"].casefold() if slug else group.casefold(),
                    country=country if country != "N/A" else "",
                    attacker_claim=True,
                ),
            )
        )
    return items


def _on_ransomware_live(url: str | None) -> bool:
    try:
        parts = urlsplit((url or "").strip())
    except ValueError:
        return False
    return parts.scheme == "https" and (parts.hostname or "") in RANSOMWARE_LIVE_HOSTS


def _str(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _date(value) -> datetime | None:
    try:
        day = date.fromisoformat(_str(value))
    except ValueError:
        return None
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _present(**fields) -> dict:
    """Drop empty values, so a missing field is absent rather than blank."""
    return {k: v for k, v in fields.items() if v not in ("", None)}
