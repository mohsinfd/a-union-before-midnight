#!/usr/bin/env python3
"""Stamp the AUBM release number into player-visible launch surfaces.

The loading screen is a legacy 24-bit BMP, so this tool draws a small,
deterministic bitmap-font badge without external image libraries.  It also
puts the same VERSION value in the 1933 scenario title and keeps the artwork
provenance hash current.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import struct
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOAD_SCREEN = pathlib.Path("mod/gfx/load_1024.bmp")
FRONTEND = pathlib.Path("mod/gfx/interface/frontend/bg_start.bmp")
SCENARIO = pathlib.Path("mod/scenarios/1933.eug")
ART_MANIFEST = pathlib.Path("docs/art_manifest.csv")

BADGE_X = 646
BADGE_Y = 684
BADGE_WIDTH = 354
BADGE_HEIGHT = 68
BADGE_FILL = (12, 24, 38)
BADGE_BORDER = (181, 151, 86)
BADGE_TEXT = (239, 226, 193)


FONT: dict[str, tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


class VisibleVersionError(RuntimeError):
    pass


def read_version(root: pathlib.Path) -> str:
    version = (root / "VERSION").read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+-]*", version):
        raise VisibleVersionError(f"VERSION cannot be rendered safely: {version!r}")
    unsupported = sorted(set(version.upper()) - set(FONT))
    if unsupported:
        raise VisibleVersionError(f"VERSION contains unsupported badge glyphs: {unsupported}")
    return version


def bmp_layout(data: bytes) -> tuple[int, int, int, int, bool]:
    if len(data) < 54 or data[:2] != b"BM":
        raise VisibleVersionError("loading screen is not a Windows BMP")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    width, signed_height = struct.unpack_from("<ii", data, 18)
    planes, bits = struct.unpack_from("<HH", data, 26)
    compression = struct.unpack_from("<I", data, 30)[0]
    if dib_size < 40 or planes != 1 or bits != 24 or compression != 0:
        raise VisibleVersionError("loading screen must be an uncompressed 24-bit BMP")
    height = abs(signed_height)
    stride = ((width * 3 + 3) // 4) * 4
    if width != 1024 or height != 768:
        raise VisibleVersionError(f"loading screen must be 1024x768, got {width}x{height}")
    if pixel_offset + stride * height > len(data):
        raise VisibleVersionError("loading screen pixel data is truncated")
    return pixel_offset, width, height, stride, signed_height < 0


def set_region_pixel(region: bytearray, x: int, y: int, colour: tuple[int, int, int]) -> None:
    if not (0 <= x < BADGE_WIDTH and 0 <= y < BADGE_HEIGHT):
        raise VisibleVersionError(f"badge drawing escaped its bounds at {x},{y}")
    offset = (y * BADGE_WIDTH + x) * 3
    red, green, blue = colour
    region[offset : offset + 3] = bytes((blue, green, red))


def fill_region_rect(
    region: bytearray,
    x: int,
    y: int,
    width: int,
    height: int,
    colour: tuple[int, int, int],
) -> None:
    for row in range(y, y + height):
        for column in range(x, x + width):
            set_region_pixel(region, column, row, colour)


def draw_text(
    region: bytearray,
    text: str,
    x: int,
    y: int,
    scale: int,
    colour: tuple[int, int, int],
) -> None:
    cursor = x
    for character in text.upper():
        glyph = FONT.get(character)
        if glyph is None:
            raise VisibleVersionError(f"unsupported badge glyph: {character!r}")
        for glyph_y, glyph_row in enumerate(glyph):
            for glyph_x, active in enumerate(glyph_row):
                if active == "1":
                    fill_region_rect(
                        region,
                        cursor + glyph_x * scale,
                        y + glyph_y * scale,
                        scale,
                        scale,
                        colour,
                    )
        cursor += 5 * scale + scale


def expected_badge(version: str) -> bytes:
    region = bytearray(BADGE_WIDTH * BADGE_HEIGHT * 3)
    fill_region_rect(region, 0, 0, BADGE_WIDTH, BADGE_HEIGHT, BADGE_FILL)
    fill_region_rect(region, 0, 0, BADGE_WIDTH, 2, BADGE_BORDER)
    fill_region_rect(region, 0, BADGE_HEIGHT - 2, BADGE_WIDTH, 2, BADGE_BORDER)
    fill_region_rect(region, 0, 0, 2, BADGE_HEIGHT, BADGE_BORDER)
    fill_region_rect(region, BADGE_WIDTH - 2, 0, 2, BADGE_HEIGHT, BADGE_BORDER)
    draw_text(region, "AUBM BUILD", 16, 10, 2, BADGE_BORDER)
    draw_text(region, version, 16, 34, 3, BADGE_TEXT)
    return bytes(region)


def badge_fits(version: str) -> bool:
    width = len(version) * 18 - 3
    return width <= BADGE_WIDTH - 32


def write_badge(path: pathlib.Path, version: str) -> None:
    if not badge_fits(version):
        raise VisibleVersionError(f"VERSION is too wide for the loading-screen badge: {version}")
    data = bytearray(path.read_bytes())
    pixel_offset, _, height, stride, top_down = bmp_layout(data)
    region = expected_badge(version)
    for local_y in range(BADGE_HEIGHT):
        image_y = BADGE_Y + local_y
        stored_y = image_y if top_down else height - 1 - image_y
        for local_x in range(BADGE_WIDTH):
            source = (local_y * BADGE_WIDTH + local_x) * 3
            target = pixel_offset + stored_y * stride + (BADGE_X + local_x) * 3
            data[target : target + 3] = region[source : source + 3]
    path.write_bytes(data)


def badge_matches(path: pathlib.Path, version: str) -> bool:
    data = path.read_bytes()
    pixel_offset, _, height, stride, top_down = bmp_layout(data)
    expected = expected_badge(version)
    for local_y in range(BADGE_HEIGHT):
        image_y = BADGE_Y + local_y
        stored_y = image_y if top_down else height - 1 - image_y
        for local_x in range(BADGE_WIDTH):
            source = (local_y * BADGE_WIDTH + local_x) * 3
            target = pixel_offset + stored_y * stride + (BADGE_X + local_x) * 3
            if data[target : target + 3] != expected[source : source + 3]:
                return False
    return True


def set_scenario_title(path: pathlib.Path, version: str) -> None:
    data = path.read_bytes()
    expected = f"A Union Before Midnight: India 1933 [{version}]".encode("ascii")
    pattern = re.compile(
        rb'(?m)^(\{ name\s*=\s*")A Union Before Midnight: India 1933'
        rb'(?: \[[^"\r\n]+\])?("[^\r\n]*)$'
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + expected + match.group(2),
        data,
        count=1,
    )
    if count != 1:
        raise VisibleVersionError("could not locate the AUBM 1933 scenario title")
    if updated != data:
        path.write_bytes(updated)


def scenario_title_matches(path: pathlib.Path, version: str) -> bool:
    expected = f'{{ name       = "A Union Before Midnight: India 1933 [{version}]"'.encode(
        "ascii"
    )
    return expected in path.read_bytes()


def load_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_manifest_hash(path: pathlib.Path, asset: str, output: str, expected_hash: str) -> None:
    data = path.read_bytes()
    pattern = re.compile(
        rb"(?m)^("
        + re.escape(asset.encode("ascii"))
        + rb",[^,\r\n]+,[^,\r\n]+,"
        + re.escape(output.encode("ascii"))
        + rb",)[0-9a-fA-F]{64}(,)"
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + expected_hash.encode("ascii") + match.group(2),
        data,
        count=1,
    )
    if count != 1:
        raise VisibleVersionError("could not locate the loading-screen art-manifest row")
    if updated != data:
        path.write_bytes(updated)


def manifest_hash_matches(path: pathlib.Path, asset: str, output: str, expected_hash: str) -> bool:
    data = path.read_bytes()
    match = re.search(
        rb"(?m)^"
        + re.escape(asset.encode("ascii"))
        + rb",[^,\r\n]+,[^,\r\n]+,"
        + re.escape(output.encode("ascii"))
        + rb",([0-9a-fA-F]{64}),",
        data,
    )
    return bool(match and match.group(1).decode("ascii").lower() == expected_hash)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    version = read_version(root)
    loading = root / LOAD_SCREEN
    frontend = root / FRONTEND
    scenario = root / SCENARIO
    manifest = root / ART_MANIFEST

    try:
        if args.check:
            checks = {
                "loading-screen badge": badge_matches(loading, version),
                "main-menu badge": badge_matches(frontend, version),
                "main-menu artwork parity": frontend.read_bytes() == loading.read_bytes(),
                "scenario-list title": scenario_title_matches(scenario, version),
                "loading art-manifest hash": manifest_hash_matches(
                    manifest,
                    "aubm_loading_1933",
                    "gfx/load_1024.bmp",
                    load_hash(loading),
                ),
                "main-menu art-manifest hash": manifest_hash_matches(
                    manifest,
                    "aubm_frontend_1933",
                    "gfx/interface/frontend/bg_start.bmp",
                    load_hash(frontend),
                ),
            }
            failures = [name for name, passed in checks.items() if not passed]
            if failures:
                raise VisibleVersionError("visible version check failed: " + ", ".join(failures))
            print(f"Visible build identity: {version} ({len(checks)} checks passed)")
            return 0

        write_badge(loading, version)
        frontend.parent.mkdir(parents=True, exist_ok=True)
        frontend.write_bytes(loading.read_bytes())
        set_scenario_title(scenario, version)
        set_manifest_hash(
            manifest,
            "aubm_loading_1933",
            "gfx/load_1024.bmp",
            load_hash(loading),
        )
        set_manifest_hash(
            manifest,
            "aubm_frontend_1933",
            "gfx/interface/frontend/bg_start.bmp",
            load_hash(frontend),
        )
        print(f"Stamped visible AUBM build identity: {version}")
        return 0
    except (OSError, VisibleVersionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
