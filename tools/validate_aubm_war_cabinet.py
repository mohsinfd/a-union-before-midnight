#!/usr/bin/env python3
"""Regression gate for the guided War Cabinet and sandbox catalogue."""

from __future__ import annotations

from dataclasses import dataclass
import pathlib
import re
import sys

from validate_aubm_cold_start import (
    UNRESTRICTED_SANDBOX_FLAG,
    has_flag,
    has_war_cabinet_access_gate,
)
from validate_v4 import direct_scalar, extract_blocks, load_text, scalar


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENT_DIRS = (
    ROOT / "mod/db/events/india_v3",
    ROOT / "mod/db/events/aubm_v4",
)
SCENARIO = ROOT / "mod/scenarios/1933.eug"
EVENT_INDEX = ROOT / "mod/db/events.txt"
GLOBAL_MATRIX_MODULE = "47_global_campaign_matrix.txt"

WAR_CABINET_ID = 9281001
EARLY_SANDBOX_ID = 9281008
CAMPAIGN_DOCKETS_ID = 9281012
UNRESTRICTED_CATALOGUE_ID = 9281013
GLOBAL_INDEX_ID = 9282300
CURATED_DISPATCHER_ID = 9289499
TOKYO_OR_SOVEREIGN_ID = 9281914
DECLARATION_EXECUTOR_ID = 9281925
SOVIET_ROUTE_DECISION_IDS = (9281410, 9281411, 9281412)
SOVIET_ROUTE_DESCENDANT_IDS = (
    9281414,
    9281421,
    9281422,
    9281423,
    9281425,
    9281426,
    9281427,
    9281431,
    9281432,
    9281433,
    9281435,
    9281436,
    9281443,
    9281444,
    9281445,
    9281446,
)
ROUTE_FLAGS = {
    "ind_aubm_route_allied",
    "ind_aubm_route_german",
    "ind_aubm_route_soviet",
    "ind_aubm_route_japan",
    "ind_aubm_route_sovereign",
}


@dataclass(frozen=True)
class EventRecord:
    event_id: int
    path: pathlib.Path
    text: str


def load_events() -> dict[int, EventRecord]:
    records: dict[int, EventRecord] = {}
    for directory in EVENT_DIRS:
        for path in sorted(directory.glob("*.txt")):
            for event in extract_blocks(load_text(path), "event"):
                raw_id = scalar(event.text, "id")
                if not raw_id or not raw_id.isdigit():
                    continue
                event_id = int(raw_id)
                if event_id in records:
                    raise ValueError(
                        f"duplicate event ID {event_id} in {records[event_id].path} and {path}"
                    )
                records[event_id] = EventRecord(event_id, path, event.text)
    return records


def actions(event: str) -> list[str]:
    return sum(
        ([block.text for block in extract_blocks(event, f"action_{letter}")] for letter in "abcd"),
        [],
    )


def commands(text: str) -> list[str]:
    return [block.text for block in extract_blocks(text, "command")]


def command_type(command: str) -> str:
    return (direct_scalar(command, "type") or "").lower()


def command_target(command: str) -> int | None:
    if command_type(command) != "event":
        return None
    target = direct_scalar(command, "which")
    return int(target) if target and target.isdigit() else None


def action_targets(action: str) -> list[int]:
    return [
        target
        for command in commands(action)
        if (target := command_target(command)) is not None
    ]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def is_persistent_ind_menu(event: str) -> bool:
    return (
        re.search(r"\brandom\s*=\s*no\b", event) is not None
        and re.search(r"\bpersistent\s*=\s*yes\b", event) is not None
        and re.search(r"(?m)^\s*country\s*=\s*IND\s*$", event) is not None
    )


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def has_canonical_soviet_route_gate(text: str) -> bool:
    compact = normalized(text)
    return all(
        term in compact
        for term in (
            "flag = ind_aubm_route_soviet",
            "flag = ind_aubm_route_sovereign",
            "flag = ind_aubm_socialist_autonomous",
        )
    )


