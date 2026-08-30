#!/usr/bin/env python3
"""Clean-room Darkest Hour lightmap compiler for A Union Before Midnight.

The tool reads the player's local Darkest Hour lightmaps, retains their raw
province lists, ownership and trailer, and applies amplitude-safe motifs to
every ordinary pixel belonging to one of the eight mechanical land terrains.
All added texture is generated from the original recipes in
``assets/v4_terrain/aubm_terrain_motifs.json``; donor-mod pixels are never read.

The codec follows the documented DH quadtree order (BR, BL, TR, TL), with all
bit streams read and written least-significant-bit first.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import mmap
import os
import shutil
import struct
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Sequence


TERRAINS = ("Plains", "Forest", "Mountain", "Desert", "Marsh", "Hills", "Jungle", "Urban")
SPECS = {
    1: (936, 360),
    2: (468, 180),
    3: (234, 90),
    4: (117, 45),
}
CHILD_OFFSETS = ((1, 1), (0, 1), (1, 0), (0, 0))  # BR, BL, TR, TL


class LightmapError(RuntimeError):
    pass


class BitReader:
    __slots__ = ("data", "bit")

    def __init__(self, data: bytes, byte_offset: int = 0) -> None:
        self.data = data
        self.bit = byte_offset * 8

    def read(self, width: int) -> int:
        if width < 0 or self.bit + width > len(self.data) * 8:
            raise LightmapError("bit stream ends early")
        value = 0
        for shift in range(width):
            value |= ((self.data[self.bit >> 3] >> (self.bit & 7)) & 1) << shift
            self.bit += 1
        return value

    def padding_to_byte(self) -> tuple[int, ...]:
        return tuple(self.read(1) for _ in range((-self.bit) & 7))

    @property
    def byte(self) -> int:
        if self.bit & 7:
            raise LightmapError("bit stream is not byte-aligned")
        return self.bit >> 3


class BitWriter:
    __slots__ = ("data", "bit")

    def __init__(self) -> None:
        self.data = bytearray()
        self.bit = 0

    def write(self, value: int, width: int) -> None:
        if value < 0 or (width and value >= (1 << width)):
            raise LightmapError(f"value {value} does not fit in {width} bits")
        for shift in range(width):
            if not (self.bit & 7):
                self.data.append(0)
            if (value >> shift) & 1:
                self.data[-1] |= 1 << (self.bit & 7)
            self.bit += 1

    def finish_byte(self, padding: Sequence[int] | None = None) -> None:
        needed = (-self.bit) & 7
        if padding is not None and len(padding) != needed:
            raise LightmapError("stored padding no longer matches stream alignment")
        for value in padding if padding is not None else (0,) * needed:
            self.write(int(value), 1)

    def bytes(self) -> bytes:
        if self.bit & 7:
            raise LightmapError("writer is not byte-aligned")
        return bytes(self.data)


@dataclass(slots=True)
class Node:
    x: int
    y: int
    size: int
    children: tuple["Node", "Node", "Node", "Node"] | None = None
    owner: int = 0
    color: int = 0

    @property
    def leaf(self) -> bool:
        return self.children is None


@dataclass(slots=True)
class ParsedBlock:
    province_words: tuple[int, ...]
    root: Node
    tree_padding: tuple[int, ...]
    owner_padding: tuple[int, ...]
    color_padding: tuple[int, ...]
    original_leaf_count: int


def iter_leaves(node: Node) -> Iterator[Node]:
    if node.children is None:
        yield node
        return
    for child in node.children:
        yield from iter_leaves(child)


def _parse_tree(reader: BitReader, x: int, y: int, size: int) -> Node:
    split = reader.read(1)
    if not split:
        return Node(x, y, size)
    if size <= 1:
        raise LightmapError("a 1x1 quadtree leaf was marked as split")
    half = size // 2
    children: list[Node] = []
    for dx, dy in CHILD_OFFSETS:
        cx, cy = x + dx * half, y + dy * half
        children.append(Node(cx, cy, 1) if size == 2 else _parse_tree(reader, cx, cy, half))
    return Node(x, y, size, tuple(children))  # type: ignore[arg-type]


def _ownership_width(province_count: int) -> int:
    if province_count == 1:
        return 0
    if province_count == 2:
        return 1
    if province_count <= 4:
        return 2
    if province_count <= 16:
        return 4
    if province_count <= 256:
        return 8
    raise LightmapError(f"block has {province_count} province entries; maximum supported is 256")


def parse_block(data: bytes) -> ParsedBlock:
    pos = 0
    words: list[int] = []
    while True:
        if pos + 2 > len(data):
            raise LightmapError("province list is unterminated")
        word = struct.unpack_from("<H", data, pos)[0]
        words.append(word)
        pos += 2
        if word & 0x8000:
            break
    reader = BitReader(data, pos)
    root = _parse_tree(reader, 0, 0, 32)
    leaves = list(iter_leaves(root))
    tree_padding = reader.padding_to_byte()
    width = _ownership_width(len(words))
    for leaf in leaves:
        leaf.owner = reader.read(width) if width else 0
        if leaf.owner >= len(words):
            raise LightmapError(f"leaf ownership index {leaf.owner} exceeds province list")
    owner_padding = reader.padding_to_byte()
    padded_count = ((len(leaves) + 3) // 4) * 4
    colors = [reader.read(6) for _ in range(padded_count)]
    for leaf, color in zip(leaves, colors):
        leaf.color = color
    color_padding = tuple(colors[len(leaves) :])
    if reader.byte != len(data):
        raise LightmapError(f"decoded {reader.byte} bytes but block contains {len(data)}")
    return ParsedBlock(tuple(words), root, tree_padding, owner_padding, color_padding, len(leaves))


def _write_tree(writer: BitWriter, node: Node) -> None:
    if node.children is None:
        writer.write(0, 1)
        return
    writer.write(1, 1)
    if node.size == 2:
        if any(child.children is not None or child.size != 1 for child in node.children):
            raise LightmapError("2x2 split must contain four implicit 1x1 leaves")
        return
    if node.size <= 1:
        raise LightmapError("invalid split node")
    for child in node.children:
        _write_tree(writer, child)


def encode_block(block: ParsedBlock, preserve_padding: bool = True) -> bytes:
    output = bytearray(struct.pack(f"<{len(block.province_words)}H", *block.province_words))
    leaves = list(iter_leaves(block.root))
    same_count = len(leaves) == block.original_leaf_count

    tree_writer = BitWriter()
    _write_tree(tree_writer, block.root)
    tree_writer.finish_byte(block.tree_padding if preserve_padding and same_count else None)
    output.extend(tree_writer.bytes())

    width = _ownership_width(len(block.province_words))
    owner_writer = BitWriter()
    for leaf in leaves:
        owner_writer.write(leaf.owner, width)
    owner_writer.finish_byte(block.owner_padding if preserve_padding and same_count else None)
    output.extend(owner_writer.bytes())

    color_writer = BitWriter()
    for leaf in leaves:
        color_writer.write(leaf.color, 6)
    padding_count = (-len(leaves)) & 3
    color_pad = block.color_padding if preserve_padding and same_count else (0,) * padding_count
    if len(color_pad) != padding_count:
        raise LightmapError("stored color padding no longer matches leaf count")
    for value in color_pad:
        color_writer.write(value, 6)
    color_writer.finish_byte()
    output.extend(color_writer.bytes())
    return bytes(output)


class LightmapFile:
    def __init__(self, path: Path, level: int) -> None:
        self.path = path
        self.level = level
        self.width, self.height = SPECS[level]
        self.blocks = self.width * self.height
        self.header_size = (self.blocks + 1) * 4
        self.handle: BinaryIO = path.open("rb")
        self.mapping = mmap.mmap(self.handle.fileno(), 0, access=mmap.ACCESS_READ)
        if len(self.mapping) < self.header_size:
            self.close()
            raise LightmapError(f"{path} is smaller than its required header")
        self.offsets = struct.unpack_from(f"<{self.blocks + 1}I", self.mapping, 0)
        if self.offsets[0] != 0 or any(a > b for a, b in zip(self.offsets, self.offsets[1:])):
            self.close()
            raise LightmapError(f"{path} has a non-monotonic offset table")
        self.data_end = self.header_size + self.offsets[-1]
        if self.data_end > len(self.mapping):
            self.close()
            raise LightmapError(f"{path} offset table extends beyond end of file")

    def block(self, index: int) -> bytes:
        start = self.header_size + self.offsets[index]
        end = self.header_size + self.offsets[index + 1]
        return bytes(self.mapping[start:end])

    @property
    def trailer(self) -> bytes:
        return bytes(self.mapping[self.data_end :])

    def close(self) -> None:
        mapping = getattr(self, "mapping", None)
        if mapping is not None:
            mapping.close()
            self.mapping = None  # type: ignore[assignment]
        handle = getattr(self, "handle", None)
        if handle is not None:
            handle.close()
            self.handle = None  # type: ignore[assignment]

    def __enter__(self) -> "LightmapFile":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_provinces(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    with path.open("r", encoding="cp1252", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            try:
                province_id = int(row.get("Id", ""))
            except ValueError:
                continue
            result[province_id] = (row.get("Terrain") or "").strip()
    missing = [terrain for terrain in TERRAINS if terrain not in result.values()]
    if missing:
        raise LightmapError(f"Province.csv is missing mechanical terrain classes: {', '.join(missing)}")
    return result


def load_motifs(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != 3:
        raise LightmapError("motif schema_version must be 3")
    if data.get("cell_pixels") != 2:
        raise LightmapError("cell_pixels must be 2 for the screen-readable refiner")
    motifs = data.get("motifs", {})
    if set(motifs) != set(TERRAINS):
        raise LightmapError("motif file must define exactly all eight mechanical land classes")
    if "terrain_color_anchors" in data:
        raise LightmapError("schema 3 must not restrict ordinary land to fixed colour anchors")
    reference = data.get("world_coordinate_reference", {})
    expected_scale = {str(level): 1 << (level - 1) for level in range(1, 5)}
    if reference.get("level_1_pixels_per_level_pixel") != expected_scale:
        raise LightmapError("world-coordinate level scaling must explicitly be 1, 2, 4, 8")
    terrain_colours = data.get("native_terrain_colour_by_terrain", {})
    if set(terrain_colours) != set(TERRAINS) or any(
        not isinstance(value, str) or not value.strip() for value in terrain_colours.values()
    ):
        raise LightmapError("native_terrain_colour_by_terrain must name a scale for all eight terrains")
    weather_colours = data.get("native_weather_colour_by_state", {})
    if set(weather_colours) != {"Snow", "Mud"} or any(
        not isinstance(value, str) or not value.strip() for value in weather_colours.values()
    ):
        raise LightmapError("native_weather_colour_by_state must name Snow and Mud scales")
    zoom = data.get("zoom_strength", {})
    if set(zoom) != {"1", "2", "3", "4"} or any(float(value) <= 0 for value in zoom.values()):
        raise LightmapError("zoom_strength must contain positive entries 1 through 4")
    if any(float(value) != 1.0 for value in zoom.values()):
        raise LightmapError("schema 3 forbids distant-zoom contrast attenuation")
    gates = data.get("gates", {})
    required_gates = {
        "maximum_absolute_mean",
        "maximum_block_grid_ratio",
        "minimum_modified_coverage_percent_all_land",
        "maximum_absolute_pair_correlation",
        "maximum_hills_to_mountain_rms_ratio",
        "native_country_colour",
        "minimum_native_marked_median_delta_e00",
        "minimum_native_delta_e00_ge_2_percent_all_land",
        "minimum_per_terrain_marked_median_delta_e00",
        "minimum_per_terrain_delta_e00_ge_2_fraction_of_modified",
        "minimum_terrain_mode_per_terrain_marked_median_delta_e00",
        "minimum_terrain_mode_per_terrain_delta_e00_ge_2_fraction_of_modified",
        "minimum_weather_mode_per_terrain_marked_median_delta_e00",
        "minimum_weather_mode_per_terrain_delta_e00_ge_1_fraction_of_modified",
    }
    if not required_gates.issubset(gates):
        raise LightmapError("motif gates are missing the schema-3 all-land/native contract")
    if not isinstance(gates["native_country_colour"], str) or not gates["native_country_colour"].strip():
        raise LightmapError("native_country_colour must name a real supplied colorscale")
    for terrain, recipe in motifs.items():
        if recipe.get("kind") not in {
            "hash_marks",
            "forest_clumps",
            "segmented_ridges",
            "segmented_arcs",
            "dash_reeds",
            "broken_contours",
            "jungle_clumps",
            "urban_fragments",
        }:
            raise LightmapError(f"{terrain} has an unknown motif kind")
        if not 0 < float(recipe.get("amplitude", 0)) <= 10:
            raise LightmapError(f"{terrain} amplitude must be in (0, 10]")
        if not isinstance(recipe.get("seed"), int):
            raise LightmapError(f"{terrain} seed must be an integer")
        coverage = recipe.get("coverage_percent_by_zoom", {})
        if set(coverage) != {"1", "2", "3", "4"}:
            raise LightmapError(f"{terrain} must define coverage ranges for all four zooms")
        for level, bounds in coverage.items():
            if not isinstance(bounds, list) or len(bounds) != 2 or not 0 <= float(bounds[0]) <= float(bounds[1]) <= 100:
                raise LightmapError(f"{terrain} zoom {level} has an invalid coverage range")
        if not isinstance(recipe.get("maximum_straight_run"), int) or recipe["maximum_straight_run"] < 1:
            raise LightmapError(f"{terrain} maximum_straight_run must be a positive integer")
        if "retention_percent" in recipe:
            if recipe["kind"] != "broken_contours":
                raise LightmapError(f"{terrain} retention_percent is only valid for broken_contours")
            if not isinstance(recipe["retention_percent"], int) or not 0 <= recipe["retention_percent"] <= 100:
                raise LightmapError(f"{terrain} retention_percent must be an integer in [0, 100]")
        if "negative_sign_flip_percent" in recipe:
            if recipe["kind"] != "broken_contours":
                raise LightmapError(f"{terrain} negative_sign_flip_percent is only valid for broken_contours")
            if not isinstance(recipe["negative_sign_flip_percent"], int) or not 0 <= recipe["negative_sign_flip_percent"] <= 100:
                raise LightmapError(f"{terrain} negative_sign_flip_percent must be an integer in [0, 100]")
    return data


def load_colorscales(path: Path) -> dict[str, tuple[tuple[int, int, int], ...]]:
    """Read Darkest Hour's native 64-step named colour scales.

    The file is supplied by the player's game.  AUBM does not author or install
    a replacement palette; this parser is used only for honest offline renders
    and perceptual acceptance measurements.
    """
    lines = [line.strip() for line in path.read_text(encoding="cp1252").splitlines() if line.strip()]
    anchors: dict[str, list[tuple[int, tuple[int, int, int]]]] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.lower().startswith("red;green;blue;index"):
            index += 1
            continue
        if line.endswith(";;;"):
            name = line[:-3].strip()
            index += 1
            if index < len(lines) and lines[index].lower().startswith("red;green;blue;index"):
                index += 1
            rows: list[tuple[int, tuple[int, int, int]]] = []
            while index < len(lines) and not lines[index].endswith(";;;"):
                fields = lines[index].split(";")
                if len(fields) >= 4:
                    try:
                        rgb = tuple(int(fields[channel]) for channel in range(3))
                        position = int(fields[3])
                    except ValueError as exc:
                        raise LightmapError(f"invalid colorscale row in {path}: {lines[index]}") from exc
                    if any(not 0 <= channel <= 255 for channel in rgb) or not 0 <= position <= 64:
                        raise LightmapError(f"out-of-range colorscale row in {path}: {lines[index]}")
                    rows.append((position, rgb))  # type: ignore[arg-type]
                index += 1
            if len(rows) < 2:
                raise LightmapError(f"colorscale {name!r} has fewer than two anchors")
            anchors[name.casefold()] = sorted(rows)
            continue
        index += 1
    if not anchors:
        raise LightmapError(f"no named colour scales found in {path}")
    result: dict[str, tuple[tuple[int, int, int], ...]] = {}
    for name, rows in anchors.items():
        lut: list[tuple[int, int, int]] = []
        for shade in range(64):
            left, right = rows[0], rows[-1]
            for first, second in zip(rows, rows[1:]):
                if first[0] <= shade <= second[0]:
                    left, right = first, second
                    break
            span = max(1, right[0] - left[0])
            fraction = (shade - left[0]) / span
            # MapUtility/Darkest Hour use truncating integer interpolation.
            # Rounding produces a subtly brighter synthetic LUT and is not an
            # honest native acceptance fixture.
            lut.append(
                tuple(int(left[1][channel] + fraction * (right[1][channel] - left[1][channel])) for channel in range(3))
            )
        result[name] = tuple(lut)
    return result


def named_colorscale(
    scales: dict[str, tuple[tuple[int, int, int], ...]],
    name: str,
) -> tuple[tuple[int, int, int], ...]:
    key = name.casefold()
    if key not in scales:
        normalized = "".join(character for character in key if character.isalnum()).replace("gray", "grey")
        matches = [
            candidate
            for candidate in scales
            if "".join(character for character in candidate if character.isalnum()).replace("gray", "grey") == normalized
        ]
        if len(matches) == 1:
            key = matches[0]
    try:
        return scales[key]
    except KeyError as exc:
        available = ", ".join(sorted(scales))
        raise LightmapError(f"colorscale {name!r} is absent; available names: {available}") from exc


def load_terrain_colour_reference(path: Path) -> dict[str, str]:
    """Read the authoritative terrain→scale mapping bundled with Darkest Hour."""
    terrain_by_label = {
        "clear": "Plains",
        "urban": "Urban",
        "forest": "Forest",
        "jungle": "Jungle",
        "desert": "Desert",
        "marsh": "Marsh",
        "hills": "Hills",
        "mountain": "Mountain",
        "mountains": "Mountain",
    }
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="cp1252").splitlines():
        line = raw.strip()
        if not line or ">" in line:
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        scale, label = fields[0], fields[1].casefold()
        terrain = terrain_by_label.get(label)
        if terrain:
            result[terrain] = scale
    if set(result) != set(TERRAINS):
        missing = ", ".join(sorted(set(TERRAINS) - set(result)))
        raise LightmapError(f"terrain colour reference {path} is missing: {missing}")
    return result


def load_weather_colour_reference(path: Path) -> dict[str, str]:
    """Read the native Snow/Mud scale substitutions from Map colors.txt."""
    labels = {"snow": "Snow", "mud": "Mud"}
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="cp1252").splitlines():
        line = raw.strip()
        if not line or ">" in line:
            continue
        fields = line.split()
        if len(fields) >= 2 and fields[1].casefold() in labels:
            result[labels[fields[1].casefold()]] = fields[0]
    if set(result) != {"Snow", "Mud"}:
        raise LightmapError(f"weather colour reference {path} must define Snow and Mud")
    return result


def _srgb_channel_to_linear(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    red, green, blue = (_srgb_channel_to_linear(value) for value in rgb)
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = (0.2126729 * red + 0.7151522 * green + 0.0721750 * blue)
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883
    epsilon = 216 / 24389
    kappa = 24389 / 27

    def transform(value: float) -> float:
        return value ** (1 / 3) if value > epsilon else (kappa * value + 16) / 116

    fx, fy, fz = transform(x), transform(y), transform(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e76(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def delta_e00(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    """CIEDE2000 colour difference with unit lightness/chroma/hue weights."""
    l1, a1, b1 = left
    l2, a2, b2 = right
    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2.0
    c7 = c_bar**7
    g = 0.5 * (1.0 - math.sqrt(c7 / (c7 + 25.0**7)))
    a1p, a2p = (1.0 + g) * a1, (1.0 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def hue(a: float, b: float) -> float:
        if a == 0.0 and b == 0.0:
            return 0.0
        return math.degrees(math.atan2(b, a)) % 360.0

    h1p, h2p = hue(a1p, b1), hue(a2p, b2)
    delta_lp = l2 - l1
    delta_cp = c2p - c1p
    if c1p * c2p == 0.0:
        delta_hp = 0.0
    else:
        difference = h2p - h1p
        if difference > 180.0:
            difference -= 360.0
        elif difference < -180.0:
            difference += 360.0
        delta_hp = 2.0 * math.sqrt(c1p * c2p) * math.sin(math.radians(difference / 2.0))
    l_bar = (l1 + l2) / 2.0
    cp_bar = (c1p + c2p) / 2.0
    if c1p * c2p == 0.0:
        hp_bar = h1p + h2p
    elif abs(h1p - h2p) <= 180.0:
        hp_bar = (h1p + h2p) / 2.0
    elif h1p + h2p < 360.0:
        hp_bar = (h1p + h2p + 360.0) / 2.0
    else:
        hp_bar = (h1p + h2p - 360.0) / 2.0
    t = (
        1.0
        - 0.17 * math.cos(math.radians(hp_bar - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * hp_bar))
        + 0.32 * math.cos(math.radians(3.0 * hp_bar + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * hp_bar - 63.0))
    )
    delta_theta = 30.0 * math.exp(-((hp_bar - 275.0) / 25.0) ** 2)
    cp7 = cp_bar**7
    rc = 2.0 * math.sqrt(cp7 / (cp7 + 25.0**7))
    sl = 1.0 + 0.015 * (l_bar - 50.0) ** 2 / math.sqrt(20.0 + (l_bar - 50.0) ** 2)
    sc = 1.0 + 0.045 * cp_bar
    sh = 1.0 + 0.015 * cp_bar * t
    rt = -math.sin(math.radians(2.0 * delta_theta)) * rc
    lightness = delta_lp / sl
    chroma = delta_cp / sc
    hue_term = delta_hp / sh
    return math.sqrt(lightness**2 + chroma**2 + hue_term**2 + rt * chroma * hue_term)


def _hash32(x: int, y: int, seed: int) -> int:
    """Stable coordinate hash; used for placement and globally balanced signs."""
    value = (x * 0x1F123BB5) ^ (y * 0x5F356495) ^ (seed * 0x9E3779B1)
    value &= 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= value >> 15
    value = (value * 0x846CA68B) & 0xFFFFFFFF
    return (value ^ (value >> 16)) & 0xFFFFFFFF


def _orientation(x: int, y: int, size: int, code: int) -> tuple[int, int]:
    """Rotate/reflect a tile so neighboring feature tiles do not form a grid."""
    if code & 4:
        x = size - 1 - x
    for _ in range(code & 3):
        x, y = size - 1 - y, x
    return x, y


def _feature_sign(x: int, y: int, seed: int) -> int:
    return 1 if _hash32(x, y, seed) & 1 else -1


def motif_unit(recipe: dict, x: int, y: int) -> int:
    """Return a sparse semantic mark in {-1, 0, +1}; never a wave or full grid."""
    kind = recipe["kind"]
    seed = int(recipe["seed"])
    if kind == "hash_marks":
        mark = _hash32(x, y, seed) % 100 < 30
        return _feature_sign(x, y, seed + 1009) if mark else 0

    if kind == "forest_clumps":
        size = 5
        tx, ty, lx, ly = x // size, y // size, x % size, y % size
        tile_hash = _hash32(tx, ty, seed)
        lx, ly = _orientation(lx, ly, size, tile_hash & 7)
        first = {(0, 2), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3)}
        second = {(2, 4), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4)}
        sign = 1 if tile_hash & 0x100 else -1
        keep = _hash32(x, y, seed + 17) % 100 < 92
        if keep and (lx, ly) in first:
            return sign
        if keep and (lx, ly) in second:
            return -sign
        return 0

    if kind == "segmented_ridges":
        across = (x - y + seed) % 7
        along = (x + y + seed) % 10
        if along < 8 and across in (0, 1):
            return 1 if across == 0 else -1
        if across == 4 and along in (1, 4):
            return _feature_sign(x // 3, y // 3, seed + 31)
        return 0

    if kind == "segmented_arcs":
        size = 12
        tx, ty, lx, ly = x // size, y // size, x % size, y % size
        tile_hash = _hash32(tx, ty, seed)
        lx, ly = _orientation(lx, ly, size, tile_hash & 7)
        dx, dy = 2 * lx - 11, 2 * ly - 11
        distance = dx * dx + dy * dy
        ring = 62 <= distance <= 112
        sector_gap = (abs(dx) <= 3 and dy < 0) or (abs(dy) <= 3 and dx > 0)
        broken = _hash32(x, y, seed + 43) % 100 < 90
        return (1 if tile_hash & 0x200 else -1) if ring and not sector_gap and broken else 0

    if kind == "dash_reeds":
        width, height = 7, 6
        tx, ty, lx, ly = x // width, y // height, x % width, y % height
        tile_hash = _hash32(tx, ty, seed)
        first_y = 1 + (tile_hash & 1)
        first_x = 1 + (tile_hash >> 2) % 3
        second_y = (first_y + 3) % height
        second_x = 1 + (tile_hash >> 5) % 3
        reed_x = (tile_hash >> 9) % width
        reed_y = (tile_hash >> 12) % 5
        tile_sign = 1 if tile_hash & 0x20000 else -1
        if ly == first_y and first_x <= lx < first_x + 3:
            return tile_sign
        if ly == second_y and second_x <= lx < second_x + 3:
            return -tile_sign
        if lx == reed_x and reed_y <= ly < reed_y + 2:
            return _feature_sign(tx, ty, seed + 59)
        return 0

    if kind == "broken_contours":
        size = 14
        tx, ty, lx, ly = x // size, y // size, x % size, y % size
        tile_hash = _hash32(tx, ty, seed)
        lx, ly = _orientation(lx, ly, size, tile_hash & 7)
        dx, dy = 2 * lx - 13, 2 * ly - 13
        distance = dx * dx + dy * dy
        inner = 48 <= distance <= 82
        outer = 130 <= distance <= 178
        sector_gap = (abs(dx) <= 3 and dy > 0) or (abs(dy) <= 3 and dx < 0)
        broken = _hash32(x, y, seed + 71) % 100 < int(recipe.get("retention_percent", 80))
        tile_sign = 1 if tile_hash & 0x400 else -1
        value = 0
        if broken and not sector_gap and inner:
            value = tile_sign
        elif broken and not sector_gap and outer:
            value = -tile_sign
        if value < 0 and _hash32(x, y, seed + 1709) % 100 < int(recipe.get("negative_sign_flip_percent", 0)):
            value = 1
        if value:
            return value
        return 0

    if kind == "jungle_clumps":
        size = 5
        tx, ty, lx, ly = x // size, y // size, x % size, y % size
        tile_hash = _hash32(tx, ty, seed)
        lx, ly = _orientation(lx, ly, size, tile_hash & 7)
        holes = {(0, 0), (0, 4), (1, 3), (2, 1), (3, 0), (3, 4), (4, 2), (4, 3)}
        if (lx, ly) in holes:
            return 0
        return _feature_sign(x // 2, y // 2, seed + 83)

    if kind == "urban_fragments":
        size = 5
        tx, ty, lx, ly = x // size, y // size, x % size, y % size
        tile_hash = _hash32(tx, ty, seed)
        lx, ly = _orientation(lx, ly, size, tile_hash & 7)
        first_block = lx <= 1 and ly <= 1
        second_block = lx >= 3 and ly >= 3
        short_road = (ly == 2 and lx <= 2) or (lx == 2 and ly >= 3)
        corner_fragments = (lx, ly) in {(4, 0), (0, 4)}
        if (x + 2 * y + seed) % 7 == 0:
            return 0
        tile_sign = 1 if tile_hash & 0x800 else -1
        if first_block:
            return tile_sign
        if second_block:
            return -tile_sign
        if short_road:
            return _feature_sign(tx, ty, seed + 101)
        if corner_fragments:
            return _feature_sign(tx, ty, seed + 131)
        return 0
    raise LightmapError(f"unknown motif kind {kind}")


def motif_offsets(recipe: dict, level: int, strength: float, points: Sequence[tuple[int, int]]) -> list[int]:
    """Return signed six-bit-index offsets for world-anchored motif-cell coordinates."""
    magnitude = max(1, int(math.floor(float(recipe["amplitude"]) * strength + 0.5)))
    return [motif_unit(recipe, x, y) * magnitude for x, y in points]


def motif_points_from_level_pixels(
    level: int,
    points: Sequence[tuple[int, int]],
    cell_pixels: int,
) -> list[tuple[int, int]]:
    """Map screen pixels through explicit level-1 world coordinates.

    A lightmap-N pixel represents ``2 ** (N - 1)`` level-1 world pixels.  The
    motif cell grows by that same world factor, so its origin is geographically
    phase-locked while the semantic marks remain two pixels wide on screen.
    Writing the cancellation explicitly avoids the former accidental use of
    unrelated per-file coordinates.
    """
    world_per_pixel = 1 << (level - 1)
    world_per_cell = cell_pixels * world_per_pixel
    return [
        ((x * world_per_pixel) // world_per_cell, (y * world_per_pixel) // world_per_cell)
        for x, y in points
    ]


def safe_color_offset(color: int, requested: int) -> tuple[int, int]:
    """Apply one motif offset without ever leaving Darkest Hour's 0..63 range."""
    applied = max(-color, min(63 - color, requested))
    return color + applied, applied


