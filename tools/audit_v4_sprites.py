#!/usr/bin/env python3
"""Validate the original India V4 map-sprite package without launching the game."""

from __future__ import annotations

import csv
import hashlib
import pathlib
import re
import struct
import sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/v4_sprite_manifest.csv"
SPRITE_DIR = ROOT / "mod/gfx/map/units"
BITMAP_DIR = SPRITE_DIR / "bmp"
PALETTE_DIR = ROOT / "mod/gfx/palette"

EXPECTED_FAMILIES = {
    "infantry",
    "gurkha",
    "motorized",
    "armor",
    "fighter",
    "bomber",
    "escort",
    "carrier",
    "submarine",
    "capital",
    "cruiser",
    "transport",
    "cavalry",
}

EXPECTED_TYPES = {
    "INFANTRY",
    "MILITIA",
    "GARRISON",
    "MARINE",
    "PARATROOPER",
    "CAVALRY",
    "MOUNTAIN",
    "d_05",
    "MOTORIZED",
    "MECHANIZED",
    "HQ",
    "PANZER",
    "FIGHTER",
    "INTERCEPTOR",
    "ESCORT",
    "ROCKET_INTERCEPTOR",
    "BOMBER",
    "CAS",
    "TACTICAL",
    "NAVAL",
    "STRATEGIC",
    "TRANSPORTPLANE",
    "DESTROYER",
    "LIGHT_CRUISER",
    "HEAVY_CRUISER",
    "BATTLECRUISER",
    "BATTLESHIP",
    "CARRIER",
    "escort_carrier",
    "SUBMARINE",
    "nuclear_submarine",
    "TRANSPORT",
}

SPRITE_PATTERN = re.compile(
    r"^T-(?P<type>.+?) A-(?P<action>STAND|WALK|FIRE) C-IND"
    r"(?: L-1)?(?: D-(?P<direction>E|NE|N|NW|W|SW|S|SE))?\.spr$"
)
BITMAP_PATTERN = re.compile(r'^\s*Bitmap\s*=\s*"([^"]+)"', re.MULTILINE)
PALETTE_PATTERN = re.compile(r'^\s*Palette\s*=\s*"([^"]+)"', re.MULTILINE)
FRAMES_PATTERN = re.compile(r"^\s*Frames\s*=\s*(\d+)", re.MULTILINE)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bmp_info(path: pathlib.Path) -> tuple[int, int, int, tuple[int, int, int]]:
    data = path.read_bytes()
    if len(data) < 58 or data[:2] != b"BM":
        raise ValueError("not a Windows BMP")
    width, height = struct.unpack_from("<ii", data, 18)
    bits = struct.unpack_from("<H", data, 28)[0]
    blue, green, red, _ = struct.unpack_from("<BBBB", data, 54)
    return width, abs(height), bits, (red, green, blue)


def manifest_issues() -> tuple[list[str], Counter[str], set[str]]:
    issues: list[str] = []
    counts: Counter[str] = Counter()
    families: set[str] = set()
    if not MANIFEST.is_file():
        return ["docs/v4_sprite_manifest.csv is missing"], counts, families

    rows: list[dict[str, str]] = []
    with MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        rows.extend(csv.DictReader(stream))
    paths = [row.get("path") or "" for row in rows]
    if len(paths) != len(set(paths)):
        issues.append("sprite manifest contains duplicate output paths")
    for line, row in enumerate(rows, 2):
        relative = row.get("path") or ""
        kind = row.get("kind") or ""
        family = row.get("family") or ""
        source = re.sub(r"#panel=\d+$", "", row.get("source") or "")
        counts[kind] += 1
        families.add(family)
        output = ROOT / relative
        if not output.is_file():
            issues.append(f"line {line}: missing output {relative}")
        elif sha256(output) != (row.get("sha256") or "").lower():
            issues.append(f"line {line}: stale hash for {relative}")
        if not (ROOT / source).is_file():
            issues.append(f"line {line}: missing source {source}")
        if row.get("provenance") != (
            "generated original India service sprite; not derived from another mod"
        ):
            issues.append(f"line {line}: invalid provenance disclosure")
    if counts != Counter({"bmp": 234, "spr": 595}):
        issues.append(f"unexpected sprite-manifest counts: {dict(counts)}")
    if families != EXPECTED_FAMILIES:
        issues.append(
            "sprite-family coverage mismatch: "
            f"missing={sorted(EXPECTED_FAMILIES - families)}, "
            f"stale={sorted(families - EXPECTED_FAMILIES)}"
        )
    return issues, counts, families


