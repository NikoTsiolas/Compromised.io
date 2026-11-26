"""Configuration from environment variables. See .env.example at the repository root."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    web_origins: tuple[str, ...]
    user_agent: str
    environment: str
    # Show the images publishers put in their own feeds. "off" removes them from every response.
    publisher_images: bool = True


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
        publisher_images=os.environ.get("PUBLISHER_IMAGES", "on").strip().lower()
        not in ("off", "0", "false", "no"),
    )
