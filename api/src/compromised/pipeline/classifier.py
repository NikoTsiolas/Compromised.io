"""Classifier: deterministic rules for one source record.

Assigns one of the thirteen categories from the brief, flags commentary (opinion, newsletters,
product announcements, promotional posts) and reads two vulnerability signals: whether the
flaw is being exploited and whether it is rated critical. Inputs are the record's headline,
excerpt and metadata, plus a prior for the source it came from.

This is the baseline and the fallback for the LLM enricher (#8), which may later override the
category; it never decides trust (#7).
"""

import re
from dataclasses import dataclass

from compromised import catalog
from compromised.records import SourceRecord

CATEGORIES: dict[str, str] = {
    "data_breach": "Data breach",
    "ransomware": "Ransomware",
    "zero_day": "Zero-day",
    "active_exploitation": "Active exploitation",
    "vulnerability": "Vulnerability",
    "supply_chain": "Supply chain attack",
    "malware": "Malware",
    "espionage": "Cyber espionage",
    "credential_leak": "Credential leak",
    "cloud_security": "Cloud security",
    "ai_security": "AI security",
    "research": "Security research",
    "other": "Other cyber incident",
}

# What kind of publisher a source is, keyed by source id (the registry id, which is also the
# name of its captured sample in tests/fixtures/real). Unlisted sources are "press".
#   claim:     relays attacker claims; every item is a ransomware claim
#   exploited: a catalog of exploited flaws
#   advisory:  vendor or government advisories, mostly vulnerabilities
#   research:  vendor threat-research blogs
SOURCE_PRIORS: dict[str, str] = {
    "ransomware-live": "claim",
    "cisa-kev": "exploited",
    "cisa-advisories": "advisory",
    "msrc-update-guide": "advisory",
    "cisco-talos": "research",
    "unit42": "research",
    "google-threat-intelligence": "research",
}


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# Arrests, charges and seizures are news about crime, not a category of attack.
LAW_ENFORCEMENT = _rx(
    r"\b(?:indicted|arrested|charged|sentenced|extradited|pleads? guilty|convicted|seized"
    r"|takedown|dismantled)\b"
)

# Checked in this order; the first category whose phrases appear wins. The headline is tried
# first and the excerpt only when the headline names no category.
CATEGORY_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ransomware", _rx(r"\bransomware\b|\bdata extortion\b|\bextortion gang")),
    ("zero_day", _rx(r"\bzero[- ]days?\b|\b0[- ]days?\b")),
    (
        "active_exploitation",
        _rx(
            r"\bexploited\b|\bexploiting\b|\bunder (?:active )?exploitation\b"
            r"|\bactively (?:exploited|attacked)\b|\bin the wild\b"
        ),
    ),
    (
        "supply_chain",
        _rx(
            r"\bsupply[- ]chain\b|\bmalicious (?:\w+ )?(?:packages?|extensions?|libraries)\b"
            r"|\bpoisoned (?:packages?|updates?)\b|\btrojani[sz]ed (?:updates?|installers?)\b"
        ),
    ),
    (
        "credential_leak",
        _rx(
            r"\b(?:credentials?|passwords?|logins?) (?:leaked|exposed|dumped)\b"
            r"|\bleaked (?:credentials|passwords|logins)\b|\bcombolists?\b"
            r"|\bcredential (?:leaks?|dumps?)\b|\binfostealer logs\b"
        ),
    ),
    (
        "data_breach",
        _rx(
            r"\bbreach(?:ed|es)?\b|\bhacked\b|\bstolen\b|\bstole\b|\bleaked\b"
            r"|\bdata (?:leak|theft|exposure)\b|\bexposes? (?:\w+ )?(?:data|records|details)\b"
            r"|\bhackers accessed\b|\bunauthori[sz]ed access\b"
        ),
    ),
    (
        "espionage",
        _rx(
            r"\bespionage\b|\bcyber ?spies\b|\bstate[- ](?:backed|sponsored)\b|\bnation[- ]state\b"
        ),
    ),
    (
        "malware",
        _rx(
            r"\bmalware\b|\binfostealers?\b|\bstealer\b|\btrojans?\b|\bbotnets?\b|\bbackdoors?\b"
            r"|\bspyware\b|\brootkits?\b|\bwipers?\b"
        ),
    ),
    (
        "ai_security",
        _rx(r"\bprompt injection\b|\bAI (?:agents?|models?|assistants?|chatbots?)\b|\bLLMs?\b"),
    ),
    (
        "cloud_security",
        _rx(r"\bcloud (?:accounts?|tenants?|storage|misconfiguration)\b|\bS3 buckets?\b"),
    ),
    (
        "vulnerability",
        _rx(
            r"\bvulnerabilit(?:y|ies)\b|\bflaws?\b|\bCVE-\d{4}-\d{4,}\b|\bbugs?\b"
            r"|\bsecurity (?:updates?|patch(?:es)?)\b|\bremote code execution\b"
        ),
    ),
)

VULNERABILITY_CATEGORIES = frozenset({"zero_day", "active_exploitation", "vulnerability"})

