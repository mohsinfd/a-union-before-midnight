#!/usr/bin/env python3
"""Regression gate for the AUBM fresh-1933 opening and old-save split."""

from __future__ import annotations

import pathlib
import re
import sys

from validate_v4 import extract_blocks, load_text, scalar


ROOT = pathlib.Path(__file__).resolve().parents[1]
FRESH_FLAG = "ind_aubm_fresh_1933_bootstrap"
EVENT_DIRS = (
    ROOT / "mod/db/events/india_v3",
    ROOT / "mod/db/events/aubm_v4",
)
FRESH_EXCLUDED_REPAIRS = {
    9270792,
    9280000,
    9280315,
    9280800,
    9281000,
    9281900,
    9281949,
    9283200,
    9287613,
}
FRESH_ONLY_RETIRED = {9270306, 9270340}
INTRO_FLAGS = {
    "ind_v3_sovereignty_proclaimed",
    "ind_v4_direct_dh",
    "ind_v4_initialized",
    "ind_v32_roster_compatibility",
    "ind_v4_inherited_service_baseline",
    "ind_v41_strategy_ledger_reconciled",
    "ind_v43_war_cabinet",
    "ind_v43_upgrade_contract_final",
    "ind_v43_upgrade_contract_low_ic",
    "ind_v43_modernization_contract",
    "ind_v43_unit_build_restore",
    "ind_aubm_wartime_framework",
    "ind_aubm_route_sovereign",
    "ind_aubm_legacy_wartime_retired",
    "ind_aubm_commitment_migration_alpha20",
    "ind_aubm_southern_refusal_migration_alpha20",
}
UNION_FLAGS = {
    "ind_v3_integrated",
    "aubm_v4_union_register_opened",
    "aubm_v4_integration_active",
}


def events() -> dict[int, str]:
    records: dict[int, str] = {}
    for directory in EVENT_DIRS:
        for path in sorted(directory.glob("*.txt")):
            for event in extract_blocks(load_text(path), "event"):
                event_id = scalar(event.text, "id")
                if event_id and event_id.isdigit():
                    records[int(event_id)] = event.text
    return records


def action(event: str, letter: str = "a") -> str:
    actions = extract_blocks(event, f"action_{letter}")
    if not actions:
        raise ValueError(f"event has no action_{letter}")
    return actions[0].text


def command_values(action_text: str, command_type: str) -> list[int]:
    values: list[int] = []
    for command in extract_blocks(action_text, "command"):
        if (scalar(command.text, "type") or "").lower() != command_type:
            continue
        value = scalar(command.text, "value")
        if value is not None:
            values.append(int(float(value)))
    return values


def setflags(action_text: str) -> set[str]:
    result: set[str] = set()
    for command in extract_blocks(action_text, "command"):
        if (scalar(command.text, "type") or "").lower() == "setflag":
            flag = scalar(command.text, "which")
            if flag:
                result.add(flag)
    return result


def sleep_targets(event: str) -> set[int]:
    result: set[int] = set()
    for command in extract_blocks(action(event), "command"):
        if (scalar(command.text, "type") or "").lower() != "sleepevent":
            continue
        target = scalar(command.text, "which")
        if target and target.isdigit():
            result.add(int(target))
    return result


