"""Worker: each pass fetches every due registry source, stores its events and records its health.

The network is replaced by httpx.MockTransport here; the fetcher's own network safety is
tested against a real local server in tests/fetcher.
"""

from datetime import UTC, datetime, timedelta

import httpx

from compromised import health, storage
from compromised.pipeline.fetcher import FetchPolicy
from compromised.sources import REGISTRY, allowed_hosts, by_id
from compromised.worker import due, run_once
from tests.samples import real_sample

UA = "CompromisedBot/test"
POLICY = FetchPolicy(
    user_agent=UA, allowed_hosts=allowed_hosts(), max_attempts=1, backoff_seconds=0
)
T0 = datetime(2026, 11, 26, 15, 0, tzinfo=UTC)

SAMPLES = {
    "therecord": "therecord.xml",
    "bleepingcomputer": "bleepingcomputer.xml",
    "securityweek": "securityweek.xml",
    "thehackernews": "thehackernews.xml",
    "darkreading": "darkreading.xml",
    "securityaffairs": "securityaffairs.xml",
    "krebsonsecurity": "krebsonsecurity.xml",
    "cisco-talos": "cisco-talos.xml",
    "unit42": "unit42.xml",
    "google-threat-intelligence": "google-threat-intelligence.xml",
}
BY_ENDPOINT = {by_id(sid).endpoint: sid for sid in SAMPLES}


class FakeSources:
    """Answers each registry endpoint with that source's real sample, unless told otherwise."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self.overrides: dict[str, httpx.Response] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        source_id = BY_ENDPOINT[str(request.url)]
        if source_id in self.overrides:
            return self.overrides[source_id]
        if request.headers.get("if-none-match") == f'"{source_id}-v1"':
            return httpx.Response(304)
        return httpx.Response(
            200,
            content=real_sample(SAMPLES[source_id]),
            headers={"ETag": f'"{source_id}-v1"', "Last-Modified": "Thu, 26 Nov 2026 14:54:00 GMT"},
        )

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self))


def health_by_id(conn, now=T0):
    return {h.source_id: h for h in health.source_health(conn, REGISTRY, now=now)}


async def test_one_pass_fetches_every_source_once_politely_and_stores_its_events(conn):
    fake = FakeSources()

    async with fake.client() as client:
        outcomes = await run_once(conn, client=client, policy=POLICY, now=T0)

    assert sorted(str(r.url) for r in fake.requests) == sorted(s.endpoint for s in REGISTRY)
    assert {r.headers["user-agent"] for r in fake.requests} == {UA}
    assert {sid: o.new_events for sid, o in outcomes.items()} == {sid: 3 for sid in SAMPLES}
    assert len(storage.list_events(conn, limit=100).events) == 30
    seen = health_by_id(conn)
    assert {h.state for h in seen.values()} == {"ok"}
    assert seen["darkreading"].last_success_at == T0


async def test_the_next_pass_sends_stored_validators_and_a_304_costs_no_parsing(conn):
    fake = FakeSources()
    async with fake.client() as client:
        await run_once(conn, client=client, policy=POLICY, now=T0)
        fake.requests.clear()
        later = T0 + timedelta(hours=1)
        outcomes = await run_once(conn, client=client, policy=POLICY, now=later)

    request = next(r for r in fake.requests if str(r.url) == by_id("securityweek").endpoint)
    assert request.headers["if-none-match"] == '"securityweek-v1"'
    assert request.headers["if-modified-since"] == "Thu, 26 Nov 2026 14:54:00 GMT"
    assert outcomes["securityweek"].not_modified
    assert outcomes["securityweek"].items is None  # the parser never ran
    assert health_by_id(conn, later)["securityweek"].last_success_at == later


async def test_a_failing_and_a_malformed_source_are_recorded_and_do_not_stop_the_others(conn):
    fake = FakeSources()
    fake.overrides["therecord"] = httpx.Response(503)
    fake.overrides["krebsonsecurity"] = httpx.Response(
        200, content=b"<html><body>Just a moment...</body></html>", headers={"ETag": '"bad"'}
    )

    async with fake.client() as client:
        outcomes = await run_once(conn, client=client, policy=POLICY, now=T0)
        second = T0 + timedelta(hours=1)
        await run_once(conn, client=client, policy=POLICY, now=second)

    assert outcomes["therecord"].error == "HTTP 503"
    assert outcomes["krebsonsecurity"].error.startswith("not a feed")
    assert len(storage.list_events(conn, limit=100).events) == 24
    seen = health_by_id(conn, second)
    for failing in ("therecord", "krebsonsecurity"):
        assert seen[failing].state == "failing"
        assert seen[failing].consecutive_failures == 2
        assert seen[failing].last_attempt_at == second
        assert seen[failing].last_success_at is None
    assert seen["therecord"].last_error == "HTTP 503"
    assert seen["bleepingcomputer"].state == "ok"
    # A malformed body's validators are not kept, so the next pass downloads it again in full.
    krebs = [r for r in fake.requests if str(r.url) == by_id("krebsonsecurity").endpoint]
    assert "if-none-match" not in krebs[-1].headers


async def test_a_source_that_recovers_is_healthy_again(conn):
    fake = FakeSources()
    fake.overrides["therecord"] = httpx.Response(503)
    async with fake.client() as client:
        await run_once(conn, client=client, policy=POLICY, now=T0)
        del fake.overrides["therecord"]
        later = T0 + timedelta(minutes=5)
        await run_once(conn, client=client, policy=POLICY, now=later)

    record = health_by_id(conn, later)["therecord"]
    assert (record.state, record.consecutive_failures, record.last_success_at) == ("ok", 0, later)


async def test_each_source_is_due_again_only_after_its_own_interval(conn):
    fake = FakeSources()
    async with fake.client() as client:
        await run_once(conn, client=client, policy=POLICY, now=T0)

    assert due(conn, REGISTRY, now=T0 + timedelta(minutes=4)) == []
    assert [s.id for s in due(conn, REGISTRY, now=T0 + timedelta(minutes=5))] == ["therecord"]
    assert {s.id for s in due(conn, REGISTRY, now=T0 + timedelta(minutes=30))} == {
        "therecord",
        "bleepingcomputer",
        "securityweek",
        "thehackernews",
        "darkreading",
        "securityaffairs",
        "krebsonsecurity",
        "cisco-talos",
        "unit42",
    }
    assert len(due(conn, REGISTRY, now=T0 + timedelta(minutes=60))) == 10


def test_every_source_is_due_before_its_first_check(conn):
    assert len(due(conn, REGISTRY, now=T0)) == 10
