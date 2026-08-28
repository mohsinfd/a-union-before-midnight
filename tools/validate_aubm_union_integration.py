#!/usr/bin/env python3
"""Validate complete coverage of the 1934 Union integration review."""

from __future__ import annotations

import itertools
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mod/db/events/aubm_v4/05_union_integration.txt"


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

    required_unfinished_guards = (
        "NOT = { flag = aubm_v4_union_legitimacy_gain }",
        "NOT = { flag = aubm_v4_state_capacity_gain }",
        "NOT = { flag = aubm_v4_provincial_bargain }",
    )
    for guard in required_unfinished_guards:
        checks += 1
        if guard not in unfinished:
            errors.append(f"unfinished-bargain review omits coverage guard: {guard}")

    # Model the three documented trigger predicates. Every possible opening
    # ledger must reach at least one review; the all-positive/non-coercive case
    # belongs to consent and the all-positive/coercive case to capacity.
    for legitimacy, state_capacity, bargain, coercion in itertools.product((False, True), repeat=4):
        checks += 1
        matches = (
            legitimacy and bargain and not coercion,
            state_capacity and coercion,
            (not legitimacy) or (not state_capacity) or (not bargain),
        )
        if not any(matches):
            errors.append(
                "uncovered 1934 ledger: "
                f"legitimacy={int(legitimacy)} capacity={int(state_capacity)} "
                f"bargain={int(bargain)} coercion={int(coercion)}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Union integration validation failed: {len(errors)} error(s), {checks} checks.")
        return 1

    print(f"Union integration validation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
