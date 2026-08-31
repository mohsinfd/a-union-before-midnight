#!/usr/bin/env python3
"""Validate exclusive coverage of the 1934 and 1936 Union reviews."""

from __future__ import annotations

import itertools
import re
from pathlib import Path

from validate_v4 import direct_scalar, extract_blocks, scalar


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mod/db/events/aubm_v4/05_union_integration.txt"
IDENTITY_FLAGS = {
    9280101: (
        "aubm_v4_ceylon_autonomy",
        "aubm_v4_ceylon_represented",
        "aubm_v4_ceylon_strategic",
    ),
    9280102: (
        "aubm_v4_compensated_customs",
        "aubm_v4_uniform_tariff",
        "aubm_v4_regional_customs",
    ),
    9280104: (
        "aubm_v4_malaya_treaty",
        "aubm_v4_malaya_commercial",
        "aubm_v4_malaya_security",
    ),
    9280105: (
        "aubm_v4_bengal_growers",
        "aubm_v4_bengal_exporters",
        "aubm_v4_bengal_board",
    ),
    9280106: (
        "aubm_v4_frontier_council",
        "aubm_v4_frontier_commissioner",
        "aubm_v4_frontier_provincial",
    ),
    9280107: (
        "aubm_v4_budget_compacts",
        "aubm_v4_budget_austerity",
        "aubm_v4_budget_loan",
    ),
}
IDENTITY_DIVIDENDS = {
    "aubm_v4_ceylon_autonomy": ("manpowerpool", "8"),
    "aubm_v4_ceylon_represented": ("tc_mod", "1"),
    "aubm_v4_ceylon_strategic": ("supplies", "200"),
    "aubm_v4_compensated_customs": ("money", "100"),
    "aubm_v4_uniform_tariff": ("money", "150"),
    "aubm_v4_regional_customs": ("dissent", "-1"),
    "aubm_v4_malaya_treaty": ("rarematerialspool", "100"),
    "aubm_v4_malaya_commercial": ("money", "150"),
    "aubm_v4_malaya_security": ("supplies", "200"),
    "aubm_v4_bengal_growers": ("manpowerpool", "8"),
    "aubm_v4_bengal_exporters": ("money", "150"),
    "aubm_v4_bengal_board": ("dissent", "-1"),
    "aubm_v4_frontier_council": ("dissent", "-1"),
    "aubm_v4_frontier_commissioner": ("supplies", "200"),
    "aubm_v4_frontier_provincial": ("manpowerpool", "8"),
    "aubm_v4_budget_compacts": ("dissent", "-1"),
    "aubm_v4_budget_austerity": ("money", "150"),
    "aubm_v4_budget_loan": ("supplies", "250"),
}


def event_blocks(text: str) -> dict[int, str]:
    clean = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    events: dict[int, str] = {}
    for match in re.finditer(r"(?m)^\s*event\s*=\s*\{", clean):
        opening = clean.find("{", match.start())
        depth = 0
        quoted = False
        escaped = False
        for position in range(opening, len(clean)):
            char = clean[position]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    block = clean[match.start() : position + 1]
                    event_id = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
                    if event_id:
                        events[int(event_id.group(1))] = block
                    break
    return events