def _longest_straight_run(mask: Sequence[bool], size: int) -> int:
    longest = 0
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        for y in range(size):
            for x in range(size):
                if not mask[y * size + x]:
                    continue
                px, py = x - dx, y - dy
                if 0 <= px < size and 0 <= py < size and mask[py * size + px]:
                    continue
                length, cx, cy = 0, x, y
                while 0 <= cx < size and 0 <= cy < size and mask[cy * size + cx]:
                    length += 1
                    cx += dx
                    cy += dy
                longest = max(longest, length)
    return longest


def motif_metrics(data: dict) -> dict:
    gates = data["gates"]
    max_mean = float(gates["maximum_absolute_mean"])
    max_grid = float(gates["maximum_block_grid_ratio"])
    max_corr = float(gates.get("maximum_absolute_pair_correlation", 1.0))
    fields: dict[str, list[float]] = {}
    rms_by_terrain: dict[str, dict[str, float]] = {}
    report: dict[str, dict] = {}
    sample = 168  # divisible by motif tile sizes, but not DH's 16-cell block width
    block_cells = 16
    for terrain in TERRAINS:
        recipe = data["motifs"][terrain]
        zoom_report: dict[str, dict] = {}
        rms_by_terrain[terrain] = {}
        for level in range(1, 5):
            strength = float(data["zoom_strength"][str(level)])
            points = [(x, y) for y in range(sample) for x in range(sample)]
            field = [float(value) for value in motif_offsets(recipe, level, strength, points)]
            if level == 1:
                fields[terrain] = field
            mean = sum(field) / len(field)
            coverage = 100.0 * sum(value != 0 for value in field) / len(field)
            rms = math.sqrt(sum(value * value for value in field) / len(field))
            rms_by_terrain[terrain][str(level)] = rms
            internal: list[float] = []
            seams: list[float] = []
            for y in range(sample):
                for x in range(sample):
                    here = field[y * sample + x]
                    if x + 1 < sample:
                        target = seams if (x + 1) % block_cells == 0 else internal
                        target.append(abs(here - field[y * sample + x + 1]))
                    if y + 1 < sample:
                        target = seams if (y + 1) % block_cells == 0 else internal
                        target.append(abs(here - field[(y + 1) * sample + x]))
            grid_ratio = (sum(seams) / len(seams)) / max(sum(internal) / len(internal), 1e-9)
            longest = _longest_straight_run([value != 0 for value in field], sample)
            low, high = (float(value) for value in recipe["coverage_percent_by_zoom"][str(level)])
            if abs(mean) > max_mean:
                raise LightmapError(f"{terrain} zoom {level} absolute mean {abs(mean):.3f} exceeds {max_mean}")
            if not low <= coverage <= high:
                raise LightmapError(f"{terrain} zoom {level} coverage {coverage:.3f}% is outside [{low}, {high}]")
            if grid_ratio > max_grid:
                raise LightmapError(f"{terrain} zoom {level} block-grid ratio {grid_ratio:.3f} exceeds {max_grid}")
            if longest > int(recipe["maximum_straight_run"]):
                raise LightmapError(
                    f"{terrain} zoom {level} straight run {longest} exceeds {recipe['maximum_straight_run']}"
                )
            zoom_report[str(level)] = {
                "mean": round(mean, 6),
                "coverage_percent": round(coverage, 3),
                "target_coverage_percent": [low, high],
                "rms": round(rms, 6),
                "block_grid_ratio": round(grid_ratio, 6),
                "longest_straight_run": longest,
            }
        report[terrain] = {"zooms": zoom_report, "maximum_straight_run": recipe["maximum_straight_run"]}
    hills_limit = float(gates["maximum_hills_to_mountain_rms_ratio"])
    hills_ratios: dict[str, float] = {}
    for level in range(1, 5):
        ratio = rms_by_terrain["Hills"][str(level)] / rms_by_terrain["Mountain"][str(level)]
        hills_ratios[str(level)] = round(ratio, 6)
        if ratio > hills_limit:
            raise LightmapError(f"Hills/Mountain RMS ratio {ratio:.3f} at zoom {level} exceeds {hills_limit}")
    correlations: dict[str, float] = {}
    for i, left in enumerate(TERRAINS):
        a = fields[left]
        am = sum(a) / len(a)
        av = sum((value - am) ** 2 for value in a)
        for right in TERRAINS[i + 1 :]:
            b = fields[right]
            bm = sum(b) / len(b)
            bv = sum((value - bm) ** 2 for value in b)
            corr = sum((x - am) * (y - bm) for x, y in zip(a, b)) / math.sqrt(av * bv)
            correlations[f"{left}/{right}"] = round(corr, 6)
            if abs(corr) > max_corr:
                raise LightmapError(f"{left} and {right} correlation {corr:.3f} exceeds {max_corr}")
    return {
        "terrains": report,
        "hills_to_mountain_rms_ratio_by_zoom": hills_ratios,
        "pair_correlations": correlations,
        "gates": gates,
    }


