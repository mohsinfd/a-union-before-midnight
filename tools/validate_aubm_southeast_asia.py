#!/usr/bin/env python3
"""Static acceptance gate for AUBM's Southeast Asian operational victories."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mod/db/events/aubm_v4/50_southeast_asia_operations.txt"
ARMISTICE_MODULE = ROOT / "mod/db/events/aubm_v4/49_bespoke_armistices.txt"
PROTOCOL_MODULE = ROOT / "mod/db/events/aubm_v4/45_enemy_campaigns.txt"
SOVIET_MODULE = ROOT / "mod/db/events/aubm_v4/43_wartime_settlements.txt"
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
    9287680,
    9287681,
    9287682,
    9287683,
    9287684,
    9287685,
    9287686,
    9287687,
    9287688,
    9287689,
}
ARMISTICE_ID = 9287690
AUTO_IDS = EXPECTED_IDS
REWARD_IDS = {
    9287640,
    9287650,
    9287660,
    9287661,
    9287662,
    9287663,
    9287670,
    9287681,
    9287682,
    9287683,
    9287684,
}
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
LIBERATIONS = {
    "malaya": {
        "award": 9287681,
        "recovery": 9287686,
        "provinces": (1432, 1438),
        "owners": ("ENG", "MLY", "U75"),
    },
    "dei": {
        "award": 9287682,
        "recovery": 9287687,
        "provinces": (1647,),
        "owners": ("U05", "HOL", "INO"),
    },
    "indochina": {
        "award": 9287683,
        "recovery": 9287688,
        "provinces": (1395, 1399),
        "owners": ("U03", "FRA", "IDC", "VIE"),
    },
    "philippines": {
        "award": 9287684,
        "recovery": 9287689,
        "provinces": (1565, 1579),
        "owners": ("PHI", "USA"),
    },
}
LANE_LIBERATIONS = {
    9287661: ("malaya", "dei"),
    9287663: ("malaya", "indochina", "philippines"),
}
LIVE_LIBERATION_FLAGS = tuple(
    f"ind_aubm_sea_land_{key}_liberated_current"
    for key in ("malaya", "dei", "indochina", "philippines")
)
LIVE_JAPAN_LEVERAGE = (
    "OR = { flag = ind_aubm_japan_current AND = { "
    "flag = ind_aubm_sea_theatre_achieved OR = { "
    + " ".join(f"flag = {flag}" for flag in LIVE_LIBERATION_FLAGS)
    + " } } }"
)
LIVE_JAPAN_WAR_AND_LEVERAGE = (
    "AND = { war = { country = IND country = JAP } " + LIVE_JAPAN_LEVERAGE + " }"
)
SOUTHERN_INFLIGHT = "ind_aubm_japan_southern_armistice_inflight"
TERMS_DISPATCHING = "ind_aubm_major_armistice_terms_dispatching"
JAPAN_MAJOR_VICTORY = "ind_aubm_japan_major_victory"
STALE_INFLIGHT_GATE = (
    f"OR = {{ flag = {JAPAN_MAJOR_VICTORY} "
    f"NOT = {{ {LIVE_JAPAN_WAR_AND_LEVERAGE} }} }}"
)
NORMAL_BOARD_CONTINUE_GATE = (
    f"OR = {{ NOT = {{ flag = {SOUTHERN_INFLIGHT} }} flag = {JAPAN_MAJOR_VICTORY} }}"
)
SOUTHERN_DECLINE_GATE = (
    f"flag = {SOUTHERN_INFLIGHT} NOT = {{ flag = {JAPAN_MAJOR_VICTORY} }}"
)
RESOURCE_PATTERN = re.compile(
    r"type\s*=\s*(supplies|money|oilpool|dissent|belligerence)\s+value\s*="
)


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


def has_control_for(block: str, province: int, country: str) -> bool:
    return f"control = {{ province = {province} data = {country} }}" in compact(block)


def has_garrison(block: str, province: int) -> bool:
    token = f"garrison = {{ country = IND province = {province} type = land size = 1 area = no }}"
    return token in compact(block)


def has_flag_effect(block: str, effect: str, flag: str) -> bool:
    return flag_effect_count(block, effect, flag) > 0


def flag_effect_count(block: str, effect: str, flag: str) -> int:
    pattern = re.compile(rf"\btype = {re.escape(effect)} which = {re.escape(flag)}(?=\s|\}})")
    return len(pattern.findall(compact(block)))


def flag_reference_count(block: str, flag: str) -> int:
    pattern = re.compile(rf"\bflag = {re.escape(flag)}(?=\s|\}})")
    return len(pattern.findall(compact(block)))


def named_brace_blocks(text: str, name: str) -> list[str]:
    clean = strip_comments(text)
    blocks: list[str] = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*=\s*\{{")
    for match in pattern.finditer(clean):
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
                    blocks.append(compact(clean[match.start() : position + 1]))
                    break
    return blocks


def has_shared_or(block: str, tokens: tuple[str, ...]) -> bool:
    return any(all(token in group for token in tokens) for group in named_brace_blocks(block, "OR"))


def validate_live_japan_leverage(errors: list[str], label: str, block: str) -> None:
    block_flat = compact(block)
    require(
        errors,
        LIVE_JAPAN_LEVERAGE in block_flat,
        f"{label} does not require Japan current leverage or SEA theatre history backed by a current liberation",
    )
    require(
        errors,
        flag_reference_count(block_flat, "ind_aubm_sea_theatre_achieved") == 1,
        f"{label} has a second route-neutral SEA theatre-history unlock",
    )
    for flag in LIVE_LIBERATION_FLAGS:
        require(
            errors,
            flag_reference_count(block_flat, flag) == 1,
            f"{label} does not keep {flag} inside the live SEA leverage branch",
        )
    require(
        errors,
        flag_reference_count(block_flat, "ind_aubm_japan_limited_victory") == 0,
        f"{label} incorrectly accepts historical Japanese limited-victory credit",
    )


def validate_dispatch_handoff(
    errors: list[str],
    label: str,
    action: str,
    event_id: int,
    where: str,
    when: int = 1,
) -> None:
    commands = named_brace_blocks(action, "command")
    dispatch_flag_sets = [
        block for block in commands if has_flag_effect(block, "setflag", TERMS_DISPATCHING)
    ]
    event_token = f"type = event which = {event_id} where = {where} when = {when}"
    dispatches = [block for block in commands if event_token in block]
    require(errors, len(dispatch_flag_sets) == 1, f"{label} does not set exactly one terms-dispatch lock")
    require(errors, len(dispatches) == 1, f"{label} does not queue exactly one event {event_id} at +{when} day")
    if len(dispatch_flag_sets) == 1 and len(dispatches) == 1:
        require(
            errors,
            commands.index(dispatch_flag_sets[0]) < commands.index(dispatches[0]),
            f"{label} queues event {event_id} before setting the terms-dispatch lock",
        )


def validate_terms_actions_clear_dispatch(
    errors: list[str],
    label: str,
    event: str,
    action_names: tuple[str, ...],
) -> None:
    for action_name in action_names:
        actions = named_brace_blocks(event, action_name)
        require(errors, len(actions) == 1, f"{label} lacks exactly one {action_name}")
        if len(actions) != 1:
            continue
        commands = named_brace_blocks(actions[0], "command")
        clears = [
            block for block in commands if has_flag_effect(block, "clrflag", TERMS_DISPATCHING)
        ]
        require(errors, len(clears) == 1, f"{label} {action_name} does not clear exactly one terms-dispatch lock")
        if len(clears) == 1:
            require(
                errors,
                commands.index(clears[0]) == 0,
                f"{label} {action_name} does not clear the terms-dispatch lock before other effects",
            )


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
    require(errors, ARMISTICE_MODULE.is_file(), "bespoke armistice event module is missing")
    require(errors, PROTOCOL_MODULE.is_file(), "major armistice protocol module is missing")
    require(errors, SOVIET_MODULE.is_file(), "Soviet wartime settlement module is missing")
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

    try:
        armistice_events = parse_events(ARMISTICE_MODULE.read_text(encoding="cp1252"))
    except ValueError as exc:
        return [f"bespoke armistice parse failure: {exc}"]
    require(errors, ARMISTICE_ID in armistice_events, f"southern armistice event {ARMISTICE_ID} is missing")
    if ARMISTICE_ID not in armistice_events:
        return errors

    try:
        soviet_events = parse_events(SOVIET_MODULE.read_text(encoding="cp1252"))
    except ValueError as exc:
        return [f"Soviet wartime settlement parse failure: {exc}"]
    require(errors, 9282036 in soviet_events, "Soviet armistice docket 9282036 is missing")
    if 9282036 not in soviet_events:
        return errors

    require(errors, set(events) == EXPECTED_IDS, f"unexpected event ID set: {sorted(events)}")
    if not EXPECTED_IDS.issubset(events):
        return errors
    require(errors, all(9287640 <= event_id <= 9287699 for event_id in events), "event outside reserved 9287640-9287699 range")
    registration = 'event = "db\\events\\aubm_v4\\50_southeast_asia_operations.txt"'
    require(errors, index_text.count(registration) == 1, "module is not registered exactly once")
    armistice_registration = 'event = "db\\events\\aubm_v4\\49_bespoke_armistices.txt"'
    require(errors, index_text.count(armistice_registration) == 1, "bespoke armistice module is not registered exactly once")

    for event_id in EXPECTED_IDS:
        occurrences: list[Path] = []
        needle = re.compile(rf"(?m)^\s*id\s*=\s*{event_id}\s*$")
        for path in EVENT_ROOT.rglob("*.txt"):
            candidate = path.read_text(encoding="cp1252", errors="replace")
            if needle.search(strip_comments(candidate)):
                occurrences.append(path)
        require(errors, occurrences == [MODULE], f"event {event_id} is not globally unique: {occurrences}")

    armistice_occurrences: list[Path] = []
    armistice_needle = re.compile(rf"(?m)^\s*id\s*=\s*{ARMISTICE_ID}\s*$")
    for path in EVENT_ROOT.rglob("*.txt"):
        candidate = path.read_text(encoding="cp1252", errors="replace")
        if armistice_needle.search(strip_comments(candidate)):
            armistice_occurrences.append(path)
    require(
        errors,
        armistice_occurrences == [ARMISTICE_MODULE],
        f"event {ARMISTICE_ID} is not globally unique: {armistice_occurrences}",
    )

    for event_id, block in events.items():
        block_flat = compact(block)
        require(errors, "persistent = yes" in block_flat, f"event {event_id} is not persistent")
        require(errors, "country = IND" in block_flat, f"event {event_id} is not Indian-scoped")
        require(errors, "action_a = {" in block_flat, f"event {event_id} lacks action_a")
        if event_id in AUTO_IDS:
            require(errors, "one_action = yes" in block_flat, f"event {event_id} is not deterministic")
            require(errors, "date = { day = 0 month = january year = 1933 }" in block_flat, f"event {event_id} is not globally dated")
            require(errors, "deathdate = { day = 29 month = december year = 1964 }" in block_flat, f"event {event_id} lacks scenario-long deathdate")
            require(errors, "offset =" in block_flat, f"event {event_id} lacks an offset")

    # Operations must not become a second armistice system or mutate diplomacy/maps.
    operations_flat = compact("\n".join(events[event_id] for event_id in AUTO_IDS))
    for effect in (
        "peace", "event", "trigger", "secedeprovince", "secederegion", "secedearea",
        "independence", "inherit", "addcore", "addclaim", "control", "alliance",
        "leave_alliance", "war",
    ):
        require(errors, f"type = {effect}" not in operations_flat, f"operational events contain forbidden effect {effect}")
    require(errors, "pending" not in operations_flat, "operational achievements create a competing pending peace docket")
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

    # Friendly-owner liberation requires a recorded Japanese occupation and
    # fresh proof that Indian troops participated in restoring the named hubs.
    watcher = compact(events[9287680])
    require(errors, "war = { country = IND country = JAP }" in watcher, "occupation watcher lacks the India-Japan war")
    for key, spec in LIBERATIONS.items():
        provinces = spec["provinces"]
        owners = spec["owners"]
        award_id = spec["award"]
        recovery_id = spec["recovery"]
        seen = f"ind_aubm_sea_land_{key}_japan_occupation_seen"
        historical = f"ind_aubm_sea_land_{key}_liberated"
        current = f"{historical}_current"
        suspended = f"{historical}_suspended"

        require(errors, f"NOT = {{ flag = {seen} }}" in watcher, f"{key} occupation watcher lacks a one-time guard")
        require(errors, has_flag_effect(watcher, "setflag", seen), f"{key} occupation is never recorded")
        for province in provinces:
            require(errors, has_control_for(watcher, province, "JAP"), f"{key} watcher omits Japanese control of {province}")
        for owner in owners:
            require(errors, f"exists = {owner}" in watcher, f"{key} watcher omits existing owner {owner}")
            require(errors, f"war = {{ country = JAP country = {owner} }}" in watcher, f"{key} watcher omits Japan's war with {owner}")
            require(errors, f"NOT = {{ war = {{ country = IND country = {owner} }} }}" in watcher, f"{key} watcher can target Indian enemy {owner}")
            for province in provinces:
                require(
                    errors,
                    f"owned = {{ province = {province} data = {owner} }}" in watcher,
                    f"{key} watcher omits {owner} ownership of {province}",
                )

        award = compact(events[award_id])
        require(errors, f"flag = {seen}" in award, f"{key} award does not require prior Japanese occupation")
        require(errors, f"NOT = {{ flag = {historical} }}" in award, f"{key} award lacks one-time historical guard")
        require(errors, "war = { country = IND country = JAP }" in award, f"{key} award can fire outside the Japan war")
        for owner in owners:
            require(errors, f"exists = {owner}" in award, f"{key} award omits friendly owner {owner}")
            require(errors, f"NOT = {{ war = {{ country = IND country = {owner} }} }}" in award, f"{key} award can target Indian enemy {owner}")
            for province in provinces:
                require(
                    errors,
                    f"owned = {{ province = {province} data = {owner} }}" in award,
                    f"{key} award omits {owner} ownership of {province}",
                )
                require(
                    errors,
                    has_control_for(award, province, owner),
                    f"{key} award omits restored {owner} control of {province}",
                )
        proof_tokens = tuple(
            [f"control = {{ province = {province} data = IND }}" for province in provinces]
            + [
                f"garrison = {{ country = IND province = {province} type = land size = 1 area = no }}"
                for province in provinces
            ]
        )
        require(errors, has_shared_or(award, proof_tokens), f"{key} award lacks one shared direct-control/garrison proof gate")
        for province in provinces:
            require(errors, has_control(award, province), f"{key} award omits direct Indian control proof at {province}")
            require(errors, has_garrison(award, province), f"{key} award omits Indian garrison proof at {province}")
        require(errors, has_flag_effect(award, "setflag", historical), f"{key} award does not record permanent credit")
        require(errors, has_flag_effect(award, "setflag", current), f"{key} award does not set current credit")
        require(errors, has_flag_effect(award, "clrflag", suspended), f"{key} award does not clear stale suspension")
        require(
            errors,
            not has_flag_effect(award, "setflag", "ind_aubm_global_campaign_victory"),
            f"{key} partial liberation prematurely opens the route-level generic fallback",
        )
        require(errors, RESOURCE_PATTERN.search(strip_comments(events[award_id])) is not None, f"{key} award has no bounded one-time reward")

        suspension = compact(events[9287685])
        require(errors, f"flag = {current}" in suspension, f"{key} has no current-state suspension trigger")
        require(errors, has_flag_effect(suspension, "setflag", suspended), f"{key} suspension is never recorded")
        require(errors, has_flag_effect(suspension, "clrflag", current), f"{key} suspension does not clear current credit")

        recovery = compact(events[recovery_id])
        require(errors, f"flag = {seen}" in recovery, f"{key} recovery forgets the prior Japanese occupation")
        require(errors, flag_reference_count(recovery, historical) >= 1, f"{key} recovery does not require permanent credit")
        require(errors, f"flag = {suspended}" in recovery, f"{key} recovery does not require suspended state")
        require(errors, "war = { country = IND country = JAP }" in recovery, f"{key} recovery can fire outside the Japan war")
        for owner in owners:
            require(errors, f"exists = {owner}" in recovery, f"{key} recovery omits friendly owner {owner}")
            require(errors, f"NOT = {{ war = {{ country = IND country = {owner} }} }}" in recovery, f"{key} recovery can target Indian enemy {owner}")
            for province in provinces:
                require(
                    errors,
                    f"owned = {{ province = {province} data = {owner} }}" in recovery,
                    f"{key} recovery omits {owner} ownership of {province}",
                )
                require(
                    errors,
                    has_control_for(recovery, province, owner),
                    f"{key} recovery omits restored {owner} control of {province}",
                )
        require(errors, has_shared_or(recovery, proof_tokens), f"{key} recovery lacks fresh direct-control/garrison proof")
        for province in provinces:
            require(errors, has_control(recovery, province), f"{key} recovery omits direct Indian control at {province}")
            require(errors, has_garrison(recovery, province), f"{key} recovery omits Indian garrison proof at {province}")
        require(errors, has_flag_effect(recovery, "setflag", current), f"{key} recovery does not restore current credit")
        require(errors, has_flag_effect(recovery, "clrflag", suspended), f"{key} recovery does not clear suspension")
        require(errors, not has_flag_effect(recovery, "setflag", historical), f"{key} recovery repays permanent credit")
        require(errors, not has_flag_effect(recovery, "setflag", "ind_aubm_global_campaign_victory"), f"{key} recovery repays global campaign credit")
        require(errors, RESOURCE_PATTERN.search(strip_comments(events[recovery_id])) is None, f"{key} recovery repays resources")

        require(errors, not has_flag_effect(flat, "clrflag", seen), f"{key} occupation history can be erased")
        require(errors, not has_flag_effect(flat, "clrflag", historical), f"{key} liberation history can be erased")

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
            alternate_tokens = tuple(
                f"control = {{ province = {province} data = IND }}" for province in alternate_ports
            )
            require(errors, has_shared_or(block, alternate_tokens), f"{key} lacks alternate ports {alternate_ports}")
        require(errors, f"type = setflag which = {suspended}" in sea_suspension, f"{key} has no suspension")
        require(errors, f"type = clrflag which = {current}" in sea_suspension, f"{key} suspension does not clear current")
        require(errors, f"type = setflag which = {current}" in sea_recovery, f"{key} has no recovery")
        require(errors, f"type = clrflag which = {suspended}" in sea_recovery, f"{key} recovery does not clear suspension")
        require(errors, f"type = clrflag which = {historical}" not in flat, f"{key} historical credit can be erased")

        for liberation_key in LANE_LIBERATIONS.get(event_id, ()):
            liberation_current = f"ind_aubm_sea_land_{liberation_key}_liberated_current"
            require(errors, f"flag = {liberation_current}" in block, f"{key} omits friendly {liberation_key} control")
            require(errors, f"flag = {liberation_current}" in sea_suspension, f"{key} suspension omits friendly {liberation_key} control")
            require(errors, f"flag = {liberation_current}" in sea_recovery, f"{key} recovery omits friendly {liberation_key} control")

    require(
        errors,
        "ind_aubm_sea_land_dei_liberated_current" not in compact(events[9287662]),
        "Batavia-only liberation incorrectly satisfies the Java Sea lane",
    )

    for event_id, block in events.items():
        if event_id in REWARD_IDS:
            check_reward_bounds(errors, event_id, block)
        else:
            require(errors, RESOURCE_PATTERN.search(strip_comments(block)) is None, f"non-award event {event_id} repays a reward")

    # Reachability regression: a partial land operation, liberation or sea
    # lane must not let a route's generic fallback consume its one-time war
    # achievement before the three-result theatre aggregate becomes true.
    global_campaign_flag = "ind_aubm_global_campaign_victory"
    global_campaign_setters = sorted(
        event_id
        for event_id, block in events.items()
        if has_flag_effect(block, "setflag", global_campaign_flag)
    )
    require(
        errors,
        global_campaign_setters == [9287670],
        f"SEA global campaign victory is not reserved for the full theatre event: {global_campaign_setters}",
    )
    for event_id in sorted(REWARD_IDS - {9287670}):
        require(
            errors,
            not has_flag_effect(events[event_id], "setflag", global_campaign_flag),
            f"partial SEA award {event_id} can consume a route war achievement before theatre completion",
        )
    require(
        errors,
        "ind_aubm_route_war_achievement" not in flat,
        "SEA operations mutate the route-level one-time achievement directly",
    )

    aggregate = compact(events[9287670])
    require(errors, "NOT = { flag = ind_aubm_sea_theatre_achieved }" in aggregate, "aggregate lacks one-time guard")
    require(errors, "type = setflag which = ind_aubm_sea_theatre_achieved" in aggregate, "aggregate does not record completion")
    require(
        errors,
        flag_effect_count(aggregate, "setflag", global_campaign_flag) == 1,
        "full SEA theatre does not publish exactly one global campaign victory",
    )
    aggregate_actions = named_brace_blocks(events[9287670], "action_a")
    require(errors, len(aggregate_actions) == 1, "full SEA theatre lacks exactly one award action")
    if len(aggregate_actions) == 1:
        aggregate_set_flags = re.findall(
            r"\btype = setflag which = ([a-z0-9_]+)",
            aggregate_actions[0],
        )
        require(
            errors,
            "ind_aubm_sea_theatre_achieved" in aggregate_set_flags
            and global_campaign_flag in aggregate_set_flags
            and aggregate_set_flags.index("ind_aubm_sea_theatre_achieved")
            < aggregate_set_flags.index(global_campaign_flag),
            "full SEA theatre publishes global campaign victory before recording theatre completion",
        )
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
    for key in LIBERATIONS:
        liberation = f"ind_aubm_sea_land_{key}_liberated"
        require(errors, flag_reference_count(aggregate, liberation) == 7, f"aggregate does not fold {key} liberation into its land category")
    require(errors, "ind_aubm_national_southern_victory" not in aggregate, "aggregate uses rigid national Southern gate")
    require(errors, "control = { province" not in aggregate and "navy = {" not in aggregate, "aggregate requires one rigid live map state")

    # The optional southern settlement is only a bridge into the existing
    # pairwise Japanese armistice protocol; it must not settle or transfer
    # anything itself.
    armistice = compact(armistice_events[ARMISTICE_ID])
    require(errors, "persistent = yes" in armistice, "southern armistice offer is not persistent")
    require(errors, "country = IND" in armistice, "southern armistice offer is not Indian-scoped")
    require(errors, "one_action = yes" not in armistice, "southern armistice offer suppresses the player's choice")
    require(errors, "date = { day = 0 month = january year = 1933 }" in armistice, "southern armistice offer is not globally dated")
    require(errors, "offset = 2" in armistice, "southern armistice offer does not use the bounded two-day poll")
    require(errors, "deathdate = { day = 29 month = december year = 1964 }" in armistice, "southern armistice offer lacks scenario-long deathdate")
    require(errors, "war = { country = IND country = JAP }" in armistice, "southern armistice offer can fire outside the Japan war")
    armistice_triggers = named_brace_blocks(armistice_events[ARMISTICE_ID], "trigger")
    require(errors, len(armistice_triggers) == 1, "southern armistice offer does not have exactly one event trigger")
    if len(armistice_triggers) == 1:
        validate_live_japan_leverage(errors, "southern armistice offer", armistice_triggers[0])
    for guard in (
        "ind_aubm_armistice_japan",
        "ind_aubm_japan_major_victory",
        "ind_aubm_major_armistice_outstanding",
        "ind_aubm_major_armistice_retry_pending",
        TERMS_DISPATCHING,
        "ind_aubm_japan_southern_armistice_declined",
        SOUTHERN_INFLIGHT,
    ):
        require(errors, f"NOT = {{ flag = {guard} }}" in armistice, f"southern armistice offer lacks guard {guard}")

    action_a_blocks = named_brace_blocks(armistice_events[ARMISTICE_ID], "action_a")
    action_b_blocks = named_brace_blocks(armistice_events[ARMISTICE_ID], "action_b")
    action_c_blocks = named_brace_blocks(armistice_events[ARMISTICE_ID], "action_c")
    require(errors, len(action_a_blocks) == 1, "southern armistice offer does not have exactly one submission action")
    require(errors, len(action_b_blocks) == 1, "southern armistice offer does not have exactly one decline action")
    require(errors, not action_c_blocks, "southern armistice offer has an unexpected third action")
    if len(action_a_blocks) == 1:
        action_a = action_a_blocks[0]
        set_flags = re.findall(r"\btype = setflag which = ([a-z0-9_]+)", action_a)
        dispatches = re.findall(r"\btype = event which = (\d+) where = ([A-Z0-9]{3}) when = (\d+)", action_a)
        require(
            errors,
            set_flags
            == [
                SOUTHERN_INFLIGHT,
                "ind_aubm_major_armistice_target_jap",
                "ind_aubm_major_armistice_outstanding",
            ],
            "southern armistice submission does not set in-flight state before the Japanese target and outstanding docket",
        )
        require(errors, dispatches == [("9282186", "JAP", "3")], "southern armistice submission does not dispatch only protocol event 9282186 to Japan")
        effect_types = re.findall(r"\btype = ([a-z_]+)", action_a)
        require(errors, effect_types == ["setflag", "setflag", "setflag", "event"], "southern armistice submission mutates state outside the pairwise protocol")
    if len(action_b_blocks) == 1:
        action_b = action_b_blocks[0]
        decline_flags = re.findall(r"\btype = setflag which = ([a-z0-9_]+)", action_b)
        effect_types = re.findall(r"\btype = ([a-z_]+)", action_b)
        require(errors, decline_flags == ["ind_aubm_japan_southern_armistice_declined"], "southern armistice decline does not set exactly its opt-out flag")
        require(errors, effect_types == ["setflag"], "southern armistice decline has an unexpected side effect")

    for effect in (
        "peace", "inherit", "annex", "secedeprovince", "secederegion", "secedearea",
        "independence", "control", "alliance", "leave_alliance", "war", "addcore", "addclaim",
    ):
        require(errors, f"type = {effect}" not in armistice, f"southern armistice offer directly applies forbidden effect {effect}")

    protocol_occurrences: list[Path] = []
    protocol_needle = re.compile(r"(?m)^\s*id\s*=\s*9282186\s*$")
    for path in EVENT_ROOT.rglob("*.txt"):
        candidate = path.read_text(encoding="cp1252", errors="replace")
        if protocol_needle.search(strip_comments(candidate)):
            protocol_occurrences.append(path)
    require(errors, protocol_occurrences == [PROTOCOL_MODULE], f"Japanese pairwise protocol 9282186 is missing or duplicated: {protocol_occurrences}")
    if protocol_occurrences == [PROTOCOL_MODULE]:
        protocol_events = parse_events(PROTOCOL_MODULE.read_text(encoding="cp1252"))
        protocol = compact(protocol_events[9282186])
        require(errors, "country = JAP" in protocol, "pairwise Japanese protocol 9282186 is not Japan-scoped")

        lifecycle_ids = (
            9282151,
            9282160,
            9282161,
            9282170,
            9282180,
            9282181,
            9282182,
            9282183,
            9282188,
            9282189,
        )
        missing_lifecycle_ids = [event_id for event_id in lifecycle_ids if event_id not in protocol_events]
        require(errors, not missing_lifecycle_ids, f"Japanese armistice lifecycle is missing events {missing_lifecycle_ids}")
        if not missing_lifecycle_ids:
            # The generic lock closes every +1-day gap between a board action
            # and its terms popup, including the first post-victory dispatch.
            claim_board_actions = named_brace_blocks(protocol_events[9282170], "action_c")
            require(errors, len(claim_board_actions) == 1, "major-victory claim lacks exactly one armistice-board action")
            if len(claim_board_actions) == 1:
                validate_dispatch_handoff(
                    errors,
                    "initial major-victory armistice dispatch",
                    claim_board_actions[0],
                    9282180,
                    "IND",
                )

            board_dispatches = (
                ("action_a", 9282181, "British"),
                ("action_b", 9282182, "German"),
                ("action_c", 9282183, "Pacific"),
                ("action_d", 9282036, "Soviet"),
            )
            for action_name, target_event, label in board_dispatches:
                board_actions = named_brace_blocks(protocol_events[9282180], action_name)
                require(errors, len(board_actions) == 1, f"major armistice board lacks exactly one {label} action")
                if len(board_actions) == 1:
                    validate_dispatch_handoff(
                        errors,
                        f"major board to {label} terms",
                        board_actions[0],
                        target_event,
                        "IND",
                    )

            soviet_board_actions = named_brace_blocks(protocol_events[9282180], "action_d")
            if len(soviet_board_actions) == 1:
                soviet_board_action = compact(soviet_board_actions[0])
                soviet_board_commands = named_brace_blocks(soviet_board_actions[0], "command")
                require(
                    errors,
                    soviet_board_action.startswith("action_d = { name ="),
                    "major armistice board can become a zero-action popup when every live opponent lapses",
                )
                stale_dispatch_clears = [
                    block
                    for block in soviet_board_commands
                    if has_flag_effect(block, "clrflag", TERMS_DISPATCHING)
                ]
                require(
                    errors,
                    len(stale_dispatch_clears) == 1
                    and soviet_board_commands.index(stale_dispatch_clears[0]) == 0
                    and compact(stale_dispatch_clears[0])
                    == f"command = {{ type = clrflag which = {TERMS_DISPATCHING} }}",
                    "unconditional board exit does not clear a stale terms-dispatch lock first",
                )
                soviet_live_tokens = (
                    "flag = ind_aubm_soviet_current",
                    "war = { country = IND country = SOV }",
                )
                soviet_relocks = [
                    block
                    for block in soviet_board_commands
                    if has_flag_effect(block, "setflag", TERMS_DISPATCHING)
                ]
                soviet_dispatches = [
                    block
                    for block in soviet_board_commands
                    if "type = event which = 9282036 where = IND when = 1" in block
                ]
                if len(soviet_relocks) == 1 and len(soviet_dispatches) == 1:
                    for block, effect in (
                        (soviet_relocks[0], "re-lock"),
                        (soviet_dispatches[0], "dispatch"),
                    ):
                        require(
                            errors,
                            all(token in block for token in soviet_live_tokens),
                            f"Soviet board {effect} is not conditional on current leverage and a live Soviet war",
                        )

            pacific_dispatches = (
                ("action_a", 9282188, "Japanese"),
                ("action_b", 9282189, "American"),
                ("action_c", 9282180, "main-board return"),
            )
            for action_name, target_event, label in pacific_dispatches:
                pacific_actions = named_brace_blocks(protocol_events[9282183], action_name)
                require(errors, len(pacific_actions) == 1, f"Pacific sub-board lacks exactly one {label} action")
                if len(pacific_actions) == 1:
                    validate_dispatch_handoff(
                        errors,
                        f"Pacific sub-board to {label}",
                        pacific_actions[0],
                        target_event,
                        "IND",
                    )

            pacific_japan_actions = named_brace_blocks(protocol_events[9282183], "action_a")
            if len(pacific_japan_actions) == 1:
                pacific_japan_action = pacific_japan_actions[0]
                pacific_japan_commands = named_brace_blocks(pacific_japan_action, "command")
                dispatch_lock_sets = [
                    block
                    for block in pacific_japan_commands
                    if has_flag_effect(block, "setflag", TERMS_DISPATCHING)
                ]
                southern_classifiers = [
                    block
                    for block in pacific_japan_commands
                    if has_flag_effect(block, "setflag", SOUTHERN_INFLIGHT)
                ]
                terms_dispatches = [
                    block
                    for block in pacific_japan_commands
                    if "type = event which = 9282188 where = IND when = 1" in block
                ]
                require(
                    errors,
                    len(southern_classifiers) == 1,
                    "Pacific Japanese offer does not contain exactly one southern classification",
                )
                if len(southern_classifiers) == 1:
                    require(
                        errors,
                        "NOT = { flag = ind_aubm_japan_major_victory }" in southern_classifiers[0],
                        "Pacific board misclassifies a major Japanese victory as a southern offer",
                    )
                if (
                    len(dispatch_lock_sets) == 1
                    and len(southern_classifiers) == 1
                    and len(terms_dispatches) == 1
                ):
                    require(
                        errors,
                        pacific_japan_commands.index(dispatch_lock_sets[0])
                        < pacific_japan_commands.index(southern_classifiers[0])
                        < pacific_japan_commands.index(terms_dispatches[0]),
                        "Pacific board queues Japanese terms before locking and classifying the offer",
                    )

            for terms_id, label in (
                (9282181, "British terms"),
                (9282182, "German terms"),
                (9282188, "Japanese terms"),
                (9282189, "American terms"),
            ):
                validate_terms_actions_clear_dispatch(
                    errors,
                    label,
                    protocol_events[terms_id],
                    ("action_a", "action_b"),
                )
            validate_terms_actions_clear_dispatch(
                errors,
                "Soviet armistice docket",
                soviet_events[9282036],
                ("action_a", "action_b", "action_c", "action_d"),
            )

            refusal = compact(protocol_events[9282151])
            require(
                errors,
                "type = event which = 9282161 where = IND when = 90" in refusal,
                "Japanese refusal does not schedule the common retry review after 90 days",
            )
            require(
                errors,
                "flag = ind_aubm_major_armistice_target_jap" in refusal
                and has_flag_effect(refusal, "setflag", "ind_aubm_major_armistice_retry_jap"),
                "Japanese refusal does not preserve a Japan-specific retry marker",
            )
            require(
                errors,
                not has_flag_effect(refusal, "clrflag", SOUTHERN_INFLIGHT),
                "Japanese refusal clears southern in-flight state before the 90-day retry",
            )

            retry_review = protocol_events[9282161]
            retry_commands = named_brace_blocks(retry_review, "command")
            retry_dispatch_lock_sets = [
                block for block in retry_commands if has_flag_effect(block, "setflag", TERMS_DISPATCHING)
            ]
            require(
                errors,
                len(retry_dispatch_lock_sets) == 1,
                "90-day retry review does not set exactly one generic terms-dispatch lock",
            )
            retry_dispatch_specs = (
                (
                    "British",
                    9282181,
                    (
                        "flag = ind_aubm_major_armistice_retry_eng",
                        "flag = ind_aubm_britain_current",
                        "war = { country = IND country = ENG }",
                    ),
                ),
                (
                    "German",
                    9282182,
                    (
                        "flag = ind_aubm_major_armistice_retry_ger",
                        "flag = ind_aubm_germany_current",
                        "war = { country = IND country = GER }",
                    ),
                ),
                (
                    "Japanese",
                    9282188,
                    (
                        "flag = ind_aubm_major_armistice_retry_jap",
                        "war = { country = IND country = JAP }",
                        LIVE_JAPAN_LEVERAGE,
                    ),
                ),
                (
                    "American",
                    9282189,
                    (
                        "flag = ind_aubm_major_armistice_retry_usa",
                        "flag = ind_aubm_america_current",
                        "war = { country = IND country = USA }",
                    ),
                ),
            )
            for label, target_event, condition_tokens in retry_dispatch_specs:
                retry_dispatches = [
                    block
                    for block in retry_commands
                    if f"type = event which = {target_event} where = IND when = 1" in block
                ]
                require(
                    errors,
                    len(retry_dispatches) == 1,
                    f"90-day retry review lacks exactly one {label} +1-day dispatch",
                )
                if len(retry_dispatch_lock_sets) == 1:
                    lock_set = retry_dispatch_lock_sets[0]
                    require(
                        errors,
                        any(
                            all(token in branch for token in condition_tokens)
                            for branch in named_brace_blocks(lock_set, "AND")
                        ),
                        f"90-day retry lock does not mirror the valid {label} retry gate",
                    )
                    if len(retry_dispatches) == 1:
                        require(
                            errors,
                            retry_commands.index(lock_set) < retry_commands.index(retry_dispatches[0]),
                            f"90-day {label} retry queues its terms popup before setting the generic lock",
                        )
            japan_retry_dispatches = [
                block
                for block in retry_commands
                if "type = event which = 9282188 where = IND when = 1" in block
            ]
            retry_inflight_sets = [
                block for block in retry_commands if has_flag_effect(block, "setflag", SOUTHERN_INFLIGHT)
            ]
            retry_inflight_clears = [
                block for block in retry_commands if has_flag_effect(block, "clrflag", SOUTHERN_INFLIGHT)
            ]
            require(
                errors,
                len(japan_retry_dispatches) == 1,
                "90-day retry review does not contain exactly one Japanese terms dispatch",
            )
            require(
                errors,
                len(retry_inflight_sets) == 1,
                "90-day retry review does not contain exactly one southern in-flight reconstruction",
            )
            require(
                errors,
                len(retry_inflight_clears) == 1,
                "90-day retry review does not contain exactly one stale in-flight cleanup",
            )

            # Route-neutral theatre history survives a route switch, so every
            # retry branch must pair it with at least one current liberation.
            if len(japan_retry_dispatches) == 1:
                japan_retry = japan_retry_dispatches[0]
                require(
                    errors,
                    "flag = ind_aubm_major_armistice_retry_jap" in japan_retry,
                    "90-day Japanese retry dispatch lacks its opponent-specific marker",
                )
                validate_live_japan_leverage(errors, "90-day Japanese retry dispatch", japan_retry)
                require(
                    errors,
                    "war = { country = IND country = JAP }" in japan_retry,
                    "90-day Japanese retry can reopen after the India-Japan war ends",
                )
                require(
                    errors,
                    not has_flag_effect(japan_retry, "setflag", SOUTHERN_INFLIGHT)
                    and not has_flag_effect(japan_retry, "clrflag", SOUTHERN_INFLIGHT),
                    "queued Japanese retry dispatch mutates in-flight state instead of preserving it",
                )

            if len(retry_inflight_sets) == 1:
                retry_inflight_set = retry_inflight_sets[0]
                require(
                    errors,
                    "flag = ind_aubm_major_armistice_retry_jap" in retry_inflight_set,
                    "90-day in-flight reconstruction lacks the Japanese retry marker",
                )
                require(
                    errors,
                    "NOT = { flag = ind_aubm_japan_major_victory }" in retry_inflight_set,
                    "normal major-victory retry can be mislabeled as a southern in-flight offer",
                )
                require(
                    errors,
                    "war = { country = IND country = JAP }" in retry_inflight_set,
                    "90-day in-flight reconstruction can survive the end of the Japan war",
                )
                validate_live_japan_leverage(errors, "90-day in-flight reconstruction", retry_inflight_set)

            if len(retry_inflight_clears) == 1:
                retry_inflight_clear = retry_inflight_clears[0]
                require(
                    errors,
                    "flag = ind_aubm_major_armistice_retry_jap" in retry_inflight_clear
                    and f"flag = {SOUTHERN_INFLIGHT}" in retry_inflight_clear,
                    "stale in-flight cleanup is not scoped to the Japanese retry and active in-flight state",
                )
                require(
                    errors,
                    STALE_INFLIGHT_GATE in compact(retry_inflight_clear),
                    "stale in-flight cleanup does not cover major victory or loss of the live Japan war/leverage pair",
                )
                validate_live_japan_leverage(errors, "stale in-flight cleanup", retry_inflight_clear)

            # Popup-race regression: reconstruct before queuing 9282188 and do
            # not clear a still-valid in-flight flag during the one-day delay.
            if len(retry_inflight_sets) == 1 and len(japan_retry_dispatches) == 1:
                require(
                    errors,
                    retry_commands.index(retry_inflight_sets[0]) < retry_commands.index(japan_retry_dispatches[0]),
                    "90-day retry queues the terms popup before reconstructing its in-flight guard",
                )
            if len(retry_inflight_clears) == 1 and len(japan_retry_dispatches) == 1:
                require(
                    errors,
                    "war = { country = IND country = JAP }" in compact(japan_retry_dispatches[0])
                    and LIVE_JAPAN_LEVERAGE in compact(japan_retry_dispatches[0])
                    and STALE_INFLIGHT_GATE in compact(retry_inflight_clears[0]),
                    "valid +1-day Japanese dispatch and stale in-flight cleanup are not logical opposites",
                )

            japan_terms_actions = named_brace_blocks(protocol_events[9282188], "action_a")
            require(errors, len(japan_terms_actions) == 1, "retried Japanese terms lack exactly one submission action")
            if len(japan_terms_actions) == 1:
                japan_terms = japan_terms_actions[0]
                validate_live_japan_leverage(errors, "retried Japanese terms", japan_terms)
                require(
                    errors,
                    "war = { country = IND country = JAP }" in japan_terms,
                    "retried Japanese terms can be submitted after the India-Japan war ends",
                )
                terms_commands = named_brace_blocks(japan_terms_actions[0], "command")
                terms_inflight_sets = [
                    block for block in terms_commands if has_flag_effect(block, "setflag", SOUTHERN_INFLIGHT)
                ]
                require(
                    errors,
                    len(terms_inflight_sets) == 1,
                    "Japanese terms do not contain exactly one in-flight reconstruction",
                )
                if len(terms_inflight_sets) == 1:
                    require(
                        errors,
                        "NOT = { flag = ind_aubm_japan_major_victory }" in terms_inflight_sets[0],
                        "normal major-victory terms can be mislabeled as a southern in-flight offer",
                    )
                    japan_target_sets = [
                        block
                        for block in terms_commands
                        if has_flag_effect(block, "setflag", "ind_aubm_major_armistice_target_jap")
                    ]
                    require(
                        errors,
                        len(japan_target_sets) == 1
                        and terms_commands.index(terms_inflight_sets[0])
                        < terms_commands.index(japan_target_sets[0]),
                        "Japanese terms reconstruct in-flight state after opening the remote protocol docket",
                    )

            japan_terms_declines = named_brace_blocks(protocol_events[9282188], "action_b")
            require(errors, len(japan_terms_declines) == 1, "retried Japanese terms lack exactly one continue-war action")
            if len(japan_terms_declines) == 1:
                decline_commands = named_brace_blocks(japan_terms_declines[0], "command")
                board_returns = [
                    block
                    for block in decline_commands
                    if "type = event which = 9282180 where = IND when = 90" in block
                ]
                southern_declines = [
                    block
                    for block in decline_commands
                    if has_flag_effect(block, "setflag", "ind_aubm_japan_southern_armistice_declined")
                ]
                inflight_clears = [
                    block for block in decline_commands if has_flag_effect(block, "clrflag", SOUTHERN_INFLIGHT)
                ]
                require(errors, len(board_returns) == 1, "normal Japanese terms do not return to the major armistice board")
                require(errors, len(southern_declines) == 1, "southern Japanese terms do not record the player's decline")
                require(errors, len(inflight_clears) == 1, "Japanese terms do not clear in-flight state after continuing the war")
                if len(board_returns) == 1:
                    require(
                        errors,
                        NORMAL_BOARD_CONTINUE_GATE in compact(board_returns[0]),
                        "Continue does not return exactly non-in-flight or newly major-victory terms to the normal board",
                    )
                if len(southern_declines) == 1:
                    require(
                        errors,
                        SOUTHERN_DECLINE_GATE in compact(southern_declines[0]),
                        "southern decline is not restricted to in-flight, non-major terms",
                    )
                    require(
                        errors,
                        "war = { country = IND country = JAP }" in compact(southern_declines[0]),
                        "invalidated southern terms can set the decline lock after the India-Japan war ends",
                    )
                    validate_live_japan_leverage(
                        errors,
                        "southern terms decline",
                        southern_declines[0],
                    )
                if len(inflight_clears) == 1:
                    require(
                        errors,
                        compact(inflight_clears[0])
                        == f"command = {{ type = clrflag which = {SOUTHERN_INFLIGHT} }}",
                        "continue-war cleanup does not unconditionally close the in-flight window",
                    )
                if len(southern_declines) == 1 and len(inflight_clears) == 1:
                    require(
                        errors,
                        decline_commands.index(southern_declines[0]) < decline_commands.index(inflight_clears[0]),
                        "southern terms clear in-flight state before recording the decline",
                    )

            ratification_actions = named_brace_blocks(protocol_events[9282160], "action_a")
            require(errors, len(ratification_actions) == 1, "great-power ratification lacks exactly one action")
            if len(ratification_actions) == 1:
                ratification_commands = named_brace_blocks(ratification_actions[0], "command")
                ratification_dispatch_clears = [
                    block
                    for block in ratification_commands
                    if has_flag_effect(block, "clrflag", TERMS_DISPATCHING)
                ]
                require(
                    errors,
                    len(ratification_dispatch_clears) == 1
                    and compact(ratification_dispatch_clears[0])
                    == f"command = {{ type = clrflag which = {TERMS_DISPATCHING} }}",
                    "great-power ratification does not defensively clear the generic terms-dispatch lock",
                )
                ratification_inflight_clears = [
                    block for block in ratification_commands if has_flag_effect(block, "clrflag", SOUTHERN_INFLIGHT)
                ]
                japan_target_clears = [
                    block
                    for block in ratification_commands
                    if has_flag_effect(block, "clrflag", "ind_aubm_major_armistice_target_jap")
                ]
                require(
                    errors,
                    len(ratification_inflight_clears) == 1,
                    "Japanese ratification does not contain exactly one in-flight cleanup",
                )
                if len(ratification_inflight_clears) == 1:
                    require(
                        errors,
                        "flag = ind_aubm_major_armistice_target_jap" in ratification_inflight_clears[0],
                        "ratification can clear southern in-flight state for a non-Japanese opponent",
                    )
                if len(ratification_inflight_clears) == 1 and len(japan_target_clears) == 1:
                    require(
                        errors,
                        ratification_commands.index(ratification_inflight_clears[0])
                        < ratification_commands.index(japan_target_clears[0]),
                        "ratification clears the Japanese target before evaluating in-flight cleanup",
                    )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"Southeast Asia validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Southeast Asia validation passed: 21 unique operational events, four friendly-owner liberation chains, four fleet-backed lanes, one flexible theatre award, and a live-leverage Japanese armistice with cross-opponent dispatch locking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
