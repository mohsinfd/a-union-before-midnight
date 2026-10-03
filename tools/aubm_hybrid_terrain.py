#!/usr/bin/env python3
"""LOCAL-ONLY hybrid terrain prototype. Never publishes donor-derived output.

Uses the established codec, not the rejected procedural mark generator.
Original atlas pixels become actual six-bit lightmap shading. Only a bounded
India/Burma prototype region is patched; the user's installed mod is not edited.
"""
from __future__ import annotations

import argparse
import csv
import json
import struct
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from aubm_lightmap import (
    CHILD_OFFSETS, LightmapFile, Node, TERRAINS, _word_province_id,
    encode_block, load_colorscales, load_provinces, named_colorscale,
    parse_block, raster_block, sha256_file,
)

REPO = Path(__file__).resolve().parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game")
CORE = GAME / "map/Map_1"
DONOR = GAME / "Mods/Blood and Iron v1.1/map/Map_1"
LIVE = GAME / "Mods/A Union Before Midnight V4.2/map/Map_1"
ATLAS = REPO / "assets/v4_terrain/hybrid/terrain-atlas-v1.png"
PROVINCES = REPO / "mod/map/Map_1/Province.csv"
REGION = (20200, 3904, 2944, 2240)
SCALES = dict(Plains="Orange", Forest="Green", Mountain="Gray", Desert="Yellow",
              Marsh="LightGreen", Hills="DarkOrange", Jungle="DarkGreen", Urban="DarkGray")
NEW = {"Hills": (0, 0), "Jungle": (1, 0), "Marsh": (0, 1), "Urban": (1, 1)}


