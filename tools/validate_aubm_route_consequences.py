#!/usr/bin/env python3
"""Validate AUBM's five route-specific wartime lifecycles."""

from __future__ import annotations

import re
from pathlib import Path

from generate_aubm_route_consequences import LEGACY_WARTIME_IDS, ROUTES


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mod/db/events/aubm_v4/48_route_wartime_consequences.txt"
INDEX = ROOT / "mod/db/events.txt"
VICTORY_AUDIT = ROOT / "mod/db/events/india_v3/62_victory.txt"
EVENT_DIRS = (
    ROOT / "mod/db/events/aubm_v4",
    ROOT / "mod/db/events/india_v3",
)


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
    if not MODULE.exists():
        print(f"ERROR: missing {MODULE.relative_to(ROOT)}")
        return 1

    text = MODULE.read_text(encoding="ascii")
    events = event_blocks(text)
    initializer = events.get(9283200, "")
    index = INDEX.read_text(encoding="cp1252").replace("\\", "/")
    audit = VICTORY_AUDIT.read_text(encoding="cp1252")

    checks += 3
    if index.count('event = "db/events/aubm_v4/48_route_wartime_consequences.txt"') != 1:
        errors.append("route consequences module is not loaded exactly once")
    if "ind_aubm_legacy_wartime_retired" not in initializer:
        errors.append("canonical initializer has no one-time retirement guard")
    if "ind_aubm_occupation_tier_1" not in initializer:
        errors.append("canonical initializer does not migrate old occupation saves")

    for event_id in LEGACY_WARTIME_IDS:
        checks += 1
        if f"sleepevent which = {event_id}" not in initializer:
            errors.append(f"legacy wartime event {event_id} is not retired")

    for live_callback in (9281349, 9281353, 9281390):
        checks += 2
        if live_callback in LEGACY_WARTIME_IDS:
            errors.append(f"live callback {live_callback} remains in the retirement list")
        if f"sleepevent which = {live_callback}" in initializer:
            errors.append(f"live callback {live_callback} is still slept by the initializer")

    loaded_events: dict[int, str] = {}
    for directory in EVENT_DIRS:
        for path in directory.glob("*.txt"):
            loaded_events.update(event_blocks(path.read_text(encoding="cp1252")))
    slept = set(LEGACY_WARTIME_IDS)
    for source_id, block in loaded_events.items():
        if source_id in slept:
            continue
        targets = {int(value) for value in re.findall(r"\btype\s*=\s*event\s+which\s*=\s*(\d+)", block)}
        for target_id in sorted(targets & slept):
            checks += 1
            errors.append(f"live event {source_id} still calls retired callback {target_id}")

    for route_index, route in enumerate(ROUTES):
        charter_id = 9283210 + route_index
        congress_id = 9283270 + route_index
        charter = events.get(charter_id, "")
        congress = events.get(congress_id, "")
        checks += 12
        if route.route_flag not in charter:
            errors.append(f"{route.key} charter omits canonical route flag")
        if "atwar = yes" not in charter:
            errors.append(f"{route.key} charter is not tied to a live war")
        if len(re.findall(r"(?m)^\s*action_[a-d]\s*=", charter)) != 4:
            errors.append(f"{route.key} charter does not offer four doctrines")
        if f"ind_aubm_route_charter_{route.key}" not in charter:
            errors.append(f"{route.key} charter has no completion guard")
        if route.route_flag not in congress or "atwar = no" not in congress:
            errors.append(f"{route.key} congress is not a route-specific postwar event")
        if len(re.findall(r"(?m)^\s*action_[a-c]\s*=", congress)) != 3:
            errors.append(f"{route.key} congress does not offer three postwar orders")
        if route.legacy_flag not in congress:
            errors.append(f"{route.key} congress does not close the long-campaign audit")
        if "ind_aubm_route_war_achievement" not in congress:
            errors.append(f"{route.key} congress can fire without a common war achievement")
        if "ind_aubm_postwar_congress_completed" not in congress:
            errors.append(f"{route.key} congress lacks the global one-congress guard")
        if "year = 1933" not in charter or "year = 1933" not in congress:
            errors.append(f"{route.key} lifecycle cannot acknowledge an early sovereign war")
        if "leave_alliance when = 1" not in congress or "setflag which = ind_aubm_route_sovereign" not in congress:
            errors.append(f"{route.key} strategic-autonomy outcome does not leave its bloc")
        if route.key == "soviet":
            checks += 4
            if "flag = ind_aubm_route_sovereign flag = ind_aubm_socialist_autonomous" not in charter:
                errors.append("autonomous socialism cannot select the Soviet-route wartime charter")
            if "flag = ind_aubm_route_sovereign flag = ind_aubm_socialist_autonomous" not in congress:
                errors.append("autonomous socialism cannot reach the socialist peace congress")
            if "setflag which = ind_v4_sov_autonomous_socialism" not in congress or "setflag which = ind_aubm_socialist_autonomous" not in congress:
                errors.append("socialist strategic autonomy erases India's domestic socialist course")
            if "setflag which = ind_v4_strategy_soviet" not in congress:
                errors.append("socialist strategic autonomy is mislabeled as ordinary non-alignment")
        if route.key == "sovereign":
            checks += 3
            if "NOT = { flag = ind_aubm_socialist_autonomous }" not in charter:
                errors.append("autonomous socialism can receive both socialist and sovereign charters")
            if "clrflag which = ind_aubm_socialist_autonomous" not in congress:
                errors.append("ordinary sovereign autonomy does not clear a stale socialist route marker")
            if "setflag which = ind_v4_strategy_nam" not in congress:
                errors.append("ordinary sovereign autonomy does not restore non-aligned strategy")
        if route.legacy_flag not in audit:
            errors.append(f"1945 audit does not recognize {route.key} settlement flag")

        base = 9283220 + route_index * 10
        for focus_index, focus in enumerate(route.focuses):
            achievement = events.get(base + focus_index, "")
            checks += 10
            focus_flag = f"ind_aubm_route_focus_{route.key}_{focus.key}"
            achievement_flag = f"ind_aubm_route_achievement_{route.key}_{focus.key}"
            if focus_flag not in charter:
                errors.append(f"{route.key}/{focus.key} is missing from its charter")
            if focus_flag not in achievement:
                errors.append(f"{route.key}/{focus.key} achievement lacks its selected doctrine")
            if route.route_flag not in achievement:
                errors.append(f"{route.key}/{focus.key} achievement can fire after India leaves its route")
            if achievement_flag not in achievement:
                errors.append(f"{route.key}/{focus.key} achievement has no one-time guard")
            if focus.trigger not in achievement:
                errors.append(f"{route.key}/{focus.key} achievement trigger drifted from the route map")
            if f"ind_aubm_route_achievement_{route.key}" not in achievement:
                errors.append(f"{route.key}/{focus.key} does not unlock its peace congress")
            if "ind_aubm_route_war_achievement" not in achievement:
                errors.append(f"{route.key}/{focus.key} does not enter the common war ledger")
            if "NOT = { flag = ind_aubm_route_war_achievement }" not in achievement:
                errors.append(f"{route.key}/{focus.key} can stack a second route achievement")
            if "NOT = { flag = ind_aubm_postwar_congress_completed }" not in achievement:
                errors.append(f"{route.key}/{focus.key} can award credit after the final congress")
            if "year = 1933" not in achievement:
                errors.append(f"{route.key}/{focus.key} cannot acknowledge an early sovereign war")

        fallback = events.get(base + 4, "")
        checks += 8
        if f"ind_aubm_route_charter_{route.key}" not in fallback:
            errors.append(f"{route.key} fallback achievement ignores its selected charter")
        if "ind_aubm_global_campaign_victory" not in fallback:
            errors.append(f"{route.key} fallback cannot recognize a generated-country victory")
        if f"ind_aubm_route_achievement_{route.key}_global" not in fallback:
            errors.append(f"{route.key} fallback has no one-time route guard")
        if f"ind_aubm_route_achievement_{route.key}" not in fallback:
            errors.append(f"{route.key} fallback does not unlock its congress")
        if "ind_aubm_route_war_achievement" not in fallback:
            errors.append(f"{route.key} fallback does not enter the common war ledger")
        if "NOT = { flag = ind_aubm_route_war_achievement }" not in fallback:
            errors.append(f"{route.key} fallback can stack with a named achievement")
        if route.route_flag not in fallback:
            errors.append(f"{route.key} fallback can fire after India leaves its route")
        if "year = 1933" not in fallback:
            errors.append(f"{route.key} fallback cannot acknowledge an early war")

        if route.key == "japan":
            dualfront = events.get(base + 1, "")
            checks += 2
            if "ind_aubm_jp_independent_soviet_war" not in dualfront:
                errors.append("Japan dual-front achievement does not require an independently declared Soviet war")
            if "NOT = { alliance = { country = IND country = JAP } }" not in dualfront:
                errors.append("Japan dual-front achievement can be earned through inherited alliance wars")

    for event_id, block in events.items():
        checks += 3
        if "persistent = yes" not in block:
            errors.append(f"route lifecycle event {event_id} is not persistent")
        if re.search(r"\btype\s*=\s*war\b", block):
            errors.append(f"route lifecycle event {event_id} declares war outside the War Cabinet")
        if re.search(r"\btype\s*=\s*peace\b", block):
            errors.append(f"route lifecycle event {event_id} bypasses country-specific settlement")

    if len(ROUTES) != 5:
        errors.append(f"expected five strategic routes, found {len(ROUTES)}")
    checks += 1

    if errors:
        print(f"AUBM route consequence validation failed ({len(errors)} errors, {checks} checks):")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print(f"AUBM route consequence validation passed ({checks} checks, five routes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
