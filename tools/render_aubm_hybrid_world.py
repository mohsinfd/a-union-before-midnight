#!/usr/bin/env python3
"""Native-palette diagnostic from COMPILED maps, never an engine screenshot.

Every land province uses the selected comparison colour; water uses Water.
No contrast enhancement, image synthesis or artificial terrain hues in political mode.
"""
import argparse
import json
from pathlib import Path

import numpy as np

import aubm_hybrid_terrain as hybrid
from aubm_lightmap import TERRAINS, load_provinces, sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--crop-l1", type=int, nargs=4, required=True)
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--country-color", default="Gray")
    parser.add_argument("--modes", nargs="+", default=["political", "terrain"])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lut = np.full(16384, -1, np.int8)
    for pid, name in load_provinces(hybrid.PROVINCES).items():
        if 0 < pid < len(lut) and name in TERRAINS:
            lut[pid] = TERRAINS.index(name)
    record = {"renderer": __doc__, "source": str(args.source.resolve()),
              "country_color": args.country_color, "levels": {}}
    for level in args.levels:
        factor = 2 ** (level - 1)
        crop = tuple(value // factor for value in args.crop_l1)
        ids, shades = hybrid.raster(args.source, level, crop)
        terrain = lut[np.maximum(ids, 0)]
        for mode in args.modes:
            hybrid.render(ids, shades, terrain, mode, args.country_color).save(args.output / f"{mode}-l{level}.png")
        record["levels"][str(level)] = {"crop": crop,
            "lightmap_sha256": sha256_file(args.source / f"lightmap{level}.tbl")}
        print(f"Rendered actual L{level}: {crop}", flush=True)
    (args.output / "PREVIEW.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
