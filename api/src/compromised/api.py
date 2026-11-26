"""Read-only JSON API, versioned under /v1."""

from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, PlainSerializer

from compromised import config, health, storage, widgets
from compromised.pipeline import verifier
from compromised.pipeline.classifier import CATEGORIES
from compromised.pipeline.scope import TABS
from compromised.sources import REGISTRY, TIER_WEIGHT, Tier, by_id
from compromised.storage import search as search_storage

# Query values accepted for ?tab=, one per feed tab.
TabId = StrEnum("TabId", {tab_id: tab_id for tab_id in TABS})
DEFAULT_TAB = TabId("all")
# Query values accepted by the search filters. Trending is a ranking, not a filter.
FilterTabId = StrEnum("FilterTabId", {t: t for t in TABS if t != "trending"})
CategoryId = StrEnum("CategoryId", {c: c for c in CATEGORIES})
SourceId = StrEnum("SourceId", {s.id: s.id for s in REGISTRY})
StatusId = StrEnum("StatusId", {s: s for s in verifier.STATUS_NAMES})

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
    cves: list[str]  # every CVE identifier the sources name, sorted
    threat_actors: list[str]  # groups a source names or a claim source credits
    attack_vector: str | None  # how the attack worked, when a source says; None if not identified


class ScoredSourceOut(BaseModel):
    name: str
    tier: str
    weight: int


class TrendingRuleOut(BaseModel):
    """Trending's recency decay: each source adds 0.5 ^ (hours since its report / half-life)."""

    window_hours: int
    half_life_hours: int


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
    trending: TrendingRuleOut


class TabOut(BaseModel):
    id: str
    label: str


class EventPageOut(BaseModel):
    events: list[EventOut]
    next_cursor: str | None


class FilterOptionOut(BaseModel):
    id: str
    label: str


class FiltersOut(BaseModel):
    """The values each search filter accepts, with reader-facing labels."""

    tabs: list[FilterOptionOut]
    categories: list[FilterOptionOut]
    sources: list[FilterOptionOut]
    statuses: list[FilterOptionOut]


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


class NotableOut(BaseModel):
    cve: str
    title: str  # the weakness, without the vendor and product CISA puts first
    name: str  # CISA's full vulnerabilityName
    organization: str
    people_use: bool
    ransomware: bool  # CISA: known to be used in ransomware campaigns


class MonthOut(BaseModel):
    month: str  # "YYYY-MM"
    count: int  # entries added to the KEV catalog that month (UTC)
    spike: bool  # by spike_rule, over the months returned
    notable: list[NotableOut]  # spike months only, at most three, newest first


class KevCatalogOut(BaseModel):
    version: str | None
    declared_count: int | None  # the size the catalog states for itself
    entries: int  # entries kept from it
    fetched_at: UtcTimestamp


class ExploitedByMonthOut(BaseModel):
    months: list[MonthOut]  # oldest first; empty until the catalog has been fetched
    spike_rule: str
    catalog: KevCatalogOut | None


class ExploitedFlawOut(BaseModel):
    cve: str
    product: str
    logo_key: str | None
    added_on: date  # the day CISA listed it as exploited


class RecentlyExploitedOut(BaseModel):
    items: list[ExploitedFlawOut]


class OrganisationOut(BaseModel):
    name: str
    key: str | None
    logo_key: str | None
    count: int  # distinct reported events naming it in the window


class MostReportedOut(BaseModel):
    window_days: int
    items: list[OrganisationOut]


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


