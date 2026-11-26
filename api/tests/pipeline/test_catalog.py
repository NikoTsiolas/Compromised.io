"""The curated alias dictionary is data (src/compromised/data/catalog.json), not code."""

import json
from importlib import resources

from compromised import catalog


def raw_catalog():
    return json.loads(
        resources.files("compromised").joinpath("data", "catalog.json").read_text("utf-8")
    )


def test_every_entry_has_a_logo_key_a_people_use_flag_and_at_least_one_alias():
    entries = raw_catalog()["organizations"]

    assert len(entries) >= 300
    for entry in entries:
        assert set(entry) == {"key", "name", "aliases", "vendor", "people_use", "logo"}, entry
        assert isinstance(entry["people_use"], bool), entry["key"]
        assert isinstance(entry["logo"], str) and entry["logo"], entry["key"]
        assert entry["aliases"], entry["key"]


def test_keys_are_unique_vendors_exist_and_no_alias_points_at_two_entries():
    entries = raw_catalog()["organizations"]
    keys = [e["key"] for e in entries]
    owners: dict[str, set[str]] = {}
    for e in entries:
        for alias in e["aliases"]:
            owners.setdefault(alias.casefold(), set()).add(e["key"])

    assert len(keys) == len(set(keys))
    assert {e["vendor"] for e in entries if e["vendor"]} <= set(keys)
    assert {alias: keys for alias, keys in owners.items() if len(keys) > 1} == {}


def test_the_products_named_in_the_wiki_are_on_the_people_use_list():
    people_use = {o.name for o in catalog.load().organizations if o.people_use}

    assert {"Windows", "iPhone", "Android", "Chrome", "TP-Link", "Netgear", "WhatsApp"} <= (
        people_use
    )


def test_ordinary_words_that_are_also_brand_names_do_not_match_on_their_own():
    found = catalog.load().first_in

    assert found("Attackers Target .NET Developers With Poisoned Job Assessments").name == ".NET"
    assert found("A Ring of Scammers Sends an Early Signal to X") is None
