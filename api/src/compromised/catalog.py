"""The curated alias dictionary (data/catalog.json): vendors, products and services.

Each organization entry carries its aliases, its vendor, whether it is a product people use
(the flag that gates vulnerabilities into the feed) and a logo key for the web app. The file
also lists threat actors and reporters, which are never the affected organization.
"""

import json
import re
from dataclasses import dataclass
from functools import cache
from importlib import resources


@dataclass(frozen=True)
class Organization:
    key: str
    name: str
    aliases: tuple[str, ...]
    vendor: str | None
    people_use: bool
    logo: str


@dataclass(frozen=True)
class ThreatActor:
    name: str
    state_linked: bool


@dataclass(frozen=True)
class Catalog:
    organizations: tuple[Organization, ...]
    threat_actors: tuple[ThreatActor, ...]
    not_organizations: frozenset[str]

    def by_key(self, key: str) -> Organization | None:
        return _index(self).get(key)

    def by_name(self, name: str) -> Organization | None:
        """The entry one of whose aliases is exactly ``name`` (case-insensitive), if any."""
        return _alias_index(self).get(name.strip().casefold())

    def first_in(self, text: str) -> Organization | None:
        """The organization named earliest in ``text`` (longest alias wins at one position).

        A match that opens the text and is followed by a colon ("Microsoft: China's hackers...")
        is the speaker, not the subject, and is skipped.
        """
        for match in _alias_pattern(self).finditer(text):
            if match.start() == 0 and text[match.end() :].startswith(":"):
                continue
            return _alias_index(self)[match.group(0).casefold()]
        return None

    def actors_in(self, text: str) -> list[ThreatActor]:
        return [a for a in self.threat_actors if _whole_word(a.name).search(text)]

    def is_not_organization(self, name: str) -> bool:
        folded = name.strip().casefold()
        return folded in {n.casefold() for n in self.not_organizations} or any(
            a.name.casefold() == folded for a in self.threat_actors
        )


@cache
def load() -> Catalog:
    raw = json.loads(
        resources.files("compromised").joinpath("data", "catalog.json").read_text("utf-8")
    )
    return Catalog(
        organizations=tuple(
            Organization(
                key=o["key"],
                name=o["name"],
                aliases=tuple(o["aliases"]),
                vendor=o["vendor"],
                people_use=o["people_use"],
                logo=o["logo"],
            )
            for o in raw["organizations"]
        ),
        threat_actors=tuple(
            ThreatActor(name=a["name"], state_linked=a["state_linked"])
            for a in raw["threat_actors"]
        ),
        not_organizations=frozenset(raw["not_organizations"]),
    )


def _whole_word(alias: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)")


@cache
def _index(catalog: Catalog) -> dict[str, Organization]:
    return {o.key: o for o in catalog.organizations}


@cache
def _alias_index(catalog: Catalog) -> dict[str, Organization]:
    return {alias.casefold(): o for o in catalog.organizations for alias in o.aliases}


@cache
def _alias_pattern(catalog: Catalog) -> re.Pattern[str]:
    aliases = sorted(
        {a for o in catalog.organizations for a in o.aliases}, key=lambda a: (-len(a), a)
    )
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in aliases) + r")(?!\w)")