def _word_province_id(word: int) -> int | None:
    value = word & 0x7FFF
    if value & 0x4000:
        return None
    province_id = value & 0x3FFF
    return province_id if province_id > 0 else None


def _full_refined_tree(x: int, y: int, size: int, owner: int, colors: dict[tuple[int, int], int]) -> Node:
    if size == 2:
        return Node(x, y, size, owner=owner, color=colors[(x, y)])
    half = size // 2
    children = tuple(
        _full_refined_tree(x + dx * half, y + dy * half, half, owner, colors) for dx, dy in CHILD_OFFSETS
    )
    return Node(x, y, size, children)  # type: ignore[arg-type]


@dataclass
class ChangeStats:
    ordinary_land_pixels: dict[str, int] = field(default_factory=lambda: {terrain: 0 for terrain in TERRAINS})
    modified_pixels: dict[str, int] = field(default_factory=lambda: {terrain: 0 for terrain in TERRAINS})
    color_pairs: dict[str, Counter[tuple[int, int]]] = field(
        default_factory=lambda: {terrain: Counter() for terrain in TERRAINS}
    )
    source_leaves: int = 0
    output_leaves: int = 0


def _weighted_percentile(weighted: Counter[float], percentile: float) -> float:
    total = sum(weighted.values())
    if total <= 0:
        return 0.0
    threshold = percentile * total
    cumulative = 0
    for value, count in sorted(weighted.items()):
        cumulative += count
        if cumulative >= threshold:
            return value
    return max(weighted)


