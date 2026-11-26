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
    grouping: Grouping = field(default_factory=Grouping)


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
            "CompromisedBot/0.1 (+https://github.com/NikoTsiolas/Compromised.io)",
        ),
        environment=os.environ.get("ENVIRONMENT", "development"),
        grouping=Grouping.from_env(),
    )
