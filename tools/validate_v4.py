#!/usr/bin/env python3
"""Static production gate for A Union Before Midnight V4.

Darkest Hour accepts some malformed data at scenario load and fails only when a
dated command executes. This validator therefore checks both parser structure
and the delayed hazards that have caused real playthrough crashes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from fnmatch import fnmatchcase


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools" / "v4_config.json"
INDIA_EVENT_DIRS = (
    pathlib.Path("db/events/india_v3"),
    pathlib.Path("db/events/aubm_v4"),
)
REQUIRED_V4_MODULES = {
    "00_world_bootstrap.txt",
    "05_union_integration.txt",
    "10_world_reactions.txt",
    "12_campaign_systems.txt",
    "15_operational_command.txt",
    "18_manpower_reserves.txt",
    "20_procurement.txt",
    "22_crisis_interventions.txt",
    "25_global_war.txt",
    "26_grand_strategy.txt",
    "27_dynamic_strategy.txt",
    "28_foreign_responses.txt",
    "29_world_pressure.txt",
    "30_war_settlements.txt",
    "31_campaign_continuity.txt",
    "32_national_consolidation.txt",
    "35_japan_partnership.txt",
    "36_allied_campaigns.txt",
    "37_german_campaigns.txt",
    "38_soviet_campaigns.txt",
    "39_non_aligned_campaigns.txt",
    "40_special_units_and_capital_ships.txt",
    "41_wartime_state.txt",
    "42_wartime_theatres.txt",
    "43_wartime_settlements.txt",
    "44_wartime_economy.txt",
    "45_enemy_campaigns.txt",
    "46_regional_campaigns.txt",
    "47_global_campaign_matrix.txt",
	"48_route_wartime_consequences.txt",
	"49_bespoke_armistices.txt",
}
KNOWN_COMMANDS = {
    "access",
    "activate_unit_type",
    "add_brigade",
    "add_corps",
    "add_division",
    "add_leader_skill",
    "add_prov_resource",
    "addclaim",
    "addcore",
    "ai",
    "alliance",
    "armamentminister",
    "belligerence",
    "build_division",
	"build_cost",
	"build_time",
    "chiefofair",
    "chiefofarmy",
    "chiefofnavy",
    "chiefofstaff",
    "clrflag",
    "construct",
    "control",
    "dissent",
    "desert_attack",
    "desert_defense",
    "desert_move",
    "domestic",
    "embargo",
    "end_mastery",
    "end_trades",
    "event",
    "foreignminister",
    "forest_attack",
    "forest_defense",
    "forest_move",
    "free_money",
    "gain_tech",
    "guarantee",
    "headofgovernment",
    "headofstate",
    "hq_supply_eff",
    "hill_attack",
    "hill_defense",
    "hill_move",
    "industrial_modifier",
    "inherit",
    "intelligence",
    "jungle_attack",
    "jungle_defense",
    "jungle_move",
    "independence",
    "leave_alliance",
    "manpowerpool",
    "max_organization",
    "mountain_attack",
    "mountain_defense",
    "mountain_move",
    "make_puppet",
    "ministerofintelligence",
    "ministerofsecurity",
    "money",
    "morale",
    "new_model",
    "night_attack",
    "night_defense",
    "night_move",
    "non_aggression",
    "oilpool",
    "paradrop_attack",
    "peace",
    "province_revoltrisk",
    "rarematerialspool",
    "relation",
    "repair_mod",
    "research_mod",
    "secedearea",
    "secedeprovince",
    "secederegion",
    "set_leader_skill",
    "setflag",
    "shore_attack",
    "shore_defense",
    "shore_move",
    "sleepevent",
    "sleepleader",
    "sleepminister",
    "steal_tech",
    "snow_attack",
    "snow_defense",
    "snow_move",
    "swamp_attack",
    "swamp_defense",
    "swamp_move",
    "supplies",
    "tc_mod",
    "trigger",
    "urban_attack",
    "urban_defense",
    "urban_move",
    "river_attack",
    "river_defense",
    "river_move",
    "wakeleader",
    "waketeam",
    "war",
}
CONSTRUCTION_TYPES = {
    "air_base",
    "coastal_fort",
    "flak",
    "ic",
    "infrastructure",
    "land_fort",
    "naval_base",
    "nuclear_reactor",
    "radar_station",
    "rocket_test",
}
BASE_CAPS = {
    "air_base": 10,
    "naval_base": 10,
    "radar_station": 10,
    "flak": 10,
    "land_fort": 10,
    "coastal_fort": 10,
    "infrastructure": 100,
}
EVENT_DESC_LIMIT = 500
ACTION_NAME_LIMIT = 58
INDIA_FLAG_PATTERN = r"ind_(?:v\d+|aubm)_[a-z0-9_]+"


@dataclass
class Issue:
    severity: str
    path: pathlib.Path
    line: int
    message: str


@dataclass
class Block:
    text: str
    line: int


def load_text(path: pathlib.Path) -> str:
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError("contains NUL bytes")
    return data.decode("cp1252")


def strip_comments(text: str) -> str:
    output: list[str] = []
    in_quote = False
    i = 0
    while i < len(text):
        char = text[i]
        if char == '"':
            in_quote = not in_quote
            output.append(char)
            i += 1
            continue
        if char == "#" and not in_quote:
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        output.append(char)
        i += 1
    return "".join(output)


def extract_blocks(text: str, key: str) -> list[Block]:
    clean = strip_comments(text)
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{", re.I)
    blocks: list[Block] = []
    cursor = 0
    while True:
        match = pattern.search(clean, cursor)
        if not match:
            break
        opening = clean.find("{", match.start())
        depth = 0
        in_quote = False
        end = None
        for index in range(opening, len(clean)):
            char = clean[index]
            if char == '"':
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
        if end is None:
            break
        blocks.append(Block(clean[match.start() : end], clean.count("\n", 0, match.start()) + 1))
        cursor = end
    return blocks


def scalar(text: str, key: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*(\"[^\"]*\"|[^\s\}}]+)", text, re.I)
    if not match:
        return None
    return match.group(1).strip('"')


def integers(text: str) -> set[int]:
    return {int(value) for value in re.findall(r"\b\d+\b", strip_comments(text))}


class Validator:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.mod = root / "mod"
        self.issues: list[Issue] = []
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.game = pathlib.Path(self.config["game_root"])
        self.stock = pathlib.Path(self.config["baseline_mod"])
        self.event_min = int(self.config["event_id_min"])
        self.event_max = int(self.config["event_id_max"])
        self.india_events: dict[int, tuple[pathlib.Path, Block]] = {}
        self.initial_owned: set[int] = set()
        self.province_ids: set[int] = set()
        self.area_names: set[str] = set()
        self.region_names: set[str] = set()
        self.leader_ids: set[int] = set()
        self.minister_ids: set[int] = set()
        self.team_ids: set[int] = set()
        self.division_types: set[str] = set()
        self.brigade_types: set[str] = set()
        self.division_model_counts: dict[str, int] = {}
        self.brigade_model_counts: dict[str, int] = {}
        self.division_allowed_brigades: dict[str, set[str]] = {}

    def issue(self, severity: str, path: pathlib.Path, line: int, message: str) -> None:
        self.issues.append(Issue(severity, path, line, message))

    def error(self, path: pathlib.Path, line: int, message: str) -> None:
        self.issue("ERROR", path, line, message)

    def warn(self, path: pathlib.Path, line: int, message: str) -> None:
        self.issue("WARN", path, line, message)

    def validate_file_structure(self, path: pathlib.Path) -> str:
        try:
            text = load_text(path)
        except (OSError, UnicodeError, ValueError) as exc:
            self.error(path, 1, f"Cannot read cp1252 text: {exc}")
            return ""
        clean = strip_comments(text)
        depth = 0
        in_quote = False
        for index, char in enumerate(clean):
            if char == '"':
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth < 0:
                        self.error(path, clean.count("\n", 0, index) + 1, "Unexpected closing brace.")
                        depth = 0
        if in_quote:
            self.error(path, text.count("\n") + 1, "Unterminated quoted string.")
        if depth:
            self.error(path, text.count("\n") + 1, f"Unbalanced braces: depth {depth}.")
        return text

    def load_provinces(self) -> None:
        candidates = (
            self.mod / "map/Map_1/Province.csv",
            self.game / "map/Map_1/Province.csv",
        )
        province_path = next((path for path in candidates if path.exists()), None)
        if not province_path:
            self.error(self.mod, 1, "No Province.csv is available.")
            return
        with province_path.open(encoding="cp1252", newline="") as stream:
            reader = csv.reader(stream, delimiter=";")
            next(reader, None)
            for row in reader:
                if row and row[0].isdigit():
                    self.province_ids.add(int(row[0]))
                    if len(row) > 2 and row[2] not in {"", "-"}:
                        self.area_names.add(row[2])
                    if len(row) > 3 and row[3] not in {"", "-"}:
                        self.region_names.add(row[3])

    def load_personnel(self) -> None:
        sources = (
            (self.mod / "db/leaders/india.csv", 1, self.leader_ids, "leader"),
            (self.mod / "db/ministers/ministers_ind.csv", 0, self.minister_ids, "minister"),
            (self.mod / "db/tech/teams/teams_ind.csv", 0, self.team_ids, "technology team"),
        )
        for path, id_column, target, label in sources:
            if not path.is_file():
                self.error(path, 1, f"India {label} file is missing.")
                continue
            with path.open(encoding="cp1252", newline="") as stream:
                for line_number, row in enumerate(csv.reader(stream, delimiter=";"), 1):
                    if len(row) <= id_column or not row[id_column].isdigit():
                        continue
                    identifier = int(row[id_column])
                    if identifier in target:
                        self.error(path, line_number, f"Duplicate {label} ID {identifier}.")
                    target.add(identifier)
                    if label == "leader" and len(row) > 14 and row[14].startswith("INDL"):
                        self.validate_india_leader_portrait(path, line_number, row[14])

        leader_path = self.mod / "db/leaders/india.csv"
        active_land: dict[int, int] = {1938: 0, 1940: 0}
        active_commandos: dict[int, int] = {1938: 0, 1940: 0}
        if leader_path.is_file():
            with leader_path.open(encoding="cp1252", newline="") as stream:
                for row in csv.reader(stream, delimiter=";"):
                    if len(row) <= 16 or not row[1].isdigit() or not row[13].isdigit():
                        continue
                    if int(row[13]) != 0:
                        continue
                    try:
                        traits = int(row[9])
                        start = int(row[15])
                        end = int(row[16])
                    except ValueError:
                        continue
                    for year in active_land:
                        if start <= year <= end:
                            active_land[year] += 1
                            if traits & 256:
                                active_commandos[year] += 1

        if active_land[1938] < 80:
            self.error(
                leader_path,
                1,
                f"India has only {active_land[1938]} active land leaders in 1938; minimum is 80.",
            )
        if active_land[1940] < 90:
            self.error(
                leader_path,
                1,
                f"India has only {active_land[1940]} active land leaders in 1940; minimum is 90.",
            )
        if active_commandos[1938] < 8:
            self.error(
                leader_path,
                1,
                f"India has only {active_commandos[1938]} commando-qualified leaders in 1938; minimum is 8.",
            )

    def validate_india_leader_portrait(
        self,
        roster_path: pathlib.Path,
        line_number: int,
        picture: str,
    ) -> None:
        portrait = self.mod / "gfx/interface/pics" / f"{picture}.bmp"
        if not portrait.is_file():
            self.error(roster_path, line_number, f"Missing custom leader portrait {picture}.bmp.")
            return
        data = portrait.read_bytes()
        if len(data) < 30 or data[:2] != b"BM":
            self.error(portrait, 1, "Leader portrait is not a valid BMP file.")
            return
        width, height = struct.unpack_from("<ii", data, 18)
        bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
        if (width, abs(height)) != (36, 50):
            self.error(portrait, 1, f"Leader portrait must be 36x50, found {width}x{abs(height)}.")
        if bits_per_pixel != 8:
            self.error(portrait, 1, f"Leader portrait must be 8-bit indexed, found {bits_per_pixel}-bit.")

    def effective_path(self, relative: pathlib.Path) -> pathlib.Path:
        overlay = self.mod / relative
        return overlay if overlay.is_file() else self.stock / relative

    def load_unit_definitions(self) -> None:
        categories = (
            (
                "division",
                pathlib.Path("db/units/division_types.txt"),
                pathlib.Path("db/units/divisions"),
                self.division_types,
                self.division_model_counts,
            ),
            (
                "brigade",
                pathlib.Path("db/units/brigade_types.txt"),
                pathlib.Path("db/units/brigades"),
                self.brigade_types,
                self.brigade_model_counts,
            ),
        )
        for label, registry_relative, definitions_relative, active, model_counts in categories:
            registry_path = self.effective_path(registry_relative)
            registry_text = self.validate_file_structure(registry_path)
            if not registry_text:
                continue

            names: set[str] = set()
            for root in (self.stock / definitions_relative, self.mod / definitions_relative):
                if root.is_dir():
                    names.update(path.stem for path in root.glob("*.txt"))

            for name in sorted(names):
                blocks = extract_blocks(registry_text, name)
                if len(blocks) > 1:
                    self.error(
                        registry_path,
                        blocks[1].line,
                        f"Duplicate {label} type definition for {name}.",
                    )
                if not blocks or scalar(blocks[0].text, "type") is None:
                    continue

                definition_relative = definitions_relative / f"{name}.txt"
                definition_path = self.effective_path(definition_relative)
                if not definition_path.is_file():
                    self.error(
                        definition_path,
                        1,
                        f"Active {label} type {name} has no model definition file.",
                    )
                    continue
                definition_text = self.validate_file_structure(definition_path)
                model_count = len(extract_blocks(definition_text, "model"))
                if model_count == 0:
                    self.error(
                        definition_path,
                        1,
                        f"Active {label} type {name} has no models.",
                    )
                    continue
                active.add(name)
                model_counts[name] = model_count
                if label == "division":
                    self.division_allowed_brigades[name] = set(
                        re.findall(
                            r"(?mi)^\s*allowed_brigades\s*=\s*([A-Za-z0-9_]+)",
                            definition_text,
                        )
                    )

    def validate_scenario(self) -> None:
        scenario = self.mod / "scenarios/1933.eug"
        text = self.validate_file_structure(scenario)
        if not text:
            return
        if not re.search(r"selectable\s*=\s*\{\s*IND\s*\}", text, re.I):
            self.error(scenario, 1, "1933 scenario must expose India as the only selectable country.")
        if not re.search(
            r"startdate\s*=\s*\{\s*year\s*=\s*1933\s+month\s*=\s*january\s+day\s*=\s*0\s*\}",
            text,
            re.I,
        ):
            self.error(scenario, 1, "Scenario must begin on 1 January 1933.")
        if re.search(r"Blood and Iron|B&I|india_overhaul", text, re.I):
            self.error(scenario, 1, "Direct-DH scenario contains a donor-mod reference.")

        india = self.mod / "scenarios/1933/british raj.inc"
        india_text = self.validate_file_structure(india)
        owned = extract_blocks(india_text, "ownedprovinces")
        if not owned:
            self.error(india, 1, "India has no ownedprovinces block.")
        else:
            self.initial_owned = integers(owned[0].text)
        for required in (1509, 1510, 1511):
            if required not in self.initial_owned:
                self.error(india, 1, f"Ceylon province {required} is not owned by India.")
        if 1513 in self.initial_owned:
            self.error(india, 1, "Goa must remain Portuguese at the 1933 start.")

        formation_sizes: list[tuple[str, int, int]] = []
        unit_ids: Counter[tuple[int, int]] = Counter()
        for formation in extract_blocks(india_text, "landunit"):
            name = scalar(formation.text, "name") or "unnamed formation"
            divisions = len(extract_blocks(formation.text, "Division"))
            formation_sizes.append((name, divisions, formation.line))
            for kind, value in re.findall(r"id\s*=\s*\{\s*type\s*=\s*(\d+)\s+id\s*=\s*(\d+)", formation.text):
                unit_ids[(int(kind), int(value))] += 1
        for name, size, line in formation_sizes:
            if re.match(r"[IVX]+ .*(Corps|Mobile Group)$", name) and size != 3:
                self.error(india, line, f"{name} contains {size} units; operational corps must contain three.")
        marker = "# V4 operational organization: three-unit corps reduce map micro."
        if india_text.count(marker) != 1:
            self.error(india, 1, "V4 operational-organization marker must appear exactly once.")
        for unit_id, count in unit_ids.items():
            if count > 1:
                self.error(india, 1, f"Duplicate scenario unit id {unit_id}, seen {count} times.")
        for match in re.finditer(r"\bleader\s*=\s*(\d+)", india_text):
            identifier = int(match.group(1))
            if identifier not in self.leader_ids:
                line = india_text.count("\n", 0, match.start()) + 1
                self.error(india, line, f"Scenario assigns unknown India leader {identifier}.")
        for role in (
            "headofstate",
            "headofgovernment",
            "foreignminister",
            "armamentminister",
            "ministerofsecurity",
            "ministerofintelligence",
            "chiefofstaff",
            "chiefofarmy",
            "chiefofnavy",
            "chiefofair",
        ):
            match = re.search(rf"\b{role}\s*=\s*\{{[^}}]*\bid\s*=\s*(\d+)", india_text)
            if match and int(match.group(1)) not in self.minister_ids:
                line = india_text.count("\n", 0, match.start()) + 1
                self.error(india, line, f"Scenario assigns unknown India minister {match.group(1)}.")
        dormant = extract_blocks(india_text, "dormant_teams")
        if dormant:
            for identifier in integers(dormant[0].text):
                if identifier not in self.team_ids:
                    self.error(
                        india,
                        dormant[0].line,
                        f"Scenario marks unknown India technology team {identifier} dormant.",
                    )

        uk = self.mod / "scenarios/1933/united kingdom.inc"
        uk_text = self.validate_file_structure(uk)
        uk_owned = extract_blocks(uk_text, "ownedprovinces")
        if uk_owned:
            overlap = {1509, 1510, 1511} & integers(uk_owned[0].text)
            if overlap:
                self.error(uk, uk_owned[0].line, f"UK still owns Ceylon provinces {sorted(overlap)}.")

    def included_event_files(self) -> list[pathlib.Path]:
        index = self.mod / "db/events.txt"
        text = self.validate_file_structure(index)
        paths: list[pathlib.Path] = []
        for relative in re.findall(r'event\s*=\s*"([^"]+)"', text, re.I):
            path = self.mod / pathlib.PureWindowsPath(relative)
            if not path.exists():
                stock_path = self.stock / pathlib.PureWindowsPath(relative)
                if not stock_path.exists():
                    self.error(index, 1, f'Event include is missing from overlay and stock: "{relative}".')
                    continue
                path = stock_path
            paths.append(path)
        return paths

    def resolve_picture(self, picture: str) -> bool:
        filename = f"{picture}.bmp"
        return any(
            path.exists()
            for path in (
                self.mod / "gfx/events_pics" / filename,
                self.stock / "gfx/events_pics" / filename,
                self.game / "gfx/events_pics" / filename,
            )
        )

    def validate_event_file(self, path: pathlib.Path) -> None:
        text = self.validate_file_structure(path)
        clean = strip_comments(text)
        # Darkest Hour event triggers do not support Clausewitz-style country
        # scopes. Ordinary `flag` values are global; country-specific state
        # must use `local_flag` in an event running for that country.
        country_scope = re.compile(
            r"\b(?!(?:AND|NOT|TAG)\b)[A-Z0-9]{3}\s*=\s*\{"
        )
        for match in country_scope.finditer(clean):
            self.error(
                path,
                clean.count("\n", 0, match.start()) + 1,
                "Unsupported country-tag scope in an event trigger.",
            )
        events = extract_blocks(text, "event")
        if not events:
            self.error(path, 1, "Loaded India event module contains no events.")
            return
        for event in events:
            event_id_text = scalar(event.text, "id")
            if not event_id_text or not event_id_text.isdigit():
                self.error(path, event.line, "Event has no numeric id.")
                continue
            event_id = int(event_id_text)
            if not self.event_min <= event_id <= self.event_max:
                self.error(path, event.line, f"Event id {event_id} is outside the reserved India range.")
            if event_id in self.india_events:
                other = self.india_events[event_id][0]
                self.error(path, event.line, f"Duplicate India event id {event_id}, also in {other.name}.")
            self.india_events[event_id] = (path, event)

            country = scalar(event.text, "country")
            if not country or not re.fullmatch(r"[A-Z0-9]{3}", country):
                self.error(path, event.line, f"Event {event_id} has an invalid country tag.")
            dates = extract_blocks(event.text, "date")
            deathdates = extract_blocks(event.text, "deathdate")
            if country == "IND" and dates:
                if not deathdates:
                    self.error(path, event.line, f"Dated India event {event_id} has no scenario-long deathdate.")
                elif scalar(deathdates[0].text, "year") != "1964":
                    self.error(
                        path,
                        event.line,
                        f"Dated India event {event_id} can expire before the campaign ends.",
                    )
            if not scalar(event.text, "name"):
                self.error(path, event.line, f"Event {event_id} has no name.")
            description = scalar(event.text, "desc")
            if description and len(description.encode("cp1252")) > EVENT_DESC_LIMIT:
                self.error(
                    path,
                    event.line,
                    f"Event {event_id} description exceeds the {EVENT_DESC_LIMIT}-byte UI limit.",
                )
            if not extract_blocks(event.text, "action_a"):
                self.error(path, event.line, f"Event {event_id} has no action_a.")

            actions: list[Block] = []
            for letter in "abcdefgh":
                actions.extend(extract_blocks(event.text, f"action_{letter}"))
            chances = [scalar(action.text, "ai_chance") for action in actions]
            if len(actions) > 1 and any(chance is not None for chance in chances):
                if any(chance is None for chance in chances):
                    self.error(path, event.line, f"Event {event_id} mixes explicit and implicit ai_chance.")
                elif sum(int(chance) for chance in chances if chance) != 100:
                    self.error(path, event.line, f"Event {event_id} ai_chance does not sum to 100.")
            names = [scalar(action.text, "name") for action in actions]
            if len([name for name in names if name]) != len(set(name for name in names if name)):
                self.error(path, event.line, f"Event {event_id} has duplicate action names.")
            for action, action_name in zip(actions, names):
                if action_name and len(action_name.encode("cp1252")) > ACTION_NAME_LIMIT:
                    self.error(
                        path,
                        event.line + action.line - 1,
                        f"Event {event_id} action label exceeds the {ACTION_NAME_LIMIT}-byte UI limit.",
                    )

            picture = scalar(event.text, "picture")
            if picture and not self.resolve_picture(picture):
                self.error(path, event.line, f'Event {event_id} picture "{picture}" cannot be resolved.')
            decision_picture = scalar(event.text, "decision_picture")
            if decision_picture and not self.resolve_picture(decision_picture):
                self.error(
                    path,
                    event.line,
                    f'Event {event_id} decision picture "{decision_picture}" cannot be resolved.',
                )

            self.validate_commands(path, event, event_id, country)

    def validate_commands(
        self,
        path: pathlib.Path,
        event: Block,
        event_id: int,
        country: str | None,
    ) -> None:
        lines = event.text.splitlines()
        for offset, line in enumerate(lines):
            command = re.search(r"\bcommand\s*=\s*\{.*?\btype\s*=\s*([A-Za-z0-9_]+)", line)
            if not command:
                continue
            command_type = command.group(1)
            line_number = event.line + offset
            if command_type not in KNOWN_COMMANDS:
                self.error(path, line_number, f"Event {event_id} uses unknown command {command_type}.")

            for province_text in re.findall(r"\bprovince\s*=\s*(-?\d+)", line):
                province = int(province_text)
                if province >= 0 and province not in self.province_ids:
                    self.error(path, line_number, f"Event {event_id} references unknown province {province}.")

            if command_type == "construct":
                target = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+).*?\bwhere\s*=\s*(-?\d+)", line)
                value_match = re.search(r"\bvalue\s*=\s*(-?\d+(?:\.\d+)?)", line)
                if not target:
                    self.error(path, line_number, f"Event {event_id} has malformed construct command.")
                    continue
                building, province_text = target.groups()
                province = int(province_text)
                value = float(value_match.group(1)) if value_match else 0
                if building not in CONSTRUCTION_TYPES:
                    self.error(path, line_number, f"Unknown construction type {building}.")
                if province > 0 and province not in self.province_ids:
                    self.error(path, line_number, f"Construction targets unknown province {province}.")
                if province > 0 and "owned = {" not in line:
                    self.error(
                        path,
                        line_number,
                        f"Construction in province {province} lacks an ownership guard.",
                    )
                if building in BASE_CAPS and value > BASE_CAPS[building]:
                    self.error(path, line_number, f"{building} construction value {value:g} exceeds engine cap.")
                if province > 0 and building in BASE_CAPS and "building = {" not in line:
                    self.error(
                        path,
                        line_number,
                        f"Uncapped {building} construction in province {province}.",
                    )
                if province > 0 and building in BASE_CAPS and value > 0:
                    guard = re.search(r"\bbuilding\s*=\s*\{([^}]*)\}", line)
                    if guard:
                        guard_type = scalar(guard.group(1), "type")
                        guard_province = scalar(guard.group(1), "province")
                        guard_value = scalar(guard.group(1), "value")
                        if guard_type != building or guard_province != str(province) or not guard_value:
                            self.error(
                                path,
                                line_number,
                                f"{building} cap guard does not match province {province}.",
                            )
                        else:
                            highest_existing = float(guard_value) - 1
                            if highest_existing + value > BASE_CAPS[building]:
                                self.error(
                                    path,
                                    line_number,
                                    f"{building} in province {province} can reach "
                                    f"{highest_existing + value:g}, above cap {BASE_CAPS[building]}.",
                                )

            if command_type == "secedeprovince":
                if country == "IND" and re.search(r"\bwhich\s*=\s*IND\b", line):
                    self.error(path, line_number, "India must not secede a province to itself.")
                target = re.search(r"\bvalue\s*=\s*(-?\d+)", line)
                if not target:
                    self.error(path, line_number, f"Event {event_id} has malformed province transfer.")
                elif int(target.group(1)) >= 0 and int(target.group(1)) not in self.province_ids:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} transfers unknown province {target.group(1)}.",
                    )

            if command_type in {"secedearea", "secederegion"}:
                target = re.search(r'\bvalue\s*=\s*(?:"([^"]+)"|([A-Za-z0-9_.-]+))', line)
                if not target:
                    self.error(path, line_number, f"Event {event_id} has malformed {command_type} command.")
                else:
                    name = target.group(1) or target.group(2)
                    known = self.area_names if command_type == "secedearea" else self.region_names
                    if name not in known:
                        self.error(path, line_number, f'Event {event_id} targets unknown map name "{name}".')

            if command_type in {"addclaim", "addcore", "add_prov_resource"}:
                target = re.search(r"\bwhich\s*=\s*(-?\d+)", line)
                if target and int(target.group(1)) >= 0 and int(target.group(1)) not in self.province_ids:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} targets unknown province {target.group(1)}.",
                    )

            if command_type in {
                "add_leader_skill",
                "set_leader_skill",
                "sleepleader",
                "wakeleader",
            }:
                identifier = re.search(r"\bwhich\s*=\s*(-?\d+)", line)
                if identifier and int(identifier.group(1)) >= 0:
                    leader_id = int(identifier.group(1))
                    if leader_id not in self.leader_ids:
                        self.error(path, line_number, f"Event {event_id} targets unknown leader {leader_id}.")

            if command_type == "waketeam":
                identifier = re.search(r"\bwhich\s*=\s*(\d+)", line)
                if identifier and int(identifier.group(1)) not in self.team_ids:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} wakes unknown technology team {identifier.group(1)}.",
                    )

            if command_type in {
                "headofgovernment",
                "headofstate",
                "foreignminister",
                "armamentminister",
                "ministerofsecurity",
                "ministerofintelligence",
                "chiefofstaff",
                "chiefofarmy",
                "chiefofnavy",
                "chiefofair",
            }:
                identifier = re.search(r"\bwhich\s*=\s*(\d+)", line)
                if identifier and int(identifier.group(1)) not in self.minister_ids:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} appoints unknown minister {identifier.group(1)}.",
                    )

            payload = line[command.end() :]

            if command_type == "activate_unit_type":
                target = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", payload)
                if not target:
                    self.error(path, line_number, f"Event {event_id} has malformed unit activation.")
                elif target.group(1) not in self.division_types | self.brigade_types:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} activates undefined unit type {target.group(1)}.",
                    )

            if command_type == "new_model":
                self.error(
                    path,
                    line_number,
                    f"Event {event_id} resets a national unit template; models must advance through technology.",
                )
                target = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", payload)
                model = re.search(r"\bvalue\s*=\s*(-?\d+)", payload)
                if not target or not model:
                    self.error(path, line_number, f"Event {event_id} has malformed new_model command.")
                else:
                    unit_type = target.group(1)
                    model_index = int(model.group(1))
                    model_count = self.division_model_counts.get(
                        unit_type,
                        self.brigade_model_counts.get(unit_type),
                    )
                    if model_count is None:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} updates undefined unit type {unit_type}.",
                        )
                    elif not 0 <= model_index < model_count:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} selects model {model_index} for {unit_type}, "
                            f"but only models 0-{model_count - 1} exist.",
                        )
                if "AUBM_V4_UNIT_GATE" in line:
                    self.error(
                        path,
                        line_number,
                        "Generated availability gates must not reset the current unit model.",
                    )

            if command_type == "add_division":
                unit = re.search(r"\bvalue\s*=\s*([A-Za-z0-9_]+)", payload)
                model = re.search(r"\bwhen\s*=\s*(-?\d+)", payload)
                attachment = re.search(r"\bwhere\s*=\s*([A-Za-z0-9_-]+)", payload)
                if not unit:
                    self.error(path, line_number, f"Event {event_id} has malformed add_division command.")
                else:
                    unit_type = unit.group(1)
                    if unit_type not in self.division_types:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} adds undefined division type {unit_type}.",
                        )
                    elif model and int(model.group(1)) >= 0:
                        model_index = int(model.group(1))
                        model_count = self.division_model_counts[unit_type]
                        if not 0 <= model_index < model_count:
                            self.error(
                                path,
                                line_number,
                                f"Event {event_id} adds model {model_index} of {unit_type}, "
                                f"but only models 0-{model_count - 1} exist.",
                            )
                if attachment and not attachment.group(1).lstrip("-").isdigit():
                    attachment_type = attachment.group(1)
                    if attachment_type != "none" and attachment_type not in self.brigade_types:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} adds undefined brigade type {attachment_type}.",
                        )
                    elif (
                        unit
                        and unit.group(1) in self.division_types
                        and attachment_type != "none"
                        and attachment_type not in self.division_allowed_brigades.get(unit.group(1), set())
                    ):
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} attaches illegal brigade {attachment_type} "
                            f"to {unit.group(1)}.",
                        )
                if unit and not unit.group(1).startswith("d_"):
                    if not model or not -99 <= int(model.group(1)) <= -1:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} directly grants a fixed-model {unit.group(1)}; "
                            "use a negative when value for a current-model understrength formation.",
                        )
                if unit and unit.group(1) in {
                    "carrier",
                    "light_carrier",
                    "battleship",
                    "battlecruiser",
                    "heavy_cruiser",
                    "light_cruiser",
                    "destroyer",
                    "submarine",
                    "interceptor",
                    "multi_role",
                    "cas",
                    "tactical_bomber",
                    "strategic_bomber",
                    "naval_bomber",
                    "transport_plane",
                } and (not model or int(model.group(1)) >= 0):
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} grants a fixed-model combat {unit.group(1)}; "
                        "use current-model partial deployment or full-cost production.",
                    )

            if command_type in {"max_organization", "morale"}:
                target = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", payload)
                broad_targets = {"land", "air", "naval"}
                if (
                    target
                    and target.group(1) not in broad_targets
                    and target.group(1) not in self.division_types
                ):
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} modifies undefined division type {target.group(1)}.",
                    )

            if command_type == "build_division":
                unit = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", payload)
                attachment = re.search(r"\bvalue\s*=\s*([A-Za-z0-9_]+)", payload)
                fixed_cost = re.search(r"\bcost\s*=\s*-?\d+(?:\.\d+)?", payload)
                accelerated = re.search(r"\bwhere\s*=\s*\d+", payload)
                serial = re.search(r"\bwhen\s*=\s*(\d+)", payload)
                if fixed_cost:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} fixes a discounted player production cost.",
                    )
                if not serial or int(serial.group(1)) != 1:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} must authorize exactly one unit per production command; "
                        "multi-unit serials hide manpower and leave later items unfunded.",
                    )
                if not accelerated:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} creates a full-cost zero-progress production line; "
                        "event procurement must fund progress on the first item.",
                    )
                else:
                    remaining_days = int(re.search(r"\bwhere\s*=\s*(\d+)", payload).group(1))
                    approved_shbb_contract = (
                        event_id in {9281880, 9281881}
                        and remaining_days == 420
                        and unit
                        and unit.group(1) == "battleship"
                    )
                    if not 1 <= remaining_days <= 730 and not approved_shbb_contract:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} uses {remaining_days} remaining days; "
                            "event-funded first-item progress must be between 1 and 730 days.",
                        )
                required: list[tuple[str, set[str], str]] = []
                if not unit:
                    self.error(path, line_number, f"Event {event_id} has malformed build_division command.")
                else:
                    unit_type = unit.group(1)
                    required.append((unit_type, self.division_types, "division"))
                    if unit_type in {"garrison", "militia"}:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} queues a {unit_type}; security formations must be named and placed directly.",
                        )
                if attachment and attachment.group(1) != "none":
                    required.append((attachment.group(1), self.brigade_types, "brigade"))
                for unit_type, active_types, label in required:
                    if unit_type not in active_types:
                        self.error(
                            path,
                            line_number,
                            f"Event {event_id} queues undefined {label} type {unit_type}.",
                        )
                        continue
                if (
                    unit
                    and attachment
                    and attachment.group(1) != "none"
                    and unit.group(1) in self.division_types
                    and attachment.group(1) in self.brigade_types
                    and attachment.group(1)
                    not in self.division_allowed_brigades.get(unit.group(1), set())
                ):
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} queues {unit.group(1)} with illegal brigade "
                        f"{attachment.group(1)}.",
                    )

            if command_type == "add_brigade":
                attachment = re.search(r"\bvalue\s*=\s*([A-Za-z0-9_]+)", payload)
                if not attachment:
                    self.error(path, line_number, f"Event {event_id} has malformed add_brigade command.")
                elif attachment.group(1) not in self.brigade_types:
                    self.error(
                        path,
                        line_number,
                        f"Event {event_id} adds undefined brigade type {attachment.group(1)}.",
                    )

    def validate_cross_event(self) -> None:
        all_ids = set(self.india_events)
        set_flags: set[str] = set()
        used_flags: list[tuple[str, pathlib.Path, int]] = []
        for path, event in self.india_events.values():
            for match in re.finditer(
                rf"\bsetflag\s+which\s*=\s*({INDIA_FLAG_PATTERN})",
                event.text,
                re.I,
            ):
                set_flags.add(match.group(1).lower())
            used_flag_patterns = (
                rf"\bflag\s*=\s*({INDIA_FLAG_PATTERN})",
                rf"\bflag\s*=\s*\{{\s*which\s*=\s*({INDIA_FLAG_PATTERN})",
            )
            for pattern in used_flag_patterns:
                for match in re.finditer(pattern, event.text, re.I):
                    line = event.line + event.text.count("\n", 0, match.start())
                    used_flags.append((match.group(1).lower(), path, line))
            for match in re.finditer(r"\bcommand\s*=\s*\{[^\n]*\btype\s*=\s*trigger[^\n]*\bwhich\s*=\s*(\d+)", event.text):
                target = int(match.group(1))
                if target not in all_ids:
                    line = event.line + event.text.count("\n", 0, match.start())
                    self.error(path, line, f"Force-trigger target {target} is not an India event.")
                elif extract_blocks(self.india_events[target][1].text, "date"):
                    line = event.line + event.text.count("\n", 0, match.start())
                    target_path = self.india_events[target][0]
                    self.error(
                        path,
                        line,
                        f"Force-trigger target {target} in {target_path.name} is dated; "
                        "dated events must fire through their own trigger window.",
                    )
            for match in re.finditer(
                r"\bcommand\s*=\s*\{[^\n]*\btype\s*=\s*event[^\n]*\bwhich\s*=\s*(\d+)[^\n]*\bwhere\s*=\s*([A-Z0-9]{3})",
                event.text,
            ):
                target = int(match.group(1))
                target_country = match.group(2)
                line = event.line + event.text.count("\n", 0, match.start())
                if target not in all_ids:
                    self.error(path, line, f"Foreign-event target {target} is not loaded.")
                    continue
                target_event = self.india_events[target][1]
                declared_country = scalar(target_event.text, "country")
                if declared_country != target_country:
                    self.error(
                        path,
                        line,
                        f"Foreign-event target {target} belongs to {declared_country}, not {target_country}.",
                    )
        for flag, path, line in used_flags:
            if flag not in set_flags:
                self.error(path, line, f'Trigger flag "{flag}" is never set by a loaded India event.')

    def validate_campaign_contracts(self) -> None:
        def loaded(event_id: int) -> tuple[pathlib.Path, Block] | None:
            result = self.india_events.get(event_id)
            if not result:
                self.error(self.mod / "db/events.txt", 1, f"Required campaign event {event_id} is not loaded.")
            return result

        bootstrap = loaded(9270000)
        if bootstrap:
            path, event = bootstrap
            slept = {
                int(value)
                for value in re.findall(r"\btype\s*=\s*sleepevent\s+which\s*=\s*(\d+)", event.text)
            }
            for event_id in (2900127, 2900128, 2900129, 2051001):
                if event_id not in slept:
                    self.error(path, event.line, f"Bootstrap does not sleep conflicting stock event {event_id}.")

        for event_id, (path, event) in self.india_events.items():
            if re.search(r"\btype\s*=\s*sleepevent\s+which\s*=\s*9000(?:1|15)\d+", event.text):
                self.error(
                    path,
                    event.line,
                    f"Event {event_id} sleeps a shared generic-election event instead of excluding India from its TAG list.",
                )

        strategy_review = loaded(9280500)
        if strategy_review:
            path, event = strategy_review
            decisions = extract_blocks(event.text, "decision")
            decision_text = decisions[0].text if decisions else ""
            dates = extract_blocks(event.text, "date")
            date_text = dates[0].text if dates else ""
            if scalar(decision_text, "year") != "1937" or scalar(date_text, "year") != "1937":
                self.error(path, event.line, "Strategic orientation review is not available from 1937.")

        strategy_menu = loaded(9280501)
        if strategy_menu:
            path, event = strategy_menu
            if "Open second menu: Germany, Japan or independent Asia" not in event.text:
                self.error(path, event.line, "Strategic review does not expose the second-menu choices in its action label.")

        dockyard_standard = loaded(9271111)
        if dockyard_standard:
            path, event = dockyard_standard
            expected = {
                "carrier": -50,
                "light_carrier": -50,
                "escort_carrier": -50,
                "battleship": -50,
                "battlecruiser": -50,
                "heavy_cruiser": -50,
                "light_cruiser": -50,
                "destroyer": -50,
                "submarine": -50,
                "transport": -50,
            }
            for unit_type, value in expected.items():
                command = (
                    f"build_time which = {unit_type} when = now "
                    f"where = relative value = {value}"
                )
                if command not in event.text:
                    self.error(path, event.line, f"Dockyard standard is missing {unit_type} efficiency {value}.")
            if re.search(r"\btype\s*=\s*build_(?:time|cost)\s+which\s*=\s*naval\b", event.text):
                self.error(path, event.line, "Dockyard standard uses a broad naval modifier.")
            for flag in (
                "ind_aubm_dockyard_efficiency_standard",
                "ind_aubm_dockyard_efficiency_50",
            ):
                if f"setflag which = {flag}" not in event.text:
                    self.error(path, event.line, f"Dockyard standard lacks compatibility flag {flag}.")

        dockyard_migration = loaded(9271112)
        if dockyard_migration:
            path, event = dockyard_migration
            expected = {
                "carrier": -40,
                "light_carrier": -40,
                "escort_carrier": -40,
                "battleship": -40,
                "battlecruiser": -40,
                "heavy_cruiser": -35,
                "light_cruiser": -35,
                "destroyer": -30,
                "submarine": -30,
                "transport": -30,
            }
            for unit_type, value in expected.items():
                command = (
                    f"build_time which = {unit_type} when = now "
                    f"where = relative value = {value}"
                )
                if command not in event.text:
                    self.error(path, event.line, f"Dockyard migration is missing {unit_type} differential {value}.")
            if "flag = ind_aubm_dockyard_efficiency_standard" not in event.text:
                self.error(path, event.line, "Dockyard migration does not require the earlier standard.")
            if "NOT = { flag = ind_aubm_dockyard_efficiency_50 }" not in event.text:
                self.error(path, event.line, "Dockyard migration lacks its one-time save guard.")
            if "setflag which = ind_aubm_dockyard_efficiency_50" not in event.text:
                self.error(path, event.line, "Dockyard migration does not mark the 50-percent standard.")

        army_rebuild = loaded(9270300)
        if army_rebuild:
            path, event = army_rebuild
            if re.search(r"\btype\s*=\s*build_division\b", event.text):
                self.error(path, event.line, "The 1934 army rebuild still creates full-manpower production lines.")
            expected_actions = {
                "action_a": (4, 24),
                "action_b": (3, 30),
                "action_c": (4, 24),
            }
            for action_name, (division_count, manpower_cost) in expected_actions.items():
                actions = extract_blocks(event.text, action_name)
                if len(actions) != 1:
                    self.error(path, event.line, f"Army rebuild is missing exactly one {action_name} block.")
                    continue
                action = actions[0]
                direct_grants = re.findall(r"\btype\s*=\s*add_division\b[^}\n]*", action.text)
                if len(direct_grants) != division_count:
                    self.error(
                        path,
                        event.line + event.text.count("\n", 0, event.text.find(action.text)),
                        f"{action_name} grants {len(direct_grants)} cadres; expected {division_count}.",
                    )
                if any(not re.search(r"\bwhen\s*=\s*-[1-9][0-9]?\b", grant) for grant in direct_grants):
                    self.error(path, event.line, f"{action_name} contains a full-strength or fixed-model cadre grant.")
                if f"manpowerpool value = -{manpower_cost}" not in action.text:
                    self.error(path, event.line, f"{action_name} does not charge its {manpower_cost}-manpower cadre cost.")
                if "setflag which = ind_v42_army_reward_contract" not in action.text:
                    self.error(path, event.line, f"{action_name} does not mark the corrected reward contract.")

        for event_id in (9270404, 9270405, 9270406, 9270407):
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            if scalar(event.text, "persistent") != "yes":
                self.error(path, event.line, f"War-entry decision {event_id} is not permanently reusable.")
            decision = extract_blocks(event.text, "decision")
            if not decision or re.search(r"\bflag\s*=\s*ind_v3_.*orientation", decision[0].text):
                self.error(path, event.line, f"War-entry decision {event_id} is gated by a historical orientation flag.")

        strategy_targets = {
            9270404: "ind_v4_strategy_allied",
            9270405: "ind_v4_strategy_axis",
            9270406: "ind_v4_strategy_soviet",
            9270407: "ind_v4_strategy_japan",
            9270408: "ind_v4_strategy_independent_asia",
            9270409: "ind_v4_strategy_nam",
        }
        all_strategy_flags = set(strategy_targets.values())
        for event_id, expected_flag in strategy_targets.items():
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            actions = extract_blocks(event.text, "action_a")
            action = actions[0].text if actions else ""
            set_flags = set(re.findall(r"\btype\s*=\s*setflag\s+which\s*=\s*(ind_v4_strategy_[a-z_]+)", action))
            clear_flags = set(re.findall(r"\btype\s*=\s*clrflag\s+which\s*=\s*(ind_v4_strategy_[a-z_]+)", action))
            if set_flags != {expected_flag} or not all_strategy_flags - {expected_flag} <= clear_flags:
                self.error(path, event.line, f"War-entry decision {event_id} leaves the V4 strategy ledger inconsistent.")

        for event_id in (9270408, 9270409, 9280800, 9280801, 9280810, 9280811, 9280812, 9280813, 9280820, 9280830, 9280840, 9280841, 9280842):
            loaded(event_id)

        mechanization = loaded(9271204)
        if mechanization:
            path, event = mechanization
            for guidance in ("fully reinforced", "Upgrades allocation"):
                if guidance not in event.text:
                    self.error(path, event.line, f"Mechanization event omits refit prerequisite: {guidance}.")

        for event_id, (path, event) in self.india_events.items():
            if scalar(event.text, "country") != "IND":
                continue
            for letter in "abcdef":
                for action in extract_blocks(event.text, f"action_{letter}"):
                    if re.search(r"\btype\s*=\s*add_division\b", action.text) and not re.search(
                        r"\btype\s*=\s*add_corps\b", action.text
                    ):
                        self.error(
                            path,
                            event.line,
                            f"Immediate formation action {event_id}{letter} lacks an explicit destination corps.",
                        )

        reserve_ledger = loaded(9280840)
        if reserve_ledger:
            path, event = reserve_ledger
            if scalar(event.text, "persistent") != "yes":
                self.error(path, event.line, "Annual trained-reserve ledger must be persistent.")
            for required in (
                "manpowerpool value = 150",
                "aubm_v4_single_army",
                "aubm_v4_territorial_army",
                "aubm_v4_cadre_army",
                "ind_v3_universal_national_service",
                "ind_v3_technical_reserve",
                "ind_v3_universal_service",
                "ind_v3_selective_service",
                "ind_v3_volunteer_service",
                "ind_v41_recruit_class_1934",
                "ind_v41_recruit_class_1964",
            ):
                if required not in event.text:
                    self.error(path, event.line, f"Annual trained-reserve ledger is missing {required}.")
            for year in range(1934, 1965):
                flag = f"ind_v41_recruit_class_{year}"
                if event.text.count(flag) != 2:
                    self.error(path, event.line, f"Annual trained-reserve ledger does not gate and mark {year} exactly once.")

        if 9280844 in self.india_events:
            path, event = self.india_events[9280844]
            self.error(path, event.line, "Obsolete old-save reserve reconciliation remains in clean-game source.")

        revenue_service = loaded(9280316)
        if revenue_service:
            path, event = revenue_service
            if "free_money value = 2" not in event.text:
                self.error(path, event.line, "The national revenue service does not provide the sustained +2 daily money floor.")

        emergency_reserve = loaded(9280841)
        if emergency_reserve:
            path, event = emergency_reserve
            if scalar(event.text, "persistent") != "yes":
                self.error(path, event.line, "Emergency reserve decision must be persistent.")
            if "NOT = { manpower = 100 }" not in event.text:
                self.error(path, event.line, "Emergency reserve decision is not limited to a depleted manpower pool.")
            helper = loaded(9280842)
            helper_text = helper[1].text if helper else ""
            for year in range(1939, 1965):
                flag = f"ind_v41_emergency_reserve_{year}"
                if flag not in event.text or flag not in helper_text:
                    self.error(path, event.line, f"Emergency reserve decision does not gate and mark {year}.")

        national_service = loaded(9273203)
        if national_service:
            path, event = national_service
            triggers = extract_blocks(event.text, "trigger")
            outer_trigger = triggers[0].text if triggers else ""
            if "ind_v3_integrated" not in outer_trigger or "ind_v3_ocean_logistics_settled" in outer_trigger:
                self.error(path, event.line, "National Service remains chained to naval logistics instead of Indian statehood.")
            if re.search(r"\btype\s*=\s*build_division\b", event.text):
                self.error(path, event.line, "National Service consumes its manpower award through event production orders.")
            for amount in (400, 260, 150):
                if f"manpowerpool value = {amount}" not in event.text:
                    self.error(path, event.line, f"National Service is missing the {amount}-manpower policy grant.")

        modernization = loaded(9281000)
        if modernization:
            path, event = modernization
            if re.search(r"\btype\s*=\s*build_(?:time|cost)\b", event.text):
                self.error(path, event.line, "The opening modernization event still changes new-unit construction values.")
            if "setflag which = ind_v43_upgrade_contract_final" not in event.text:
                self.error(path, event.line, "The final India upgrade contract lacks its save-compatibility marker.")
            if "setflag which = ind_v43_upgrade_contract_low_ic" not in event.text:
                self.error(path, event.line, "The India upgrade contract lacks its low-IC marker.")
            if "setflag which = ind_v43_unit_build_restore" not in event.text:
                self.error(path, event.line, "Fresh games are not protected from the legacy unit-build repair.")

        for event_id, (path, event) in self.india_events.items():
            broad_discount = re.search(
                r"\btype\s*=\s*build_(?:time|cost)\s+which\s*=\s*(?:land|air|naval)\b[^}\n]*\bvalue\s*=\s*-",
                event.text,
            )
            if broad_discount:
                self.error(
                    path,
                    event.line,
                    f"Event {event_id} applies a broad unit-build discount that also changes new construction.",
                )

        construction_repair = loaded(9281007)
        if construction_repair:
            path, event = construction_repair
            if "ind_v43_modernization_contract" not in event.text or "ind_v43_unit_build_restore" not in event.text:
                self.error(path, event.line, "The legacy construction repair lacks its one-time save guard.")
            for branch in ("land", "air", "naval"):
                if f"build_time which = {branch} when = on_upgrade where = relative value = 90" not in event.text:
                    self.error(path, event.line, f"The legacy repair cannot reverse the final {branch} time discount.")
                if f"build_cost which = {branch} when = on_upgrade where = relative value = 75" not in event.text:
                    self.error(path, event.line, f"The legacy repair cannot reverse the final {branch} cost discount.")
        else:
            self.error(pathlib.Path("mod/db/events/aubm_v4/32_national_consolidation.txt"), 1, "Legacy construction repair event 9281007 is missing.")

        modernization_repair = loaded(9281005)
        if modernization_repair:
            path, event = modernization_repair
            if "ind_v43_modernization_contract" not in event.text or "ind_v43_unit_build_restore" not in event.text:
                self.error(path, event.line, "The upgrade-contract amendment lacks its old-save guard.")
            if re.search(r"\btype\s*=\s*build_(?:time|cost)\b", event.text):
                self.error(path, event.line, "The compatibility ledger still changes unit construction.")

        low_ic_repair = loaded(9281006)
        if low_ic_repair:
            path, event = low_ic_repair
            if "ind_v43_upgrade_contract_low_ic" not in event.text:
                self.error(path, event.line, "The low-IC amendment lacks its one-time guard.")
            if "ind_v43_unit_build_restore" not in event.text:
                self.error(path, event.line, "The low-IC compatibility ledger can run before construction repair.")
            if re.search(r"\btype\s*=\s*build_(?:time|cost)\b", event.text):
                self.error(path, event.line, "The low-IC compatibility ledger still changes unit construction.")

        naval_progress_commands = []
        for event_id in (9271104, 9271105, 9271106, 9271109, 9274009):
            result = loaded(event_id)
            if not result:
                continue
            _, event = result
            naval_progress_commands.extend(
                re.findall(r"\btype\s*=\s*build_division\b[^}\n]*\bwhere\s*=\s*\d+", event.text)
            )
        if len(naval_progress_commands) < 20:
            self.error(pathlib.Path("mod/db/events/india_v3/32_navy.txt"), 1, "Naval programmes do not preserve enough inherited hull progress.")

        ledger = loaded(9280800)
        if ledger:
            path, event = ledger
            trigger_blocks = extract_blocks(event.text, "trigger")
            trigger_text = trigger_blocks[0].text if trigger_blocks else ""
            if "NOT = { flag = ind_v3_world_role }" not in trigger_text:
                self.error(path, event.line, "Strategy ledger must run only before the elected programme exists.")
            for strategy_flag in ("ind_v3_non_aligned", "ind_v4_strategy_nam"):
                if f"type = setflag which = {strategy_flag}" in event.text:
                    self.error(
                        path,
                        event.line,
                        f"Strategy ledger must not infer {strategy_flag} from the absence of an alliance.",
                    )

        state_reactions = {
            9280352: "ind_v4_burma_refugees",
            9280353: "ind_v4_siamese_alignment_crisis",
            9280356: "ind_v4_siamese_alignment_crisis",
            9280357: "ind_v4_japanese_southern_choice",
        }
        for event_id, forbidden_flag in state_reactions.items():
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            trigger = extract_blocks(event.text, "trigger")
            if trigger and re.search(rf"(?m)^\s*flag\s*=\s*{re.escape(forbidden_flag)}\s*$", trigger[0].text):
                self.error(
                    path,
                    event.line,
                    f"State reaction {event_id} still depends on predecessor flag {forbidden_flag}.",
                )

        for event_id in (9270780, 9270781, 9270782, 9270783):
            result = loaded(event_id)
            if result and scalar(result[1].text, "persistent") != "yes":
                self.error(result[0], result[1].line, f"Cabinet watchdog {event_id} is not persistent.")

        for event_id in (
            9280310,
            9280311,
            9280312,
            9280500,
            9280501,
            9280502,
            9280503,
            9280510,
            9280511,
            9280512,
        ):
            result = loaded(event_id)
            if result and scalar(result[1].text, "persistent") != "yes":
                self.error(result[0], result[1].line, f"Recurring campaign event {event_id} must be persistent.")

        path_modules = {
            "41_allied.txt",
            "42_axis.txt",
            "43_soviet.txt",
            "44_non_aligned.txt",
            "45_japan.txt",
        }
        for event_id, (path, event) in self.india_events.items():
            if path.name not in path_modules:
                continue
            deathdates = extract_blocks(event.text, "deathdate")
            year = scalar(deathdates[0].text, "year") if deathdates else None
            expected_year = "1964"
            if year != expected_year:
                self.error(path, event.line, f"Path event {event_id} expires before the campaign end.")

        dynamic_path_bridges = {
            9280520: "ind_v3_allied_naval_mission",
            9280521: "ind_v3_german_mission",
            9280522: "ind_v3_soviet_planning_mission",
            9280523: "ind_v3_japanese_naval_mission",
            9280524: "ind_v3_delhi_conference",
        }
        for event_id, bridge_flag in dynamic_path_bridges.items():
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            if bridge_flag not in event.text:
                self.error(path, event.line, f"Dynamic mission {event_id} does not bridge into its path chain.")

        for event_id in (9270404, 9270405, 9270406, 9270407):
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            decision = extract_blocks(event.text, "decision")
            if decision and re.search(r"\batwar\s*=\s*no\b", decision[0].text):
                self.error(path, event.line, f"Coalition-entry decision {event_id} is unavailable during war.")
            deathdates = extract_blocks(event.text, "deathdate")
            if not deathdates or scalar(deathdates[0].text, "year") != "1964":
                self.error(path, event.line, f"Coalition-entry decision {event_id} expires too early.")

        for event_id, (path, event) in self.india_events.items():
            if scalar(event.text, "country") != "IND":
                continue
            actions: list[Block] = []
            for letter in "abcdefgh":
                actions.extend(extract_blocks(event.text, f"action_{letter}"))
            for action in actions:
                if re.search(r"\btype\s*=\s*add_division\b", action.text) and not re.search(
                    r"\btype\s*=\s*manpowerpool\s+value\s*=\s*-[0-9]",
                    action.text,
                ):
                    self.error(
                        path,
                        event.line,
                        f"Direct formation grant in event {event_id} has no explicit cadre-manpower charge.",
                    )
            if len(actions) != 1 or extract_blocks(event.text, "decision"):
                continue
            if re.search(
                r"\btype\s*=\s*(?:money|supplies)\s+value\s*=\s*-",
                actions[0].text,
            ):
                self.error(
                    path,
                    event.line,
                    f"Automatic one-action event {event_id} imposes an unavoidable resource cost.",
                )

        maturity = loaded(9270206)
        if maturity:
            path, event = maturity
            added_ic = sum(
                int(value)
                for value in re.findall(
                    r"\btype\s*=\s*construct\s+which\s*=\s*ic\s+where\s*=\s*\d+\s+value\s*=\s*(\d+)",
                    event.text,
                )
            )
            if added_ic > 8:
                self.error(path, event.line, f"Industrial maturity grants {added_ic} province IC; cap is 8.")

        regional_fleet_contract = Counter(
            {
                "battleship": 1,
                "light_cruiser": 2,
                "destroyer": 2,
            }
        )
        for event_id in (9271104, 9271105):
            result = loaded(event_id)
            if not result:
                continue
            path, event = result
            actions = extract_blocks(event.text, "action_a")
            if len(actions) != 1:
                self.error(path, event.line, f"Regional fleet event {event_id} lacks one action_a contract.")
                continue
            orders = Counter(
                re.findall(
                    r"\btype\s*=\s*build_division\b[^}\n]*\bwhich\s*=\s*([A-Za-z0-9_]+)",
                    actions[0].text,
                )
            )
            if orders != regional_fleet_contract:
                self.error(
                    path,
                    event.line,
                    f"Regional fleet event {event_id} orders {dict(orders)}; expected "
                    f"one battleship, two light cruisers and two destroyers.",
                )
            if actions[0].text.count("type = add_brigade") < 12:
                self.error(path, event.line, f"Regional fleet event {event_id} lacks its full fit-out pool.")

        oceanic_fleet = loaded(9271106)
        if oceanic_fleet:
            path, event = oceanic_fleet
            expected_paths = {
                "ind_v3_fleet_carrier_authorized": Counter(
                    {"carrier": 1, "heavy_cruiser": 2, "destroyer": 2}
                ),
                "ind_v3_two_light_carriers": Counter(
                    {"light_carrier": 2, "light_cruiser": 2, "destroyer": 2}
                ),
                "ind_v3_submarine_navy": Counter(
                    {"battlecruiser": 1, "light_cruiser": 1, "destroyer": 1, "submarine": 2}
                ),
            }
            for flag, expected_orders in expected_paths.items():
                orders = Counter()
                for line in event.text.splitlines():
                    if flag not in line or "type = build_division" not in line:
                        continue
                    unit = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", line)
                    if unit:
                        orders[unit.group(1)] += 1
                if orders != expected_orders:
                    self.error(
                        path,
                        event.line,
                        f"Oceanic fleet path {flag} orders {dict(orders)}; expected {dict(expected_orders)}.",
                    )
        arsenal = loaded(9273205)
        if arsenal and re.search(
            r"\bbuild_division\s+which\s*=\s*(?:carrier|light_carrier|battleship)",
            arsenal[1].text,
        ):
            self.error(arsenal[0], arsenal[1].line, "Wartime arsenal grants a late capital ship.")

        direct_appointments = {
            event_id
            for event_id, (_, event) in self.india_events.items()
            if scalar(event.text, "country") == "IND"
            and re.search(r"\btype\s*=\s*(?:headofstate|headofgovernment)\b", event.text)
        }
        allowed_appointments = {
            9270002,
            9270103,
            9270780,
            9270781,
            9270782,
            9270783,
            9270792,
            9272206,
            9274000,
            9280830,
        }
        unexpected = direct_appointments - allowed_appointments
        for event_id in sorted(unexpected):
            path, event = self.india_events[event_id]
            self.error(path, event.line, f"Event {event_id} can overwrite the stable constitutional cabinet.")
        for event_id in (9270780, 9270781, 9270782):
            result = loaded(event_id)
            if result and "ind_v3_1936_mandate" not in result[1].text:
                self.error(
                    result[0],
                    result[1].line,
                    f"Cabinet repair event {event_id} can override the 1936 mandate.",
                )
        bose_repair = loaded(9270783)
        if bose_repair and "ind_v3_bose_mandate" not in bose_repair[1].text:
            self.error(bose_repair[0], bose_repair[1].line, "Bose cabinet repair lacks its mandate guard.")

        combined_text = "\n".join(event.text for _, event in self.india_events.values())
        if re.search(r"\baubm_v4_malaya_settled\b", combined_text, re.I):
            self.error(
                self.mod / "db/events/aubm_v4",
                1,
                "Malaya is external territory and must not use an internal-settlement flag.",
            )

        india = self.mod / "scenarios/1933/british raj.inc"
        india_text = load_text(india) if india.is_file() else ""
        money = scalar(india_text, "money")
        supplies = scalar(india_text, "supplies")
        if not money or int(money) < 3000:
            self.error(india, 1, "India must start with at least 3000 money for the opening research budget.")
        if not supplies or int(supplies) < 4000:
            self.error(india, 1, "India must start with at least 4000 supplies.")

        mobilization = self.mod / "db/events/Mobilization.txt"
        if mobilization.is_file() and re.search(r"(?<![A-Z0-9])IND(?![A-Z0-9])", load_text(mobilization)):
            self.error(mobilization, 1, "India remains in the stock generic mobilization TAG lists.")

    def validate_combat_rules(self) -> None:
        path = self.mod / "db/misc.txt"
        text = self.validate_file_structure(path)
        expected_fragments = {
            "Air vs. Air strength pacing": "0.45 # AUBM V4",
            "Air vs. Navy strength pacing": "0.40 # AUBM V4",
            "Navy vs. Navy strength pacing": "0.55 # AUBM V4",
            "Auto-retreat threshold": "12.0 # AUBM V4",
            "Emergency rebase speed": "0.65\t# AUBM V4",
            "Air scramble enabled": "# _MISSION_AIR_SCRAMBLE_",
            "Naval scramble enabled": "# _MISSION_NAVAL_SCRAMBLE_",
            "Paid upgrade cost": "0.5 # AUBM V4.2: paid upgrades use the Darkest Hour baseline cost",
            "Paid upgrade time": "0.5 # AUBM V4.2: paid upgrades use the Darkest Hour baseline time",
            "No reinforcement-funded upgrades": "0.0 # AUBM V4.2: reinforcement does not bypass the upgrade budget",
            "No passive free upgrades": "0 # AUBM V4.2: zero upgrade IC means zero upgrade progress",
        }
        for label, fragment in expected_fragments.items():
            if fragment not in text:
                self.error(path, 1, f"{label} is missing expected V4 setting.")
        for mission in ("AIR_SCRAMBLE", "NAVAL_SCRAMBLE"):
            match = re.search(rf"# _MISSION_{mission}_\s*\r?\n\s*(\d+)", text)
            if not match or match.group(1) != "1":
                self.error(path, 1, f"{mission.replace('_', ' ').title()} must be enabled.")

    def validate_naval_conversions(self) -> None:
        expected = {
            "battleship.txt": (
                "upgrade = { type = carrier upgrade_time_factor = 0.90 upgrade_cost_factor = 0.70 }",
            ),
            "battlecruiser.txt": (
                "upgrade = { type = carrier upgrade_time_factor = 0.80 upgrade_cost_factor = 0.75 }",
            ),
            "heavy_cruiser.txt": (
                "upgrade = { type = light_carrier upgrade_time_factor = 0.32 upgrade_cost_factor = 0.60 }",
                "upgrade = { type = escort_carrier upgrade_time_factor = 0.45 upgrade_cost_factor = 0.35 }",
            ),
            "light_cruiser.txt": (
                "upgrade = { type = light_carrier upgrade_time_factor = 0.30 upgrade_cost_factor = 0.65 }",
                "upgrade = { type = escort_carrier upgrade_time_factor = 0.42 upgrade_cost_factor = 0.35 }",
            ),
            "transport.txt": (
                "upgrade = { type = light_carrier upgrade_time_factor = 0.30 upgrade_cost_factor = 1.00 }",
                "upgrade = { type = escort_carrier upgrade_time_factor = 0.40 upgrade_cost_factor = 0.60 }",
            ),
        }
        root = self.mod / "db/units/divisions"
        for filename, routes in expected.items():
            path = root / filename
            text = self.validate_file_structure(path)
            for route in routes:
                if route not in text:
                    self.error(path, 1, f"Required naval conversion route is missing: {route}")

        land_routes = {
            "cavalry.txt": "upgrade = { type = motorized upgrade_time_factor = 0.45 upgrade_cost_factor = 0.45 }",
            "militia.txt": "upgrade = { type = infantry upgrade_time_factor = 0.45 upgrade_cost_factor = 0.70 }",
            "garrison.txt": "upgrade = { type = infantry upgrade_time_factor = 0.50 upgrade_cost_factor = 0.70 }",
        }
        for filename, route in land_routes.items():
            path = root / filename
            text = self.validate_file_structure(path)
            if route not in text:
                self.error(path, 1, f"Required paid land conversion route is missing: {route}")

    def validate_direct_dh_provenance(self) -> None:
        installer = self.root / "installer/Install-A-Union-Before-Midnight.ps1"
        text = self.validate_file_structure(installer)
        if "Darkest Hour Full" not in text:
            self.error(installer, 1, "Installer does not identify Darkest Hour Full as its foundation.")
        election_path = self.mod / "db/events/Election_day.txt"
        election_text = self.validate_file_structure(election_path)
        if re.search(r"(?<![A-Z0-9])IND(?![A-Z0-9])", election_text):
            self.error(election_path, 1, "India remains in the shared generic-election TAG lists.")
        sprite_root = self.mod / "gfx/map/units"
        bitmap_root = sprite_root / "bmp"
        palette_root = self.mod / "gfx/palette"
        if sprite_root.exists():
            bitmap_pattern = re.compile(r'^\s*Bitmap\s*=\s*"([^"]+)"', re.M)
            palette_pattern = re.compile(r'^\s*Palette\s*=\s*"([^"]+)"', re.M)
            for asset in sprite_root.glob("*.spr"):
                if " C-IND" not in asset.name:
                    self.error(asset, 1, "India sprite descriptor must use the C-IND namespace.")
                    continue
                definition = asset.read_text(encoding="ascii", errors="replace")
                bitmap = bitmap_pattern.search(definition)
                palette = palette_pattern.search(definition)
                if not bitmap:
                    self.error(asset, 1, "Sprite descriptor does not declare a bitmap.")
                elif not (bitmap_root / bitmap.group(1)).is_file():
                    self.error(asset, 1, f"Missing sprite bitmap {bitmap.group(1)!r}.")
                if not palette:
                    self.error(asset, 1, "Sprite descriptor does not declare a palette.")
                else:
                    palette_path = palette_root / palette.group(1)
                    if not palette_path.suffix:
                        palette_path = palette_path.with_suffix(".bmp")
                    if not palette_path.is_file():
                        self.error(asset, 1, f"Missing sprite palette {palette.group(1)!r}.")

        stock_province = self.game / "map/Map_1/Province.csv"
        mod_province = self.mod / "map/Map_1/Province.csv"
        if stock_province.exists() and mod_province.exists():
            stock_rows = {
                row[0]: row
                for row in csv.reader(stock_province.open(encoding="cp1252"), delimiter=";")
                if row and row[0].isdigit()
            }
            india_range = set(range(1278, 1279)) | set(range(1406, 1541)) | {1612}
            with mod_province.open(encoding="cp1252", newline="") as stream:
                for line, row in enumerate(csv.reader(stream, delimiter=";"), 1):
                    if not row or not row[0].isdigit() or row[0] not in stock_rows:
                        continue
                    if row != stock_rows[row[0]] and int(row[0]) not in india_range:
                        self.error(
                            mod_province,
                            line,
                            f"Province {row[0]} changes the world map outside the India scope.",
                        )

    def validate_installer_manifest(self) -> None:
        manifest_path = self.root / "installer/manifest.txt"
        hash_path = self.root / "installer/manifest-sha256.txt"
        if not manifest_path.is_file() or not hash_path.is_file():
            self.error(self.root / "installer", 1, "Installer manifests are missing.")
            return

        manifest = [
            line.strip()
            for line in manifest_path.read_text(encoding="ascii").splitlines()
            if line.strip()
        ]
        hashes: dict[str, str] = {}
        for line_number, line in enumerate(
            hash_path.read_text(encoding="ascii").splitlines(),
            1,
        ):
            if not line.strip():
                continue
            match = re.fullmatch(r"([0-9a-f]{64}) \*(.+)", line)
            if not match:
                self.error(hash_path, line_number, "Malformed SHA-256 manifest entry.")
                continue
            digest, relative = match.groups()
            if relative in hashes:
                self.error(hash_path, line_number, f"Duplicate hash entry for {relative}.")
            hashes[relative] = digest

        if len(manifest) != len(set(manifest)):
            self.error(manifest_path, 1, "Installer manifest contains duplicate paths.")
        # Mirrors .NET StringComparer.OrdinalIgnoreCase used by the PowerShell
        # manifest generator. Uppercasing matters for ASCII punctuation order.
        if manifest != sorted(manifest, key=str.upper):
            self.error(manifest_path, 1, "Installer manifest is not sorted.")
        if set(manifest) != set(hashes):
            missing_hashes = sorted(set(manifest) - set(hashes))
            extra_hashes = sorted(set(hashes) - set(manifest))
            if missing_hashes:
                self.error(
                    hash_path,
                    1,
                    f"Hash manifest is missing {len(missing_hashes)} path(s).",
                )
            if extra_hashes:
                self.error(
                    hash_path,
                    1,
                    f"Hash manifest contains {len(extra_hashes)} unmanaged path(s).",
                )

        def read_patterns(filename: str) -> tuple[str, ...]:
            pattern_path = self.root / "installer" / filename
            if not pattern_path.is_file():
                self.error(pattern_path, 1, "Installer exclusion list is missing.")
                return ()
            return tuple(
                line.strip()
                for line in pattern_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )

        nonredistributable_patterns = read_patterns(
            "nonredistributable-overlay-patterns.txt"
        )
        personal_sprite_patterns = read_patterns(
            "personal-sprite-overlay-patterns.txt"
        )

        def matches_any(relative: str, patterns: tuple[str, ...]) -> bool:
            return any(fnmatchcase(relative, pattern) for pattern in patterns)

        actual: set[str] = set()
        for path in self.mod.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.mod).as_posix()
            lowered_parts = {part.lower() for part in path.relative_to(self.mod).parts}
            if "save games" in lowered_parts or "logs" in lowered_parts or "log" in lowered_parts:
                continue
            actual.add(relative)

        nonredistributable = {
            relative
            for relative in actual
            if matches_any(relative, nonredistributable_patterns)
        }
        personal_sprites = {
            relative
            for relative in actual
            if matches_any(relative, personal_sprite_patterns)
        }
        public_overlay = actual - nonredistributable - personal_sprites
        personal_overlay = public_overlay | personal_sprites
        manifest_set = set(manifest)

        leaked = sorted(manifest_set & nonredistributable)
        if leaked:
            self.error(
                manifest_path,
                1,
                "Installer manifest includes nonredistributable local payload, "
                f"first: {leaked[0]}",
            )

        valid_overlays = (public_overlay, personal_overlay)
        if manifest_set not in valid_overlays:
            expected = (
                personal_overlay
                if manifest_set & personal_sprites
                else public_overlay
            )
            missing = sorted(expected - manifest_set)
            stale = sorted(manifest_set - expected)
            if missing:
                self.error(
                    manifest_path,
                    1,
                    f"Installer manifest omits {len(missing)} overlay file(s), first: {missing[0]}",
                )
            if stale:
                self.error(
                    manifest_path,
                    1,
                    f"Installer manifest names {len(stale)} absent file(s), first: {stale[0]}",
                )

        for relative in manifest:
            path = (self.mod / relative).resolve()
            try:
                path.relative_to(self.mod.resolve())
            except ValueError:
                self.error(manifest_path, 1, f"Unsafe installer path: {relative}")
                continue
            if not path.is_file() or relative not in hashes:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != hashes[relative]:
                self.error(hash_path, 1, f"Stale SHA-256 entry for {relative}.")

    def run(self) -> int:
        self.load_provinces()
        self.load_personnel()
        self.load_unit_definitions()
        self.validate_scenario()
        included = self.included_event_files()
        included_resolved = {path.resolve() for path in included}

        v4_dir = self.mod / INDIA_EVENT_DIRS[1]
        actual_v4 = {path.name for path in v4_dir.glob("*.txt")}
        missing = REQUIRED_V4_MODULES - actual_v4
        for name in sorted(missing):
            self.error(v4_dir / name, 1, "Required V4 event module is missing.")

        for relative_dir in INDIA_EVENT_DIRS:
            event_dir = self.mod / relative_dir
            for path in sorted(event_dir.glob("*.txt")):
                if path.resolve() not in included_resolved:
                    self.error(path, 1, "India event module is not loaded by db/events.txt.")
                self.validate_event_file(path)

        self.validate_cross_event()
        self.validate_campaign_contracts()
        self.validate_combat_rules()
        self.validate_naval_conversions()
        self.validate_direct_dh_provenance()
        self.validate_installer_manifest()

        self.issues.sort(key=lambda item: (item.severity != "ERROR", str(item.path), item.line))
        for issue in self.issues:
            try:
                display = issue.path.relative_to(self.root)
            except ValueError:
                display = issue.path
            print(f"{issue.severity}: {display}:{issue.line}: {issue.message}")
        errors = sum(issue.severity == "ERROR" for issue in self.issues)
        warnings = sum(issue.severity == "WARN" for issue in self.issues)
        print(f"\nA Union Before Midnight V4 validation: {errors} error(s), {warnings} warning(s)")
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    return Validator(args.root.resolve()).run()


if __name__ == "__main__":
    sys.exit(main())