def main() -> int:
    errors: list[str] = []
    checks = 0

    try:
        records = load_events()
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    required_ids = {
        WAR_CABINET_ID,
        EARLY_SANDBOX_ID,
        CAMPAIGN_DOCKETS_ID,
        UNRESTRICTED_CATALOGUE_ID,
        GLOBAL_INDEX_ID,
        CURATED_DISPATCHER_ID,
        TOKYO_OR_SOVEREIGN_ID,
        DECLARATION_EXECUTOR_ID,
        *SOVIET_ROUTE_DECISION_IDS,
        *SOVIET_ROUTE_DESCENDANT_IDS,
    }
    missing = required_ids - records.keys()
    checks += len(required_ids)
    if missing:
        errors.append("missing War Cabinet events: " + ", ".join(map(str, sorted(missing))))

    # Continue collecting useful diagnostics when one optional branch is still
    # being authored, but never index a missing record.
    cabinet = records.get(WAR_CABINET_ID)
    dockets = records.get(CAMPAIGN_DOCKETS_ID)
    catalogue = records.get(UNRESTRICTED_CATALOGUE_ID)
    dispatcher = records.get(CURATED_DISPATCHER_ID)
    tokyo_or_sovereign = records.get(TOKYO_OR_SOVEREIGN_ID)
    declaration_executor = records.get(DECLARATION_EXECUTOR_ID)

    # Old delayed Soviet corridor callbacks can arrive after the player changes
    # alignment. Every player-facing continuation must therefore carry the
    # current Soviet (or sovereign-autonomous-socialist) route gate, while the
    # three entry decisions must apply it both to visibility and execution.
    for event_id in SOVIET_ROUTE_DECISION_IDS:
        record = records.get(event_id)
        if not record:
            continue
        decision_blocks = extract_blocks(record.text, "decision")
        event_actions = actions(record.text)
        checks += 3
        require(
            errors,
            len(decision_blocks) == 1
            and has_canonical_soviet_route_gate(decision_blocks[0].text),
            f"{event_id} exposes a Soviet corridor outside the current Soviet/autonomous route",
        )
        require(errors, bool(event_actions), f"{event_id} has no execution action")
        if event_actions:
            action_triggers = extract_blocks(event_actions[0], "trigger")
            require(
                errors,
                bool(action_triggers)
                and has_canonical_soviet_route_gate(action_triggers[0].text),
                f"{event_id} can execute after its Soviet route becomes stale",
            )

    for event_id in SOVIET_ROUTE_DESCENDANT_IDS:
        record = records.get(event_id)
        if not record:
            continue
        event_actions = actions(record.text)
        checks += 1 + len(event_actions)
        require(errors, bool(event_actions), f"{event_id} has no route-safe reply")
        for index, action in enumerate(event_actions, start=1):
            action_triggers = extract_blocks(action, "trigger")
            require(
                errors,
                bool(action_triggers)
                and has_canonical_soviet_route_gate(action_triggers[0].text),
                f"{event_id} action {index} can resolve without a current Soviet/autonomous route gate",
            )

    afghan_coercion = records.get(9281435)
    if afghan_coercion:
        afghan_actions = actions(afghan_coercion.text)
        checks += 8
        require(errors, len(afghan_actions) == 4, "9281435 must retain three policies plus a stale-state lapse")
        if len(afghan_actions) == 4:
            force_action = normalized(afghan_actions[1])
            lapse_action = normalized(afghan_actions[3])
            for guard in (
                "exists = AFG",
                "NOT = { war = { country = IND country = AFG } }",
                "NOT = { alliance = { country = IND country = AFG } }",
                "NOT = { flag = ind_v3_delhi_pact }",
            ):
                require(
                    errors,
                    guard in force_action,
                    f"9281435 coercion does not recheck Afghan protection: {guard}",
                )
            require(
                errors,
                "type = war which = AFG" in force_action,
                "9281435 coercion no longer owns its explicit Afghan war command",
            )
            require(
                errors,
                all(
                    guard in lapse_action
                    for guard in (
                        "NOT = { exists = AFG }",
                        "war = { country = IND country = AFG }",
                        "alliance = { country = IND country = AFG }",
                        "flag = ind_v3_delhi_pact",
                    )
                ),
                "9281435 lacks a safe lapse when Afghanistan becomes invalid or protected",
            )
            require(
                errors,
                all(
                    "type = war which = AFG" not in normalized(action)
                    for action in (afghan_actions[0], afghan_actions[2], afghan_actions[3])
                ),
                "9281435 exposes an Afghan war command outside its guarded coercion action",
            )

    if tokyo_or_sovereign:
        tokyo_actions = actions(tokyo_or_sovereign.text)
        checks += 3
        require(errors, bool(tokyo_actions), "9281914 has no Tokyo-entry action")
        if tokyo_actions:
            join_triggers = extract_blocks(tokyo_actions[0], "trigger")
            join_trigger = re.sub(r"\s+", " ", join_triggers[0].text) if join_triggers else ""
            require(
                errors,
                "OR = { NOT = { flag = ind_v4_japan_commercial_channel } money = 300 }"
                in join_trigger,
                "9281914 can charge the commercial-channel reversal without reserving 300 money",
            )
            require(
                errors,
                "type = money value = -300" in re.sub(r"\s+", " ", tokyo_actions[0]),
                "9281914 no longer contains the disclosed commercial-channel charge",
            )

    if declaration_executor:
        executor_actions = actions(declaration_executor.text)
        checks += 3
        require(
            errors,
            len(executor_actions) == 2,
            "9281925 must have one issue action and one stale-treaty lapse action",
        )
        if len(executor_actions) == 2:
            issue_action, lapse_action = executor_actions
            war_commands = {
                direct_scalar(command, "which"): re.sub(r"\s+", " ", command)
                for command in commands(issue_action)
                if command_type(command) == "war"
            }
            expected_targets = {
                "ENG": (
                    "alliance = { country = IND country = ENG }",
                    "alliance = { country = IND country = USA }",
                    "flag = ind_aubm_commitment_allied",
                ),
                "GER": (
                    "alliance = { country = IND country = GER }",
                    "flag = ind_aubm_commitment_german",
                ),
                "SOV": (
                    "alliance = { country = IND country = SOV }",
                    "flag = ind_aubm_commitment_soviet",
                ),
                "JAP": (
                    "alliance = { country = IND country = JAP }",
                    "flag = ind_aubm_commitment_japan",
                ),
                "USA": (
                    "alliance = { country = IND country = ENG }",
                    "alliance = { country = IND country = USA }",
                    "flag = ind_aubm_commitment_allied",
                ),
            }
            checks += len(expected_targets)
            for target, guards in expected_targets.items():
                command = war_commands.get(target, "")
                require(
                    errors,
                    bool(command) and all(f"NOT = {{ {guard} }}" in command for guard in guards),
                    f"9281925 does not recheck {target}'s live alliance/commitment before war",
                )

            regional_targets = {
                "PER", "IRQ", "SAU", "AFG", "TIB", "SIK", "CHI", "CHC", "SIA",
                "ITA", "FRA", "POR", "TUR", "U05", "HOL", "AST", "NZL", "OMN",
                "YEM", "ETH", "SAF",
            }
            checks += len(regional_targets)
            for target in regional_targets:
                command = war_commands.get(target, "")
                alliance_guard = f"NOT = {{ alliance = {{ country = IND country = {target} }} }}"
                require(
                    errors,
                    bool(command) and alliance_guard in command,
                    f"9281925 does not recheck {target}'s live alliance before war",
                )

            lapse_text = re.sub(r"\s+", " ", lapse_action)
            great_power_flags = {
                "ind_aubm_declare_eng",
                "ind_aubm_declare_ger",
                "ind_aubm_declare_sov",
                "ind_aubm_declare_jap",
                "ind_aubm_declare_usa",
            }
            checks += len(great_power_flags) + 1
            for flag in great_power_flags:
                require(
                    errors,
                    f"type = clrflag which = {flag}" in lapse_text,
                    f"9281925 stale-treaty lapse does not clear {flag}",
                )
            require(
                errors,
                "ind_aubm_war_declared_by_cabinet" not in lapse_text,
                "9281925 records a declaration after a new treaty cancels it",
            )

    if cabinet:
        checks += 9
        require(errors, is_persistent_ind_menu(cabinet.text), "9281001 is not a permanent IND menu")
        for block_name in ("decision", "decision_trigger"):
            blocks = extract_blocks(cabinet.text, block_name)
            require(
                errors,
                len(blocks) == 1 and has_war_cabinet_access_gate(blocks[0].text),
                f"9281001 {block_name} lacks the Union plus 1937/war/sandbox access gate",
            )

        cabinet_actions = actions(cabinet.text)
        require(errors, len(cabinet_actions) == 4, "9281001 must remain a four-action top-level menu")
        expected_targets = ([9281910], [CURATED_DISPATCHER_ID], [CAMPAIGN_DOCKETS_ID], [])
        if len(cabinet_actions) == 4:
            for index, (menu_action, expected) in enumerate(
                zip(cabinet_actions, expected_targets), start=1
            ):
                require(
                    errors,
                    action_targets(menu_action) == expected,
                    f"9281001 action {index} targets {action_targets(menu_action)}, expected {expected}",
                )
        require(
            errors,
            GLOBAL_INDEX_ID not in action_targets(cabinet.text),
            "9281001 exposes the unrestricted country index at top level",
        )
        require(
            errors,
            UNRESTRICTED_CATALOGUE_ID not in action_targets(cabinet.text),
            "9281001 skips the campaign-docket nesting level",
        )

    if dispatcher:
        checks += 10
        require(
            errors,
            is_persistent_ind_menu(dispatcher.text),
            "9289499 is not a permanent curated IND dispatcher",
        )
        dispatcher_module = dispatcher.path.relative_to(ROOT / "mod").as_posix()
        event_index = load_text(EVENT_INDEX).replace("\\", "/")
        require(
            errors,
            event_index.count(f'event = "{dispatcher_module}"') == 1,
            f"9289499 module {dispatcher_module} is not loaded exactly once",
        )
        require(
            errors,
            not extract_blocks(dispatcher.text, "decision")
            and not extract_blocks(dispatcher.text, "decision_trigger"),
            "9289499 is independently exposed instead of remaining beneath the War Cabinet",
        )
        dispatcher_language = " ".join(
            filter(None, (scalar(dispatcher.text, "name"), scalar(dispatcher.text, "desc")))
        ).lower()
        require(
            errors,
            "route" in dispatcher_language
            and ("authored" in dispatcher_language or "curated" in dispatcher_language),
            "9289499 does not identify itself as the authored route dispatcher",
        )
        dispatcher_actions = actions(dispatcher.text)
        require(errors, len(dispatcher_actions) == 4, "9289499 must remain a four-action dispatcher")
        dispatcher_commands = commands(dispatcher.text)
        require(
            errors,
            bool(dispatcher_commands) and all(command_type(command) == "event" for command in dispatcher_commands),
            "9289499 mutates game state instead of dispatching to authored menus",
        )
        dispatcher_targets = action_targets(dispatcher.text)
        require(
            errors,
            all(has_flag(dispatcher.text, flag) for flag in ROUTE_FLAGS),
            "9289499 does not route all five commitment families through authored actions",
        )
        require(
            errors,
            WAR_CABINET_ID in dispatcher_targets,
            "9289499 has no return to the National War Cabinet",
        )
        require(
            errors,
            GLOBAL_INDEX_ID not in dispatcher_targets
            and UNRESTRICTED_CATALOGUE_ID not in dispatcher_targets,
            "9289499 mixes the unrestricted catalogue into curated route operations",
        )
        require(
            errors,
            len(set(dispatcher_targets) - {WAR_CABINET_ID}) >= 2,
            "9289499 does not expose multiple authored operation pages",
        )

    if dockets:
        checks += 7
        require(errors, is_persistent_ind_menu(dockets.text), "9281012 is not a permanent IND submenu")
        docket_actions = actions(dockets.text)
        require(errors, len(docket_actions) == 4, "9281012 must remain a four-action submenu")
        expected_targets = ([9281913], [9281911], [9281912], [UNRESTRICTED_CATALOGUE_ID])
        if len(docket_actions) == 4:
            for index, (menu_action, expected) in enumerate(
                zip(docket_actions, expected_targets), start=1
            ):
                require(
                    errors,
                    action_targets(menu_action) == expected,
                    f"9281012 action {index} targets {action_targets(menu_action)}, expected {expected}",
                )
        require(
            errors,
            GLOBAL_INDEX_ID not in action_targets(dockets.text),
            "9281012 bypasses the unrestricted-catalogue disclosure page",
        )
        require(
            errors,
            UNRESTRICTED_CATALOGUE_ID in action_targets(dockets.text),
            "9281012 does not nest the unrestricted catalogue beneath campaign dockets",
        )

    if catalogue:
        checks += 14
        require(
            errors,
            is_persistent_ind_menu(catalogue.text),
            "9281013 is not a permanent unrestricted-catalogue menu",
        )
        require(
            errors,
            not extract_blocks(catalogue.text, "decision")
            and not extract_blocks(catalogue.text, "decision_trigger"),
            "9281013 is independently exposed instead of remaining nested",
        )
        catalogue_language = " ".join(
            filter(None, (scalar(catalogue.text, "name"), scalar(catalogue.text, "desc")))
        ).lower()
        for term in ("210-country", "optional", "permanent", "no reward"):
            require(errors, term in catalogue_language, f"9281013 does not disclose {term}")

        catalogue_actions = actions(catalogue.text)
        require(errors, len(catalogue_actions) == 4, "9281013 must remain a four-action submenu")
        if len(catalogue_actions) == 4:
            enable, open_index, return_to_cabinet, close = catalogue_actions
            enable_commands = commands(enable)
            require(
                errors,
                any(
                    has_flag(block.text, UNRESTRICTED_SANDBOX_FLAG)
                    for block in extract_blocks(enable, "NOT")
                ),
                "9281013 enable action is visible after the sandbox is already enabled",
            )
            require(
                errors,
                sorted(command_type(command) for command in enable_commands) == ["event", "setflag"]
                and any(
                    command_type(command) == "setflag"
                    and direct_scalar(command, "which") == UNRESTRICTED_SANDBOX_FLAG
                    for command in enable_commands
                )
                and action_targets(enable) == [UNRESTRICTED_CATALOGUE_ID],
                "9281013 enable action must only set the sandbox flag and reopen its disclosure page",
            )
            require(
                errors,
                has_flag(open_index, UNRESTRICTED_SANDBOX_FLAG)
                and [command_type(command) for command in commands(open_index)] == ["event"]
                and action_targets(open_index) == [GLOBAL_INDEX_ID],
                "9281013 opens the 210-country index without the permanent sandbox flag",
            )
            require(
                errors,
                [command_type(command) for command in commands(return_to_cabinet)] == ["event"]
                and action_targets(return_to_cabinet) == [WAR_CABINET_ID],
                "9281013 return action does not lead back to the National War Cabinet",
            )
            require(errors, not commands(close), "9281013 close action has gameplay effects")

    # The generated global matrix legitimately links its pages back to its own
    # index. Every hand-authored entry point must pass through 9281013 so the
    # optional/permanent/no-reward disclosure cannot be skipped.
    direct_index_callers: list[int] = []
    sandbox_setters: list[int] = []
    sandbox_clearers: list[int] = []
    for record in records.values():
        for command in commands(record.text):
            if command_target(command) == GLOBAL_INDEX_ID and record.path.name != GLOBAL_MATRIX_MODULE:
                direct_index_callers.append(record.event_id)
            if (
                command_type(command) == "setflag"
                and direct_scalar(command, "which") == UNRESTRICTED_SANDBOX_FLAG
            ):
                sandbox_setters.append(record.event_id)
            if (
                command_type(command) == "clrflag"
                and direct_scalar(command, "which") == UNRESTRICTED_SANDBOX_FLAG
            ):
                sandbox_clearers.append(record.event_id)

    checks += 4
    require(
        errors,
        sorted(set(direct_index_callers)) == [UNRESTRICTED_CATALOGUE_ID],
        "hand-authored events bypass 9281013 when opening 9282300: "
        + ", ".join(map(str, sorted(set(direct_index_callers)))),
    )
    require(
        errors,
        set(sandbox_setters) == {EARLY_SANDBOX_ID, UNRESTRICTED_CATALOGUE_ID},
        "unreviewed events set the unrestricted-sandbox flag: "
        + ", ".join(map(str, sorted(set(sandbox_setters)))),
    )
    require(errors, not sandbox_clearers, "the permanent sandbox flag is cleared by an event")
    require(
        errors,
        not re.search(
            rf"(?m)^\s*{re.escape(UNRESTRICTED_SANDBOX_FLAG)}\s*=\s*1\s*$",
            load_text(SCENARIO),
        ),
        "fresh 1933 starts with unrestricted sandbox access enabled",
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"AUBM War Cabinet validation failed ({checks} checks, {len(errors)} errors).")
        return 1

    print(f"AUBM War Cabinet validation passed ({checks} checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
