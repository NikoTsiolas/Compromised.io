"""Source registry: every news and research source, as agreed in docs/wiki/feed-scope-and-sources.md
(endpoints, intervals) and docs/wiki/trust-labels-and-score.md (tiers, default weights)."""

from compromised.sources import MSRC_SUG, REGISTRY, Tier, allowed_hosts, by_id

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
        "cisco-talos",
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
        "google-threat-intelligence",
        "Google Threat Intelligence",
        "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v",
        Tier.OFFICIAL,
        90,
        60 * MIN,
    ),
]


# The structured sources (#4), from the same wiki table; each adapter's format, and a backfill
# window of 30 days (wiki: "First run backfills 30 days from structured sources").
EXPECTED_STRUCTURED = [
    (
        "cisa-advisories",
        "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "rss",
        Tier.OFFICIAL,
        90,
        30 * MIN,
    ),
    (
        "ransomware-live",
        "https://www.ransomware.live/rss.xml",
        "ransomware-live",
        Tier.ATTACKER_CLAIM,
        20,
        30 * MIN,
    ),
    (
        "cisa-kev",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "cisa-kev",
        Tier.OFFICIAL,
        90,
        60 * MIN,
    ),
    (
        "msrc-update-guide",
        "https://api.msrc.microsoft.com/update-guide/rss",
        "msrc",
        Tier.OFFICIAL,
        90,
        60 * MIN,
    ),
]
STRUCTURED_IDS = {e[0] for e in EXPECTED_STRUCTURED}


def test_every_news_and_research_source_matches_the_wiki():
    actual = [
        (s.id, s.name, s.endpoint, s.tier, s.weight, s.interval_seconds)
        for s in REGISTRY
        if s.id not in STRUCTURED_IDS
    ]
    assert sorted(actual) == sorted(EXPECTED)
    assert {s.backfill_days for s in REGISTRY if s.id not in STRUCTURED_IDS} == {None}


def test_every_structured_source_matches_the_wiki_and_backfills_30_days():
    actual = [
        (s.id, s.endpoint, s.format, s.tier, s.weight, s.interval_seconds)
        for s in REGISTRY
        if s.id in STRUCTURED_IDS
    ]
    assert sorted(actual) == sorted(EXPECTED_STRUCTURED)
    assert {by_id(i).backfill_days for i in STRUCTURED_IDS} == {30}


def test_the_structured_feeds_fit_under_their_size_cap():
    # Measured on 2026-11-26: KEV 1.9 MB, the MSRC Update Guide 3.3 MB.
    assert by_id("cisa-kev").max_bytes >= 4 * 1024 * 1024
    assert by_id("msrc-update-guide").max_bytes >= 8 * 1024 * 1024


def test_ransomware_live_crawl_delay_is_respected():
    assert by_id("ransomware-live").crawl_delay_seconds == 5


def test_every_endpoint_is_https_and_has_a_response_size_cap():
    for source in REGISTRY:
        assert source.endpoint.startswith("https://")
        assert 0 < source.max_bytes <= 16 * 1024 * 1024


def test_the_full_text_feeds_fit_under_their_size_cap():
    # Measured on 2026-11-26: Talos served 1.1 MB; Google's 20 items run to 90 KB each.
    assert by_id("cisco-talos").max_bytes >= 3 * 1024 * 1024
    assert by_id("google-threat-intelligence").max_bytes >= 4 * 1024 * 1024


def test_the_allow_list_is_exactly_the_registry_hosts_plus_the_msrc_sug_api():
    # The SUG API shares its host with the MSRC Update Guide feed.
    assert MSRC_SUG.host == "api.msrc.microsoft.com"
    assert allowed_hosts() == {
        "www.cisa.gov",
        "www.ransomware.live",
        "api.msrc.microsoft.com",
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
