#!/usr/bin/env python3
"""Sustained money and manpower regression gate for a clean V4 campaign."""

from __future__ import annotations

import pathlib
import re
import sys

from analyze_v4_opening import (
    OPTIONAL_1934,
    V3_OPENING,
    V4_1933,
    V4_1934,
    apply_choices,
    event_records,
    scenario_value,
)
from validate_v4 import extract_blocks, load_text, scalar


ROOT = pathlib.Path(__file__).resolve().parents[1]
DAILY_REVENUE = 2
ANNUAL_BUDGET = 700
ANNUAL_DISCRETIONARY_SPEND = 1300
ANNUAL_RESERVE_BASE = 150
LEAN_POLICY_BONUS = 50
TYPICAL_POLICY_BONUS = 100


def event_action(event: str, letter: str) -> str:
    actions = extract_blocks(event, f"action_{letter}")
    if not actions:
        raise ValueError(f"Event has no action_{letter}.")
    return actions[0].text


def resource_command(action: str, command_type: str) -> list[int]:
    values: list[int] = []
    for command in extract_blocks(action, "command"):
        if (scalar(command.text, "type") or "").lower() != command_type:
            continue
        value = scalar(command.text, "value")
        if value is not None:
            values.append(int(float(value)))
    return values


def main() -> int:
    records = event_records(ROOT)
    scenario = load_text(ROOT / "mod/scenarios/1933/british raj.inc")
    opening = {
        "money": scenario_value(scenario, "money"),
        "supplies": scenario_value(scenario, "supplies"),
        "manpower": scenario_value(scenario, "manpower"),
    }
    active_flags: set[str] = set()
    opening = apply_choices(opening, records, V3_OPENING, active_flags)
    opening = apply_choices(opening, records, V4_1933, active_flags)
    opening = apply_choices(opening, records, V4_1934, active_flags)
    opening = apply_choices(opening, records, OPTIONAL_1934, active_flags)

    errors: list[str] = []
    revenue_action = event_action(records[9280316], "a")
    revenue = resource_command(revenue_action, "free_money")
    if revenue != [DAILY_REVENUE]:
        errors.append(f"Revenue service is {revenue}, expected +{DAILY_REVENUE} money daily.")

    budget_action = event_action(records[9280311], "a")
    positive_budget = [value for value in resource_command(budget_action, "money") if value > 0]
    if positive_budget != [ANNUAL_BUDGET]:
        errors.append(f"Conservative annual budget is {positive_budget}, expected +{ANNUAL_BUDGET} money.")

    reserve_action = event_action(records[9280840], "a")
    reserve_values = resource_command(reserve_action, "manpowerpool")
    if not reserve_values or reserve_values[0] != ANNUAL_RESERVE_BASE:
        errors.append(
            f"Annual reserve base is {reserve_values[:1]}, expected {ANNUAL_RESERVE_BASE} manpower."
        )

    production_lines = 0
    serial_errors = 0
    for event in records.values():
        for command in extract_blocks(event, "command"):
            if (scalar(command.text, "type") or "").lower() != "build_division":
                continue
            production_lines += 1
            if scalar(command.text, "when") != "1":
                serial_errors += 1
    if serial_errors:
        errors.append(f"{serial_errors} event production line(s) still reserve hidden serial manpower.")

    cash = opening["money"]
    cash_floor = cash
    annual_rows: list[tuple[int, int]] = []
    for year in range(1934, 1946):
        cash += DAILY_REVENUE * 365 + ANNUAL_BUDGET - ANNUAL_DISCRETIONARY_SPEND
        cash_floor = min(cash_floor, cash)
        annual_rows.append((year, cash))
    if cash_floor < 800:
        errors.append(
            f"Sustained cash stress floor is {cash_floor}; expected at least 800 after annual spending."
        )

    six_year_lean = 6 * (ANNUAL_RESERVE_BASE + LEAN_POLICY_BONUS)
    six_year_typical = 6 * (ANNUAL_RESERVE_BASE + TYPICAL_POLICY_BONUS)
    if six_year_lean < 650 or six_year_typical < 800:
        errors.append("The 1934-39 reserve classes do not support a great-power expansion path.")

    print("A Union Before Midnight V4 sustained resource audit")
    print(f"  Conservative post-opening cash: {opening['money']}")
    print(
        "  Annual stress model: "
        f"+{DAILY_REVENUE * 365} revenue, +{ANNUAL_BUDGET} budget, "
        f"-{ANNUAL_DISCRETIONARY_SPEND} discretionary spending"
    )
    print(f"  1945 stress-model cash: {annual_rows[-1][1]}")
    print(f"  Cash floor: {cash_floor}")
    print(f"  1934-39 lean reserve intake: {six_year_lean}")
    print(f"  1934-39 typical reserve intake: {six_year_typical}")
    print(f"  Event production contracts: {production_lines}, all single-unit required")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("V4 SUSTAINED RESOURCE GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