def native_perceptual_metrics(
    color_pairs: dict[str, Counter[tuple[int, int]]],
    luts: Sequence[tuple[int, int, int]] | dict[str, Sequence[tuple[int, int, int]]],
) -> dict:
    """Measure real named-colorscale contrast over every ordinary land pixel."""
    distance76: dict[str, list[list[float]]] = {}
    distance00: dict[str, list[list[float]]] = {}
    for terrain in TERRAINS:
        lut = luts[terrain] if isinstance(luts, dict) else luts
        labs = [rgb_to_lab(rgb) for rgb in lut]
        distance76[terrain] = [[delta_e76(labs[old], labs[new]) for new in range(64)] for old in range(64)]
        distance00[terrain] = [[delta_e00(labs[old], labs[new]) for new in range(64)] for old in range(64)]
    all_pixels = changed_pixels = ge1_pixels = ge2_pixels = 0
    marked76: Counter[float] = Counter()
    marked00: Counter[float] = Counter()
    by_terrain: dict[str, dict] = {}
    for terrain in TERRAINS:
        pairs = color_pairs[terrain]
        terrain_all = sum(pairs.values())
        terrain_changed = sum(count for (old, new), count in pairs.items() if old != new)
        terrain_ge1 = sum(count for (old, new), count in pairs.items() if distance00[terrain][old][new] >= 1.0)
        terrain_ge2 = sum(count for (old, new), count in pairs.items() if distance00[terrain][old][new] >= 2.0)
        terrain_marked76: Counter[float] = Counter()
        terrain_marked00: Counter[float] = Counter()
        for (old, new), count in pairs.items():
            if old != new:
                terrain_marked76[distance76[terrain][old][new]] += count
                terrain_marked00[distance00[terrain][old][new]] += count
                marked76[distance76[terrain][old][new]] += count
                marked00[distance00[terrain][old][new]] += count
        all_pixels += terrain_all
        changed_pixels += terrain_changed
        ge1_pixels += terrain_ge1
        ge2_pixels += terrain_ge2
        by_terrain[terrain] = {
            "ordinary_land_pixels": terrain_all,
            "modified_pixels": terrain_changed,
            "modified_coverage_percent_all_land": round(100.0 * terrain_changed / terrain_all, 3) if terrain_all else None,
            "marked_median_delta_e76": round(_weighted_percentile(terrain_marked76, 0.5), 4),
            "marked_p95_delta_e76": round(_weighted_percentile(terrain_marked76, 0.95), 4),
            "marked_median_delta_e00": round(_weighted_percentile(terrain_marked00, 0.5), 4),
            "marked_p95_delta_e00": round(_weighted_percentile(terrain_marked00, 0.95), 4),
            "delta_e00_ge_1_percent_all_land": round(100.0 * terrain_ge1 / terrain_all, 3) if terrain_all else None,
            "delta_e00_ge_1_fraction_of_modified": round(terrain_ge1 / terrain_changed, 4) if terrain_changed else None,
            "delta_e00_ge_2_percent_all_land": round(100.0 * terrain_ge2 / terrain_all, 3) if terrain_all else None,
            "delta_e00_ge_2_fraction_of_modified": round(terrain_ge2 / terrain_changed, 4) if terrain_changed else None,
        }
    return {
        "ordinary_land_pixels": all_pixels,
        "modified_pixels": changed_pixels,
        "modified_coverage_percent_all_land": round(100.0 * changed_pixels / all_pixels, 3) if all_pixels else None,
        "marked_median_delta_e76": round(_weighted_percentile(marked76, 0.5), 4),
        "marked_p95_delta_e76": round(_weighted_percentile(marked76, 0.95), 4),
        "marked_median_delta_e00": round(_weighted_percentile(marked00, 0.5), 4),
        "marked_p95_delta_e00": round(_weighted_percentile(marked00, 0.95), 4),
        "delta_e00_ge_1_percent_all_land": round(100.0 * ge1_pixels / all_pixels, 3) if all_pixels else None,
        "delta_e00_ge_2_percent_all_land": round(100.0 * ge2_pixels / all_pixels, 3) if all_pixels else None,
        "by_terrain": by_terrain,
    }


