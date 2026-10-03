#!/usr/bin/env python3
"""Gate cumulative AUBM infrastructure and strategic-base construction.

Darkest Hour clamps infrastructure at 100 and air/naval bases at 10. Commands
above those limits are wasted and can make a few provinces disproportionately
strong. This analysis starts from the Darkest Hour Full 1933 baseline, takes the
strongest action in each event, and treats the five strategic paths as
mutually exclusive.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import defaultdict

import validate_v3_legacy as validator


SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[1]
LIMITS = {"infrastructure": 100, "air_base": 10, "naval_base": 10}
PATH_MODULES = {
    "41_allied.txt",
    "42_axis.txt",
    "43_soviet.txt",
    "44_non_aligned.txt",
    "45_japan.txt",
}
POSTWAR_MODULES = {"60_postwar.txt", "61_cold_war.txt", "62_victory.txt"}


Key = tuple[int, str]


def event_files(root: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for relative in ("db/events/india_v3", "db/events/aubm_v4"):
        files.extend(sorted((root / relative).glob("*.txt")))
    return files


def registry_path(root: pathlib.Path) -> pathlib.Path:
    deployed = root / "tools" / "data" / "provinces.csv"
    return deployed if deployed.exists() else SOURCE_ROOT / "tools" / "data" / "provinces.csv"


def baseline(root: pathlib.Path) -> dict[Key, int]:
    values: dict[Key, int] = defaultdict(int)
    registry = registry_path(root)
    with registry.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            province = int(row["province_id"])
            values[(province, "infrastructure")] = int(float(row["infrastructure"]))

    bases = root / "scenarios" / "1933" / "bases.inc"
    if not bases.exists():
        config = json.loads((SOURCE_ROOT / "tools/v4_config.json").read_text(encoding="utf-8"))
        bases = pathlib.Path(config["baseline_mod"]) / "scenarios/1933/bases.inc"
    text = validator.read_text(bases)
    for block in validator.find_top_level_blocks(text, "province"):
        province = validator.integer(block.text, "id")
        if province is None:
            continue
        for kind in ("air_base", "naval_base"):
            nested = validator.find_blocks(block.text, kind)
            if nested:
                size = validator.integer(nested[0].text, "size")
                if size is not None:
                    values[(province, kind)] = size
    return values


def action_construction(action: validator.Block) -> dict[Key, int]:
    result: dict[Key, int] = defaultdict(int)
    for command in validator.find_blocks(action.text, "command"):
        if (validator.atom(command.text, "type") or "").lower() != "construct":
            continue
        kind = (validator.atom(command.text, "which") or "").lower()
        if kind not in LIMITS:
            continue
        province = validator.integer(command.text, "where")
        amount = validator.integer(command.text, "value")
        if province is not None and amount is not None and amount > 0:
            result[(province, kind)] += amount
    return result


def expected_guard(kind: str, amount: int) -> str:
    if kind == "infrastructure":
        return f"{1.0 - amount / 100.0 + 0.01:.2f}".rstrip("0").rstrip(".")
    return str(10 - amount + 1)


def guard_errors(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for path in event_files(root):
        text = validator.read_text(path)
        for command in validator.find_blocks(text, "command"):
            if (validator.atom(command.text, "type") or "").lower() != "construct":
                continue
            kind = (validator.atom(command.text, "which") or "").lower()
            amount = validator.integer(command.text, "value")
            province = validator.integer(command.text, "where")
            if (
                kind not in LIMITS
                or amount is None
                or amount <= 0
                or province is None
            ):
                continue
            buildings = validator.find_blocks(command.text, "building")
            not_blocks = validator.find_blocks(command.text, "NOT")
            expected = expected_guard(kind, amount)
            valid = False
            for building in buildings:
                building_province = validator.integer(building.text, "province")
                building_kind = (validator.atom(building.text, "type") or "").lower()
                building_value = validator.atom(building.text, "value")
                if (
                    building_province == province
                    and building_kind == kind
                    and building_value == expected
                    and validator.atom(building.text, "when") is None
                    and any(building.text in block.text for block in not_blocks)
                ):
                    valid = True
                    break
            if not valid:
                errors.append(
                    f"{path.name}:{command.line} {kind} +{amount} in {province} "
                    f"needs a max-size NOT building guard at {expected}."
                )
    return errors


def event_envelope(event: validator.Block) -> dict[Key, int]:
    actions = [
        blocks[0]
        for letter in "abcd"
        if (blocks := validator.find_blocks(event.text, f"action_{letter}"))
    ]
    envelope: dict[Key, int] = defaultdict(int)
    for action in actions:
        for key, amount in action_construction(action).items():
            envelope[key] = max(envelope[key], amount)
    return envelope


def add_values(target: dict[Key, int], source: dict[Key, int]) -> None:
    for key, amount in source.items():
        target[key] += amount


def projected_additions(root: pathlib.Path, include_postwar: bool) -> dict[Key, int]:
    common: dict[Key, int] = defaultdict(int)
    route_totals: dict[str, dict[Key, int]] = {
        module: defaultdict(int) for module in PATH_MODULES
    }
    for path in event_files(root):
        if not include_postwar and path.name in POSTWAR_MODULES:
            continue
        text = validator.read_text(path)
        for event in validator.find_top_level_blocks(text, "event"):
            envelope = event_envelope(event)
            if path.name in PATH_MODULES:
                add_values(route_totals[path.name], envelope)
            else:
                add_values(common, envelope)

    route_max: dict[Key, int] = defaultdict(int)
    for totals in route_totals.values():
        for key, amount in totals.items():
            route_max[key] = max(route_max[key], amount)
    add_values(common, route_max)
    return common


def touched_provinces(root: pathlib.Path) -> set[int]:
    touched: set[int] = set()
    for path in event_files(root):
        text = validator.read_text(path)
        for command in validator.find_blocks(text, "command"):
            if (validator.atom(command.text, "type") or "").lower() != "construct":
                continue
            kind = (validator.atom(command.text, "which") or "").lower()
            province = validator.integer(command.text, "where")
            if kind in LIMITS and province is not None:
                touched.add(province)
    return touched


def save_levels(save: pathlib.Path, relevant: set[int]) -> dict[Key, int]:
    levels: dict[Key, int] = defaultdict(int)
    lines = save.read_text(encoding="cp1252", errors="replace").splitlines()
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("country = {"):
            break
        if not stripped.startswith("province = {"):
            index += 1
            continue
        block_lines = [lines[index]]
        depth = lines[index].count("{") - lines[index].count("}")
        index += 1
        while depth > 0 and index < len(lines):
            block_lines.append(lines[index])
            depth += lines[index].count("{") - lines[index].count("}")
            index += 1
        block = "\n".join(block_lines)
        id_match = re.search(r"\bid\s*=\s*(\d+)", block)
        if not id_match:
            continue
        province = int(id_match.group(1))
        if province not in relevant:
            continue
        for kind, save_key, scale in (
            ("infrastructure", "infra", 100),
            ("air_base", "air_base", 1),
            ("naval_base", "naval_base", 1),
        ):
            match = re.search(
                rf"\b{save_key}\s*=\s*\{{\s*size\s*=\s*([0-9.]+)",
                block,
                re.S,
            )
            if match:
                levels[(province, kind)] = round(float(match.group(1)) * scale)
    return levels


def province_names(root: pathlib.Path) -> dict[int, str]:
    names: dict[int, str] = {}
    with registry_path(root).open(
        encoding="utf-8", newline=""
    ) as stream:
        for row in csv.DictReader(stream):
            names[int(row["province_id"])] = row["name"]
    return names


def report_projection(
    label: str,
    base: dict[Key, int],
    additions: dict[Key, int],
    names: dict[int, str],
) -> list[str]:
    errors: list[str] = []
    rows = []
    for key, amount in additions.items():
        province, kind = key
        total = min(LIMITS[kind], base.get(key, 0) + amount)
        rows.append((total, province, kind, base.get(key, 0), amount))
    print(f"{label} highest cumulative levels:")
    for total, province, kind, start, amount in sorted(rows, reverse=True)[:20]:
        print(
            f"  {names.get(province, province):18} {province}: "
            f"{kind:14} {start}+{amount}={total}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=SOURCE_ROOT)
    parser.add_argument("--save", type=pathlib.Path)
    args = parser.parse_args()
    root = args.root.resolve()

    names = province_names(root)
    base = baseline(root)
    errors = guard_errors(root)
    errors.extend(report_projection(
        "Prewar",
        base,
        projected_additions(root, include_postwar=False),
        names,
    ))
    errors.extend(
        report_projection(
            "Lifetime",
            base,
            projected_additions(root, include_postwar=True),
            names,
        )
    )

    if args.save:
        levels = save_levels(args.save, touched_provinces(root))
        print("Current playtest high levels:")
        high = [
            (amount, province, kind)
            for (province, kind), amount in levels.items()
            if amount >= (90 if kind == "infrastructure" else 8)
        ]
        for amount, province, kind in sorted(high, reverse=True):
            print(
                f"  {names.get(province, province):18} {province}: "
                f"{kind:14} {amount}"
            )

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"CONSTRUCTION CAP GATE FAILED: {len(errors)} over-cap projection(s)")
        return 1
    print("CONSTRUCTION CAP GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
