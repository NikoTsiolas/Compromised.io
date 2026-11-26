"""Worker: each pass fetches every due registry source, stores its events and records its health.

The network is replaced by httpx.MockTransport here; the fetcher's own network safety is
tested against a real local server in tests/fetcher.
"""

from datetime import UTC, datetime, timedelta

import httpx

from compromised import health, storage
from compromised.pipeline.fetcher import FetchPolicy
from compromised.sources import MSRC_SUG, REGISTRY, allowed_hosts, by_id
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
    "cisa-advisories": "cisa-advisories.xml",
    "ransomware-live": "ransomware-live.xml",
    "cisa-kev": "cisa-kev.json",
    "msrc-update-guide": "msrc-update-guide.xml",
}
BY_ENDPOINT = {by_id(sid).endpoint: sid for sid in SAMPLES}
# New events per source from one pass over the real samples: every item, except that only one
# MSRC entry (Visio, rated Critical) passes the product and rating gate.
NEW_EVENTS = {sid: 3 for sid in SAMPLES} | {"msrc-update-guide": 1}


class FakeSources:
    """Answers each registry endpoint with that source's real sample, unless told otherwise, and
    the MSRC SUG API with its real answer for the three listed-product CVEs in the MSRC sample."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self.overrides: dict[str, httpx.Response] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.copy_with(query=None) == httpx.URL(MSRC_SUG.endpoint):
            if "msrc-sug" in self.overrides:
                return self.overrides["msrc-sug"]
            return httpx.Response(200, content=real_sample("msrc-sug.json"))
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

    feeds = [
        r for r in fake.requests if r.url.host != "api.msrc.microsoft.com" or "rss" in str(r.url)
    ]
    assert sorted(str(r.url) for r in feeds) == sorted(s.endpoint for s in REGISTRY)
    assert {r.headers["user-agent"] for r in fake.requests} == {UA}
    # Security Affairs and The Hacker News each carry the 1Password breach BleepingComputer
    # already reported, so that item joins BleepingComputer's event. CISA's "Adds 10 Known
    # Exploited Vulnerabilities" alert joins Security Affairs' write-up (shared CVE), and the
    # KEV Juniper entry joins SecurityWeek's story on the same CVE.
    joined = {"securityaffairs", "thehackernews", "cisa-advisories", "cisa-kev"}
    assert {sid: (o.new_events, o.grouped) for sid, o in outcomes.items()} == {
        sid: (NEW_EVENTS[sid] - 1, 1) if sid in joined else (NEW_EVENTS[sid], 0) for sid in SAMPLES
    }
    assert len(storage.list_events(conn, limit=100).events) == 36
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
    # 40 items less The Record's and Krebs' 6, grouped as in the pass above.
    assert len(storage.list_events(conn, limit=100).events) == 30
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
        "cisa-advisories",
        "ransomware-live",
    }
    assert len(due(conn, REGISTRY, now=T0 + timedelta(minutes=60))) == 14


def test_every_source_is_due_before_its_first_check(conn):
    assert len(due(conn, REGISTRY, now=T0)) == 14


def sug_requests(fake):
    return [r for r in fake.requests if r.url.path.startswith("/sug/")]


async def test_msrc_ratings_are_asked_only_for_listed_products_revised_since_the_last_check(conn):
    fake = FakeSources()
    async with fake.client() as client:
        await run_once(
            conn, client=client, policy=POLICY, sources=[by_id("msrc-update-guide")], now=T0
        )
        [first] = sug_requests(fake)
        fake.requests.clear()
        fake.overrides["msrc-update-guide"] = httpx.Response(
            200, content=real_sample("msrc-update-guide.xml")
        )
        await run_once(
            conn,
            client=client,
            policy=POLICY,
            sources=[by_id("msrc-update-guide")],
            now=T0 + timedelta(hours=1),
        )

    assert first.url.host == "api.msrc.microsoft.com"
    assert first.headers["user-agent"] == UA
    assert first.url.params["$filter"] == (
        "cveNumber eq 'CVE-2026-112732' or cveNumber eq 'CVE-2026-69291'"
        " or cveNumber eq 'CVE-2026-72965'"
    )
    # Nothing in the feed was revised since the first check: no lookup at all.
    assert sug_requests(fake) == []


async def test_a_failed_msrc_rating_lookup_fails_the_source_so_the_next_pass_retries(conn):
    fake = FakeSources()
    fake.overrides["msrc-sug"] = httpx.Response(503)
    async with fake.client() as client:
        outcomes = await run_once(
            conn, client=client, policy=POLICY, sources=[by_id("msrc-update-guide")], now=T0
        )

    assert outcomes["msrc-update-guide"].error == "HTTP 503"
    seen = health_by_id(conn)["msrc-update-guide"]
    assert (seen.state, seen.last_success_at) == ("failing", None)
    assert storage.list_events(conn, limit=100).events == []
