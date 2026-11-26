"""Read-only JSON API, versioned under /v1."""

from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, PlainSerializer

from compromised import config, health, storage
from compromised.pipeline import verifier
from compromised.pipeline.classifier import CATEGORIES
from compromised.pipeline.scope import TABS
from compromised.sources import REGISTRY, TIER_WEIGHT, Tier, by_id

# Query values accepted for ?tab=, one per feed tab.
TabId = StrEnum("TabId", {tab_id: tab_id for tab_id in TABS})
DEFAULT_TAB = TabId("all")

UtcTimestamp = Annotated[
    datetime,
    PlainSerializer(
        lambda d: d.astimezone(UTC).isoformat().replace("+00:00", "Z"), return_type=str
    ),
]


class SourceOut(BaseModel):
    record_id: int
    publisher: str
    url: str
    headline: str
    excerpt: str
    published_at: UtcTimestamp


class TrustOut(BaseModel):
    """Verification status, its reader-facing label, the 0-100 score and the publishers the
    score counted. Always sent and shown together: the score never stands alone."""

    status: str  # confirmed | reported | claimed | investigating | disputed
    label: str
    score: int
    sources: list[str]


class ImageOut(BaseModel):
    """The image a publisher put in its own feed. The browser loads it from the publisher with
    no referrer and credits the publisher; our servers never fetch or store it."""

    url: str
    publisher: str


class EventOut(BaseModel):
    id: int
    title: str
    published_at: UtcTimestamp
    first_seen_at: UtcTimestamp
    category: str
    category_label: str
    commentary: bool
    affected_organization: str  # "unknown" when no organization is known
    organization_key: str | None
    logo_key: str | None
    tabs: list[str]
    summary: str | None  # plain-language summary written by the model; show as "AI summary"
    action_line: str | None  # only when a source states the action
    enrichment: str  # "ai" when the model's reply was accepted, "rules" otherwise
    source_count: int
    sources: list[SourceOut]  # earliest first; the first one's headline is the title
    trust: TrustOut | None  # None for commentary (not an incident) or before first assessment
    image: ImageOut | None  # the earliest source's feed image; None when off or absent


class ScoredSourceOut(BaseModel):
    name: str
    tier: str
    weight: int


class ScoringOut(BaseModel):
    """The confidence formula's numbers, as the code uses them ("How we score")."""

    claim_only: int
    one_outlet: int
    per_extra_outlet: int
    press_cap: int
    official: int
    official_and_press: int
    disputed: int
    sources: list[ScoredSourceOut]


class TabOut(BaseModel):
    id: str
    label: str


class EventPageOut(BaseModel):
    events: list[EventOut]
    next_cursor: str | None


class SourceHealthOut(BaseModel):
    id: str
    name: str
    tier: str
    interval_seconds: int
    state: str  # pending | ok | failing | stale
    last_attempt_at: UtcTimestamp | None
    last_success_at: UtcTimestamp | None
    consecutive_failures: int


class StatusOut(BaseModel):
    status: str  # starting | live | degraded | down
    last_success_at: UtcTimestamp | None
    sources: list[SourceHealthOut]


def _image(event, settings: config.Settings) -> ImageOut | None:
    """The earliest source's image, skipping sources whose images are switched off."""
    if not settings.publisher_images:
        return None
    for source in event.sources:
        if not source.image_url or source.source_id in settings.publisher_images_off_for:
            continue
        try:
            if not by_id(source.source_id).publisher_images:
                continue
        except KeyError:
            pass  # a source no longer in the registry keeps its stored image
        return ImageOut(url=source.image_url, publisher=source.publisher)
    return None


def create_app(database_url: str | None = None) -> FastAPI:
    settings = config.load()
    url = database_url or settings.database_url

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        with ConnectionPool(url, min_size=1, max_size=5, open=True) as pool:
            app.state.pool = pool
            yield

    app = FastAPI(title="Compromised API", version="1", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=list(settings.web_origins), allow_methods=["GET"]
    )

    @app.get("/v1/events", response_model=EventPageOut)
    def list_events(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=storage.MAX_PAGE_SIZE)] = 20,
        cursor: str | None = None,
        tab: TabId = DEFAULT_TAB,
    ):
        if tab == "trending":
            # Trending is ranked by its own ticket (#10); until then it has no events.
            return EventPageOut(events=[], next_cursor=None)
        with request.app.state.pool.connection() as conn:
            try:
                page = storage.list_events(conn, limit=limit, cursor=cursor, tab=tab.value)
            except storage.InvalidCursor:
                raise HTTPException(status_code=400, detail="Invalid cursor") from None
        return EventPageOut(
            events=[
                EventOut.model_validate(
                    {
                        **asdict(e),
                        "category_label": CATEGORIES[e.category],
                        "source_count": len(e.sources),
                        "trust": _trust(e),
                        "image": _image(e, settings),
                    }
                )
                for e in page.events
            ],
            next_cursor=page.next_cursor,
        )

    @app.get("/v1/scoring", response_model=ScoringOut)
    def scoring(response: Response):
        response.headers["Cache-Control"] = "public, max-age=300"
        return ScoringOut(
            claim_only=TIER_WEIGHT[Tier.ATTACKER_CLAIM],
            one_outlet=TIER_WEIGHT[Tier.PRESS],
            per_extra_outlet=verifier.PER_EXTRA_OUTLET,
            press_cap=verifier.PRESS_CAP,
            official=TIER_WEIGHT[Tier.OFFICIAL],
            official_and_press=verifier.OFFICIAL_AND_PRESS,
            disputed=verifier.DISPUTED,
            sources=[
                ScoredSourceOut(name=s.name, tier=str(s.tier), weight=s.weight) for s in REGISTRY
            ],
        )

    @app.get("/v1/tabs", response_model=list[TabOut])
    def list_tabs():
        return [TabOut(id=tab_id, label=label) for tab_id, label in TABS.items()]

    @app.get("/v1/status", response_model=StatusOut)
    def status(request: Request, response: Response):
        """Overall ingestion status and each source's health. Error details stay server-side."""
        with request.app.state.pool.connection() as conn:
            current = health.ingestion_status(conn, REGISTRY, now=datetime.now(UTC))
        response.headers["Cache-Control"] = "public, max-age=15"
        return StatusOut(
            status=current.status,
            last_success_at=current.last_success_at,
            sources=[
                SourceHealthOut(
                    id=h.source_id,
                    name=h.name,
                    tier=str(h.tier),
                    interval_seconds=h.interval_seconds,
                    state=h.state,
                    last_attempt_at=h.last_attempt_at,
                    last_success_at=h.last_success_at,
                    consecutive_failures=h.consecutive_failures,
                )
                for h in current.sources
            ],
        )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app


def _trust(event) -> dict | None:
    if event.status is None:
        return None
    return {
        "status": event.status,
        "label": event.status_label,
        "score": event.score,
        "sources": list(event.score_sources),
    }
