"""Configuration from environment variables. See .env.example at the repository root."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    web_origins: tuple[str, ...]
    user_agent: str
    environment: str
    anthropic_api_key: str | None  # None: no enrichment, rules only (#8)
    enrichment_daily_cap: int


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
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        enrichment_daily_cap=_int("ENRICHMENT_DAILY_CAP", 500),
    )


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"{name} must be a whole number, got {raw!r}") from None
