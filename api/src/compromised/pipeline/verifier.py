"""Verifier and scorer: an event's verification status, its reader-facing label and its 0-100
confidence score, from its source records and the registry's tiers and weights only. Never from
the model (pipeline.enricher), and never from what a record claims about itself, with one
exception: the "disputed" guard.

Rules (docs/wiki/trust-labels-and-score.md):
- Status is the strongest tier among the event's sources: official -> confirmed, press ->
  reported, attacker claim only -> claimed. So a ransomware claim is upgraded only when a press
  or official source joins its event.
- Independent outlets are distinct publishers: two records from one source count once.
- The score's anchors, for sources at their tier's default weight (sources.TIER_WEIGHT), are the
  constants below. The "How we score" page is generated from them.

The label says who confirmed what, so that it stays true for every category: a vendor confirms
only what concerns its own organization or products ("the company"); a government agency or a
vendor's research unit writing about anyone else is not the company; and an advisory about a
flaw confirms the flaw, not a breach ("Flaw confirmed by ...").
"""

import re
from dataclasses import dataclass

from compromised import catalog
from compromised.pipeline.classifier import VULNERABILITY_CATEGORIES, classify
from compromised.pipeline.extractor import extract
from compromised.records import SourceRecord
from compromised.sources import TIER_WEIGHT, Tier

# --- the formula --------------------------------------------------------------------------------
PER_EXTRA_OUTLET = 10  # each additional independent news outlet, at the press default weight
PRESS_CAP = 80  # the most news coverage alone can reach
OFFICIAL_AND_PRESS = 100  # official confirmation plus at least one news outlet
DISPUTED = 10  # disputed or retracted, whatever the sources

STATUS_OF_TIER = {
    Tier.OFFICIAL: "confirmed",
    Tier.PRESS: "reported",
    Tier.ATTACKER_CLAIM: "claimed",
}
TIER_ORDER = (Tier.OFFICIAL, Tier.PRESS, Tier.ATTACKER_CLAIM)  # strongest first

# Every status, strongest first, with a short reader-facing name for the search filter (an
# event's own label says more: who confirmed, how many outlets reported).
STATUS_NAMES = {
    "confirmed": "Confirmed",
    "reported": "Reported",
    "investigating": "Under investigation",
    "claimed": "Claimed by attackers",
    "disputed": "Disputed",
}

# Who confirmed, strongest first, and how the label names them.
CONFIRMERS = {
    "company": "the company",
    "government": "a government agency",
    "researchers": "security researchers",
}


