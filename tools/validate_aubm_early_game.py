#!/usr/bin/env python3
"""Regression gate for audited AUBM opening and early-game event contracts."""

from __future__ import annotations

import re
import sys

from validate_aubm_cold_start import action, command_values, events, setflags
from validate_v4 import direct_scalar, extract_blocks, scalar


OPENING_LABELS = {
    (9270000, "a"): "Assume sovereignty: +1000 money, +250 manpower",
    (9270002, "a"): "Gandhi-Nehru: -100 money, -250 supplies, -3 dissent",
    (9270002, "b"): "Patel: -200 money/-400 supplies/-1 dissent; defence reform",
    (9270002, "c"): "Bose: -75 money, -200 supplies, +30 MP, +2 dissent",
    (9270001, "a"): "Negotiate: -150 money, -350 supplies, -10 MP, -5 dissent",
    (9270001, "b"): "Provincial: -75 money, -200 supplies, -3 dissent",
    (9270001, "c"): "Centralize: +150 money, -400 supplies, -5 MP, +4 dissent",
}


def queued_division_types(action_text: str) -> list[str]:
    """Return the ordinary production contracts an action actually queues."""
    return [
        scalar(command.text, "which") or ""
        for command in extract_blocks(action_text, "command")
        if (scalar(command.text, "type") or "").lower() == "build_division"
    ]


def main() -> int:
    records = events()
    errors: list[str] = []
    checks = 0

    for (event_id, letter), expected_label in OPENING_LABELS.items():
        checks += 2
        label = scalar(action(records[event_id], letter), "name") or ""
        if label != expected_label:
            errors.append(
                f"{event_id} action_{letter} label is {label!r}; expected {expected_label!r}"
            )
        if len(label.encode("cp1252")) > 58:
            errors.append(f"{event_id} action_{letter} exceeds the 58-byte UI limit")

    language = records[9270102]
    for letter, expected_reward in (("a", 1), ("c", 2)):
        checks += 2
        selected = action(language, letter)
        actual_rewards = command_values(selected, "research_mod")
        if actual_rewards != [expected_reward]:
            errors.append(
                f"9270102 action_{letter} research reward is {actual_rewards}, "
                f"expected [{expected_reward}]"
            )
        label = scalar(selected, "name") or ""
        if f"+{expected_reward} research" not in label:
            errors.append(f"9270102 action_{letter} does not disclose its research reward")

    air_group = records.get(9280162)
    checks += 27
    if air_group is None:
        errors.append("missing 9280162 First Operational Air Group decision")
    else:
        for required_flag in (
            "ind_v3_air_staff_founded",
            "ind_v3_flying_schools",
            "ind_v4_airfield_security",
        ):
            if not re.search(rf"\bflag\s*=\s*{required_flag}\b", air_group):
                errors.append(f"9280162 is missing prerequisite {required_flag}")
        for blocker in (
            "ind_v4_first_operational_air_group",
            "ind_v3_hal_expansion",
            "ind_v3_air_doctrine_1936",
            "ind_v3_arsenal_air",
        ):
            if not re.search(
                rf"NOT\s*=\s*\{{\s*flag\s*=\s*{blocker}\s*\}}", air_group
            ):
                errors.append(f"9280162 does not block duplicate air package {blocker}")

        if "Airfield security protects aircraft; it does not create them." not in air_group:
            errors.append("9280162 does not explain the security-versus-aircraft split")

        expected_contracts = {
            "a": (["interceptor", "interceptor"], -350, -1250, "ind_v4_first_air_group_fighter"),
            "b": (["interceptor", "tactical_bomber"], -325, -1150, "ind_v4_first_air_group_army"),
            "c": (["interceptor", "naval_bomber"], -325, -1200, "ind_v4_first_air_group_maritime"),
        }
        for letter, (units, money, supplies, doctrine_flag) in expected_contracts.items():
            selected = action(air_group, letter)
            if queued_division_types(selected) != units:
                errors.append(
                    f"9280162 action_{letter} queues {queued_division_types(selected)}, expected {units}"
                )
            if command_values(selected, "money") != [money]:
                errors.append(f"9280162 action_{letter} has the wrong money cost")
            if command_values(selected, "supplies") != [supplies]:
                errors.append(f"9280162 action_{letter} has the wrong supply cost")
            if command_values(selected, "manpowerpool"):
                errors.append(
                    f"9280162 action_{letter} double-charges manpower outside normal production"
                )
            expected_flags = {doctrine_flag, "ind_v4_first_operational_air_group"}
            if not expected_flags.issubset(setflags(selected)):
                errors.append(f"9280162 action_{letter} is missing its one-use doctrine flags")

        doctrine_first = action(air_group, "d")
        if queued_division_types(doctrine_first):
            errors.append("9280162 doctrine-first action queues aircraft")
        if command_values(doctrine_first, "max_organization") != [1]:
            errors.append("9280162 doctrine-first action must grant exactly +1 air organization")
        if command_values(doctrine_first, "manpowerpool"):
            errors.append("9280162 doctrine-first action double-charges manpower")
        if not {
            "ind_v4_first_air_group_doctrine",
            "ind_v4_first_operational_air_group",
        }.issubset(setflags(doctrine_first)):
            errors.append("9280162 doctrine-first action is missing its one-use flags")

    budget = records[9280311]
    credit = action(budget, "c")
    checks += 6
    if scalar(budget, "persistent") != "yes":
        errors.append("9280311 must remain the persistent Union Budget menu")
    credit_actions = extract_blocks(credit, "trigger")
    action_trigger = credit_actions[0].text if credit_actions else ""
    if not re.search(
        r"NOT\s*=\s*\{\s*flag\s*=\s*ind_v4_foreign_credit\s*\}",
        action_trigger,
    ):
        errors.append("9280311 foreign credit action is not limited to the first credit")
    if command_values(credit, "money").count(1100) != 1:
        errors.append("9280311 foreign credit does not grant exactly one advertised +1100")

    foreign_charges = []
    set_credit = []
    for command in extract_blocks(credit, "command"):
        command_type = direct_scalar(command.text, "type")
        triggers = extract_blocks(command.text, "trigger")
        if (
            command_type == "money"
            and direct_scalar(command.text, "value") == "-175"
            and triggers
            and re.search(r"\bflag\s*=\s*ind_v4_foreign_credit\b", triggers[0].text)
        ):
            foreign_charges.append(command)
        if command_type == "setflag" and scalar(command.text, "which") == "ind_v4_foreign_credit":
            set_credit.append(command)
    if len(foreign_charges) != 1:
        errors.append(
            f"9280311 foreign-credit service charge occurs {len(foreign_charges)} times, expected one"
        )
    if len(set_credit) != 1:
        errors.append(f"9280311 sets foreign credit {len(set_credit)} times, expected one")
    if foreign_charges and set_credit:
        if credit.find(foreign_charges[0].text) > credit.find(set_credit[0].text):
            errors.append("9280311 sets foreign credit before testing the prior-credit charge")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"AUBM early-game audit failed ({checks} checks, {len(errors)} errors).")
        return 1

    print(f"AUBM early-game audit passed ({checks} checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