def descriptor_issues() -> tuple[list[str], set[str]]:
    issues: list[str] = []
    unit_types: set[str] = set()
    descriptors = sorted(SPRITE_DIR.glob("T-* C-IND*.spr"))
    if len(descriptors) != 595:
        issues.append(f"expected 595 C-IND descriptors, found {len(descriptors)}")
    for path in descriptors:
        filename = SPRITE_PATTERN.match(path.name)
        if not filename:
            issues.append(f"{path.name}: invalid C-IND descriptor filename")
            continue
        unit_types.add(filename.group("type"))
        action = filename.group("action")
        direction = filename.group("direction")
        if action == "STAND" and direction:
            issues.append(f"{path.name}: stand descriptor should not have a direction")
        if action != "STAND" and not direction:
            issues.append(f"{path.name}: moving/firing descriptor lacks a direction")

        text = path.read_text(encoding="ascii")
        bitmap = BITMAP_PATTERN.search(text)
        palette = PALETTE_PATTERN.search(text)
        frames = FRAMES_PATTERN.search(text)
        if not bitmap or not palette or not frames:
            issues.append(f"{path.name}: incomplete sprite definition")
            continue
        bitmap_path = BITMAP_DIR / bitmap.group(1)
        palette_path = PALETTE_DIR / palette.group(1)
        if not bitmap_path.is_file():
            issues.append(f"{path.name}: missing bitmap {bitmap.group(1)}")
            continue
        if not palette_path.is_file():
            issues.append(f"{path.name}: missing palette {palette.group(1)}")
            continue
        frame_count = int(frames.group(1))
        try:
            width, height, bits, transparent = bmp_info(bitmap_path)
            p_width, p_height, p_bits, p_transparent = bmp_info(palette_path)
        except ValueError as exc:
            issues.append(f"{path.name}: {exc}")
            continue
        if (width, height, bits) != (96 * frame_count, 96, 8):
            issues.append(
                f"{path.name}: bitmap is {width}x{height} {bits}-bit for "
                f"{frame_count} frames"
            )
        if transparent != (255, 0, 255):
            issues.append(f"{bitmap_path.name}: palette index 0 is not magenta")
        if (p_width, p_height, p_bits) != (4, 4, 8):
            issues.append(
                f"{palette_path.name}: expected 4x4 8-bit palette bitmap, "
                f"got {p_width}x{p_height} {p_bits}-bit"
            )
        if p_transparent != (255, 0, 255):
            issues.append(f"{palette_path.name}: palette index 0 is not magenta")

    if unit_types != EXPECTED_TYPES:
        issues.append(
            "sprite unit-type coverage mismatch: "
            f"missing={sorted(EXPECTED_TYPES - unit_types)}, "
            f"stale={sorted(unit_types - EXPECTED_TYPES)}"
        )
    return issues, unit_types


def main() -> int:
    manifest_errors, counts, families = manifest_issues()
    descriptor_errors, unit_types = descriptor_issues()
    errors = manifest_errors + descriptor_errors

    print("A Union Before Midnight V4 service-sprite audit")
    print(f"  Original visual families: {len(families)}")
    print(f"  Covered engine unit types: {len(unit_types)}")
    print(f"  Bitmap/palette files: {counts['bmp']}")
    print(f"  C-IND descriptors: {counts['spr']}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("V4 SERVICE-SPRITE GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
