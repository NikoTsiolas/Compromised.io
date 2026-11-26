from pathlib import Path

from compromised import sources
from compromised.sources import Source, Tier

FIXTURES = Path(__file__).parent / "fixtures"

# Sources whose real samples are captured in fixtures/real/<id>.xml. Until each one has a
# registry entry (#3, #4), tests describe it here with its wiki endpoint.
SAMPLE_SOURCES = {
    "therecord": ("The Record", "https://therecord.media/feed"),
    "securityweek": ("SecurityWeek", "https://www.securityweek.com/feed/"),
    "thehackernews": ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    "darkreading": ("Dark Reading", "https://www.darkreading.com/rss.xml"),
    "securityaffairs": ("Security Affairs", "https://securityaffairs.com/feed"),
    "krebsonsecurity": ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    "cisa-advisories": (
        "CISA advisories",
        "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    ),
    "cisco-talos": ("Cisco Talos", "https://blog.talosintelligence.com/rss/"),
    "unit42": ("Unit 42", "https://unit42.paloaltonetworks.com/feed/"),
    "google-threat-intelligence": (
        "Google Threat Intelligence",
        "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v",
    ),
    "ransomware-live": ("Ransomware.live", "https://www.ransomware.live/rss.xml"),
    "msrc-update-guide": ("MSRC Update Guide", "https://api.msrc.microsoft.com/update-guide/rss"),
}


def real_sample(name: str) -> bytes:
    """Bytes of a real captured feed response (see fixtures/real/README.md)."""
    return (FIXTURES / "real" / name).read_bytes()


def synthetic_sample(name: str) -> bytes:
    """Bytes of a hand-written input (see fixtures/synthetic/README.md). Not a real incident."""
    return (FIXTURES / "synthetic" / name).read_bytes()


def sample_source(source_id: str) -> Source:
    """The registry entry for a sampled source, or a stand-in with its wiki endpoint."""
    try:
        return sources.by_id(source_id)
    except KeyError:
        name, endpoint = SAMPLE_SOURCES[source_id]
        return Source(
            id=source_id,
            name=name,
            endpoint=endpoint,
            format="rss",
            tier=STAND_IN_TIERS.get(source_id, Tier.PRESS),
            interval_seconds=1800,
        )


# Tiers (docs/wiki/trust-labels-and-score.md) for sampled sources not yet in the registry (#4).
STAND_IN_TIERS = {
    "cisa-advisories": Tier.OFFICIAL,
    "msrc-update-guide": Tier.OFFICIAL,
    "ransomware-live": Tier.ATTACKER_CLAIM,
}
