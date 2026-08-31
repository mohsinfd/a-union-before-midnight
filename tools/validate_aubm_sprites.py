#!/usr/bin/env python3
"""Deep integrity gate for the A Union Before Midnight India sprite package."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIRECTIONS = ("E", "NE", "N", "NW", "W", "SW", "S", "SE")
EXPECTED_KEYS = {
    "infantry": "d_41",
    "cavalry": "d_42",
    "motorized": "d_43",
    "mechanized": "d_44",
    "light_armor": "d_45",
    "armor": "d_46",
    "paratrooper": "d_47",
    "marine": "d_48",
    "bergsjaeger": "d_49",
    "garrison": "d_50",
    "hq": "d_51",
    "militia": "d_52",
    "multi_role": "d_53",
    "interceptor": "d_54",
    "strategic_bomber": "d_55",
    "tactical_bomber": "d_56",
    "naval_bomber": "d_57",
    "cas": "d_58",
    "transport_plane": "d_59",
    "flying_bomb": "d_60",
    "flying_rocket": "d_61",
    "battleship": "d_62",
    "light_cruiser": "d_63",
    "heavy_cruiser": "d_64",
    "battlecruiser": "d_65",
    "destroyer": "d_66",
    "carrier": "d_67",
    "escort_carrier": "d_68",
    "submarine": "d_69",
    "nuclear_submarine": "d_70",
    "transport": "d_71",
    "light_carrier": "d_72",
    "rocket_interceptor": "d_73",
    "d_rsv_33": "d_74",
    "d_rsv_34": "d_75",
    "d_rsv_35": "d_76",
    "d_rsv_36": "d_77",
    "d_rsv_37": "d_78",
    "d_rsv_38": "d_79",
    "d_rsv_39": "d_80",
    "d_rsv_40": "d_81",
}
SPECIAL_ROLES = {
    "d_rsv_33": "Gurkha Rifles",
    "d_rsv_34": "Frontier Force",
    "d_rsv_35": "Chindit Columns",
    "d_rsv_36": "Indian Airborne",
    "d_rsv_37": "Coromandel Marines",
    "d_rsv_38": "Guards Armour",
    "d_rsv_39": "Guards Motorised",
    "d_rsv_40": "Indian Pioneers",
}
DESCRIPTOR_NAME = re.compile(
    r"^T-(?P<key>[^ ]+) A-(?P<action>STAND|WALK|FIRE) C-IND L-1"
    r"(?: D-(?P<direction>E|NE|N|NW|W|SW|S|SE))?\.spr$"
)
FIELDS = {
    "bitmap": re.compile(r'^\s*Bitmap\s*=\s*"([^"]+)"\s*$', re.MULTILINE),
    "palette": re.compile(r'^\s*Palette\s*=\s*"([^"]+)"\s*$', re.MULTILINE),
    "frames": re.compile(r"^\s*Frames\s*=\s*(\d+)\s*$", re.MULTILINE),
    "speed": re.compile(r"^\s*Speed\s*=\s*([0-9.]+)\s*$", re.MULTILINE),
    "origin": re.compile(
        r"^\s*Origin\s*=\s*\{\s*x\s*=\s*(-?\d+)\s+y\s*=\s*(-?\d+)\s*\}\s*$",
        re.MULTILINE,
    ),
}


@dataclass(frozen=True)
class Bmp:
    path: pathlib.Path
    data: bytes
    width: int
    signed_height: int
    bits: int
    compression: int
    pixel_offset: int
    dib_size: int
    colors_used: int

    @property
    def height(self) -> int:
        return abs(self.signed_height)

    @property
    def stride(self) -> int:
        return ((self.width * self.bits + 31) // 32) * 4


@dataclass(frozen=True)
class Descriptor:
    path: pathlib.Path
    key: str
    action: str
    direction: str | None
    bitmap_name: str
    palette_name: str
    frames: int
    speed: float


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def read_bmp(path: pathlib.Path) -> Bmp:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("not a Windows BMP")
    declared_size = struct.unpack_from("<I", data, 2)[0]
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"unsupported DIB header size {dib_size}")
    width, signed_height = struct.unpack_from("<ii", data, 18)
    planes, bits = struct.unpack_from("<HH", data, 26)
    compression = struct.unpack_from("<I", data, 30)[0]
    colors_used = struct.unpack_from("<I", data, 46)[0]
    if declared_size not in (0, len(data)):
        raise ValueError(f"header size {declared_size} does not match {len(data)} bytes")
    if width <= 0 or signed_height == 0:
        raise ValueError(f"invalid dimensions {width}x{signed_height}")
    if planes != 1:
        raise ValueError(f"invalid plane count {planes}")
    if bits != 8:
        raise ValueError(f"expected an 8-bit indexed BMP, got {bits}-bit")
    if compression != 0:
        raise ValueError(f"expected uncompressed BI_RGB data, compression={compression}")
    bmp = Bmp(
        path=path,
        data=data,
        width=width,
        signed_height=signed_height,
        bits=bits,
        compression=compression,
        pixel_offset=pixel_offset,
        dib_size=dib_size,
        colors_used=colors_used,
    )
    if pixel_offset < 14 + dib_size or pixel_offset + bmp.stride * bmp.height > len(data):
        raise ValueError("pixel array lies outside the BMP file")
    return bmp


def palette_colors(palette: Bmp) -> list[tuple[int, int, int]]:
    count = palette.colors_used or (1 << palette.bits)
    table_start = 14 + palette.dib_size
    table_end = table_start + count * 4
    if table_end > palette.pixel_offset or table_end > len(palette.data):
        raise ValueError(f"declared {count}-entry palette does not fit before pixel data")
    colors: list[tuple[int, int, int]] = []
    for offset in range(table_start, table_end, 4):
        blue, green, red, _ = struct.unpack_from("<BBBB", palette.data, offset)
        colors.append((red, green, blue))
    return colors


def pixel_index(bmp: Bmp, x: int, y: int) -> int:
    source_y = bmp.height - 1 - y if bmp.signed_height > 0 else y
    return bmp.data[bmp.pixel_offset + source_y * bmp.stride + x]


def frame_indexes(bmp: Bmp, frame: int, frame_width: int) -> bytes:
    start_x = frame * frame_width
    output = bytearray(frame_width * bmp.height)
    cursor = 0
    for y in range(bmp.height):
        source_y = bmp.height - 1 - y if bmp.signed_height > 0 else y
        row_start = bmp.pixel_offset + source_y * bmp.stride + start_x
        output[cursor : cursor + frame_width] = bmp.data[row_start : row_start + frame_width]
        cursor += frame_width
    return bytes(output)


def parse_descriptor(path: pathlib.Path, errors: list[str]) -> Descriptor | None:
    match = DESCRIPTOR_NAME.fullmatch(path.name)
    if not match:
        errors.append(f"descriptor filename is outside the C-IND L-1 contract: {path.name}")
        return None
    try:
        text = path.read_text(encoding="ascii")
    except UnicodeDecodeError:
        errors.append(f"descriptor is not ASCII: {path.name}")
        return None
    if text.count("{") != 2 or text.count("}") != 2 or not re.search(r"^Sprite\s*=\s*\{", text):
        errors.append(f"descriptor has malformed Sprite braces: {path.name}")
        return None
    values: dict[str, re.Match[str]] = {}
    for field, pattern in FIELDS.items():
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            errors.append(f"descriptor must contain one {field} field: {path.name}")
            return None
        values[field] = matches[0]
    frames = int(values["frames"].group(1))
    speed = float(values["speed"].group(1))
    if frames < 1:
        errors.append(f"descriptor has invalid frame count {frames}: {path.name}")
    if speed < 0 or (match.group("action") in {"WALK", "FIRE"} and speed == 0):
        errors.append(f"descriptor has invalid speed {speed}: {path.name}")
    return Descriptor(
        path=path,
        key=match.group("key"),
        action=match.group("action"),
        direction=match.group("direction"),
        bitmap_name=values["bitmap"].group(1),
        palette_name=values["palette"].group(1),
        frames=frames,
        speed=speed,
    )


def registry_sprite_fields(path: pathlib.Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    fields: dict[str, str] = {}
    current: str | None = None
    depth = 0
    sprite_count = 0
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        if current is None:
            block = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", line)
            if block and block.group(1) in EXPECTED_KEYS:
                current = block.group(1)
                if current in fields:
                    errors.append(f"duplicate registry block {current} at line {line_number}")
                depth = line.count("{") - line.count("}")
                sprite_count = 0
            continue
        sprite = re.match(r"^\s*sprite\s*=\s*(\S+)", line, re.IGNORECASE)
        if sprite:
            sprite_count += 1
            fields[current] = sprite.group(1)
        depth += line.count("{") - line.count("}")
        if depth == 0:
            if sprite_count != 1:
                errors.append(f"registry block {current} has {sprite_count} sprite fields")
            current = None
        elif depth < 0:
            errors.append(f"registry braces underflow at line {line_number}")
            current = None
    if current is not None:
        errors.append(f"unclosed registry block {current}")
    return fields, errors


def snapshot(root: pathlib.Path, manifest: dict) -> dict[str, str]:
    mod_root = root / "mod"
    paths = [root / "mod/db/units/division_types.txt", root / "mod/gfx/map/units/AUBM-IND-GENERATED-MANIFEST.json"]
    paths.extend(mod_root / entry["path"] for entry in manifest["files"])
    return {
        path.resolve().relative_to(root.resolve()).as_posix(): sha256(path)
        for path in paths
    }


def static_validate(root: pathlib.Path, game_root: pathlib.Path) -> tuple[list[str], dict, dict[str, int]]:
    errors: list[str] = []
    counters: Counter[str] = Counter()
    mod_root = root / "mod"
    sprite_root = mod_root / "gfx/map/units"
    bitmap_root = sprite_root / "bmp"
    palette_root = mod_root / "gfx/palette"
    manifest_path = sprite_root / "AUBM-IND-GENERATED-MANIFEST.json"
    registry_path = mod_root / "db/units/division_types.txt"
    if not manifest_path.is_file():
        return [f"generated manifest is missing: {manifest_path}"], {}, dict(counters)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"generated manifest is invalid: {exc}"], {}, dict(counters)

    if manifest.get("schema") != 1 or manifest.get("namespace") != "AUBM-IND":
        errors.append("manifest schema or namespace is invalid")
    if manifest.get("country") != "IND" or manifest.get("unit_count") != 41:
        errors.append("manifest must declare country IND and exactly 41 units")

    fields, registry_errors = registry_sprite_fields(registry_path)
    errors.extend(registry_errors)
    for unit_type, expected_key in EXPECTED_KEYS.items():
        actual = fields.get(unit_type)
        if actual != expected_key:
            errors.append(f"registry {unit_type} sprite is {actual!r}, expected {expected_key!r}")
    if len(set(fields.values())) != 41:
        errors.append("unit registry does not expose 41 unique sprite keys")

    families = manifest.get("families", [])
    if len(families) != 41:
        errors.append(f"manifest contains {len(families)} families, expected 41")
    family_by_key: dict[str, dict] = {}
    for family in families:
        key = family.get("sprite_key")
        if key in family_by_key:
            errors.append(f"duplicate manifest family for sprite key {key}")
        family_by_key[key] = family
        unit_type = family.get("unit_type")
        if EXPECTED_KEYS.get(unit_type) != key:
            errors.append(f"manifest family mapping is invalid: {unit_type!r} -> {key!r}")
        if key in SPECIAL_ROLES and family.get("role") != SPECIAL_ROLES[key]:
            errors.append(f"special family {key} has role {family.get('role')!r}")
        expected_donor = "Darkest Hour core" if key == "d_70" else "Blood and Iron v1.1"
        if family.get("source_mod") != expected_donor:
            errors.append(f"family {key} uses {family.get('source_mod')!r}, expected {expected_donor!r}")
        if family.get("walk_descriptors") != 8:
            errors.append(f"family {key} does not have eight-direction donor movement")
        if family.get("stand_descriptors") != 1 or family.get("fire_descriptors", 0) < 1:
            errors.append(f"family {key} lacks donor stand or combat animation")
        if family.get("minimum_walk_frames", 0) <= 1 or family.get("minimum_fire_frames", 0) <= 1:
            errors.append(f"family {key} contains a static movement/combat strip")
    signatures = [family.get("stand_signature") for family in families]
    if len(signatures) != len(set(signatures)):
        errors.append("two target families share the same bitmap+palette stand signature")

    donor_roots = {
        "Blood and Iron v1.1": game_root / "Mods/Blood and Iron v1.1",
        "Darkest Hour core": game_root,
    }
    manifest_entries: dict[str, dict] = {}
    for entry in manifest.get("files", []):
        relative = entry.get("path", "")
        if relative in manifest_entries:
            errors.append(f"duplicate manifest file entry: {relative}")
            continue
        manifest_entries[relative] = entry
        target = (mod_root / relative).resolve()
        if not (within(target, sprite_root) or within(target, palette_root)):
            errors.append(f"manifest path escapes generated roots: {relative}")
            continue
        kind = entry.get("kind")
        if kind in {"bitmap", "palette"} and not target.name.startswith("AUBM-IND-"):
            errors.append(f"manifested visual leaves the AUBM-IND namespace: {relative}")
        if kind == "descriptor" and not DESCRIPTOR_NAME.fullmatch(target.name):
            errors.append(f"manifested descriptor leaves the C-IND namespace: {relative}")
        if kind not in {"bitmap", "palette", "descriptor"}:
            errors.append(f"manifest file has unknown kind {kind!r}: {relative}")
        if not target.is_file():
            errors.append(f"manifest file is missing: {relative}")
            continue
        target_hash = sha256(target)
        if target_hash != entry.get("sha256"):
            errors.append(f"manifest hash mismatch: {relative}")
        if target.stat().st_size != entry.get("bytes"):
            errors.append(f"manifest byte count mismatch: {relative}")
        source_root = donor_roots.get(entry.get("source_mod"))
        if source_root is None:
            errors.append(f"unknown donor for {relative}: {entry.get('source_mod')!r}")
            continue
        source = (source_root / entry.get("source_path", "")).resolve()
        if not within(source, source_root) or not source.is_file():
            errors.append(f"donor provenance is missing or unsafe: {relative}")
            continue
        source_hash = sha256(source)
        if source_hash != entry.get("source_sha256"):
            errors.append(f"donor provenance hash mismatch: {relative}")
        if entry.get("kind") in {"bitmap", "palette"} and target_hash != source_hash:
            errors.append(f"copied visual is not byte-identical to its donor: {relative}")
        counters[f"manifest_{entry.get('kind', 'unknown')}"] += 1

    manifest_paths = set(manifest_entries)
    actual_namespaced = {
        path.resolve().relative_to(mod_root.resolve()).as_posix()
        for path in list(bitmap_root.glob("AUBM-IND-*.bmp"))
        + list(palette_root.glob("AUBM-IND-*.bmp"))
    }
    actual_descriptors = {
        path.resolve().relative_to(mod_root.resolve()).as_posix()
        for path in sprite_root.glob("T-* C-IND L-1*.spr")
        if (match := DESCRIPTOR_NAME.fullmatch(path.name))
        and match.group("key") in set(EXPECTED_KEYS.values())
    }
    untracked = (actual_namespaced | actual_descriptors) - manifest_paths
    if untracked:
        errors.append(f"generated namespace contains {len(untracked)} unmanifested file(s)")

    descriptors: list[Descriptor] = []
    for relative, entry in manifest_entries.items():
        if entry.get("kind") != "descriptor":
            continue
        descriptor = parse_descriptor(mod_root / relative, errors)
        if descriptor:
            descriptors.append(descriptor)
    by_key: dict[str, list[Descriptor]] = defaultdict(list)
    for descriptor in descriptors:
        by_key[descriptor.key].append(descriptor)
    for key in EXPECTED_KEYS.values():
        records = by_key.get(key, [])
        stand = [item for item in records if item.action == "STAND"]
        walk = [item for item in records if item.action == "WALK"]
        fire = [item for item in records if item.action == "FIRE"]
        if len(stand) != 1 or stand and stand[0].direction is not None:
            errors.append(f"sprite key {key} must have one undirected stand descriptor")
        if {item.direction for item in walk} != set(DIRECTIONS) or len(walk) != 8:
            errors.append(f"sprite key {key} must have exactly eight walk directions")
        if not fire:
            errors.append(f"sprite key {key} has no combat descriptor")
        if any(item.frames <= 1 for item in walk + fire):
            errors.append(f"sprite key {key} uses a one-frame movement/combat descriptor")

    bmp_cache: dict[pathlib.Path, Bmp] = {}
    palette_cache: dict[pathlib.Path, tuple[Bmp, list[tuple[int, int, int]]]] = {}
    visual_cache: dict[tuple[str, str, int], list[str]] = {}
    stand_signatures: dict[str, str] = {}
    for descriptor in descriptors:
        key_token = descriptor.key.upper()
        if not descriptor.bitmap_name.startswith(f"AUBM-IND-{key_token}-BMP-"):
            errors.append(f"bitmap leaves key namespace in {descriptor.path.name}")
        if not descriptor.palette_name.startswith(f"AUBM-IND-{key_token}-PAL-"):
            errors.append(f"palette leaves key namespace in {descriptor.path.name}")
        bitmap_path = bitmap_root / descriptor.bitmap_name
        palette_path = palette_root / descriptor.palette_name
        for asset, label in ((bitmap_path, "bitmap"), (palette_path, "palette")):
            relative = asset.resolve().relative_to(mod_root.resolve()).as_posix() if asset.exists() else ""
            if not asset.is_file():
                errors.append(f"dangling {label} reference in {descriptor.path.name}: {asset.name}")
            elif relative not in manifest_entries:
                errors.append(f"unmanifested {label} reference in {descriptor.path.name}: {asset.name}")
        if not bitmap_path.is_file() or not palette_path.is_file():
            continue
        try:
            bitmap = bmp_cache.setdefault(bitmap_path, read_bmp(bitmap_path))
            if palette_path not in palette_cache:
                palette_bmp = read_bmp(palette_path)
                palette_cache[palette_path] = (palette_bmp, palette_colors(palette_bmp))
            _, colors = palette_cache[palette_path]
        except (OSError, ValueError, struct.error) as exc:
            errors.append(f"invalid visual used by {descriptor.path.name}: {exc}")
            continue
        if bitmap.width % descriptor.frames:
            errors.append(
                f"strip width {bitmap.width} is not divisible by Frames={descriptor.frames}: {descriptor.path.name}"
            )
            continue
        frame_width = bitmap.width // descriptor.frames
        if frame_width < 8 or bitmap.height < 8:
            errors.append(f"implausibly small frame {frame_width}x{bitmap.height}: {descriptor.path.name}")
            continue
        cache_key = (sha256(bitmap_path), sha256(palette_path), descriptor.frames)
        if cache_key not in visual_cache:
            visual_errors: list[str] = []
            magenta = {index for index, color in enumerate(colors) if color == (255, 0, 255)}
            # Clausewitz-era sprite sheets use palette index 0 as the matte.
            # Most B&I palettes also color that index magenta; MDS keeps a
            # non-magenta index 0. Both are safe when the external palette is
            # present and the frame corners actually use the matte index.
            transparent_indexes = {0} | magenta
            frame_hashes: set[str] = set()
            for frame in range(descriptor.frames):
                indexes = frame_indexes(bitmap, frame, frame_width)
                if indexes and max(indexes) >= len(colors):
                    visual_errors.append(f"frame {frame} uses an index outside its {len(colors)}-color palette")
                    continue
                transparent = sum(index in transparent_indexes for index in indexes)
                if transparent == 0:
                    visual_errors.append(f"frame {frame} has no palette-managed transparency")
                if transparent == len(indexes):
                    visual_errors.append(f"frame {frame} contains no visible sprite pixels")
                corner_points = (
                    (frame * frame_width, 0),
                    ((frame + 1) * frame_width - 1, 0),
                    (frame * frame_width, bitmap.height - 1),
                    ((frame + 1) * frame_width - 1, bitmap.height - 1),
                )
                transparent_corners = sum(
                    pixel_index(bitmap, x, y) in transparent_indexes for x, y in corner_points
                )
                if transparent_corners < 3:
                    visual_errors.append(f"frame {frame} exposes its magenta matte at multiple corners")
                frame_hashes.add(hashlib.sha256(indexes).hexdigest())
            if descriptor.action in {"WALK", "FIRE"} and len(frame_hashes) < min(3, descriptor.frames):
                visual_errors.append("animated strip does not contain enough distinct donor frames")
            visual_cache[cache_key] = visual_errors
        for issue in visual_cache[cache_key]:
            errors.append(f"{descriptor.path.name}: {issue}")
        if descriptor.action == "STAND":
            signature = f"{sha256(bitmap_path)}:{sha256(palette_path)}"
            stand_signatures[descriptor.key] = signature
            declared = family_by_key.get(descriptor.key, {}).get("stand_signature")
            if declared != signature:
                errors.append(f"stand signature disagrees with manifest for {descriptor.key}")

    if len(stand_signatures) != 41 or len(set(stand_signatures.values())) != 41:
        errors.append("actual stand visuals do not provide 41 unique bitmap+palette signatures")
    if manifest.get("descriptor_count") != len(descriptors):
        errors.append(
            f"manifest descriptor count is {manifest.get('descriptor_count')}, parsed {len(descriptors)}"
        )
    counters["families"] = len(families)
    counters["descriptors"] = len(descriptors)
    counters["unique_visual_checks"] = len(visual_cache)
    counters["stand_signatures"] = len(set(stand_signatures.values()))
    return errors, manifest, dict(counters)


def check_idempotence(root: pathlib.Path, game_root: pathlib.Path, manifest: dict) -> list[str]:
    before = snapshot(root, manifest)
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        return ["cannot run repeat-build check because PowerShell is unavailable"]
    command = [
        shell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(root / "tools/Build-Aubm-IndiaSprites.ps1"),
        "-RepositoryRoot",
        str(root),
        "-GameRoot",
        str(game_root),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if result.returncode:
        output = (result.stdout + result.stderr).strip()
        return [f"repeat build failed with exit {result.returncode}: {output[-2000:]}"]
    rebuilt_manifest = json.loads(
        (root / "mod/gfx/map/units/AUBM-IND-GENERATED-MANIFEST.json").read_text(encoding="ascii")
    )
    after = snapshot(root, rebuilt_manifest)
    if before != after:
        changed = sorted(set(before) ^ set(after) | {path for path in before.keys() & after.keys() if before[path] != after[path]})
        return [f"repeat build changed {len(changed)} generated path(s): {', '.join(changed[:8])}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument(
        "--game-root",
        type=pathlib.Path,
        default=pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game"),
    )
    parser.add_argument("--skip-idempotence", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    game_root = args.game_root.resolve()

    errors, manifest, counters = static_validate(root, game_root)
    if not errors and not args.skip_idempotence:
        errors.extend(check_idempotence(root, game_root, manifest))

    print("A Union Before Midnight India sprite validation")
    print(f"  unit families: {counters.get('families', 0)} / 41")
    print(f"  descriptors: {counters.get('descriptors', 0)}")
    print(f"  copied bitmaps: {counters.get('manifest_bitmap', 0)}")
    print(f"  copied palettes: {counters.get('manifest_palette', 0)}")
    print(f"  donor descriptor provenance: {counters.get('manifest_descriptor', 0)}")
    print(f"  unique bitmap/palette stand signatures: {counters.get('stand_signatures', 0)} / 41")
    print(f"  unique strip checks: {counters.get('unique_visual_checks', 0)}")
    print(f"  repeat-build check: {'skipped' if args.skip_idempotence else 'performed'}")
    print(f"  errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("AUBM INDIA SPRITE GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