def strip_donor_ink(donor, core=None, terrain=None, level=1):
    """Remove donor lettering before sampling relief; keep only the core font.

    B&I bakes a different font into its shading. A two-pixel halo removes the
    antialias fringe around dark ink; neighbouring non-ink shade fills the holes.
    This is not contrast enhancement. The final compositor restores core labels.
    """
    ink = donor >= 45
    if core is not None and terrain is not None:
        # Forest silhouettes also use dark strokes. Remove their donor lettering
        # only beside the core lettering, not every dark tree crown on the map.
        radius = max(3, 8 // (2 ** (level - 1)))
        near_core_ink = np.asarray(Image.fromarray((core >= 45).astype(np.uint8) * 255)
                                   .filter(ImageFilter.MaxFilter(radius * 2 + 1))) > 0
        ink &= (terrain != TERRAINS.index("Forest")) | near_core_ink
    if not np.any(ink):
        return donor
    mask = np.asarray(Image.fromarray(ink.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    values = donor.astype(np.float32)
    known = ~mask
    for _ in range(24):
        if np.all(known):
            break
        v = np.pad(values * known, 1)
        k = np.pad(known.astype(np.float32), 1)
        total = np.zeros(values.shape, np.float32)
        count = np.zeros(values.shape, np.float32)
        h, w = values.shape
        for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            total += v[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            count += k[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        fill = ~known & (count > 0)
        values[fill] = total[fill] / count[fill]
        known[fill] = True
    values[~known] = 19
    return np.rint(values).astype(np.uint8)


def raster(directory: Path, level: int, crop: tuple[int, int, int, int]):
    x0, y0, w, h = crop
    pid = np.full((h, w), -1, np.int32)
    color = np.zeros((h, w), np.uint8)
    with LightmapFile(directory / f"lightmap{level}.tbl", level) as lm:
        for by in range(y0 // 32, (y0+h-1) // 32+1):
            for bx in range(x0 // 32, (x0+w-1) // 32+1):
                block = parse_block(lm.block(by * lm.width + bx))
                owners, shades = raster_block(block)
                pids = np.asarray([_word_province_id(v) or -1 for v in block.province_words])
                bp = pids[np.asarray(owners)].reshape(32, 32)
                bc = np.asarray(shades, np.uint8).reshape(32, 32)
                gx, gy = bx*32, by*32
                sx, sy = max(x0-gx, 0), max(y0-gy, 0)
                ex, ey = min(x0+w-gx, 32), min(y0+h-gy, 32)
                target = np.s_[gy+sy-y0:gy+ey-y0, gx+sx-x0:gx+ex-x0]
                pid[target] = bp[sy:ey, sx:ex]
                color[target] = bc[sy:ey, sx:ex]
    return pid, color


def source_at_level(level, crop):
    if level <= 2:
        return raster(DONOR, level, crop)
    factor = 2 ** (level-2)
    x, y, w, h = crop
    pids, shades = raster(DONOR, 2, (x*factor, y*factor, w*factor, h*factor))
    # Do not average province-edge/text pixels into land relief at distant zooms.
    # Match each core owner below; invalid samples fall back to the core.
    pids = pids.reshape(h, factor, w, factor).transpose(0, 2, 1, 3)
    shades = shades.reshape(h, factor, w, factor).transpose(0, 2, 1, 3)
    return pids, shades


def fields(level, crop):
    ids, core = raster(CORE, level, crop)
    donor_ids, donor = source_at_level(level, crop)
    if level > 2:
        match = (donor_ids == ids[:, :, None, None]) & (donor < 45)
        total = match.sum(axis=(2, 3))
        donor = np.rint((donor * match).sum(axis=(2, 3)) / np.maximum(1, total)).astype(np.uint8)
        donor[total == 0] = core[total == 0]
    else:
        mismatch = (donor_ids != ids) & (ids > 0)
        # Donor geometry is never used; only matching ordinary province pixels.
        donor[mismatch] = core[mismatch]
    data = load_provinces(PROVINCES)
    terrain = np.full(ids.shape, -1, np.int8)
    for i, name in enumerate(TERRAINS):
        terrain[np.isin(ids, [p for p, t in data.items() if t == name])] = i
    if level <= 2:
        donor = strip_donor_ink(donor, core, terrain, level)
    return ids, core, donor, terrain


@lru_cache(maxsize=16)
def atlas_tile(name, level):
    im = Image.open(ATLAS).convert("L")
    hw, hh = im.width//2, im.height//2
    col, row = NEW[name]
    im = im.crop((col*hw, row*hh, (col+1)*hw, (row+1)*hh))
    widths = (256, 192, 128, 96) if name != "Urban" else (144, 112, 88, 64)
    size = widths[level-1]
    tile = np.asarray(im.resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32)
    # Mechanical quantization into DH's actual shade range, not preview contrast.
    ground, gain = {"Hills": (165, .22), "Jungle": (130, .15),
                    "Marsh": (165, .22), "Urban": (155, .22)}[name]
    shade = np.clip(np.rint(19 + (ground-tile)*gain), 5, 43).astype(np.uint8)
    return shade


def atlas_field(name, level, crop):
    shade = atlas_tile(name, level)
    size = shade.shape[0]
    col, row = NEW[name]
    x, y, w, h = crop
    # Reflect at tile boundaries to avoid a discontinuous rectangular seam.
    xx = (np.arange(x, x+w) + col*43) % (size*2)
    yy = (np.arange(y, y+h) + row*71) % (size*2)
    xx = np.where(xx < size, xx, size*2-1-xx)
    yy = np.where(yy < size, yy, size*2-1-yy)
    return shade[yy[:, None], xx[None, :]]


def candidate(level, crop):
    ids, core, donor, terrain = fields(level, crop)
    result, protected = compose(level, crop, core, donor, terrain)
    return ids, core, donor, terrain, result, protected


def compose(level, crop, core, donor, terrain):
    """Shared pilot/world treatment; callers supply a halo for tiled builds."""
    result = core.copy()
    retained = np.isin(terrain, [TERRAINS.index(x) for x in ("Mountain", "Desert", "Forest")])
    result[retained] = donor[retained]
    for name in NEW:
        mask = terrain == TERRAINS.index(name)
        result[mask] = atlas_field(name, level, crop)[mask]
    # Plains use clean core, not Alpha 27's speckle. Keep original label pixels
    # and a one-pixel halo around them; leave special words and non-land exact.
    ink = Image.fromarray((core >= 40).astype(np.uint8) * 255)
    feather = np.asarray(ink.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)/255
    result = np.rint(result*(1-feather) + core*feather).astype(np.uint8)
    protected = (core >= 45) | (terrain < 0)
    result[protected] = core[protected]
    assert np.array_equal(result[protected], core[protected])
    return result, protected


def render(ids, color, terrain, mode="political", country="Gray"):
    scales = load_colorscales(CORE / "colorscales.csv")
    water = np.asarray(named_colorscale(scales, "Water"), np.uint8)
    rgb = water[color]
    if mode == "political":
        lut = np.asarray(named_colorscale(scales, country), np.uint8)
        rgb[terrain >= 0] = lut[color[terrain >= 0]]
    elif mode in ("snow", "mud"):
        lut = np.asarray(named_colorscale(scales, "White" if mode == "snow" else "Brown"), np.uint8)
        rgb[terrain >= 0] = lut[color[terrain >= 0]]
    else:
        for i, name in enumerate(TERRAINS):
            lut = np.asarray(named_colorscale(scales, SCALES[name]), np.uint8)
            mask = terrain == i
            rgb[mask] = lut[color[mask]]
    return Image.fromarray(rgb)


def preview(out, crop, country="Gray"):
    out.mkdir(parents=True, exist_ok=True)
    report = {"status": "prototype-not-human-accepted", "atlas_sha256": sha256_file(ATLAS),
              "source": "local Blood and Iron L1/L2 plus original raster atlas",
              "region_l1": crop, "country_colour": country, "levels": {},
              "renderer": "offline native LUT; NOT engine screenshot"}
    for level in range(1, 5):
        factor = 2**(level-1)
        rect = tuple(v//factor for v in crop)
        ids, core, donor, terrain, result, protected = candidate(level, rect)
        _, alpha = raster(LIVE, level, rect)
        for mode in ("political", "terrain", "snow", "mud"):
            render(ids, result, terrain, mode, country).save(out / f"hybrid-{mode}-l{level}.png")
        for label, field in (("bi", donor), ("alpha27", alpha)):
            render(ids, field, terrain, country=country).save(out / f"{label}-political-l{level}.png")
        # Full-size render at every zoom; never amplify the preview.
        np.savez_compressed(out / f"raster-l{level}.npz", ids=ids, core=core,
                            result=result, protected=protected, terrain=terrain)
        counts = {name: int(((terrain == i) & (result != core)).sum()) for i, name in enumerate(TERRAINS)}
        report["levels"][str(level)] = {"crop": rect, "changed_pixels": counts,
                                      "protected_pixels_unchanged": bool(np.array_equal(core[protected], result[protected]))}
        print(f"Preview L{level}: {counts}", flush=True)
    (out / "preview.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def tree_from_arrays(owners, colors, x=0, y=0, size=32):
    o, c = owners[y:y+size, x:x+size], colors[y:y+size, x:x+size]
    if size == 1 or (np.all(o == o[0, 0]) and np.all(c == c[0, 0])):
        return Node(x, y, size, owner=int(o[0, 0]), color=int(c[0, 0]))
    half = size//2
    children = tuple(tree_from_arrays(owners, colors, x+dx*half, y+dy*half, half)
                     for dx, dy in CHILD_OFFSETS)
    return Node(x, y, size, children=children)


def compile_region(previews, out):
    if out.resolve().is_relative_to(GAME.resolve()) or out.resolve().is_relative_to((REPO / "mod").resolve()):
        raise ValueError("Prototype compiler may write only to a staging directory, never a game/mod folder")
    out.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((previews / "preview.json").read_text())
    if recipe["atlas_sha256"] != sha256_file(ATLAS):
        raise ValueError("Atlas changed since preview; rebuild previews first")
    receipt = {"status": "local-prototype-not-release", "levels": {}}
    for level in range(1, 5):
        x, y, w, h = recipe["levels"][str(level)]["crop"]
        cache = np.load(previews / f"raster-l{level}.npz")
        result = cache["result"]
        path = out / f"lightmap{level}.tbl"
        changed = 0
        with LightmapFile(CORE / path.name, level) as lm, path.open("wb") as dest:
            dest.write(b"\0" * lm.header_size)
            offsets = [0]
            for index in range(lm.blocks):
                bx, by = index % lm.width * 32, index // lm.width * 32
                data = lm.block(index)
                if bx < x+w and bx+32 > x and by < y+h and by+32 > y:
                    block = parse_block(data)
                    owners, colors = raster_block(block)
                    owners = np.asarray(owners).reshape(32, 32)
                    colors = np.asarray(colors, np.uint8).reshape(32, 32)
                    before = colors.copy()
                    sx, sy = max(x-bx, 0), max(y-by, 0)
                    ex, ey = min(x+w-bx, 32), min(y+h-by, 32)
                    colors[sy:ey, sx:ex] = result[by+sy-y:by+ey-y, bx+sx-x:bx+ex-x]
                    if not np.array_equal(before, colors):
                        block.root = tree_from_arrays(owners, colors)
                        data = encode_block(block, preserve_padding=False)
                        check = parse_block(data)
                        oo, cc = raster_block(check)
                        assert check.province_words == block.province_words
                        assert np.array_equal(np.asarray(oo).reshape(32, 32), owners)
                        assert np.array_equal(np.asarray(cc).reshape(32, 32), colors)
                        changed += 1
                        if changed % 1000 == 0:
                            print(f"L{level}: {changed} patched blocks independently decoded", flush=True)
                dest.write(data)
                offsets.append(offsets[-1]+len(data))
            dest.write(lm.trailer)
            dest.seek(0)
            dest.write(struct.pack(f"<{len(offsets)}I", *offsets))
        # Reopen the actual written file, not just encoded in-memory blocks.
        ids, shades = raster(out, level, (x, y, w, h))
        assert np.array_equal(ids, cache["ids"])
        assert np.array_equal(shades, result)
        with LightmapFile(CORE / path.name, level) as base, LightmapFile(path, level) as written:
            assert base.trailer == written.trailer
        receipt["levels"][str(level)] = {"sha256": sha256_file(path), "patched_blocks": changed,
                                          "geometry_and_render_roundtrip": True}
        print(f"Compiled and reread L{level}: {changed} blocks", flush=True)
    (out / "HYBRID_PROTOTYPE.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "compile", "recolor"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previews", type=Path)
    parser.add_argument("--crop", nargs=4, type=int, default=REGION)
    parser.add_argument("--country-color", default="Gray")
    args = parser.parse_args()
    if args.command == "preview":
        preview(args.output, tuple(args.crop), args.country_color)
    elif args.command == "compile":
        compile_region(args.previews, args.output)
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for level in range(1, 5):
            cache = np.load(args.previews / f"raster-l{level}.npz")
            for mode in ("political", "terrain", "snow", "mud"):
                render(cache["ids"], cache["result"], cache["terrain"], mode,
                       args.country_color).save(args.output / f"hybrid-{mode}-l{level}.png")
        print(f"Native {args.country_color} previews saved; no lightmaps or installed files changed")


if __name__ == "__main__":
    main()
