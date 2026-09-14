#!/usr/bin/env python3
"""Validate AUBM reserved special units and capital-ship contracts."""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import struct
import sys
from dataclasses import dataclass


SLOTS = tuple(range(33, 41))
EVENT_FILE = pathlib.Path("mod/db/events/aubm_v4/40_special_units_and_capital_ships.txt")
SOURCE_COLUMNS = {
    33: "MTN",
    34: "MTN",
    35: "MTN",
    36: "PARA",
    37: "MAR",
    38: "ARM",
    39: "MOT",
    40: "INF",
}
COUNTER_SOURCES = {33: 8, 34: 8, 35: 8, 36: 6, 37: 7, 38: 5, 39: 2, 40: 0}
PUBLIC_SPRITE_KEYS = {
    33: "bergsjaeger",
    34: "bergsjaeger",
    35: "bergsjaeger",
    36: "paratrooper",
    37: "marine",
    38: "panzer",
    39: "motorized",
    40: "infantry",
}
PERSONAL_SPRITE_KEYS = {slot: f"d_{slot + 41}" for slot in SLOTS}
DEPLOYMENT_PROVINCES = {slot: (1451 if slot == 33 else 1459) for slot in SLOTS}
LOCALIZATION_BEGIN = "# AUBM SPECIAL UNIT LOCALIZATION BEGIN;;;;;;;;;;;X"
LOCALIZATION_END = "# AUBM SPECIAL UNIT LOCALIZATION END;;;;;;;;;;;X"


@dataclass(frozen=True)
class SpecialUnit:
    event_id: int
    technology: int
    manpower: int
    unit_name_key: str
    base_type: str
    min_cost: float
    max_cost: float


SPECIAL_UNITS = {
    33: SpecialUnit(9281800, 1240, 11, "AUBM_NAME_GURKHA_RIFLES", "bergsjaeger", 6, 9),
    34: SpecialUnit(9281801, 1240, 10, "AUBM_NAME_FRONTIER_FORCE", "bergsjaeger", 6, 9),
    35: SpecialUnit(9281802, 1100, 9, "AUBM_NAME_CHINDIT_COLUMNS", "bergsjaeger", 7, 10),
    36: SpecialUnit(9281803, 1670, 9, "AUBM_NAME_INDIAN_AIRBORNE", "paratrooper", 9, 13),
    37: SpecialUnit(9281804, 1590, 13, "AUBM_NAME_COROMANDEL_MARINES", "marine", 8, 11),
    38: SpecialUnit(9281805, 2070, 8, "AUBM_NAME_GUARDS_ARMOUR", "armor", 20, 27),
    39: SpecialUnit(9281806, 1396, 12, "AUBM_NAME_GUARDS_MOTORISED", "motorized", 14, 19),
    40: SpecialUnit(9281807, 1860, 10, "AUBM_NAME_INDIAN_PIONEERS", "infantry", 6, 9),
}
SHBB_EVENTS = {9281880: "INS Meru", 9281881: "INS Trikuta"}
DOCTRINE_MIGRATION_EVENT = 9281808
MODEL_TECHS = {
    33: ((1270,), (1280,), (1300,), (13040,)),
    34: ((1270,), (1280,), (1300,), (13040,)),
    35: ((1270,), (1280,), (1300,), (13040,)),
    36: ((1680,), (1690,), (1710,), (1730,)),
    37: ((1600,), (1610,), (1630,), (1650,)),
    38: ((2080,), (2090,), (2140,), (2660,), (2670,)),
    39: ((1400,), (1410,), (1420,), (1440,), (1460,)),
    40: ((1110, 1870), (1130, 1880), (1150, 1890), (13010, 1900)),
}
MODEL_COUNTS = {slot: len(stages) + 1 for slot, stages in MODEL_TECHS.items()}
DOCTRINE_CONTRACTS = {
    9281800: (
        "ind_aubm_gurkha_doctrine",
        "mountain_attack which = d_rsv_33 value = 20",
        "mountain_defense which = d_rsv_33 value = 25",
        "hill_attack which = d_rsv_33 value = 15",
    ),
    9281801: (
        "ind_aubm_frontier_doctrine",
        "mountain_move which = d_rsv_34 value = 20",
        "hill_defense which = d_rsv_34 value = 15",
        "desert_move which = d_rsv_34 value = 15",
    ),
    9281802: (
        "ind_aubm_chindit_doctrine",
        "jungle_attack which = d_rsv_35 value = 25",
        "forest_move which = d_rsv_35 value = 20",
        "night_attack which = d_rsv_35 value = 10",
    ),
    9281803: (
        "ind_aubm_airborne_doctrine",
        "paradrop_attack which = d_rsv_36 value = 20",
        "urban_attack which = d_rsv_36 value = 10",
    ),
    9281804: (
        "ind_aubm_coromandel_doctrine",
        "shore_attack which = d_rsv_37 value = 25",
        "river_attack which = d_rsv_37 value = 15",
    ),
    9281807: (
        "ind_aubm_pioneer_doctrine",
        "river_attack which = d_rsv_40 value = 30",
        "urban_defense which = d_rsv_40 value = 20",
    ),
}


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.integration: list[str] = []
        self.checks = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(message)

    def require_integration(self, condition: bool, message: str) -> None:
        if not condition:
            self.integration.append(message)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="cp1252")


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char in "\r\n":
                comment = False
            continue
        if escaped:
            escaped = False
            continue
        if quoted and char == "\\":
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
            continue
        if not quoted and char == "#":
            comment = True
            continue
        if quoted:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
            if depth < 0:
                break
    raise ValueError(f"Unmatched opening brace at byte {opening}")


