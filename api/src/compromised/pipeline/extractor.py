"""Entity extractor: which organization or product a source record is about.

Order of evidence, first hit wins:
1. Structured fields a source adapter put in the record's metadata: ``victim`` (ransomware
   claims), or ``product`` / ``vendor`` (CISA KEV, MSRC). Adapters are #4; these are the keys
   they should fill.
2. The Ransomware.live headline template "<group> has just published a new victim : <victim>".
3. The curated alias dictionary (data/catalog.json), matched against the headline.
4. A publisher's own entity tag (feed <category>) that appears verbatim in the headline.
5. A headline that opens with "<Name> says / confirms / discloses / warns ...".
Otherwise the organization is unknown (None). Threat actors and reporters are never returned.
"""

import re
from dataclasses import dataclass

from compromised import catalog
from compromised.pipeline import classifier
from compromised.records import SourceRecord

CLAIM_TITLE = re.compile(r"^\S+ (?P<group>.+?) has just published a new victim : (?P<victim>.+)$")
SPEAKER = re.compile(
    r"^(?P<name>[A-Z0-9][\w&.'’-]*(?: [A-Z0-9][\w&.'’-]*){0,3})"
    r" (?:says|confirms|discloses|warns|admits|reports|notifies|investigates)\b"
)
# Feed tags that name a topic, not an organization.
TOPIC_TAGS = frozenset(
    t.casefold()
    for t in ("Security", "Hacking", "News", "Breaking News", "AI", "Cybercrime", "Cyber Crime")
)


@dataclass(frozen=True)
class Affected:
    name: str
    key: str | None = None  # catalog key, when the organization is in the dictionary
    logo: str | None = None
    people_use: bool = False


def extract(record: SourceRecord) -> Affected | None:
    cat = catalog.load()
    metadata = record.metadata or {}

    victim = _text(metadata.get("victim"))
    if victim:
        return _named(victim, cat)
    for field in ("product", "vendor"):
        value = _text(metadata.get(field))
        if value:
            # Structured product names are longer than aliases ("Juniper Session Smart
            # Conductor and Session Smart Router"), so look for an alias inside them.
            entry = cat.by_name(value) or cat.first_in(value)
            return _from_entry(entry) if entry else Affected(name=value)

    claim = CLAIM_TITLE.match(record.headline)
    if claim:
        return _named(claim["victim"].strip(), cat)

    found = cat.first_in(record.headline)
    if found:
        return _from_entry(found)

    tag = _tag_in_headline(record.headline, metadata.get("categories", []), cat)
    if tag:
        return _named(tag, cat)

    speaker = SPEAKER.match(record.headline)
    if speaker and not cat.is_not_organization(speaker["name"]):
        return _named(speaker["name"], cat)
    return None


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _named(name: str, cat: catalog.Catalog) -> Affected:
    """A name taken as a whole; it maps to a dictionary entry only on an exact alias."""
    entry = cat.by_name(name)
    return _from_entry(entry) if entry else Affected(name=name)


def _from_entry(entry: catalog.Organization) -> Affected:
    return Affected(name=entry.name, key=entry.key, logo=entry.logo, people_use=entry.people_use)


def _tag_in_headline(headline: str, tags, cat: catalog.Catalog) -> str | None:
    candidates = []
    for tag in tags:
        tag = str(tag).strip()
        if (
            len(tag) < 2
            or not (tag[0].isupper() or tag[0].isdigit())
            or tag.casefold() in TOPIC_TAGS
            or cat.is_not_organization(tag)
            or any(p.search(tag) for _, p in classifier.CATEGORY_RULES)
        ):
            continue
        match = re.search(rf"(?<!\w){re.escape(tag)}(?!\w)", headline)
        if match:
            candidates.append((match.start(), -len(tag), tag))
    return min(candidates)[2] if candidates else None
