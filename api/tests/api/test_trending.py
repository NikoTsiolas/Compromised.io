"""HTTP API seam: Trending order (#10).

The formula (docs/wiki/feed-scope-and-sources.md, "Trending as built"): every distinct news or
official source that reported the event within the last 72 hours adds 0.5 ^ (hours since that
source's latest report on it / 24). Attacker-claim sources add nothing. No engagement data exists.

Every item here is SYNTHETIC: hand-written RSS, not a real incident.
"""

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
from fastapi.testclient import TestClient

from compromised.api import create_app
from compromised.pipeline import ingest
from tests.samples import sample_source

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def rss(*items: tuple[str, str, float]) -> bytes:
    """A synthetic feed of (headline, link, hours before NOW) items."""
    body = "".join(
        f"<item><title>{title}</title><link>{link}</link><guid>{link}</guid>"
        f"<pubDate>{format_datetime(NOW - timedelta(hours=hours))}</pubDate>"
        "<description>Synthetic excerpt.</description></item>"
        for title, link, hours in items
    )
    return (
        '<?xml version="1.0"?><rss version="2.0"><channel><title>Synthetic</title>'
        f"<link>https://example.com/</link><description>Synthetic</description>{body}"
        "</channel></rss>"
    ).encode()


# Headline, link, and the hours before NOW at which each listed source reported it. One link per
# event, so every source's record groups into the same event (identical canonical URL).
EVENTS = {
    # 3 sources, all 50 h ago: 3 x 0.5^(50/24) = 0.708
    "A": ("[Synthetic test item] Dropbox data breach exposes users", [50, 50, 50]),
    # 1 source, 1 h ago: 0.972
    "B": ("[Synthetic test item] Spotify data breach exposes users", [1]),
    # 2 sources, 10 h ago: 2 x 0.749 = 1.498
    "C": ("[Synthetic test item] Netflix data breach exposes users", [10, 10]),
    # 4 sources, 80 h ago: outside the 72-hour window, not trending at all
    "D": ("[Synthetic test item] Ticketmaster data breach exposes users", [80, 80, 80, 80]),
    # An older story that fresh coverage revives: 0.5^(70/24) + 0.5^(2/24) = 0.132 + 0.944 = 1.076
    "E": ("[Synthetic test item] Uber data breach exposes users", [70, 2]),
}
PRESS = ["bleepingcomputer", "securityaffairs", "therecord", "darkreading"]


@pytest.fixture
def client(conn, database_url):
    for i, source_id in enumerate(PRESS):
        items = [
            (title, f"https://example.com/synthetic-{key.lower()}", hours[i])
            for key, (title, hours) in EVENTS.items()
            if i < len(hours)
        ]
        ingest(conn, sample_source(source_id), rss(*items), fetched_at=NOW)
    app = create_app(database_url=database_url, clock=lambda: NOW)
    with TestClient(app) as test_client:
        yield test_client


def keys(response) -> list[str]:
    assert response.status_code == 200, response.text
    by_title = {title: key for key, (title, _) in EVENTS.items()}
    return [by_title[e["title"]] for e in response.json()["events"]]


def test_trending_ranks_by_distinct_sources_decayed_by_each_sources_report_age(client):
    assert keys(client.get("/v1/trending")) == ["C", "E", "B", "A"]


def test_the_trending_tab_lists_the_same_ranking(client):
    assert keys(client.get("/v1/events", params={"tab": "trending"})) == ["C", "E", "B", "A"]


def test_trending_pages_keep_the_ranking_of_the_first_page(client):
    first = client.get("/v1/trending", params={"limit": 2})
    assert keys(first) == ["C", "E"]
    second = client.get("/v1/trending", params={"limit": 2, "cursor": first.json()["next_cursor"]})
    assert keys(second) == ["B", "A"]
    assert second.json()["next_cursor"] is None


def test_trending_uses_no_engagement_data(client):
    [event, *_] = client.get("/v1/trending").json()["events"]
    engagement = {"views", "likes", "clicks", "shares", "comments", "reads", "votes"}
    assert not engagement & set(event)


def test_a_tampered_trending_cursor_is_a_client_error(client):
    response = client.get("/v1/trending", params={"cursor": "MjAyNi0xMS0yNnwx"})
    assert response.status_code == 400
