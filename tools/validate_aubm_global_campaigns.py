#!/usr/bin/env python3
"""Acceptance checks for AUBM's generated every-country campaign matrix."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
MODULE = ROOT / "mod/db/events/aubm_v4/47_global_campaign_matrix.txt"
INDEX = ROOT / "mod/db/events.txt"
CABINET = ROOT / "mod/db/events/aubm_v4/32_national_consolidation.txt"

sys.path.insert(0, str(TOOLS))
from generate_aubm_global_campaigns import (  # noqa: E402
    ARMISTICE_LAPSE_ID,
    COUNTRIES,
    EXTENSION_COUNTRIES,
    MENU_FIRST_ID,
    WORLD_INDEX_ID,
    lifecycle_ids,
    render,
)


REQUIRED_EMERGENT_TAGS = {
    "SPA", "DDR", "DFR", "RSI", "CRO", "SER", "MTN", "SLO", "BOS", "SLV", "SCO", "FLA", "WLL",
    "UKR", "BLR", "ARM", "AZB", "GEO", "KAZ", "UZB", "TAJ", "KYG", "TRK", "MEN", "U74", "U87",
    "KOR", "PRK", "PHI", "MLY", "BUR", "LAO", "CMB", "VIE", "ISR", "JOR", "LEB", "SYR", "PAK",
    "GUY", "LBY",
}

BASELINE_1933_TARGETS = {
    "ETH", "AFG", "ALB", "ARG", "AST", "AUS", "BEL", "BHU", "BOL", "BRA", "BUL", "CAN",
    "UPE", "CGX", "CHC", "CHI", "CHL", "COL", "COS", "CSX", "CUB", "CXB", "CYN", "CZE",
    "DEN", "DOM", "ECU", "EGY", "ENG", "EST", "FIN", "FRA", "GER", "GRE", "GUA", "HAI",
    "HOL", "HON", "HUN", "IRE", "IRQ", "ITA", "JAP", "LAT", "LIB", "LIT", "LUX", "MAN",
    "MEX", "MON", "U05", "NEP", "U60", "NIC", "NOR", "NZL", "OMN", "PAN", "PAR", "PER",
    "POL", "POR", "PRU", "ROM", "SAF", "SAL", "SAU", "SCH", "SIA", "SIK", "SOV", "SPR",
    "SWE", "TAN", "TIB", "TUR", "U03", "U04", "U06", "URU", "USA", "VEN", "YEM", "YUG",
}

BESPOKE_CAMPAIGN_TAGS = {
    "ENG", "GER", "SOV", "JAP", "USA", "PER", "IRQ", "SAU", "AFG", "TIB", "SIK", "CHI",
    "CHC", "SIA", "ITA", "FRA", "TUR", "U05", "HOL", "AST", "POR", "NZL", "OMN", "YEM",
    "ETH", "SAF",
}

LOADED_EVENT_SUCCESSORS = {
    "CAL", "CSA", "INO", "PRI", "SOM", "TEX", "U01", "U12", "U13", "U16", "U20", "U21",
    "U22", "U23", "U27", "U29", "U30", "U31", "U32", "U34", "U39", "U40", "U41", "U42",
    "U43", "U70", "U73", "U79", "U90", "U97",
}


def strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


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
            raise ValueError(f"duplicate generated event ID {event_id}")
        events[event_id] = block
    return events


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def country_of(block: str) -> str:
    match = re.search(r"(?m)^\s*country\s*=\s*([A-Z0-9]{3})", block)
    return match.group(1) if match else ""


def main() -> int:
    errors: list[str] = []
    checks = 0

    require(errors, MODULE.exists(), "generated global campaign module is missing")
    if errors:
        print(f"ERROR: {errors[0]}")
        return 1

    text = MODULE.read_text(encoding="ascii")
    checks += 1
    require(errors, text == render(), "global campaign module is stale; rerun its generator")

    try:
        events = parse_events(text)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    index_text = INDEX.read_text(encoding="cp1252").replace("\\", "/")
    checks += 1
    require(
        errors,
        index_text.count('event = "db/events/aubm_v4/47_global_campaign_matrix.txt"') == 1,
        "global campaign module must be loaded exactly once",
    )

    cabinet_text = CABINET.read_text(encoding="cp1252")
    checks += 3
    require(errors, "id = 9281012" in cabinet_text, "permanent War Cabinet has no global-target submenu")
    require(errors, f"which = {WORLD_INDEX_ID} where = IND" in cabinet_text, "global country index is buried outside the permanent War Cabinet")
    require(errors, "which = 9281012 where = IND" in cabinet_text, "War Cabinet root does not expose the global-target submenu")

    expected_pages = sum((sum(c.group == group for c in COUNTRIES) + 2) // 3 for group in ("Europe", "Asia", "Americas", "Africa"))
    expected_events = 1 + expected_pages + 1 + 15 * len(COUNTRIES)
    checks += 5
    require(errors, len(events) == expected_events, f"generated event count is {len(events)}, expected {expected_events}")
    require(errors, len(COUNTRIES) == 210, f"fallback matrix has {len(COUNTRIES)} countries instead of the audited 210")
    require(errors, len(EXTENSION_COUNTRIES) == 111, f"successor catalog has {len(EXTENSION_COUNTRIES)} countries instead of 111")
    require(errors, LOADED_EVENT_SUCCESSORS <= {country.tag for country in COUNTRIES}, "a country created by loaded events is missing from the campaign matrix")
    require(errors, MENU_FIRST_ID + expected_pages - 1 < 9286000, "campaign menu pages exceed their reserved event-ID band")

    for event_id, block in events.items():
        checks += 3
        require(errors, "persistent = yes" in block, f"event {event_id} is consumable instead of persistent")
        require(errors, "type = trigger" not in block, f"event {event_id} uses an unsafe immediate trigger command")
        require(errors, block.count("command =") <= 253, f"event {event_id} exceeds the 253-command stock-scale ceiling")
        if country_of(block) != "IND":
            checks += 2
            require(errors, "type = peace" not in block, f"foreign event {event_id} executes peace in the wrong scope")
            require(errors, "type = setflag" not in block, f"foreign event {event_id} leaks country-scoped campaign flags")

    lapse = events.get(ARMISTICE_LAPSE_ID, "")
    checks += 11
    require(errors, country_of(lapse) == "IND", "vanished-government router is not executed by India")
    require(errors, 9282355 not in events, "obsolete duplicate partner-rupture event is still generated")
    require(errors, "9282355" not in text, "pairwise peace can still force the obsolete partner-rupture callback")
    require(errors, all(event_id not in events for event_id in range(9283300, 9283306)), "one or more retired monolithic helper events are still generated")
    require(errors, all(str(event_id) not in text for event_id in range(9283300, 9283306)), "generated callbacks still reference a retired monolithic helper")
    require(errors, "persistent = yes" in lapse, "vanished-government armistice recovery is not persistent")
    require(errors, "ind_aubm_universal_armistice_outstanding" in lapse, "vanished-government recovery does not release the universal response lock")
    require(errors, "year = 1933" in lapse and "year = 1964" in lapse, "vanished-government recovery does not cover the complete scenario")
    require(errors, "type = clrflag which = ind_aubm_global_rewarded_" not in lapse, "vanished-government recovery erases earned campaign credit")
    require(errors, "type = clrflag which = ind_aubm_global_campaign_victory" not in lapse, "vanished-government recovery erases route congress credit")
    require(errors, lapse.count("command =") == len(COUNTRIES), "vanished-government router does not contain exactly one country callback per target")
    require(errors, lapse.count("NOT = { exists =") == 2 * len(COUNTRIES), "vanished-government router does not guard every target and callback")

    world_index = events.get(WORLD_INDEX_ID, "")
    for index, country in enumerate(COUNTRIES):
        key = country.key
        ids = lifecycle_ids(index)
        event_ids = tuple(vars(ids).values())
        for event_id in event_ids:
            checks += 1
            require(errors, event_id in events, f"{country.tag} lifecycle event {event_id} is missing")

        start = events.get(ids.brief, "")
        victory = events.get(ids.victory, "")
        reversal = events.get(ids.reversal, "")
        recovery = events.get(ids.recovery, "")
        normal_response = events.get(ids.normal_response, "")
        docket = events.get(ids.docket, "")
        backed_response = events.get(ids.backed_response, "")
        settlement = events.get(ids.settlement, "")
        annex_monitor = events.get(ids.annex_monitor, "")
        retry_release = events.get(ids.retry_release, "")
        declaration = events.get(ids.declaration, "")
        accept = events.get(ids.accept, "")
        counter = events.get(ids.counter, "")
        refuse = events.get(ids.refuse, "")
        country_lapse = events.get(ids.lapse, "")
        target_flag = f"ind_aubm_armistice_target_{key}"
        retry_flag = f"ind_aubm_armistice_retry_{key}"

        checks += 69
        safe_departure = (
            f"trigger = {{ alliance = {{ country = IND country = {country.tag} }} }} "
            "type = leave_alliance when = 1"
        )
        require(errors, safe_departure in text, f"war with allied {country.tag} cannot invoke safe coalition withdrawal")
        require(errors, f"which = {ids.declaration} where = IND when = 1" in text, f"{country.tag} menu does not schedule its declaration callback")
        require(errors, f"flag = {target_flag} NOT = {{ exists = {country.tag} }}" in lapse, f"a vanished {country.tag} response cannot release its target lock")
        require(errors, f"type = event which = {ids.lapse} where = IND when = 1" in lapse, f"vanished {country.tag} response is not routed to its country audit")
        require(errors, country_of(declaration) == "IND", f"{country.tag} declaration callback is not Indian-scoped")
        require(errors, f"exists = {country.tag}" in declaration, f"{country.tag} declaration can target a vanished government")
        require(errors, re.search(rf"type\s*=\s*war\s+which\s*=\s*{country.tag}\b", declaration) is not None, f"India cannot declare war on {country.tag}")
        require(errors, declaration.count("type = war") == 1, f"{country.tag} declaration can open more than one war")
        require(errors, "ind_aubm_global_declare_" not in declaration, f"{country.tag} declaration still depends on a global selector flag")
        require(errors, f"war = {{ country = IND country = {country.tag} }}" in start, f"{country.tag} brief is not activated by live war")
        require(errors, f"province = {country.capital} data = {country.tag}" in victory, f"{country.tag} victory omits legal ownership of capital {country.capital}")
        require(errors, f"province = {country.capital} data = IND" in victory, f"{country.tag} victory omits Indian capital control")
        require(errors, f"NOT = {{ exists = {country.tag} }}" in victory, f"{country.tag} victory has no annexation fallback")
        require(errors, f"flag = ind_aubm_global_active_{key} NOT = {{ exists = {country.tag} }}" in victory, f"{country.tag} annexation fallback can reward an unrelated inheritance")
        require(errors, f"ind_aubm_global_current_{key}" in reversal, f"{country.tag} has no live-claim reversal")
        require(errors, f"ind_aubm_global_suspended_{key}" in recovery, f"{country.tag} has no recovery state")
        require(errors, country_of(normal_response) == country.tag, f"normal response for {country.tag} has the wrong country scope")
        require(errors, country_of(backed_response) == country.tag, f"supported response for {country.tag} has the wrong country scope")
        require(errors, tuple(map(int, re.findall(r"\bai_chance\s*=\s*(\d+)", normal_response))) == (60, 25, 15), f"{country.tag} base armistice odds are malformed")
        require(errors, tuple(map(int, re.findall(r"\bai_chance\s*=\s*(\d+)", backed_response))) == (75, 20, 5), f"{country.tag} supported armistice odds are malformed")
        require(errors, normal_response.count(f"control = {{ province = {country.capital} data = IND }}") >= 2, f"{country.tag} base acceptance survives loss of the published objective")
        require(errors, backed_response.count(f"control = {{ province = {country.capital} data = IND }}") >= 2, f"{country.tag} supported acceptance survives loss of the published objective")
        for response_name, response in (("base", normal_response), ("supported", backed_response)):
            require(errors, f"which = {ids.accept} where = IND when = 3" in response, f"{country.tag} {response_name} acceptance omits its Indian callback")
            require(errors, f"which = {ids.counter} where = IND when = 3" in response, f"{country.tag} {response_name} counteroffer omits its Indian callback")
            require(errors, f"which = {ids.refuse} where = IND when = 3" in response, f"{country.tag} {response_name} refusal omits its Indian callback")
        require(errors, target_flag in docket, f"{country.tag} docket does not identify its own peace target")
        require(errors, f"which = {ids.normal_response} where = {country.tag}" in docket, f"{country.tag} docket omits normal response")
        require(errors, f"which = {ids.backed_response} where = {country.tag}" in docket, f"{country.tag} docket omits supported response")
        require(errors, country_of(accept) == "IND", f"{country.tag} acceptance callback is not Indian-scoped")
        require(errors, country_of(counter) == "IND", f"{country.tag} counteroffer callback is not Indian-scoped")
        require(errors, country_of(refuse) == "IND", f"{country.tag} refusal callback is not Indian-scoped")
        require(errors, country_of(country_lapse) == "IND", f"{country.tag} vanished-government callback is not Indian-scoped")
        require(errors, f"type = peace which = {country.tag} value = 1" in accept, f"{country.tag} accepted armistice omits separate peace")
        require(errors, f"type = peace which = {country.tag} value = 1" in counter, f"{country.tag} counteroffer omits limited separate peace")
        require(errors, "type = peace" not in refuse, f"{country.tag} refusal accidentally ends a war")
        for callback_name, callback in (("acceptance", accept), ("counteroffer", counter)):
            require(errors, f"type = setflag which = ind_aubm_global_settled_{key}" in callback, f"{country.tag} {callback_name} does not record settlement")
            require(errors, f"type = clrflag which = ind_aubm_global_active_{key}" in callback, f"{country.tag} {callback_name} does not close its active campaign")
            require(errors, f"type = clrflag which = {target_flag}" in callback, f"{country.tag} {callback_name} does not release its target lock")
            require(errors, "type = clrflag which = ind_aubm_universal_armistice_outstanding" in callback, f"{country.tag} {callback_name} does not release the response lock")
        require(errors, f"type = setflag which = {retry_flag}" in counter, f"{country.tag} counteroffer cannot be postponed independently")
        require(errors, f"which = {ids.retry_release} where = IND when = 90" in counter, f"{country.tag} postponed counteroffer has no cooldown callback")
        require(errors, f"type = setflag which = {retry_flag}" in refuse, f"{country.tag} refusal has no country-specific cooldown")
        require(errors, f"which = {ids.retry_release} where = IND when = 90" in refuse, f"{country.tag} refusal has no retry callback")
        require(errors, f"type = clrflag which = {target_flag}" in refuse, f"{country.tag} refusal does not release its target lock")
        require(errors, "type = clrflag which = ind_aubm_universal_armistice_outstanding" in refuse, f"{country.tag} refusal does not release the response lock")
        callback_bundle = "\n".join((declaration, accept, counter, refuse, country_lapse))
        callback_targets = set(re.findall(r"ind_aubm_armistice_target_([a-z0-9_]+)", callback_bundle))
        callback_retries = set(re.findall(r"ind_aubm_armistice_retry_([a-z0-9_]+)", callback_bundle))
        require(errors, callback_targets <= {key}, f"{country.tag} callbacks reference another country's target lock")
        require(errors, callback_retries <= {key}, f"{country.tag} callbacks reference another country's retry lock")
        require(errors, f"type = clrflag which = {target_flag}" in country_lapse, f"vanished {country.tag} target flag is never cleared")
        require(errors, f"type = clrflag which = ind_aubm_global_active_{key}" in country_lapse, f"third-party annexation of {country.tag} cannot reset its interrupted lifecycle")
        require(errors, f"type = clrflag which = ind_aubm_global_pending_{key}" in country_lapse, f"third-party annexation of {country.tag} leaves a pending settlement")
        require(errors, f"type = clrflag which = ind_aubm_global_victory_{key}" in country_lapse, f"third-party annexation of {country.tag} leaves live victory state")
        require(errors, f"type = clrflag which = ind_aubm_global_rewarded_{key}" not in country_lapse, f"vanished {country.tag} audit erases earned campaign credit")
        require(errors, "type = clrflag which = ind_aubm_global_campaign_victory" not in country_lapse, f"vanished {country.tag} audit erases route congress credit")
        require(errors, f"owned = {{ province = {country.capital} data = IND }} control = {{ province = {country.capital} data = IND }}" in country_lapse, f"{country.tag} annexation recovery omits verified Indian ownership and control")
        require(errors, f"which = {ids.settlement} where = IND when = 1" in country_lapse, f"{country.tag} annexation recovery does not open its constitutional settlement")
        require(errors, f"type = independence which = {country.tag}" in settlement, f"{country.tag} settlement cannot restore sovereignty")
        require(errors, f"type = make_puppet which = {country.tag}" in settlement, f"{country.tag} settlement cannot establish a protectorate")
        require(errors, f"ind_aubm_global_direct_{key}" in settlement, f"{country.tag} settlement has no direct-administration state")
        require(errors, "when = 90" in settlement, f"{country.tag} constitutional settlement cannot be deferred")
        require(errors, f"ind_aubm_global_rewarded_{key}" in victory, f"{country.tag} victory reward is repeatable")
        require(errors, "ind_aubm_global_campaign_victory" in victory, f"{country.tag} victory cannot unlock a route congress")
        require(errors, f"flag = ind_aubm_global_active_{key}" in annex_monitor, f"{country.tag} annexation monitor can reward an unrelated inheritance")
        require(errors, f"flag = ind_aubm_global_victory_{key}" in annex_monitor, f"{country.tag} annexation monitor lacks verified campaign credit")
        require(errors, f"NOT = {{ exists = {country.tag} }}" in annex_monitor, f"{country.tag} annexation monitor can fire while the opponent survives")
        require(errors, f"province = {country.capital} data = IND" in annex_monitor, f"{country.tag} annexation monitor omits legal Indian ownership")
        require(errors, f"which = {ids.settlement} where = IND" in annex_monitor, f"{country.tag} annexation monitor does not open its constitutional settlement")
        require(errors, f"type = clrflag which = ind_aubm_armistice_retry_{key}" in retry_release, f"{country.tag} retry cooldown never releases")
        require(errors, f"which = {ids.docket} where = IND" in retry_release, f"{country.tag} retry cooldown does not reopen its own docket")
        require(errors, "ind_aubm_universal_armistice_retry_pending" not in docket, f"{country.tag} still uses a global refusal lock")

    checks += 5
    require(errors, all(group in world_index for group in ("Europe", "Asia", "Americas", "Africa")), "world index omits a geographic group")
    require(errors, len({country.tag for country in COUNTRIES}) == len(COUNTRIES), "country matrix contains duplicate tags")
    require(errors, REQUIRED_EMERGENT_TAGS <= {country.tag for country in COUNTRIES}, "standard emergent-state coverage is incomplete")
    require(errors, BASELINE_1933_TARGETS <= ({country.tag for country in COUNTRIES} | BESPOKE_CAMPAIGN_TAGS), "one or more 1933 countries have no campaign lifecycle")
    require(errors, "ind_aubm_universal_armistice_retry_pending" not in text, "global armistice retry lock still blocks unrelated countries")

    if errors:
        print(f"AUBM global campaign validation failed ({len(errors)} errors, {checks} checks):")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print(f"AUBM global campaign validation passed ({checks} checks, {len(COUNTRIES)} countries, {len(events)} events).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
