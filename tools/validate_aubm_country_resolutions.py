#!/usr/bin/env python3
"""Focused release gate for the country-specific peace system."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from generate_aubm_country_resolutions import BASE_ID, COUNTRIES, MAJOR_EVENTS, OUTPUT, render


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
    expected_count = len(COUNTRIES) * 2 + len(MAJOR_EVENTS)
    if len(ids) != expected_count or len(ids) != len(set(ids)):
        errors.append(f"expected {expected_count} unique events, found {len(ids)}")
    if actual.count("\tdecision = {") != len(COUNTRIES) + len(MAJOR_EVENTS):
        errors.append("one or more countries lacks exactly one visible peace decision")

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
