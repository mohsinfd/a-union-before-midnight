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
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass


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
    "15_operational_command.txt",
    "20_procurement.txt",
    "30_war_settlements.txt",
}
KNOWN_COMMANDS = {
    "access",
    "activate_unit_type",
    "add_corps",
    "add_division",
    "add_leader_skill",
    "add_prov_resource",
    "addcore",
    "ai",
    "alliance",
    "armamentminister",
    "belligerence",
    "build_division",
    "chiefofair",
    "chiefofarmy",
    "chiefofnavy",
    "chiefofstaff",
    "clrflag",
    "construct",
    "dissent",
    "domestic",
    "foreignminister",
    "gain_tech",
    "headofgovernment",
    "headofstate",
    "hq_supply_eff",
    "industrial_modifier",
    "inherit",
    "intelligence",
    "manpowerpool",
    "max_organization",
    "ministerofintelligence",
    "ministerofsecurity",
    "money",
    "morale",
    "new_model",
    "rarematerialspool",
    "relation",
    "repair_mod",
    "research_mod",
    "secedeprovince",
    "set_leader_skill",
    "setflag",
    "sleepleader",
    "steal_tech",
    "supplies",
    "tc_mod",
    "trigger",
    "wakeleader",
    "waketeam",
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
        self.leader_ids: set[int] = set()
        self.minister_ids: set[int] = set()
        self.team_ids: set[int] = set()

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
            if not scalar(event.text, "name"):
                self.error(path, event.line, f"Event {event_id} has no name.")
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

            if command_type == "secedeprovince":
                if country == "IND" and re.search(r"\bwhich\s*=\s*IND\b", line):
                    self.error(path, line_number, "India must not secede a province to itself.")

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

            if command_type == "build_division":
                unit = re.search(r"\bwhich\s*=\s*([A-Za-z0-9_]+)", line)
                attachment = re.search(r"\bvalue\s*=\s*([A-Za-z0-9_]+)", line)
                required = [unit.group(1)] if unit else []
                if attachment and attachment.group(1) != "none":
                    required.append(attachment.group(1))
                context = "\n".join(lines[max(0, offset - 10) : offset])
                for unit_type in required:
                    activated = re.search(
                        rf"\bactivate_unit_type\s+which\s*=\s*{re.escape(unit_type)}\b",
                        context,
                    )
                    modelled = re.search(
                        rf"\bnew_model\s+which\s*=\s*{re.escape(unit_type)}\s+value\s*=\s*0\b",
                        context,
                    )
                    if not activated or not modelled:
                        self.error(
                            path,
                            line_number,
                            f"Event-built {unit_type} lacks an immediate type/model availability gate.",
                        )

    def validate_cross_event(self) -> None:
        all_ids = set(self.india_events)
        set_flags: set[str] = set()
        used_flags: list[tuple[str, pathlib.Path, int]] = []
        for path, event in self.india_events.values():
            for match in re.finditer(r"\bsetflag\s+which\s*=\s*(ind_v[34]_[a-z0-9_]+)", event.text, re.I):
                set_flags.add(match.group(1).lower())
            for match in re.finditer(r"\bflag\s*=\s*(ind_v[34]_[a-z0-9_]+)", event.text, re.I):
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
        for flag, path, line in used_flags:
            if flag not in set_flags:
                self.error(path, line, f'Trigger flag "{flag}" is never set by a loaded India event.')

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
        }
        for label, fragment in expected_fragments.items():
            if fragment not in text:
                self.error(path, 1, f"{label} is missing expected V4 setting.")
        for mission in ("AIR_SCRAMBLE", "NAVAL_SCRAMBLE"):
            match = re.search(rf"# _MISSION_{mission}_\s*\r?\n\s*(\d+)", text)
            if not match or match.group(1) != "1":
                self.error(path, 1, f"{mission.replace('_', ' ').title()} must be enabled.")

    def validate_direct_dh_provenance(self) -> None:
        installer = self.root / "installer/Install-A-Union-Before-Midnight.ps1"
        text = self.validate_file_structure(installer)
        if "Darkest Hour Full" not in text:
            self.error(installer, 1, "Installer does not identify Darkest Hour Full as its foundation.")
        if re.search(r"Blood and Iron|B&I", text, re.I):
            self.error(installer, 1, "Installer still depends on Blood and Iron.")
        models = self.mod / "gfx/interface/models"
        if models.exists() and any(path.is_file() for path in models.rglob("*")):
            self.error(
                models,
                1,
                "Donor-dependent model-panel overrides must not ship in V4.",
            )

        sprite_root = self.mod / "gfx/map/units"
        if sprite_root.exists():
            for asset in sprite_root.rglob("*"):
                if not asset.is_file():
                    continue
                relative = asset.relative_to(sprite_root).as_posix()
                if relative.startswith("bmp/"):
                    allowed = (
                        asset.suffix.lower() == ".bmp"
                        and asset.name.startswith("AUBM-IND-")
                    )
                else:
                    allowed = (
                        asset.suffix.lower() == ".spr"
                        and " C-IND" in asset.name
                        and "AUBM-IND-" in asset.read_text(
                            encoding="ascii",
                            errors="replace",
                        )
                    )
                if not allowed:
                    self.error(
                        asset,
                        1,
                        "Map-sprite override is outside the original AUBM India namespace.",
                    )

        palette_root = self.mod / "gfx/palette"
        if palette_root.exists():
            for asset in palette_root.rglob("*"):
                if not asset.is_file():
                    continue
                if asset.suffix.lower() != ".bmp" or not asset.name.startswith(
                    "AUBM-IND-"
                ):
                    self.error(
                        asset,
                        1,
                        "Palette override is outside the original AUBM India namespace.",
                    )

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
        if manifest != sorted(manifest, key=str.casefold):
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

        actual: set[str] = set()
        for path in self.mod.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.mod).as_posix()
            lowered_parts = {part.lower() for part in path.relative_to(self.mod).parts}
            if "save games" in lowered_parts or "logs" in lowered_parts or "log" in lowered_parts:
                continue
            actual.add(relative)
        if set(manifest) != actual:
            missing = sorted(actual - set(manifest))
            stale = sorted(set(manifest) - actual)
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
        self.validate_combat_rules()
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
