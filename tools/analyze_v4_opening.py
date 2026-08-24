#!/usr/bin/env python3
"""Regression gate for the 1933-34 AUBM money and supply ledger."""

from __future__ import annotations

import pathlib
import re
import sys

from validate_v4 import extract_blocks, load_text, scalar


ROOT = pathlib.Path(__file__).resolve().parents[1]
V3_OPENING = {
    9270000: "a",
    9270002: "a",
    9270001: "a",
    9270100: "b",
    9270101: "b",
    9271000: "a",
    9271200: "a",
    9271201: "a",
    9271300: "a",
    9271301: "a",
    9271302: "a",
    9271303: "b",
    9271400: "a",
}
V4_1933 = {
    9280000: "a",
    9280100: "a",
    9280101: "a",
    9280102: "a",
    9280103: "a",
    9280104: "a",
    9280105: "a",
    9280106: "a",
    9280107: "a",
    9280300: "a",
    9280301: "a",
    9280150: "a",
    9281000: "a",
}
V4_1934 = {
    9280108: "a",
    9280111: "a",
    9280112: "a",
    9280113: "a",
    9280302: "a",
    9280151: "a",
}
OPTIONAL_1934 = {9280152: "a"}
RESOURCE_COMMANDS = {
    "money": "money",
    "supplies": "supplies",
    "manpowerpool": "manpower",
}


def scenario_value(text: str, key: str) -> int:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(-?\d+)", text, re.I)
    if not match:
        raise ValueError(f"Scenario does not define {key}.")
    return int(match.group(1))


def event_records(root: pathlib.Path) -> dict[int, str]:
    records: dict[int, str] = {}
    for relative in ("mod/db/events/india_v3", "mod/db/events/aubm_v4"):
        for path in sorted((root / relative).glob("*.txt")):
            for event in extract_blocks(load_text(path), "event"):
                event_id = scalar(event.text, "id")
                if event_id and event_id.isdigit():
                    records[int(event_id)] = event.text
    return records


def action_delta(event: str, letter: str) -> dict[str, int]:
    actions = extract_blocks(event, f"action_{letter}")
    if not actions:
        raise ValueError(f"Event has no action_{letter}.")
    delta = {"money": 0, "supplies": 0, "manpower": 0}
    for command in extract_blocks(actions[0].text, "command"):
        command_type = (scalar(command.text, "type") or "").lower()
        resource = RESOURCE_COMMANDS.get(command_type)
        value = scalar(command.text, "value")
        if resource and value:
            delta[resource] += int(float(value))
    return delta


def apply_choices(
    ledger: dict[str, int],
    records: dict[int, str],
    choices: dict[int, str],
) -> dict[str, int]:
    updated = dict(ledger)
    for event_id, letter in choices.items():
        if event_id not in records:
            raise ValueError(f"Missing opening event {event_id}.")
        for resource, value in action_delta(records[event_id], letter).items():
            updated[resource] += value
    return updated


def main() -> int:
    scenario = load_text(ROOT / "mod/scenarios/1933/british raj.inc")
    start = {
        "money": scenario_value(scenario, "money"),
        "supplies": scenario_value(scenario, "supplies"),
        "manpower": scenario_value(scenario, "manpower"),
    }
    records = event_records(ROOT)
    after_v3 = apply_choices(start, records, V3_OPENING)
    end_1933 = apply_choices(after_v3, records, V4_1933)
    end_1934 = apply_choices(end_1933, records, V4_1934)
    with_security = apply_choices(end_1934, records, OPTIONAL_1934)

    print("A Union Before Midnight V4 opening ledger")
    print(f"  Start: {start}")
    print(f"  After V3 opening commitments and V4 1933: {end_1933}")
    print(f"  After default 1934 institutions: {end_1934}")
    print(f"  With optional full airfield-security act: {with_security}")
    print("  Daily production and trade income are deliberately excluded.")

    errors: list[str] = []
    if end_1933["money"] < 1400:
        errors.append("Default opening leaves less than 1400 money before 1934 institutions.")
    if end_1933["supplies"] < 750:
        errors.append("Default opening leaves less than 750 supplies before 1934 institutions.")
    if end_1934["money"] < 1000:
        errors.append("Default 1934 institutions leave less than 1000 money before daily income.")
    if with_security["money"] < 800 or with_security["supplies"] < 450:
        errors.append("Optional airfield security makes the static opening ledger insolvent.")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("V4 OPENING ECONOMY GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
