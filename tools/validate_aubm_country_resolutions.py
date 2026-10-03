#!/usr/bin/env python3
"""Focused release gate for the country-specific peace system."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from generate_aubm_country_resolutions import (
    BASE_ID,
    COUNTRIES,
    FRAGMENT_CALLBACKS,
    FRAGMENT_PLANS,
    ISLAND_DEFENSES,
    MAJOR_EVENTS,
    OUTPUT,
    render,
)


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "mod/db/events.txt"
RETIRED = {
    "42_wartime_theatres.txt",
    "43_wartime_settlements.txt",
    "45_enemy_campaigns.txt",
    "46_regional_campaigns.txt",
    "47_global_campaign_matrix.txt",
    "48_route_wartime_consequences.txt",
    "49_bespoke_armistices.txt",
    "50_southeast_asia_operations.txt",
    "51_bespoke_route_arcs.txt",
}
FORBIDDEN = re.compile(r"\b(theatre|theater|report|ledger|docket|board|provisional|regional)\b", re.I)


def balanced(text: str) -> bool:
    depth = 0
    quoted = False
    for char in text:
        if char == '"':
            quoted = not quoted
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not quoted


def main() -> int:
    errors: list[str] = []
    expected = render()
    actual = OUTPUT.read_text(encoding="ascii") if OUTPUT.exists() else ""
    index = INDEX.read_text(encoding="cp1252")

    if actual != expected:
        errors.append("53_country_resolutions.txt is stale; run its generator")
    if not balanced(actual):
        errors.append("country-resolution braces or quotes are unbalanced")
    if 'event = "db\\events\\aubm_v4\\53_country_resolutions.txt"' not in index:
        errors.append("country-resolution module is not loaded")
    for name in sorted(RETIRED):
        if name in index:
            errors.append(f"retired module remains loaded: {name}")
        if (OUTPUT.parent / name).exists():
            errors.append(f"retired module remains packaged: {name}")

    ids = [int(value) for value in re.findall(r"(?m)^\s*id\s*=\s*(\d+)", actual)]
    base_callbacks = sum(bool(country.retained_bases) for country in COUNTRIES)
    bespoke_events = 37  # Malaya, Arab, Soviet and island-defence chains.
    expected_count = (
        len(COUNTRIES) * 2 + len(MAJOR_EVENTS) + len(FRAGMENT_CALLBACKS)
        + len(FRAGMENT_PLANS) + base_callbacks + bespoke_events
    )
    if len(ids) != expected_count or len(ids) != len(set(ids)):
        errors.append(f"expected {expected_count} unique events, found {len(ids)}")
    visible_decisions = len(COUNTRIES) + len(MAJOR_EVENTS) + 2
    if actual.count("\tdecision = {") != visible_decisions:
        errors.append("one or more countries lacks exactly one visible peace decision")
    if actual.count("\ttrigger = { ai = no }") != visible_decisions:
        errors.append("one or more visible peace decisions lacks its event-level human-player guard")
    if re.search(r"(?m)^\s*decision(?:_trigger)?\s*=\s*\{\s*ai\s*=", actual):
        errors.append("ai guard is incorrectly nested inside decision or decision_trigger")
    dated_events = visible_decisions + 2 + len(ISLAND_DEFENSES)
    daily_events = visible_decisions + 2  # Decisions plus both Alpha 33 recovery events.
    if actual.count("\tdate = { day = 0 month = january year = 1933 }") != dated_events:
        errors.append("one or more visible peace decisions lacks its polling start date")
    if actual.count("\toffset = 1") != daily_events:
        errors.append("one or more visible peace decisions is not polled daily")
    if actual.count("\tdeathdate = { day = 29 month = december year = 1964 }") != dated_events:
        errors.append("one or more visible peace decisions lacks its scenario-long deathdate")
    if actual.count("\toffset = 5") != len(ISLAND_DEFENSES):
        errors.append("one or more global island-defence events lacks its five-day polling interval")

    visible = "\n".join(
        line for line in actual.splitlines()
        if re.match(r"^\s*(name|desc|decision_desc)\s*=", line)
    )
    match = FORBIDDEN.search(visible)
    if match:
        errors.append(f"forbidden bureaucratic word remains in visible text: {match.group(0)}")

    labels = re.findall(r"(?m)^\s*name\s*=\s*\"([^\"]*)\"", actual)
    over = [label for label in labels if len(label.encode("cp1252")) > 58]
    if over:
        errors.append(f"{len(over)} action/title labels exceed 58 bytes; first: {over[0]}")

    for index_number, country in enumerate(COUNTRIES):
        event_id = BASE_ID + index_number * 2
        marker = f"id = {event_id}"
        start = actual.find(marker)
        end = actual.find("\nevent = {", start + len(marker))
        block = actual[start : len(actual) if end < 0 else end]
        if f'{country.name}: Decide the Peace' not in block:
            errors.append(f"{country.tag} has no plainly named decision")
        if f"changes {country.name} only" not in block:
            errors.append(f"{country.tag} does not state its country-only scope")
        protectorate = block.split("action_a = {", 1)[-1].split("action_b = {", 1)[0]
        if re.search(r"type\s*=\s*dissent\s+value\s*=\s*[1-9]", protectorate):
            errors.append(f"{country.tag} protectorate still adds dissent")
        if "supplies value = -250" not in protectorate:
            errors.append(f"{country.tag} protectorate lacks its disclosed supply cost")
        neutral = block.split("action_b = {", 1)[-1].split("action_c = {", 1)[0]
        if "make_puppet" in neutral or "alliance" in neutral:
            errors.append(f"{country.tag} protected neutrality can still create a puppet or alliance")
        if "guarantee which = IND" not in neutral:
            errors.append(f"{country.tag} protected neutrality lacks an Indian guarantee")
        if "ind_country_resolution_" + country.key + "_dismissed" not in block:
            errors.append(f"{country.tag} lacks a permanent-dismiss outcome")

    for country in (item for item in COUNTRIES if item.retained_bases):
        if f'{country.name}: Indian Base Treaty' not in actual:
            errors.append(f"{country.tag} lacks its protectorate base treaty")
        for province, name in country.retained_bases:
            if f"secedeprovince which = IND value = {province} when = 2" not in actual:
                errors.append(f"{country.tag} does not deterministically transfer {name} to India")

    for phrase in (
        "Malaysia: Settle the British Colony",
        "Protectorate; India keeps Singapore",
        "Arab Federation: Unite the Defeated States",
        "Transfer Suez, Aden and Basrah",
        "Dismiss this peace; continue the war",
        "Soviet Union: India Can Dictate a Settlement",
        "Liberation peace: aligned republics; -4 dissent",
        "Island Agreements Corrected",
        "Soerabaja Base Handover Completed",
    ):
        if phrase not in actual:
            errors.append(f"required country-resolution text is missing: {phrase}")

    for island in ISLAND_DEFENSES:
        for phrase in (
            f"{island.name}: Complete the Settlement",
            f"{island.name}: Founding Defence Force",
            f"{island.name}: Indian Defence Mission",
        ):
            if phrase not in actual:
                errors.append(f"island-defence event is missing: {phrase}")

    if "Breakup options: Indonesia, Brunei, Sarawak" not in actual:
        errors.append("East Indies fragmentation choice is missing or unnamed")
    if "Breakup options: Vietnam, Cambodia, Laos" not in actual:
        errors.append("Indochina fragmentation choice is missing or unnamed")
    for phrase in (
        "Active protectorates: -500 supplies; share wars",
        "Protected neutrals: -250 supplies; separate wars",
    ):
        if actual.count(phrase) != len(FRAGMENT_PLANS):
            errors.append(f"fragmentation menus do not disclose both outcomes: {phrase}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"OK: {len(COUNTRIES)} named country settlements, {len(MAJOR_EVENTS)} named major-power peaces; "
        f"{len(RETIRED)} legacy layers purged"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
