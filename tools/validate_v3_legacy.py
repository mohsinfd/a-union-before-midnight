#!/usr/bin/env python3
"""Static production gate for India Mod V3.

The Darkest Hour parser is permissive enough to load many malformed commands and
then fail days or months later. This validator checks the command semantics that
matter to V3 before files are copied into the game directory.
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


SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = SOURCE_ROOT / "tools" / "v3_config.json"
REGISTRY_PATH = SOURCE_ROOT / "tools" / "data" / "provinces.csv"
ROLES_PATH = SOURCE_ROOT / "tools" / "data" / "province_roles.csv"
PROVINCE_OVERRIDES_PATH = SOURCE_ROOT / "tools" / "data" / "province_overrides.csv"
INDIA_VISUAL_MANIFEST_PATH = SOURCE_ROOT / "tools" / "data" / "india_visual_manifest.csv"
V32_ART_MANIFEST_PATH = SOURCE_ROOT / "tools" / "data" / "v32_art_manifest.csv"
PERSONNEL_ART_MANIFEST_PATH = SOURCE_ROOT / "tools" / "data" / "personnel_art_manifest.csv"
HISTORICAL_TRAITS_PATH = SOURCE_ROOT / "tools" / "data" / "india_historical_traits.csv"
V3_EVENT_PREFIX = pathlib.PureWindowsPath("db/events/india_v3")
MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}
CONSTRUCTION_TYPES = {
    "aa",
    "air_base",
    "coastal_fort",
    "ic",
    "infrastructure",
    "land_fort",
    "naval_base",
    "nuclear_reactor",
    "radar_station",
    "rocket_test",
}
NAVAL_CONSTRUCTION = {"naval_base", "coastal_fort"}
RESOURCE_TYPES = {"energy", "metal", "oil", "rare_materials"}
KNOWN_COMMAND_TYPES = {
    "access",
    "activate_unit_type",
    "add_corps",
    "add_division",
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
    "guarantee",
    "headofstate",
    "headofgovernment",
    "industrial_modifier",
    "intelligence",
    "independence",
    "inherit",
    "leave_alliance",
    "manpowerpool",
    "ministerofintelligence",
    "ministerofsecurity",
    "morale",
    "money",
    "max_organization",
    "new_model",
    "peace",
    "relation",
    "research_mod",
    "secedeprovince",
    "set_leader_skill",
    "setflag",
    "sleepleader",
    "sleepminister",
    "steal_tech",
    "supplies",
    "tc_mod",
    "trigger",
    "wakeleader",
    "waketeam",
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
    start: int
    end: int
    line: int


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="cp1252", errors="replace")


def without_comments(text: str) -> str:
    return re.sub(r"#[^\r\n]*", "", text)


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def find_blocks(text: str, key: str) -> list[Block]:
    """Return balanced blocks introduced by `key = {`."""
    clean = without_comments(text)
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{", re.I)
    blocks: list[Block] = []
    for match in pattern.finditer(clean):
        open_brace = clean.find("{", match.start(), match.end())
        depth = 1
        cursor = open_brace + 1
        in_quote = False
        while cursor < len(clean) and depth:
            char = clean[cursor]
            if char == '"' and (cursor == 0 or clean[cursor - 1] != "\\"):
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            cursor += 1
        if depth == 0:
            blocks.append(
                Block(
                    text=clean[match.start() : cursor],
                    start=match.start(),
                    end=cursor,
                    line=line_number(clean, match.start()),
                )
            )
    return blocks


def find_top_level_blocks(text: str, key: str) -> list[Block]:
    """Return balanced `key = {` blocks whose key begins at brace depth zero."""
    clean = without_comments(text)
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{", re.I)
    depths = [0] * (len(clean) + 1)
    depth = 0
    in_quote = False
    for index, char in enumerate(clean):
        depths[index] = depth
        if char == '"' and (index == 0 or clean[index - 1] != "\\"):
            in_quote = not in_quote
        elif not in_quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
    depths[len(clean)] = depth
    blocks: list[Block] = []
    for match in pattern.finditer(clean):
        if depths[match.start()] != 0:
            continue
        open_brace = clean.find("{", match.start(), match.end())
        block_depth = 1
        cursor = open_brace + 1
        in_quote = False
        while cursor < len(clean) and block_depth:
            char = clean[cursor]
            if char == '"' and clean[cursor - 1] != "\\":
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    block_depth += 1
                elif char == "}":
                    block_depth -= 1
            cursor += 1
        if block_depth == 0:
            blocks.append(
                Block(
                    text=clean[match.start() : cursor],
                    start=match.start(),
                    end=cursor,
                    line=line_number(clean, match.start()),
                )
            )
    return blocks


def balanced(text: str) -> bool:
    clean = without_comments(text)
    depth = 0
    in_quote = False
    for index, char in enumerate(clean):
        if char == '"' and (index == 0 or clean[index - 1] != "\\"):
            in_quote = not in_quote
        elif not in_quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    return False
    return depth == 0 and not in_quote


def atom(block: str, key: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(key)}\s*=\s*(?:\"([^\"]*)\"|([^\s{{}}#]+))",
        block,
        re.I,
    )
    return (match.group(1) or match.group(2)) if match else None


def integer(block: str, key: str) -> int | None:
    value = atom(block, key)
    if value is None or not re.fullmatch(r"-?\d+", value):
        return None
    return int(value)


def scenario_list(block: str, key: str) -> set[int]:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*\{{([^}}]*)\}}", block, re.I | re.S)
    return set(map(int, re.findall(r"\b\d+\b", match.group(1)))) if match else set()


def normalize_game_path(raw: str) -> pathlib.Path:
    return pathlib.Path(*pathlib.PureWindowsPath(raw).parts)


class Validator:
    def __init__(self, root: pathlib.Path):
        self.root = root.resolve()
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.game_root = pathlib.Path(self.config["game_root"])
        self.baseline_root = pathlib.Path(self.config["baseline_mod"]).resolve()
        self.event_min = int(self.config["event_id_min"])
        self.event_max = int(self.config["event_id_max"])
        self.issues: list[Issue] = []
        self.provinces: dict[int, dict[str, str]] = {}
        self.ind_owned: set[int] = set()
        self.ind_controlled: set[int] = set()
        self.starting_owned_by_tag: dict[str, set[int]] = defaultdict(set)
        self.province_roles: dict[int, dict[str, str]] = {}
        self.divisions = self.load_unit_types("divisions")
        self.brigades = self.load_unit_types("brigades")
        self.disabled_brigades = self.load_disabled_brigade_types()
        self.tech_ids = self.load_tech_ids()
        self.tech_specialities = self.load_tech_specialities()
        self.minister_ids = self.load_csv_ids(self.root / "db" / "ministers" / "ministers_ind.csv")
        self.minister_pictures = self.load_minister_pictures()
        self.team_ids: set[int] = set()
        self.asset_index: dict[str, pathlib.Path] | None = None
        self.v3_events: dict[int, tuple[pathlib.Path, Block]] = {}

    def issue(self, severity: str, path: pathlib.Path, line: int, message: str) -> None:
        try:
            display = path.resolve().relative_to(self.root)
        except ValueError:
            display = path
        self.issues.append(Issue(severity, display, line, message))

    def error(self, path: pathlib.Path, line: int, message: str) -> None:
        self.issue("ERROR", path, line, message)

    def warn(self, path: pathlib.Path, line: int, message: str) -> None:
        self.issue("WARN", path, line, message)

    def load_registry(self) -> None:
        if not REGISTRY_PATH.exists():
            self.error(REGISTRY_PATH, 1, "Province registry is missing; run build_province_registry.py.")
            return
        with REGISTRY_PATH.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                province_id = int(row["province_id"])
                self.provinces[province_id] = row
        if not self.provinces:
            self.error(REGISTRY_PATH, 1, "Province registry contains no rows.")
        if not ROLES_PATH.exists():
            self.error(ROLES_PATH, 1, "Curated province-role registry is missing.")
            return
        with ROLES_PATH.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                province_id = int(row["province_id"])
                if province_id in self.province_roles:
                    self.error(ROLES_PATH, 1, f"Duplicate province role {province_id}.")
                self.province_roles[province_id] = row
                authoritative = self.provinces.get(province_id)
                if not authoritative:
                    self.error(ROLES_PATH, 1, f"Province role {province_id} is not on the Map_1 registry.")
                elif row["canonical_name"].casefold() != authoritative["name"].casefold():
                    self.error(
                        ROLES_PATH,
                        1,
                        f"Province role {province_id} name {row['canonical_name']!r} "
                        f"does not match Map_1 name {authoritative['name']!r}.",
                    )

    def load_unit_types(self, category: str) -> set[str]:
        directory = self.root / "db" / "units" / category
        return {path.stem.lower() for path in directory.glob("*.txt")}

    def load_disabled_brigade_types(self) -> set[str]:
        """Find placeholders that the engine loads without display strings."""
        path = self.root / "db" / "units" / "brigade_types.txt"
        if not path.exists():
            self.error(path, 1, "Brigade type registry is missing.")
            return set()
        text = read_text(path)
        required = ("type", "name", "short_name", "desc", "short_desc")
        disabled: set[str] = set()
        for brigade in self.brigades - {"none"}:
            blocks = find_top_level_blocks(text, brigade)
            if len(blocks) != 1:
                self.error(
                    path,
                    1,
                    f"Brigade type {brigade!r} must have exactly one registry block; found {len(blocks)}.",
                )
                disabled.add(brigade)
                continue
            if any(atom(blocks[0].text, field) is None for field in required):
                disabled.add(brigade)
        return disabled

    def load_tech_ids(self) -> set[int]:
        ids: set[int] = set()
        for path in (self.root / "db" / "tech").glob("*.txt"):
            text = without_comments(read_text(path))
            ids.update(map(int, re.findall(r"\bid\s*=\s*(\d+)", text, re.I)))
        return ids

    def load_tech_specialities(self) -> set[str]:
        specialities: set[str] = set()
        pattern = re.compile(r"\bcomponent\s*=\s*\{[^}]*?\btype\s*=\s*([a-z_]+)", re.I | re.S)
        for path in (self.root / "db" / "tech").glob("*.txt"):
            specialities.update(match.group(1).lower() for match in pattern.finditer(read_text(path)))
        return specialities

    @staticmethod
    def load_csv_ids(path: pathlib.Path) -> set[int]:
        ids: set[int] = set()
        if not path.exists():
            return ids
        with path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if row and row[0].isdigit():
                    ids.add(int(row[0]))
        return ids

    def load_minister_pictures(self) -> dict[int, str]:
        path = self.root / "db" / "ministers" / "ministers_ind.csv"
        pictures: dict[int, str] = {}
        if not path.exists():
            return pictures
        with path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if len(row) > 9 and row[0].isdigit():
                    pictures[int(row[0])] = row[9]
        return pictures

    def resolve_asset(self, basename: str) -> pathlib.Path | None:
        name = pathlib.Path(basename).stem.lower() + ".bmp"
        direct_candidates = (
            self.root / "gfx" / "events" / name,
            self.root / "gfx" / "interface" / "pics" / name,
            self.game_root / "gfx" / "events" / name,
            self.game_root / "gfx" / "interface" / "pics" / name,
        )
        for candidate in direct_candidates:
            if candidate.exists():
                return candidate
        if self.asset_index is None:
            self.asset_index = {}
            for base in (self.root / "gfx", self.game_root / "gfx"):
                if base.exists():
                    for path in base.rglob("*.bmp"):
                        self.asset_index.setdefault(path.name.lower(), path)
        return self.asset_index.get(name)

    def validate_required_structure(self) -> list[pathlib.Path]:
        events_txt = self.root / "db" / "events.txt"
        event_dir = self.root / V3_EVENT_PREFIX
        required = [
            "00_bootstrap.txt",
            "10_politics.txt",
            "12_society.txt",
            "20_development.txt",
            "21_fallbacks.txt",
            "22_resources.txt",
            "30_military.txt",
            "31_air_force.txt",
            "32_navy.txt",
            "33_command_research.txt",
            "34_elite_forces.txt",
            "40_diplomacy.txt",
            "46_world_reactions.txt",
            "41_allied.txt",
            "42_axis.txt",
            "43_soviet.txt",
            "44_non_aligned.txt",
            "45_japan.txt",
            "47_revisionist_aftermath.txt",
            "50_wartime.txt",
            "51_theatres.txt",
            "52_home_front.txt",
            "60_postwar.txt",
            "61_cold_war.txt",
            "62_victory.txt",
        ]
        paths = [event_dir / name for name in required]
        if not events_txt.exists():
            self.error(events_txt, 1, "Global event loader is missing.")
            return paths
        loader = read_text(events_txt)
        for path in paths:
            relative = str(path.relative_to(self.root)).replace("/", "\\")
            count = len(
                re.findall(
                    rf'^\s*event\s*=\s*"{re.escape(relative)}"\s*$',
                    loader,
                    re.I | re.M,
                )
            )
            if not path.exists():
                self.error(path, 1, "Required V3 event module is missing.")
            if count != 1:
                self.error(events_txt, 1, f"{relative} must be loaded exactly once; found {count}.")
        return paths

    def validate_india_names(self) -> None:
        formation_requirements = {
            "armynames.csv": (200, r"^\d+(?:st|nd|rd|th) Indian Corps$"),
            "airnames.csv": (100, r"^No\. \d+ Indian Air Group$"),
            "navynames.csv": (100, r"^\d+(?:st|nd|rd|th) Indian Naval Group$"),
        }
        for filename, (expected_count, pattern) in formation_requirements.items():
            path = self.root / "db" / filename
            if not path.exists():
                self.error(path, 1, "Formation-name file is missing.")
                continue
            with path.open(encoding="latin-1", newline="") as stream:
                rows = [row for row in csv.reader(stream, delimiter=";") if row and row[0].upper() == "IND"]
            names = [row[1].strip() for row in rows if len(row) > 1]
            if len(names) != expected_count:
                self.error(path, 1, f"IND requires {expected_count} formation names; found {len(names)}.")
            if len(names) != len(set(name.casefold() for name in names)):
                self.error(path, 1, "IND formation names contain duplicates.")
            if pattern:
                malformed = [name for name in names if not re.fullmatch(pattern, name)]
                if malformed:
                    self.error(path, 1, f"Malformed IND formation name: {malformed[0]!r}.")

        path = self.root / "db" / "unitnames.csv"
        if not path.exists():
            self.error(path, 1, "Unit-name file is missing.")
            return
        with path.open(encoding="latin-1", newline="") as stream:
            rows = [
                row
                for row in csv.reader(stream, delimiter=";")
                if len(row) > 2 and row[0].upper() == "IND"
            ]
        by_type: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            by_type[row[1]].append(row[2].strip())
        minimums = {
            "HQ": 16,
            "Inf": 96,
            "Gar": 40,
            "Cav": 24,
            "Mot": 36,
            "Mec": 36,
            "L ARM": 24,
            "Arm": 30,
            "Par": 16,
            "Mar": 16,
            "Mtn": 24,
            "45": 24,
            "Mil": 60,
            "Fig": 64,
            "Int F": 64,
            "Esc F": 32,
            "Str": 32,
            "Tac": 64,
            "CAS": 64,
            "Nav": 64,
            "Trp": 32,
            "V1": 16,
            "V2": 16,
            "CV": 12,
            "27": 12,
            "31": 12,
            "BB": 12,
            "BC": 12,
            "CA": 24,
            "CL": 30,
            "DD": 40,
            "SS": 32,
            "NS": 12,
            "TP": 40,
        }
        for unit_type, minimum in minimums.items():
            names = by_type.get(unit_type, [])
            if len(names) < minimum:
                self.error(path, 1, f"IND {unit_type} requires at least {minimum} names; found {len(names)}.")
            if len(names) != len(set(name.casefold() for name in names)):
                self.error(path, 1, f"IND {unit_type} names contain duplicates.")
            if any(not name for name in names):
                self.error(path, 1, f"IND {unit_type} contains a blank unit name.")
        for unit_type in ("Mot", "Mec"):
            stale = [name for name in by_type.get(unit_type, []) if "infantry division" in name.casefold()]
            if stale:
                self.error(path, 1, f"IND {unit_type} retains an infantry name: {stale[0]!r}.")
        all_names = [name for names in by_type.values() for name in names]
        forbidden = [name for name in all_names if "hmis" in name.casefold() or "virrant" in name.casefold()]
        if forbidden:
            self.error(path, 1, f"IND unit catalogue retains a forbidden legacy name: {forbidden[0]!r}.")

    def validate_province_overrides(self) -> None:
        province_path = self.root / "map" / "Map_1" / "Province.csv"
        names_path = self.root / "map" / "Map_1" / "province_names.csv"
        for path in (province_path, names_path, PROVINCE_OVERRIDES_PATH):
            if not path.exists():
                self.error(path, 1, "Required V3 province-override input is missing.")
                return
        with province_path.open(encoding="latin-1", newline="") as stream:
            provinces = {
                int(row[0]): row
                for row in csv.reader(stream, delimiter=";")
                if row and row[0].isdigit()
            }
        with names_path.open(encoding="latin-1", newline="") as stream:
            names = {}
            for row in csv.reader(stream, delimiter=";"):
                match = re.fullmatch(r"PROV(\d+)", row[0] if row else "")
                if match and len(row) > 1:
                    names[int(match.group(1))] = row[1]
        columns = {
            "terrain": 6,
            "infrastructure": 9,
            "oil": 16,
            "metal": 17,
            "energy": 18,
            "rares": 19,
        }
        with PROVINCE_OVERRIDES_PATH.open(encoding="utf-8-sig", newline="") as stream:
            overrides = list(csv.DictReader(stream))
        for override in overrides:
            province_id = int(override["province_id"])
            row = provinces.get(province_id)
            if row is None:
                self.error(province_path, 1, f"V3 province override {province_id} is absent from Province.csv.")
                continue
            if override["new_name"].strip() and names.get(province_id, "").casefold() != override["new_name"].strip().casefold():
                self.error(
                    names_path,
                    1,
                    f"Province {province_id} name is {names.get(province_id)!r}; "
                    f"expected {override['new_name'].strip()!r}.",
                )
            for key, column in columns.items():
                expected = override[f"new_{key}"].strip()
                if expected and row[column].casefold() != expected.casefold():
                    self.error(
                        province_path,
                        1,
                        f"Province {province_id} {key} is {row[column]!r}; expected {expected!r}.",
                    )

    def validate_india_visual_namespace(self) -> None:
        country_path = self.root / "db" / "country.csv"
        if not country_path.exists():
            self.error(country_path, 1, "Country graphics mapping is missing.")
            return
        with country_path.open(encoding="latin-1", newline="") as stream:
            india_rows = [
                row
                for row in csv.reader(stream, delimiter=";")
                if row and row[0].upper() == "IND"
            ]
        if len(india_rows) != 1:
            self.error(country_path, 1, f"Expected one IND country row; found {len(india_rows)}.")
        elif len(india_rows[0]) < 6 or india_rows[0][3:6] != ["IND", "IND", "IND"]:
            self.error(
                country_path,
                1,
                "IND must use the IND army-sprite, unit-picture and model-icon namespaces.",
            )

        if not INDIA_VISUAL_MANIFEST_PATH.exists():
            self.error(INDIA_VISUAL_MANIFEST_PATH, 1, "India visual manifest is missing.")
            return
        with INDIA_VISUAL_MANIFEST_PATH.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        expected_counts = {
            "sprite": 2008,
            "gurkha_sprite": 18,
            "national_flag": 2,
            "unit_panel": 314,
            "production_icon": 338,
        }
        actual_counts = Counter(row["kind"] for row in rows)
        if actual_counts != Counter(expected_counts):
            self.error(
                INDIA_VISUAL_MANIFEST_PATH,
                1,
                f"India visual manifest counts are {dict(actual_counts)}; expected {expected_counts}.",
            )
        targets = [row["target"] for row in rows]
        if len(targets) != len(set(target.casefold() for target in targets)):
            self.error(INDIA_VISUAL_MANIFEST_PATH, 1, "India visual manifest contains duplicate targets.")

        sprite_bmp_dir = self.root / "gfx" / "map" / "units" / "bmp"
        palette_dir = self.root / "gfx" / "palette"
        inspected_palettes: dict[pathlib.Path, list[tuple[int, int, int]]] = {}
        compared_palette_pairs: set[tuple[pathlib.Path, pathlib.Path]] = set()

        def resolve_palette(reference: str) -> pathlib.Path:
            candidate = palette_dir / reference
            if not candidate.exists() and not candidate.suffix:
                candidate = candidate.with_suffix(".bmp")
            return candidate

        def palette_colours(path: pathlib.Path) -> list[tuple[int, int, int]]:
            if path in inspected_palettes:
                return inspected_palettes[path]
            data = path.read_bytes()
            if len(data) < 54 or data[:2] != b"BM":
                raise ValueError(f"not a BMP palette: {path}")
            pixel_offset = struct.unpack_from("<I", data, 10)[0]
            dib_size = struct.unpack_from("<I", data, 14)[0]
            bits = struct.unpack_from("<H", data, 28)[0]
            if bits != 8:
                raise ValueError(f"palette is {bits}-bit, expected 8-bit: {path}")
            table_start = 14 + dib_size
            colours = [
                tuple(data[offset : offset + 3])
                for offset in range(table_start, pixel_offset - 3, 4)
            ]
            inspected_palettes[path] = colours
            return colours

        for line, row in enumerate(rows, start=2):
            target = self.root / pathlib.PurePosixPath(row["target"])
            if not target.exists():
                self.error(target, 1, f"Generated India {row['kind']} asset is missing.")
                continue
            if row["kind"] in {"sprite", "gurkha_sprite"}:
                if "C-IND" not in target.name:
                    self.error(target, 1, "India sprite descriptor lacks the C-IND country token.")
                text = read_text(target)
                bitmap = atom(text, "Bitmap")
                palette = atom(text, "Palette")
                if not bitmap or not (sprite_bmp_dir / bitmap).exists():
                    self.error(target, 1, f"India sprite references missing bitmap {bitmap!r}.")
                if palette:
                    palette_path = resolve_palette(palette)
                    if not palette_path.exists():
                        self.error(target, 1, f"India sprite references missing palette {palette!r}.")
                    elif not palette_path.name.upper().startswith("V3-IND-"):
                        self.error(target, 1, "India sprite does not use a V3 Indian service palette.")
                    else:
                        donor = self.root / pathlib.PurePosixPath(row["donor"])
                        donor_palette_name = atom(read_text(donor), "Palette") if donor.exists() else None
                        donor_palette = (
                            resolve_palette(donor_palette_name)
                            if donor_palette_name
                            else pathlib.Path()
                        )
                        pair = (palette_path, donor_palette)
                        if pair not in compared_palette_pairs:
                            compared_palette_pairs.add(pair)
                            try:
                                indian_colours = palette_colours(palette_path)
                                donor_colours = palette_colours(donor_palette)
                                changed = sum(
                                    left != right
                                    for left, right in zip(indian_colours, donor_colours)
                                )
                                colour_delta = sum(
                                    sum(abs(a - b) for a, b in zip(left, right))
                                    for left, right in zip(indian_colours, donor_colours)
                                )
                                if changed < 32 or colour_delta < 2500:
                                    self.error(
                                        target,
                                        1,
                                        "India sprite palette is not visibly distinct from its donor "
                                        f"({changed} entries changed, RGB delta {colour_delta}).",
                                    )
                            except (OSError, ValueError, struct.error) as exc:
                                self.error(target, 1, f"Cannot compare India sprite palette: {exc}.")
                else:
                    self.error(target, 1, "India sprite descriptor has no palette.")
            elif row["kind"] in {"unit_panel", "production_icon"}:
                donor = self.root / pathlib.PurePosixPath(row["donor"])
                try:
                    header = target.read_bytes()[:30]
                    if len(header) < 30 or header[:2] != b"BM":
                        raise ValueError("not a BMP")
                    donor_header = donor.read_bytes()[:30]
                    if len(donor_header) < 30 or donor_header[:2] != b"BM":
                        raise ValueError(f"donor is not a BMP: {donor}")
                    actual = (
                        struct.unpack_from("<i", header, 18)[0],
                        abs(struct.unpack_from("<i", header, 22)[0]),
                        struct.unpack_from("<H", header, 28)[0],
                    )
                    expected = (
                        struct.unpack_from("<i", donor_header, 18)[0],
                        abs(struct.unpack_from("<i", donor_header, 22)[0]),
                        struct.unpack_from("<H", donor_header, 28)[0],
                    )
                    if actual != expected:
                        self.error(
                            target,
                            1,
                            f"India {row['kind']} must match donor dimensions {expected}; found {actual}.",
                        )
                    if actual[2] != 24:
                        self.error(target, 1, f"India {row['kind']} must be 24-bit; found {actual[2]}-bit.")
                except (OSError, ValueError, struct.error) as exc:
                    self.error(target, 1, f"Cannot inspect India {row['kind']}: {exc}.")

        for relative in (
            "gfx/interface/models/ill_div_IND_45_8.bmp",
            "gfx/interface/models/IND_model_45_8.bmp",
            "gfx/map/units/T-d_05 A-STAND C-IND L-1.spr",
        ):
            path = self.root / pathlib.PurePosixPath(relative)
            if not path.exists():
                self.error(path, 1, "Native Gurkha visual coverage is incomplete.")

    def validate_fleet_doctrine(self) -> None:
        expectations = {
            (9271104, "action_a"): Counter({"battleship": 1, "light_cruiser": 2}),
            (9271105, "action_a"): Counter({"battleship": 1, "light_cruiser": 2}),
            (9271107, "action_a"): Counter({"carrier": 1, "heavy_cruiser": 2, "destroyer": 2}),
            (9271107, "action_b"): Counter({"light_carrier": 2, "heavy_cruiser": 2, "destroyer": 2}),
            (
                9271107,
                "action_c",
            ): Counter({"heavy_cruiser": 2, "destroyer": 2, "submarine": 3}),
        }
        for (event_id, action_key), expected in expectations.items():
            entry = self.v3_events.get(event_id)
            if not entry:
                continue
            path, event = entry
            actions = find_blocks(event.text, action_key)
            if not actions:
                self.error(path, event.line, f"Fleet doctrine event {event_id} has no {action_key}.")
                continue
            actual = Counter(
                (atom(command.text, "value") or "").lower()
                for command in find_blocks(actions[0].text, "command")
                if (atom(command.text, "type") or "").lower() == "add_division"
            )
            if actual != expected:
                self.error(
                    path,
                    event.line + actions[0].line - 1,
                    f"Event {event_id} {action_key} fleet composition is {dict(actual)}; "
                    f"expected {dict(expected)}.",
                )

    def loaded_event_files(self) -> list[pathlib.Path]:
        loaders = [self.root / "db" / "events.txt", self.root / "scenarios" / "1933.eug"]
        paths: list[pathlib.Path] = []
        for loader in loaders:
            if not loader.exists():
                continue
            for raw in re.findall(
                r'^\s*event\s*=\s*"([^"]+\.txt)"\s*$',
                without_comments(read_text(loader)),
                re.I | re.M,
            ):
                path = self.root / normalize_game_path(raw)
                if path.exists() and path not in paths:
                    paths.append(path)
        return paths

    def validate_event_ids(self, loaded: list[pathlib.Path], v3_files: list[pathlib.Path]) -> None:
        occurrences: dict[int, list[tuple[pathlib.Path, int]]] = defaultdict(list)
        v3_set = {path.resolve() for path in v3_files if path.exists()}
        for path in loaded:
            text = read_text(path)
            for block in find_top_level_blocks(text, "event"):
                event_id = integer(block.text, "id")
                if event_id is not None:
                    occurrences[event_id].append((path, block.line))
        for event_id, entries in sorted(occurrences.items()):
            if len(entries) > 1:
                touches_v3 = any(path.resolve() in v3_set for path, _ in entries)
                detail = ", ".join(f"{path.name}:{line}" for path, line in entries[:5])
                if touches_v3:
                    for path, line in entries:
                        self.error(path, line, f"Duplicate event id {event_id}: {detail}.")
                else:
                    self.warn(entries[0][0], entries[0][1], f"Baseline duplicate event id {event_id}: {detail}.")

    def validate_loaded_event_assets(self, loaded: list[pathlib.Path]) -> None:
        for path in loaded:
            text = read_text(path)
            for event in find_top_level_blocks(text, "event"):
                picture = atom(event.text, "picture")
                if picture and not self.resolve_asset(picture):
                    event_id = integer(event.text, "id")
                    self.error(
                        path,
                        event.line,
                        f'Loaded event {event_id or "?"} picture "{picture}" cannot be resolved.',
                    )

    def validate_loaded_calendar_days(self, loaded: list[pathlib.Path]) -> None:
        paths = set(loaded)
        paths.add(self.root / "scenarios" / "1933.eug")
        paths.update((self.root / "scenarios" / "1933").glob("*.inc"))
        pattern = re.compile(r"\bday\s*=\s*(-?\d+)\b", re.I)
        for path in sorted(paths):
            if not path.exists():
                continue
            text = without_comments(read_text(path))
            for match in pattern.finditer(text):
                day = int(match.group(1))
                if not 0 <= day <= 29:
                    line = text.count("\n", 0, match.start()) + 1
                    self.error(path, line, f"Calendar day {day} is outside Darkest Hour's 0-29 range.")

    def validate_dormant_ministers(self) -> None:
        path = self.root / "scenarios" / "1933.eug"
        if not path.exists():
            return
        blocks = find_top_level_blocks(read_text(path), "dormant_ministers")
        for block in blocks:
            seen: set[int] = set()
            for match in re.finditer(r"\b\d+\b", without_comments(block.text)):
                minister_id = int(match.group())
                if minister_id in seen:
                    self.error(path, block.line, f"Dormant minister ID {minister_id} is listed more than once.")
                seen.add(minister_id)

    def validate_india_minister_file(self) -> None:
        path = self.root / "db" / "ministers" / "ministers_ind.csv"
        if not path.exists():
            self.error(path, 1, "IND minister file is missing.")
            return
        allowed_personalities: dict[str, set[str]] = defaultdict(set)
        personality_positions = {
            "headofstate": "head of state",
            "headofgovernment": "head of government",
            "foreignminister": "foreign minister",
            "armamentminister": "minister of armament",
            "ministerofsecurity": "minister of security",
            "ministerofintelligence": "head of military intelligence",
            "chiefofstaff": "chief of staff",
            "chiefofarmy": "chief of army",
            "chiefofnavy": "chief of navy",
            "chiefofair": "chief of air force",
        }
        personalities_path = self.root / "db" / "ministers" / "minister_personalities.txt"
        if personalities_path.exists():
            personality_ids: dict[int, tuple[str, int]] = {}
            personality_traits: dict[str, tuple[str, int]] = {}
            for block in find_top_level_blocks(read_text(personalities_path), "minister"):
                trait = atom(block.text, "trait")
                personality_id = integer(block.text, "id")
                game_position = (atom(block.text, "position") or "all").casefold()
                if not trait or personality_id is None:
                    self.error(
                        personalities_path,
                        block.line,
                        "Minister personality requires both trait and numeric id.",
                    )
                    continue
                folded_trait = trait.casefold()
                if personality_id in personality_ids:
                    previous_trait, previous_line = personality_ids[personality_id]
                    self.error(
                        personalities_path,
                        block.line,
                        f"Minister personality id {personality_id} duplicates {previous_trait!r} at line {previous_line}.",
                    )
                personality_ids[personality_id] = (trait, block.line)
                if folded_trait in personality_traits:
                    previous_trait, previous_line = personality_traits[folded_trait]
                    self.error(
                        personalities_path,
                        block.line,
                        f"Minister personality trait {trait!r} duplicates {previous_trait!r} at line {previous_line}.",
                    )
                personality_traits[folded_trait] = (trait, block.line)
                if game_position in {"all", "generic"}:
                    for csv_position in personality_positions.values():
                        allowed_personalities[csv_position].add(folded_trait)
                elif game_position in personality_positions:
                    allowed_personalities[personality_positions[game_position]].add(folded_trait)
                else:
                    self.error(
                        personalities_path,
                        block.line,
                        f"Minister personality {trait!r} has unknown position {game_position!r}.",
                    )
        for donor in (self.root / "db" / "ministers").glob("ministers_*.csv"):
            if donor.name.casefold() == "ministers_ind.csv":
                continue
            with donor.open(encoding="latin-1", newline="") as stream:
                for row in csv.reader(stream, delimiter=";"):
                    if len(row) >= 8 and row[0].isdigit():
                        allowed_personalities[row[1].casefold()].add(row[7].casefold())

        valid_positions = {
            "head of state",
            "head of government",
            "foreign minister",
            "minister of armament",
            "minister of security",
            "head of military intelligence",
            "chief of staff",
            "chief of army",
            "chief of navy",
            "chief of air force",
        }
        valid_ideologies = {"NS", "FA", "PA", "SC", "ML", "SL", "SD", "LWR", "LE", "ST"}
        valid_loyalties = {"very low", "low", "medium", "high", "very high", "undying"}
        seen: set[int] = set()
        with path.open(encoding="latin-1", newline="") as stream:
            rows = list(csv.reader(stream, delimiter=";"))
        for line, row in enumerate(rows[1:], start=2):
            if not row:
                continue
            if not row[0]:
                marker = row[1].strip().casefold() if len(row) > 1 else ""
                if marker != "replacements":
                    self.error(
                        path,
                        line,
                        f"Blank-ID minister row uses unsupported section marker {row[1] if len(row) > 1 else ''!r}.",
                    )
                continue
            if not row[0].isdigit():
                self.error(path, line, f"Minister id must be numeric; found {row[0]!r}.")
                continue
            if len(row) != 11:
                self.error(path, line, f"Minister row has {len(row)} columns; expected 11.")
                continue
            minister_id = int(row[0])
            if minister_id in seen:
                self.error(path, line, f"Duplicate IND minister id {minister_id}.")
            seen.add(minister_id)
            position = row[1].casefold()
            if position not in valid_positions:
                self.error(path, line, f"Minister {minister_id} has unknown position {row[1]!r}.")
            try:
                start_year, end_year, retirement_year = map(int, row[3:6])
                if start_year > end_year or start_year > retirement_year:
                    self.error(path, line, f"Minister {minister_id} has an invalid service-year range.")
            except ValueError:
                self.error(path, line, f"Minister {minister_id} has malformed service years.")
            if row[6].upper() not in valid_ideologies:
                self.error(path, line, f"Minister {minister_id} has unknown ideology {row[6]!r}.")
            if row[8].casefold() not in valid_loyalties:
                self.error(path, line, f"Minister {minister_id} has unknown loyalty {row[8]!r}.")
            if position in allowed_personalities and row[7].casefold() not in allowed_personalities[position]:
                self.error(
                    path,
                    line,
                    f"Minister {minister_id} personality {row[7]!r} is not valid for {row[1]}.",
                )
            if row[10].casefold() != "x":
                self.error(path, line, f"Minister {minister_id} row does not end with X.")

    def validate_events(self, paths: list[pathlib.Path]) -> None:
        seen: set[int] = set()
        for path in paths:
            if not path.exists():
                continue
            text = read_text(path)
            if not balanced(text):
                self.error(path, 1, "Unbalanced braces or quotes.")
                continue
            events = find_top_level_blocks(text, "event")
            if not events:
                self.error(path, 1, "V3 event module contains no events.")
            for event in events:
                event_id = integer(event.text, "id")
                country = (atom(event.text, "country") or "").upper()
                if event_id is None:
                    self.error(path, event.line, "Event has no numeric id.")
                else:
                    if not self.event_min <= event_id <= self.event_max:
                        self.error(
                            path,
                            event.line,
                            f"V3 event id {event_id} is outside reserved range "
                            f"{self.event_min}-{self.event_max}.",
                        )
                    if event_id in seen:
                        self.error(path, event.line, f"Duplicate V3 event id {event_id}.")
                    seen.add(event_id)
                    self.v3_events[event_id] = (path, event)
                for required in ("name", "desc", "picture"):
                    if atom(event.text, required) is None:
                        self.error(path, event.line, f"Event {event_id or '?'} has no {required}.")
                if not find_blocks(event.text, "action_a"):
                    self.error(path, event.line, f"Event {event_id or '?'} has no action_a.")
                actions = [
                    blocks[0]
                    for letter in "abcd"
                    if (blocks := find_blocks(event.text, f"action_{letter}"))
                ]
                chance_values = [integer(action.text, "ai_chance") for action in actions]
                if any(chance is not None for chance in chance_values):
                    if any(chance is None for chance in chance_values):
                        self.error(
                            path,
                            event.line,
                            f"Event {event_id or '?'} mixes explicit and implicit ai_chance values.",
                        )
                    elif sum(chance_values) != 100:
                        self.error(
                            path,
                            event.line,
                            f"Event {event_id or '?'} ai_chance values sum to {sum(chance_values)}, expected 100.",
                        )
                action_names = [(atom(action.text, "name") or "").casefold() for action in actions]
                if len(action_names) != len(set(action_names)):
                    self.error(path, event.line, f"Event {event_id or '?'} has duplicate action names.")
                if not find_blocks(event.text, "decision") and actions:
                    action_resource_gates = []
                    for action in actions:
                        name_match = re.search(r"\bname\s*=", action.text, re.I)
                        gates = [
                            trigger
                            for trigger in find_blocks(action.text, "trigger")
                            if name_match is not None
                            and trigger.start < name_match.start()
                            and re.fullmatch(
                                r"\s*(?:(?:money|supplies|manpower)\s*=\s*\d+\s*)+",
                                without_comments(
                                    trigger.text[
                                        trigger.text.find("{") + 1 : trigger.text.rfind("}")
                                    ]
                                ),
                                re.I,
                            )
                        ]
                        action_resource_gates.append(bool(gates))
                    first_action_start = min(action.start for action in actions)
                    top_triggers = [
                        trigger
                        for trigger in find_blocks(event.text, "trigger")
                        if trigger.start < first_action_start
                    ]
                    has_reachability_gate = False
                    if top_triggers:
                        for or_block in find_blocks(top_triggers[0].text, "OR"):
                            requirements = find_blocks(or_block.text, "AND")
                            if len(requirements) != len(actions):
                                continue
                            if all(
                                re.fullmatch(
                                    r"\s*(?:(?:money|supplies|manpower)\s*=\s*\d+\s*)+",
                                    without_comments(
                                        requirement.text[
                                            requirement.text.find("{") + 1 :
                                            requirement.text.rfind("}")
                                        ]
                                    ),
                                    re.I,
                                )
                                for requirement in requirements
                            ):
                                has_reachability_gate = True
                                break
                    if all(action_resource_gates) and not has_reachability_gate:
                        self.error(
                            path,
                            event.line,
                            f"Mandatory event {event_id or '?'} can fire with no valid action; "
                            "run apply_v31_balance.py to add an affordability gate.",
                        )
                picture = atom(event.text, "picture")
                if picture and not self.resolve_asset(picture):
                    self.error(path, event.line, f'Event picture "{picture}" cannot be resolved.')
                self.validate_dates(path, event, event_id)
                self.validate_commands(path, event, event_id, country)

    def validate_dates(self, path: pathlib.Path, event: Block, event_id: int | None) -> None:
        for key in ("date", "deathdate"):
            for date in find_blocks(event.text, key):
                day = integer(date.text, "day")
                month = (atom(date.text, "month") or "").lower()
                if day is None or not 0 <= day <= 29:
                    self.error(path, event.line + date.line - 1, f"Event {event_id or '?'} has invalid {key} day.")
                if month not in MONTHS:
                    self.error(
                        path,
                        event.line + date.line - 1,
                        f"Event {event_id or '?'} has invalid {key} month.",
                    )

    def ownership_is_gated(self, event_text: str, province: int, country: str) -> bool:
        trigger_blocks = find_blocks(event_text, "trigger") + find_blocks(event_text, "decision_trigger")
        pattern = re.compile(
            rf"\b(?:owned|control)\s*=\s*\{{[^}}]*\bprovince\s*=\s*{province}\b"
            rf"[^}}]*\bdata\s*=\s*(?:{re.escape(country)}|-1)\b",
            re.I | re.S,
        )
        return any(pattern.search(block.text) for block in trigger_blocks)

    def country_owns_or_is_gated(
        self,
        event_text: str,
        province: int,
        country: str,
    ) -> bool:
        starting_owned = self.starting_owned_by_tag.get(country)
        if starting_owned is None:
            return True
        return (
            province in starting_owned
            or self.ownership_is_gated(event_text, province, country)
        )

    def validate_province(
        self,
        path: pathlib.Path,
        line: int,
        province: int | None,
        context: str,
    ) -> bool:
        if province is None:
            self.error(path, line, f"{context} requires a numeric province.")
            return False
        if province not in self.provinces:
            self.error(path, line, f"{context} references unknown province {province}.")
            return False
        if context.startswith("Event") and province not in self.province_roles:
            self.error(
                path,
                line,
                f"{context} uses province {province} without a curated geographic role.",
            )
            return False
        return True

    def validate_commands(
        self,
        path: pathlib.Path,
        event: Block,
        event_id: int | None,
        country: str,
    ) -> None:
        previous_add_corps = False
        for command in find_blocks(event.text, "command"):
            command_line = event.line + command.line - 1
            command_type = (atom(command.text, "type") or "").lower()
            which = atom(command.text, "which")
            value = atom(command.text, "value")
            where = atom(command.text, "where")
            prefix = f"Event {event_id or '?'} {command_type or 'command'}"
            if not command_type:
                self.error(path, command_line, f"Event {event_id or '?'} has a command without type.")
                continue
            if command_type not in KNOWN_COMMAND_TYPES:
                self.error(path, command_line, f"{prefix} is not in the V3 documented-command allowlist.")

            if command_type == "construct":
                building = (which or "").lower()
                if building not in CONSTRUCTION_TYPES:
                    self.error(path, command_line, f"{prefix} has unknown building type {which!r}.")
                province = int(where) if where and re.fullmatch(r"-?\d+", where) else None
                if province in {-1, -4}:
                    pass
                elif self.validate_province(path, command_line, province, prefix):
                    assert province is not None
                    row = self.provinces[province]
                    if not self.country_owns_or_is_gated(
                        event.text,
                        province,
                        country,
                    ):
                        self.error(
                            path,
                            command_line,
                            f"{prefix} targets province {province} ({row['name']}) "
                            f"not owned by {country} without ownership/control gates.",
                        )
                    if building == "naval_base" and row["port_allowed"].strip().lower() not in {"1", "yes"}:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} targets inland province {province} ({row['name']}).",
                        )
                    if building == "coastal_fort" and row["beaches"].strip().lower() not in {"1", "yes"}:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} targets province {province} ({row['name']}) without a beach.",
                        )
                if value is None or not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                    self.error(path, command_line, f"{prefix} requires numeric value.")
                elif (
                    building in {"air_base", "naval_base"}
                    and float(value) > 0
                    and float(value) not in {3.0, 6.0, 10.0}
                ):
                    self.error(
                        path,
                        command_line,
                        f"{prefix} uses value={value}; V3 strategic bases must use "
                        "regional +3, major +6, or national +10 programmes.",
                    )

            elif command_type == "build_division":
                division = (which or "").lower()
                brigade = (value or "none").lower()
                if division not in self.divisions:
                    self.error(path, command_line, f"{prefix} has unknown division type {which!r}.")
                if brigade not in self.brigades:
                    self.error(path, command_line, f"{prefix} has unknown brigade type {value!r}.")
                elif brigade in self.disabled_brigades:
                    self.error(
                        path,
                        command_line,
                        f"{prefix} uses disabled brigade type {brigade!r}; "
                        "its missing display strings can crash unit tooltips.",
                    )
                if where is not None:
                    if not re.fullmatch(r"\d+", where):
                        self.error(path, command_line, f"{prefix} completion delay must be a non-negative integer.")
                    elif int(where) >= 1000:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} where={where} looks like a province id; here it means completion days.",
                        )
                    elif int(where) > 365:
                        self.error(path, command_line, f"{prefix} completion delay exceeds 365 days.")
                cost = atom(command.text, "cost")
                if cost is not None:
                    if not re.fullmatch(r"-?\d+(?:\.\d+)?", cost):
                        self.error(path, command_line, f"{prefix} cost must be numeric.")
                    elif float(cost) < -10:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} cost={cost} is an implausibly high fixed IC cost; "
                            "negative values are absolute costs, not percentages.",
                        )

            elif command_type == "add_corps":
                province = int(where) if where and re.fullmatch(r"\d+", where) else None
                if self.validate_province(path, command_line, province, prefix):
                    assert province is not None
                    if not self.country_owns_or_is_gated(
                        event.text,
                        province,
                        country,
                    ):
                        self.error(
                            path,
                            command_line,
                            f"{prefix} deploys to province {province} not owned by "
                            f"{country} without ownership/control gates.",
                        )
                if (value or "").lower() not in {"land", "air", "naval"}:
                    self.error(path, command_line, f"{prefix} value must be land, air, or naval.")
                previous_add_corps = True
                continue

            elif command_type == "add_division":
                division = (value or "").lower()
                if division not in self.divisions:
                    self.error(path, command_line, f"{prefix} has unknown division type {value!r}.")
                if where is not None:
                    brigade = where.lower()
                    damaged = re.fullmatch(r"-\d+", where)
                    if brigade not in self.brigades and not damaged:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} where={where!r} must be a brigade type or negative strength loss.",
                        )
                    elif brigade in self.disabled_brigades:
                        self.error(
                            path,
                            command_line,
                            f"{prefix} uses disabled brigade type {brigade!r}; "
                            "its missing display strings can crash unit tooltips.",
                        )
                    if re.fullmatch(r"\d+", where):
                        self.error(
                            path,
                            command_line,
                            f"{prefix} where={where} is not a deployment province; use add_corps first.",
                        )
                if not previous_add_corps:
                    self.warn(
                        path,
                        command_line,
                        f"{prefix} has no preceding add_corps and will enter the deployment pool.",
                    )
                continue

            elif command_type == "secedeprovince":
                province = int(value) if value and re.fullmatch(r"\d+", value) else None
                if self.validate_province(path, command_line, province, prefix):
                    assert province is not None
                    if not self.country_owns_or_is_gated(
                        event.text,
                        province,
                        country,
                    ):
                        self.error(
                            path,
                            command_line,
                            f"{prefix} transfers province {province}, which is not owned "
                            f"by {country}, without ownership/control gates.",
                        )
                if country and (which or "").upper() == country:
                    self.error(
                        path,
                        command_line,
                        f"{prefix} makes {country} secede a province to itself.",
                    )

            elif command_type == "add_prov_resource":
                province = int(which) if which and re.fullmatch(r"\d+", which) else None
                if self.validate_province(path, command_line, province, prefix):
                    assert province is not None
                    if not self.country_owns_or_is_gated(
                        event.text,
                        province,
                        country,
                    ):
                        self.error(
                            path,
                            command_line,
                            f"{prefix} targets province {province} not owned by "
                            f"{country} without ownership/control gates.",
                        )
                if (where or "").lower() not in RESOURCE_TYPES:
                    self.error(path, command_line, f"{prefix} has unknown resource type {where!r}.")
                if value is None or not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                    self.error(path, command_line, f"{prefix} requires numeric value.")

            elif command_type == "addcore":
                province = int(which) if which and re.fullmatch(r"\d+", which) else None
                self.validate_province(path, command_line, province, prefix)

            elif command_type == "gain_tech":
                tech = int(which) if which and re.fullmatch(r"\d+", which) else None
                if tech is None or tech not in self.tech_ids:
                    self.error(path, command_line, f"{prefix} references unknown technology {which!r}.")

            elif command_type == "activate_unit_type":
                unit_type = (which or "").lower()
                if unit_type not in self.divisions and unit_type not in self.brigades:
                    self.error(path, command_line, f"{prefix} references unknown unit type {which!r}.")

            elif command_type in {"max_organization", "morale"}:
                unit_type = (which or "").lower()
                if unit_type not in self.divisions and unit_type not in {"land", "air", "naval"}:
                    self.error(path, command_line, f"{prefix} references unknown unit type {which!r}.")
                if value is None or not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                    self.error(path, command_line, f"{prefix} requires numeric value.")

            elif command_type in {"waketeam", "sleepteam"}:
                team = int(which) if which and re.fullmatch(r"\d+", which) else None
                if team is None or team not in self.team_ids:
                    self.error(path, command_line, f"{prefix} references unknown IND tech team {which!r}.")

            elif command_type == "headofgovernment":
                minister = int(which) if which and re.fullmatch(r"\d+", which) else None
                if minister is None or minister not in self.minister_ids:
                    self.error(path, command_line, f"{prefix} references unknown IND minister {which!r}.")

            previous_add_corps = False

    def validate_trigger_targets(self) -> None:
        all_ids = set(self.v3_events)
        for event_id, (path, event) in self.v3_events.items():
            for command in find_blocks(event.text, "command"):
                if (atom(command.text, "type") or "").lower() != "trigger":
                    continue
                target = integer(command.text, "which")
                line = event.line + command.line - 1
                if target not in all_ids:
                    self.error(path, line, f"Event {event_id} triggers missing V3 event {target}.")
                    continue
                target_path, target_event = self.v3_events[target]
                if find_blocks(target_event.text, "date") or find_blocks(target_event.text, "deathdate"):
                    self.error(
                        path,
                        line,
                        f"Event {event_id} triggers dated event {target} in {target_path.name}; "
                        "trigger-only targets must have no date window.",
                    )

    def validate_path_exclusivity(self) -> None:
        path_groups = {
            "ind_v3_allied_orientation": "allied",
            "ind_v3_axis_orientation": "axis",
            "ind_v3_japanese_orientation": "japan",
            "ind_v3_soviet_orientation": "soviet",
            "ind_v3_non_aligned": "non-aligned",
            "ind_v3_independent_asia": "non-aligned",
        }
        for path, event in self.v3_events.values():
            event_id = integer(event.text, "id")
            for letter in "abcd":
                actions = find_blocks(event.text, f"action_{letter}")
                if not actions:
                    continue
                assigned_groups = set()
                for command in find_blocks(actions[0].text, "command"):
                    if (atom(command.text, "type") or "").lower() != "setflag":
                        continue
                    flag = (atom(command.text, "which") or "").lower()
                    if flag in path_groups:
                        assigned_groups.add(path_groups[flag])
                if len(assigned_groups) > 1:
                    self.error(
                        path,
                        actions[0].line,
                        f"Event {event_id} action_{letter} assigns incompatible strategic paths "
                        f"{sorted(assigned_groups)}.",
                    )

    def validate_flag_references(self) -> None:
        produced: set[str] = set()
        references: dict[str, tuple[pathlib.Path, int]] = {}
        for path, event in self.v3_events.values():
            for command in find_blocks(event.text, "command"):
                if (atom(command.text, "type") or "").lower() == "setflag":
                    flag = (atom(command.text, "which") or "").lower()
                    if flag.startswith("ind_v3_"):
                        produced.add(flag)
            clean = without_comments(event.text)
            for match in re.finditer(r"\bflag\s*=\s*(ind_v3_[a-z0-9_]+)", clean, re.I):
                flag = match.group(1).lower()
                references.setdefault(flag, (path, event.line + line_number(clean, match.start()) - 1))
        for flag in sorted(references.keys() - produced):
            path, line = references[flag]
            self.error(path, line, f'V3 trigger references flag "{flag}" that no V3 action sets.')

    def validate_scenario(self) -> None:
        eug = self.root / "scenarios" / "1933.eug"
        india = self.root / "scenarios" / "1933" / "british raj.inc"
        if not eug.exists() or not india.exists():
            self.error(india, 1, "1933 scenario files are missing.")
            return
        eug_text = without_comments(read_text(eug))
        india_text = read_text(india)
        if not balanced(eug_text):
            self.error(eug, 1, "Unbalanced braces or quotes.")
        if not balanced(india_text):
            self.error(india, 1, "Unbalanced braces or quotes.")
        if not re.search(r"\bselectable\s*=\s*\{[^}]*\bIND\b", eug_text, re.I | re.S):
            self.error(eug, 1, "IND is not selectable in the 1933 scenario.")
        if re.search(r"\bselectable\s*=\s*\{[^}]*\bU02\b", eug_text, re.I | re.S):
            self.error(eug, 1, "The obsolete British Raj tag U02 remains selectable.")
        start = re.search(r"\bglobaldata\s*=\s*\{.*?\bstartdate\s*=\s*\{([^}]*)\}", eug_text, re.I | re.S)
        if not start or integer(start.group(1), "year") != 1933 or atom(start.group(1), "month") != "january" or integer(start.group(1), "day") != 0:
            self.error(eug, 1, "V3 must begin on 1 January 1933 (day = 0).")

        countries = find_top_level_blocks(india_text, "country")
        if len(countries) != 1:
            self.error(india, 1, f"Expected one India country block; found {len(countries)}.")
            return
        country = countries[0]
        if (atom(country.text, "tag") or "").upper() != "IND":
            self.error(india, country.line, "V3 country tag must be IND.")
        for forbidden in ("puppet", "regular_id"):
            if atom(country.text, forbidden) is not None:
                self.error(india, country.line, f"Independent India must not define {forbidden}.")
        self.ind_owned = scenario_list(country.text, "ownedprovinces")
        self.ind_controlled = scenario_list(country.text, "controlledprovinces")
        nationals = scenario_list(country.text, "nationalprovinces")
        if self.ind_owned != self.ind_controlled:
            self.error(india, country.line, "Starting ownedprovinces and controlledprovinces differ.")
        if not self.ind_owned.issubset(nationals):
            missing = sorted(self.ind_owned - nationals)
            self.error(india, country.line, f"Owned provinces missing from nationalprovinces: {missing}.")
        if {1509, 1510, 1511, 1513} & self.ind_owned:
            self.error(india, country.line, "V3 starting borders must not include Ceylon or Portuguese Goa.")
        if 1459 not in self.ind_owned or integer(country.text, "capital") != 1459:
            self.error(india, country.line, "Delhi (1459) must be the owned starting capital.")

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
            role_block = find_blocks(country.text, role)
            minister = integer(role_block[0].text, "id") if role_block else None
            if minister is None or minister not in self.minister_ids:
                self.error(india, country.line, f"{role} references unknown IND minister {minister}.")
            elif minister in self.minister_pictures:
                self.inspect_bmp(
                    india,
                    country.line,
                    self.minister_pictures[minister],
                    (36, 50, 8),
                    "Minister",
                )

        self.validate_scenario_ownership(eug)
        self.validate_india_units(india, country)

    def validate_scenario_ownership(self, eug: pathlib.Path) -> None:
        owners: dict[int, list[tuple[str, pathlib.Path]]] = defaultdict(list)
        eug_text = without_comments(read_text(eug))
        includes = re.findall(r'^\s*include\s*=\s*"(scenarios\\1933\\[^"]+\.inc)"', eug_text, re.I | re.M)
        for raw in includes:
            path = self.root / normalize_game_path(raw)
            if not path.exists():
                self.error(eug, 1, f"Scenario include is missing: {raw}.")
                continue
            text = read_text(path)
            for country in find_top_level_blocks(text, "country"):
                tag = (atom(country.text, "tag") or "").upper()
                owned = scenario_list(country.text, "ownedprovinces")
                self.starting_owned_by_tag[tag].update(owned)
                for province in owned:
                    owners[province].append((tag, path))
        for province, entries in owners.items():
            if len(entries) > 1:
                detail = ", ".join(f"{tag}:{path.name}" for tag, path in entries)
                self.error(eug, 1, f"Province {province} has multiple scenario owners: {detail}.")

    def validate_india_units(self, path: pathlib.Path, country: Block) -> None:
        unit_ids: set[tuple[int, int]] = set()
        for kind in ("landunit", "airunit", "navalunit"):
            for unit in find_blocks(country.text, kind):
                line = country.line + unit.line - 1
                location = integer(unit.text, "location")
                if not self.validate_province(path, line, location, f"Starting {kind}"):
                    continue
                if location not in self.ind_controlled:
                    self.error(path, line, f"Starting {kind} is outside controlled India at province {location}.")
                for id_block in find_blocks(unit.text, "id"):
                    id_type = integer(id_block.text, "type")
                    id_value = integer(id_block.text, "id")
                    if id_type is None or id_value is None:
                        self.error(path, line, f"Starting {kind} has malformed object id.")
                    elif (id_type, id_value) in unit_ids:
                        self.error(path, line, f"Duplicate starting object id {id_type}:{id_value}.")
                    else:
                        unit_ids.add((id_type, id_value))
                expected = {
                    "landunit": "land",
                    "airunit": "air",
                    "navalunit": "naval",
                }[kind]
                for division in find_blocks(unit.text, "division"):
                    without_id = re.sub(r"\bid\s*=\s*\{[^}]*\}", "", division.text, flags=re.I | re.S)
                    division_type = (atom(without_id, "type") or "").lower()
                    if division_type not in self.divisions:
                        self.error(path, line, f"Starting {expected} unit has unknown division type {division_type!r}.")

    def validate_tech_teams(self) -> None:
        path = self.root / "db" / "tech" / "teams" / "teams_ind.csv"
        if not path.exists():
            self.error(path, 1, "IND tech-team file is missing.")
            return
        rows: list[list[str]] = []
        with path.open(encoding="cp1252", errors="replace", newline="") as stream:
            rows = [row for row in csv.reader(stream, delimiter=";") if row and row[0].isdigit()]
        team_specialities: dict[int, set[str]] = {}
        for line, row in enumerate(rows, start=2):
            team_id = int(row[0])
            if team_id in self.team_ids:
                self.error(path, line, f"Duplicate IND tech-team id {team_id}.")
            self.team_ids.add(team_id)
            if len(row) < 6:
                self.error(path, line, f"Malformed tech-team row {team_id}.")
                continue
            team_specialities[team_id] = {
                item.lower() for item in row[6:-1] if item
            }
            for speciality in (item for item in row[6:-1] if item):
                if speciality.lower() not in self.tech_specialities:
                    self.error(path, line, f'Tech team {team_id} uses unknown speciality "{speciality}".')
            picture = row[2]
            local_asset = self.root / "gfx" / "interface" / "pics" / f"{pathlib.Path(picture).stem}.bmp"
            if not local_asset.exists():
                self.error(path, line, f'Tech-team portrait "{picture}" is not packaged inside V3.')
            asset = self.resolve_asset(picture)
            if not asset:
                self.error(path, line, f'Tech-team portrait "{picture}" cannot be resolved.')
                continue
            try:
                header = asset.read_bytes()[:30]
                if len(header) < 30 or header[:2] != b"BM":
                    raise ValueError("not a BMP")
                width, height = struct.unpack_from("<ii", header, 18)
                bits = struct.unpack_from("<H", header, 28)[0]
                if (width, abs(height), bits) != (96, 96, 8):
                    self.error(
                        path,
                        line,
                        f"Portrait {asset.name} must be 96x96 indexed 8-bit BMP; "
                        f"found {width}x{abs(height)} {bits}-bit.",
                    )
            except (OSError, ValueError, struct.error) as exc:
                self.error(path, line, f"Cannot inspect portrait {asset}: {exc}.")
        if len(rows) < 12:
            self.error(path, 1, "V3 requires at least 12 curated IND tech teams.")

        required_coverage = {
            250004: {"vehicle_engineering"},
            250006: {"submarine_design"},
            250008: {
                "aeronautics",
                "aircraft_testing",
                "fighter_design",
                "bomber_design",
                "avionics",
            },
            250023: {"marine_training"},
            250024: {"submarine_design"},
            250025: {"airborne_training"},
            250026: {"maneuver_tactics", "blitzkrieg_tactics"},
            250027: {"infantry_focus", "mountain_training", "maneuver_tactics"},
            250031: {"medicine", "chemistry"},
        }
        for team_id, required in required_coverage.items():
            missing = required - team_specialities.get(team_id, set())
            if missing:
                self.error(
                    path,
                    1,
                    f"Tech team {team_id} is missing required B&I coverage {sorted(missing)}.",
                )

        applications: list[tuple[int, list[str]]] = []
        for tech_path in (self.root / "db" / "tech").glob("*.txt"):
            for application in find_blocks(read_text(tech_path), "application"):
                year = integer(application.text, "year")
                components = [
                    (atom(component.text, "type") or "").lower()
                    for component in find_blocks(application.text, "component")
                ]
                if year is not None and components:
                    applications.append((year, components))

        phases = {
            1933: (list(range(250001, 250013)) + [250027, 250031], 0.85),
            1934: (list(range(250001, 250013)) + [250025, 250027, 250031], 0.88),
            1936: (list(range(250001, 250028)) + [250031], 0.95),
            1944: (list(range(250001, 250032)), 0.96),
        }
        for year, (team_ids, minimum_ratio) in phases.items():
            contemporary = [
                components
                for tech_year, components in applications
                if year - 1 <= tech_year <= year + 1
            ]
            covered = 0
            for components in contemporary:
                best_match = max(
                    (
                        sum(
                            component in team_specialities.get(team_id, set())
                            for component in components
                        )
                        for team_id in team_ids
                    ),
                    default=0,
                )
                covered += best_match >= 3
            ratio = covered / len(contemporary) if contemporary else 0
            if ratio < minimum_ratio:
                self.error(
                    path,
                    1,
                    f"{year} B&I tech coverage is {covered}/{len(contemporary)} "
                    f"({ratio:.1%}); expected at least {minimum_ratio:.0%} with three matching components.",
                )

    def inspect_bmp(
        self,
        source_path: pathlib.Path,
        source_line: int,
        picture: str,
        expected: tuple[int, int, int],
        kind: str,
    ) -> None:
        asset = self.resolve_asset(picture)
        if not asset:
            self.error(source_path, source_line, f'{kind} portrait "{picture}" cannot be resolved.')
            return
        try:
            header = asset.read_bytes()[:30]
            if len(header) < 30 or header[:2] != b"BM":
                raise ValueError("not a BMP")
            width, height = struct.unpack_from("<ii", header, 18)
            bits = struct.unpack_from("<H", header, 28)[0]
            actual = (width, abs(height), bits)
            if actual != expected:
                self.error(
                    source_path,
                    source_line,
                    f"{kind} portrait {asset.name} must be {expected[0]}x{expected[1]} "
                    f"indexed {expected[2]}-bit BMP; found {actual[0]}x{actual[1]} {actual[2]}-bit.",
                )
        except (OSError, ValueError, struct.error) as exc:
            self.error(source_path, source_line, f"Cannot inspect {kind.lower()} portrait {asset}: {exc}.")

    def validate_leaders(self) -> None:
        path = self.root / "db" / "leaders" / "india.csv"
        if not path.exists():
            self.error(path, 1, "IND leader file is missing.")
            return
        seen: set[int] = set()
        early_by_type: dict[int, int] = defaultdict(int)
        with path.open(encoding="cp1252", errors="replace", newline="") as stream:
            rows = list(csv.reader(stream, delimiter=";"))
        for line, row in enumerate(rows[1:], start=2):
            if len(row) < 18 or not row[1].isdigit():
                continue
            leader_id = int(row[1])
            if leader_id in seen:
                self.error(path, line, f"Duplicate IND leader id {leader_id}.")
            seen.add(leader_id)
            if row[2].upper() != "IND":
                self.error(path, line, f"Leader {leader_id} has country {row[2]!r}, expected IND.")
            try:
                max_skill = int(row[8])
                leader_type = int(row[13])
                start_year = int(row[15])
                end_year = int(row[16])
            except ValueError:
                self.error(path, line, f"Leader {leader_id} has malformed numeric fields.")
                continue
            if not 1 <= max_skill <= 9:
                self.error(path, line, f"Leader {leader_id} has invalid maximum skill {max_skill}.")
            if leader_type not in {0, 1, 2}:
                self.error(path, line, f"Leader {leader_id} has invalid service type {leader_type}.")
            if start_year > end_year:
                self.error(path, line, f"Leader {leader_id} starts after retirement.")
            if start_year <= 1938:
                early_by_type[leader_type] += 1
            self.inspect_bmp(path, line, row[14], (36, 50, 8), "Leader")
        if early_by_type[0] < 8 or early_by_type[1] < 1 or early_by_type[2] < 1:
            self.error(
                path,
                1,
                "1938 leader roster must include at least 8 land, 1 naval and 1 air leader; "
                f"found {dict(early_by_type)}.",
            )

    def validate_v32_art_provenance(self) -> None:
        if not V32_ART_MANIFEST_PATH.exists():
            self.error(V32_ART_MANIFEST_PATH, 1, "V3.2 art manifest is missing.")
            return
        with V32_ART_MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
            art_rows = list(csv.DictReader(stream))
        expected_counts = {"event": 28, "inherited_event": 4, "tech_team": 31}
        actual_counts = Counter(row["kind"] for row in art_rows)
        if actual_counts != Counter(expected_counts):
            self.error(
                V32_ART_MANIFEST_PATH,
                1,
                f"V3.2 art counts are {dict(actual_counts)}; expected {expected_counts}.",
            )
        assets = [row["asset"] for row in art_rows]
        if len(assets) != len(set(asset.casefold() for asset in assets)):
            self.error(V32_ART_MANIFEST_PATH, 1, "V3.2 art manifest contains duplicate assets.")
        rendered_hashes: dict[str, str] = {}
        for line, row in enumerate(art_rows, start=2):
            output = self.root / pathlib.PurePosixPath(row["output"])
            # Authoring sources are intentionally excluded from the playable
            # deployment; the manifest and validator remain in the source tree.
            source = SOURCE_ROOT / pathlib.PurePosixPath(row["source"])
            if not source.exists():
                self.error(V32_ART_MANIFEST_PATH, line, f"Art source is missing: {row['source']}.")
            if not output.exists():
                self.error(V32_ART_MANIFEST_PATH, line, f"Rendered art is missing: {row['output']}.")
                continue
            actual_hash = hashlib.sha256(output.read_bytes()).hexdigest()
            if actual_hash != row["sha256"]:
                self.error(
                    V32_ART_MANIFEST_PATH,
                    line,
                    f"{row['asset']} hash does not match its packaged output.",
                )
            prior = rendered_hashes.get(actual_hash)
            if prior:
                self.error(
                    V32_ART_MANIFEST_PATH,
                    line,
                    f"{row['asset']} duplicates the rendered bytes of {prior}.",
                )
            rendered_hashes[actual_hash] = row["asset"]
            if not row["provenance"].strip():
                self.error(V32_ART_MANIFEST_PATH, line, f"{row['asset']} has no provenance.")
            if row["kind"] == "tech_team":
                expected_prefix = "tools/art_sources/tech_teams/"
                if not row["source"].replace("\\", "/").startswith(expected_prefix):
                    self.error(
                        V32_ART_MANIFEST_PATH,
                        line,
                        f"{row['asset']} still reuses a packaged game donor instead of a custom source.",
                    )
                if row["provenance"] != "generated original":
                    self.error(
                        V32_ART_MANIFEST_PATH,
                        line,
                        f"{row['asset']} is not labelled as a generated original.",
                    )

        teams_path = self.root / "db" / "tech" / "teams" / "teams_ind.csv"
        with teams_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            expected_teams = {
                row[2]
                for row in csv.reader(stream, delimiter=";")
                if row and row[0].isdigit()
            }
        manifested_teams = {
            row["asset"] for row in art_rows if row["kind"] == "tech_team"
        }
        if manifested_teams != expected_teams:
            self.error(
                V32_ART_MANIFEST_PATH,
                1,
                "Tech-team art manifest does not exactly cover the IND tech-team picture namespace.",
            )

        expected_event_art = {
            picture
            for _event_id, (_path, event) in self.v3_events.items()
            if (picture := atom(event.text, "picture"))
            and picture.casefold().startswith("india_v3_")
        }
        manifested_event_art = {
            row["asset"] for row in art_rows if row["kind"] == "event"
        }
        if manifested_event_art != expected_event_art:
            self.error(
                V32_ART_MANIFEST_PATH,
                1,
                "Custom V3 event art manifest does not exactly cover custom event pictures.",
            )

        if not PERSONNEL_ART_MANIFEST_PATH.exists():
            self.error(PERSONNEL_ART_MANIFEST_PATH, 1, "Personnel art manifest is missing.")
            return
        with PERSONNEL_ART_MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
            personnel_rows = list(csv.DictReader(stream))
        personnel_assets = [row["asset"] for row in personnel_rows]
        if len(personnel_assets) != len(set(asset.casefold() for asset in personnel_assets)):
            self.error(PERSONNEL_ART_MANIFEST_PATH, 1, "Personnel art manifest has duplicate assets.")

        expected_personnel: set[str] = set()
        ministers_path = self.root / "db" / "ministers" / "ministers_ind.csv"
        with ministers_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if row and row[0].isdigit() and int(row[0]) >= 251001:
                    expected_personnel.add(row[9])
        leaders_path = self.root / "db" / "leaders" / "india.csv"
        with leaders_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if len(row) > 14 and row[1].isdigit() and int(row[1]) >= 251001:
                    expected_personnel.add(row[14])
        if set(personnel_assets) != expected_personnel:
            self.error(
                PERSONNEL_ART_MANIFEST_PATH,
                1,
                "Personnel manifest does not exactly cover all V3 minister and leader portraits.",
            )

        personnel_hashes: dict[str, str] = {}
        for line, row in enumerate(personnel_rows, start=2):
            asset = self.root / "gfx" / "interface" / "pics" / f"{row['asset']}.bmp"
            if not asset.exists():
                self.error(PERSONNEL_ART_MANIFEST_PATH, line, f"Personnel portrait is missing: {asset.name}.")
                continue
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()
            prior = personnel_hashes.get(digest)
            if prior:
                self.error(
                    PERSONNEL_ART_MANIFEST_PATH,
                    line,
                    f"{row['asset']} duplicates the rendered bytes of {prior}.",
                )
            personnel_hashes[digest] = row["asset"]
            if not row["person"].strip() or not row["provenance"].strip() or not row["license"].strip():
                self.error(
                    PERSONNEL_ART_MANIFEST_PATH,
                    line,
                    f"{row['asset']} lacks person, provenance or license metadata.",
                )
            if row["license"].strip().upper().startswith("CC") and (
                not row.get("artist", "").strip()
                or not row.get("credit", "").strip()
            ):
                self.error(
                    PERSONNEL_ART_MANIFEST_PATH,
                    line,
                    f"{row['asset']} lacks complete Creative Commons attribution.",
                )
            self.inspect_bmp(
                PERSONNEL_ART_MANIFEST_PATH,
                line,
                row["asset"],
                (36, 50, 8),
                "Personnel",
            )

    def validate_historical_traits(self) -> None:
        if not HISTORICAL_TRAITS_PATH.exists():
            self.error(HISTORICAL_TRAITS_PATH, 1, "Historical trait manifest is missing.")
            return
        with HISTORICAL_TRAITS_PATH.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        records = {(row["kind"], row["id"]): row for row in rows}
        if len(records) != len(rows):
            self.error(HISTORICAL_TRAITS_PATH, 1, "Historical trait manifest has duplicate kind/id records.")

        expected: dict[tuple[str, str], tuple[str, str]] = {}
        ministers_path = self.root / "db" / "ministers" / "ministers_ind.csv"
        with ministers_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if row and row[0].isdigit() and int(row[0]) >= 251001:
                    expected[("minister", row[0])] = (
                        row[2],
                        f"{row[1]} | {row[7]} | {row[6]}",
                    )

        land_traits = {
            1: "Logistics Wizard",
            2: "Defensive Doctrine",
            4: "Offensive Doctrine",
            8: "Winter Specialist",
            16: "Trickster",
            32: "Engineer",
            64: "Panzer Leader",
            128: "Commando",
            256: "Old Guard",
        }
        naval_traits = {
            1024: "Blockade Runner",
            2048: "Spotter",
            4096: "Superior Tactician",
            8192: "Sea Wolf",
        }
        air_traits = {
            4096: "Superior Tactician",
            8192: "Spotter",
            16384: "Tank Buster",
            32768: "Carpet Bomber",
            65536: "Night Flyer",
            131072: "Fleet Destroyer",
        }
        trait_maps = (land_traits, naval_traits, air_traits)
        leaders_path = self.root / "db" / "leaders" / "india.csv"
        with leaders_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if len(row) < 18 or not row[1].isdigit() or int(row[1]) < 251001:
                    continue
                service = int(row[13])
                mask = int(row[9])
                traits = ", ".join(
                    name for bit, name in trait_maps[service].items() if mask & bit
                ) or "None"
                assignment = (
                    f"{('land', 'naval', 'air')[service]} | max skill {row[8]} | "
                    f"{traits} | available {row[15]}"
                )
                expected[("leader", row[1])] = (row[0], assignment)

        teams_path = self.root / "db" / "tech" / "teams" / "teams_ind.csv"
        with teams_path.open(encoding="cp1252", errors="replace", newline="") as stream:
            for row in csv.reader(stream, delimiter=";"):
                if not row or not row[0].isdigit():
                    continue
                specialities = ", ".join(item for item in row[6:-1] if item)
                expected[("tech_team", row[0])] = (
                    row[1],
                    f"skill {row[3]} | {specialities} | available {int(row[4])}",
                )

        if set(records) != set(expected):
            self.error(
                HISTORICAL_TRAITS_PATH,
                1,
                f"Historical trait coverage is {len(records)} records; expected exactly {len(expected)} current records.",
            )
        for key, (expected_name, expected_assignment) in expected.items():
            row = records.get(key)
            if not row:
                continue
            if row["name"] != expected_name:
                self.error(
                    HISTORICAL_TRAITS_PATH,
                    1,
                    f"{key[0]} {key[1]} is documented as {row['name']!r}, expected {expected_name!r}.",
                )
            if row["game_assignment"] != expected_assignment:
                self.error(
                    HISTORICAL_TRAITS_PATH,
                    1,
                    f"{key[0]} {key[1]} historical record is stale relative to the game assignment.",
                )
            for field in ("historical_basis", "alt_history_embellishment", "source_url"):
                if not row[field].strip():
                    self.error(
                        HISTORICAL_TRAITS_PATH,
                        1,
                        f"{key[0]} {key[1]} has no {field.replace('_', ' ')}.",
                    )

    def validate_ai(self) -> None:
        scenario = self.root / "scenarios" / "1933" / "british raj.inc"
        scenario_text = read_text(scenario)
        ai_name = atom(scenario_text, "ai")
        if not ai_name:
            self.error(scenario, 1, "IND scenario has no AI file.")
            return
        normalized_ai = normalize_game_path(ai_name)
        path = self.root / normalized_ai
        if not path.exists():
            path = self.root / "ai" / normalized_ai
        if not path.exists():
            self.error(scenario, 1, f"IND AI file is missing: {ai_name}.")
            return
        text = read_text(path)
        if not balanced(text):
            self.error(path, 1, "Unbalanced braces or quotes.")
            return
        military = find_top_level_blocks(text, "military")
        if len(military) != 1:
            self.error(path, 1, f"Expected one military AI block; found {len(military)}.")
            return
        division_names = {
            "infantry",
            "cavalry",
            "motorized",
            "mechanized",
            "light_armor",
            "armor",
            "paratrooper",
            "marine",
            "bergsjaeger",
            "garrison",
            "hq",
            "militia",
            "interceptor",
            "multi_role",
            "cas",
            "strategic_bomber",
            "tactical_bomber",
            "naval_bomber",
            "transport_plane",
            "flying_bomb",
            "flying_rocket",
            "battleship",
            "carrier",
            "light_carrier",
            "escort_carrier",
            "destroyer",
            "light_cruiser",
            "heavy_cruiser",
            "battlecruiser",
            "submarine",
            "nuclear_submarine",
            "transports",
        }
        assignments = {
            match.group(1).lower(): float(match.group(2))
            for match in re.finditer(
                r"^\s*([a-z_]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*$",
                without_comments(military[0].text),
                re.I | re.M,
            )
        }
        division_total = sum(assignments.get(name, 0) for name in division_names)
        if abs(division_total - 100) > 0.01:
            self.error(path, military[0].line, f"AI division build ratios sum to {division_total}, expected 100.")
        if assignments.get("infantry", 0) < 15:
            self.error(path, military[0].line, "AI infantry build ratio is too low for continental defence.")

        construction = find_top_level_blocks(text, "construction")
        if len(construction) != 1:
            self.error(path, 1, f"Expected one construction AI block; found {len(construction)}.")
        else:
            for field in (
                "AA_provs",
                "coastal_fort_provs",
                "radar_provs",
                "air_base_provs",
                "naval_base_provs",
                "IC_provs",
            ):
                for province in scenario_list(construction[0].text, field):
                    if province not in self.ind_owned:
                        self.error(path, construction[0].line, f"{field} uses non-owned province {province}.")
                    if province not in self.province_roles:
                        self.error(path, construction[0].line, f"{field} province {province} has no curated role.")
                    if field == "coastal_fort_provs":
                        row = self.provinces.get(province)
                        if row and row["beaches"].strip().lower() not in {"1", "yes"}:
                            self.error(
                                path,
                                construction[0].line,
                                f"{field} province {province} ({row['name']}) has no beach.",
                            )

        event_dir = self.root / V3_EVENT_PREFIX
        referenced_switches: set[pathlib.Path] = set()
        for event_path in event_dir.glob("*.txt"):
            event_text = without_comments(read_text(event_path))
            for match in re.finditer(
                r"\btype\s*=\s*ai\b[^}]*?\bwhich\s*=\s*\"([^\"]+\.ai)\"",
                event_text,
                re.I | re.S,
            ):
                referenced_switches.add(self.root / "ai" / normalize_game_path(match.group(1)))

        for switch_path in sorted(referenced_switches):
            if not switch_path.exists():
                self.error(switch_path, 1, "Event-referenced AI switch file is missing.")
                continue
            switch_text = read_text(switch_path)
            if not balanced(switch_text):
                self.error(switch_path, 1, "AI switch has unbalanced braces or quotes.")
                continue
            switch_military = find_top_level_blocks(switch_text, "military")
            if len(switch_military) > 1:
                self.error(switch_path, 1, "AI switch contains multiple military blocks.")
            elif switch_military:
                switch_assignments = {
                    match.group(1).lower(): float(match.group(2))
                    for match in re.finditer(
                        r"^\s*([a-z_]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*$",
                        without_comments(switch_military[0].text),
                        re.I | re.M,
                    )
                }
                switch_total = sum(switch_assignments.get(name, 0) for name in division_names)
                if abs(switch_total - 100) > 0.01:
                    self.error(
                        switch_path,
                        switch_military[0].line,
                        f"AI switch division build ratios sum to {switch_total}, expected 100.",
                    )

    def validate_contamination(self) -> None:
        uk = self.root / "db" / "events" / "UK.txt"
        if uk.exists() and "STABLE UNITED INDIA START" in read_text(uk):
            self.error(uk, 1, "Legacy Stable United India start block remains in the baseline.")
        old = self.root / "db" / "events" / "india_overhaul.txt"
        if old.exists():
            loader = read_text(self.root / "db" / "events.txt")
            if re.search(r'india_overhaul\.txt', loader, re.I):
                self.error(old, 1, "Legacy India overhaul is still loaded.")

    def validate_v3_visuals(self) -> None:
        scenario_picture = self.root / "scenarios" / "data" / "propaganda_IND_V3.bmp"
        event_picture_dir = self.root / "gfx" / "events_pics"
        founding_candidates = [event_picture_dir / "india_v3_independence.bmp"]
        founding_picture = next(
            (path for path in founding_candidates if path.exists()),
            founding_candidates[0],
        )
        event_pictures = [
            founding_picture,
            event_picture_dir / "india_v3_industry.bmp",
            event_picture_dir / "india_v3_armed_forces.bmp",
        ]
        requirements = [(scenario_picture, (256, 256, 24))]
        requirements.extend((path, (400, 116, 24)) for path in event_pictures)
        for path, expected in requirements:
            if not path.exists():
                self.error(path, 1, "Required V3 visual asset is missing.")
                continue
            try:
                header = path.read_bytes()[:30]
                if len(header) < 30 or header[:2] != b"BM":
                    raise ValueError("not a BMP")
                width, height = struct.unpack_from("<ii", header, 18)
                bits = struct.unpack_from("<H", header, 28)[0]
                actual = (width, abs(height), bits)
                if actual != expected:
                    self.error(path, 1, f"V3 asset must be {expected}; found {actual}.")
            except (OSError, ValueError, struct.error) as exc:
                self.error(path, 1, f"Cannot inspect V3 visual asset: {exc}.")

        eug = self.root / "scenarios" / "1933.eug"
        eug_text = read_text(eug)
        if not re.search(
            r'\bIND\s*=\s*\{[^}]*picture\s*=\s*"scenarios\\data\\propaganda_IND_V3\.bmp"',
            eug_text,
            re.I | re.S,
        ):
            self.error(eug, 1, "IND scenario header does not use the V3 propaganda artwork.")

    def validate_model_bmps(self) -> None:
        model_dir = self.root / "gfx" / "interface" / "models"
        for path in model_dir.glob("*.bmp"):
            relative = path.relative_to(self.root)
            baseline = self.baseline_root / relative
            is_india_asset = path.name.casefold().startswith(
                ("ind_model_", "ill_div_ind_")
            )
            if (
                not is_india_asset
                and baseline.exists()
                and path.read_bytes() == baseline.read_bytes()
            ):
                continue
            try:
                header = path.read_bytes()[:30]
                if len(header) < 30 or header[:2] != b"BM":
                    raise ValueError("not a BMP")
                bits = struct.unpack_from("<H", header, 28)[0]
                if bits not in {8, 24}:
                    self.error(path, 1, f"Model BMP uses unsupported {bits}-bit pixels; expected 8 or 24.")
            except (OSError, ValueError, struct.error) as exc:
                self.error(path, 1, f"Cannot inspect model BMP: {exc}.")

    def validate_revolt_definitions(self) -> None:
        path = self.root / "db" / "revolt.txt"
        if not path.exists():
            self.error(path, 1, "Revolt definitions are missing.")
            return
        text = read_text(path)
        if not balanced(text):
            self.error(path, 1, "Unbalanced revolt-definition braces or quotes.")
            return
        tags = set(
            re.findall(
                r"^\s*([A-Z0-9]{3})\s*=\s*\{",
                without_comments(text),
                re.M,
            )
        )
        for tag in sorted(tags):
            for block in find_top_level_blocks(text, tag):
                minimum = scenario_list(block.text, "minimum")
                extra = scenario_list(block.text, "extra")
                claims = scenario_list(block.text, "claims")
                overlaps = {
                    "minimum/extra": minimum & extra,
                    "minimum/claims": minimum & claims,
                    "extra/claims": extra & claims,
                }
                for lists, provinces in overlaps.items():
                    if provinces:
                        self.error(
                            path,
                            block.line,
                            f"Revolter {tag} repeats provinces {sorted(provinces)} across {lists}.",
                        )

    def run(self) -> int:
        self.load_registry()
        self.validate_india_names()
        self.validate_province_overrides()
        self.validate_tech_teams()
        self.validate_scenario()
        self.validate_leaders()
        self.validate_ai()
        self.validate_v3_visuals()
        self.validate_india_visual_namespace()
        self.validate_model_bmps()
        self.validate_revolt_definitions()
        v3_files = self.validate_required_structure()
        loaded = self.loaded_event_files()
        self.validate_event_ids(loaded, v3_files)
        self.validate_loaded_event_assets(loaded)
        self.validate_loaded_calendar_days(loaded)
        self.validate_dormant_ministers()
        self.validate_india_minister_file()
        self.validate_events(v3_files)
        self.validate_v32_art_provenance()
        self.validate_historical_traits()
        self.validate_fleet_doctrine()
        self.validate_trigger_targets()
        self.validate_path_exclusivity()
        self.validate_flag_references()
        self.validate_contamination()

        self.issues.sort(key=lambda item: (item.severity != "ERROR", str(item.path), item.line, item.message))
        for issue in self.issues:
            print(f"{issue.severity}: {issue.path}:{issue.line}: {issue.message}")
        errors = sum(issue.severity == "ERROR" for issue in self.issues)
        warnings = sum(issue.severity == "WARN" for issue in self.issues)
        print()
        print(f"India Mod V3 validation: {errors} error(s), {warnings} warning(s)")
        if errors:
            print("BUILD BLOCKED")
            return 1
        print("BUILD PASSED")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=SOURCE_ROOT)
    args = parser.parse_args()
    return Validator(args.root).run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VALIDATOR FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
