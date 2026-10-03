#!/usr/bin/env python3
"""Clone proven Blood and Iron sprite definitions into the India namespace."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOKEN_PATTERN = re.compile(r"(?:^| )(T|A|C|L|D)-([^ ]+)")
FIELD_PATTERNS = {
    key: re.compile(rf'^\s*{key}\s*=\s*(?:"([^"]+)"|(\S+))', re.I | re.M)
    for key in ("Bitmap", "Palette", "Frames")
}
DIRECTION_ANGLE = {
    "E": 0,
    "NE": 1,
    "N": 2,
    "NW": 3,
    "W": 4,
    "SW": 5,
    "S": 6,
    "SE": 7,
}
TYPE_ALIASES = {
    "escort": "fighter",
    "garrison": "infantry",
    "mountain": "bergsjaeger",
    "nuclear_submarine": "submarine",
    "strategic": "bomber",
}
SPECIAL_DONOR_TYPES = {
    # Gurkha formations use DH Full's mountain unit family, while retaining
    # the dedicated animated Gurkha service art imported from the donor set.
    "bergsjaeger": "d_05",
}
PREFERRED_COUNTRIES = {
    "d_05": ("ENG", "AST", "NZL"),
    "infantry": ("AST", "ENG", "CAN"),
    "militia": ("AST", "ENG", "CAN"),
    "garrison": ("AST", "ENG", "CAN"),
    "hq": ("AST", "ENG"),
    "bergsjaeger": ("AST", "ENG"),
    "mountain": ("AST", "ENG"),
    "marine": ("AST", "ENG"),
    "paratrooper": ("AST", "ENG"),
}


@dataclass(frozen=True)
class SpriteRecord:
    path: pathlib.Path
    unit_type: str
    action: str
    country: str | None
    level: int | None
    direction: str | None
    bitmap: str
    palette: str
    frames: int


def metadata(path: pathlib.Path) -> tuple[str, str, str | None, int | None, str | None]:
    tokens = {key: value for key, value in TOKEN_PATTERN.findall(path.stem)}
    level_text = tokens.get("L", "")
    return (
        tokens.get("T", ""),
        tokens.get("A", ""),
        tokens.get("C"),
        int(level_text) if level_text.isdigit() else None,
        tokens.get("D"),
    )


def field(text: str, name: str) -> str | None:
    match = FIELD_PATTERNS[name].search(text)
    if not match:
        return None
    return match.group(1) or match.group(2)


def record(path: pathlib.Path) -> SpriteRecord | None:
    text = path.read_text(encoding="ascii", errors="replace")
    bitmap = field(text, "Bitmap")
    palette = field(text, "Palette")
    frame_text = field(text, "Frames")
    unit_type, action, country, level, direction = metadata(path)
    if not unit_type or not action or not bitmap or not palette or not frame_text:
        return None
    return SpriteRecord(
        path=path,
        unit_type=unit_type,
        action=action,
        country=country,
        level=level,
        direction=direction,
        bitmap=bitmap,
        palette=palette,
        frames=int(frame_text),
    )


def directional_distance(left: str | None, right: str | None) -> int:
    if left == right:
        return 0
    if left not in DIRECTION_ANGLE or right not in DIRECTION_ANGLE:
        return 4
    distance = abs(DIRECTION_ANGLE[left] - DIRECTION_ANGLE[right])
    return min(distance, 8 - distance)


def resolve_asset(root: pathlib.Path, name: str) -> pathlib.Path | None:
    direct = root / name
    if direct.is_file():
        return direct
    if not pathlib.Path(name).suffix:
        with_extension = root / f"{name}.bmp"
        if with_extension.is_file():
            return with_extension
    return None


def copy_if_changed(source: pathlib.Path, destination: pathlib.Path) -> None:
    if destination.is_file() and destination.read_bytes() == source.read_bytes():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def choose_donor(
    target: SpriteRecord,
    by_bitmap: dict[str, list[SpriteRecord]],
    by_type_action: dict[tuple[str, str], list[SpriteRecord]],
) -> tuple[SpriteRecord | None, bool]:
    exact = by_bitmap.get(target.bitmap.casefold(), [])
    target_type = target.unit_type.casefold()
    donor_type = SPECIAL_DONOR_TYPES.get(
        target_type,
        TYPE_ALIASES.get(target_type, target_type),
    )
    if target_type in SPECIAL_DONOR_TYPES:
        candidates = by_type_action.get((donor_type, target.action.upper()), [])
        exact = []
    else:
        candidates = exact or by_type_action.get((donor_type, target.action.upper()), [])
    if not candidates:
        return None, bool(exact)

    target_level = target.level or 1
    preferences = PREFERRED_COUNTRIES.get(
        target.unit_type.casefold(),
        ("ENG", "AST", "MIN", "U02"),
    )

    def score(candidate: SpriteRecord) -> tuple[int, str]:
        value = 0
        if candidate.bitmap.casefold() == target.bitmap.casefold():
            value += 2000
        if candidate.unit_type.casefold() == donor_type:
            value += 1000
        if candidate.action.upper() == target.action.upper():
            value += 300
        value += 200 - directional_distance(candidate.direction, target.direction) * 30
        if candidate.country in preferences:
            value += 100 - preferences.index(candidate.country) * 10
        value -= abs((candidate.level or 1) - target_level) * 3
        if target.action.upper() == "WALK" and candidate.frames >= 7:
            value += 100
        if target.action.upper() == "FIRE" and candidate.frames >= 3:
            value += 50
        return value, candidate.path.name.casefold()

    return max(candidates, key=score), bool(exact)


def rebuild(repository_root: pathlib.Path, donor_mod: pathlib.Path) -> int:
    target_mod = repository_root / "mod"
    target_sprite_dir = target_mod / "gfx/map/units"
    target_bitmap_dir = target_sprite_dir / "bmp"
    target_palette_dir = target_mod / "gfx/palette"
    donor_sprite_dir = donor_mod / "gfx/map/units"
    donor_bitmap_dir = donor_sprite_dir / "bmp"
    donor_palette_dir = donor_mod / "gfx/palette"

    for required in (
        target_sprite_dir,
        donor_sprite_dir,
        donor_bitmap_dir,
        donor_palette_dir,
    ):
        if not required.is_dir():
            print(f"ERROR: required sprite directory is missing: {required}")
            return 1

    by_bitmap: dict[str, list[SpriteRecord]] = defaultdict(list)
    by_type_action: dict[tuple[str, str], list[SpriteRecord]] = defaultdict(list)
    donor_count = 0
    for path in sorted(donor_sprite_dir.glob("*.spr")):
        donor = record(path)
        if not donor:
            continue
        donor_count += 1
        by_bitmap[donor.bitmap.casefold()].append(donor)
        by_type_action[(donor.unit_type.casefold(), donor.action.upper())].append(donor)

    failures: list[str] = []
    provenance = Counter()
    frame_counts = Counter()
    targets = sorted(target_sprite_dir.glob("*C-IND*.spr"))
    for target_path in targets:
        target = record(target_path)
        if not target:
            failures.append(f"{target_path.name}: incomplete target descriptor")
            continue
        donor, exact = choose_donor(target, by_bitmap, by_type_action)
        if not donor:
            failures.append(f"{target_path.name}: no donor animation is available")
            continue
        bitmap_source = resolve_asset(donor_bitmap_dir, donor.bitmap)
        palette_source = resolve_asset(donor_palette_dir, donor.palette)
        if not bitmap_source:
            failures.append(f"{target_path.name}: donor bitmap {donor.bitmap!r} is missing")
            continue
        if not palette_source:
            failures.append(f"{target_path.name}: donor palette {donor.palette!r} is missing")
            continue

        target_path.write_bytes(donor.path.read_bytes())
        copy_if_changed(bitmap_source, target_bitmap_dir / bitmap_source.name)
        copy_if_changed(palette_source, target_palette_dir / palette_source.name)
        provenance["exact" if exact else "replacement"] += 1
        frame_counts[donor.frames] += 1

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        print(f"India sprite rebuild failed with {len(failures)} error(s).")
        return 1

    print("Rebuilt India service sprites from proven Blood and Iron definitions:")
    print(f"  donor descriptors indexed: {donor_count}")
    print(f"  India descriptors rebuilt: {len(targets)}")
    print(f"  exact donor pairings: {provenance['exact']}")
    print(f"  placeholder replacements: {provenance['replacement']}")
    print(f"  selected frame counts: {dict(sorted(frame_counts.items()))}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--donor", type=pathlib.Path, required=True)
    args = parser.parse_args()
    return rebuild(args.root.resolve(), args.donor.resolve())


if __name__ == "__main__":
    sys.exit(main())
