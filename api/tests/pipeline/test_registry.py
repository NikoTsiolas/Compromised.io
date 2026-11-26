"""Source registry: every news and research source, as agreed in docs/wiki/feed-scope-and-sources.md
(endpoints, intervals) and docs/wiki/trust-labels-and-score.md (tiers, default weights)."""

from compromised.sources import REGISTRY, Tier, allowed_hosts, by_id

MIN = 60

# (id, name, endpoint, tier, weight, interval) copied from the wiki tables, not from the code.
EXPECTED = [
    ("therecord", "The Record", "https://therecord.media/feed", Tier.PRESS, 50, 5 * MIN),
    (
        "bleepingcomputer",
        "BleepingComputer",
        "https://www.bleepingcomputer.com/feed/",
        Tier.PRESS,
        50,
        10 * MIN,
    ),
    (
        "securityweek",
        "SecurityWeek",
        "https://www.securityweek.com/feed/",
        Tier.PRESS,
        50,
        10 * MIN,
    ),
    (
        "thehackernews",
        "The Hacker News",
        "https://feeds.feedburner.com/TheHackersNews",
        Tier.PRESS,
        50,
        15 * MIN,
    ),
    (
        "darkreading",
        "Dark Reading",
        "https://www.darkreading.com/rss.xml",
        Tier.PRESS,
        50,
        15 * MIN,
    ),
    (
        "securityaffairs",
        "Security Affairs",
        "https://securityaffairs.com/feed",
        Tier.PRESS,
        50,
        15 * MIN,
    ),
    (
        "krebsonsecurity",
        "Krebs on Security",
        "https://krebsonsecurity.com/feed/",
        Tier.PRESS,
        50,
        30 * MIN,
    ),
    (
        "ciscotalos",
        "Cisco Talos",
        "https://blog.talosintelligence.com/rss/",
        Tier.OFFICIAL,
        90,
        30 * MIN,
    ),
    (
        "unit42",
        "Unit 42",
        "https://unit42.paloaltonetworks.com/feed/",
        Tier.OFFICIAL,
        90,
        30 * MIN,
    ),
    (
        "googlethreatintel",
        "Google Threat Intelligence",
        "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v",
        Tier.OFFICIAL,
        90,
        60 * MIN,
    ),
]


def test_every_news_and_research_source_matches_the_wiki():
    actual = [
        (s.id, s.name, s.endpoint, s.tier, s.weight, s.interval_seconds)
        for s in REGISTRY
        if s.format == "rss"
    ]
    assert sorted(actual) == sorted(EXPECTED)


def test_every_endpoint_is_https_and_has_a_response_size_cap():
    for source in REGISTRY:
        assert source.endpoint.startswith("https://")
        assert 0 < source.max_bytes <= 16 * 1024 * 1024


def test_the_full_text_feeds_fit_under_their_size_cap():
    # Measured on 2026-11-26: Talos served 1.1 MB; Google's 20 items run to 90 KB each.
    assert by_id("ciscotalos").max_bytes >= 3 * 1024 * 1024
    assert by_id("googlethreatintel").max_bytes >= 4 * 1024 * 1024


def test_the_allow_list_is_exactly_the_registry_hosts():
    assert allowed_hosts() == {
        "therecord.media",
        "www.bleepingcomputer.com",
        "www.securityweek.com",
        "feeds.feedburner.com",
        "www.darkreading.com",
        "securityaffairs.com",
        "krebsonsecurity.com",
        "blog.talosintelligence.com",
        "unit42.paloaltonetworks.com",
    }


def test_krebs_crawl_delay_is_respected():
    assert by_id("krebsonsecurity").crawl_delay_seconds == 35
