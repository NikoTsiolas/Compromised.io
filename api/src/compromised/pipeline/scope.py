"""Feed scope: which tabs an event appears in.

Rules (docs/wiki/feed-scope-and-sources.md):
- Commentary, product announcements and promotional posts appear in no tab.
- Threat research, malware analysis and espionage reports appear only under Research.
- Every other tab needs a named affected organization or product.
- A vulnerability appears only when its product is on the "people use" list and it is critical
  or exploited; it then shows in All and Update now, and in Under attack when exploited.
- An attacker claim with no other coverage appears only under Ransomware.

``refresh_event`` derives an event's facts from all of its source records and stores them with
its tabs. Call it whenever an event gains or loses a record (#5) or its status changes (#7). The
LLM enricher (#8) may override category or organization: build ``EventFacts`` with its values
and store them with ``storage.save_classification(conn, event_id, facts, tabs_for(facts))``.
Trending is ranked by a query (#10), so it is never stored as a tab.
"""

from dataclasses import dataclass

import psycopg

from compromised import storage
from compromised.pipeline.classifier import VULNERABILITY_CATEGORIES, classify
from compromised.pipeline.extractor import extract

# Tab ids double as URL slugs. Labels are the reader-facing names.
TABS: dict[str, str] = {
    "all": "All",
    "breaches": "Breaches",
    "ransomware": "Ransomware",
    "under-attack": "Under attack",
    "update-now": "Update now",
    "research": "Research",
    "trending": "Trending",
}
RESEARCH_CATEGORIES = frozenset({"research", "malware", "espionage"})
BREACH_CATEGORIES = frozenset({"data_breach", "credential_leak"})


@dataclass(frozen=True)
class EventFacts:
    category: str
    commentary: bool
    organization: str | None  # None means unknown
    organization_key: str | None
    logo: str | None
    people_use: bool
    exploited: bool
    critical: bool
    claim_only: bool  # every source is an attacker-claim aggregator


def tabs_for(facts: EventFacts) -> frozenset[str]:
    if facts.commentary:
        return frozenset()
    if facts.category in RESEARCH_CATEGORIES:
        return frozenset({"research"})
    if facts.organization is None:
        return frozenset()
    if facts.category in VULNERABILITY_CATEGORIES:
        if not (facts.people_use and (facts.critical or facts.exploited)):
            return frozenset()
        return frozenset({"all", "update-now"} | ({"under-attack"} if facts.exploited else set()))
    if facts.claim_only:
        return frozenset({"ransomware"}) if facts.category == "ransomware" else frozenset()
    tabs = {"all"}
    if facts.category in BREACH_CATEGORIES:
        tabs.add("breaches")
    if facts.category == "ransomware":
        tabs.add("ransomware")
    return frozenset(tabs)


def facts_for(records) -> EventFacts:
    """Facts for an event from its source records, earliest first.

    The earliest record sets the category and commentary flag (it also gives the event its
    headline); the organization is the first one any record names; the vulnerability signals
    hold if any record carries them.
    """
    classified = [classify(r) for r in records]
    lead = classified[0]
    affected = next((a for a in map(extract, records) if a is not None), None)
    return EventFacts(
        category=lead.category,
        commentary=lead.commentary,
        organization=affected.name if affected else None,
        organization_key=affected.key if affected else None,
        logo=affected.logo if affected else None,
        people_use=affected.people_use if affected else False,
        exploited=any(c.exploited for c in classified),
        critical=any(c.critical for c in classified),
        claim_only=all(c.claim for c in classified),
    )


def refresh_event(conn: psycopg.Connection, event_id: int) -> EventFacts:
    facts = facts_for(storage.event_records(conn, event_id))
    storage.save_classification(conn, event_id, facts, tabs_for(facts))
    return facts


def refresh_all(conn: psycopg.Connection) -> int:
    """Re-derive every event's facts and tabs, e.g. after the rules or the dictionary change."""
    event_ids = storage.all_event_ids(conn)
    for event_id in event_ids:
        refresh_event(conn, event_id)
    return len(event_ids)
