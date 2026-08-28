#!/usr/bin/env python3
"""Static acceptance gate for AUBM's Southeast Asian operational victories."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mod/db/events/aubm_v4/50_southeast_asia_operations.txt"
INDEX = ROOT / "mod/db/events.txt"
EVENT_ROOT = ROOT / "mod/db/events"
EXPECTED_IDS = {
    9287640,
    9287650,
    9287657,
    9287658,
    9287660,
    9287661,
    9287662,
    9287663,
    9287664,
    9287665,
    9287670,
}
AUTO_IDS = EXPECTED_IDS
REWARD_IDS = {9287640, 9287650, 9287660, 9287661, 9287662, 9287663, 9287670}
RELEVANT_WARS = {
    "ENG", "JAP", "U05", "HOL", "SIA", "U03", "FRA", "PHI", "USA",
    "MLY", "BUR", "VIE", "LAO", "CMB", "IDC", "INO", "BRU", "SAR", "U75",
}
LANES = {
    9287660: ("bay", 8, (1415, 1421), None),
    9287661: ("malacca", 12, (1432, 1438), (1636, 1647)),
    9287662: ("java", 16, (1647, 1653), None),
    9287663: ("south_china", 18, (1432,), (1399, 1565)),
}
LAND = {
    9287640: (
        "indochina",
        (1395, 1399),
        ("U03", "FRA"),
        9287657,
        9287658,
    ),
    9287650: (
        "philippines",
        (1565, 1579),
        ("PHI", "USA", "JAP"),
        9287657,
        9287658,
    ),
}


def strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", strip_comments(text)).strip()


def event_blocks(text: str) -> list[str]:
    clean = strip_comments(text)
    blocks: list[str] = []
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
                    blocks.append(clean[match.start() : position + 1])
                    break
        else:
            raise ValueError("unterminated event block")
    return blocks


def parse_events(text: str) -> dict[int, str]:
    events: dict[int, str] = {}
    for block in event_blocks(text):
        match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
        if not match:
            raise ValueError("event block without an ID")
        event_id = int(match.group(1))
        if event_id in events:
            raise ValueError(f"duplicate event {event_id} inside the module")
        events[event_id] = block
    return events


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def has_control(block: str, province: int) -> bool:
    return f"control = {{ province = {province} data = IND }}" in compact(block)


def has_navy_gate(block: str, size: int) -> bool:
    token = f"navy = {{ size = {size} type = 1 when = 0 where = 1 which = 1 country = IND }}"
    return token in compact(block)


def check_reward_bounds(errors: list[str], event_id: int, block: str) -> None:
    values: dict[str, list[int]] = {}
    for command, raw in re.findall(
        r"type\s*=\s*(supplies|money|oilpool|dissent|belligerence)\s+value\s*=\s*(-?\d+)",
        strip_comments(block),
    ):
        values.setdefault(command, []).append(int(raw))
    bounds = {
        "supplies": (0, 500),
        "money": (0, 100),
        "oilpool": (0, 300),
        "dissent": (-2, 0),
        "belligerence": (-2, 0),
    }
    for command, command_values in values.items():
        low, high = bounds[command]
        for value in command_values:
            require(errors, low <= value <= high, f"event {event_id} has excessive {command} reward {value}")


def validate() -> list[str]:
    errors: list[str] = []
    require(errors, MODULE.is_file(), "Southeast Asia event module is missing")
    require(errors, INDEX.is_file(), "db/events.txt is missing")
    if errors:
        return errors

    text = MODULE.read_text(encoding="cp1252")
    clean = strip_comments(text)
    flat = compact(text)
    index_text = INDEX.read_text(encoding="cp1252")

    try:
        events = parse_events(text)
    except ValueError as exc:
        return [str(exc)]

    require(errors, set(events) == EXPECTED_IDS, f"unexpected event ID set: {sorted(events)}")
    require(errors, all(9287640 <= event_id <= 9287699 for event_id in events), "event outside reserved 9287640-9287699 range")
    registration = 'event = "db\\events\\aubm_v4\\50_southeast_asia_operations.txt"'
    require(errors, index_text.count(registration) == 1, "module is not registered exactly once")

    for event_id in EXPECTED_IDS:
        occurrences: list[Path] = []
        needle = re.compile(rf"(?m)^\s*id\s*=\s*{event_id}\s*$")
        for path in EVENT_ROOT.rglob("*.txt"):
            candidate = path.read_text(encoding="cp1252", errors="replace")
            if needle.search(strip_comments(candidate)):
                occurrences.append(path)
        require(errors, occurrences == [MODULE], f"event {event_id} is not globally unique: {occurrences}")

    for event_id, block in events.items():
        block_flat = compact(block)
        require(errors, "persistent = yes" in block_flat, f"event {event_id} is not persistent")
        require(errors, "country = IND" in block_flat, f"event {event_id} is not Indian-scoped")
        require(errors, "one_action = yes" in block_flat, f"event {event_id} is not deterministic")
        require(errors, "action_a = {" in block_flat, f"event {event_id} lacks action_a")
        if event_id in AUTO_IDS:
            require(errors, "date = { day = 0 month = january year = 1933 }" in block_flat, f"event {event_id} is not globally dated")
            require(errors, "deathdate = { day = 29 month = december year = 1964 }" in block_flat, f"event {event_id} lacks scenario-long deathdate")
            require(errors, "offset =" in block_flat, f"event {event_id} lacks an offset")

    # Operations must not become a second armistice system or mutate diplomacy/maps.
    for effect in (
        "peace", "event", "trigger", "secedeprovince", "secederegion", "secedearea",
        "independence", "inherit", "addcore", "addclaim", "control", "alliance",
        "leave_alliance", "war",
    ):
        require(errors, f"type = {effect}" not in flat, f"module contains forbidden effect {effect}")
    require(errors, "pending" not in flat, "operational achievements create a competing pending peace docket")
    require(
        errors,
        re.search(r"command\s*=\s*\{\s*type\s*=[^}\n]+\btrigger\s*=", clean) is None,
        "a conditional command places type before trigger",
    )

    # Land milestones are one-time historical credit with reversible live state.
    suspension = compact(events[9287657])
    recovery = compact(events[9287658])
    for event_id, (key, provinces, owners, _, _) in LAND.items():
        block = compact(events[event_id])
        historical = f"ind_aubm_sea_land_{key}"
        current = f"{historical}_current"
        suspended = f"{historical}_suspended"
        require(errors, f"NOT = {{ flag = {historical} }}" in block, f"{key} lacks one-time guard")
        require(errors, f"type = setflag which = {historical}" in block, f"{key} does not record history")
        require(errors, f"type = setflag which = {current}" in block, f"{key} does not set live state")
        require(errors, f"type = clrflag which = {suspended}" in block, f"{key} does not clear stale suspension")
        for province in provinces:
            require(errors, has_control(block, province), f"{key} omits Indian control of {province}")
        for owner in owners:
            owner_chain = " ".join(f"owned = {{ province = {province} data = {owner} }}" for province in provinces)
            require(errors, f"exists = {owner}" in block and f"war = {{ country = IND country = {owner} }}" in block and owner_chain in block, f"{key} omits legal owner {owner}")
        require(errors, f"type = setflag which = {suspended}" in suspension, f"{key} has no suspension transition")
        require(errors, f"type = clrflag which = {current}" in suspension, f"{key} suspension does not clear current")
        require(errors, f"type = setflag which = {current}" in recovery, f"{key} has no recovery transition")
        require(errors, f"type = clrflag which = {suspended}" in recovery, f"{key} recovery does not clear suspension")
        erases_history = re.search(
            rf"type = clrflag which = {re.escape(historical)}(?:\s|\}})",
            flat,
        )
        require(errors, erases_history is None, f"{key} historical credit can be erased")

    # Sea lanes require exact ports, ready surface fleets and relevant war.
    sea_suspension = compact(events[9287664])
    sea_recovery = compact(events[9287665])
    for event_id, (key, size, mandatory_ports, alternate_ports) in LANES.items():
        block = compact(events[event_id])
        historical = f"ind_aubm_sea_lane_{key}_achieved"
        current = f"ind_aubm_sea_lane_{key}_current"
        suspended = f"ind_aubm_sea_lane_{key}_suspended"
        require(errors, "atwar = yes" in block, f"{key} can fire in peace")
        wars = set(re.findall(r"war = \{ country = IND country = ([A-Z0-9]{3}) \}", block))
        require(errors, len(wars & RELEVANT_WARS) >= 5, f"{key} lacks a relevant-war guard")
        require(errors, "AFG" not in wars, f"{key} counts an unrelated Afghan war")
        require(errors, f"NOT = {{ flag = {historical} }}" in block, f"{key} lacks one-time guard")
        require(errors, f"type = setflag which = {historical}" in block, f"{key} does not record history")
        require(errors, f"type = setflag which = {current}" in block, f"{key} does not set current")
        require(errors, has_navy_gate(block, size), f"{key} lacks fleet threshold {size}")
        for province in mandatory_ports:
            require(errors, has_control(block, province), f"{key} omits port {province}")
        if alternate_ports:
            alternates = " ".join(f"control = {{ province = {province} data = IND }}" for province in alternate_ports)
            require(errors, f"OR = {{ {alternates} }}" in block, f"{key} lacks alternate ports {alternate_ports}")
        require(errors, f"type = setflag which = {suspended}" in sea_suspension, f"{key} has no suspension")
        require(errors, f"type = clrflag which = {current}" in sea_suspension, f"{key} suspension does not clear current")
        require(errors, f"type = setflag which = {current}" in sea_recovery, f"{key} has no recovery")
        require(errors, f"type = clrflag which = {suspended}" in sea_recovery, f"{key} recovery does not clear suspension")
        require(errors, f"type = clrflag which = {historical}" not in flat, f"{key} historical credit can be erased")

    resource_pattern = re.compile(r"type\s*=\s*(supplies|money|oilpool|dissent|belligerence)\s+value\s*=")
    for event_id, block in events.items():
        if event_id in REWARD_IDS:
            check_reward_bounds(errors, event_id, block)
        else:
            require(errors, resource_pattern.search(strip_comments(block)) is None, f"non-award event {event_id} repays a reward")

    aggregate = compact(events[9287670])
    require(errors, "NOT = { flag = ind_aubm_sea_theatre_achieved }" in aggregate, "aggregate lacks one-time guard")
    require(errors, "type = setflag which = ind_aubm_sea_theatre_achieved" in aggregate, "aggregate does not record completion")
    for flag in ("ind_aubm_sea_land_indochina", "ind_aubm_sea_land_philippines"):
        require(errors, flag in aggregate, f"aggregate omits {flag}")
    for key in ("bay", "malacca", "java", "south_china"):
        require(errors, f"ind_aubm_sea_lane_{key}_achieved" in aggregate, f"aggregate omits {key}")
    require(errors, aggregate.count("ind_aubm_sea_lane_") >= 16, "aggregate lacks flexible multi-lane combinations")
    require(errors, "ind_aubm_global_rewarded_mly" in aggregate and "ind_aubm_regional_settled_u05" in aggregate, "aggregate omits existing land results")
    local_categories = {
        "Malaya victory": "ind_aubm_regional_victory_eng_malaya",
        "Malaya settlement": "ind_aubm_regional_settled_eng_malaya",
        "Dutch colonial victory": "ind_aubm_regional_victory_hol_colonial",
        "Dutch colonial settlement": "ind_aubm_regional_settled_hol_colonial",
    }
    for label, flag in local_categories.items():
        require(errors, aggregate.count(flag) == 7, f"aggregate does not count {label} in every land category")
    require(errors, "ind_aubm_national_southern_victory" not in aggregate, "aggregate uses rigid national Southern gate")
    require(errors, "control = { province" not in aggregate and "navy = {" not in aggregate, "aggregate requires one rigid live map state")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"Southeast Asia validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Southeast Asia validation passed: 11 unique events, two non-duplicating reversible land operations, four fleet-backed lanes, and one flexible theatre award.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
