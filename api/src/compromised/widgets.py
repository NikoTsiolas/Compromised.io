"""Figures behind the homepage widgets (#15). Read-only: every figure is derived from stored data
when it is asked for, so it can never drift from what it counts.

- Exploited flaws by month: entries added to the whole CISA KEV catalog per calendar month (UTC),
  from the catalog the worker last fetched (storage ``kev_catalog_entries``), not from feed
  events, which hold only the last 30 days.
- The spike rule (``SPIKE_RULE``), applied here so the API and the chart agree.
- Recently exploited: the newest catalog entries in a product on the "people use" list.
- Most reported organisations: distinct feed events per organisation over the last 30 days.

Trending belongs to ticket #10. The sector and service-outage chart views wait for the owner's
confirmation and are not built.
"""

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import psycopg

from compromised import storage
from compromised.pipeline.extractor import from_structured

SPIKE_RULE = (
    "A month is a spike when its count is at least one standard deviation (population) above"
    " the average of the months shown, provided at least three months are shown and they are"
    " not all equal."
)
NOTABLE_PER_MONTH = 3
RECENTLY_EXPLOITED = 5
MOST_REPORTED = 5
MOST_REPORTED_DAYS = 30


@dataclass(frozen=True)
class Notable:
    cve: str
    title: str  # CISA's vulnerabilityName, unchanged
    organization: str  # the product as the feed names it (catalog name, else CISA's product)
    people_use: bool  # the product is on the curated "people use" list
    ransomware: bool  # CISA marks it as known to be used in ransomware campaigns


@dataclass(frozen=True)
class Month:
    month: str  # "YYYY-MM"
    count: int
    spike: bool
    notable: list[Notable] = field(default_factory=list)  # spike months only


@dataclass(frozen=True)
class CatalogInfo:
    version: str | None
    declared_count: int | None  # what the catalog says its size is
    entries: int  # entries kept from it
    fetched_at: datetime


@dataclass(frozen=True)
class History:
    months: list[Month]  # oldest first; empty until a catalog has been fetched
    catalog: CatalogInfo | None


def spikes(counts: list[int]) -> list[bool]:
    """``SPIKE_RULE`` for each count, in order."""
    n = len(counts)
    if n < 3:
        return [False] * n
    mean = sum(counts) / n
    sd = math.sqrt(sum((c - mean) ** 2 for c in counts) / n)
    if sd == 0:
        return [False] * n
    # A tiny tolerance so a month exactly on the threshold is not lost to rounding.
    return [c >= mean + sd - 1e-9 for c in counts]


def exploitation_history(conn: psycopg.Connection, *, now: datetime, months: int = 12) -> History:
    """The last ``months`` calendar months up to and including the current one, with zeros for
    months that had no additions, each marked by the spike rule over those months."""
    info = storage.kev_catalog_info(conn)
    if info is None:
        return History(months=[], catalog=None)
    last = date(now.year, now.month, 1)
    starts = [_add_months(last, -i) for i in reversed(range(months))]
    counts = storage.kev_monthly_counts(conn, starts[0], last)
    values = [counts.get(m, 0) for m in starts]
    out = []
    for start, count, spike in zip(starts, values, spikes(values), strict=True):
        notable = _notable(conn, start) if spike else []
        out.append(Month(month=start.strftime("%Y-%m"), count=count, spike=spike, notable=notable))
    return History(months=out, catalog=CatalogInfo(**info))


def _notable(conn: psycopg.Connection, month: date) -> list[Notable]:
    """A spike month's entries in a product people use or known to be used by ransomware,
    newest added first, at most ``NOTABLE_PER_MONTH``."""
    out = []
    for e in storage.kev_entries(conn, since=month, before=_add_months(month, 1)):
        affected = from_structured(e["product"], e["vendor"])
        people_use = bool(affected and affected.people_use)
        if not (people_use or e["known_ransomware_use"]):
            continue
        out.append(
            Notable(
                cve=e["cve"],
                title=e["name"],
                organization=affected.name if affected else e["vendor"],
                people_use=people_use,
                ransomware=e["known_ransomware_use"],
            )
        )
        if len(out) == NOTABLE_PER_MONTH:
            break
    return out


@dataclass(frozen=True)
class ExploitedFlaw:
    cve: str
    product: str  # as the feed names it (the catalog's name)
    logo_key: str | None
    added_on: date  # dateAdded: when CISA listed it as exploited


def recently_exploited(conn: psycopg.Connection, limit: int = RECENTLY_EXPLOITED) -> list:
    """The newest KEV entries whose product is on the "people use" list, newest first."""
    out = []
    for e in storage.kev_entries(conn):
        affected = from_structured(e["product"], e["vendor"])
        if not (affected and affected.people_use):
            continue
        out.append(
            ExploitedFlaw(
                cve=e["cve"],
                product=affected.name,
                logo_key=affected.logo,
                added_on=e["date_added"],
            )
        )
        if len(out) == limit:
            break
    return out


@dataclass(frozen=True)
class OrganisationCount:
    name: str
    key: str | None  # catalog key, when the organisation is in the catalog
    logo_key: str | None
    count: int  # distinct events naming it in the window


def most_reported(
    conn: psycopg.Connection,
    *,
    now: datetime,
    days: int = MOST_REPORTED_DAYS,
    limit: int = MOST_REPORTED,
) -> list[OrganisationCount]:
    """Organisations named in the most distinct events published in the last ``days`` days.

    Only events on the main feed count (the All tab): an incident naming the organisation that
    a source other than an attacker reported. So commentary, research, flaws outside the
    "people use" list and attacker claims that no one else reported never count. A claim that
    a news outlet or official source also reported counts once, as a reported event.
    Ties go to the organisation with the more recent event.
    """
    rows = storage.events_per_organisation(
        conn, since=now - timedelta(days=days), until=now, limit=limit
    )
    return [OrganisationCount(**r) for r in rows]


def _add_months(month: date, n: int) -> date:
    index = month.year * 12 + month.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)