def top_blocks(text: str, keyword: str) -> list[str]:
    blocks: list[str] = []
    pattern = re.compile(rf"(?mi)^\s*{re.escape(keyword)}\s*=\s*\{{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start(), match.end())
        blocks.append(text[match.start() : matching_brace(text, opening) + 1])
    return blocks


def field(text: str, name: str) -> str | None:
    match = re.search(rf"(?mi)^\s*{re.escape(name)}\s*=\s*([^\s#}}]+)", text)
    return match.group(1).strip('"') if match else None


def numeric_field(text: str, name: str) -> float | None:
    value = field(text, name)
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def parse_event_blocks(text: str) -> dict[int, str]:
    events: dict[int, str] = {}
    for block in top_blocks(text, "event"):
        match = re.search(r"(?mi)^\s*id\s*=\s*(\d+)\s*$", block)
        if not match:
            raise ValueError("Event block has no numeric id")
        event_id = int(match.group(1))
        if event_id in events:
            raise ValueError(f"Duplicate event id {event_id} in target file")
        events[event_id] = block
    return events


def top_level_unit_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    pattern = re.compile(r"(?m)^([A-Za-z0-9_]+)\s*=\s*\{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start(), match.end())
        blocks[match.group(1)] = text[match.start() : matching_brace(text, opening) + 1]
    return blocks


def parse_csv(path: pathlib.Path) -> list[list[str]]:
    with path.open("r", encoding="cp1252", newline="") as handle:
        return list(csv.reader(handle, delimiter=";"))


def validate_config(root: pathlib.Path, result: Validation) -> None:
    source_paths = (
        root / "mod/config/aubm_special_units.csv",
        root / "mod/config/aubm_special_unit_models.csv",
    )
    source_rows: dict[str, tuple[int, list[str]]] = {}
    for path in source_paths:
        result.check(path.is_file(), f"Missing special-unit text file: {path}")
        if not path.is_file():
            continue
        for line, row in enumerate(parse_csv(path), 1):
            if not row or not row[0] or row[0].startswith("#"):
                continue
            result.check(len(row) == 12, f"{path}:{line} must contain 12 semicolon fields, found {len(row)}")
            result.check(row[-1] == "X", f"{path}:{line} must end with the X sentinel")
            result.check(
                row[0] not in source_rows,
                f"Duplicate localization key {row[0]} on line {line}",
            )
            source_rows[row[0]] = (line, row)

    required: set[str] = set()
    for slot, spec in SPECIAL_UNITS.items():
        stem = spec.unit_name_key.removeprefix("AUBM_NAME_")
        required.update(
            {
                spec.unit_name_key,
                f"AUBM_SNAME_{stem}",
                f"AUBM_SDESC_{stem}",
                f"AUBM_LDESC_{stem}",
                *(f"MODEL_{slot}_{model}" for model in range(MODEL_COUNTS[slot])),
            }
        )
    for key in sorted(required):
        result.check(key in source_rows, f"Missing localization key {key}")

    loaded_path = root / "mod/config/unit_names.csv"
    result.check(loaded_path.is_file(), f"Missing loaded localization table: {loaded_path}")
    if not loaded_path.is_file():
        return
    loaded_text = read_text(loaded_path)
    result.check(loaded_text.count(LOCALIZATION_BEGIN) == 1, "Loaded localization lacks one AUBM begin marker")
    result.check(loaded_text.count(LOCALIZATION_END) == 1, "Loaded localization lacks one AUBM end marker")
    loaded_rows: dict[str, list[list[str]]] = {}
    for line, row in enumerate(parse_csv(loaded_path), 1):
        if not row or not row[0] or row[0].startswith("#"):
            continue
        loaded_rows.setdefault(row[0], []).append(row)
        if row[0] in required:
            result.check(len(row) == 12, f"{loaded_path}:{line} must contain 12 semicolon fields")
            result.check(row[-1] == "X", f"{loaded_path}:{line} must end with the X sentinel")
    for key in sorted(required):
        occurrences = loaded_rows.get(key, [])
        result.check(len(occurrences) == 1, f"Loaded localization key {key} occurs {len(occurrences)} times")
        if len(occurrences) == 1 and key in source_rows:
            result.check(
                occurrences[0] == source_rows[key][1],
                f"Loaded localization key {key} differs from its specialist source table",
            )


def validate_unit_models(root: pathlib.Path, baseline: pathlib.Path, result: Validation) -> None:
    brigade_types_path = baseline / "db/units/brigade_types.txt"
    brigade_types = top_level_unit_blocks(read_text(brigade_types_path))
    required_model_fields = {
        "cost",
        "buildtime",
        "manpower",
        "maxspeed",
        "defaultorganisation",
        "morale",
        "defensiveness",
        "toughness",
        "softness",
        "suppression",
        "airdefence",
        "softattack",
        "hardattack",
        "airattack",
        "transportweight",
        "supplyconsumption",
        "fuelconsumption",
        "upgrade_time_factor",
        "upgrade_cost_factor",
        "reinforce_time",
        "reinforce_cost",
    }

    for slot, spec in SPECIAL_UNITS.items():
        path = root / f"mod/db/units/divisions/d_rsv_{slot}.txt"
        result.check(path.is_file(), f"Missing unit model file {path}")
        if not path.is_file():
            continue
        text = read_text(path)
        try:
            models = top_blocks(text, "model")
        except ValueError as exc:
            result.check(False, f"{path}: {exc}")
            continue
        expected_count = MODEL_COUNTS[slot]
        result.check(
            len(models) == expected_count,
            f"{path} must define {expected_count} milestone models, found {len(models)}",
        )
        if len(models) != expected_count:
            continue
        previous: dict[str, float] | None = None
        for model_index, model in enumerate(models):
            values: dict[str, float] = {}
            for name in sorted(required_model_fields):
                value = numeric_field(model, name)
                result.check(value is not None, f"{path}: model {model_index} lacks numeric {name}")
                if value is not None:
                    values[name] = value
            cost = values.get("cost")
            buildtime = values.get("buildtime")
            manpower = values.get("manpower")
            result.check(
                cost is not None and 5 <= cost <= 32,
                f"{path}: model {model_index} cost {cost} is outside the divisional range",
            )
            result.check(
                buildtime is not None and 280 <= buildtime <= 520,
                f"{path}: model {model_index} buildtime {buildtime} is not a normal schedule",
            )
            result.check(
                manpower is not None and 5 <= manpower <= 16,
                f"{path}: model {model_index} manpower {manpower} is implausible",
            )
            if model_index == 0:
                result.check(
                    cost is not None and spec.min_cost <= cost <= spec.max_cost,
                    f"{path}: commissioning cost {cost} is outside {spec.min_cost}-{spec.max_cost}",
                )
                result.check(
                    manpower == spec.manpower,
                    f"{path}: commissioning manpower {manpower} does not match event {spec.manpower}",
                )
            if previous:
                for name in (
                    "defaultorganisation",
                    "morale",
                    "defensiveness",
                    "toughness",
                    "softattack",
                    "hardattack",
                ):
                    result.check(
                        values.get(name, -1) >= previous.get(name, -1),
                        f"{path}: model {model_index} regresses {name}",
                    )
                result.check(
                    values.get("softness", 101) <= previous.get("softness", 101),
                    f"{path}: model {model_index} becomes softer than its predecessor",
                )
                for name in ("upgrade_time_factor", "upgrade_cost_factor"):
                    result.check(
                        values.get(name) == previous.get(name),
                        f"{path}: model {model_index} changes normal {name}",
                    )
            equipment = re.search(r"(?ms)\bequipment\s*=\s*\{(.*?)\}", model)
            result.check(equipment is not None, f"{path}: model {model_index} lacks equipment")
            if equipment and manpower is not None:
                equipment_manpower = re.search(r"\bmanpower\s*=\s*(\d+)", equipment.group(1))
                expected = int(manpower * 1000)
                result.check(
                    equipment_manpower is not None and int(equipment_manpower.group(1)) == expected,
                    f"{path}: model {model_index} equipment manpower must be {expected}",
                )
            previous = values
        for brigade in re.findall(r"(?mi)^\s*allowed_brigades\s*=\s*([A-Za-z0-9_]+)", text):
            result.check(brigade in brigade_types, f"{path}: unknown allowed brigade {brigade}")


def validate_division_types(
    root: pathlib.Path, baseline: pathlib.Path, result: Validation
) -> str | None:
    path = root / "mod/db/units/division_types.txt"
    result.check(path.is_file(), f"Generated division_types.txt is missing; run Ensure-Aubm-SpecialUnits.ps1")
    if not path.is_file():
        return None
    current = top_level_unit_blocks(read_text(path))
    stock = top_level_unit_blocks(read_text(baseline / "db/units/division_types.txt"))
    result.check(list(current) == list(stock), "Reserved-slot installation changed the division-type count or ordering")
    for slot, spec in SPECIAL_UNITS.items():
        key = f"d_rsv_{slot}"
        block = current.get(key, "")
        result.check(bool(block), f"division_types.txt lacks {key}")
        if not block:
            continue
        result.check(field(block, "type") == spec.base_type, f"{key} must inherit engine class {spec.base_type}")
        result.check(field(block, "name") == spec.unit_name_key, f"{key} has the wrong localization key")
        result.check(field(block, "list_prio") != "-1", f"{key} remains disabled in division_types.txt")

    sprites = {
        slot: field(current.get(f"d_rsv_{slot}", ""), "sprite")
        for slot in SLOTS
    }
    profiles = {
        "public": PUBLIC_SPRITE_KEYS,
        "personal": PERSONAL_SPRITE_KEYS,
    }
    matching_profiles = [
        name for name, expected in profiles.items() if sprites == expected
    ]
    result.check(
        len(matching_profiles) == 1,
        "Reserved-unit sprite fields must use one complete public fallback or personal animated profile",
    )
    profile = matching_profiles[0] if len(matching_profiles) == 1 else None

    if profile == "public":
        reserved = {f"d_rsv_{slot}" for slot in SLOTS}
        for unit_type, block in current.items():
            if unit_type in reserved or unit_type not in stock:
                continue
            expected = field(stock[unit_type], "sprite")
            if expected is None:
                continue
            result.check(
                field(block, "sprite") == expected,
                f"Public sprite profile must retain Darkest Hour Full's {unit_type} sprite {expected}",
            )

    return profile


def validate_modifiers(root: pathlib.Path, result: Validation) -> None:
    path = root / "mod/db/units/modifiers.csv"
    result.check(path.is_file(), f"Generated modifiers.csv is missing; run Ensure-Aubm-SpecialUnits.ps1")
    if not path.is_file():
        return
    rows = parse_csv(path)
    result.check(bool(rows), f"{path} is empty")
    if not rows:
        return
    header = rows[0]
    columns = {name: index for index, name in enumerate(header)}
    for slot, source in SOURCE_COLUMNS.items():
        destination = f"rsv_{slot}"
        result.check(destination in columns, f"modifiers.csv lacks {destination}")
        result.check(source in columns, f"modifiers.csv lacks source column {source}")
    for line, row in enumerate(rows[1:], 2):
        if not row:
            continue
        result.check(len(row) == len(header), f"{path}:{line} has {len(row)} columns; expected {len(header)}")
        if len(row) != len(header):
            continue
        for slot, source in SOURCE_COLUMNS.items():
            result.check(
                row[columns[f"rsv_{slot}"]] == row[columns[source]],
                f"{path}:{line} rsv_{slot} does not inherit {source} terrain/weather modifiers",
            )


def bmp_layout(data: bytes) -> tuple[int, int, int, int]:
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("not a Windows BMP")
    offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = abs(struct.unpack_from("<i", data, 22)[0])
    bits = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if bits != 8 or compression != 0:
        raise ValueError("must be an uncompressed 8-bit indexed BMP")
    stride = ((width * bits + 31) // 32) * 4
    if offset + stride * height > len(data):
        raise ValueError("pixel payload is truncated")
    return offset, width, height, stride


def validate_counter_strip(root: pathlib.Path, result: Validation) -> None:
    path = root / "mod/gfx/map/hoi_counter_strip.bmp"
    result.check(path.is_file(), f"Counter strip is missing: {path}")
    if not path.is_file():
        return
    data = path.read_bytes()
    try:
        offset, width, height, stride = bmp_layout(data)
    except ValueError as exc:
        result.check(False, f"{path}: {exc}")
        return
    tile_width = 32
    result.check(width >= 41 * tile_width, f"Counter strip width {width} cannot contain unit ID 40")
    if width < 41 * tile_width:
        return
    for destination, source in COUNTER_SOURCES.items():
        for row in range(height):
            start = offset + row * stride
            source_pixels = data[start + source * tile_width : start + (source + 1) * tile_width]
            destination_pixels = data[start + destination * tile_width : start + (destination + 1) * tile_width]
            if source_pixels != destination_pixels:
                result.check(False, f"Counter tile {destination} is not the safe {source} fallback on row {row}")
                break
        else:
            result.check(True, f"Counter tile {destination}")


def validate_events(root: pathlib.Path, result: Validation) -> None:
    path = root / EVENT_FILE
    result.check(path.is_file(), f"Missing event file: {path}")
    if not path.is_file():
        return
    text = read_text(path)
    try:
        events = parse_event_blocks(text)
    except ValueError as exc:
        result.check(False, f"{path}: {exc}")
        return
    expected_ids = (
        {spec.event_id for spec in SPECIAL_UNITS.values()}
        | set(SHBB_EVENTS)
        | {DOCTRINE_MIGRATION_EVENT}
    )
    result.check(set(events) == expected_ids, f"Event file must contain exactly {sorted(expected_ids)}")
    result.check(all(9281800 <= event_id <= 9281899 for event_id in events), "Event ID escaped reserved range 9281800-9281899")

    for event_id, event in events.items():
        picture = field(event, "picture")
        result.check(bool(picture), f"Event {event_id} has no picture key")
        if picture:
            local_picture = root / f"mod/gfx/events_pics/{picture}.bmp"
            result.check(local_picture.is_file(), f"Event {event_id} references missing picture {picture}.bmp")
        for action in top_blocks(event, "action_a"):
            label_match = re.search(r'(?mi)^\s*name\s*=\s*"([^"]+)"', action)
            result.check(label_match is not None, f"Event {event_id} action has no explicit label")
            if label_match:
                result.check(
                    len(label_match.group(1).encode("cp1252")) <= 58,
                    f"Event {event_id} action label exceeds the 58-byte DH UI limit",
                )

    for slot, spec in SPECIAL_UNITS.items():
        event = events.get(spec.event_id, "")
        result.check(bool(event), f"Missing commissioning event {spec.event_id}")
        if not event:
            continue
        result.check(re.search(rf"\btechnology\s*=\s*{spec.technology}\b", event) is not None, f"Event {spec.event_id} lacks tech gate {spec.technology}")
        province = DEPLOYMENT_PROVINCES[slot]
        result.check(
            re.search(rf"\bcontrol\s*=\s*\{{\s*province\s*=\s*{province}\s+data\s*=\s*IND\s*\}}", event) is not None,
            f"Event {spec.event_id} can deploy without Indian control of province {province}",
        )
        result.check(re.search(rf"\bactivate_unit_type\s+which\s*=\s*d_rsv_{slot}\b", event) is not None, f"Event {spec.event_id} does not activate d_rsv_{slot}")
        result.check(
            re.search(rf"\badd_corps\s+which\s*=\s*\"[^\"]+\"\s+value\s*=\s*land\s+where\s*=\s*{province}", event) is not None,
            f"Event {spec.event_id} lacks an explicit formation name/location",
        )
        result.check(re.search(rf"\badd_division\s+which\s*=\s*\"[^\"]+\"\s+value\s*=\s*d_rsv_{slot}\s+when\s*=\s*0", event) is not None, f"Event {spec.event_id} lacks an explicit division name/model")
        result.check(re.search(rf"\bmanpowerpool\s+value\s*=\s*-{spec.manpower}\b", event) is not None, f"Event {spec.event_id} does not pay the model's {spec.manpower} manpower")
        result.check("build_division" not in event, f"Event {spec.event_id} must commission one paid ready formation, not create a production exploit")

        if slot == 35:
            decision_blocks = top_blocks(event, "decision")
            decision = decision_blocks[0] if decision_blocks else ""
            result.check("year = 1939" in decision, "Chindit commissioning must become visible from 1939")
            result.check(
                re.search(r"war\s*=\s*\{\s*country\s*=\s*JAP\s+country\s*=\s*CHI\s*\}", decision) is not None,
                "Chindit commissioning must respond to the Sino-Japanese War",
            )
            result.check("year = 1941" in decision, "Chindit commissioning needs an unconditional 1941 fallback")
            result.check("atwar = yes" in decision, "Chindit commissioning must remain available during any Indian war")

    for event_id, contract in DOCTRINE_CONTRACTS.items():
        event = events.get(event_id, "")
        flag, *commands = contract
        result.check(f"setflag which = {flag}" in event, f"Event {event_id} does not mark doctrine flag {flag}")
        for command in commands:
            result.check(command in event, f"Event {event_id} lacks specialist modifier: {command}")

    doctrine_migration = events.get(DOCTRINE_MIGRATION_EVENT, "")
    result.check(bool(doctrine_migration), f"Missing doctrine migration event {DOCTRINE_MIGRATION_EVENT}")
    for event_id, contract in DOCTRINE_CONTRACTS.items():
        flag, *commands = contract
        result.check(flag in doctrine_migration, f"Doctrine migration omits flag {flag}")
        for command in commands:
            result.check(command in doctrine_migration, f"Doctrine migration omits {event_id} modifier: {command}")

    all_ship_orders = re.findall(r"(?mi)^\s*command\s*=\s*\{[^{}]*\btype\s*=\s*build_division\b[^{}]*\bwhich\s*=\s*battleship\b[^{}]*\}", text)
    result.check(len(all_ship_orders) == 2, f"Expected exactly two SHBB production orders, found {len(all_ship_orders)}")
    for event_id, ship_name in SHBB_EVENTS.items():
        event = events.get(event_id, "")
        result.check(bool(event), f"Missing SHBB event {event_id}")
        if not event:
            continue
        result.check(re.search(r"\btechnology\s*=\s*3490\b", event) is not None, f"Event {event_id} lacks technology 3490")
        orders = re.findall(r"(?mi)^\s*command\s*=\s*\{[^{}]*\btype\s*=\s*build_division\b[^{}]*\}", event)
        result.check(len(orders) == 1, f"Event {event_id} must order exactly one ship")
        if len(orders) == 1:
            order = orders[0]
            result.check(re.search(r"\bwhich\s*=\s*battleship\b", order) is not None, f"Event {event_id} does not order a battleship")
            result.check(re.search(r"\bwhen\s*=\s*1\b", order) is not None, f"Event {event_id} is not a one-ship contract")
            result.check(re.search(r"\bwhere\s*=\s*420\b", order) is not None, f"Event {event_id} does not use the 420-day half-yard schedule")
            result.check(re.search(rf"\bname\s*=\s*\"{re.escape(ship_name)}\"", order) is not None, f"Event {event_id} ship name is not {ship_name}")
            result.check(re.search(r"\bcost\s*=", order) is None, f"Event {event_id} overrides normal daily IC cost")
        result.check(event.count("# AUBM_APPROVED_SHBB_HALF_COMPLETE_BEGIN") == 1, f"Event {event_id} lacks its normalizer-exemption begin marker")
        result.check(event.count("# AUBM_APPROVED_SHBB_HALF_COMPLETE_END") == 1, f"Event {event_id} lacks its normalizer-exemption end marker")
        result.check(re.search(r"\bmanpowerpool\s+value\s*=\s*-", event) is None, f"Event {event_id} manually charges manpower in addition to the queue")
        result.check(re.search(r"\bmanpower\s*=\s*3\b", event) is not None, f"Event {event_id} lacks a normal manpower admission gate")

    for ship_name in SHBB_EVENTS.values():
        occurrences = 0
        for candidate in (root / "mod/db/events").rglob("*.txt"):
            occurrences += read_text(candidate).count(f'name = "{ship_name}"')
        result.check(occurrences == 1, f"Ship name {ship_name} appears {occurrences} times across event sources")

    reserved_occurrences: dict[int, list[pathlib.Path]] = {event_id: [] for event_id in expected_ids}
    id_pattern = re.compile(r"(?mi)^\s*id\s*=\s*(92818\d\d)\s*$")
    for candidate in (root / "mod/db/events").rglob("*.txt"):
        candidate_text = read_text(candidate)
        for match in id_pattern.finditer(candidate_text):
            event_id = int(match.group(1))
            if event_id in reserved_occurrences:
                reserved_occurrences[event_id].append(candidate)
    for event_id, paths in reserved_occurrences.items():
        result.check(len(paths) == 1, f"Event ID {event_id} appears in {len(paths)} files: {paths}")


def validate_technology_ladders(root: pathlib.Path, result: Validation) -> None:
    paths = {
        "infantry_tech.txt": root / "mod/db/tech/infantry_tech.txt",
        "armor_tech.txt": root / "mod/db/tech/armor_tech.txt",
    }
    applications: dict[str, dict[int, str]] = {}
    for filename, path in paths.items():
        result.check(path.is_file(), f"Missing specialist technology overlay: {path}")
        if not path.is_file():
            continue
        blocks: dict[int, str] = {}
        for block in top_blocks(read_text(path), "application"):
            match = re.search(r"\bid\s*=\s*(\d+)", block)
            if match:
                blocks[int(match.group(1))] = block
        applications[filename] = blocks

    for slot, stages in MODEL_TECHS.items():
        filename = "armor_tech.txt" if slot == 38 else "infantry_tech.txt"
        for model, techs in enumerate(stages, 1):
            for technology in techs:
                block = applications.get(filename, {}).get(technology, "")
                result.check(bool(block), f"Missing technology application {technology}")
                if not block:
                    continue
                other_techs = tuple(candidate for candidate in techs if candidate != technology)
                new_match = re.search(
                    rf"(?mi)^\s*command\s*=\s*\{{([^\r\n]*\btype\s*=\s*new_model\s+which\s*=\s*d_rsv_{slot}\s+value\s*=\s*{model}\b[^\r\n]*)\}}",
                    block,
                )
                scrap_match = re.search(
                    rf"(?mi)^\s*command\s*=\s*\{{([^\r\n]*\btype\s*=\s*scrap_model\s+which\s*=\s*d_rsv_{slot}\s+value\s*=\s*{model - 1}\b[^\r\n]*)\}}",
                    block,
                )
                result.check(
                    new_match is not None,
                    f"Technology {technology} does not unlock d_rsv_{slot} model {model}",
                )
                result.check(
                    scrap_match is not None,
                    f"Technology {technology} does not retire d_rsv_{slot} model {model - 1}",
                )
                for command_name, match in (("new_model", new_match), ("scrap_model", scrap_match)):
                    if not match:
                        continue
                    command = match.group(1)
                    for requirement in other_techs:
                        result.check(
                            re.search(rf"\btechnology\s*=\s*{requirement}\b", command) is not None,
                            f"Technology {technology} {command_name} for d_rsv_{slot} model {model} bypasses prerequisite {requirement}",
                        )

    event_text = "\n".join(
        read_text(path) for path in (root / "mod/db/events").rglob("*.txt")
    )
    result.check(
        re.search(r"\b(?:new_model|scrap_model)\s+which\s*=\s*d_rsv_(?:33|34|35|36|37|38|39|40)\b", event_text) is None,
        "Specialist models must advance through technology, not event commands",
    )


def validate_integration(
    root: pathlib.Path, result: Validation, sprite_profile: str | None
) -> None:
    events_index = read_text(root / "mod/db/events.txt") if (root / "mod/db/events.txt").is_file() else ""
    result.require_integration(
        "db\\events\\aubm_v4\\40_special_units_and_capital_ships.txt" in events_index,
        "Add 40_special_units_and_capital_ships.txt to Build-EventsIndex in Rebase-V4-DirectDH.ps1; direct events.txt editing is intentionally excluded.",
    )

    rebase_path = root / "tools/Rebase-V4-DirectDH.ps1"
    rebase = read_text(rebase_path) if rebase_path.is_file() else ""
    result.require_integration(
        "Ensure-Aubm-SpecialUnits.ps1" in rebase,
        "Invoke Ensure-Aubm-SpecialUnits.ps1 after the procurement normalizer and before validation/deployment.",
    )
    generator_path = root / "tools/generate_aubm_special_unit_models.py"
    generator = read_text(generator_path) if generator_path.is_file() else ""
    ensure_path = root / "tools/Ensure-Aubm-SpecialUnits.ps1"
    ensure = read_text(ensure_path) if ensure_path.is_file() else ""
    result.require_integration(
        bool(generator) and "generate_aubm_special_unit_models.py" in ensure,
        "Run the deterministic specialist model generator from Ensure-Aubm-SpecialUnits.ps1.",
    )

    normalizer_path = root / "tools/Ensure-V4-EventProcurement.ps1"
    normalizer = read_text(normalizer_path) if normalizer_path.is_file() else ""
    result.require_integration(
        "AUBM_APPROVED_SHBB_HALF_COMPLETE" in normalizer,
        "Teach Ensure-V4-EventProcurement.ps1 to preserve the 420-day national-yard SHBB contracts.",
    )

    central_validator_path = root / "tools/validate_v4.py"
    central_validator = read_text(central_validator_path) if central_validator_path.is_file() else ""
    central_validator_uses_stripped_markers = bool(
        re.search(
            r'["\']AUBM_APPROVED_SHBB_HALF_COMPLETE_(?:BEGIN|END)["\']\s+in\s+event\.text',
            central_validator,
        )
        and "blocks.append(Block(clean[" in central_validator
    )
    central_validator_has_contract_exception = all(
        token in central_validator
        for token in ("9281880", "9281881", "remaining_days == 420", 'unit.group(1) == "battleship"')
    )
    result.require_integration(
        central_validator_has_contract_exception and not central_validator_uses_stripped_markers,
        "Keep validate_v4.py aligned with the 420-day SHBB contracts; the dedicated validator enforces markers, names and exact orders.",
    )

    build_path = root / "tools/Build-And-Deploy-V4.ps1"
    build = read_text(build_path) if build_path.is_file() else ""
    result.require_integration(
        "validate_aubm_units.py" in build,
        "Run validate_aubm_units.py from Build-And-Deploy-V4.ps1 before installer-manifest generation/deployment.",
    )

    manifest_path = root / "installer/manifest.txt"
    manifest = read_text(manifest_path).replace("\\", "/") if manifest_path.is_file() else ""
    manifest_requirements = [
        "config/aubm_special_units.csv",
        "config/aubm_special_unit_models.csv",
        "config/unit_names.csv",
        "db/events/aubm_v4/40_special_units_and_capital_ships.txt",
        "db/tech/infantry_tech.txt",
        "db/tech/armor_tech.txt",
        "db/units/division_types.txt",
        "db/units/modifiers.csv",
        *(f"db/units/divisions/d_rsv_{slot}.txt" for slot in SLOTS),
    ]
    missing_manifest = [path for path in manifest_requirements if path not in manifest]
    result.require_integration(
        not missing_manifest,
        "Regenerate installer manifests after integration; they currently omit "
        + ", ".join(missing_manifest)
        + ".",
    )

    if sprite_profile == "personal":
        sprite_path = root / "mod/gfx/map/units"
        sprite_names = (
            {path.name.lower() for path in sprite_path.glob("*.spr")}
            if sprite_path.is_dir()
            else set()
        )
        missing_sprites = [
            slot
            for slot in SLOTS
            if not any(
                name.startswith(f"t-{PERSONAL_SPRITE_KEYS[slot]} ")
                and " c-ind " in name
                for name in sprite_names
            )
        ]
        result.require_integration(
            not missing_sprites,
            "Supply complete C-IND .spr/BMP/palette families for sprite keys "
            + ", ".join(PERSONAL_SPRITE_KEYS[slot] for slot in missing_sprites)
            + "; reserved unit IDs must use the engine's numeric sprite sequence.",
        )


def resolve_baseline(root: pathlib.Path, requested: pathlib.Path | None) -> pathlib.Path:
    if requested:
        return requested.resolve()
    config = json.loads((root / "tools/v4_config.json").read_text(encoding="utf-8"))
    return pathlib.Path(config["baseline_mod"]).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline", type=pathlib.Path)
    parser.add_argument("--strict-integration", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    baseline = resolve_baseline(root, args.baseline)
    result = Validation()
    result.check(baseline.is_dir(), f"Darkest Hour Full baseline is missing: {baseline}")
    if baseline.is_dir():
        validate_config(root, result)
        validate_unit_models(root, baseline, result)
        sprite_profile = validate_division_types(root, baseline, result)
        validate_modifiers(root, result)
        validate_counter_strip(root, result)
        validate_events(root, result)
        validate_technology_ladders(root, result)
        validate_integration(root, result, sprite_profile)

    if result.errors:
        print(f"AUBM special-unit validation FAILED with {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"  ERROR: {error}")
    else:
        print(f"AUBM special-unit validation passed ({result.checks} checks).")

    if result.integration:
        print("Required parent-pipeline integration:")
        for item in result.integration:
            print(f"  INTEGRATION: {item}")

    if result.errors or (args.strict_integration and result.integration):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