def create_app(
    database_url: str | None = None, clock: Callable[[], datetime] | None = None
) -> FastAPI:
    """The API. ``clock`` gives the current time (tests fix it); it ranks Trending and ends the
    widgets' windows."""
    settings = config.load()
    now = clock or (lambda: datetime.now(UTC))
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
            return trending(request, limit=limit, cursor=cursor)
        with request.app.state.pool.connection() as conn:
            try:
                page = storage.list_events(conn, limit=limit, cursor=cursor, tab=tab.value)
            except storage.InvalidCursor:
                raise HTTPException(status_code=400, detail="Invalid cursor") from None
        return _page_out(page, settings)

    @app.get("/v1/search", response_model=EventPageOut)
    def search_events(
        request: Request,
        response: Response,
        q: Annotated[str, Query(max_length=search_storage.MAX_QUERY_LENGTH)] = "",
        tab: FilterTabId | None = None,
        category: Annotated[list[CategoryId], Query()] = [],  # noqa: B006 (FastAPI copies it)
        source: Annotated[list[SourceId], Query()] = [],  # noqa: B006
        status: Annotated[list[StatusId], Query()] = [],  # noqa: B006
        since: Annotated[date | None, Query(alias="from")] = None,
        until: Annotated[date | None, Query(alias="to")] = None,
        limit: Annotated[int, Query(ge=1, le=storage.MAX_PAGE_SIZE)] = 20,
        cursor: str | None = None,
    ):
        """Published events matching a query and filters, newest first. ``q`` matches an
        organization, product, vendor, threat actor, attack vector or any word of the sources;
        CVE identifiers in it match exactly. ``from`` and ``to`` are UTC dates, both inclusive."""
        filters = search_storage.Filters(
            query=q,
            tab=tab.value if tab else None,
            categories=tuple(c.value for c in category),
            sources=tuple(s.value for s in source),
            statuses=tuple(s.value for s in status),
            since=_utc_day(since),
            until=_utc_day(until + timedelta(days=1)) if until else None,
        )
        with request.app.state.pool.connection() as conn:
            try:
                page = search_storage.search(conn, filters, limit=limit, cursor=cursor)
            except storage.InvalidCursor:
                raise HTTPException(status_code=400, detail="Invalid cursor") from None
        response.headers["Cache-Control"] = "public, max-age=30"
        return _page_out(page, settings)

    @app.get("/v1/trending", response_model=EventPageOut)
    def trending(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=storage.MAX_PAGE_SIZE)] = 20,
        cursor: str | None = None,
    ):
        """Published events ranked by distinct source coverage with recency decay
        (storage.search.trending). The Trending tab of /v1/events lists the same."""
        with request.app.state.pool.connection() as conn:
            try:
                page = search_storage.trending(conn, now=now(), limit=limit, cursor=cursor)
            except storage.InvalidCursor:
                raise HTTPException(status_code=400, detail="Invalid cursor") from None
        return _page_out(page, settings)

    @app.get("/v1/filters", response_model=FiltersOut)
    def filters(response: Response):
        response.headers["Cache-Control"] = "public, max-age=300"
        return FiltersOut(
            tabs=[FilterOptionOut(id=t, label=TABS[t]) for t in FilterTabId],
            categories=[FilterOptionOut(id=c, label=label) for c, label in CATEGORIES.items()],
            sources=[FilterOptionOut(id=s.id, label=s.name) for s in REGISTRY],
            statuses=[
                FilterOptionOut(id=s, label=label) for s, label in verifier.STATUS_NAMES.items()
            ],
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
            trending=TrendingRuleOut(
                window_hours=int(search_storage.TRENDING_WINDOW.total_seconds() // 3600),
                half_life_hours=search_storage.TRENDING_HALF_LIFE_HOURS,
            ),
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

    # Widget figures (#15). The KEV catalog is fetched hourly, so its figures keep 5 minutes.

    @app.get("/v1/widgets/exploited-by-month", response_model=ExploitedByMonthOut)
    def exploited_by_month(
        request: Request,
        response: Response,
        months: Annotated[int, Query(ge=1, le=60)] = 12,
    ):
        with request.app.state.pool.connection() as conn:
            history = widgets.exploitation_history(conn, now=now(), months=months)
        response.headers["Cache-Control"] = "public, max-age=300"
        return ExploitedByMonthOut(
            months=[MonthOut.model_validate(asdict(m)) for m in history.months],
            spike_rule=widgets.SPIKE_RULE,
            catalog=KevCatalogOut.model_validate(asdict(history.catalog))
            if history.catalog
            else None,
        )

    @app.get("/v1/widgets/recently-exploited", response_model=RecentlyExploitedOut)
    def recently_exploited(request: Request, response: Response):
        with request.app.state.pool.connection() as conn:
            flaws = widgets.recently_exploited(conn)
        response.headers["Cache-Control"] = "public, max-age=300"
        return RecentlyExploitedOut(
            items=[ExploitedFlawOut.model_validate(asdict(f)) for f in flaws]
        )

    @app.get("/v1/widgets/most-reported", response_model=MostReportedOut)
    def most_reported(request: Request, response: Response):
        with request.app.state.pool.connection() as conn:
            top = widgets.most_reported(conn, now=now())
        response.headers["Cache-Control"] = "public, max-age=60"
        return MostReportedOut(
            window_days=widgets.MOST_REPORTED_DAYS,
            items=[OrganisationOut.model_validate(asdict(o)) for o in top],
        )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app


def _utc_day(day: date | None) -> datetime | None:
    return datetime.combine(day, time(), tzinfo=UTC) if day else None


def _page_out(page, settings: config.Settings) -> EventPageOut:
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


def _trust(event) -> dict | None:
    if event.status is None:
        return None
    return {
        "status": event.status,
        "label": event.status_label,
        "score": event.score,
        "sources": list(event.score_sources),
    }
