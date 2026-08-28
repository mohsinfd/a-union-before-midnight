#!/usr/bin/env python3
"""Acceptance checks for AUBM's coalition-independent wartime framework."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_ROOT = ROOT / "mod/db/events"
INDEX = ROOT / "mod/db/events.txt"
MODULE_NAMES = (
    "41_wartime_state.txt",
    "42_wartime_theatres.txt",
    "43_wartime_settlements.txt",
    "44_wartime_economy.txt",
    "45_enemy_campaigns.txt",
    "46_regional_campaigns.txt",
	"48_route_wartime_consequences.txt",
	"49_bespoke_armistices.txt",
	"50_southeast_asia_operations.txt",
)
MODULE_PATHS = tuple(EVENT_ROOT / "aubm_v4" / name for name in MODULE_NAMES)

ROUTES = {
    9281901: "ind_aubm_route_allied",
    9281902: "ind_aubm_route_german",
    9281903: "ind_aubm_route_soviet",
    9281904: "ind_aubm_route_japan",
    9281905: "ind_aubm_route_sovereign",
}
COMPACTS = {
    9281906: "ind_aubm_route_allied",
    9281907: "ind_aubm_route_german",
    9281908: "ind_aubm_route_soviet",
    9281909: "ind_aubm_socialist_autonomous",
}
RELATIONSHIP_FAMILIES = {
    "allied": (
        "ind_v4a_treaty_commonwealth",
        "ind_v4a_treaty_naval_compact",
        "ind_v4a_treaty_formal_alliance",
        "ind_v4a_treaty_cobelligerent",
    ),
    "german": (
        "ind_gc_formal_axis",
        "ind_gc_cobelligerent",
        "ind_gc_sovereign",
    ),
    "soviet": (
        "ind_v4_sov_equal_compact",
        "ind_v4_sov_supervised_compact",
        "ind_v4_sov_autonomous_socialism",
        "ind_aubm_socialist_autonomous",
    ),
    "japan": (
        "ind_aubm_jp_partnership",
        "ind_aubm_jp_formal_alliance",
        "ind_aubm_jp_independent_cobelligerent",
        "ind_aubm_jp_tier_senior",
        "ind_aubm_jp_tier_peer",
        "ind_aubm_jp_tier_junior",
        "ind_aubm_jp_tier_counter",
        "ind_aubm_jp_india_full_sphere",
        "ind_aubm_jp_india_core_sphere",
    ),
}
RELATIONSHIP_SYNCHRONIZERS = {
    9281901: "allied",
    9281902: "german",
    9281903: "soviet",
    9281904: "japan",
    9281906: "allied",
    9281907: "german",
    9281908: "soviet",
    9281909: "soviet",
}
MAJOR_TARGETS = ("ENG", "GER", "SOV", "JAP", "USA")
REGIONAL_CAPITALS = {
    "PER": (1085, "per"),
    "IRQ": (1034, "irq"),
    "SAU": (1045, "sau"),
    "AFG": (2171, "afg"),
    "TIB": (1289, "tib"),
    "SIK": (1281, "sik"),
    "CHI": (1337, "chi"),
    "CHC": (1354, "chc"),
    "SIA": (1423, "sia"),
    "ITA": (419, "ita"),
    "FRA": (55, "fra"),
    "TUR": (1075, "tur"),
    "U05": (1647, "u05"),
    "HOL": (122, "hol"),
    "AST": (1707, "ast"),
    "POR": (476, "por"),
    "NZL": (1721, "nzl"),
    "OMN": (1052, "omn"),
    "YEM": (1050, "yem"),
    "ETH": (825, "eth"),
    "SAF": (876, "saf"),
}
PROPOSALS = (
    ("CHI", "chi", 9282210, 9282220),
    ("CHC", "chc", 9282211, 9282221),
    ("SIA", "sia", 9282212, 9282222),
    ("ITA", "ita", 9282213, 9282223),
    ("FRA", "fra", 9282214, 9282224),
    ("TUR", "tur", 9282215, 9282225),
    ("POR", "por", 9282216, 9282226),
    ("NZL", "nzl", 9282217, 9282227),
    ("ETH", "eth", 9282218, 9282228),
    ("SAF", "saf", 9282219, 9282229),
)
BESPOKE_PROPOSALS = (
    ("PER", "per", 1085, 9282270, 9282280),
    ("IRQ", "irq", 1034, 9282271, 9282281),
    ("SAU", "sau", 1045, 9282272, 9282282),
    ("YEM", "yem", 1050, 9282273, 9282283),
    ("OMN", "omn", 1052, 9282274, 9282284),
    ("AFG", "afg", 2171, 9282275, 9282285),
    ("TIB", "tib", 1289, 9282276, 9282286),
    ("SIK", "sik", 1281, 9282277, 9282287),
)


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
    return blocks


def parse_events(paths: tuple[Path, ...]) -> dict[int, str]:
    events: dict[int, str] = {}
    for path in paths:
        for block in event_blocks(path.read_text(encoding="cp1252")):
            match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
            if match:
                event_id = int(match.group(1))
                if event_id in events:
                    raise ValueError(f"duplicate event ID {event_id}")
                events[event_id] = block
    return events


def action_blocks(block: str) -> dict[str, str]:
    clean = strip_comments(block)
    actions: dict[str, str] = {}
    for match in re.finditer(r"(?m)^\s*action_([a-d])\s*=\s*\{", clean):
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
                    actions[match.group(1)] = clean[match.start() : position + 1]
                    break
    return actions


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def contains_war_command(block: str, tag: str) -> bool:
    return re.search(rf"type\s*=\s*war\s+which\s*=\s*{tag}\b", block) is not None


def response_odds(block: str) -> tuple[int, ...]:
    return tuple(int(value) for value in re.findall(r"\bai_chance\s*=\s*(\d+)", block))


def main() -> int:
    errors: list[str] = []
    checks = 0

    for path in MODULE_PATHS:
        require(errors, path.exists(), f"missing wartime module {path.name}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    try:
        events = parse_events(MODULE_PATHS)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    index_text = INDEX.read_text(encoding="cp1252").replace("\\", "/")
    for name in MODULE_NAMES:
        include = f'event = "db/events/aubm_v4/{name}"'
        checks += 1
        require(errors, index_text.count(include) == 1, f"{name} must be loaded exactly once")

    migration = events.get(9281900, "")
    for forbidden in (9280840, 9280841):
        checks += 1
        require(
            errors,
            f"sleepevent which = {forbidden}" not in migration,
            f"migration must not sleep trained-reserve event {forbidden}",
        )
    for route in ROUTES.values():
        checks += 1
        require(errors, route in migration, f"migration omits canonical route {route}")

    route_flags = tuple(ROUTES.values())
    for event_id, selected in ROUTES.items():
        block = events.get(event_id, "")
        checks += 1
        require(errors, f"type = setflag which = {selected}" in block, f"{event_id} does not set {selected}")
        for sibling in route_flags:
            if sibling == selected:
                continue
            checks += 1
            require(
                errors,
                f"type = clrflag which = {sibling}" in block,
                f"{event_id} does not clear incompatible route {sibling}",
            )
    for event_id, token in COMPACTS.items():
        checks += 1
        require(errors, token in events.get(event_id, ""), f"compact synchronizer {event_id} omits {token}")

    compact_commitment_family = {
        9281906: "allied",
        9281907: "german",
        9281908: "soviet",
    }
    for event_id, selected in compact_commitment_family.items():
        block = events.get(event_id, "")
        for rival in ("allied", "german", "soviet", "japan"):
            if rival == selected:
                continue
            checks += 1
            require(errors, f"NOT = {{ flag = ind_aubm_commitment_{rival} }}" in block, f"compact synchronizer {event_id} can override {rival} commitment")
    for family in ("allied", "german", "soviet", "japan"):
        checks += 1
        require(errors, f"NOT = {{ flag = ind_aubm_commitment_{family} }}" in events.get(9281909, ""), f"autonomous-socialist synchronizer can override {family} commitment")

    for event_id, selected_family in RELATIONSHIP_SYNCHRONIZERS.items():
        block = events.get(event_id, "")
        for family, tokens in RELATIONSHIP_FAMILIES.items():
            if family == selected_family:
                continue
            for token in tokens:
                checks += 1
                require(
                    errors,
                    f"type = clrflag which = {token}" in block,
                    f"relationship synchronizer {event_id} does not terminate incompatible {family} token {token}",
                )

    formal_repairs = {
        9281901: "OR = { NOT = { flag = ind_aubm_route_allied } NOT = { flag = ind_v4a_treaty_formal_alliance } }",
        9281902: "OR = { NOT = { flag = ind_aubm_route_german } NOT = { flag = ind_gc_formal_axis } }",
        9281903: "OR = { NOT = { flag = ind_aubm_route_soviet } NOT = { flag = ind_v3_joined_comintern } }",
        9281904: "AND = { alliance = { country = IND country = JAP } NOT = { flag = ind_aubm_jp_formal_alliance } }",
    }
    for event_id, repair_guard in formal_repairs.items():
        checks += 1
        require(errors, repair_guard in events.get(event_id, ""), f"formal synchronizer {event_id} cannot repair a stale compact marker")

    bootstrap_action = action_blocks(events.get(9281900, "")).get("a", "")
    formal_precedence = (
        "type = setflag which = ind_aubm_route_allied",
        "type = setflag which = ind_aubm_route_german",
        "type = setflag which = ind_aubm_route_soviet",
        "type = setflag which = ind_aubm_route_japan",
    )
    precedence_positions = tuple(bootstrap_action.find(token) for token in formal_precedence)
    checks += len(formal_precedence) + 1
    for token, position in zip(formal_precedence, precedence_positions):
        require(errors, position >= 0, f"wartime bootstrap omits formal precedence token {token}")
    require(
        errors,
        precedence_positions == tuple(sorted(precedence_positions)) and len(set(precedence_positions)) == len(precedence_positions),
        "wartime bootstrap does not apply Allied > German > Soviet > Japanese precedence",
    )

    japan_formal_sync = events.get(9281904, "")
    for partner in ("ENG", "USA", "GER", "SOV"):
        checks += 1
        require(
            errors,
            f"NOT = {{ alliance = {{ country = IND country = {partner} }} }}" in japan_formal_sync,
            f"Japanese formal synchronizer can override an existing {partner} coalition",
        )
    checks += 1
    require(errors, "exists = JAP" in japan_formal_sync, "Japanese formal synchronizer does not require Japan to exist")

    formal_exclusions = {
        9281901: ("GER", "SOV"),
        9281902: ("ENG", "USA"),
        9281903: ("ENG", "USA", "GER"),
    }
    for event_id, incompatible_partners in formal_exclusions.items():
        block = events.get(event_id, "")
        for partner in incompatible_partners:
            checks += 1
            require(
                errors,
                f"NOT = {{ alliance = {{ country = IND country = {partner} }} }}" in block,
                f"formal synchronizer {event_id} can override an existing {partner} coalition",
            )
    for event_id, partner in ((9281907, "GER"), (9281908, "SOV")):
        checks += 1
        require(errors, f"exists = {partner}" in events.get(event_id, ""), f"compact synchronizer {event_id} survives a missing {partner}")

    bootstrap = events.get(9281900, "")
    checks += 1
    require(
        errors,
        "OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } } } type = setflag which = ind_v3_joined_allies" in bootstrap,
        "wartime bootstrap does not recognize an existing American-led Allied membership",
    )

    coalition_menu = events.get(9281910, "")
    coalition_actions = action_blocks(coalition_menu)
    for letter, partners in {"b": ("GER",), "c": ("SOV",)}.items():
        action = coalition_actions.get(letter, "")
        for partner in partners:
            checks += 1
            require(
                errors,
                f"war = {{ country = IND country = {partner} }}" in action,
                f"coalition menu action {letter} can join while India is at war with {partner}",
            )

    allied_selector = coalition_actions.get("a", "")
    allied_partner_actions = action_blocks(events.get(9281934, ""))
    checks += 10
    require(errors, "year = 1937" in allied_selector, "Allied formal entry bypasses the 1937 chronology")
    require(errors, "event which = 9281934" in allied_selector, "Allied entry does not expose an explicit leader choice")
    for letter, partner in (("a", "ENG"), ("b", "USA")):
        action = allied_partner_actions.get(letter, "")
        require(errors, f"type = alliance which = {partner} when = 1" in action, f"Allied entry cannot join safely through {partner}")
        require(errors, "war = { country = IND country = ENG }" in action, f"Allied {partner} entry ignores a British war")
        require(errors, "war = { country = IND country = USA }" in action, f"Allied {partner} entry ignores an American war")
        require(errors, "event which = 9281901" in action, f"Allied {partner} entry does not schedule canonical normalization")

    compact_actions = action_blocks(events.get(9281919, ""))
    compact_chronology = {"a": 1938, "b": 1940, "c": 1937}
    for letter, year in compact_chronology.items():
        checks += 1
        require(
            errors,
            f"year = {year}" in compact_actions.get(letter, ""),
            f"strategic compact {letter} bypasses its {year} chronology",
        )
    berlin_menu = compact_actions.get("b", "")
    for guard in (
        "ispuppet = IND",
        "ind_gc_formal_axis",
        "ind_gc_cobelligerent",
        "ind_gc_sovereign",
        "ind_gc_berlin_negotiating",
        "ind_gc_berlin_cooldown",
    ):
        checks += 1
        require(errors, guard in berlin_menu, f"War Cabinet can bypass Berlin conference guard {guard}")
    japan_menu_actions = action_blocks(events.get(9281914, ""))
    for letter, route_name in (("a", "Tokyo alliance"), ("b", "autonomous socialism"), ("d", "Tokyo compact")):
        checks += 1
        require(errors, "year = 1937" in japan_menu_actions.get(letter, ""), f"{route_name} bypasses the 1937 chronology")

    commitment_flags = {
        "allied": "ind_aubm_commitment_allied",
        "german": "ind_aubm_commitment_german",
        "soviet": "ind_aubm_commitment_soviet",
        "japan": "ind_aubm_commitment_japan",
    }
    legacy_binding = {
        "allied": RELATIONSHIP_FAMILIES["allied"],
        "german": ("ind_gc_formal_axis", "ind_gc_cobelligerent"),
        "soviet": ("ind_v4_sov_equal_compact", "ind_v4_sov_supervised_compact"),
        "japan": ("ind_aubm_jp_partnership",),
    }
    route_entries = {
        "allied": (allied_partner_actions.get("a", ""), allied_partner_actions.get("b", ""), compact_actions.get("a", "")),
        "german": (coalition_actions.get("b", ""), compact_actions.get("b", "")),
        "soviet": (coalition_actions.get("c", ""), compact_actions.get("c", "")),
        "japan": (japan_menu_actions.get("a", ""), japan_menu_actions.get("d", "")),
    }
    for selected, entries in route_entries.items():
        for entry_number, action in enumerate(entries, start=1):
            checks += 2
            require(errors, "NOT = { participant = { country = IND value = 4 } }" in action, f"{selected} route entry {entry_number} ignores a live formal alliance")
            require(errors, "ind_aubm_diplomatic_negotiation_pending" in action and "ind_aubm_realignment_cooldown" in action, f"{selected} route entry {entry_number} bypasses pending/cooldown serialization")
            if "type = alliance" in action:
                checks += 1
                require(errors, f"NOT = {{ flag = {commitment_flags[selected]} }}" not in action, f"{selected} formal entry {entry_number} blocks its own compact-to-formal upgrade")
            for rival, commitment in commitment_flags.items():
                if rival == selected:
                    continue
                checks += 1
                require(errors, f"NOT = {{ flag = {commitment} }}" in action, f"{selected} route entry {entry_number} ignores rival {rival} commitment")
                for token in legacy_binding[rival]:
                    checks += 1
                    require(errors, f"NOT = {{ flag = {token} }}" in action, f"{selected} route entry {entry_number} ignores legacy {rival} binding token {token}")

    for letter, partner in (("b", "GER"), ("c", "SOV")):
        checks += 1
        require(errors, f"type = alliance which = {partner} when = 1" in coalition_actions.get(letter, ""), f"{partner} formal entry still uses side-switch semantics")
    checks += 1
    require(errors, "type = alliance which = JAP when = 1" in japan_menu_actions.get("a", ""), "Japanese formal entry still uses side-switch semantics")

    commitment_migration = events.get(9281949, "")
    checks += 9
    require(errors, "persistent = yes" in commitment_migration, "Alpha20 commitment migration is not scenario-long")
    require(errors, "ind_aubm_commitment_migration_alpha20" in commitment_migration, "Alpha20 commitment migration is not one-shot")
    require(errors, "AND = { flag = ind_aubm_jp_partnership NOT = { flag = ind_aubm_jp_rupture } }" in commitment_migration, "old Tokyo-compact saves are not recognized by migration")
    for commitment in commitment_flags.values():
        require(errors, f"type = setflag which = {commitment}" in commitment_migration, f"migration cannot reconstruct {commitment}")
    require(errors, "sleepevent which = 9270456" in commitment_migration, "migration does not retire legacy 1939 War in Europe bypass")
    require(errors, "sleepevent which = 9280940" in commitment_migration, "migration does not retire legacy War Cabinet bypass")

    migration_routes = {
        "allied": "ind_aubm_route_allied",
        "german": "ind_aubm_route_german",
        "soviet": "ind_aubm_route_soviet",
        "japan": "ind_aubm_route_japan",
    }
    for family, route_flag in migration_routes.items():
        checks += 2
        require(errors, f"type = clrflag which = {route_flag}" in commitment_migration, f"migration does not clear stale {family} route state")
        require(
            errors,
            f"trigger = {{ flag = {commitment_flags[family]} }} type = setflag which = {route_flag}" in commitment_migration,
            f"migration does not rebuild the {family} route from its selected commitment",
        )
    checks += 2
    require(errors, "type = clrflag which = ind_aubm_route_sovereign" in commitment_migration, "migration does not clear stale sovereign route state")
    require(
        errors,
        "NOT = { participant = { country = IND value = 4 } }" in commitment_migration
        and "type = setflag which = ind_aubm_route_sovereign" in commitment_migration,
        "migration can label a live formal-alliance member sovereign",
    )

    migration_binding = {
        "allied": (
            "ind_v4a_treaty_commonwealth",
            "ind_v4a_treaty_naval_compact",
            "ind_v4a_treaty_formal_alliance",
            "ind_v4a_treaty_cobelligerent",
        ),
        "german": ("ind_gc_formal_axis", "ind_gc_cobelligerent"),
        "soviet": (
            "ind_v4_sov_equal_compact",
            "ind_v4_sov_supervised_compact",
            "ind_v4_sov_formal_alliance",
            "ind_v4_sov_independent_cobelligerent",
        ),
        "japan": (
            "ind_aubm_jp_partnership",
            "ind_aubm_jp_formal_alliance",
            "ind_aubm_jp_independent_cobelligerent",
        ),
    }
    for family, tokens in migration_binding.items():
        for token in tokens:
            checks += 1
            require(
                errors,
                f"trigger = {{ NOT = {{ flag = {commitment_flags[family]} }} }} type = clrflag which = {token}" in commitment_migration,
                f"migration does not remove rival {family} binding state {token}",
            )
    checks += 7
    precedence_offsets = [
        commitment_migration.find(f"type = setflag which = {commitment_flags[family]}")
        for family in ("allied", "german", "soviet", "japan")
    ]
    require(errors, all(offset >= 0 for offset in precedence_offsets) and precedence_offsets == sorted(precedence_offsets), "migration precedence is not Allied > German > Soviet > Japanese")
    first_binding_offset = commitment_migration.find("flag = ind_v4a_treaty_commonwealth")
    last_formal_offset = commitment_migration.find("alliance = { country = IND country = JAP } } type = setflag which = ind_aubm_commitment_japan")
    require(errors, first_binding_offset >= 0 and last_formal_offset >= 0 and last_formal_offset < first_binding_offset, "migration lets a stale binding compact outrank live formal alliance membership")
    require(errors, "flag = ind_gc_cobelligerent" in commitment_migration and "flag = ind_aubm_jp_partnership" in commitment_migration, "migration cannot canonicalize an old Germany-over-Tokyo exploit save")
    require(errors, "ind_v4_sov_formal_alliance" in commitment_migration, "migration misses legacy formal Soviet commitment state")
    require(errors, "ind_v4_sov_independent_cobelligerent" in commitment_migration, "migration misses legacy Soviet co-belligerency state")
    require(errors, "ind_aubm_jp_independent_cobelligerent" in commitment_migration, "migration misses legacy Japanese co-belligerency state")
    require(errors, "type = clrflag which = ind_aubm_route_achievement_" not in commitment_migration, "migration erases completed route achievements")

    for recovery_id in (9281935, 9281936):
        recovery = events.get(recovery_id, "")
        checks += 2
        require(errors, "persistent = yes" in recovery, f"Allied lock recovery {recovery_id} is not persistent")
        require(
            errors,
            "type = clrflag which = ind_v4a_allied_framework_started" in recovery,
            f"Allied lock recovery {recovery_id} does not release the conference",
        )
    stalled_allied = events.get(9281936, "")
    for proposal in ("commonwealth", "naval_compact", "formal_alliance", "cobelligerent"):
        checks += 1
        require(
            errors,
            f"type = clrflag which = ind_v4a_proposal_{proposal}" in stalled_allied,
            f"Allied lock recovery does not clear the {proposal} proposal",
        )

    allied_failover = events.get(9281937, "")
    checks += 7
    require(errors, "persistent = yes" in allied_failover, "Allied partner failover is not persistent")
    require(errors, "ind_aubm_route_allied" in allied_failover, "Allied partner failover is not route-gated")
    require(errors, "ind_aubm_allied_partner_eng" in allied_failover, "Allied failover omits the British partner")
    require(errors, "ind_aubm_allied_partner_usa" in allied_failover, "Allied failover omits the American partner")
    require(errors, "NOT = { exists = ENG }" in allied_failover and "exists = USA" in allied_failover, "Allied failover cannot move London to Washington")
    require(errors, "NOT = { exists = USA }" in allied_failover and "exists = ENG" in allied_failover, "Allied failover cannot move Washington to London")
    require(errors, "type = clrflag which = ind_aubm_campaign_" not in allied_failover, "Allied failover erases campaign credit")

    partner_claim = events.get(9282170, "")
    checks += 4
    require(errors, "ind_aubm_allied_partner_eng" in partner_claim, "battlefield claim loses the selected British partner")
    require(errors, "ind_aubm_allied_partner_usa" in partner_claim, "battlefield claim loses the selected American partner")
    require(errors, "which = 9282171 where = ENG" in partner_claim, "battlefield claim cannot reach London")
    require(errors, "which = 9282175 where = USA" in partner_claim, "battlefield claim cannot reach Washington")

    cabinet_transitions = (
        (9281910, "b", "german"),
        (9281910, "c", "soviet"),
        (9281914, "a", "japan"),
        (9281914, "b", "soviet"),
    )
    for event_id, letter, selected_family in cabinet_transitions:
        action = action_blocks(events.get(event_id, "")).get(letter, "")
        for family, tokens in RELATIONSHIP_FAMILIES.items():
            if family == selected_family:
                continue
            for token in tokens:
                checks += 1
                require(
                    errors,
                    f"type = clrflag which = {token}" in action,
                    f"Cabinet transition {event_id}/{letter} does not terminate incompatible {family} token {token}",
                )

    allied_sync = events.get(9281901, "")
    for family, tokens in RELATIONSHIP_FAMILIES.items():
        if family == "allied":
            continue
        for token in tokens:
            checks += 1
            require(
                errors,
                f"type = clrflag which = {token}" in allied_sync,
                f"Allied canonical synchronizer does not terminate incompatible {family} token {token}",
            )

    sovereign_action = action_blocks(events.get(9281914, "")).get("c", "")
    for family, tokens in RELATIONSHIP_FAMILIES.items():
        for token in tokens:
            checks += 1
            require(
                errors,
                f"type = clrflag which = {token}" in sovereign_action,
                f"sovereign withdrawal does not terminate {family} token {token}",
            )

    allied_legacy = (EVENT_ROOT / "aubm_v4" / "36_allied_campaigns.txt").read_text(encoding="cp1252")
    legacy_alliances = re.findall(r"type\s*=\s*alliance\s+which\s*=\s*(?:IND|ENG)([^}]*)}", allied_legacy)
    checks += 1
    require(
        errors,
        bool(legacy_alliances) and all("when = 1" in tail for tail in legacy_alliances),
        "legacy Allied conference still uses direct side-switch alliance semantics",
    )

    german_recovery = events.get(9282142, "")
    for left, right in ((377, 338), (377, 195), (377, 419), (338, 195), (338, 419), (195, 419)):
        pair = f"control = {{ province = {left} data = IND }} control = {{ province = {right} data = IND }}"
        checks += 1
        require(
            errors,
            german_recovery.count(pair) >= 2,
            f"German campaign recovery omits valid objective pair ({left}, {right}) from its outer trigger",
        )

    rupture = events.get(9281998, "")
    checks += 13
    require(errors, "persistent = yes" in rupture, "strategic-partner rupture monitor is not reusable")
    for route, partner in (
        ("ind_aubm_route_allied", "ENG"),
        ("ind_aubm_route_german", "GER"),
        ("ind_aubm_route_soviet", "SOV"),
        ("ind_aubm_route_japan", "JAP"),
    ):
        require(errors, route in rupture, f"strategic-partner rupture monitor omits {route}")
        require(
            errors,
            f"war = {{ country = IND country = {partner} }}" in rupture,
            f"strategic-partner rupture monitor omits war with {partner}",
        )
    require(errors, "setflag which = ind_aubm_route_sovereign" in rupture, "partner rupture does not restore sovereign command")
    require(errors, "type = leave_alliance" in rupture, "partner rupture does not leave the invalid alliance")
    require(errors, "setflag which = ind_aubm_realignment_cooldown" in rupture and "event which = 9281938 where = IND when = 90" in rupture, "partner rupture permits an immediate coalition pivot")
    require(errors, "type = clrflag which = ind_aubm_campaign_" not in rupture, "partner rupture erases campaign credit")

    collapse = events.get(9281997, "")
    checks += 9
    require(errors, "persistent = yes" in collapse, "partner-collapse monitor is not persistent")
    require(errors, "type = leave_alliance" in collapse, "partner-collapse monitor does not leave the dead coalition")
    require(errors, "setflag which = ind_aubm_route_sovereign" in collapse, "partner collapse does not restore sovereign command")
    require(errors, "setflag which = ind_aubm_realignment_cooldown" in collapse and "event which = 9281938 where = IND when = 90" in collapse, "partner collapse permits an immediate coalition pivot")
    for route, partner in (
        ("ind_aubm_route_allied", "ENG"),
        ("ind_aubm_route_german", "GER"),
        ("ind_aubm_route_soviet", "SOV"),
        ("ind_aubm_route_japan", "JAP"),
    ):
        require(errors, route in collapse and f"exists = {partner}" in collapse, f"partner-collapse monitor omits {route}/{partner}")
    require(
        errors,
        re.search(r"type\s*=\s*clrflag\s+which\s*=\s*ind_aubm_\S*(?:victory|achievement|campaign)", collapse) is None,
        "partner collapse erases earned campaign or victory credit",
    )

    german_campaign_events = parse_events((EVENT_ROOT / "aubm_v4" / "37_german_campaigns.txt",))
    german_collapse = german_campaign_events.get(9281353, "")
    german_collapse_actions = action_blocks(german_collapse)
    checks += 3
    require(errors, set(german_collapse_actions) == {"a", "b"}, "German-collapse response does not expose both sovereign outcomes")
    for letter in ("a", "b"):
        action = german_collapse_actions.get(letter, "")
        require(errors, "setflag which = ind_aubm_realignment_cooldown" in action and "event which = 9281938 where = IND when = 90" in action, f"German-collapse action {letter} permits an immediate coalition pivot")

    bitter_peace = events.get(9281996, "")
    bitter_actions = action_blocks(bitter_peace)
    checks += 8
    require(errors, "persistent = yes" in bitter_peace, "Bitter Peace handling is not persistent")
    require(errors, "event = 2007033" in bitter_peace and "war = { country = IND country = SOV }" in bitter_peace, "Bitter Peace cannot reach an independent India-Soviet war")
    require(errors, set(bitter_actions) == {"a", "b", "c"}, "Bitter Peace does not expose all three Indian responses")
    require(errors, "type = peace which = SOV" in bitter_actions.get("a", ""), "India cannot enter the Bitter Peace armistice")
    require(errors, "war = { country = IND country = SOV }" in bitter_actions.get("b", ""), "separate Soviet war is not state-gated")
    require(errors, "type = peace which = SOV" not in bitter_actions.get("b", ""), "separate Soviet war is accidentally terminated")
    require(errors, "ind_aubm_bitter_peace_independent_war" in bitter_actions.get("b", ""), "separate Soviet war is not recorded")
    require(errors, "NOT = { war = { country = IND country = SOV } }" in bitter_actions.get("c", ""), "inherited Bitter Peace response can fire during a live war")
    require(errors, "type = clrflag which = ind_aubm_" not in bitter_peace, "Bitter Peace erases India's campaign ledger")

    all_paths = tuple(sorted((EVENT_ROOT / "aubm_v4").glob("*.txt")))
    all_events = parse_events(all_paths)
    all_event_text = "\n".join(path.read_text(encoding="cp1252") for path in all_paths)

    delayed_acceptances = {
        9280966: ("soviet", "a", "b"),
        9280967: ("soviet", "a", "c"),
        9281113: ("japan", "a", "b"),
        9281205: ("allied", "a", "b"),
        9281208: ("allied", "a", "b"),
        9281211: ("allied", "a", "b"),
        9281214: ("allied", "a", "b"),
        9281304: ("german", "a", "b"),
        9281307: ("german", "a", "b"),
        9281402: ("soviet", "a", "b"),
        9281403: ("soviet", "a", "d"),
        9281453: ("soviet", "a", "d"),
    }
    for event_id, (family, acceptance_letter, lapse_letter) in delayed_acceptances.items():
        actions = action_blocks(all_events.get(event_id, ""))
        accepted = actions.get(acceptance_letter, "")
        lapsed = actions.get(lapse_letter, "")
        checks += 6
        require(errors, "ind_aubm_diplomatic_negotiation_pending" in accepted, f"delayed acceptance {event_id} does not revalidate the global pending file")
        require(errors, f"ind_aubm_negotiation_{family}" in accepted, f"delayed acceptance {event_id} does not revalidate its {family} file")
        require(errors, "NOT = { participant = { country = IND value = 4 } }" in accepted, f"delayed acceptance {event_id} can override a formal alliance")
        require(errors, f"setflag which = ind_aubm_commitment_{family}" in accepted, f"delayed acceptance {event_id} does not record the binding {family} commitment")
        require(errors, "clrflag which = ind_aubm_diplomatic_negotiation_pending" in lapsed, f"stale callback {event_id} has no global lapse path")
        require(errors, f"clrflag which = ind_aubm_negotiation_{family}" in lapsed, f"stale callback {event_id} has no family lapse path")

    relationship_paths = tuple(EVENT_ROOT / "aubm_v4" / name for name in (
        "22_crisis_interventions.txt",
        "35_japan_partnership.txt",
        "36_allied_campaigns.txt",
        "37_german_campaigns.txt",
        "38_soviet_campaigns.txt",
        "41_wartime_state.txt",
    ))
    relationship_text = "\n".join(path.read_text(encoding="cp1252") for path in relationship_paths)
    checks += 1
    require(errors, re.search(r"type\s*=\s*alliance\s+which\s*=\s*\w+\s+when\s*=\s*2", relationship_text) is None, "a diplomatic route still contains alliance when=2 side-switch semantics")

    soviet_wartime_root = all_events.get(9281450, "")
    soviet_delayed_demand = action_blocks(all_events.get(9281453, "")).get("a", "")
    checks += 6
    require(errors, "NOT = { participant = { country = IND value = 4 } }" in soviet_wartime_root, "legacy Soviet wartime negotiation ignores a live alliance")
    require(errors, "ind_aubm_diplomatic_negotiation_pending" in soviet_wartime_root, "legacy Soviet wartime negotiation is not serialized")
    require(errors, "ind_aubm_jp_partnership" in soviet_wartime_root, "legacy Soviet wartime negotiation ignores the Tokyo compact")
    require(errors, "type = alliance which = SOV when = 1" in soviet_delayed_demand, "legacy delayed Soviet alliance still side-switches")
    require(errors, "ind_aubm_negotiation_soviet" in soviet_delayed_demand, "legacy delayed Soviet alliance does not revalidate")
    require(errors, "ind_aubm_commitment_soviet" in soviet_delayed_demand, "legacy delayed Soviet alliance does not bind the Soviet route")

    legacy_reactions = parse_events((EVENT_ROOT / "india_v3" / "46_world_reactions.txt",))
    checks += 2
    require(errors, "NOT = { flag = ind_aubm_wartime_framework }" in legacy_reactions.get(9270456, ""), "legacy War in Europe event can reopen the retired cabinet")
    legacy_cabinet = all_events.get(9280940, "")
    require(errors, all("NOT = { participant = { country = IND value = 4 } }" in action_blocks(legacy_cabinet).get(letter, "") for letter in ("a", "b", "c")), "legacy 1939 cabinet can override a live alliance")

    legacy_diplomacy = parse_events((EVENT_ROOT / "india_v3" / "40_diplomacy.txt",))
    soviet_technical_compact = legacy_diplomacy.get(9270403, "")
    delhi_pact = all_events.get(9280968, "")
    checks += 4
    require(errors, "NOT = { participant = { country = IND value = 4 } }" in soviet_technical_compact, "legacy Soviet compact can start inside a formal alliance")
    require(errors, "ind_aubm_diplomatic_negotiation_pending" in action_blocks(soviet_technical_compact).get("a", ""), "legacy Soviet compact does not serialize its delayed reply")
    require(errors, "NOT = { participant = { country = IND value = 4 } }" in delhi_pact, "legacy Delhi Pact can replace a formal alliance")
    require(errors, all("NOT = { participant = { country = IND value = 4 } }" in action_blocks(delhi_pact).get(letter, "") for letter in ("a", "b", "c")), "legacy Delhi Pact actions do not revalidate alliance exclusivity")

    tokyo_soviet_war = action_blocks(all_events.get(9281180, "")).get("a", "")
    checks += 2
    require(errors, "type = war which = SOV" in tokyo_soviet_war, "Tokyo compact lost India's independent Soviet-war option")
    require(errors, "clrflag which = ind_aubm_jp_partnership" not in tokyo_soviet_war and "type = leave_alliance" not in tokyo_soviet_war, "independent Soviet war ruptures the Tokyo compact")

    checks += 1
    require(
        errors,
        "which = 9282355" not in all_event_text and 9282355 not in all_events,
        "obsolete partner-rupture callback can still override a valid strategic compact",
    )
    route_roots = {
        9281200: "ind_aubm_route_allied",
        9281300: "ind_aubm_route_german",
        9281400: "ind_aubm_route_soviet",
        9281500: "ind_aubm_route_sovereign",
    }
    for event_id, route in route_roots.items():
        checks += 1
        require(errors, route in all_events.get(event_id, ""), f"legacy route root {event_id} lacks {route} guard")

    executor = events.get(9281925, "")
    declared = list(MAJOR_TARGETS) + list(REGIONAL_CAPITALS)
    for tag in declared:
        suffix = tag.lower()
        checks += 2
        require(errors, f"ind_aubm_declare_{suffix}" in executor, f"declaration executor omits {tag} flag")
        require(errors, contains_war_command(executor, tag), f"declaration executor cannot start war with {tag}")
    for tag in REGIONAL_CAPITALS:
        checks += 1
        target_guard = f"NOT = {{ alliance = {{ country = IND country = {tag} }} }}"
        require(errors, target_guard in all_event_text, f"war docket does not hide allied regional target {tag}")
    for event_id, partner in ((9281921, "GER"), (9281922, "SOV"), (9281923, "JAP")):
        checks += 2
        block = events.get(event_id, "")
        require(errors, "type = leave_alliance" not in block, f"war confirmation {event_id} still performs a wartime side switch")
        require(errors, f"NOT = {{ alliance = {{ country = IND country = {partner} }} }}" in block, f"war confirmation {event_id} does not block current ally {partner}")
    for event_id, partner in ((9281920, "ENG"), (9281924, "USA")):
        checks += 2
        block = events.get(event_id, "")
        require(errors, "type = leave_alliance" not in block, f"war confirmation {event_id} still performs an Allied side switch")
        require(errors, f"NOT = {{ alliance = {{ country = IND country = {partner} }} }}" in block, f"war confirmation {event_id} does not block Allied leader {partner}")
    require(errors, "type = trigger" not in executor, "declaration executor uses unsafe immediate trigger command")

    declaration_cleanup = {
        "Allied": (*RELATIONSHIP_FAMILIES["allied"], "ind_aubm_allied_partner_eng", "ind_aubm_allied_partner_usa"),
        "German": RELATIONSHIP_FAMILIES["german"],
        "Soviet": ("ind_v4_sov_equal_compact", "ind_v4_sov_supervised_compact"),
        "Japanese": ("ind_aubm_jp_partnership", "ind_aubm_jp_formal_alliance"),
    }
    for family, tokens in declaration_cleanup.items():
        for token in tokens:
            checks += 1
            require(
                errors,
                f"type = clrflag which = {token}" in executor,
                f"direct declaration does not terminate incompatible {family} state {token}",
            )
    checks += 4
    require(errors, "trigger = { flag = ind_aubm_declare_sov } type = clrflag which = ind_v4_sov_program_defined" in executor, "war with Moscow leaves a dead Soviet conference lock")
    require(errors, "trigger = { flag = ind_aubm_declare_sov } type = clrflag which = ind_v4_sov_autonomous_socialism" not in executor, "war with Moscow erases India's domestic socialist programme")
    require(errors, "trigger = { flag = ind_aubm_declare_sov } type = clrflag which = ind_aubm_socialist_autonomous" not in executor, "war with Moscow erases autonomous-socialist identity")
    require(errors, "ind_v4a_allied_framework_started" in executor and "ind_v4a_proposal_formal_alliance" in executor, "war with an Allied leader leaves the conference locked")

    required_major_events = {
        9282120, 9282121, 9282122, 9282123, 9282124, 9282125,
        9282130, 9282131, 9282132, 9282133, 9282134, 9282135,
        9282136, 9282137, 9282138, 9282139, 9282140, 9282141,
        9282142, 9282170, 9282180, 9282181, 9282182, 9282183,
        9282188, 9282189,
    }
    for event_id in required_major_events:
        checks += 1
        require(errors, event_id in events, f"major campaign lifecycle event {event_id} is missing")
    for event_id in range(9282130, 9282141):
        checks += 1
        require(errors, "control =" in events.get(event_id, ""), f"victory event {event_id} is not based on live control")
    early_theatre_monitors = (9281940, 9281941, 9281942, 9281943, 9281944, 9281950, 9281951, 9281952, 9281953, 9281954, 9281955, 9281983)
    for event_id in early_theatre_monitors:
        checks += 1
        require(
            errors,
            "date = { day = 0 month = january year = 1933 }" in events.get(event_id, ""),
            f"theatre monitor {event_id} sleeps through an early Indian war",
        )
    require(errors, "atwar = no" not in strip_comments(MODULE_PATHS[2].read_text(encoding="cp1252")), "local settlements wait for global peace")
    require(errors, "atwar = no" not in strip_comments(MODULE_PATHS[4].read_text(encoding="cp1252")), "great-power settlements wait for global peace")
    require(errors, "atwar = no" not in strip_comments(MODULE_PATHS[5].read_text(encoding="cp1252")), "regional settlements wait for global peace")

    recognition = events.get(9282200, "")
    checks += 1
    require(errors, "date = { day = 0 month = january year = 1933 }" in recognition, "regional recognition sleeps through early wars")
    regional_reversal = events.get(9282265, "")
    regional_recovery = events.get(9282266, "")
    southern_external_cleanup = events.get(9287612, "")
    for tag, (province, suffix) in REGIONAL_CAPITALS.items():
        pending = f"ind_aubm_regional_pending_{suffix}"
        settled = f"ind_aubm_regional_settled_{suffix}"
        victory = f"ind_aubm_regional_victory_{suffix}"
        current = f"ind_aubm_regional_current_{suffix}"
        suspended = f"ind_aubm_regional_suspended_{suffix}"
        checks += 13
        require(errors, f"province = {province}" in recognition, f"regional recognition omits {tag} capital {province}")
        require(errors, pending in recognition, f"regional recognition omits {tag} pending docket")
        require(errors, victory in recognition, f"regional recognition omits {tag} victory flag")
        require(errors, f"NOT = {{ flag = {settled} }}" in recognition, f"settled {tag} can be recognized and rewarded again")
        require(
            errors,
            recognition.find(f"type = setflag which = {pending}") < recognition.find(f"type = setflag which = {victory}"),
            f"{tag} victory is recorded before its settlement docket opens",
        )
        require(errors, f"exists = {tag}" in recognition, f"regional recognition omits live-state existence for {tag}")
        require(errors, f"owned = {{ province = {province} data = {tag} }}" in recognition, f"regional recognition ignores legal {tag} ownership")
        require(errors, f"war = {{ country = IND country = {tag} }}" in recognition, f"regional recognition ignores the live {tag} war")
        if tag in {"U05", "AST"}:
            require(errors, f"NOT = {{ exists = {tag} }}" not in recognition, f"regional recognition falsely credits an annexed {tag}")
            require(
                errors,
                current in southern_external_cleanup and pending in southern_external_cleanup and suspended in southern_external_cleanup,
                f"vanished/external-peace {tag} ledger has no target-specific suspension cleanup",
            )
        else:
            require(errors, f"NOT = {{ exists = {tag} }}" in recognition, f"regional recognition has no annexed-{tag} branch")
            require(errors, f"owned = {{ province = {province} data = IND }}" in recognition, f"annexed {tag} recognition ignores Indian ownership")
        require(errors, current in regional_reversal, f"regional reversal omits {tag}")
        require(errors, suspended in regional_recovery, f"regional recovery omits {tag}")
        require(
            errors,
            f"owned = {{ province = {province} data = {tag} }}" in regional_reversal
            and f"owned = {{ province = {province} data = {tag} }}" in regional_recovery,
            f"regional reversal/recovery ignores legal {tag} ownership",
        )

    for country, suffix, proposal_id, response_id in PROPOSALS:
        proposal = events.get(proposal_id, "")
        response = events.get(response_id, "")
        checks += 13
        require(errors, f"country = {country}" in response, f"response {response_id} uses wrong country")
        require(errors, response_odds(response) == (60, 25, 15), f"response {response_id} odds are {response_odds(response)}")
        require(errors, "type = peace" not in response, f"foreign response {response_id} executes peace outside India scope")
        require(errors, "type = setflag" not in response, f"response {response_id} leaks foreign-scoped flags")
        require(errors, "which = 9282261 where = IND" in response, f"{response_id} lacks accept callback")
        require(errors, "which = 9282262 where = IND" in response, f"{response_id} lacks counter callback")
        require(errors, "which = 9282263 where = IND" in response, f"{response_id} lacks refusal callback")
        require(errors, f"ind_aubm_regional_direct_{suffix}" in proposal, f"{proposal_id} lacks direct administration")
        require(errors, "ind_aubm_occupation_upkeep" in proposal, f"{proposal_id} direct rule has no upkeep")
        require(errors, f"ind_aubm_regional_armistice_target_{suffix}" in proposal, f"{proposal_id} does not identify its pairwise target")
        require(errors, "ind_aubm_regional_armistice_outstanding" in proposal, f"{proposal_id} does not lock its open response")
        require(errors, "ind_aubm_regional_armistice_retry_pending" in proposal, f"{proposal_id} can bypass the refusal cooldown")
        require(errors, f"ind_aubm_regional_retry_{suffix}" in events.get(9282263, ""), f"{country} refusal loses its retry file")

    bespoke_ratifier = events.get(9282291, "")
    bespoke_refusal = events.get(9282290, "")
    for country, suffix, province, proposal_id, response_id in BESPOKE_PROPOSALS:
        proposal = events.get(proposal_id, "")
        response = events.get(response_id, "")
        target = f"ind_aubm_bespoke_target_{suffix}"
        checks += 18
        require(errors, f"country = {country}" in response, f"bespoke response {response_id} uses wrong country")
        require(errors, response_odds(response) == (60, 25, 15), f"bespoke response {response_id} odds are {response_odds(response)}")
        require(errors, "type = peace" not in response, f"bespoke foreign response {response_id} executes peace")
        require(errors, "type = setflag" not in response, f"bespoke response {response_id} leaks foreign-scoped flags")
        require(errors, "which = 9282288 where = IND" in response, f"{response_id} lacks accept callback")
        require(errors, "which = 9282289 where = IND" in response, f"{response_id} lacks counter callback")
        require(errors, "which = 9282290 where = IND" in response, f"{response_id} lacks refusal callback")
        require(errors, f"owned = {{ province = {province} data = {country} }}" in proposal, f"{proposal_id} ignores legal {country} ownership")
        require(errors, f"control = {{ province = {province} data = IND }}" in proposal, f"{proposal_id} ignores Indian control")
        require(errors, target in proposal, f"{proposal_id} does not identify its pairwise target")
        require(errors, "ind_aubm_bespoke_armistice_outstanding" in proposal, f"{proposal_id} has no response lock")
        require(errors, f"ind_aubm_bespoke_retry_{suffix}" in proposal, f"{proposal_id} can bypass its refusal cooldown")
        require(errors, f"ind_aubm_bespoke_sovereign_{suffix}" in proposal, f"{proposal_id} cannot restore sovereignty")
        require(errors, f"ind_aubm_bespoke_protected_{suffix}" in proposal, f"{proposal_id} cannot establish protection")
        require(errors, f"ind_aubm_bespoke_direct_{suffix}" in proposal, f"{proposal_id} lacks direct administration")
        require(errors, "ind_aubm_occupation_upkeep" in proposal, f"{proposal_id} direct rule has no upkeep")
        require(errors, f"type = peace which = {country} value = 1" in bespoke_ratifier, f"bespoke ratifier omits {country}")
        require(errors, f"ind_aubm_bespoke_retry_{suffix}" in bespoke_refusal, f"{country} refusal loses its retry file")

    gulf_board = events.get(9282278, "")
    checks += 8
    for proposal_id in range(9282271, 9282275):
        require(errors, f"which = {proposal_id} where = IND" in gulf_board, f"Gulf board omits independent file {proposal_id}")
    require(errors, "ind_aubm_bespoke_armistice_outstanding" in events.get(9282279, ""), "bespoke negotiation lapse does not release a dead response")
    require(errors, "when = 90" in bespoke_refusal, "bespoke refusal has no ninety-day cooldown")
    require(errors, "ind_aubm_bespoke_retry_pending" in events.get(9282292, ""), "bespoke retry event does not release its cooldown")
    require(errors, "type = peace" in bespoke_ratifier and "country = IND" in bespoke_ratifier, "bespoke pairwise peace is not India-scoped")

    foreign_callbacks = []
    for event_id, block in events.items():
        country_match = re.search(r"(?m)^\s*country\s*=\s*([A-Z0-9]{3})", block)
        country = country_match.group(1) if country_match else ""
        if country and country != "IND" and re.search(r"where\s*=\s*IND", block):
            foreign_callbacks.append((event_id, block))
    for event_id, block in foreign_callbacks:
        checks += 1
        require(errors, "type = peace" not in block, f"foreign callback event {event_id} executes peace")

    for protocol_id in (9282059, 9282160, 9282260, 9282291):
        block = events.get(protocol_id, "")
        checks += 3
        require(errors, "country = IND" in block, f"peace protocol {protocol_id} is not India-scoped")
        require(errors, "type = peace" in block, f"peace protocol {protocol_id} executes no pairwise peace")
        require(errors, "armistice_outstanding" in block, f"peace protocol {protocol_id} does not close its response lock")

    for event_id, block in events.items():
        country_match = re.search(r"(?m)^\s*country\s*=\s*([A-Z0-9]{3})", block)
        country = country_match.group(1) if country_match else ""
        if country and country != "IND":
            checks += 1
            require(errors, "type = peace" not in block, f"foreign event {event_id} executes an unsafe peace command")

    callback_contracts = {
        9282037: (9282040, 9282044, 9282045),
        9282038: (9282043, 9282044, 9282045),
        9282039: (9282044, 9282044, 9282045),
        9282171: (9282143, 9282144, 9282145),
        9282172: (9282143, 9282144, 9282145),
        9282173: (9282143, 9282144, 9282145),
        9282174: (9282143, 9282144, 9282145),
        9282175: (9282143, 9282144, 9282145),
        9282184: (9282146, 9282150, 9282151),
        9282185: (9282147, 9282150, 9282151),
        9282186: (9282148, 9282150, 9282151),
        9282187: (9282149, 9282150, 9282151),
    }
    for source_id, target_ids in callback_contracts.items():
        block = events.get(source_id, "")
        actual = tuple(
            int(value)
            for value in re.findall(r"type\s*=\s*event\s+which\s*=\s*(\d+)\s+where\s*=\s*IND", block)
        )
        checks += 1
        require(errors, actual == target_ids, f"{source_id} callback contract is {actual}, expected {target_ids}")

    soviet_docket_actions = action_blocks(events.get(9282036, ""))
    for letter in ("a", "b"):
        action = soviet_docket_actions.get(letter, "")
        checks += 3
        require(errors, "owned = {" in action and "data = SOV" in action, f"Soviet territorial offer {letter} ignores Soviet ownership")
        require(errors, "control = {" in action and "data = IND" in action, f"Soviet territorial offer {letter} ignores Indian control")
        require(errors, "ind_aubm_local_armistice_outstanding" in action, f"Soviet territorial offer {letter} does not lock its response")

    for response_id in (9282037, 9282038):
        response = events.get(response_id, "")
        checks += 3
        require(errors, "type = secedeprovince" not in response, f"Soviet response {response_id} still mutates ownership sequentially")
        require(errors, "event which = 9282046 where = SOV when = 1" in response, f"Soviet response {response_id} does not call the transfer snapshot")
        require(errors, "when = 3" in response, f"Soviet response {response_id} callback can race the transfer helper")

    transfer_helper = events.get(9282046, "")
    transfer_lines = [line for line in transfer_helper.splitlines() if "type = secedeprovince which = IND" in line]
    checks += 9 + len(transfer_lines)
    require(errors, "country = SOV" in transfer_helper, "Central Asian transfer helper is not Soviet-scoped")
    require(errors, len(transfer_lines) == 17, f"Central Asian helper transfers {len(transfer_lines)} provinces instead of 17")
    for snapshot in ("trk", "uzb", "taj", "kyg", "kaz"):
        require(errors, f"setflag which = sov_aubm_transfer_{snapshot}" in transfer_helper, f"Central Asian helper omits {snapshot.upper()} snapshot")
    first_transfer = transfer_helper.find("type = secedeprovince")
    last_snapshot = max(transfer_helper.find(f"setflag which = sov_aubm_transfer_{snapshot}") for snapshot in ("trk", "uzb", "taj", "kyg", "kaz"))
    require(errors, 0 <= last_snapshot < first_transfer, "Central Asian helper begins transfer before all republics are snapshotted")
    require(errors, all("flag = sov_aubm_transfer_" in line for line in transfer_lines), "Central Asian helper rechecks mutable ownership during transfer")

    for callback_id in (9282040, 9282043):
        callback_actions = action_blocks(events.get(callback_id, ""))
        accepted = callback_actions.get("a", "")
        failed = callback_actions.get("b", "")
        checks += 6
        require(errors, "owned = {" in accepted and "data = IND" in accepted, f"Central Asian callback {callback_id} does not verify transferred ownership")
        require(errors, "event which = 9282059" in accepted, f"Central Asian callback {callback_id} cannot ratify a valid peace")
        require(errors, "type = peace" not in failed, f"Central Asian callback {callback_id} grants peace after a failed transfer")
        require(errors, "ind_aubm_local_armistice_retry_sov" in failed, f"Central Asian callback {callback_id} does not preserve the Soviet retry")
        require(errors, "ind_aubm_local_armistice_retry_pending" in failed, f"Central Asian callback {callback_id} does not apply retry cooldown")
        require(errors, "type = clrflag which = ind_aubm_local_armistice_outstanding" in failed, f"Central Asian callback {callback_id} leaves a dead response lock")

    for event_id in range(9282080, 9282095):
        checks += 1
        require(errors, event_id in events, f"wartime economy or mobilisation event {event_id} is missing")
        require(errors, "persistent = yes" in events.get(event_id, ""), f"reusable economy event {event_id} is not persistent")
    checks += 15
    require(errors, "ind_aubm_budget_review_pending" in events.get(9282080, ""), "wartime budget does not guard its annual cycle")
    require(errors, "ind_aubm_budget_review_pending" in events.get(9282081, ""), "annual budget review does not reset its cycle")
    require(errors, "ind_aubm_debt_tier_4" in events.get(9282082, ""), "debt settlement omits cumulative high debt")
    require(errors, "ind_aubm_debt_amortize" in events.get(9282091, ""), "debt service lacks one-tier amortisation markers")
    require(errors, "ind_aubm_occupation_tier_4" in events.get(9282085, ""), "occupation upkeep does not scale to tier four")
    occupation_upkeep = events.get(9282085, "")
    require(errors, "date = { day = 0 month = january year = 1933 }" in occupation_upkeep, "occupation upkeep does not begin with the scenario")
    upkeep_actions = action_blocks(occupation_upkeep)
    civilianize = upkeep_actions.get("c", "")
    require(errors, all(flag in civilianize for flag in ("ind_aubm_occupation_overhang", "ind_aubm_occupation_tier_4", "ind_aubm_occupation_tier_3", "ind_aubm_occupation_tier_2")), "civilianization does not cover every reducible occupation tier")
    require(errors, "flag = ind_aubm_occupation_tier_1" not in civilianize, "civilianization is selectable for an irreducible lone tier one mandate")
    require(errors, "ind_aubm_mobilisation_delay_cooldown" in events.get(9282086, ""), "mobilisation delay has no cooldown")
    require(errors, "ind_aubm_wartime_establishment_retained" in events.get(9282088, ""), "demobilisation omits retained readiness")
    require(errors, "ind_aubm_occupation_tier_1" in events.get(9282093, ""), "occupation register does not create its first tier")
    occupation_devolution = events.get(9282094, "")
    require(errors, "ind_aubm_occupation_overhang" in occupation_devolution, "occupation devolution does not clear overhang first")
    require(errors, "ind_aubm_occupation_tier_4" in occupation_devolution and "ind_aubm_occupation_tier_2" in occupation_devolution, "occupation devolution does not cover every reducible tier")
    require(errors, "type = clrflag which = ind_aubm_occupation_tier_1" not in occupation_devolution, "civilianization illegally removes the irreducible tier-one mandate")
    require(errors, "type = clrflag which = ind_aubm_occupation_upkeep" not in occupation_devolution, "civilianization illegally ends recurring upkeep while direct rule remains")
    require(errors, "without releasing territory or changing a government's constitutional status" in occupation_devolution, "civilianization description does not preserve sovereignty state")

    reusable_ids = {
        *range(9281930, 9281934),
        *range(9281950, 9281956),
        *range(9281980, 9281983),
        *range(9282000, 9282009), *range(9282020, 9282047),
        *range(9282050, 9282055), 9282059,
        *range(9282080, 9282095),
        *range(9282120, 9282126), *range(9282130, 9282136),
        *range(9282137, 9282152), *range(9282160, 9282167), 9282169,
        *range(9282170, 9282176), *range(9282180, 9282190),
        *range(9282200, 9282206), *range(9282210, 9282230),
        *range(9282260, 9282267),
        *range(9282270, 9282293),
    }
    for event_id in reusable_ids:
        checks += 1
        require(errors, "persistent = yes" in events.get(event_id, ""), f"reusable wartime event {event_id} is not persistent")

    japan_text = (EVENT_ROOT / "aubm_v4/35_japan_partnership.txt").read_text(encoding="cp1252")
    japan_settlement = parse_events((EVENT_ROOT / "aubm_v4/35_japan_partnership.txt",)).get(9281160, "")
    checks += 3
    require(errors, "ind_aubm_occupation_upkeep" in japan_settlement, "Japan-route direct mandates have no occupation upkeep")
    require(errors, "which = 9282093 where = IND" in japan_settlement, "Japan-route direct mandates bypass the occupation register")
    require(errors, "ind_aubm_jp_settlement_direct" in japan_text, "Japan settlement doctrine is absent")
    require(errors, "U05" in "\n".join(path.read_text(encoding="cp1252") for path in MODULE_PATHS), "East Indies legal owner U05 is absent")

    if errors:
        print(f"AUBM wartime validation failed ({len(errors)} errors, {checks} checks):")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print(f"AUBM wartime validation passed ({checks} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
