#!/usr/bin/env python3
"""Validate Alpha 23's five authored strategic-route campaign overlays."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from generate_aubm_bespoke_route_arcs import (
    ALPHA23_CONTRACT_FLAG,
    CRISIS_CONFIRMATIONS,
    CRISIS_DOCKET_IDS,
    CRISIS_ROUTE_TARGETS,
    DISPATCHER_ID,
    OUTPUT,
    ROUTES,
    crisis_partner_enemy_condition,
    declaration_legality,
    limited_support_effect_commands,
    relationship_condition,
    render,
    resettable_current_flags,
    resource_costs,
    route_condition,
    sovereign_member_condition,
)


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "mod/db/events.txt"
EVENT_DIRS = (ROOT / "mod/db/events/aubm_v4", ROOT / "mod/db/events/india_v3")
FORBIDDEN_DIRECT_COMMANDS = {
    "alliance", "inherit", "independence", "make_puppet", "peace", "secedearea",
    "secedeprovince", "secederegion", "war",
}
RESOURCE_TRIGGERS = {"money": "money", "supplies": "supplies", "oilpool": "oil"}


def braced_blocks(text: str, pattern: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(pattern, text, re.MULTILINE):
        opening = text.find("{", match.start())
        depth = 0
        quoted = False
        escaped = False
        for position in range(opening, len(text)):
            char = text[position]
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
                    blocks.append(text[match.start(): position + 1])
                    break
    return blocks


def event_blocks(text: str) -> dict[int, str]:
    events: dict[int, str] = {}
    for block in braced_blocks(text, r"^\s*event\s*=\s*\{"):
        event_id = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
        if event_id:
            events[int(event_id.group(1))] = block
    return events


def action_blocks(event: str) -> dict[str, str]:
    actions: dict[str, str] = {}
    for block in braced_blocks(event, r"^\s*action_([a-d])\s*=\s*\{"):
        letter = re.search(r"action_([a-d])", block)
        if letter:
            actions[letter.group(1)] = block
    return actions


def quoted_field(block: str, field: str) -> str:
    match = re.search(rf'(?m)^\s*{field}\s*=\s*"([^"]*)"', block)
    return match.group(1) if match else ""


def command_types(block: str) -> list[str]:
    return re.findall(r"\bcommand\s*=\s*\{[^{}]*?\btype\s*=\s*([a-zA-Z0-9_]+)", block)


def main() -> int:
    errors: list[str] = []
    checks = 0
    if not OUTPUT.exists():
        print(f"ERROR: missing {OUTPUT.relative_to(ROOT)}")
        return 1

    text = OUTPUT.read_text(encoding="ascii")
    events = event_blocks(text)
    expected_ids = {DISPATCHER_ID}
    for route in ROUTES:
        expected_ids.update(range(route.base, route.base + 25))
    expected_ids.update(CRISIS_DOCKET_IDS.values())
    expected_ids.update(range(9289645, 9289653))
    expected_ids.add(9289698)
    expected_ids.add(9289699)
    checks += 3
    if text != render():
        errors.append("generated module is stale relative to its generator")
    if set(events) != expected_ids:
        errors.append(f"event inventory differs: missing={sorted(expected_ids - set(events))}, extra={sorted(set(events) - expected_ids)}")
    index = INDEX.read_text(encoding="cp1252").replace("\\", "/")
    if index.count('event = "db/events/aubm_v4/51_bespoke_route_arcs.txt"') != 1:
        errors.append("module 51 is not loaded exactly once")
    for malformed_label in ("London or washington", "The delhi regional council"):
        checks += 1
        if malformed_label in text:
            errors.append(f"generated partner prose contains malformed capitalization: {malformed_label}")

    # New IDs must remain globally unique, including the dispatcher immediately below the band.
    counts: Counter[int] = Counter()
    for directory in EVENT_DIRS:
        for path in directory.glob("*.txt"):
            for event_id in event_blocks(path.read_text(encoding="cp1252", errors="replace")):
                counts[event_id] += 1
    for event_id in sorted(expected_ids):
        checks += 1
        if counts[event_id] != 1:
            errors.append(f"event id {event_id} appears {counts[event_id]} times across loaded Indian modules")
    for event_id, block in events.items():
        checks += 1
        description = quoted_field(block, "desc")
        if len(description.encode("cp1252")) > 500:
            errors.append(f"event {event_id} description exceeds the 500-byte UI limit")
        for letter, action in action_blocks(block).items():
            checks += 1
            label = quoted_field(action, "name")
            if len(label.encode("cp1252")) > 58:
                errors.append(f"event {event_id} action {letter} label exceeds the 58-byte UI limit")

    dispatcher = events.get(DISPATCHER_ID, "")
    dispatch_actions = action_blocks(dispatcher)
    checks += 12
    if "persistent = yes" not in dispatcher or "country = IND" not in dispatcher:
        errors.append("9289499 is not a persistent Indian dispatcher")
    if set(dispatch_actions) != set("abcd"):
        errors.append("9289499 does not expose exactly four actions")
    if "date =" in dispatcher or "decision =" in dispatcher or "decision_trigger" in dispatcher:
        errors.append("9289499 bypasses the War Cabinet gate with a dated or decision entry")
    for route in ROUTES:
        if route.route_flag not in dispatcher or f"which = {route.base}" not in dispatcher:
            errors.append(f"dispatcher omits the {route.key} route-aware operations board")
    if "which = 9281913" not in dispatcher or "which = 9281001" not in dispatcher:
        errors.append("dispatcher lacks shared-ledger or War Cabinet return links")
    if "9282300" in dispatcher or "9281013" in dispatcher:
        errors.append("dispatcher uses a retired or unrestricted bypass target")
    if any(kind != "event" for kind in command_types(dispatcher)):
        errors.append("dispatcher contains a non-event command")

    watchdog = events.get(9289698, "")
    watchdog_action = action_blocks(watchdog).get("a", "")
    checks += len(resettable_current_flags()) + 12
    if not all(token in watchdog for token in ("persistent = yes", "one_action = yes", "year = 1937", ALPHA23_CONTRACT_FLAG)):
        errors.append("route-mismatch watchdog lacks its persistent Alpha23/date contract")
    for route in ROUTES:
        if f"flag = ind_aubm_route_charter_{route.key}" not in watchdog or f"NOT = {{ {route.route_trigger} }}" not in watchdog:
            errors.append(f"route-mismatch watchdog omits the {route.key} charter/current-route mismatch")
    for flag in resettable_current_flags():
        if f"clrflag which = {flag}" not in watchdog_action:
            errors.append(f"route-mismatch watchdog omits shared live-state reset flag {flag}")
    if "setflag which = ind_aubm_bespoke_route_contract_reset_alpha23" not in watchdog_action:
        errors.append("route-mismatch watchdog does not record the centralized contract reset")
    if "which = 9289699" in watchdog_action or "type = event" in watchdog_action:
        errors.append("route-mismatch watchdog creates a second administrative reset popup")
    if set(command_types(watchdog_action)) - {"clrflag", "setflag"}:
        errors.append("route-mismatch watchdog mutates more than shared current flags")

    reset = events.get(9289699, "")
    checks += len(resettable_current_flags()) + 8
    for flag in resettable_current_flags():
        if f"clrflag which = {flag}" not in reset:
            errors.append(f"lawful-withdrawal reset omits live flag {flag}")
    preserved_markers = (
        "clrflag which = ind_aubm_bespoke_focus_culminated_",
        "clrflag which = ind_aubm_bespoke_focus_intermediate_",
        "clrflag which = ind_aubm_bespoke_focus_dilemma_",
        "clrflag which = ind_aubm_bespoke_partner_crisis_",
        "clrflag which = ind_aubm_bespoke_partner_collapse_",
        "clrflag which = ind_aubm_route_achievement_",
        "clrflag which = ind_aubm_congress_entitlement_",
        "clrflag which = ind_aubm_route_war_achievement",
        "clrflag which = ind_aubm_national_",
        "clrflag which = ind_aubm_japan_grand_campaign_complete",
        "clrflag which = ind_aubm_japan_grand_",
        "clrflag which = ind_aubm_japan_caucasus_relief_",
    )
    if any(marker in reset for marker in preserved_markers):
        errors.append("lawful-withdrawal reset destroys earned historical/congress/achievement state")
    for route in ROUTES:
        for suffix in ("done", "accepted", "countered", "refused", "absent"):
            checks += 1
            flag = f"ind_aubm_bespoke_partner_response_{route.key}_{suffix}"
            if f"clrflag which = {flag}" in reset:
                errors.append(f"lawful-withdrawal reset reopens paid partner result {flag}")
    paid_choice_flags = {
        option.flag
        for route in ROUTES
        for option in (*route.collapse_choices, *(option for focus in route.focuses for option in focus.choices))
    }
    for flag in paid_choice_flags:
        checks += 1
        if f"clrflag which = {flag}" in reset:
            errors.append(f"lawful-withdrawal reset reopens paid choice {flag}")
    if set(command_types(reset)) - {"clrflag", "setflag"}:
        errors.append("lawful-withdrawal reset mutates more than current flags")

    wartime = (ROOT / "mod/db/events/aubm_v4/41_wartime_state.txt").read_text(encoding="cp1252")
    wartime_events = event_blocks(wartime)
    withdrawal = action_blocks(event_blocks(wartime).get(9281914, "")).get("c", "")
    if "which = 9289699" not in withdrawal:
        errors.append("legal withdrawal 9281914 action C does not invoke centralized Alpha23 reset 9289699")
    for transition_id in (9281997, 9281998):
        checks += 1
        transition = wartime_events.get(transition_id, "")
        if "which = 9289699" not in transition and "setflag which = ind_aubm_route_sovereign" not in transition:
            errors.append(f"automatic route transition {transition_id} neither resets Alpha23 nor creates a watchdog-visible route mismatch")

    # A queued regional declaration is revalidated at both the visible docket
    # and the delayed foreign-ministry executor.  Otherwise a same-day pact
    # ratification can turn a formerly legal target into a Delhi Pact partner.
    delhi_target_guards = {
        "PER": (9281916, "a", ("ind_v3_delhi_pact",)),
        "AFG": (9281917, "a", ("ind_v3_delhi_pact",)),
        "CHI": (
            9281918,
            "a",
            (
                "ind_v3_delhi_pact",
                "ind_v42_delhi_pact_alliance",
                "ind_v42_delhi_china_alliance",
                "ind_v42_delhi_pact_consultative",
                "ind_v42_china_accepts_delhi_pact",
            ),
        ),
        "SIA": (
            9281918,
            "c",
            (
                "ind_v3_delhi_pact",
                "ind_v42_delhi_pact_alliance",
                "ind_v42_delhi_siam_alliance",
                "ind_v42_delhi_pact_consultative",
                "ind_v42_siam_accepts_delhi_pact",
            ),
        ),
    }
    executor = wartime_events.get(9281925, "")
    executor_commands = braced_blocks(executor, r"^\s*command\s*=\s*\{")
    for country, (docket_id, letter, guards) in delhi_target_guards.items():
        docket_action = action_blocks(wartime_events.get(docket_id, "")).get(letter, "")
        war_commands = [
            command for command in executor_commands
            if f"type = war which = {country}" in command
        ]
        checks += 2 + (2 * len(guards))
        if len(war_commands) != 1:
            errors.append(f"foreign-ministry executor does not contain exactly one {country} declaration")
            continue
        executor_command = war_commands[0]
        for guard in guards:
            if guard not in docket_action:
                errors.append(f"regional docket {docket_id} action {letter} does not guard {country} with {guard}")
            if guard not in executor_command:
                errors.append(f"foreign-ministry executor does not revalidate {country} against {guard}")
        if country in {"CHI", "SIA"}:
            consultative_guard = (
                "NOT = { AND = { flag = ind_v42_delhi_pact_consultative "
                f"flag = ind_v42_{'china' if country == 'CHI' else 'siam'}_accepts_delhi_pact }} }}"
            )
            checks += 2
            if consultative_guard not in docket_action:
                errors.append(f"regional docket {docket_id} action {letter} does not couple {country}'s consultative membership")
            if consultative_guard not in executor_command:
                errors.append(f"foreign-ministry executor does not couple {country}'s consultative membership")
    route_module = (ROOT / "mod/db/events/aubm_v4/48_route_wartime_consequences.txt").read_text(encoding="cp1252")
    route_events = event_blocks(route_module)
    global_campaign_module = (ROOT / "mod/db/events/aubm_v4/47_global_campaign_matrix.txt").read_text(encoding="cp1252")
    checks += 1
    if "OR = { flag = ind_aubm_coalition_credit flag = ind_aubm_coalition_consultation" not in global_campaign_module:
        errors.append("shared coalition-consultation standing has no settlement-system consumer")
    for charter_id in range(9283210, 9283215):
        checks += 2
        if "NOT = { flag = ind_aubm_postwar_congress_completed }" not in route_events.get(charter_id, ""):
            errors.append(f"charter {charter_id} can select a second primary after global congress completion")
        if "NOT = { flag = ind_aubm_route_war_achievement }" not in route_events.get(charter_id, ""):
            errors.append(f"charter {charter_id} can select a second primary after earned route victory")
    legacy_german = event_blocks((ROOT / "mod/db/events/aubm_v4/37_german_campaigns.txt").read_text(encoding="cp1252")).get(9281353, "")
    checks += 1
    if f"NOT = {{ flag = {ALPHA23_CONTRACT_FLAG} }}" not in legacy_german:
        errors.append("legacy German collapse 9281353 can race the Alpha23 authored collapse")

    stage_titles: set[str] = set()
    stage_descs: set[str] = set()
    all_focus_flags = {
        f"ind_aubm_route_focus_{route.key}_{focus.key}"
        for route in ROUTES for focus in route.focuses
    }
    for route in ROUTES:
        status = events.get(route.base, "")
        crisis = events.get(route.base + 1, "")
        primary_response = events.get(route.base + 2, "")
        secondary = events.get(route.base + 3, "")
        collapse = events.get(route.base + 4, "")
        crisis_docket = events.get(CRISIS_DOCKET_IDS[route.key], "")
        checks += 34
        if set(action_blocks(status)) != set("abcd") or f"which = {DISPATCHER_ID}" not in status:
            errors.append(f"{route.key} status board is not a four-way persistent menu with dispatcher return")
        if "zero-reward" not in secondary.lower() or "persistent = yes" not in secondary:
            errors.append(f"{route.key} secondary ledger is not a repeatable zero-reward review")
        if "ind_aubm_route_war_achievement" in secondary or "ind_aubm_congress_entitlement" in secondary:
            errors.append(f"{route.key} secondary ledger can complete the primary route")
        if "year = 1937" not in crisis or route.compact_condition not in crisis:
            errors.append(f"{route.key} compact-entry crisis lacks its 1937 separate-command gate")
        if set(action_blocks(crisis)) != set("abcd") or f"which = {CRISIS_DOCKET_IDS[route.key]}" not in crisis:
            errors.append(f"{route.key} compact-entry crisis lacks four legal choices/contextual war docket")
        if "which = 9281911" in crisis:
            errors.append(f"{route.key} compact-entry crisis leaks into the unrestricted generic war board")
        expected_docket_actions = set("abc" if len(CRISIS_ROUTE_TARGETS[route.key]) == 2 else "abcd")
        docket_actions = action_blocks(crisis_docket)
        if set(docket_actions) != expected_docket_actions:
            errors.append(f"{route.key} contextual war docket has the wrong target/return actions")
        if "date =" in crisis_docket or "offset =" in crisis_docket:
            errors.append(f"{route.key} contextual war docket is dated instead of manual-only")
        if route.crisis_targets not in quoted_field(crisis_docket, "desc"):
            errors.append(f"{route.key} contextual war docket does not name its bounded enemies")
        for letter, country in zip("abc", CRISIS_ROUTE_TARGETS[route.key]):
            action = docket_actions.get(letter, "")
            confirmation_id, _ = CRISIS_CONFIRMATIONS[country]
            required = (
                ALPHA23_CONTRACT_FLAG,
                route_condition(route),
                relationship_condition(route),
                f"ind_aubm_bespoke_partner_crisis_{route.key}_separate_campaign",
                f"exists = {country}",
                f"NOT = {{ war = {{ country = IND country = {country} }} }}",
                crisis_partner_enemy_condition(route, country),
                declaration_legality(country),
                f"type = event which = {confirmation_id} where = IND when = 1",
            )
            checks += len(required)
            for token in required:
                if token not in action:
                    errors.append(f"{route.key} contextual war action {letter}/{country} omits {token}")
            if set(command_types(action)) != {"event"}:
                errors.append(f"{route.key} contextual war action {letter}/{country} bypasses confirmation authority")
        return_letter = "c" if len(CRISIS_ROUTE_TARGETS[route.key]) == 2 else "d"
        if f"which = {DISPATCHER_ID}" not in docket_actions.get(return_letter, ""):
            errors.append(f"{route.key} contextual war docket lacks a safe return")
        allowed_confirmation_ids = {
            CRISIS_CONFIRMATIONS[country][0]
            for country in CRISIS_ROUTE_TARGETS[route.key]
        }
        linked_confirmation_ids = {
            int(event_id)
            for event_id in re.findall(r"\btype\s*=\s*event\s+which\s*=\s*(\d+)", crisis_docket)
            if int(event_id) in set(range(9281920, 9281925))
        }
        if linked_confirmation_ids != allowed_confirmation_ids:
            errors.append(f"{route.key} contextual war docket exposes non-route confirmation targets")
        if route.key == "sovereign":
            if "which = 9281910" in crisis or not all(token in crisis for token in ("ind_aubm_bespoke_partner_crisis_sovereign_independent_plan", "ind_aubm_bespoke_partner_crisis_sovereign_armed_neutrality")):
                errors.append("sovereign crisis uses impossible bloc-withdrawal semantics instead of independent plan/armed neutrality")
            sovereign_action_a = action_blocks(crisis).get("a", "")
            if "ind_aubm_victory_sovereign_credit" in sovereign_action_a or "ind_aubm_route_war_achievement" in sovereign_action_a:
                errors.append("sovereign independent response plan grants unearned victory credit")
            if not all(token in crisis for token in (
                "ind_v42_delhi_pact_consultative",
                "ind_v42_delhi_china_alliance",
                "ind_v42_delhi_siam_alliance",
                sovereign_member_condition("CHI"),
                sovereign_member_condition("SIA"),
            )):
                errors.append("sovereign crisis does not recognize and couple wars to actual V4 Delhi Pact members")
        elif "which = 9281910" not in crisis:
            errors.append(f"{route.key} compact-entry crisis omits lawful formal-entry/withdrawal review")
        if f"ind_aubm_bespoke_partner_crisis_{route.key}_resolved" not in crisis:
            errors.append(f"{route.key} compact-entry crisis lacks a one-resolution guard")
        support_action = action_blocks(crisis).get("c", "")
        support_flag = f"ind_aubm_bespoke_partner_crisis_{route.key}_limited_support"
        support_effects = limited_support_effect_commands(route)
        checks += len(support_effects) + 9
        if "earn consultation" not in quoted_field(support_action, "name"):
            errors.append(f"{route.key} paid limited support does not advertise its immediate benefit")
        if not all(token in support_action for token in (
            "supplies value = -600",
            "money value = -150",
            f"setflag which = {support_flag}",
            f"setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_resolved",
            "setflag which = ind_aubm_coalition_consultation",
            "dissent value = -1",
            "type = relation",
        )):
            errors.append(f"{route.key} paid limited support lacks its cost, relation, consultation or one-shot effect")
        for effect in support_effects:
            if f"command = {{ {effect} }}" not in support_action:
                errors.append(f"{route.key} limited-support flag lacks mechanical consumer/effect: {effect}")
        first_set = support_action.find(f"setflag which = {support_flag}")
        first_consumer = support_action.find(f"flag = {support_flag}")
        if first_set < 0 or first_consumer < first_set:
            errors.append(f"{route.key} limited-support effects run before their state is established")
        if set(command_types(support_action)) - {"supplies", "money", "setflag", "relation", "dissent"}:
            errors.append(f"{route.key} paid limited support bypasses safe India-scoped effects")
        if f"ind_aubm_bespoke_partner_response_{route.key}_pending" not in primary_response:
            # Foreign scope cannot inspect IND's flag; the request is locked before dispatch.
            if f"ind_aubm_bespoke_partner_request_{route.key}_" not in text:
                errors.append(f"{route.key} partner reaction has no locked request context")
        if f"ind_aubm_bespoke_partner_collapse_{route.key}_handled" not in collapse or set(action_blocks(collapse)) != set("abcd"):
            errors.append(f"{route.key} partner-collapse reaction is not a guarded four-way dilemma")
        if route.key != "sovereign" and "alliance = { country = IND" not in collapse:
            errors.append(f"{route.key} partner-collapse reaction excludes formal alliance service")
        if route.key == "sovereign" and not all(flag in collapse for flag in ("ind_v42_delhi_pact_consultative", "ind_v42_siam_accepts_delhi_pact", "ind_v42_china_accepts_delhi_pact", "alliance = { country = IND country = SIA }", "alliance = { country = IND country = CHI }")):
            errors.append("sovereign collapse can mistake an enemy for a Delhi-system partner")
        if route.key == "german" and "ind_gc_german_collapse_answered" not in collapse:
            errors.append("German collapse reaction is not cross-guarded with the existing bespoke chain")
        if ALPHA23_CONTRACT_FLAG not in collapse:
            errors.append(f"{route.key} authored collapse can fire outside an Alpha23 charter")

        callbacks = [events.get(route.base + offset, "") for offset in (22, 23, 24)]
        for callback in callbacks:
            checks += 3
            if not all(token in callback for token in (
                route.route_flag,
                f"ind_aubm_bespoke_partner_response_{route.key}_pending",
                f"ind_aubm_bespoke_partner_response_{route.key}_done",
            )):
                errors.append(f"{route.key} partner callback lacks exact current-route/pending/done guards")
            if "persistent = yes" not in callback:
                errors.append(f"{route.key} partner callback is not reusable across save/load")

        for focus_index, focus in enumerate(route.focuses):
            ids = (
                route.base + 5 + focus_index,
                route.base + 9 + focus_index,
                route.base + 13 + focus_index,
                route.base + 17 + focus_index,
            )
            blocks = [events.get(event_id, "") for event_id in ids]
            focus_flag = f"ind_aubm_route_focus_{route.key}_{focus.key}"
            active_flag = f"ind_aubm_bespoke_focus_active_{route.key}_{focus.key}"
            intermediate_flag = f"ind_aubm_bespoke_focus_intermediate_{route.key}_{focus.key}"
            dilemma_flag = f"ind_aubm_bespoke_focus_dilemma_{route.key}_{focus.key}"
            culmination_flag = f"ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key}"
            checks += 32
            for event_id, block in zip(ids, blocks):
                if not block:
                    errors.append(f"missing {route.key}/{focus.key} stage event {event_id}")
                    continue
                if not all(token in block for token in ("year = 1937", ALPHA23_CONTRACT_FLAG, route.route_flag, focus_flag)):
                    errors.append(f"event {event_id} lacks Alpha23/date/route/exact-focus isolation")
                foreign_focuses = (all_focus_flags - {focus_flag}) & set(re.findall(r"ind_aubm_route_focus_[a-z0-9_]+", block))
                if foreign_focuses:
                    errors.append(f"event {event_id} references another selected focus: {sorted(foreign_focuses)}")
                title, desc = quoted_field(block, "name"), quoted_field(block, "desc")
                if not title or title in stage_titles:
                    errors.append(f"event {event_id} has a missing or duplicate stage title")
                if not desc or desc in stage_descs:
                    errors.append(f"event {event_id} has a missing or duplicate stage description")
                stage_titles.add(title)
                stage_descs.add(desc)
            activation, intermediate, dilemma, culmination = blocks
            if active_flag not in activation or culmination_flag not in activation:
                errors.append(f"{route.key}/{focus.key} activation lacks its active/completion lifecycle flags")
            if "NOT = { flag = ind_aubm_route_war_achievement }" not in activation:
                errors.append(f"{route.key}/{focus.key} activation can start a second primary after earned route victory")
            if not all(token in intermediate for token in (active_flag, intermediate_flag, culmination_flag)):
                errors.append(f"{route.key}/{focus.key} intermediate stage lacks ordered lifecycle guards")
            if not all(token in dilemma for token in (active_flag, intermediate_flag, dilemma_flag, culmination_flag)):
                errors.append(f"{route.key}/{focus.key} dilemma lacks ordered lifecycle guards")
            if len(action_blocks(dilemma)) < 3 or dilemma.count(f"setflag which = {dilemma_flag}") < 3:
                errors.append(f"{route.key}/{focus.key} dilemma lacks three resolving strategic choices")
            if route.key != "sovereign" and route.compact_condition not in dilemma:
                errors.append(f"{route.key}/{focus.key} doctrine response dispatch is not gated on the actual compact/formal relationship")
            if route.key == "allied":
                eng_invalid = "OR = { NOT = { exists = ENG } war = { country = IND country = ENG } }"
                usa_invalid = "OR = { NOT = { exists = USA } war = { country = IND country = USA } }"
                no_selection = "AND = { NOT = { flag = ind_aubm_allied_partner_eng } NOT = { flag = ind_aubm_allied_partner_usa } }"
                request = f"ind_aubm_bespoke_partner_request_allied_focus_{focus.key}"
                pending = "ind_aubm_bespoke_partner_response_allied_pending"
                primary = (
                    "flag = ind_aubm_allied_partner_eng exists = ENG "
                    "NOT = { war = { country = IND country = ENG } } "
                    f"flag = {request} flag = {pending}"
                )
                alternate = (
                    "NOT = { flag = ind_aubm_allied_partner_eng } "
                    "flag = ind_aubm_allied_partner_usa exists = USA "
                    "NOT = { war = { country = IND country = USA } } "
                    f"flag = {request} flag = {pending}"
                )
                fallback_primary = (
                    f"OR = {{ {no_selection} "
                    "AND = { NOT = { flag = ind_aubm_allied_partner_eng } "
                    f"flag = ind_aubm_allied_partner_usa {usa_invalid} }} }} "
                    "exists = ENG NOT = { war = { country = IND country = ENG } } "
                    f"flag = {request} flag = {pending}"
                )
                fallback_alternate = (
                    f"OR = {{ AND = {{ {no_selection} {eng_invalid} }} "
                    f"AND = {{ flag = ind_aubm_allied_partner_eng {eng_invalid} }} }} "
                    "exists = USA NOT = { war = { country = IND country = USA } } "
                    f"flag = {request} flag = {pending}"
                )
                expected_dispatches = (
                    f"command = {{ trigger = {{ {primary} }} type = event which = {route.base + 2} where = ENG when = 2 }}",
                    f"command = {{ trigger = {{ {alternate} }} type = event which = {route.base + 21} where = USA when = 2 }}",
                    f"command = {{ trigger = {{ {fallback_primary} }} type = event which = {route.base + 2} where = ENG when = 2 }}",
                    f"command = {{ trigger = {{ {fallback_alternate} }} type = event which = {route.base + 21} where = USA when = 2 }}",
                )
                no_partner = f"{eng_invalid} {usa_invalid} flag = {request} flag = {pending}"
                expected_cleanup = (
                    f"command = {{ trigger = {{ {no_partner} }} type = setflag which = ind_aubm_bespoke_partner_response_allied_absent }}",
                    f"command = {{ trigger = {{ {no_partner} }} type = setflag which = ind_aubm_bespoke_partner_response_allied_done }}",
                    f"command = {{ trigger = {{ {no_partner} }} type = clrflag which = {pending} }}",
                )
                for letter, action in action_blocks(dilemma).items():
                    for expected in (*expected_dispatches, *expected_cleanup):
                        checks += 1
                        if expected not in action:
                            errors.append(f"allied/{focus.key} action {letter} lacks an exclusive fallback/cleanup command")
                    checks += 1
                    dispatch_count = len(re.findall(
                        rf"\btype\s*=\s*event\s+which\s*=\s*(?:{route.base + 2}|{route.base + 21})"
                        rf"\s+where\s*=\s*(?:ENG|USA)\s+when\s*=\s*2",
                        action,
                    ))
                    if dispatch_count != 4:
                        errors.append(f"allied/{focus.key} action {letter} has {dispatch_count} partner branches, expected 4")
            if route.key == "sovereign":
                siam_nonmember = f"NOT = {{ {sovereign_member_condition('SIA')} }}"
                if siam_nonmember not in dilemma or f"where = CHI" not in dilemma:
                    errors.append(f"sovereign/{focus.key} cannot route a response to CHI when peaceful SIA is a non-member")
                if not all(token in dilemma for token in (
                    "setflag which = ind_aubm_bespoke_partner_response_sovereign_absent",
                    "clrflag which = ind_aubm_bespoke_partner_response_sovereign_pending",
                )):
                    errors.append(f"sovereign/{focus.key} partner dispatch can leave an unresolved pending request")
            if not all(token in culmination for token in (
                active_flag, intermediate_flag, dilemma_flag, culmination_flag,
                f"ind_aubm_route_achievement_{route.key}_{focus.key}",
                f"ind_aubm_route_achievement_{route.key}",
                f"ind_aubm_congress_entitlement_{route.key}",
                "ind_aubm_route_war_achievement",
            )):
                errors.append(f"{route.key}/{focus.key} culmination does not authoritatively close ledger and congress entitlement")
            if "\n\t\tatwar = yes\n" in culmination:
                errors.append(f"{route.key}/{focus.key} culmination can softlock after immediate peace")
            if "NOT = { flag = ind_aubm_route_war_achievement }" not in culmination:
                errors.append(f"{route.key}/{focus.key} culmination can pay after another primary victory")
            if focus.culmination_condition not in activation or focus.culmination_condition not in intermediate:
                errors.append(f"{route.key}/{focus.key} stages cannot recover from victory followed by immediate peace")

    # Every charged option must advertise and enforce the complete reserve cost.
    for event_id, event in events.items():
        for letter, action in action_blocks(event).items():
            commands = tuple(re.findall(r"\btype\s*=\s*(money|supplies|oilpool)\s+value\s*=\s*(-\d+)", action))
            flattened = tuple(f"{kind} value = {value}" for kind, value in commands)
            for resource, amount in resource_costs(flattened).items():
                checks += 1
                trigger_name = RESOURCE_TRIGGERS[resource]
                if not re.search(rf"\b{trigger_name}\s*=\s*{amount}\b", action):
                    errors.append(f"event {event_id} action {letter} charges {resource} {amount} without full affordability gate")

    forbidden = sorted(set(command_types(text)) & FORBIDDEN_DIRECT_COMMANDS)
    checks += 3
    if forbidden:
        errors.append(f"module bypasses shared legal/settlement authority with direct commands: {forbidden}")
    if re.search(r"\btype\s*=\s*leave_alliance\b", text):
        errors.append("module directly changes alliance membership")

    # Japan's optional four-theatre follow-on and finite German-country relief callback.
    japan_text = "\n".join(events[event_id] for event_id in range(9289645, 9289653))
    relief = events.get(9289649, "")
    german_callback = events.get(9289650, "")
    grand_end = events.get(9289652, "")
    japan_dualfront = events.get(9289626, "") + events.get(9289630, "") + events.get(9289634, "") + events.get(9289638, "")
    checks += 24
    required_japan_tokens = (
        "alliance = { country = IND country = JAP }",
        "war = { country = IND country = CHI }",
        "ind_aubm_japan_grand_china_posture",
        "ind_aubm_japan_grand_philippines_allocation",
        "ind_aubm_japan_grand_southern_australia",
        "province = 1053",
        "province = 900",
        "ind_aubm_japan_grand_ocean_africa",
        "ind_aubm_japan_grand_northern_posture",
        "province = 713",
        "province = 709",
        "province = 706",
    )
    for token in required_japan_tokens:
        if token not in japan_text:
            errors.append(f"Japanese grand-campaign overlay omits {token}")
    for token in (
        "war = { country = IND country = SOV }",
        "war = { country = GER country = SOV }",
        "exists = GER",
        "control = { province = 163 data = GER }",
        "control = { province = 713 data = IND }",
        "control = { province = 709 data = IND }",
        "control = { province = 706 data = IND }",
        "supplies value = -1200",
        "oilpool value = -500",
        "where = GER",
    ):
        if token not in relief:
            errors.append(f"Delhi-Tokyo-Berlin relief trigger/action omits {token}")
    if "country = GER" not in german_callback or "supplies value = 900" not in german_callback or "oilpool value = 350" not in german_callback:
        errors.append("Caucasus relief is not a limited GER-country stockpile callback")
    if any(token in german_callback for token in ("industrial_modifier", "research_mod", "tc_mod")):
        errors.append("German relief callback applies a passive/global Germany buff")
    if "ind_aubm_route_war_achievement" in grand_end or "ind_aubm_congress_entitlement" in grand_end:
        errors.append("Japanese cumulative grand-campaign endgame steals the primary charter reward")
    if not all(flag in grand_end for flag in ("ind_aubm_japan_grand_china_posture", "ind_aubm_regional_victory_chi", "ind_aubm_regional_victory_chc")):
        errors.append("Japanese grand endgame does not require both China posture and Indian China victory")
    if "Northern Coalition Campaign" not in japan_dualfront or "alliance = { country = IND country = JAP }" not in japan_dualfront:
        errors.append("Japanese northern focus does not support the formal-or-compact Northern Coalition Campaign")
    japan_status = events.get(9289620, "")
    japan_status_a = action_blocks(japan_status).get("a", "")
    if ALPHA23_CONTRACT_FLAG not in japan_status_a or "ind_aubm_jp_partnership" not in japan_status_a or "alliance = { country = IND country = JAP }" not in japan_status_a:
        errors.append("Japanese status board exposes the grand ledger without the Alpha23 relationship gate")
    if "date =" in relief or "offset =" in relief:
        errors.append("Caucasus relief decision is dated as well as manual and can spam/overlap")
    if "ind_aubm_bespoke_partner_request_" in "\n".join(events[route.base + 1] for route in ROUTES):
        errors.append("compact crisis support consumes the one doctrine-response interaction")

    # All internal event links must resolve, while shared targets must exist elsewhere.
    all_loaded_ids = set(counts)
    for source_id, block in events.items():
        for target in map(int, re.findall(r"\btype\s*=\s*event\s+which\s*=\s*(\d+)", block)):
            checks += 1
            if target not in all_loaded_ids:
                errors.append(f"event {source_id} calls missing event {target}")

    if errors:
        print(f"FAILED: {len(errors)} bespoke-route issue(s) across {checks} checks")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"OK: {checks} bespoke-route checks; 20 primary arcs and Japan's cumulative four-theatre follow-on are coherent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
