"""Configuration from environment variables. See .env.example at the repository root."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Grouping:
    """Deduplicator thresholds, chosen from the real samples (docs/wiki/stack-and-hosting.md).

    headline_similarity: pg_trgm similarity two headlines about the same organization must reach.
    organization_window_hours: how far apart in publication time those two records may be.
    cve_window_days: how far apart in publication time two records sharing a CVE may be.
    """

    headline_similarity: float = 0.2
    organization_window_hours: float = 72
    cve_window_days: float = 7

    @classmethod
    def from_env(cls) -> "Grouping":
        defaults = cls()
        return cls(
            headline_similarity=float(
                os.environ.get("GROUPING_HEADLINE_SIMILARITY", defaults.headline_similarity)
            ),
            organization_window_hours=float(
                os.environ.get(
                    "GROUPING_ORGANIZATION_WINDOW_HOURS", defaults.organization_window_hours
                )
            ),
            cve_window_days=float(
                os.environ.get("GROUPING_CVE_WINDOW_DAYS", defaults.cve_window_days)
            ),
        )


@dataclass(frozen=True)
class Settings:
    database_url: str
    web_origins: tuple[str, ...]
    user_agent: str
    environment: str
    anthropic_api_key: str | None  # None: no enrichment, rules only (#8)
    enrichment_daily_cap: int
    grouping: Grouping = field(default_factory=Grouping)
    # Show the images publishers put in their own feeds. "off" removes them from every response.
    publisher_images: bool = True
    # Source ids whose images are never shown, whatever the registry says.
    publisher_images_off_for: frozenset[str] = frozenset()


def load() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "postgresql:///compromised"),
        web_origins=tuple(
            o.strip()
            for o in os.environ.get("WEB_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ),
        user_agent=os.environ.get(
            "USER_AGENT",
            "Compromised/0.1 (+https://github.com/NikoTsiolas/Compromised.io)",
        ),
        environment=os.environ.get("ENVIRONMENT", "development"),
        grouping=Grouping.from_env(),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        enrichment_daily_cap=_int("ENRICHMENT_DAILY_CAP", 500),
        publisher_images=os.environ.get("PUBLISHER_IMAGES", "on").strip().lower()
        not in ("off", "0", "false", "no"),
        publisher_images_off_for=frozenset(
            s.strip()
            for s in os.environ.get("PUBLISHER_IMAGES_OFF_FOR", "").split(",")
            if s.strip()
        ),
    )


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"{name} must be a whole number, got {raw!r}") from None
