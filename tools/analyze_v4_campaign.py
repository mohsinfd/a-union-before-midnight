#!/usr/bin/env python3
"""Cold-start campaign audit for A Union Before Midnight V4.

This complements the parser validator with player-facing checks: prewar event
cadence, structural choice diversity, world-state effects, research inheritance,
leader capacity, automatic cash drains, and brittle flag-only chains.
"""

from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import Counter, defaultdict

from validate_v4 import extract_blocks, load_text, scalar, strip_comments


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENT_DIRS = (
    ROOT / "mod/db/events/india_v3",
    ROOT / "mod/db/events/aubm_v4",
)
WORLD_COMMANDS = {
    "access",
    "alliance",
    "end_mastery",
    "end_trades",
    "guarantee",
    "inherit",
    "independence",
    "make_puppet",
    "non_aggression",
    "peace",
    "secedearea",
    "secedeprovince",
    "secederegion",
    "war",
}
FORCE_COMMANDS = {
    "activate_unit_type",
    "add_corps",
    "add_division",
    "build_division",
    "new_model",
}
INSTITUTION_COMMANDS = {
    "add_leader_skill",
    "chiefofair",
    "chiefofarmy",
    "chiefofnavy",
    "chiefofstaff",
    "foreignminister",
    "headofgovernment",
    "headofstate",
    "intelligence",
    "ministerofintelligence",
    "ministerofsecurity",
    "set_leader_skill",
    "wakeleader",
    "waketeam",
}
CAPACITY_COMMANDS = {
    "add_prov_resource",
    "construct",
    "free_money",
    "industrial_modifier",
    "max_organization",
    "morale",
    "repair_mod",
    "research_mod",
    "tc_mod",
}
SOFT_COMMANDS = {
    "belligerence",
    "dissent",
    "domestic",
    "manpowerpool",
    "money",
    "rarematerialspool",
    "relation",
    "supplies",
}
FLOW_COMMANDS = {"clrflag", "event", "setflag", "sleepevent", "sleepleader", "trigger"}
CRITICAL_PREWAR_REACTIONS = {
	9270401: "Commonwealth or German partnership",
	9270402: "Japanese or independent Asian partnership",
	9270403: "Delhi-Moscow compact",
    9270450: "Abyssinia",
    9270451: "Spain",
    9270452: "China",
    9270453: "Anschluss",
    9270454: "Munich",
    9270455: "Empires on the March",
    9270456: "War in Europe",
}


def event_records() -> dict[int, tuple[pathlib.Path, str]]:
    records: dict[int, tuple[pathlib.Path, str]] = {}
    for directory in EVENT_DIRS:
        for path in sorted(directory.glob("*.txt")):
            for event in extract_blocks(load_text(path), "event"):
                value = scalar(event.text, "id")
                if value and value.isdigit():
                    records[int(value)] = (path, event.text)
    return records


def event_year(event: str) -> int | None:
    dates = extract_blocks(event, "date")
    if not dates:
        return None
    year = scalar(dates[0].text, "year")
    return int(year) if year and year.isdigit() else None


def actions(event: str) -> list[str]:
    result: list[str] = []
    for letter in "abcdefgh":
        result.extend(block.text for block in extract_blocks(event, f"action_{letter}"))
    return result


def event_trigger(event: str) -> str:
    """Return only the event-level trigger, never an action availability block."""
    preamble = re.split(r"(?m)^\s*(?:action_[a-h]|decision)\s*=", event, maxsplit=1)[0]
    blocks = extract_blocks(preamble, "trigger")
    return blocks[0].text if blocks else ""


