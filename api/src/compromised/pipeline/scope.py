"""Feed scope: which tabs an event appears in.

Rules (docs/wiki/feed-scope-and-sources.md):
- Commentary, product announcements and promotional posts appear in no tab.
- Threat research, malware analysis and espionage reports appear only under Research.
- Every other tab needs a named affected organization or product.
- A vulnerability appears only when its product is on the "people use" list and it is critical
  or exploited; it then shows in All and Update now, and in Under attack when exploited.
- An attacker claim with no other coverage appears only under Ransomware.

``refresh_event`` derives an event's facts from all of its source records, lays the enricher's
stored output over them (#8: category and commentary flag; the organization only when the rules
found none) and stores them with its tabs and action line. Call it whenever an event gains or
loses a record (#5) or a record's metadata is revised; it also re-assesses the event's
verification status and score (#7, pipeline.verifier).
Trending is ranked by a query (#10), so it is never stored as a tab.
"""

from dataclasses import dataclass, replace

import psycopg

from compromised import catalog, storage
from compromised.pipeline import search_terms, verifier
from compromised.pipeline.actions import required_action_line
from compromised.pipeline.classifier import VULNERABILITY_CATEGORIES, classify
from compromised.pipeline.extractor import extract
from compromised.sources import Tier

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


def with_enrichment(facts: EventFacts, ai: dict | None) -> EventFacts:
    """Facts with the model's checked output laid over the rules' (see pipeline.enricher)."""
    if not ai:
        return facts
    facts = replace(facts, category=ai["category"], commentary=ai["commentary"])
    if facts.organization is None and ai["organization"]:
        entry = catalog.load().by_name(ai["organization"])
        facts = replace(
            facts,
            organization=entry.name if entry else ai["organization"],
            organization_key=entry.key if entry else None,
            logo=entry.logo if entry else None,
            people_use=entry.people_use if entry else False,
        )
    return facts


def action_line_for(records, facts: EventFacts, ai: dict | None) -> str | None:
    """A source's structured required action first; else the model's, if the input stated it.

    An attacker's own words are never turned into advice: claim-only events get none from the
    model.
    """
    stated = required_action_line(records)
    if stated:
        return stated
    if ai and ai["action_line"] and not facts.claim_only:
        return ai["action_line"]
    return None


def refresh_event(conn: psycopg.Connection, event_id: int) -> EventFacts:
    records = storage.event_records(conn, event_id)
    ai = storage.enrichment_of(conn, event_id)
    rules = facts_for(records)
    facts = with_enrichment(rules, ai)
    storage.save_classification(conn, event_id, facts, tabs_for(facts))
    storage.save_action_line(conn, event_id, action_line_for(records, facts, ai))
    save_search_terms(conn, event_id, records, facts)
    # Commentary (newsletters, podcasts, opinion) is not an incident: no label and no score.
    # Decided by the rules' commentary flag, never the model's, as trust never comes from it.
    assessment = None if rules.commentary else verifier.assess(records, _registry(conn, records))
    storage.save_trust(conn, event_id, assessment)
    return facts


def save_search_terms(conn: psycopg.Connection, event_id: int, records, facts: EventFacts) -> None:
    """Store the event's CVEs, threat actors and attack vector (pipeline.search_terms) and its
    full-text search document. Beyond the records' own words, the document names the catalog
    vendor of the affected product, so "Google" finds a Chrome flaw."""
    actors = search_terms.threat_actors(records)
    vector = search_terms.attack_vector(records)
    names = [*actors, vector or ""]
    entry = catalog.load().by_key(facts.organization_key) if facts.organization_key else None
    vendor = catalog.load().by_key(entry.vendor) if entry and entry.vendor else None
    if vendor:
        names.append(vendor.name)
    for record in records:
        for field in ("vendor", "product"):
            value = (record.metadata or {}).get(field)
            if isinstance(value, str):
                names.append(value)
    storage.save_search_terms(
        conn,
        event_id,
        cves=search_terms.cves(records),
        threat_actors=actors,
        attack_vector=vector,
        names=" ".join(names),
    )


def _registry(conn, records) -> dict[str, verifier.RegisteredSource]:
    rows = storage.registered_sources(conn, {r.source_id for r in records})
    return {
        source_id: verifier.RegisteredSource(
            name=r["name"],
            tier=Tier(r["tier"]),
            weight=r["weight"],
            government=r["government"],
            organization=r["organization"],
        )
        for source_id, r in rows.items()
    }


def refresh_all(conn: psycopg.Connection) -> int:
    """Re-derive every event's facts and tabs, e.g. after the rules or the dictionary change."""
    event_ids = storage.all_event_ids(conn)
    for event_id in event_ids:
        refresh_event(conn, event_id)
    return len(event_ids)