EXPLOITED = _rx(
    r"\bexploited\b|\bexploiting\b|\bunder (?:active )?exploitation\b|\bactively attacked\b"
    r"|\bin the wild\b|\bzero[- ]days?\b|\b0[- ]days?\b"
)
CRITICAL = _rx(r"\bcritical\b(?! infrastructure)|\bCVSS(?: score)?:? (?:9\.\d|10(?:\.0)?)\b")

# Words that make a headline about something that happened. A press headline with none of them
# is commentary, analysis of the industry, policy news or an announcement.
INCIDENT_SIGNALS = _rx(
    r"\bhack(?:s|ed|ers?|ing)?\b|\bbreach(?:ed|es)?\b|\battack(?:s|ed|ers?)?\b|\bcyberattacks?\b"
    r"|\bstol(?:en|e)\b|\bsteal(?:s|ing)?\b|\bleak(?:s|ed)?\b|\bexpos(?:ed|es)\b|\bransomware\b"
    r"|\bmalware\b|\bexploit(?:s|ed|ing|ation)?\b|\bvulnerab\w*|\bflaws?\b|\bzero[- ]days?\b"
    r"|\bCVE-\d|\bbugs?\b|\bpatch(?:es|ed)?\b|\bcompromis\w*|\bespionage\b|\bspy(?:ing)?\b"
    r"|\bphishing\b|\bscams?\b|\bfraud\b|\bbackdoor\w*|\bbotnets?\b|\bDDoS\b|\bintrusions?\b"
    r"|\binfostealers?\b|\btrojan\w*|\bextortion\b|\bwipers?\b|\bincident\b|\bpoisoned\b"
    r"|\bindicted\b|\barrested\b|\bcharged\b|\bsentenced\b|\bseized\b|\bstalkerware\b"
)
PROMOTIONAL = re.compile(
    r"\b(?:[Ww]ebinars?|[Ss]ponsored|[Ww]hite ?paper|e-?[Bb]ook|[Ff]ree trial|[Rr]egister now"
    r"|[Pp]artner [Cc]ontent)\b"
    # A vendor speaking for itself: "At Push Security, we measure..."
    r"|\b[Aa]t [A-Z][\w.-]*(?: [A-Z][\w.-]*){0,3}, we\b"
)
BUSINESS_NEWS = _rx(r"\braises \$|\bfunding round\b|\bacquires\b|\bacquisition of\b|\bto acquire\b")
# Feed categories publishers use for columns, newsletters and profiles.
COMMENTARY_TAGS = frozenset(
    t.casefold()
    for t in (
        "Threat Source newsletter",
        "Humans of Talos",
        "Insights",
        "Podcast",
        "Podcasts",
        "Webinar",
        "Webinars",
        "Opinion",
        "Commentary",
        "Sponsored",
        "Partner Content",
        "Interview",
        "Interviews",
        "Newsletter",
        "Product News",
        "Press Release",
        "Press Releases",
        "Events",
    )
)


@dataclass(frozen=True)
class Classification:
    category: str
    commentary: bool
    exploited: bool
    critical: bool
    claim: bool  # the record is an attacker's claim relayed by an aggregator


def source_prior(source_id: str) -> str:
    return SOURCE_PRIORS.get(source_id, "press")


def classify(record: SourceRecord) -> Classification:
    prior = source_prior(record.source_id)
    headline, excerpt = record.headline, record.excerpt
    text = f"{headline}\n{excerpt}"
    metadata = record.metadata or {}

    category = _category(headline, excerpt, prior)
    exploited = (
        prior == "exploited"
        or metadata.get("exploited") is True
        or bool(EXPLOITED.search(text))
        or category in {"zero_day", "active_exploitation"}
    )
    critical = str(metadata.get("severity", "")).casefold() == "critical" or bool(
        CRITICAL.search(text)
    )
    return Classification(
        category=category,
        commentary=_commentary(headline, excerpt, metadata, prior),
        exploited=exploited,
        critical=critical,
        claim=prior == "claim",
    )


def _category(headline: str, excerpt: str, prior: str) -> str:
    if prior == "claim":
        return "ransomware"
    if prior == "exploited":
        return "active_exploitation"
    found = _rule_category(headline) or _rule_category(excerpt)
    if prior == "research":
        # Vendor threat research is filed under Research whatever it covers.
        return found if found in {"espionage", "malware"} else "research"
    if found:
        return found
    if prior == "advisory":
        return "vulnerability"
    return "other"


def _rule_category(text: str) -> str | None:
    if LAW_ENFORCEMENT.search(text):
        return "other"
    for category, pattern in CATEGORY_RULES:
        if pattern.search(text):
            return category
    if any(a.state_linked for a in catalog.load().actors_in(text)):
        return "espionage"
    return None


def _commentary(headline: str, excerpt: str, metadata: dict, prior: str) -> bool:
    if prior in {"claim", "exploited"}:
        return False
    tags = {str(t).casefold() for t in metadata.get("categories", [])}
    if tags & COMMENTARY_TAGS:
        return True
    if PROMOTIONAL.search(f"{headline}\n{excerpt}") or BUSINESS_NEWS.search(headline):
        return True
    if prior == "press":
        return not (INCIDENT_SIGNALS.search(headline) or catalog.load().actors_in(headline))
    return False
