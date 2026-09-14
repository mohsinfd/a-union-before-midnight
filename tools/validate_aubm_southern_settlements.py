#!/usr/bin/env python3
"""Deterministic checks for Alpha 20 southern local settlements."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_ROOT = ROOT / "mod/db/events/aubm_v4"
THEATRES = EVENT_ROOT / "42_wartime_theatres.txt"
SETTLEMENTS = EVENT_ROOT / "43_wartime_settlements.txt"
REGIONAL = EVENT_ROOT / "46_regional_campaigns.txt"
FILES = (THEATRES, SETTLEMENTS, REGIONAL)
LOCAL_IDS = (9287600, 9287601, 9287602, 9287603, 9287604, 9287606, 9287607, 9287609, 9287611, 9287612, 9287613)
WEST_NEW_GUINEA = tuple(range(1594, 1602))


def strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def blocks(text: str, token: str) -> list[str]:
    clean = strip_comments(text)
    found: list[str] = []
    pattern = rf"(?m)^\s*{re.escape(token)}\s*=\s*\{{"
    for match in re.finditer(pattern, clean):
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
                    found.append(clean[match.start() : position + 1])
                    break
    return found


def parse_events(paths: tuple[Path, ...]) -> dict[int, str]:
    parsed: dict[int, str] = {}
    for path in paths:
        for block in blocks(path.read_text(encoding="cp1252"), "event"):
            match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
            if not match:
                continue
            event_id = int(match.group(1))
            if event_id in parsed:
                raise ValueError(f"duplicate event ID {event_id} in selected modules")
            parsed[event_id] = block
    return parsed


def action(block: str, letter: str) -> str:
    target = f"action_{letter}"
    matches = blocks(block, target)
    return matches[0] if matches else ""


def balanced(text: str) -> bool:
    clean = strip_comments(text)
    depth = 0
    quoted = False
    escaped = False
    for char in clean:
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
            if depth < 0:
                return False
    return not quoted and depth == 0


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def contains_all(block: str, tokens: tuple[str, ...]) -> bool:
    return all(token in block for token in tokens)


def simulate_serial_callbacks() -> tuple[list[str], int]:
    """Model three simultaneous grand acceptances using the scripted mutex/requeue rule."""
    callbacks: dict[int, list[str]] = {0: ["u05", "eng", "hol"]}
    ratifier: dict[int, str] = {}
    target: str | None = None
    completed: list[str] = []
    retries = 0
    for tick in range(20):
        if tick in ratifier:
            assert target == ratifier[tick]
            completed.append(target)
            target = None
        for candidate in callbacks.get(tick, []):
            if target is None:
                target = candidate
                ratifier[tick + 1] = candidate
            else:
                callbacks.setdefault(tick + 2, []).append(candidate)
                retries += 1
        if len(completed) == 3:
            break
    return completed, retries


def main() -> int:
    errors: list[str] = []
    checks = 0

    for path in FILES:
        text = path.read_text(encoding="cp1252")
        checks += 1
        require(errors, balanced(text), f"{path.name} has unbalanced braces or quotes")

    try:
        events = parse_events(FILES)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    all_ids: dict[int, list[Path]] = {}
    for path in (ROOT / "mod/db/events").rglob("*.txt"):
        text = strip_comments(path.read_text(encoding="cp1252"))
        for value in re.findall(r"(?m)^\s*id\s*=\s*(\d+)\s*$", text):
            all_ids.setdefault(int(value), []).append(path)
    for event_id in LOCAL_IDS:
        checks += 2
        require(errors, event_id in events, f"missing local settlement event {event_id}")
        require(errors, len(all_ids.get(event_id, [])) == 1, f"local event ID {event_id} is not unique")

    board = events.get(9287600, "")
    checks += 13
    require(errors, "ind_aubm_national_southern_current" not in board, "local board still requires full Southern victory")
    require(errors, "ind_aubm_route_" not in board, "local board is not route-neutral")
    require(errors, "ind_aubm_regional_pending_u05" in board, "local board omits U05 Batavia file")
    require(errors, "ind_aubm_regional_pending_hol_colonial" in board, "local board omits Dutch Batavia file")
    require(errors, "ind_aubm_regional_pending_eng_malaya" in board, "local board omits standalone Malaya file")
    require(errors, board.count("type = setflag which = ind_aubm_southern_local_lock") == 3, "local board does not lock exactly one selected southern docket")
    require(errors, board.count("NOT = { flag = ind_aubm_common_south_pending }") == 3, "local board can overlap a grand Southern settlement")
    for dispatch in ("u05", "eng", "hol"):
        require(errors, board.count(f"NOT = {{ flag = ind_aubm_south_grand_{dispatch}_dispatch }}") == 3, f"local board can overlap queued grand {dispatch.upper()} response")
    require(errors, "NOT = { flag = ind_aubm_jp_settlement_pending }" in board, "local board can overlap a legacy Japan settlement")
    require(errors, "NOT = { exists = HOL } owned = { province = 122 data = IND }" in board, "local board omits annexed-Netherlands Amsterdam routing")

    migration = events.get(9287613, "")
    migration_action = action(migration, "a")
    checks += 23
    require(errors, "persistent = yes" in migration and "one_action = yes" in migration, "southern refusal migration is not a one-action persistent old-save repair")
    require(errors, "flag = ind_aubm_wartime_framework" in migration, "southern refusal migration can run before the wartime ledger exists")
    require(errors, "NOT = { flag = ind_aubm_southern_refusal_migration_alpha20 }" in migration, "southern refusal migration lacks a one-time guard")
    refusal_migrations = (
        ("ind_aubm_south_u05_reject", "u05", True),
        ("ind_aubm_common_south_britain_reject", "eng_malaya", True),
        ("ind_aubm_hol_colonial_reject", "hol_colonial", True),
        ("ind_aubm_common_south_ast_reject", "ast", False),
    )
    for refusal, suffix, has_regional_refusal in refusal_migrations:
        if has_regional_refusal:
            require(errors, f"trigger = {{ flag = {refusal} }} type = setflag which = ind_aubm_regional_refused_{suffix}" in migration_action, f"Alpha 19 {suffix} refusal is not made terminal during migration")
        for ledger in ("pending", "current", "suspended"):
            require(errors, f"trigger = {{ flag = {refusal} }} type = clrflag which = ind_aubm_regional_{ledger}_{suffix}" in migration_action, f"Alpha 19 {suffix} refusal leaves its {ledger} ledger live")
    for preserved in ("victory_u05", "victory_eng_malaya", "victory_hol_colonial", "victory_ast"):
        require(errors, f"type = clrflag which = ind_aubm_regional_{preserved}" not in migration_action, f"southern refusal migration erases historical {preserved} credit")
    for refusal, _, _ in refusal_migrations:
        require(errors, f"type = clrflag which = {refusal}" not in migration_action, f"southern refusal migration erases retry provenance {refusal}")
    require(errors, "type = peace" not in migration_action and "type = secede" not in migration_action and "type = dissent" not in migration_action, "southern refusal migration grants a settlement or reward")
    require(errors, "type = setflag which = ind_aubm_southern_refusal_migration_alpha20" in migration_action, "southern refusal migration never closes its one-time guard")

    detector = events.get(9282200, "")
    detector_contracts = (
        ("U05 Batavia", ("owned = { province = 1647 data = U05 }", "war = { country = IND country = U05 }", "control = { province = 1647 data = IND }")),
        ("Dutch Batavia", ("ind_aubm_regional_pending_hol_colonial", "owned = { province = 1647 data = HOL }", "war = { country = IND country = HOL }")),
        ("British Malaya", ("ind_aubm_regional_pending_eng_malaya", "owned = { province = 1432 data = ENG }", "owned = { province = 1438 data = ENG }", "control = { province = 1432 data = IND }", "control = { province = 1438 data = IND }")),
    )
    for label, tokens in detector_contracts:
        checks += 1
        require(errors, contains_all(detector, tokens), f"regional detector violates {label} legal-control contract")
    checks += 2
    require(errors, "type = event which = 9287600 where = IND when = 1" in detector, "regional detector does not open the local board in one day")
    require(errors, "NOT = { exists = U05 } owned = { province = 1647 data = IND }" not in detector, "initial regional detector mislabels an annexed Dutch Batavia as a U05 victory")

    dei_recheck = events.get(9287603, "")
    malaya_recheck = events.get(9287604, "")
    checks += 8
    require(errors, "type = event which = 9282000 where = U05 when = 0" in dei_recheck, "U05 response is not dispatched immediately after recheck")
    require(errors, "type = event which = 9287606 where = HOL when = 0" in dei_recheck, "Dutch colonial response is not dispatched immediately after recheck")
    require(errors, "type = event which = 9282050 where = IND when = 0" in dei_recheck, "annexed-U05 Batavia path has no immediate local implementation")
    require(errors, "NOT = {" in action(dei_recheck, "b"), "Batavia recheck has no lapse branch")
    require(errors, "war = { country = IND country = U05 }" in dei_recheck, "U05 recheck omits live pairwise war")
    require(errors, "war = { country = IND country = HOL }" in dei_recheck, "Dutch recheck omits live pairwise war")
    require(errors, "type = event which = 9282005 where = ENG when = 0" in malaya_recheck, "British response is not dispatched immediately after recheck")
    require(errors, "NOT = { AND = {" in action(malaya_recheck, "b"), "Malaya recheck has no peace/control lapse branch")

    u05_response = events.get(9282000, "")
    hol_response = events.get(9287606, "")
    for label, response, country in (("U05", u05_response, "U05"), ("HOL", hol_response, "HOL")):
        checks += 3
        require(errors, f"country = {country}" in response, f"{label} cession is not executed in legal-owner scope")
        require(errors, 'type = secederegion which = IND value = "Indonesia" when = 1' in response, f"{label} response omits Indonesia region")
        for letter in ("a", "b"):
            province_commands = {
                int(value)
                for value in re.findall(r"type\s*=\s*secedeprovince\s+which\s*=\s*IND\s+value\s*=\s*(\d+)", action(response, letter))
            }
            checks += 1
            require(errors, set(WEST_NEW_GUINEA).issubset(province_commands), f"{label} option {letter} omits western New Guinea 1594-1601")

    malaya_response = events.get(9282005, "")
    checks += 5
    require(errors, "country = ENG" in malaya_response, "Malaya cession is not executed in British legal-owner scope")
    require(errors, 'type = secedearea which = IND value = "Malacka" when = 1' in malaya_response, "Malaya response omits the Malacka area")
    for province in (1624, 1625, 1626, 1629):
        require(
            errors,
            f"flag = ind_aubm_south_grand_eng_dispatch }} type = secedeprovince which = IND value = {province}" in malaya_response,
            f"standalone Malaya can incorrectly transfer Borneo province {province}",
        )

    hol_home = events.get(9287607, "")
    checks += 3
    require(errors, "province = 122" in hol_home, "Netherlands home convention does not use Amsterdam")
    require(errors, "province = 1647" not in hol_home, "Netherlands home convention is coupled to Batavia")
    require(errors, "secede" not in hol_home, "Netherlands home convention transfers colonial territory")

    ratifier = events.get(9282059, "")
    checks += 8
    for tag in ("U05", "ENG", "HOL"):
        require(errors, f"type = peace which = {tag} value = 1" in ratifier, f"ratifier lacks pairwise peace for {tag}")
    require(errors, "type = peace which = -1" not in ratifier, "ratifier contains a global peace command")
    require(errors, "ind_aubm_regional_pending_hol_colonial" in ratifier, "ratifier does not clear Dutch colonial pending state")
    require(errors, "ind_aubm_regional_pending_eng_malaya" in ratifier, "ratifier does not clear Malaya pending state")
    require(errors, "ind_aubm_local_dei_outstanding" in ratifier, "ratifier does not clear Batavia outstanding state")
    require(errors, "ind_aubm_local_malaya_outstanding" in ratifier, "ratifier does not clear Malaya outstanding state")

    grand = events.get(9282001, "")
    checks += 4
    require(errors, grand.count("NOT = { flag = ind_aubm_south_dei_secured }") >= 6, "grand Southern docket can redemand a settled East Indies file")
    require(errors, grand.count("NOT = { flag = ind_aubm_south_malaya_secured }") >= 3, "grand Southern docket can redemand settled Malaya")
    require(errors, "owned = { province = 1647 data = HOL }" in grand, "grand Dutch request ignores Batavia legal ownership")
    require(errors, "owned = { province = 1432 data = ENG }" in grand and "owned = { province = 1438 data = ENG }" in grand, "grand British request ignores Malayan legal ownership")

    theatre = events.get(9281940, "") + events.get(9281950, "") + events.get(9281951, "")
    checks += 4
    require(errors, theatre.count("ind_aubm_south_malaya_secured") >= 3, "Southern victory/reversal does not retain secured Malaysia")
    require(errors, theatre.count("control = { province = 1432 data = MLY }") >= 3, "friendly Malaysia does not satisfy the Straits hinge")
    require(errors, theatre.count("ind_aubm_south_dei_secured") >= 3, "Southern victory/reversal does not retain secured Indonesia")
    require(errors, theatre.count("control = { province = 1647 data = INO }") >= 3, "friendly Indonesia does not satisfy the East Indies hinge")

    lapse = events.get(9287611, "")
    checks += 5
    for token in (
        "ind_aubm_regional_pending_u05",
        "ind_aubm_regional_pending_hol_colonial",
        "ind_aubm_regional_pending_eng_malaya",
        "ind_aubm_local_dei_outstanding",
        "ind_aubm_local_malaya_outstanding",
    ):
        require(errors, token in lapse, f"lapse cleanup omits {token}")

    # Concurrency/provenance contract: grand responses may all accept on the
    # same day, but callbacks hold their dispatch evidence and requeue until
    # the single ratifier slot is free. No busy callback is treated as refusal.
    callbacks = {
        "U05": events.get(9282050, ""),
        "ENG": events.get(9282051, ""),
        "HOL": events.get(9282053, ""),
    }
    for tag, callback in callbacks.items():
        event_id = {"U05": 9282050, "ENG": 9282051, "HOL": 9282053}[tag]
        checks += 5
        require(errors, f"type = event which = {event_id} where = IND when = 2" in action(callback, "a"), f"busy {tag} callback is not requeued")
        require(errors, "type = event which = 9282059 where = IND when = 0" in action(callback, "a"), f"{tag} callback does not immediately enter the ratifier")
        require(errors, "type = event which = 9287611" not in action(callback, "a"), f"busy {tag} callback incorrectly lapses")
        require(errors, f"ind_aubm_south_grand_{tag.lower()}_dispatch" in callback, f"{tag} callback lacks explicit grand provenance")
        require(errors, "NOT = { OR = { flag = ind_aubm_local_armistice_target_u05" in action(callback, "a"), f"{tag} callback does not acquire the shared target mutex")

    completed, retries = simulate_serial_callbacks()
    checks += 2
    require(errors, completed == ["u05", "eng", "hol"], "simultaneous grand acceptances do not all reach ratification exactly once")
    require(errors, retries >= 2, "concurrency model did not exercise callback requeueing")

    checks += 9
    require(errors, "ind_aubm_south_grand_u05_dispatch" in u05_response, "U05 response lacks explicit grand dispatch branch")
    require(errors, "ind_aubm_south_legacy_u05_dispatch" in u05_response, "legacy U05 response does not record dedicated provenance")
    require(errors, "type = event which = 9282050 where = IND when = 0" in action(u05_response, "a"), "U05 acceptance leaves a post-cession day gap")
    require(errors, "type = event which = 9282051 where = IND when = 0" in action(malaya_response, "a"), "British acceptance leaves a post-cession day gap")
    require(errors, "type = event which = 9282053 where = IND when = 0" in action(hol_response, "a"), "Dutch colonial acceptance leaves a post-cession day gap")
    require(errors, "ind_aubm_south_legacy_hol_dispatch" in callbacks["HOL"], "legacy Dutch callback lacks explicit provenance")
    require(errors, "ind_aubm_ratify_hol_colonial" in callbacks["HOL"], "Dutch callback does not distinguish colonial ratification")
    require(errors, "ind_aubm_ratify_hol_home" in callbacks["HOL"], "Dutch callback does not distinguish home ratification")
    require(errors, "owned = { province = 1647 data = IND }" in action(callbacks["HOL"], "a"), "Dutch colonial callback does not verify the accepted legal transfer")

    ratify_action = action(ratifier, "a")
    ratify_collision = action(ratifier, "b")
    checks += 12
    for target in ("u05", "eng", "ast", "hol", "sov"):
        require(errors, f"flag = ind_aubm_local_armistice_target_{target}" in ratify_action, f"ratifier exact-one gate omits {target.upper()}")
    require(errors, ratify_action.count("NOT = { OR = {") >= 5, "ratifier does not exclude every second simultaneous target")
    require(errors, "type = event which = 9287611 where = IND when = 1" in ratify_collision, "stale/colliding ratifier has no lapse path")
    require(errors, "ind_aubm_southern_lapse_ast" in ratify_collision and "ind_aubm_southern_lapse_sov" in ratify_collision, "AST/SOV ratifier lapses are not isolated")
    require(errors, "ind_aubm_south_dei_secured" in ratify_action, "successful Batavia ratification does not secure the theatre")
    require(errors, "ind_aubm_south_malaya_secured" in ratify_action, "successful Malaya ratification does not secure the theatre")
    require(errors, "type = independence which = INO" in ratify_action, "successful local Batavia ratification omits Indonesia implementation")
    require(errors, "type = independence which = MLY" in ratify_action, "successful local Malaya ratification omits Malaysia implementation")
    u05_reject_clears = [command for command in blocks(ratify_action, "command") if "type = clrflag which = ind_aubm_south_u05_reject" in command]
    require(errors, len(u05_reject_clears) == 1 and "flag = ind_aubm_local_armistice_target_u05" in u05_reject_clears[0] and "ind_aubm_local_armistice_target_hol" not in u05_reject_clears[0], "Dutch ratification can erase a separate U05 refusal/retry docket")

    refusal = events.get(9287609, "")
    refusal_action = action(refusal, "a")
    checks += 10
    for suffix in ("u05", "hol_colonial", "eng_malaya", "hol"):
        require(errors, f"type = setflag which = ind_aubm_regional_refused_{suffix}" in refusal_action, f"refusal is not terminal for {suffix}")
    require(errors, "type = clrflag which = ind_aubm_southern_local_lock" in refusal_action, "refusal leaves the global local lock stuck")
    require(errors, "clrflag which = ind_aubm_regional_victory_" not in refusal_action, "refusal erases historical victory and re-enables rewards")
    require(errors, refusal_action.count("type = dissent value = 1") == 1, "refusal can charge dissent more than once per notice")
    require(errors, bool(action(refusal, "b")), "duplicate refusal notice has no no-op branch")
    require(errors, all(f"ind_aubm_regional_refused_{suffix}" in detector for suffix in ("u05", "hol_colonial", "eng_malaya", "hol")), "regional detector ignores terminal refusal flags")
    require(errors, "type = clrflag which = ind_aubm_regional_pending_u05" in refusal_action and "type = clrflag which = ind_aubm_regional_pending_eng_malaya" in refusal_action, "refusal leaves a daily-reroll pending file")

    lapse_action = action(lapse, "a")
    checks += 12
    require(errors, "clrflag which = ind_aubm_regional_victory_" not in lapse_action, "lapse erases historical victory and permits reward farming")
    require(errors, "type = clrflag which = ind_aubm_southern_local_lock" in lapse_action, "lapse leaves the global local lock stuck")
    require(errors, not re.search(r"(?m)^\s*command\s*=\s*\{\s*type\s*=\s*clrflag\s+which\s*=\s*ind_aubm_local_(?:dei|malaya|hol)", lapse_action), "lapse unconditionally clears unrelated local dockets")
    for helper in ("u05", "eng", "ast", "hol", "sov", "noop"):
        require(errors, f"type = clrflag which = ind_aubm_southern_lapse_{helper}" in lapse_action, f"lapse helper {helper} is sticky")
    require(errors, "flag = ind_aubm_southern_lapse_ast } type = clrflag which = ind_aubm_local_armistice_target_ast" in lapse_action, "AST lapse can clear a target without AST provenance")
    require(errors, "flag = ind_aubm_southern_lapse_sov } type = clrflag which = ind_aubm_local_armistice_target_sov" in lapse_action, "SOV lapse can clear a target without SOV provenance")
    require(errors, bool(action(lapse, "b")), "duplicate lapse notice has no no-op branch")

    checks += 8
    require(errors, "ind_aubm_callback_annexed_u05" in callbacks["U05"], "annexed U05 Batavia path is not explicitly sourced")
    require(errors, "NOT = { exists = U05 } owned = { province = 1647 data = IND }" in callbacks["U05"], "annexed U05 callback lacks Indian legal ownership")
    require(errors, "type = setflag which = ind_aubm_regional_settled_u05" in callbacks["U05"], "annexed U05 path does not settle")
    require(errors, "type = clrflag which = ind_aubm_southern_local_lock" in callbacks["U05"], "annexed U05 path leaves the local lock stuck")
    require(errors, "ind_aubm_callback_annexed_hol_home" in callbacks["HOL"], "annexed Netherlands home path is not explicitly sourced")
    require(errors, "type = event which = 9282053 where = IND when = 0" in board, "annexed Netherlands home path is not IND-scoped")
    require(errors, "type = setflag which = ind_aubm_regional_settled_hol" in callbacks["HOL"], "annexed Netherlands home path does not settle")
    require(errors, "type = clrflag which = ind_aubm_southern_local_lock" in callbacks["HOL"], "annexed Netherlands home path leaves the local lock stuck")

    recovery = events.get(9282266, "")
    checks += 8
    for suffix in ("u05", "hol_colonial", "eng_malaya", "hol"):
        require(errors, f"type = setflag which = ind_aubm_regional_pending_{suffix}" in recovery, f"recapture does not reopen suspended {suffix} without a new reward")
        require(errors, f"ind_aubm_regional_refused_{suffix}" in recovery, f"recovery ignores terminal refusal for {suffix}")

    retry = events.get(9282054, "")
    checks += 4
    require(errors, "type = setflag which = ind_aubm_south_grand_u05_dispatch" in retry, "U05 grand retry lacks dispatch provenance")
    require(errors, "type = setflag which = ind_aubm_south_grand_eng_dispatch" in retry, "British grand retry lacks dispatch provenance")
    require(errors, "flag = ind_aubm_south_grand_u05_dispatch } type = event which = 9282000" in retry, "U05 retry can dispatch without provenance")
    require(errors, "flag = ind_aubm_south_grand_eng_dispatch } type = event which = 9282005" in retry, "British retry can dispatch without provenance")

    # Adversarial lifecycle checks added after concurrency review. A queued
    # target or queued lapse must serialize the board, and no target helper
    # may erase an unrelated local file.
    checks += 4
    require(errors, board.count("flag = ind_aubm_local_armistice_target_ast") >= 3, "local board can open over an AST ratifier")
    require(errors, board.count("flag = ind_aubm_local_armistice_target_sov") >= 3, "local board can open over a Soviet ratifier")
    require(errors, board.count("flag = ind_aubm_southern_lapse_noop") >= 3, "local board can open while a stale lapse is queued")
    require(errors, "flag = ind_aubm_southern_lapse_ast flag = ind_aubm_local_" not in lapse_action and "flag = ind_aubm_southern_lapse_sov flag = ind_aubm_local_" not in lapse_action, "AST/SOV lapse can erase an unrelated southern local docket")

    local_cleanup_contracts = {
        "ind_aubm_local_dei_target_u05": "ind_aubm_southern_lapse_u05",
        "ind_aubm_local_dei_target_hol_colonial": "ind_aubm_southern_lapse_hol",
        "ind_aubm_local_malaya_outstanding": "ind_aubm_southern_lapse_eng",
        "ind_aubm_local_hol_home_outstanding": "ind_aubm_southern_lapse_hol",
    }
    lapse_commands = blocks(lapse_action, "command")
    for marker, helper in local_cleanup_contracts.items():
        relevant = [command for command in lapse_commands if "type = clrflag" in command and marker in command]
        checks += 2
        require(errors, bool(relevant), f"lapse has no cleanup for {marker}")
        require(errors, all(helper in command for command in relevant), f"lapse cleanup for {marker} is not target-scoped")
    checks += 1
    require(errors, all("ind_aubm_local_" not in command for command in lapse_commands if "ind_aubm_southern_lapse_noop" in command), "generic no-op lapse clears a local docket")

    for suffix in ("u05", "hol_colonial", "eng_malaya", "hol", "ast"):
        suspend_commands = [command for command in lapse_commands if re.search(rf"type\s*=\s*setflag\s+which\s*=\s*ind_aubm_regional_suspended_{suffix}\s*\}}", command)]
        checks += 2
        require(errors, len(suspend_commands) == 1, f"target lapse does not preserve suspended state for {suffix}")
        require(errors, not any(token in suspend_commands[0] for token in ("exists =", "war =", "owned =", "control =")), f"{suffix} lapse suspension wrongly depends on the state that caused the lapse")

    # Accepted cessions are binding evidence: the callbacks retain dispatch
    # while busy, accept exact Indian legal ownership after target death, and
    # finalize without a second peace/reward if an external peace intervenes.
    cession_contracts = {
        "U05": (callbacks["U05"], "u05", "1647"),
        "ENG": (callbacks["ENG"], "eng", "1432"),
        "HOL": (callbacks["HOL"], "hol", "1647"),
    }
    for tag, (callback, suffix, province) in cession_contracts.items():
        callback_action = action(callback, "a")
        checks += 5
        require(errors, f"ind_aubm_callback_final_{suffix}" in callback_action if tag != "HOL" else "ind_aubm_callback_final_hol_colonial" in callback_action, f"{tag} callback lacks no-war finalization")
        require(errors, f"flag = ind_aubm_south_grand_{suffix}_dispatch owned = {{ province = {province} data = IND }}" in callback_action, f"{tag} accepted cession cannot finalize if the target ceases")
        final_name = f"ind_aubm_callback_final_{suffix}" if tag != "HOL" else "ind_aubm_callback_final_hol_colonial"
        require(errors, f"trigger = {{ flag = {final_name} }} type = clrflag which = ind_aubm_south_grand_{suffix}_dispatch" in callback_action, f"{tag} busy callback clears its dispatch provenance")
        require(errors, "NOT = { war = { country = IND country =" in callback_action, f"{tag} callback lacks external-peace completion")
        require(errors, f"ind_aubm_ratifier_resume_{suffix}" in ratify_collision, f"{tag} ratifier cannot return a no-war accepted cession to its callback")
    checks += 3
    require(errors, "ind_aubm_ratifier_resume_ast" not in ratify_collision, "unceded AST file can settle after external peace")
    require(errors, "ind_aubm_ratifier_resume_sov" not in ratify_collision, "unceded Soviet file can settle after external peace")
    require(errors, "flag = ind_aubm_ratify_hol_home" not in " ".join(command for command in blocks(ratify_collision, "command") if "ind_aubm_ratifier_resume_hol" in command), "unceded Netherlands-home file can settle after external peace")

    ratify_trigger = blocks(ratify_action, "trigger")[0]
    checks += 4
    require(errors, "war = { country = IND country = U05 } owned = { province = 1647 data = IND } control" not in ratify_trigger, "U05 ratifier rechecks control after accepted cession")
    require(errors, "owned = { province = 1438 data = IND } control" not in ratify_trigger, "British ratifier rechecks control after accepted cession")
    require(errors, "flag = ind_aubm_ratify_hol_colonial owned = { province = 1647 data = IND } control" not in ratify_trigger, "Dutch colonial ratifier rechecks control after accepted cession")
    require(errors, "flag = ind_aubm_ratify_hol_home owned = { province = 122 data = HOL } control = { province = 122 data = IND }" in ratify_trigger, "Netherlands-home ratifier lost its live-control safeguard")

    ast_response = events.get(9282006, "")
    ast_callback = events.get(9282052, "")
    checks += 14
    for letter in ("a", "b", "c"):
        ast_option = action(ast_response, letter)
        require(errors, contains_all(ast_option, ("ind_aubm_south_grand_ast_dispatch", "exists = AST", "war = { country = IND country = AST }", "owned = { province = 1707 data = AST }", "control = { province = 1707 data = IND }")), f"AST response {letter} lacks standalone live provenance")
        require(errors, "ind_aubm_common_south_pending" not in ast_option, f"AST response {letter} still depends on the national Southern conference")
    require(errors, bool(action(ast_response, "d")), "AST response has no stale action")
    require(errors, contains_all(action(ast_response, "d"), ("ind_aubm_southern_lapse_ast", "type = clrflag which = ind_aubm_south_grand_ast_dispatch", "type = event which = 9287611 where = IND when = 1")), "stale standalone AST response does not run target-specific lapse cleanup")
    require(errors, action(ast_response, "a").count("type = event which = 9282052 where = IND when = 0") == 1, "AST acceptance is not immediately transactional")
    require(errors, "type = setflag which = ind_aubm_south_grand_ast_dispatch" in retry and "type = setflag which = ind_aubm_common_south_pending" in retry, "AST retry does not restore response provenance")
    require(errors, "ind_aubm_southern_lapse_ast" in action(ast_callback, "b"), "stale AST callback uses a generic lapse helper")
    require(errors, contains_all(ratify_trigger, ("ind_aubm_south_grand_ast_dispatch", "owned = { province = 1707 data = AST }", "control = { province = 1707 data = IND }")), "AST ratifier lacks live provenance")
    require(errors, "type = clrflag which = ind_aubm_south_grand_ast_dispatch" in ratify_action, "successful AST ratification leaves dispatch provenance set")

    lock_clears = [command for command in blocks(ratify_action, "command") if "which = ind_aubm_southern_local_lock" in command]
    checks += 3
    require(errors, len(lock_clears) == 1, "ratifier has ambiguous southern-lock cleanup")
    require(errors, contains_all(lock_clears[0], ("ind_aubm_local_armistice_target_u05", "ind_aubm_local_dei_target_u05", "ind_aubm_local_armistice_target_eng", "ind_aubm_local_malaya_outstanding", "ind_aubm_local_armistice_target_hol")), "ratifier lock cleanup is not tied to matching local provenance")
    require(errors, "ind_aubm_local_armistice_target_ast" not in lock_clears[0] and "ind_aubm_local_armistice_target_sov" not in lock_clears[0], "AST/SOV ratification can clear an unrelated southern-local lock")

    resistance = events.get(9282008, "")
    checks += 7
    for label, response, suffix in (
        ("U05", u05_response, "u05"),
        ("ENG", malaya_response, "eng_malaya"),
        ("HOL", hol_response, "hol_colonial"),
    ):
        rejection = action(response, "c")
        require(errors, f"type = setflag which = ind_aubm_regional_refused_{suffix}" in rejection and f"type = clrflag which = ind_aubm_regional_pending_{suffix}" in rejection, f"grand {label} rejection permits an immediate local reroll")
    require(errors, "ind_aubm_hol_colonial_reject" in resistance, "Dutch colonial rejection is absent from Southern resistance policy")
    require(errors, "type = setflag which = ind_aubm_south_grand_hol_dispatch" in retry, "Dutch colonial retry lacks dispatch provenance")
    require(errors, "flag = ind_aubm_south_grand_hol_dispatch } type = event which = 9287606 where = HOL when = 0" in retry, "Dutch colonial retry can dispatch without provenance or with a disappearance gap")
    require(errors, "type = war which = HOL" in action(resistance, "a"), "Southern enforcement omits a rejecting Netherlands")

    checks += 10
    for suffix, response_id, tag in (("eng_malaya", 9282005, "ENG"), ("u05", 9282000, "U05"), ("hol_colonial", 9287606, "HOL")):
        dispatch_suffix = {"eng_malaya": "eng", "u05": "u05", "hol_colonial": "hol"}[suffix]
        require(errors, grand.count(f"NOT = {{ flag = ind_aubm_regional_refused_{suffix} }}") >= 3, f"terminal {suffix} local refusal can be rerolled through the grand docket")
        require(errors, grand.count(f"flag = ind_aubm_south_grand_{dispatch_suffix}_dispatch }} type = event which = {response_id} where = {tag} when = 0") >= 3, f"grand {tag} response can dispatch without refusal-checked provenance")
    detector_commands = blocks(action(detector, "a"), "command")
    for suffix in ("pending_u05", "victory_u05", "current_u05"):
        u05_creation = [command for command in detector_commands if f"type = setflag which = ind_aubm_regional_{suffix}" in command]
        require(errors, len(u05_creation) == 1 and contains_all(u05_creation[0], ("exists = U05", "owned = { province = 1647 data = U05 }", "war = { country = IND country = U05 }", "control = { province = 1647 data = IND }")) and "NOT = { exists = U05 }" not in u05_creation[0], f"9282200 {suffix} retains false annexed-U05 credit")
    require(errors, "ind_aubm_callback_annexed_hol_home" in callbacks["HOL"] and "type = dissent" not in callbacks["HOL"], "explicit annexed Netherlands-home completion is missing or grants a second reward")

    stale_cleanup = events.get(9287612, "")
    regional_board = events.get(9282205, "")
    regional_south = action(regional_board, "c")
    checks += 20
    require(errors, "NOT = { exists = AST } owned = { province = 1707 data = IND }" not in detector, "initial regional detector creates an annexed-AST victory with no live opponent")
    for suffix in ("pending_ast", "victory_ast", "current_ast"):
        ast_creation = [command for command in detector_commands if f"type = setflag which = ind_aubm_regional_{suffix}" in command]
        require(errors, len(ast_creation) == 1 and contains_all(ast_creation[0], ("exists = AST", "owned = { province = 1707 data = AST }", "war = { country = IND country = AST }", "control = { province = 1707 data = IND }")) and "NOT = { exists = AST }" not in ast_creation[0], f"9282200 {suffix} retains false annexed-AST credit")
    require(errors, "type = setflag which = ind_aubm_regional_suspended_ast" in stale_cleanup, "external peace or AST disappearance does not suspend its historical victory")
    require(errors, "type = clrflag which = ind_aubm_regional_pending_ast" in stale_cleanup and "type = clrflag which = ind_aubm_regional_current_ast" in stale_cleanup, "external AST cleanup leaves a stranded regional ledger")
    require(errors, "type = setflag which = ind_aubm_regional_pending_ast" in recovery, "renewed live AST leverage does not reopen its settlement board")
    ast_recovery_current = [command for command in blocks(action(recovery, "a"), "command") if "type = setflag which = ind_aubm_regional_current_ast" in command]
    require(errors, len(ast_recovery_current) == 1 and contains_all(ast_recovery_current[0], ("exists = AST", "owned = { province = 1707 data = AST }", "war = { country = IND country = AST }", "control = { province = 1707 data = IND }")) and "NOT = { exists = AST }" not in ast_recovery_current[0], "AST recovery resurrects an annexed or non-belligerent ledger")
    require(errors, "flag = ind_aubm_regional_pending_ast } type = event which = 9282001" not in regional_south, "regional board still routes standalone AST leverage through the national Southern conference")
    require(errors, contains_all(regional_south, ("flag = ind_aubm_regional_pending_ast", "flag = ind_aubm_regional_current_ast", "NOT = { flag = ind_aubm_common_south_ast_reject }", "exists = AST", "war = { country = IND country = AST }", "owned = { province = 1707 data = AST }", "control = { province = 1707 data = IND }", "type = setflag which = ind_aubm_south_grand_ast_dispatch")), "regional board lacks a live, refusal-safe standalone AST dispatch")
    require(errors, "flag = ind_aubm_south_grand_ast_dispatch } type = event which = 9282006 where = AST when = 0" in regional_south, "regional board does not dispatch the standalone AST response transactionally")
    require(errors, "ind_aubm_common_south_complete" not in regional_south and "ind_aubm_common_south_pending" not in regional_south, "standalone AST settlement is blocked by national Southern conference state")
    require(errors, grand.count("NOT = { flag = ind_aubm_common_south_ast_reject }") == 3, "ordinary national Southern policies can bypass a standalone AST refusal")
    require(errors, recovery.count("NOT = { flag = ind_aubm_common_south_ast_reject }") >= 4, "ordinary AST recovery can bypass the paid-retry boundary")
    direct_south = action(grand, "d")
    require(errors, "type = setflag which = ind_aubm_south_grand_ast_dispatch" in direct_south, "direct Southern policy strands a live AST file")
    require(errors, "flag = ind_aubm_south_grand_ast_dispatch } type = event which = 9282006 where = AST when = 0" in direct_south, "direct Southern policy does not transactionally dispatch the AST response")
    require(errors, grand.count("type = setflag which = ind_aubm_south_grand_ast_dispatch") == 3, "not every Southern constitutional policy handles a live AST file")
    require(errors, "type = clrflag which = ind_aubm_regional_pending_ast" in action(ast_response, "c") and "type = clrflag which = ind_aubm_regional_current_ast" in action(ast_response, "c"), "AST rejection leaves a permanently routed regional docket behind common_south_complete")

    checks += 8
    require(errors, bool(stale_cleanup), "missing external-peace southern cleanup monitor")
    require(errors, "type = dissent" not in stale_cleanup and "type = money" not in stale_cleanup, "external-peace cleanup grants or charges a repeatable reward")
    require(errors, "NOT = { flag = ind_aubm_southern_local_lock }" in stale_cleanup, "external-peace cleanup can cancel an outstanding local response")
    require(errors, "ind_aubm_south_grand_u05_dispatch" in stale_cleanup and "ind_aubm_local_armistice_target_u05" in stale_cleanup, "external-peace cleanup ignores in-flight provenance")
    for suffix in ("u05", "hol_colonial", "eng_malaya", "hol"):
        require(errors, f"type = setflag which = ind_aubm_regional_suspended_{suffix}" in stale_cleanup and f"type = clrflag which = ind_aubm_regional_pending_{suffix}" in stale_cleanup, f"external-peace cleanup cannot reopen {suffix} on a later recapture")

    checks += 5
    delayed_foreign = re.findall(r"type\s*=\s*event\s+which\s*=\s*(?:9282000|9282005|9282006|9287606|9287607)\s+where\s*=\s*(?:U05|ENG|AST|HOL)\s+when\s*=\s*1", events.get(9282001, "") + retry + board + dei_recheck + malaya_recheck)
    require(errors, not delayed_foreign, "a queued foreign response can disappear while holding settlement provenance")
    require(errors, "type = event which = 9287607 where = HOL when = 0" in board, "Netherlands-home response can vanish while holding the local lock")
    require(errors, "ind_aubm_regional_suspended_u05 control = { province = 1647 data = IND } OR = { AND = { exists = U05" in recovery and "NOT = { exists = U05 } owned = { province = 1647 data = IND }" in recovery, "annexed U05 recovery is missing")
    require(errors, "ind_aubm_regional_suspended_hol control = { province = 122 data = IND } OR = { AND = { exists = HOL" in recovery and "NOT = { exists = HOL } owned = { province = 122 data = IND }" in recovery, "annexed Netherlands-home recovery is missing")
    require(errors, "type = dissent" not in action(recovery, "a") and "type = money" not in action(recovery, "a"), "regional recovery grants an extra repeatable reward")

    if errors:
        print(f"AUBM southern-settlement validation failed ({len(errors)} errors, {checks} checks):")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print(f"AUBM southern-settlement validation passed ({checks} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
