"""Worker: one pass fetches each registry source and stores its events."""

import httpx

from compromised import storage
from compromised.worker import run_once
from tests.samples import real_sample


async def test_one_pass_fetches_the_registry_endpoint_politely_and_stores_events(conn):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=real_sample("bleepingcomputer.xml"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await run_once(conn, client=client, user_agent="CompromisedBot/test")
        await run_once(conn, client=client, user_agent="CompromisedBot/test")

    assert [str(r.url) for r in seen] == ["https://www.bleepingcomputer.com/feed/"] * 2
    assert seen[0].headers["user-agent"] == "CompromisedBot/test"
    assert len(storage.list_events(conn, limit=10).events) == 3


async def test_a_failed_fetch_is_logged_and_does_not_raise(conn):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results = await run_once(conn, client=client, user_agent="CompromisedBot/test")

    assert results == {"bleepingcomputer": None}
    assert storage.list_events(conn, limit=10).events == []