def main() -> int:
    errors: list[str] = []
    checks = 0
    events = event_blocks(MODULE.read_text(encoding="cp1252"))

    consent = events.get(9280108, "")
    capacity = events.get(9280109, "")
    unfinished = events.get(9280110, "")
    for event_id, block in ((9280108, consent), (9280109, capacity), (9280110, unfinished)):
        checks += 2
        if not block:
            errors.append(f"missing 1934 integration review event {event_id}")
        if "setflag which = aubm_v4_review_1934" not in block:
            errors.append(f"review event {event_id} does not close the 1934 review")

    checks += 1
    exact_1934_complement = re.search(
        r"NOT\s*=\s*\{\s*OR\s*=\s*\{\s*"
        r"AND\s*=\s*\{[^{}]*flag\s*=\s*aubm_v4_union_legitimacy_gain"
        r"[^{}]*flag\s*=\s*aubm_v4_provincial_bargain"
        r"[^{}]*NOT\s*=\s*\{\s*flag\s*=\s*aubm_v4_union_coercion\s*\}[^{}]*\}\s*"
        r"AND\s*=\s*\{[^{}]*flag\s*=\s*aubm_v4_state_capacity_gain"
        r"[^{}]*flag\s*=\s*aubm_v4_union_coercion[^{}]*\}\s*\}\s*\}",
        unfinished,
        re.DOTALL,
    )
    if exact_1934_complement is None:
        errors.append("9280110 is not the exact complement of the two named 1934 reviews")

    # Model the three documented trigger predicates. Every possible opening
    # ledger must reach exactly one review.
    for legitimacy, state_capacity, bargain, coercion in itertools.product((False, True), repeat=4):
        checks += 1
        matches = (
            legitimacy and bargain and not coercion,
            state_capacity and coercion,
            not (
                (legitimacy and bargain and not coercion)
                or (state_capacity and coercion)
            ),
        )
        if sum(matches) != 1:
            errors.append(
                "non-exclusive 1934 ledger: "
                f"legitimacy={int(legitimacy)} capacity={int(state_capacity)} "
                f"bargain={int(bargain)} coercion={int(coercion)} "
                f"matches={sum(matches)}"
            )

    rooted = events.get(9280116, "")
    contested = events.get(9280117, "")
    for event_id, block in ((9280116, rooted), (9280117, contested)):
        checks += 2
        if not block:
            errors.append(f"missing 1936 state review event {event_id}")
        if "setflag which = aubm_v4_review_1936" not in block:
            errors.append(f"review event {event_id} does not close the 1936 review")

    checks += 1
    exact_1936_complement = re.search(
        r"NOT\s*=\s*\{\s*OR\s*=\s*\{\s*"
        r"flag\s*=\s*aubm_v4_legitimacy_established\s*"
        r"AND\s*=\s*\{[^{}]*flag\s*=\s*aubm_v4_union_legitimacy_gain"
        r"[^{}]*flag\s*=\s*aubm_v4_provincial_bargain[^{}]*\}\s*\}\s*\}",
        contested,
        re.DOTALL,
    )
    if exact_1936_complement is None:
        errors.append("9280117 is not the exact complement of the rooted 1936 review")

    for established, legitimacy, bargain in itertools.product((False, True), repeat=3):
        checks += 1
        rooted_match = established or (legitimacy and bargain)
        contested_match = not rooted_match
        if sum((rooted_match, contested_match)) != 1:
            errors.append(
                "non-exclusive 1936 ledger: "
                f"established={int(established)} legitimacy={int(legitimacy)} "
                f"bargain={int(bargain)}"
            )

    all_identity_flags = set(IDENTITY_DIVIDENDS)
    for event_id, expected_flags in IDENTITY_FLAGS.items():
        source = events.get(event_id, "")
        for letter, expected_flag in zip("abc", expected_flags):
            checks += 1
            actions = extract_blocks(source, f"action_{letter}")
            action = actions[0].text if actions else ""
            written_flags = {
                scalar(command.text, "which")
                for command in extract_blocks(action, "command")
                if direct_scalar(command.text, "type") == "setflag"
            }
            identity_writes = written_flags & all_identity_flags
            if identity_writes != {expected_flag}:
                errors.append(
                    f"{event_id} action_{letter} identity is {sorted(identity_writes)}, "
                    f"expected only {expected_flag}"
                )

    report = events.get(9280112, "")
    report_actions = extract_blocks(report, "action_a")
    report_action = report_actions[0].text if report_actions else ""
    checks += 6
    if scalar(report, "random") != "no" or scalar(report, "persistent") == "yes":
        errors.append("9280112 must remain a nonpersistent, non-random one-shot report")
    if not report_actions or any(extract_blocks(report, f"action_{letter}") for letter in "bcd"):
        errors.append("9280112 must remain a one-action report")
    report_triggers = extract_blocks(report, "trigger")
    event_trigger = report_triggers[0].text if report_triggers else ""
    if not re.search(
        r"NOT\s*=\s*\{\s*flag\s*=\s*aubm_v4_statistics_service\s*\}",
        event_trigger,
    ):
        errors.append("9280112 is not guarded as a one-shot report")
    label = scalar(report_action, "name") or ""
    if len(label.encode("cp1252")) > 58:
        errors.append("9280112 action label exceeds the 58-byte UI limit")

    callback_positions: list[int] = []
    for flag, expected_effect in IDENTITY_DIVIDENDS.items():
        checks += 1
        callbacks = []
        for command in extract_blocks(report_action, "command"):
            trigger_blocks = extract_blocks(command.text, "trigger")
            if not trigger_blocks:
                continue
            trigger_flags = re.findall(r"\bflag\s*=\s*([a-z0-9_]+)", trigger_blocks[0].text, re.I)
            if trigger_flags == [flag]:
                callbacks.append(command)
        if len(callbacks) != 1:
            errors.append(f"9280112 has {len(callbacks)} callbacks for {flag}, expected one")
            continue
        callback = callbacks[0]
        actual_effect = (
            direct_scalar(callback.text, "type"),
            direct_scalar(callback.text, "value"),
        )
        if actual_effect != expected_effect:
            errors.append(
                f"9280112 callback for {flag} is {actual_effect}, expected {expected_effect}"
            )
        callback_positions.append(report_action.find(callback.text))

    completion_match = re.search(
        r"command\s*=\s*\{\s*type\s*=\s*setflag\s+which\s*=\s*aubm_v4_statistics_service\s*\}",
        report_action,
    )
    if completion_match is None:
        errors.append("9280112 does not set its completion flag")
    elif callback_positions and completion_match.start() < max(callback_positions):
        errors.append("9280112 sets its completion flag before all identity dividends")

    conditional_flags = []
    for command in extract_blocks(report_action, "command"):
        trigger_blocks = extract_blocks(command.text, "trigger")
        if trigger_blocks:
            conditional_flags.extend(
                re.findall(r"\bflag\s*=\s*([a-z0-9_]+)", trigger_blocks[0].text, re.I)
            )
    checks += 1
    if sorted(conditional_flags) != sorted(all_identity_flags):
        errors.append("9280112 conditional callbacks are not exactly the 18 approved identity flags")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Union integration validation failed: {len(errors)} error(s), {checks} checks.")
        return 1

    print(f"Union integration validation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
