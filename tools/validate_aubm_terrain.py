#!/usr/bin/env python3
"""Static release gate for AUBM's original all-terrain source pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from aubm_lightmap import SPECS, TERRAINS, load_motifs, load_provinces, motif_metrics, sha256_file


EXPECTED_SPECS = {
    1: (936, 360),
    2: (468, 180),
    3: (234, 90),
    4: (117, 45),
}
FORBIDDEN_DONOR_HASHES = {
    "5678ef053cdc78b1f53d2477209411847c23478cb42987baa91a57e0b55cccec",
    "abf9a0397248b151eaf7fa198b084895f3a139fef10d3f061970bea5b870f8f4",
    "6b72e5b2855e9ced79c1290e892769dee43b62c26c2b4a42ad8e9a04e3e14df2",
}
COMPILED_PATHS = tuple(f"mod/map/Map_1/lightmap{level}.tbl" for level in range(1, 5))
COMPILED_PATHS += ("mod/map/Map_1/colorscales.csv",)


def fail(message: str) -> None:
    raise RuntimeError(message)


def tracked_paths(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        fail(f"could not inspect Git's tracked-file set: {error}")
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    motif_path = root / "assets/v4_terrain/aubm_terrain_motifs.json"
    atlas_path = root / "assets/v4_terrain/aubm_terrain_motif_atlas.png"
    moodboard_path = root / "assets/v4_terrain/aubm_terrain_motif_moodboard.png"
    province_path = root / "mod/map/Map_1/Province.csv"
    denylist_path = root / "installer/nonredistributable-overlay-patterns.txt"
    ignore_path = root / ".gitignore"
    installer_path = root / "tools/Enable-Aubm-OriginalTerrainVisuals.ps1"
    sprite_helper_path = root / "tools/Enable-Aubm-PersonalIndiaSprites.ps1"

    if SPECS != EXPECTED_SPECS:
        fail(f"lightmap dimensions changed: {SPECS!r}")
    if len(TERRAINS) != 8 or len(set(TERRAINS)) != 8:
        fail("the compiler must define exactly eight unique mechanical land terrains")

    motifs = load_motifs(motif_path)
    metrics = motif_metrics(motifs)
    provinces = load_provinces(province_path)
    counts = Counter(provinces.values())
    missing = [terrain for terrain in TERRAINS if counts[terrain] <= 0]
    if missing:
        fail(f"Province.csv has no provinces for: {', '.join(missing)}")

    for path in (atlas_path, moodboard_path):
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"terrain review asset is missing or empty: {path.relative_to(root)}")
        if sha256_file(path) in FORBIDDEN_DONOR_HASHES:
            fail(f"terrain review asset matches a forbidden donor hash: {path.relative_to(root)}")

    denylist = {
        line.strip().replace("\\", "/")
        for line in denylist_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    ignored = {
        line.strip().replace("\\", "/")
        for line in ignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    expected_denied = {path.removeprefix("mod/") for path in COMPILED_PATHS}
    if not expected_denied.issubset(denylist):
        fail("the public-installer denylist does not exclude every compiled lightmap/palette path")
    if not set(COMPILED_PATHS).issubset(ignored):
        fail(".gitignore does not exclude every locally compiled lightmap/palette path")

    tracked = tracked_paths(root)
    leaked = sorted(set(COMPILED_PATHS) & tracked)
    if leaked:
        fail(f"locally derived compiled terrain is tracked by Git: {', '.join(leaked)}")

    installer_source = installer_path.read_text(encoding="utf-8")
    if "[System.IO.File]::Replace($temporary, $Path, $null" in installer_source or (
        "[System.IO.File]::Replace($temporary, $Destination, $null" in installer_source
    ):
        fail("the Windows PowerShell atomic swap must not pass a null backup path")
    if installer_source.count(".aubm-replaced-") < 2:
        fail("the terrain installer is missing its same-directory atomic replacement backups")
    for helper in (installer_path, sprite_helper_path):
        source = helper.read_text(encoding="utf-8")
        if "[string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)" in source:
            fail(f"{helper.name} resolves PSScriptRoot too early for direct -File invocation")

    report = {
        "status": "passed",
        "mechanical_land_terrains": list(TERRAINS),
        "province_counts": {terrain: counts[terrain] for terrain in TERRAINS},
        "lightmap_dimensions_blocks": {str(level): list(size) for level, size in SPECS.items()},
        "motif_sha256": sha256_file(motif_path),
        "atlas_sha256": sha256_file(atlas_path),
        "moodboard_sha256": sha256_file(moodboard_path),
        "motif_gates": metrics["gates"],
        "compiled_runtime_payload": "local-only; excluded from Git and the public installer",
        "donor_pixels": "none",
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
