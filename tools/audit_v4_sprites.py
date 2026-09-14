#!/usr/bin/env python3
"""Validate the active India V4 map-sprite package without launching the game."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
import sys
from collections import Counter
from functools import lru_cache


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools/v4_config.json"
SPRITE_DIR = ROOT / "mod/gfx/map/units"
BITMAP_DIR = SPRITE_DIR / "bmp"
PALETTE_DIR = ROOT / "mod/gfx/palette"

EXPECTED_TYPES = {
    "INFANTRY",
    "MILITIA",
    "GARRISON",
    "MARINE",
    "PARATROOPER",
    "CAVALRY",
    "BERGSJAEGER",
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
    r"(?: L-\d+)?(?: D-(?P<direction>E|NE|N|NW|W|SW|S|SE))?\.spr$"
)
BITMAP_PATTERN = re.compile(r'^\s*Bitmap\s*=\s*"([^"]+)"', re.MULTILINE)
PALETTE_PATTERN = re.compile(r'^\s*Palette\s*=\s*"([^"]+)"', re.MULTILINE)
FRAMES_PATTERN = re.compile(r"^\s*Frames\s*=\s*(\d+)", re.MULTILINE)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bmp_info(path: pathlib.Path) -> tuple[bytes, int, int, int, int]:
    data = path.read_bytes()
    if len(data) < 58 or data[:2] != b"BM":
        raise ValueError("not a Windows BMP")
    width, height = struct.unpack_from("<ii", data, 18)
    bits = struct.unpack_from("<H", data, 28)[0]
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    return data, width, height, bits, pixel_offset


def resolve_palette(name: str) -> pathlib.Path | None:
    direct = PALETTE_DIR / name
    if direct.is_file():
        return direct
    if not pathlib.Path(name).suffix:
        with_extension = PALETTE_DIR / f"{name}.bmp"
        if with_extension.is_file():
            return with_extension
    return None


def border_indexes(path: pathlib.Path) -> list[int]:
    data, width, signed_height, bits, pixel_offset = bmp_info(path)
    if bits != 8:
        raise ValueError(f"expected 8-bit indexed BMP, got {bits}-bit")
    height = abs(signed_height)
    stride = ((width * bits + 31) // 32) * 4

    def index_at(x: int, y: int) -> int:
        row = height - 1 - y if signed_height > 0 else y
        return data[pixel_offset + row * stride + x]

    indexes = [index_at(x, 0) for x in range(width)]
    indexes.extend(index_at(x, height - 1) for x in range(width))
    indexes.extend(index_at(0, y) for y in range(1, height - 1))
    indexes.extend(index_at(width - 1, y) for y in range(1, height - 1))
    return indexes


def palette_color(path: pathlib.Path, index: int) -> tuple[int, int, int]:
    data, _, _, bits, _ = bmp_info(path)
    if bits != 8:
        raise ValueError(f"expected 8-bit palette BMP, got {bits}-bit")
    blue, green, red, _ = struct.unpack_from("<BBBB", data, 54 + index * 4)
    return red, green, blue


@lru_cache(maxsize=None)
def transparent_border_ratio(bitmap: pathlib.Path, palette: pathlib.Path) -> float:
    counts = Counter(border_indexes(bitmap))
    transparent = sum(
        count
        for index, count in counts.items()
        if palette_color(palette, index) == (255, 0, 255)
    )
    return transparent / sum(counts.values())


def stable_profile_issues() -> tuple[list[str], int]:
    """Require stock fallback rendering in the live overlay.

    The archived source sheets and manifest remain available for future art
    work, but no custom service-sprite descriptor or palette is shipped until
    it has survived an in-engine soak test.
    """
    issues: list[str] = []
    custom_descriptors = sorted(SPRITE_DIR.glob("*.spr")) if SPRITE_DIR.exists() else []
    custom_bitmaps = sorted(BITMAP_DIR.glob("*")) if BITMAP_DIR.exists() else []
    custom_palettes = sorted(PALETTE_DIR.glob("*")) if PALETTE_DIR.exists() else []
    if custom_descriptors:
        issues.append(
            f"live overlay still contains {len(custom_descriptors)} custom service-sprite descriptors"
        )
    if custom_bitmaps:
        issues.append(f"live overlay still contains {len(custom_bitmaps)} service-sprite bitmaps")
    if custom_palettes:
        issues.append(f"live overlay still contains {len(custom_palettes)} service-sprite palettes")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    stock_root = pathlib.Path(config["game_root"]) / "gfx/map/units"
    stock_descriptors = list(stock_root.glob("*.spr")) if stock_root.is_dir() else []
    if len(stock_descriptors) < 100:
        issues.append(
            f"Darkest Hour's stock fallback renderer is unavailable or incomplete: {stock_root}"
        )
    return issues, len(stock_descriptors)


def main() -> int:
    errors, stock_descriptor_count = stable_profile_issues()

    print("A Union Before Midnight V4 rendering audit")
    print("  Visual mode: stable Darkest Hour service-sprite fallback")
    print(f"  Stock fallback descriptors available: {stock_descriptor_count}")
    print("  Custom live service-sprite descriptors: 0 required")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("V4 STABLE RENDERING GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