def main() -> int:
    records = events()
    scenario = load_text(ROOT / "mod/scenarios/1933.eug")
    errors: list[str] = []
    checks = 0

    checks += 1
    if not re.search(rf"(?m)^\s*{re.escape(FRESH_FLAG)}\s*=\s*1\s*$", scenario):
        errors.append("1933 scenario does not seed the fresh-start marker")

    scenario_sleepers: set[int] = set()
    for block in extract_blocks(scenario, "sleepevent"):
        scenario_sleepers.update(int(item) for item in re.findall(r"\b\d+\b", block.text))
    legacy_sleepers = sleep_targets(records[9281900]) | sleep_targets(records[9283200])
    expected_sleepers = legacy_sleepers | FRESH_ONLY_RETIRED
    checks += 4
    if len(legacy_sleepers) != 216:
        errors.append(f"legacy retirement source contract has {len(legacy_sleepers)} targets, expected 216")
    if len(expected_sleepers) != 218:
        errors.append(f"fresh retirement contract has {len(expected_sleepers)} targets, expected 218")
    missing_sleepers = expected_sleepers - scenario_sleepers
    if missing_sleepers:
        errors.append(
            "fresh scenario does not pre-sleep all retired events: "
            + ", ".join(str(item) for item in sorted(missing_sleepers))
        )
    unexpected_sleepers = scenario_sleepers - expected_sleepers
    if unexpected_sleepers:
        errors.append(
            "fresh scenario contains unreviewed sleeper IDs: "
            + ", ".join(str(item) for item in sorted(unexpected_sleepers))
        )

    intro_action = action(records[9270000])
    checks += 4
    if not re.search(rf"\bflag\s*=\s*{FRESH_FLAG}\b", records[9270000]):
        errors.append("9270000 is not restricted to the fresh 1933 scenario")
    if sum(command_values(intro_action, "money")) != 1000:
        errors.append("9270000 must contain the single fresh +1000 money grant")
    if sum(command_values(intro_action, "manpowerpool")) != 250:
        errors.append("9270000 must contain the single fresh +250 manpower grant")
    missing_intro_flags = INTRO_FLAGS - setflags(intro_action)
    if missing_intro_flags:
        errors.append("9270000 is missing fresh state flags: " + ", ".join(sorted(missing_intro_flags)))

    for event_id in sorted(FRESH_EXCLUDED_REPAIRS):
        checks += 1
        event = records.get(event_id)
        if event is None:
            errors.append(f"missing repair event {event_id}")
            continue
        if not re.search(
            rf"NOT\s*=\s*\{{\s*flag\s*=\s*{re.escape(FRESH_FLAG)}\s*\}}",
            event,
        ):
            errors.append(f"repair event {event_id} is not excluded from fresh 1933 campaigns")

    for event_id in (9280000, 9281000):
        repair_action = action(records[event_id])
        for command_type in ("money", "manpowerpool"):
            checks += 1
            if command_values(repair_action, command_type):
                errors.append(f"old-save repair {event_id} still grants {command_type}")

    union = records[9270001]
    for letter in ("a", "b", "c"):
        checks += 1
        missing = UNION_FLAGS - setflags(action(union, letter))
        if missing:
            errors.append(f"9270001 action_{letter} is missing flags: {', '.join(sorted(missing))}")

    war_cabinet = records[9281001]
    for block_name in ("decision", "decision_trigger"):
        checks += 1
        blocks = extract_blocks(war_cabinet, block_name)
        if not blocks or not all(
            re.search(rf"\bflag\s*=\s*{flag}\b", blocks[0].text)
            for flag in ("ind_v3_integrated", "aubm_v4_union_register_opened")
        ):
            errors.append(f"9281001 {block_name} can open before the Union settlement")

    for event_id in (9281002, 9281003, 9281004):
        checks += 1
        retired = records[event_id]
        retired_actions = sum(
            (extract_blocks(retired, f"action_{letter}") for letter in "abcd"),
            [],
        )
        commands = [
            command
            for retired_action in retired_actions
            for command in extract_blocks(retired_action.text, "command")
        ]
        safe_redirect = (
            re.search(r"\bone_action\s*=\s*yes\b", retired)
            and len(retired_actions) == 1
            and len(commands) == 1
            and (scalar(commands[0].text, "type") or "").lower() == "event"
            and scalar(commands[0].text, "which") == "9281001"
            and all(
                re.search(rf"\bflag\s*=\s*{flag}\b", commands[0].text)
                for flag in ("ind_v3_integrated", "aubm_v4_union_register_opened")
            )
            and not re.search(r"\btype\s*=\s*war\b", retired)
        )
        if not safe_redirect:
            errors.append(f"retired War Cabinet event {event_id} is not a safe one-action redirect")

    # Fresh campaigns must use the reserved V4 families (and therefore their
    # distinct model/sprite slots), while upgraded saves still receive a
    # symmetric guard if either old or new decision was already taken.
    for v4_id, legacy_id, legacy_flag, commissioned_flag in (
        (9281800, 9270306, "ind_v3_gurkha_arm", "ind_aubm_gurkha_rifles_commissioned"),
        (9281801, 9270340, "ind_v3_frontier_force", "ind_aubm_frontier_force_commissioned"),
    ):
        checks += 3
        v4_decision = extract_blocks(records[v4_id], "decision")[0].text
        legacy_decision = extract_blocks(records[legacy_id], "decision")[0].text
        if not re.search(rf"NOT\s*=\s*\{{\s*flag\s*=\s*{legacy_flag}\s*\}}", v4_decision):
            errors.append(f"V4 unit event {v4_id} does not guard legacy flag {legacy_flag}")
        if legacy_flag not in setflags(action(records[v4_id])):
            errors.append(f"V4 unit event {v4_id} does not close legacy event {legacy_id}")
        if not re.search(
            rf"NOT\s*=\s*\{{\s*flag\s*=\s*{commissioned_flag}\s*\}}",
            legacy_decision,
        ):
            errors.append(f"legacy unit event {legacy_id} does not guard V4 flag {commissioned_flag}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"AUBM cold-start validation failed ({checks} checks, {len(errors)} errors).")
        return 1
    print(
        "AUBM cold-start validation passed "
        f"({checks} checks, {len(legacy_sleepers)} legacy events and "
        f"{len(FRESH_ONLY_RETIRED)} generic unit decisions pre-slept)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