def _per_mode_failures(
    mode: str,
    metrics: dict,
    median_minimum: float,
    threshold: int,
    fraction_minimum: float,
) -> list[str]:
    failures: list[str] = []
    for terrain in TERRAINS:
        values = metrics["by_terrain"][terrain]
        if not values["ordinary_land_pixels"]:
            continue
        median = float(values["marked_median_delta_e00"])
        fraction = float(values[f"delta_e00_ge_{threshold}_fraction_of_modified"] or 0.0)
        if median < median_minimum or fraction < fraction_minimum:
            failures.append(
                f"{mode}/{terrain}=median DE00 {median:.4f}, DE00>={threshold}/modified {fraction:.3f} "
                f"(minimum {median_minimum:g}, {fraction_minimum:g})"
            )
    return failures


def enforce_compiled_gates(
    level: int,
    political: dict,
    terrain_mode: dict,
    snow: dict,
    mud: dict,
    motifs: dict,
) -> None:
    """Apply all-land density and real-colorscale perceptual release gates."""
    minimum = float(motifs["gates"]["minimum_modified_coverage_percent_all_land"])
    failures: list[str] = []
    for terrain in TERRAINS:
        value = political["by_terrain"][terrain]["modified_coverage_percent_all_land"]
        if value is None:
            continue
        low, high = (float(bound) for bound in motifs["motifs"][terrain]["coverage_percent_by_zoom"][str(level)])
        if float(value) < max(minimum, low) or float(value) > high:
            failures.append(f"{terrain}={float(value):.3f}% (target {max(minimum, low):g}..{high:g}%)")
    if failures:
        raise LightmapError(f"lightmap{level} all-land motif coverage gate failed: " + "; ".join(failures))
    native_median_minimum = float(motifs["gates"]["minimum_native_marked_median_delta_e00"])
    native_ge2_minimum = float(motifs["gates"]["minimum_native_delta_e00_ge_2_percent_all_land"])
    if float(political["marked_median_delta_e00"]) < native_median_minimum:
        raise LightmapError(
            f"lightmap{level} political marked median DE00 {political['marked_median_delta_e00']} "
            f"is below {native_median_minimum}"
        )
    if float(political["delta_e00_ge_2_percent_all_land"]) < native_ge2_minimum:
        raise LightmapError(
            f"lightmap{level} political DE00>=2 coverage {political['delta_e00_ge_2_percent_all_land']}% "
            f"is below {native_ge2_minimum}% of all ordinary land"
        )
    political_failures = _per_mode_failures(
        "political",
        political,
        float(motifs["gates"]["minimum_per_terrain_marked_median_delta_e00"]),
        2,
        float(motifs["gates"]["minimum_per_terrain_delta_e00_ge_2_fraction_of_modified"]),
    )
    terrain_failures = _per_mode_failures(
        "terrain",
        terrain_mode,
        float(motifs["gates"]["minimum_terrain_mode_per_terrain_marked_median_delta_e00"]),
        2,
        float(motifs["gates"]["minimum_terrain_mode_per_terrain_delta_e00_ge_2_fraction_of_modified"]),
    )
    weather_median = float(motifs["gates"]["minimum_weather_mode_per_terrain_marked_median_delta_e00"])
    weather_fraction = float(
        motifs["gates"]["minimum_weather_mode_per_terrain_delta_e00_ge_1_fraction_of_modified"]
    )
    weather_failures = _per_mode_failures("snow", snow, weather_median, 1, weather_fraction)
    weather_failures += _per_mode_failures("mud", mud, weather_median, 1, weather_fraction)
    perceptual_failures = political_failures + terrain_failures + weather_failures
    if perceptual_failures:
        raise LightmapError(f"lightmap{level} per-mode/per-terrain native contrast gate failed: " + "; ".join(perceptual_failures))


