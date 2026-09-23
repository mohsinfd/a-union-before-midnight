#!/usr/bin/env python3
"""Compile the LOCAL-ONLY hybrid art worldwide, without editing any installation.

Uses the pilot's artwork and shade treatment, in bounded tiles with a label halo.
Province geometry, special words, water and label ink remain from the core map.
Donor-derived output belongs only in ignored local staging and test installations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

import aubm_hybrid_terrain as hybrid
from aubm_lightmap import (LightmapFile, SPECS, TERRAINS, _word_province_id,
                          encode_block, load_provinces, parse_block,
                          raster_block, sha256_file)

_MAPS = {}
_TERRAIN = None
_BASE = hybrid.CORE
_RETAINED_ONLY = False
HALO = 64
BUILD = "HYBRID-WORLD1"


def safe_output(out):
    out = Path(out).resolve()
    for forbidden in (hybrid.GAME, hybrid.REPO / "mod", hybrid.CORE, hybrid.DONOR):
        if out == forbidden.resolve() or out.is_relative_to(forbidden.resolve()):
            raise ValueError("World compiler may only write local staging, not game/public mod files")
    return out


def initialize(base=None):
    global _TERRAIN, _BASE, _RETAINED_ONLY
    _BASE = Path(base) if base else hybrid.CORE
    _RETAINED_ONLY = base is not None
    data = load_provinces(hybrid.PROVINCES)
    _TERRAIN = np.full(16384, -1, np.int8)
    for pid, name in data.items():
        if 0 < pid < len(_TERRAIN) and name in TERRAINS:
            _TERRAIN[pid] = TERRAINS.index(name)


def lightmap(directory, level):
    key = (str(directory), level)
    if key not in _MAPS:
        _MAPS[key] = LightmapFile(directory / f"lightmap{level}.tbl", level)
    return _MAPS[key]


def close_maps():
    for lm in _MAPS.values():
        lm.close()
    _MAPS.clear()


def raster(lm, crop):
    x, y, w, h = crop
    ids = np.full((h, w), -1, np.int32)
    shades = np.zeros((h, w), np.uint8)
    for by in range(y // 32, (y + h - 1) // 32 + 1):
        for bx in range(x // 32, (x + w - 1) // 32 + 1):
            block = parse_block(lm.block(by * lm.width + bx))
            oo, cc = raster_block(block)
            pids = np.asarray([_word_province_id(v) or -1 for v in block.province_words], np.int32)
            owners = pids[np.asarray(oo)].reshape(32, 32)
            colors = np.asarray(cc, np.uint8).reshape(32, 32)
            gx, gy = bx * 32, by * 32
            sx, sy = max(x - gx, 0), max(y - gy, 0)
            ex, ey = min(x + w - gx, 32), min(y + h - gy, 32)
            target = np.s_[gy + sy - y:gy + ey - y, gx + sx - x:gx + ex - x]
            ids[target] = owners[sy:ey, sx:ex]
            shades[target] = colors[sy:ey, sx:ex]
    return ids, shades


def has_treated_land(data):
    for pos in range(0, len(data), 2):
        word = struct.unpack_from("<H", data, pos)[0]
        pid = _word_province_id(word)
        if pid is not None and (_TERRAIN[pid] in (1, 2, 3) if _RETAINED_ONLY else _TERRAIN[pid] > 0):
            return True
        if word & 0x8000:
            return False
    raise ValueError("Unterminated core province list")


def fields(level, crop):
    ids, core = raster(lightmap(hybrid.CORE, level), crop)
    terrain = _TERRAIN[np.maximum(ids, 0)]
    if level <= 2:
        donor_ids, donor = raster(lightmap(hybrid.DONOR, level), crop)
        mismatch = (donor_ids != ids) & (ids > 0)
        donor[mismatch] = core[mismatch]
        donor = hybrid.strip_donor_ink(donor, core, terrain, level)
    else:
        factor = 2 ** (level - 2)
        x, y, w, h = crop
        donor_ids, donor = raster(lightmap(hybrid.DONOR, 2),
                                 (x * factor, y * factor, w * factor, h * factor))
        donor_ids = donor_ids.reshape(h, factor, w, factor).transpose(0, 2, 1, 3)
        donor = donor.reshape(h, factor, w, factor).transpose(0, 2, 1, 3)
        match = (donor_ids == ids[:, :, None, None]) & (donor < 45)
        total = match.sum(axis=(2, 3))
        donor = np.rint((donor * match).sum(axis=(2, 3)) / np.maximum(1, total)).astype(np.uint8)
        donor[total == 0] = core[total == 0]
    return ids, core, donor, terrain


def pixel_digest(words, owners, colors):
    digest = hashlib.sha256(struct.pack(f"<{len(words)}H", *words))
    digest.update(np.asarray(owners, np.uint8).tobytes())
    digest.update(np.asarray(colors, np.uint8).tobytes())
    return digest.hexdigest()


def build_tile(job):
    level, x, y, w, h = job
    lm = lightmap(hybrid.CORE, level)
    indexes = [by * lm.width + bx for by in range(y // 32, (y + h) // 32)
               for bx in range(x // 32, (x + w) // 32)]
    if not any(has_treated_land(lm.block(i)) for i in indexes):
        return [], {}, [], len(indexes)
    left, top = max(0, x - HALO), max(0, y - HALO)
    right, bottom = min(lm.width * 32, x + w + HALO), min(lm.height * 32, y + h + HALO)
    crop = (left, top, right - left, bottom - top)
    ids, core, donor, terrain = fields(level, crop)
    result, protected = hybrid.compose(level, crop, core, donor, terrain)
    base_map = lightmap(_BASE, level)
    previous = raster(base_map, crop)[1] if _BASE != hybrid.CORE else core
    sx, sy = x - left, y - top
    center = np.s_[sy:sy + h, sx:sx + w]
    counts = {name: int(np.count_nonzero((terrain[center] == i) & (result[center] != core[center])))
              for i, name in enumerate(TERRAINS)}
    seen = np.unique(ids[center][terrain[center] > 0]).tolist()
    assert np.array_equal(core[protected], result[protected])
    patches = []
    for index in indexes:
        bx, by = index % lm.width * 32 - left, index // lm.width * 32 - top
        after = result[by:by + 32, bx:bx + 32]
        if np.array_equal(previous[by:by + 32, bx:bx + 32], after):
            continue
        block = parse_block(lm.block(index))
        oo, _ = raster_block(block)
        owners = np.asarray(oo).reshape(32, 32)
        block.root = hybrid.tree_from_arrays(owners, after)
        encoded = encode_block(block, preserve_padding=False)
        check = parse_block(encoded)
        checked_owners, checked_colors = raster_block(check)
        assert check.province_words == block.province_words
        assert np.array_equal(np.asarray(checked_owners).reshape(32, 32), owners)
        assert np.array_equal(np.asarray(checked_colors).reshape(32, 32), after)
        digest = pixel_digest(block.province_words, owners, after)
        patches.append((index, encoded, digest))
    return patches, counts, seen, len(indexes)


def jobs_for(level, tile_blocks):
    bw, bh = SPECS[level]
    step = tile_blocks * 32
    return [(level, x, y, min(step, bw * 32 - x), min(step, bh * 32 - y))
            for y in range(0, bh * 32, step) for x in range(0, bw * 32, step)]


def assemble(level, patches, out, base_dir=hybrid.CORE):
    target = out / f"lightmap{level}.tbl"
    with LightmapFile(base_dir / target.name, level) as lm, target.open("wb") as dest:
        dest.write(b"\0" * lm.header_size)
        offsets = [0]
        for index in range(lm.blocks):
            data = patches[index][0] if index in patches else lm.block(index)
            dest.write(data)
            offsets.append(offsets[-1] + len(data))
        dest.write(lm.trailer)
        dest.seek(0)
        dest.write(struct.pack(f"<{len(offsets)}I", *offsets))
    checked = 0
    with LightmapFile(base_dir / target.name, level) as base, LightmapFile(target, level) as actual:
        assert base.trailer == actual.trailer
        for index in range(actual.blocks):
            data = actual.block(index)
            if index not in patches:
                assert data == base.block(index)
            else:
                assert data == patches[index][0]
                block = parse_block(data)
                oo, cc = raster_block(block)
                assert pixel_digest(block.province_words, oo, cc) == patches[index][1]
                checked += 1
                if checked % 10000 == 0:
                    print(f"L{level}: reread {checked:,} written patches", flush=True)
    return {"sha256": sha256_file(target), "patched_blocks": len(patches),
            "all_written_blocks_verified": True, "geometry_and_render_roundtrip": True,
            "untouched_blocks_byte_identical": True, "trailer_unchanged": True}


def inputs():
    paths = [hybrid.ATLAS, hybrid.PROVINCES]
    paths.extend(hybrid.CORE / f"lightmap{level}.tbl" for level in range(1, 5))
    paths.extend(hybrid.DONOR / f"lightmap{level}.tbl" for level in (1, 2))
    return {str(path): sha256_file(path) for path in paths}


def compile_world(out, workers=4, tile_blocks=16, base=None):
    out = safe_output(out)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Use an empty staging directory; existing build will not be overwritten")
    before = inputs()
    receipt = {"build": BUILD, "status": "local-world-prototype-not-human-accepted",
               "base_gameplay": "4.2.0-alpha.27", "scope": "worldwide, all four zooms",
               "renderer": "actual six-bit map shading; no province/gameplay edits",
               "input_sha256": dict(before), "levels": {}}
    receipt["donor_lettering_cleanup"] = "native core font; donor dark ink removed with forest-symbol protection"
    receipt["source_code_sha256"] = {str(p): sha256_file(p) for p in (Path(__file__), Path(hybrid.__file__))}
    if base:
        base = base.resolve()
        prior = json.loads((base / "HYBRID_WORLD.json").read_text(encoding="utf-8"))
        if prior.get("build") != BUILD or set(prior["levels"]) != {"1", "2", "3", "4"}:
            raise ValueError("Incremental base must be a verified complete world build")
        for level in range(1, 5):
            path = base / f"lightmap{level}.tbl"
            expected = prior["levels"][str(level)]["sha256"]
            if sha256_file(path) != expected:
                raise ValueError(f"Incremental base L{level} changed")
            receipt["input_sha256"][str(path)] = expected
        receipt["incremental_base"] = str(base)
        receipt["base_receipt_sha256"] = sha256_file(base / "HYBRID_WORLD.json")
        for level in (3, 4):
            shutil.copy2(base / f"lightmap{level}.tbl", out / f"lightmap{level}.tbl")
            assert sha256_file(out / f"lightmap{level}.tbl") == prior["levels"][str(level)]["sha256"]
            receipt["levels"][str(level)] = prior["levels"][str(level)]
    start = time.monotonic()
    with ProcessPoolExecutor(max_workers=workers, initializer=initialize, initargs=(base,)) as pool:
        # Coarsest first gives an early worldwide preview, not just an India sample.
        for level in ((2, 1) if base else (4, 3, 2, 1)):
            jobs = jobs_for(level, tile_blocks)
            pending = [pool.submit(build_tile, job) for job in jobs]
            patches, seen = {}, set()
            counts = {name: 0 for name in TERRAINS}
            blocks = done = 0
            last = time.monotonic()
            for future in as_completed(pending):
                result, tally, observed, checked = future.result()
                for index, data, digest in result:
                    assert index not in patches
                    patches[index] = (data, digest)
                for name, count in tally.items():
                    counts[name] += count
                seen.update(observed)
                blocks += checked
                done += 1
                now = time.monotonic()
                if now - last >= 15 or done == len(jobs):
                    print(f"L{level}: {done}/{len(jobs)} tiles, {blocks:,} blocks checked, "
                          f"{len(patches):,} patched; elapsed {now-start:.0f}s", flush=True)
                    last = now
            assert blocks == SPECS[level][0] * SPECS[level][1]
            print(f"L{level}: assembling and rereading actual file", flush=True)
            info = assemble(level, patches, out, base or hybrid.CORE)
            info.update(changed_pixels_by_terrain=counts, observed_treated_provinces=sorted(seen),
                        all_core_blocks_considered=blocks, protected_pixels_unchanged=True)
            if base:
                info["comparison_base"] = str(base)
                info["base_patched_blocks"] = prior["levels"][str(level)]["patched_blocks"]
            receipt["levels"][str(level)] = info
            (out / "WORLD_PROGRESS.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(f"L{level} verified: {info['sha256']}", flush=True)
    if inputs() != before or any(sha256_file(Path(p)) != expected
                                for p, expected in receipt["input_sha256"].items()):
        raise ValueError("Source files changed during compilation; build not approved")
    receipt["elapsed_seconds"] = round(time.monotonic() - start, 1)
    receipt["inputs_unchanged"] = True
    (out / "HYBRID_WORLD.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Worldwide local build verified in {receipt['elapsed_seconds']} seconds", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--tile-blocks", type=int, default=16)
    parser.add_argument("--base", type=Path, help="verified world build for the L1/L2 lettering correction only")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8 or not 1 <= args.tile_blocks <= 32:
        parser.error("workers must be 1..8 and tile-blocks 1..32")
    compile_world(args.output, args.workers, args.tile_blocks, args.base)


if __name__ == "__main__":
    main()
