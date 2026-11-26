"""Pipeline seam for the homepage widgets' data (#15): the exploited-flaws-per-month history
kept from the whole CISA KEV catalog, the spike rule, recently exploited flaws, and the
organisations named in the most events.

Expected values were counted by hand from the fixture files. The real KEV sample is trimmed to
its 3 newest entries (all added on 25 November 2026) while its own ``count`` still says 1805, so
it can show that every entry it carries is counted, not that a full catalog's months match; the
labelled synthetic catalog (tests/fixtures/synthetic/kev-history.json) spans several months.
"""

from datetime import UTC, date, datetime

import pytest

from compromised import widgets
from compromised.pipeline import ParseError, ingest
from compromised.sources import by_id
from tests.samples import real_sample, synthetic_sample

KEV = by_id("cisa-kev")
REAL_FETCH = datetime(2026, 11, 26, 14, 54, 7, tzinfo=UTC)
SYNTHETIC_FETCH = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def months(history):
    return [(m.month, m.count) for m in history.months]


def test_no_history_before_the_catalog_has_been_fetched(conn):
    history = widgets.exploitation_history(conn, now=REAL_FETCH)

    assert history.months == []
    assert history.catalog is None


def test_the_real_sample_is_counted_entry_for_entry_in_its_month(conn):
    ingest(conn, KEV, real_sample("cisa-kev.json"), fetched_at=REAL_FETCH)

    history = widgets.exploitation_history(conn, now=REAL_FETCH)

    # Twelve months ending with the current one; months with no additions count zero.
    assert months(history) == [
        ("2025-12", 0),
        ("2026-01", 0),
        ("2026-02", 0),
        ("2026-03", 0),
        ("2026-04", 0),
        ("2026-05", 0),
        ("2026-06", 0),
        ("2026-07", 0),
        ("2026-08", 0),
        ("2026-09", 0),
        ("2026-10", 0),
        ("2026-11", 3),
    ]
    assert history.catalog.version == "2026.11.25"
    assert history.catalog.entries == 3
    # The trimmed sample still declares the full catalog's size: the gap is reported, not hidden.
    assert history.catalog.declared_count == 1805