def transform_block(
    block: ParsedBlock,
    level: int,
    origin_x: int,
    origin_y: int,
    provinces: dict[int, str],
    motifs: dict,
    stats: ChangeStats,
    zero_motif: bool = False,
) -> None:
    strength = float(motifs["zoom_strength"][str(level)])
    cell_pixels = int(motifs["cell_pixels"])

    def record(terrain: str, old: int, new: int, area: int) -> None:
        stats.ordinary_land_pixels[terrain] += area
        stats.color_pairs[terrain][(old, new)] += area
        if old != new:
            stats.modified_pixels[terrain] += area

    def transform(node: Node) -> Node:
        if node.children is not None:
            node.children = tuple(transform(child) for child in node.children)  # type: ignore[assignment]
            return node
        stats.source_leaves += 1
        province_id = _word_province_id(block.province_words[node.owner])
        terrain = provinces.get(province_id, "") if province_id is not None else ""
        if terrain not in TERRAINS:
            stats.output_leaves += 1
            return node
        area = node.size * node.size
        if node.size <= 2:
            # Distant zooms already contain many 1x1/2x2 source leaves.  They
            # cannot be refined further, but they still need the same 2-pixel
            # semantic motif cell or the entire L3/L4 layer becomes a no-op.
            # Changing the stored colour here preserves the source tree,
            # province owner and every non-colour field exactly.
            point = motif_points_from_level_pixels(
                level,
                [(origin_x + node.x, origin_y + node.y)],
                cell_pixels,
            )[0]
            offset = 0 if zero_motif else motif_offsets(
                motifs["motifs"][terrain], level, strength, [point]
            )[0]
            color, _applied = safe_color_offset(node.color, offset)
            old = node.color
            node.color = color
            record(terrain, old, color, area)
            stats.output_leaves += 1
            return node
        points_local = [(x, y) for y in range(node.y, node.y + node.size, 2) for x in range(node.x, node.x + node.size, 2)]
        points_global = [(origin_x + x, origin_y + y) for x, y in points_local]
        motif_points = motif_points_from_level_pixels(level, points_global, cell_pixels)
        offsets = [0] * len(motif_points) if zero_motif else motif_offsets(
            motifs["motifs"][terrain], level, strength, motif_points
        )
        colors: dict[tuple[int, int], int] = {}
        for point, offset in zip(points_local, offsets):
            color, _applied = safe_color_offset(node.color, offset)
            colors[point] = color
            record(terrain, node.color, color, 4)
        stats.output_leaves += len(points_local)
        return _full_refined_tree(node.x, node.y, node.size, node.owner, colors)

    block.root = transform(block.root)


def _level_path(directory: Path, level: int) -> Path:
    return directory / f"lightmap{level}.tbl"


def validate_directory(directory: Path) -> dict:
    result: dict[str, dict] = {}
    for level in range(1, 5):
        path = _level_path(directory, level)
        blocks = leaves = 0
        with LightmapFile(path, level) as lightmap:
            for index in range(lightmap.blocks):
                parsed = parse_block(lightmap.block(index))
                leaves += sum(1 for _ in iter_leaves(parsed.root))
                blocks += 1
            result[str(level)] = {
                "path": str(path),
                "blocks": blocks,
                "leaves": leaves,
                "trailer_bytes": len(lightmap.trailer),
                "sha256": sha256_file(path),
            }
    return result


def _write_compiled_level(
    source: Path,
    destination: Path,
    level: int,
    provinces: dict[int, str],
    motifs: dict,
    political_lut: Sequence[tuple[int, int, int]],
    terrain_luts: dict[str, Sequence[tuple[int, int, int]]],
    snow_lut: Sequence[tuple[int, int, int]],
    mud_lut: Sequence[tuple[int, int, int]],
    zero_motif: bool = False,
) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    stats = ChangeStats()
    try:
        with LightmapFile(source, level) as lightmap, temp_path.open("w+b") as output:
            output.write(b"\0" * lightmap.header_size)
            offsets = [0]
            for index in range(lightmap.blocks):
                block = parse_block(lightmap.block(index))
                block_x = (index % lightmap.width) * 32
                block_y = (index // lightmap.width) * 32
                transform_block(block, level, block_x, block_y, provinces, motifs, stats, zero_motif=zero_motif)
                encoded = encode_block(block, preserve_padding=False)
                output.write(encoded)
                offsets.append(offsets[-1] + len(encoded))
            output.write(lightmap.trailer)
            output.seek(0)
            output.write(struct.pack(f"<{len(offsets)}I", *offsets))
            output.flush()
            os.fsync(output.fileno())
            trailer_bytes = len(lightmap.trailer)
        os.replace(temp_path, destination)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    coverage = {
        terrain: (
            100.0 * stats.modified_pixels[terrain] / stats.ordinary_land_pixels[terrain]
            if stats.ordinary_land_pixels[terrain]
            else None
        )
        for terrain in TERRAINS
    }
    political = native_perceptual_metrics(stats.color_pairs, political_lut)
    terrain_mode = native_perceptual_metrics(stats.color_pairs, terrain_luts)
    snow = native_perceptual_metrics(stats.color_pairs, snow_lut)
    mud = native_perceptual_metrics(stats.color_pairs, mud_lut)
    if not zero_motif:
        try:
            enforce_compiled_gates(level, political, terrain_mode, snow, mud, motifs)
        except LightmapError:
            destination.unlink(missing_ok=True)
            raise
    return {
        "source": str(source),
        "output": str(destination),
        "source_sha256": sha256_file(source),
        "output_sha256": sha256_file(destination),
        "output_bytes": destination.stat().st_size,
        "trailer_bytes_preserved": trailer_bytes,
        "source_leaves": stats.source_leaves,
        "output_leaves": stats.output_leaves,
        "ordinary_land_pixels": stats.ordinary_land_pixels,
        "modified_pixels": stats.modified_pixels,
        "modified_coverage_percent_all_land": {k: None if v is None else round(v, 3) for k, v in coverage.items()},
        "native_perceptual": {
            "method": "offline truncating native LUT + CIEDE2000 release gates; DeltaE76 retained for continuity; not an engine screenshot",
            "political": political,
            "terrain": terrain_mode,
            "snow_provisional": snow,
            "mud_provisional": mud,
        },
        "zero_motif": zero_motif,
    }


def command_build(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    province_path = Path(args.province_csv).resolve()
    motif_path = Path(args.motifs).resolve()
    provinces = load_provinces(province_path)
    motifs = load_motifs(motif_path)
    motif_report = motif_metrics(motifs)
    colorscale_path = Path(args.colorscales).resolve() if args.colorscales else source_dir / "colorscales.csv"
    scales = load_colorscales(colorscale_path)
    country_colour = args.country_color or str(motifs["gates"]["native_country_colour"])
    political_lut = named_colorscale(scales, country_colour)
    map_colours_path = (
        Path(args.map_colors).resolve()
        if args.map_colors
        else source_dir.parents[1] / "Modding documentation" / "Map colors.txt"
    )
    documented_terrain_colours = load_terrain_colour_reference(map_colours_path)
    configured_terrain_colours = motifs["native_terrain_colour_by_terrain"]
    if documented_terrain_colours != configured_terrain_colours:
        raise LightmapError(
            f"motif terrain colour mapping differs from the supplied authoritative reference {map_colours_path}"
        )
    terrain_luts = {
        terrain: named_colorscale(scales, configured_terrain_colours[terrain]) for terrain in TERRAINS
    }
    weather_colours = motifs["native_weather_colour_by_state"]
    documented_weather_colours = load_weather_colour_reference(map_colours_path)
    if documented_weather_colours != weather_colours:
        raise LightmapError(
            f"motif weather colour mapping differs from the supplied authoritative reference {map_colours_path}"
        )
    snow_lut = named_colorscale(scales, weather_colours["Snow"])
    mud_lut = named_colorscale(scales, weather_colours["Mud"])
    cap_evidence: dict[str, dict] = {}
    for terrain in TERRAINS:
        name = configured_terrain_colours[terrain]
        lut = terrain_luts[terrain]
        labs = [rgb_to_lab(rgb) for rgb in lut]
        cap_evidence[terrain] = {
            "terrain_colour": name,
            "source_shade": 24,
            "safe_cap_index_delta": 10,
            "negative_cap_delta_e00": round(delta_e00(labs[24], labs[14]), 4),
            "negative_cap_delta_e76": round(delta_e76(labs[24], labs[14]), 4),
            "positive_cap_delta_e00": round(delta_e00(labs[24], labs[34]), 4),
            "positive_cap_delta_e76": round(delta_e76(labs[24], labs[34]), 4),
        }
    levels: dict[str, dict] = {}
    for level in range(1, 5):
        levels[str(level)] = _write_compiled_level(
            _level_path(source_dir, level),
            _level_path(output_dir, level),
            level,
            provinces,
            motifs,
            political_lut,
            terrain_luts,
            snow_lut,
            mud_lut,
            zero_motif=bool(args.zero_motif),
        )
    validation = validate_directory(output_dir)
    manifest_path = Path(args.manifest).resolve() if args.manifest else output_dir / "AUBM_ORIGINAL_TERRAIN_MANIFEST.json"
    manifest = {
        "format": "AUBM original terrain lightmap manifest v3",
        "build_mode": "zero-motif-refinement-fixture" if args.zero_motif else "procedural-motifs",
        "zero_motif": bool(args.zero_motif),
        "provenance": {
            "statement": "Generated from the player's local Darkest Hour lightmaps and original AUBM procedural recipes; no Blood and Iron or DEC pixels were read.",
            "source_directory": str(source_dir),
            "province_csv": str(province_path),
            "province_csv_sha256": sha256_file(province_path),
            "motifs": str(motif_path),
            "motifs_sha256": sha256_file(motif_path),
            "generator_sha256": sha256_file(Path(__file__).resolve()),
            "native_colorscales": str(colorscale_path),
            "native_colorscales_sha256": sha256_file(colorscale_path),
            "native_country_colour": country_colour,
            "terrain_colour_reference": str(map_colours_path),
            "terrain_colour_reference_sha256": sha256_file(map_colours_path),
            "native_terrain_colour_by_terrain": configured_terrain_colours,
            "native_weather_colour_by_state": weather_colours,
        },
        "technical_cap_evidence": {
            "purpose": "documents why the terrain-mode DE00 median gate is 2.25 rather than 3.0 under the reviewed +/-10 shade-index cap",
            "interpolation": "truncating linear interpolation matching Darkest Hour/MapUtility",
            "shade_24_signed_cap": cap_evidence,
            "actual_engine_human_visibility_gate": "mandatory; offline metrics are not acceptance",
        },
        "motif_validation": motif_report,
        "levels": levels,
        "compiled_validation": validation,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "levels": levels}, indent=2))


