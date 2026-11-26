"""Search terms (#10): the threat actors, attack vector and CVEs an event's source records name.

Deterministic, from the records' own words only; the model is never asked.

Threat actors, in order of first appearance, without repeats:
1. A claim source's structured ``group`` field (Ransomware.live).
2. Names in the catalog's threat-actor list (data/catalog.json), as whole words in a headline or
   excerpt.
3. A name a source introduces explicitly: 'a threat group called "Volant Manticore"', 'the
   ransomware gang dubbed Foo'. Quoted, or a run of capitalised words.

Attack vector: the first rule in ``ATTACK_VECTORS`` that matches any headline or excerpt. The
rules run from the most specific weakness to the most general, so a KEV entry for an "OS command
injection" that "could allow a remote attacker to execute arbitrary commands" is a command
injection, not remote code execution. None when no rule matches: the page then says the attack
vector is not identified.
"""

import re

from compromised import catalog
from compromised.records import SourceRecord


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# (label, rule): reader-facing label first. Ordered most specific first; the first match wins.
ATTACK_VECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("SQL injection", _rx(r"\bSQL injection\b|\bSQLi\b")),
    ("Command injection", _rx(r"\b(?:OS )?command injection\b")),
    ("Path traversal", _rx(r"\b(?:path|directory) traversal\b")),
    (
        "Authentication bypass",
        _rx(
            r"\bauth(?:entication)? bypass\b|\bbypass(?:es|ing)? (?:the )?authentication\b"
            r"|\b(?:improper|missing|broken) authentication\b"
        ),
    ),
    (
        "Memory corruption",
        _rx(
            r"\buse[- ]after[- ]free\b|\b(?:buffer|heap|stack|integer) overflow\b"
            r"|\bout[- ]of[- ]bounds (?:read|write)\b|\bmemory corruption\b|\btype confusion\b"
            r"|\bcorrupt (?:application )?memory\b"
        ),
    ),
    (
        "Remote code execution",
        _rx(
            r"\bremote code execution\b|\bRCE\b|\barbitrary code execution\b"
            r"|\bexecute (?:arbitrary |malicious )?code\b"
        ),
    ),
    (
        "Supply chain",
        _rx(
            r"\bsupply[- ]chain\b|\bmalicious (?:npm|PyPI|NuGet|RubyGems|VS Code|open[- ]source)"
            r"\b|\bmalicious (?:\w+ )?packages?\b|\bpoisoned (?:packages?|updates?)\b"
            r"|\btrojani[sz]ed\b"
        ),
    ),
    (
        "Third-party breach",
        _rx(r"\bthird[- ]party (?:breach|vendor|supplier|provider|service)"),
    ),
    ("Phishing", _rx(r"\b(?:spear[- ]?)?phish(?:ing|ed)?\b|\bsmishing\b")),
    (
        "Social engineering",
        _rx(
            r"\bsocial engineering\b|\bimpersonat(?:e|es|ed|ing|ion)\b|\bvishing\b"
            r"|\bfake (?:recruit\w*|job|support|help desk)\b|\bClickFix\b"
        ),
    ),
    (
        "Malicious ads",
        _rx(r"\bmalvertising\b|\bmalicious (?:ads|advertis\w+)\b|\bthrough \w+ ads\b"),
    ),
    (
        "Stolen credentials",
        _rx(
            r"\bstolen (?:credentials|passwords|logins?)\b|\bcredential stuffing\b"
            r"|\bpassword spraying\b|\bcompromised credentials\b"
        ),
    ),
    (
        "Compromised account",
        _rx(
            r"\baccounts? (?:was |were )?(?:hacked|compromised|hijacked|taken over)\b"
            r"|\b(?:hacked|compromised|hijacked) (?:\w+ ){0,2}accounts?\b"
        ),
    ),
    (
        "Misconfiguration",
        _rx(
            r"\bmisconfigur\w+\b|\b(?:exposed|unsecured|unprotected|open) (?:\w+ )?"
            r"(?:database|bucket|server|Elasticsearch)\b"
        ),
    ),
    ("Denial of service", _rx(r"\bDDoS\b|\bdenial[- ]of[- ]service\b")),
    ("Insider", _rx(r"\binsider\b|\brogue (?:employee|staff)\b")),
    ("Zero-day exploit", _rx(r"\bzero[- ]days?\b|\b0[- ]days?\b")),
    (
        "Exploited flaw",
        _rx(
            r"\bexploit\w*\b.{0,60}\b(?:vulnerabilit\w+|flaws?|bugs?|gap)\b"
            r"|\b(?:vulnerabilit\w+|flaws?|bugs?)\b.{0,60}\bexploit\w*"
        ),
    ),
)

# "a threat group called "Volant Manticore"", "the ransomware gang dubbed Foo Bar".
INTRODUCED_ACTOR = re.compile(
    r"\b(?:threat|hacking|hacker|ransomware|extortion|cybercrime|APT|espionage|state-backed)"
    r" (?:group|gang|actor|crew|cluster|operation)"
    r" (?:called|named|dubbed|known as|tracked as)"
    r" (?:[\"“‘'](?P<quoted>[^\"”’']{2,40})[\"”’']"
    r"|(?P<bare>[A-Z0-9][\w-]*(?: [A-Z0-9][\w-]*){0,2}))"
)


def threat_actors(records: list[SourceRecord]) -> list[str]:
    cat = catalog.load()
    found: list[str] = []

    def add(name: str) -> None:
        name = " ".join(name.split())
        if name and name.casefold() not in {f.casefold() for f in found}:
            found.append(name)

    for record in records:
        group = (record.metadata or {}).get("group")
        if isinstance(group, str):
            add(group)
    for record in records:
        for text in (record.headline, record.excerpt):
            # Longest name at a position wins; a name inside it ("Lazarus" in "Lazarus Group")
            # is not a second actor.
            hits = sorted(
                (m.start(), -len(a.name), m.end(), a.name)
                for a in cat.threat_actors
                for m in _whole(a.name, text)
            )
            taken_until = -1
            for start, _, end, name in hits:
                if start >= taken_until:
                    add(name)
                    taken_until = end
            for m in INTRODUCED_ACTOR.finditer(text):
                add(m["quoted"] or m["bare"])
    return found


def attack_vector(records: list[SourceRecord]) -> str | None:
    texts = [t for r in records for t in (r.headline, r.excerpt) if t]
    for label, rule in ATTACK_VECTORS:
        if any(rule.search(t) for t in texts):
            return label
    return None


def cves(records: list[SourceRecord]) -> list[str]:
    return sorted({c for r in records for c in r.cves})


def _whole(name: str, text: str):
    return re.finditer(rf"(?<!\w){re.escape(name)}(?!\w)", text)
