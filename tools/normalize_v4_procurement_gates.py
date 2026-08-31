#!/usr/bin/env python3
"""Recalculate manpower gates after event procurement is normalized.

Legacy V3 events encoded the manpower of an entire serial line in action and
event triggers. V4 contracts authorize one formation per command, so those
gates must be derived from the remaining commands or valid choices stay hidden.
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

from ensure_decision_visibility import matching_brace, top_blocks


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENT_ROOTS = (
    ROOT / "mod/db/events/india_v3",
    ROOT / "mod/db/events/aubm_v4",
)

# Conservative current-model establishments, including a small allowance for
# the attached brigade named by the event command.
UNIT_MANPOWER = {
    "infantry": 13,
    "cavalry": 11,
    "motorized": 13,
    "mechanized": 10,
    "light_armor": 8,
    "armor": 8,
    "paratrooper": 15,
    "marine": 15,
    "bergsjaeger": 13,
    "garrison": 8,
    "hq": 5,
    "militia": 7,
    "multi_role": 1,
    "interceptor": 1,
    "strategic_bomber": 1,
    "tactical_bomber": 1,
    "naval_bomber": 1,
    "cas": 1,
    "transport_plane": 1,
    "battleship": 2,
    "light_cruiser": 1,
    "heavy_cruiser": 2,
    "battlecruiser": 2,
    "destroyer": 1,
    "carrier": 2,
    "escort_carrier": 1,
    "submarine": 1,
    "transport": 1,
    "light_carrier": 2,
}
ATTACHMENT_MANPOWER = {
    "artillery": 4,
    "engineer": 4,
    "armored_car": 3,
    "tank_destroyer": 4,
    "sp_artillery": 4,
    "anti_air": 3,
}
QUEUE_MARKER = re.compile(
    r"(?mi)^(?P<indent>[ \t]*)#\s*V3_QUEUE_MANPOWER\s*=\s*\d+[ \t]*\r?\n"
    r"[ \t]*manpower\s*=\s*\d+[ \t]*(?:\r?\n)?"
)
REACHABILITY_MARKER = re.compile(
    r"(?ms)^(?P<indent>[ \t]*)#\s*V3_ACTION_REACHABILITY_BEGIN[ \t]*\r?\n"
    r".*?^[ \t]*#\s*V3_ACTION_REACHABILITY_END[ \t]*(?:\r?\n)?"
)


def field(command: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*([A-Za-z0-9_-]+)", command, re.I)
    return match.group(1) if match else None


def production_manpower(action: str) -> int:
    total = 0.0
    for start, opening, closing in top_blocks(action, r"command"):
        command = action[start : closing + 1]
        if not re.search(r"\btype\s*=\s*build_division\b", command, re.I):
            continue
        unit_type = field(command, "which")
        if not unit_type or unit_type not in UNIT_MANPOWER:
            raise ValueError(f"No manpower establishment for event unit {unit_type!r}")
        serial_text = field(command, "when") or "1"
        serial = int(serial_text)
        attachment = field(command, "value")
        per_unit = UNIT_MANPOWER[unit_type] + ATTACHMENT_MANPOWER.get(attachment or "", 0)
        total += per_unit * serial
    return math.ceil(total)


def update_action(action: str) -> tuple[str, int, bool]:
    requirement = production_manpower(action)
    marker = QUEUE_MARKER.search(action)
    if not marker:
        return action, requirement, False
    indent = marker.group("indent")
    replacement = (
        f"{indent}# V3_QUEUE_MANPOWER = {requirement}\n"
        f"{indent}manpower = {requirement}\n"
        if requirement
        else ""
    )
    updated = action[: marker.start()] + replacement + action[marker.end() :]
    return updated, requirement, updated != action


def reachability(requirements: list[int], indent: str) -> str:
    if not requirements or any(value == 0 for value in requirements):
        return ""
    lines = [f"{indent}# V3_ACTION_REACHABILITY_BEGIN"]
    if len(requirements) == 1:
        lines.append(f"{indent}manpower = {requirements[0]}")
    else:
        lines.append(f"{indent}OR = {{")
        for value in requirements:
            lines.append(f"{indent}\tAND = {{ manpower = {value} }}")
        lines.append(f"{indent}}}")
    lines.append(f"{indent}# V3_ACTION_REACHABILITY_END")
    return "\n".join(lines) + "\n"


def update_event(event: str) -> tuple[str, int]:
    actions = top_blocks(event, r"action(?:_[a-z]+)?")
    requirements: list[int] = []
    changed = 0
    for start, _opening, closing in reversed(actions):
        updated, requirement, did_change = update_action(event[start : closing + 1])
        requirements.insert(0, requirement)
        if did_change:
            event = event[:start] + updated + event[closing + 1 :]
            changed += 1

    marker = REACHABILITY_MARKER.search(event)
    if marker:
        replacement = reachability(requirements, marker.group("indent"))
        updated = event[: marker.start()] + replacement + event[marker.end() :]
        if updated != event:
            changed += 1
            event = updated
    return event, changed


def update_file(path: pathlib.Path) -> int:
    original = path.read_text(encoding="cp1252")
    events: list[tuple[int, int]] = []
    for match in re.finditer(r"(?mi)^event\s*=\s*\{", original):
        opening = original.find("{", match.start(), match.end())
        events.append((match.start(), matching_brace(original, opening) + 1))

    updated = original
    changed = 0
    for start, end in reversed(events):
        event, count = update_event(updated[start:end])
        if count:
            updated = updated[:start] + event + updated[end:]
            changed += count
    if updated != original:
        path.write_text(updated, encoding="cp1252", newline="")
    return changed


def main() -> int:
    changed = 0
    for root in EVENT_ROOTS:
        for path in sorted(root.glob("*.txt")):
            changed += update_file(path)
    print(f"Recalculated {changed} event procurement manpower gate(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