def command_validate(args: argparse.Namespace) -> None:
    print(json.dumps(validate_directory(Path(args.source_dir).resolve()), indent=2))


def command_roundtrip(args: argparse.Namespace) -> None:
    directory = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    report: dict[str, dict] = {}
    for level in range(1, 5):
        path = _level_path(directory, level)
        destination = _level_path(output_dir, level) if output_dir else None
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            target = destination.open("wb")
        else:
            target = None
        try:
            with LightmapFile(path, level) as lightmap:
                if target:
                    target.write(bytes(lightmap.mapping[: lightmap.header_size]))
                for index in range(lightmap.blocks):
                    raw = lightmap.block(index)
                    rebuilt = encode_block(parse_block(raw), preserve_padding=True)
                    if rebuilt != raw:
                        first = next((i for i, (a, b) in enumerate(zip(raw, rebuilt)) if a != b), min(len(raw), len(rebuilt)))
                        raise LightmapError(f"lightmap{level} block {index} is not canonical byte-identical at block byte {first}")
                    if target:
                        target.write(rebuilt)
                if target:
                    target.write(lightmap.trailer)
                report[str(level)] = {"blocks": lightmap.blocks, "byte_identical": True, "trailer_bytes": len(lightmap.trailer)}
        finally:
            if target:
                target.close()
        if destination and sha256_file(destination) != sha256_file(path):
            raise LightmapError(f"lightmap{level} round-trip file hash differs")
    print(json.dumps(report, indent=2))


def _raster(node: Node, owners: list[int], colors: list[int]) -> None:
    if node.children is not None:
        for child in node.children:
            _raster(child, owners, colors)
        return
    for y in range(node.y, node.y + node.size):
        start = y * 32 + node.x
        owners[start : start + node.size] = [node.owner] * node.size
        colors[start : start + node.size] = [node.color] * node.size


def raster_block(block: ParsedBlock) -> tuple[list[int], list[int]]:
    owners = [0] * 1024
    colors = [0] * 1024
    _raster(block.root, owners, colors)
    return owners, colors


def command_compare(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir).resolve()
    candidate_dir = Path(args.candidate_dir).resolve()
    provinces = load_provinces(Path(args.province_csv).resolve())
    motifs = load_motifs(Path(args.motifs).resolve())
    colorscale_path = Path(args.colorscales).resolve() if args.colorscales else source_dir / "colorscales.csv"
    country_colour = args.country_color or str(motifs["gates"]["native_country_colour"])
    scales = load_colorscales(colorscale_path)
    political_lut = named_colorscale(scales, country_colour)
    map_colours_path = (
        Path(args.map_colors).resolve()
        if args.map_colors
        else source_dir.parents[1] / "Modding documentation" / "Map colors.txt"
    )
    documented_terrain = load_terrain_colour_reference(map_colours_path)
    documented_weather = load_weather_colour_reference(map_colours_path)
    if documented_terrain != motifs["native_terrain_colour_by_terrain"]:
        raise LightmapError("configured terrain scales differ from the supplied Map colors.txt")
    if documented_weather != motifs["native_weather_colour_by_state"]:
        raise LightmapError("configured weather scales differ from the supplied Map colors.txt")
    terrain_luts = {terrain: named_colorscale(scales, documented_terrain[terrain]) for terrain in TERRAINS}
    snow_lut = named_colorscale(scales, documented_weather["Snow"])
    mud_lut = named_colorscale(scales, documented_weather["Mud"])
    report: dict[str, dict] = {}
    for level in range(1, 5):
        pairs: dict[str, Counter[tuple[int, int]]] = {terrain: Counter() for terrain in TERRAINS}
        with LightmapFile(_level_path(source_dir, level), level) as source, LightmapFile(
            _level_path(candidate_dir, level), level
        ) as candidate:
            if source.trailer != candidate.trailer:
                raise LightmapError(f"lightmap{level} trailer changed")
            for index in range(source.blocks):
                before = parse_block(source.block(index))
                after = parse_block(candidate.block(index))
                if before.province_words != after.province_words:
                    raise LightmapError(f"lightmap{level} block {index} province list changed")
                before_owners, before_colors = raster_block(before)
                after_owners, after_colors = raster_block(after)
                if before_owners != after_owners:
                    raise LightmapError(f"lightmap{level} block {index} pixel ownership changed")
                for owner, old, new in zip(before_owners, before_colors, after_colors):
                    word = before.province_words[owner]
                    pid = _word_province_id(word)
                    terrain = provinces.get(pid, "") if pid is not None else ""
                    ordinary_land = terrain in TERRAINS
                    if old != new:
                        if not ordinary_land:
                            raise LightmapError(f"lightmap{level} block {index} changed a protected/non-land pixel")
                        maximum = int(math.floor(float(motifs["motifs"][terrain]["amplitude"]) + 0.5))
                        if abs(new - old) > maximum:
                            raise LightmapError(
                                f"lightmap{level} block {index} moved {terrain} by {new - old}; maximum is {maximum}"
                            )
                    if ordinary_land:
                        pairs[terrain][(old, new)] += 1
            political = native_perceptual_metrics(pairs, political_lut)
            terrain_mode = native_perceptual_metrics(pairs, terrain_luts)
            snow = native_perceptual_metrics(pairs, snow_lut)
            mud = native_perceptual_metrics(pairs, mud_lut)
            gate_error = None
            if not args.zero_motif:
                try:
                    enforce_compiled_gates(level, political, terrain_mode, snow, mud, motifs)
                except LightmapError as error:
                    if not args.diagnostic_no_gates:
                        raise
                    gate_error = str(error)
            elif political["modified_pixels"] != 0:
                raise LightmapError(f"lightmap{level} zero-motif fixture changed raster colours")
            report[str(level)] = {
                "ownership_identical": True,
                "trailer_identical": True,
                "protected_and_non_land_identical": True,
                "ordinary_land_pixels": political["ordinary_land_pixels"],
                "modified_pixels": political["modified_pixels"],
                "modified_coverage_percent_all_land": political["modified_coverage_percent_all_land"],
                "native_country_colour": country_colour,
                "native_terrain_colour_by_terrain": documented_terrain,
                "native_weather_colour_by_state": documented_weather,
                "native_perceptual": {
                    "method": "offline truncating native LUT + CIEDE2000; DeltaE76 retained; not an engine screenshot",
                    "political": political,
                    "terrain": terrain_mode,
                    "snow_provisional": snow,
                    "mud_provisional": mud,
                },
                "gate_error": gate_error,
            }
    print(json.dumps(report, indent=2))


