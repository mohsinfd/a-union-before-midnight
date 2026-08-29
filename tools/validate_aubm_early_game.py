#!/usr/bin/env python3
"""Regression gate for audited AUBM opening and early-game event contracts."""

from __future__ import annotations

import re
import sys

from validate_aubm_cold_start import action, command_values, events
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