def test_the_whole_catalog_is_kept_not_only_the_thirty_day_backfill(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    history = widgets.exploitation_history(conn, now=SYNTHETIC_FETCH)

    assert months(history) == [
        ("2025-07", 0),
        ("2025-08", 0),
        ("2025-09", 0),
        ("2025-10", 0),
        ("2025-11", 0),
        ("2025-12", 0),
        ("2026-01", 2),
        ("2026-02", 1),
        ("2026-03", 6),
        ("2026-04", 2),
        ("2026-05", 0),
        ("2026-06", 1),
    ]
    # Every entry is kept, including the 2024 one outside the window, and matches the count.
    assert history.catalog.entries == 13
    assert history.catalog.declared_count == 13
    # Only the June entry is inside the 30-day backfill, so only it became a feed event.
    events = conn.execute("select count(*) from events").fetchone()[0]
    assert events == 1


def test_a_longer_window_reaches_back_to_older_entries(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    history = widgets.exploitation_history(conn, now=SYNTHETIC_FETCH, months=20)

    assert months(history)[:2] == [("2024-11", 1), ("2024-12", 0)]
    assert sum(m.count for m in history.months) == 13


def test_a_later_catalog_replaces_the_history_so_removed_entries_stop_counting(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)
    ingest(conn, KEV, real_sample("cisa-kev.json"), fetched_at=REAL_FETCH)

    history = widgets.exploitation_history(conn, now=REAL_FETCH)

    assert history.catalog.entries == 3
    assert sum(m.count for m in history.months) == 3


def test_a_response_that_is_not_a_catalog_leaves_the_history_alone(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    with pytest.raises(ParseError):
        ingest(conn, KEV, b'{"vulnerabilities": "none"}', fetched_at=REAL_FETCH)

    assert widgets.exploitation_history(conn, now=SYNTHETIC_FETCH).catalog.entries == 13


# --- spike rule ---------------------------------------------------------------------------------


def test_a_spike_is_a_month_at_least_one_standard_deviation_above_the_windows_average():
    # Worked example: mean 1, population standard deviation sqrt(34/12) = 1.68, so a month
    # needs 2.68 or more. Only the 6 qualifies; the 2s do not.
    counts = [0, 0, 0, 0, 0, 0, 2, 1, 6, 2, 0, 1]
    assert widgets.spikes(counts) == [False] * 8 + [True, False, False, False]


@pytest.mark.parametrize(
    "counts",
    [[], [5], [5, 9], [4, 4, 4, 4]],
    ids=["no months", "one month", "two months", "all equal"],
)
def test_too_few_months_or_no_variation_means_no_spike(counts):
    assert widgets.spikes(counts) == [False] * len(counts)


def test_a_month_exactly_on_the_threshold_is_a_spike():
    # Mean 2, standard deviation 2: 4 is exactly one deviation above.
    assert widgets.spikes([0, 4, 0, 4]) == [False, True, False, True]


def test_spike_months_carry_their_notable_entries_newest_first_capped_at_three(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    history = widgets.exploitation_history(conn, now=SYNTHETIC_FETCH)

    flagged = {m.month: m for m in history.months if m.spike}
    assert list(flagged) == ["2026-03"]
    # March's notable entries: in a product people use (Windows, iOS, Chrome) or known to be
    # used by ransomware (Windows, FortiOS). Four qualify; the newest three are kept. The
    # Danfoss and Ivanti entries are neither.
    # The title drops CISA's leading vendor and product, which the organisation already names;
    # the full name is kept beside it.
    assert [
        (n.cve, n.organization, n.title, n.name, n.people_use, n.ransomware)
        for n in flagged["2026-03"].notable
    ] == [
        (
            "CVE-0000-0306",
            "Windows",
            "Use-After-Free Vulnerability",
            "Microsoft Windows Use-After-Free Vulnerability",
            True,
            True,
        ),
        (
            "CVE-0000-0305",
            "FortiOS",
            "Heap Overflow Vulnerability",
            "Fortinet FortiOS Heap Overflow Vulnerability",
            False,
            True,
        ),
        (
            "CVE-0000-0303",
            "iOS",
            "Memory Corruption Vulnerability",
            "Apple iOS Memory Corruption Vulnerability",
            True,
            False,
        ),
    ]
    assert all(m.notable == [] for m in history.months if not m.spike)


def test_the_real_samples_month_is_a_spike_with_nothing_notable(conn):
    ingest(conn, KEV, real_sample("cisa-kev.json"), fetched_at=REAL_FETCH)

    [november] = [m for m in widgets.exploitation_history(conn, now=REAL_FETCH).months if m.spike]

    # 3 against eleven empty months. HPE/Juniper session routers, Vates Xen Orchestra and a
    # Danfoss controller are not on the "people use" list and none is marked "Known" ransomware.
    assert november.month == "2026-11"
    assert november.notable == []


@pytest.mark.parametrize(
    ("name", "vendor", "product", "title"),
    [
        # Real CISA names (the real KEV sample and the live catalog of 2026-11-25).
        (
            (
                "Hewlett Packard Enterprise (HPE) Juniper Session Smart Conductor and Session Smart"
                " Router OS Command Injection Vulnerability"
            ),
            "Hewlett Packard Enterprise (HPE)",
            "Juniper Session Smart Conductor and Session Smart Router",
            "OS Command Injection Vulnerability",
        ),
        (
            "Google Chromium V8 Out of Bounds Write Vulnerability",
            "Google",
            "Chromium V8",
            "Out of Bounds Write Vulnerability",
        ),
        (
            (
                "WordPress WordPress Core Time-of-check Time-of-use (TOCTOU) Race Condition"
                " Vulnerability"
            ),
            "WordPress",
            "WordPress Core",
            "Time-of-check Time-of-use (TOCTOU) Race Condition Vulnerability",
        ),
        # Hand-written: a name that does not start with its vendor is kept whole.
        (
            "Log4j Remote Code Execution Vulnerability",
            "Apache",
            "Log4j2",
            "Log4j Remote Code Execution Vulnerability",
        ),
    ],
)
def test_a_notable_title_drops_the_vendor_and_product_cisa_puts_first(name, vendor, product, title):
    assert widgets.short_title(name, vendor, product) == title


# --- recently exploited -------------------------------------------------------------------------


def test_recently_exploited_lists_the_newest_entries_in_products_people_use(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    flaws = widgets.recently_exploited(conn)

    # "Office" alone is not an alias in the catalog, so the January entry does not qualify;
    # FortiOS, Ivanti, Cisco, Danfoss, Zimbra and Oracle are not products people use.
    assert [(f.cve, f.product, f.logo_key, f.added_on) for f in flaws] == [
        ("CVE-0000-0601", "Firefox", "firefox", date(2026, 6, 3)),
        ("CVE-0000-0306", "Windows", "windows", date(2026, 3, 24)),
        ("CVE-0000-0303", "iOS", "ios", date(2026, 3, 12)),
        ("CVE-0000-0302", "Chrome", "chrome", date(2026, 3, 5)),
    ]


def test_recently_exploited_is_empty_when_no_listed_entry_is_in_a_product_people_use(conn):
    ingest(conn, KEV, real_sample("cisa-kev.json"), fetched_at=REAL_FETCH)

    assert widgets.recently_exploited(conn) == []


def test_recently_exploited_is_capped(conn):
    ingest(conn, KEV, synthetic_sample("kev-history.json"), fetched_at=SYNTHETIC_FETCH)

    assert [f.cve for f in widgets.recently_exploited(conn, limit=2)] == [
        "CVE-0000-0601",
        "CVE-0000-0306",
    ]


# --- most reported organisations ----------------------------------------------------------------

AFTER_THE_SAMPLES = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)


def ingest_feed_samples(conn):
    for source_id in (
        "bleepingcomputer",
        "therecord",
        "securityaffairs",
        "darkreading",
        "thehackernews",
        "securityweek",
        "krebsonsecurity",
        "ransomware-live",
        "cisa-advisories",
    ):
        ingest(conn, by_id(source_id), real_sample(f"{source_id}.xml"), fetched_at=REAL_FETCH)
    ingest(
        conn,
        by_id("securityweek"),
        synthetic_sample("press-on-a-ransomware-claim.xml"),
        fetched_at=REAL_FETCH,
    )


def test_most_reported_counts_distinct_feed_events_per_organisation(conn):
    ingest_feed_samples(conn)

    top = widgets.most_reported(conn, now=AFTER_THE_SAMPLES)

    # One event each, most recent event first. Leaving out: the two Ransomware.live claims
    # nobody else reported (E Xing Precision Design, TACORP), which are claims, not reports;
    # commentary; research (Gmail, Optimizely); and flaws in products outside the "people use"
    # list (Drupal twice, Juniper, Palo Alto Networks, HPE), which appear in no feed tab.
    # Exceptional Healthcare counts: a press outlet reported the attack the group claimed.
    assert [(o.name, o.count) for o in top] == [
        ("Exceptional Healthcare Inc.", 1),
        ("Flight Centre", 1),
        ("1Password", 1),
        ("FIFA", 1),
        (".NET", 1),
    ]
    assert [(o.key, o.logo_key) for o in top][2] == ("1password", "1password")


def test_most_reported_ranks_by_count_inside_the_last_thirty_days(conn):
    ingest_feed_samples(conn)
    ingest(
        conn,
        by_id("bleepingcomputer"),
        synthetic_sample("most-reported.xml"),
        fetched_at=REAL_FETCH,
    )

    top = widgets.most_reported(conn, now=AFTER_THE_SAMPLES)

    # Contoso Pharmacy: 2 events inside the window (10 and 20 November); the 1 October one is
    # older than 30 days. Five places, so .NET (the oldest single event) drops off.
    assert [(o.name, o.count) for o in top] == [
        ("Contoso Pharmacy", 2),
        ("Exceptional Healthcare Inc.", 1),
        ("Flight Centre", 1),
        ("1Password", 1),
        ("FIFA", 1),
    ]


def test_most_reported_is_empty_when_nothing_was_reported_in_the_window(conn):
    ingest_feed_samples(conn)

    assert widgets.most_reported(conn, now=datetime(2027, 1, 15, tzinfo=UTC)) == []