# --- the "disputed" guard -----------------------------------------------------------------------
# Explicit retraction or denial wording, matched only in the headline of a press or official
# record published after the event's earliest record. Kept narrow on purpose: a missed dispute
# leaves the tier's label, a false one would wrongly tell readers a real incident is in doubt.
_INCIDENT = r"(?:breach|hack|hacked|hacking|attack|cyberattack|claims?|compromise|ransomware|leak|intrusion|incident)"
DISPUTE_PATTERNS = (
    # "X denies breach", "X disputes ransomware gang's claims", within five words
    re.compile(
        rf"\b(?:denies|disputes|refutes)\b(?:\W+\w+){{0,5}}?\W+{_INCIDENT}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bretract(?:s|ed|ion)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:claims?|reports?)\b(?:\W+\w+){0,2}?\W+(?:is|was|are|were)\s+(?:a\s+)?"
        r"(?:false|fake|hoax|fabricated)\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\bno evidence of (?:a |an |any )?{_INCIDENT}\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class RegisteredSource:
    """What the verifier needs to know about a source (the registry mirror in storage)."""

    name: str
    tier: Tier
    weight: int
    government: bool = False
    organization: str | None = None  # catalog key of the vendor an official source speaks for


@dataclass(frozen=True)
class Assessment:
    status: str
    label: str
    score: int
    sources: tuple[str, ...]  # names of the publishers the score counted, earliest first


def assess(records: list[SourceRecord], registry: dict[str, RegisteredSource]) -> Assessment:
    """Assess an event from its records, earliest first."""
    outlets = _independent(records, registry)  # source id -> source, first appearance order
    by_tier = {t: [s for s in outlets.values() if s.tier == t] for t in Tier}
    strongest = next(t for t in TIER_ORDER if by_tier[t])
    press = by_tier[Tier.PRESS]
    order = list(outlets.values())
    if _disputed(records, registry):
        return Assessment(
            status="disputed",
            label="Disputed",
            score=DISPUTED,
            sources=tuple(s.name for s in order),
        )
    if strongest == Tier.OFFICIAL:
        official = by_tier[Tier.OFFICIAL]
        counted = official + press
        score = OFFICIAL_AND_PRESS if press else max(s.weight for s in official)
        label = _confirmed_label(records, registry)
    elif strongest == Tier.PRESS:
        counted = press
        score = _press_score(press)
        label = f"Reported by {len(press)} news outlet{'' if len(press) == 1 else 's'}"
    else:
        counted = by_tier[Tier.ATTACKER_CLAIM]
        score = max(s.weight for s in counted)
        label = "Claimed by attackers, not confirmed"
    return Assessment(
        status=STATUS_OF_TIER[strongest],
        label=label,
        score=_clamp(score),
        sources=tuple(s.name for s in sorted(counted, key=order.index)),
    )


def disputes(headline: str) -> bool:
    """Whether a headline explicitly retracts or denies the incident (see DISPUTE_PATTERNS)."""
    return any(p.search(headline) for p in DISPUTE_PATTERNS)


def _disputed(records, registry) -> bool:
    first = records[0].published_at
    return any(
        r.published_at > first
        and registry[r.source_id].tier != Tier.ATTACKER_CLAIM
        and disputes(r.headline)
        for r in records
    )


def _independent(records, registry) -> dict[str, RegisteredSource]:
    """One entry per publisher: two records from one source count once."""
    out: dict[str, RegisteredSource] = {}
    for record in records:
        out.setdefault(record.source_id, registry[record.source_id])
    return out


def _press_score(press: list[RegisteredSource]) -> float:
    """The heaviest outlet sets the base; each other adds PER_EXTRA_OUTLET scaled by its weight
    relative to the press default; capped at PRESS_CAP."""
    heaviest, *others = sorted(press, key=lambda s: -s.weight)
    extra = sum(PER_EXTRA_OUTLET * s.weight / TIER_WEIGHT[Tier.PRESS] for s in others)
    return min(PRESS_CAP, heaviest.weight + extra)


def _clamp(score: float) -> int:
    return max(0, min(100, int(score + 0.5)))


def _confirmed_label(records, registry) -> str:
    """Name the strongest confirmer among the official records; "Flaw confirmed" when that
    record (by the rules, never the model) is about a flaw."""
    found = []
    for record in records:
        source = registry[record.source_id]
        if source.tier == Tier.OFFICIAL:
            found.append((list(CONFIRMERS).index(_confirmer(record, source)), record))
    rank, record = min(found, key=lambda f: f[0])
    who = CONFIRMERS[list(CONFIRMERS)[rank]]
    if classify(record).category in VULNERABILITY_CATEGORIES:
        return f"Flaw confirmed by {who}"
    return f"Confirmed by {who}"


def _confirmer(record: SourceRecord, source: RegisteredSource) -> str:
    if source.government:
        return "government"
    if source.organization and _about_organization(record, source.organization):
        return "company"
    return "researchers"


def _about_organization(record: SourceRecord, key: str) -> bool:
    """Whether the rules find the record about this organization or one of its products."""
    affected = extract(record)
    if affected is None or affected.key is None:
        return False
    entry = catalog.load().by_key(affected.key)
    return affected.key == key or (entry is not None and entry.vendor == key)