def command_render(args: argparse.Namespace) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise LightmapError("render and atlas output require Pillow") from exc
    level = int(args.lightmap)
    if not args.colorscales:
        raise LightmapError("render requires a real --colorscales file")
    if args.render_mode == "political" and not args.country_color:
        raise LightmapError("political render requires --country-color")
    if args.render_mode == "terrain" and (not args.province_csv or not args.map_colors):
        raise LightmapError("terrain render requires --province-csv and authoritative --map-colors")
    colorscale_path = Path(args.colorscales).resolve()
    scales = load_colorscales(colorscale_path)
    political_lut = named_colorscale(scales, args.country_color) if args.country_color else None
    water_lut = named_colorscale(scales, "Water")
    provinces = load_provinces(Path(args.province_csv).resolve()) if args.province_csv else {}
    terrain_names = load_terrain_colour_reference(Path(args.map_colors).resolve()) if args.map_colors else {}
    terrain_luts = {terrain: named_colorscale(scales, name) for terrain, name in terrain_names.items()}
    weather_lut = named_colorscale(scales, "White" if args.render_mode == "snow" else "Brown")
    x0, y0, width, height = args.x, args.y, args.width, args.height
    if min(x0, y0, width, height) < 0 or width == 0 or height == 0:
        raise LightmapError("render crop must use non-negative coordinates and positive dimensions")
    pixels = bytearray(width * height * 3)
    with LightmapFile(_level_path(Path(args.source_dir).resolve(), level), level) as lightmap:
        max_width, max_height = lightmap.width * 32, lightmap.height * 32
        if x0 + width > max_width or y0 + height > max_height:
            raise LightmapError(f"crop exceeds {max_width}x{max_height} lightmap bounds")
        bx0, bx1 = x0 // 32, (x0 + width - 1) // 32
        by0, by1 = y0 // 32, (y0 + height - 1) // 32
        for by in range(by0, by1 + 1):
            for bx in range(bx0, bx1 + 1):
                block = parse_block(lightmap.block(by * lightmap.width + bx))
                owners, colors = raster_block(block)
                for ly in range(32):
                    gy = by * 32 + ly
                    if not y0 <= gy < y0 + height:
                        continue
                    for lx in range(32):
                        gx = bx * 32 + lx
                        if not x0 <= gx < x0 + width:
                            continue
                        offset = ly * 32 + lx
                        word = block.province_words[owners[offset]]
                        pid = _word_province_id(word)
                        if pid is None:
                            lut = water_lut
                        elif args.render_mode == "political":
                            if political_lut is None:
                                raise LightmapError("political render has no country colour LUT")
                            lut = political_lut
                        elif args.render_mode == "terrain":
                            terrain = provinces.get(pid, "")
                            lut = terrain_luts.get(terrain, water_lut)
                        else:
                            lut = weather_lut
                        rgb = lut[colors[offset]]
                        target = ((gy - y0) * width + (gx - x0)) * 3
                        pixels[target : target + 3] = bytes(rgb)
    image = Image.frombytes("RGB", (width, height), bytes(pixels))
    if args.scale != 1.0:
        image = image.resize((max(1, round(width * args.scale)), max(1, round(height * args.scale))), Image.Resampling.NEAREST)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(json.dumps({
        "output": str(output),
        "size": list(image.size),
        "render": f"offline native {args.render_mode} named-colorscale mapping; not an engine screenshot",
        "colorscales": str(colorscale_path),
        "colorscales_sha256": sha256_file(colorscale_path),
        "country_colour": args.country_color if args.render_mode == "political" else None,
        "map_colours": str(Path(args.map_colors).resolve()) if args.map_colors else None,
        "contrast_multiplier": None,
    }, indent=2))


def write_atlas(data: dict, path: Path, lut: Sequence[tuple[int, int, int]]) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise LightmapError("atlas output requires Pillow") from exc
    cell = 3
    tile_cells = 32
    panel_w, panel_h = tile_cells * cell, tile_cells * cell + 20
    image = Image.new("RGB", (panel_w * 4, panel_h * 2), (27, 29, 31))
    draw = ImageDraw.Draw(image)
    for index, terrain in enumerate(TERRAINS):
        ox, oy = (index % 4) * panel_w, (index // 4) * panel_h
        recipe = data["motifs"][terrain]
        points = [(x, y) for y in range(tile_cells) for x in range(tile_cells)]
        offsets = motif_offsets(recipe, 1, float(data["zoom_strength"]["1"]), points)
        for (x, y), offset in zip(points, offsets):
            shade, _applied = safe_color_offset(24, offset)
            rgb = lut[shade]
            draw.rectangle((ox + x * cell, oy + y * cell, ox + (x + 1) * cell - 1, oy + (y + 1) * cell - 1), fill=rgb)
        draw.text((ox + 4, oy + tile_cells * cell + 3), terrain, fill=(238, 238, 232))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def command_motifs(args: argparse.Namespace) -> None:
    motif_path = Path(args.motifs).resolve()
    data = load_motifs(motif_path)
    metrics = motif_metrics(data)
    result: dict[str, object] = {"motifs": str(motif_path), "validation": metrics}
    if args.atlas:
        if not args.colorscales or not args.country_color:
            raise LightmapError("--atlas requires --colorscales and --country-color; diagnostic palette amplification is forbidden")
        atlas = Path(args.atlas).resolve()
        colorscale_path = Path(args.colorscales).resolve()
        write_atlas(data, atlas, named_colorscale(load_colorscales(colorscale_path), args.country_color))
        result["atlas"] = str(atlas)
        result["atlas_sha256"] = sha256_file(atlas)
        result["colorscales"] = str(colorscale_path)
        result["colorscales_sha256"] = sha256_file(colorscale_path)
        result["country_colour"] = args.country_color
        result["contrast_multiplier"] = None
    print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="structurally validate all four lightmaps")
    validate.add_argument("--source-dir", required=True)
    validate.set_defaults(func=command_validate)

    build = sub.add_parser("build", help="compile original AUBM motifs into local DH lightmaps")
    build.add_argument("--source-dir", required=True)
    build.add_argument("--province-csv", required=True)
    build.add_argument("--motifs", required=True)
    build.add_argument("--output-dir", required=True)
    build.add_argument("--manifest")
    build.add_argument(
        "--colorscales",
        help="real Darkest Hour colorscales.csv (defaults to SOURCE-DIR/colorscales.csv)",
    )
    build.add_argument(
        "--country-color",
        help="named political colour used for native perceptual gates (defaults to the motif recipe)",
    )
    build.add_argument(
        "--map-colors",
        help="authoritative Map colors.txt (defaults to the game root's Modding documentation copy)",
    )
    build.add_argument(
        "--zero-motif",
        action="store_true",
        help="refine ordinary land structurally while copying every baseline raster colour exactly",
    )
    build.set_defaults(func=command_build)

    roundtrip = sub.add_parser("roundtrip", help="prove canonical parse/write byte identity")
    roundtrip.add_argument("--source-dir", required=True)
    roundtrip.add_argument("--output-dir")
    roundtrip.set_defaults(func=command_roundtrip)

    compare = sub.add_parser("compare", help="prove compiled pixel ownership and protection invariants")
    compare.add_argument("--source-dir", required=True)
    compare.add_argument("--candidate-dir", required=True)
    compare.add_argument("--province-csv", required=True)
    compare.add_argument("--motifs", required=True)
    compare.add_argument("--colorscales", help="real colorscales.csv (defaults to SOURCE-DIR/colorscales.csv)")
    compare.add_argument("--country-color", help="named political colour (defaults to the motif recipe)")
    compare.add_argument("--map-colors", help="authoritative Map colors.txt (defaults from SOURCE-DIR)")
    compare.add_argument("--zero-motif", action="store_true", help="require a colour-neutral structural fixture")
    compare.add_argument(
        "--diagnostic-no-gates",
        action="store_true",
        help="report failed perceptual gates instead of aborting; never used for release acceptance",
    )
    compare.set_defaults(func=command_compare)

    render = sub.add_parser("render", help="render a diagnostic lightmap crop")
    render.add_argument("--source-dir", required=True)
    render.add_argument("--lightmap", type=int, choices=range(1, 5), required=True)
    render.add_argument("--x", type=int, required=True)
    render.add_argument("--y", type=int, required=True)
    render.add_argument("--width", type=int, required=True)
    render.add_argument("--height", type=int, required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--province-csv")
    render.add_argument("--colorscales", help="real Darkest Hour colorscales.csv")
    render.add_argument("--country-color", help="exact named country colour from colorscales.csv")
    render.add_argument("--map-colors", help="authoritative Map colors.txt; required for terrain mode")
    render.add_argument(
        "--render-mode",
        choices=("political", "terrain", "snow", "mud"),
        default="political",
        help="native offline LUT mode; output is never described as an engine screenshot",
    )
    render.add_argument("--scale", type=float, default=1.0)
    render.set_defaults(func=command_render)

    motifs = sub.add_parser("motifs", help="validate recipes and optionally write a QA atlas")
    motifs.add_argument("--motifs", required=True)
    motifs.add_argument("--atlas")
    motifs.add_argument("--colorscales", help="real Darkest Hour colorscales.csv; required with --atlas")
    motifs.add_argument("--country-color", help="named political colour; required with --atlas")
    motifs.set_defaults(func=command_motifs)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        args.func(args)
        return 0
    except (LightmapError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