def commands(action: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for command in extract_blocks(action, "command"):
        command_type = (scalar(command.text, "type") or "").lower()
        if command_type:
            result.append((command_type, command.text))
    return result


def impact_signature(
    action: str,
    records: dict[int, tuple[pathlib.Path, str]] | None = None,
    seen: frozenset[int] = frozenset(),
) -> frozenset[str]:
    signature: set[str] = set()
    for command_type, text in commands(action):
        if command_type == "event":
            target = scalar(text, "where")
            signature.add("world" if target and target != "IND" else "flow")
        elif command_type in WORLD_COMMANDS:
            signature.add("world")
        elif command_type in FORCE_COMMANDS:
            signature.add("force")
        elif command_type in INSTITUTION_COMMANDS:
            signature.add("institution")
        elif command_type in CAPACITY_COMMANDS:
            signature.add("capacity")
        elif command_type in SOFT_COMMANDS:
            signature.add("soft")
        elif command_type in {"event", "trigger"}:
            signature.add("flow")
            target = scalar(text, "which")
            if records and target and target.isdigit() and int(target) not in seen:
                nested = records.get(int(target))
                if nested:
                    for nested_action in actions(nested[1]):
                        signature.update(
                            impact_signature(
                                nested_action,
                                records,
                                seen | {int(target)},
                            )
                        )
        elif command_type in FLOW_COMMANDS:
            signature.add("flow")
        else:
            signature.add("other")
    return frozenset(signature)


def completed_techs(path: pathlib.Path) -> set[int]:
    text = strip_comments(load_text(path))
    block = extract_blocks(text, "techapps")
    if not block:
        return set()
    return {int(value) for value in re.findall(r"\b\d+\b", block[0].text)}


def leader_capacity(year: int) -> tuple[int, Counter[str]]:
    capacity = 0
    ranks: Counter[str] = Counter()
    path = ROOT / "mod/db/leaders/india.csv"
    with path.open(encoding="cp1252", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        for row in reader:
            if row.get("Country") != "IND" or row.get("Type") != "0":
                continue
            start = int(row["Start Year"])
            end = int(row["End Year"])
            if not start <= year <= end:
                continue
            rank = 3
            for candidate in (0, 1, 2, 3):
                rank_year = int(row[f"Rank {candidate} Year"])
                if rank_year <= year:
                    rank = min(rank, candidate)
            label, command = {
                0: ("General", 12),
                1: ("Lt General", 9),
                2: ("Major General", 3),
                3: ("Brigadier", 1),
            }[rank]
            ranks[label] += 1
            capacity += command
    return capacity, ranks


def main() -> int:
    records = event_records()
    errors: list[str] = []
    cadence: Counter[int] = Counter()
    prewar_world_events: list[int] = []
    prewar_structural_choices: list[int] = []
    soft_only_choices: list[int] = []
    automatic_cash_costs: list[tuple[int, int]] = []
    internal_flag_chains: list[int] = []
    brittle_world_chains: list[int] = []

    for event_id, (_, event) in records.items():
        if scalar(event, "country") != "IND":
            continue
        year = event_year(event)
        event_actions = actions(event)
        signatures = [impact_signature(action, records) for action in event_actions]
        if year and 1933 <= year <= 1939:
            cadence[year] += 1
            if any("world" in signature for signature in signatures):
                prewar_world_events.append(event_id)
            if len(set(signatures)) >= 2 and any(
                signature & {"world", "force", "institution"} for signature in signatures
            ):
                prewar_structural_choices.append(event_id)
            if len(event_actions) >= 2 and all(
                signature <= {"soft", "capacity", "flow"} for signature in signatures
            ):
                soft_only_choices.append(event_id)

        if len(event_actions) == 1 and not extract_blocks(event, "decision"):
            cost = 0
            for command_type, text in commands(event_actions[0]):
                if command_type != "money":
                    continue
                value = scalar(text, "value")
                if value and float(value) < 0:
                    cost += int(float(value))
            if cost:
                automatic_cash_costs.append((event_id, cost))

        trigger_text = strip_comments(event_trigger(event))
        if trigger_text:
            has_flag = bool(re.search(r"(?m)^\s*flag\s*=", trigger_text))
            has_state = bool(
                re.search(
                    r"\b(?:alliance|atwar|control|event|exists|government|lost_national|owned|technology|war)\s*=",
                    trigger_text,
                )
                or re.search(
                    r"\bflag\s*=\s*ind_v3_(?:[a-z_]*orientation|joined_[a-z_]+|"
                    r"non_aligned|independent_asia|[a-z_]*mission)\b",
                    trigger_text,
                )
                or event_year(event) is not None
            )
            if has_flag and not has_state and not extract_blocks(event, "decision"):
                internal_flag_chains.append(event_id)
                if any("world" in signature for signature in signatures):
                    brittle_world_chains.append(event_id)

    india_tech = completed_techs(ROOT / "mod/scenarios/1933/british raj.inc")
    uk_tech = completed_techs(ROOT / "mod/scenarios/1933/united kingdom.inc")
    missing_tech = sorted(uk_tech - india_tech)

    print("A Union Before Midnight V4 cold-start campaign audit")
    print("\nPrewar dated-event cadence")
    for year in range(1933, 1940):
        print(f"  {year}: {cadence[year]} India event(s)")
    print(f"  World-state prewar events: {len(prewar_world_events)}")
    print(f"  Structurally divergent prewar choices: {len(prewar_structural_choices)}")
    print(f"  Soft/capacity-only prewar choices: {len(soft_only_choices)}")

    print("\nResearch inheritance")
    print(f"  India completed techs: {len(india_tech)}")
    print(f"  United Kingdom completed techs: {len(uk_tech)}")
    print(f"  Missing inherited baseline techs: {len(missing_tech)}")

    print("\nHistorical land-command capacity")
    for year in (1933, 1936, 1939, 1942):
        capacity, ranks = leader_capacity(year)
        print(f"  {year}: capacity {capacity}, ranks {dict(ranks)}")

    print("\nContinuity risks")
    print(f"  Unavoidable one-action money costs: {len(automatic_cash_costs)}")
    print(f"  External-effect chains without a state fallback: {len(brittle_world_chains)}")
    print(f"  Internal narrative transitions using ledger flags: {len(internal_flag_chains)}")

    for event_id, label in CRITICAL_PREWAR_REACTIONS.items():
        record = records.get(event_id)
        if not record:
            errors.append(f"Missing critical prewar reaction {event_id} ({label}).")
            continue
        event_actions = actions(record[1])
        if not any("world" in impact_signature(action, records) for action in event_actions):
            errors.append(f"Critical prewar reaction {event_id} ({label}) has no world-state action.")

    if missing_tech:
        errors.append(f"India is missing {len(missing_tech)} British/Raj baseline technologies.")
    if automatic_cash_costs:
        errors.append(f"Automatic events still impose money costs: {automatic_cash_costs}.")
    if len(prewar_world_events) < 8:
        errors.append("Fewer than eight dated 1933-39 India events can alter foreign state.")
    if len(prewar_structural_choices) < 8:
        errors.append("Fewer than eight dated 1933-39 choices have structurally divergent outcomes.")
    capacity_1939, _ = leader_capacity(1939)
    if capacity_1939 < 100:
        errors.append(f"1939 land-command capacity is only {capacity_1939}; target is at least 100.")
    if brittle_world_chains:
        errors.append(
            "External-effect events still depend only on prior flags: "
            + ", ".join(str(value) for value in brittle_world_chains)
        )

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("V4 CAMPAIGN AUDIT PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
