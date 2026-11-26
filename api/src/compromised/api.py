"""Read-only JSON API, versioned under /v1."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, PlainSerializer

from compromised import config, storage

UtcTimestamp = Annotated[
    datetime,
    PlainSerializer(
        lambda d: d.astimezone(UTC).isoformat().replace("+00:00", "Z"), return_type=str
    ),
]


class SourceOut(BaseModel):
    publisher: str
    url: str
    headline: str
    excerpt: str
    published_at: UtcTimestamp


class EventOut(BaseModel):
    id: int
    title: str
    published_at: UtcTimestamp
    first_seen_at: UtcTimestamp
    sources: list[SourceOut]


class EventPageOut(BaseModel):
    events: list[EventOut]
    next_cursor: str | None


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
    ):
        with request.app.state.pool.connection() as conn:
            try:
                page = storage.list_events(conn, limit=limit, cursor=cursor)
            except storage.InvalidCursor:
                raise HTTPException(status_code=400, detail="Invalid cursor") from None
        return EventPageOut.model_validate(page, from_attributes=True)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app
