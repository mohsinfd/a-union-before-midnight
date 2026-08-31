#!/usr/bin/env python3
"""Static release gate for AUBM's original all-terrain source pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from aubm_lightmap import (
    SPECS,
    TERRAINS,
    ChangeStats,
    LightmapError,
    Node,
    ParsedBlock,
    delta_e00,
    delta_e76,
    encode_block,
    enforce_compiled_gates,
    iter_leaves,
    load_colorscales,
    load_motifs,
    load_provinces,
    load_terrain_colour_reference,
    load_weather_colour_reference,
    motif_metrics,
    motif_points_from_level_pixels,
    named_colorscale,
    native_perceptual_metrics,
    parse_block,
    raster_block,
    rgb_to_lab,
    safe_color_offset,
    sha256_file,
    transform_block,
)


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--colorscales",
        help="optional real Darkest Hour colorscales.csv for the native perceptual regression",
    )
    parser.add_argument("--map-colors", help="optional authoritative Darkest Hour Map colors.txt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
    expected_amplitudes = {
        "Plains": 10,
        "Hills": 8,
        "Desert": 10,
        "Marsh": 9,
        "Forest": 10,
        "Urban": 8,
        "Jungle": 9,
        "Mountain": 10,
    }
    actual_amplitudes = {terrain: motifs["motifs"][terrain]["amplitude"] for terrain in TERRAINS}
    if actual_amplitudes != expected_amplitudes:
        fail(f"native-contrast amplitudes changed: {actual_amplitudes!r}")
    if "terrain_color_anchors" in motifs:
        fail("fixed lightmap-colour anchors must not limit ordinary mechanical land")
    if any(float(value) != 1.0 for value in motifs["zoom_strength"].values()):
        fail("motif contrast must not attenuate at distant zooms")
    for level in range(1, 5):
        points = [(0, 0), (1, 1), (2, 2), (31, 47), (128, 255)]
        expected_points = [(x // 2, y // 2) for x, y in points]
        if motif_points_from_level_pixels(level, points, 2) != expected_points:
            fail(f"zoom {level} motif phase is not world-origin locked at two screen pixels per cell")
    for color in range(64):
        for offset in range(-10, 11):
            new, applied = safe_color_offset(color, offset)
            if not 0 <= new <= 63 or new - color != applied or abs(applied) > abs(offset):
                fail(f"amplitude-safe colour application failed for {color=} {offset=}")
    if abs(delta_e00((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485)) - 2.0425) > 0.0001:
        fail("CIEDE2000 implementation fails the published Sharma reference pair")
    zero_fixture = ParsedBlock(
        province_words=(0x8001,),
        root=Node(0, 0, 32, owner=0, color=17),
        tree_padding=(),
        owner_padding=(),
        color_padding=(),
        original_leaf_count=1,
    )
    zero_stats = ChangeStats()
    transform_block(zero_fixture, 1, 0, 0, {1: "Plains"}, motifs, zero_stats, zero_motif=True)
    zero_reparsed = parse_block(encode_block(zero_fixture, preserve_padding=False))
    zero_owners, zero_colors = raster_block(zero_reparsed)
    if set(zero_owners) != {0} or set(zero_colors) != {17}:
        fail("zero-motif structural fixture changed ownership or a raster colour")
    if zero_stats.ordinary_land_pixels["Plains"] != 1024 or zero_stats.modified_pixels["Plains"] != 0:
        fail("zero-motif structural fixture does not use the all-land denominator or reports a colour change")
    if sum(1 for _ in iter_leaves(zero_reparsed.root)) <= 1:
        fail("zero-motif fixture did not exercise structural refinement")
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

    compiler_source = (root / "tools/aubm_lightmap.py").read_text(encoding="utf-8")
    if 'set(motifs["terrain_color_anchors"])' in compiler_source or '"eligible_pixels"' in compiler_source:
        fail("the compiler still contains the Alpha 26 eligible-anchor denominator")
    for required in (
        "ordinary_land_pixels",
        "modified_coverage_percent_all_land",
        "marked_median_delta_e76",
        "marked_median_delta_e00",
        "delta_e00_ge_2_percent_all_land",
        "offline truncating native LUT + CIEDE2000",
        "actual_engine_human_visibility_gate",
    ):
        if required not in compiler_source:
            fail(f"terrain compiler is missing the native/all-land contract: {required}")

    native_regression: dict[str, object]
    if args.colorscales:
        colorscale_path = Path(args.colorscales).resolve()
        colour_name = str(motifs["gates"]["native_country_colour"])
        scales = load_colorscales(colorscale_path)
        lut = named_colorscale(scales, colour_name)
        map_colours_path = (
            Path(args.map_colors).resolve()
            if args.map_colors
            else colorscale_path.parents[2] / "Modding documentation" / "Map colors.txt"
        )
        terrain_names = load_terrain_colour_reference(map_colours_path)
        weather_names = load_weather_colour_reference(map_colours_path)
        if terrain_names != motifs["native_terrain_colour_by_terrain"]:
            fail("recipe terrain colours differ from the authoritative Map colors.txt")
        if weather_names != motifs["native_weather_colour_by_state"]:
            fail("recipe weather colours differ from the authoritative Map colors.txt")
        terrain_luts = {terrain: named_colorscale(scales, terrain_names[terrain]) for terrain in TERRAINS}
        snow_lut = named_colorscale(scales, weather_names["Snow"])
        mud_lut = named_colorscale(scales, weather_names["Mud"])
        # Model Alpha 26's measured 84.33% unchanged all-land result with its
        # former low amplitudes.  The gate must reject it on both density and
        # native contrast when evaluated through the real supplied DarkBlue LUT.
        alpha26_amplitudes = {
            "Plains": 1,
            "Forest": 3,
            "Mountain": 4,
            "Desert": 2,
            "Marsh": 2,
            "Hills": 2,
            "Jungle": 3,
            "Urban": 2,
        }
        alpha26_pairs = {terrain: Counter({(24, 24): 8433}) for terrain in TERRAINS}
        for terrain, amplitude in alpha26_amplitudes.items():
            alpha26_pairs[terrain][(24, 24 + amplitude)] += 784
            alpha26_pairs[terrain][(24, 24 - amplitude)] += 783
        alpha26_political = native_perceptual_metrics(alpha26_pairs, lut)
        alpha26_terrain = native_perceptual_metrics(alpha26_pairs, terrain_luts)
        alpha26_snow = native_perceptual_metrics(alpha26_pairs, snow_lut)
        alpha26_mud = native_perceptual_metrics(alpha26_pairs, mud_lut)
        rejected = False
        try:
            enforce_compiled_gates(
                2,
                alpha26_political,
                alpha26_terrain,
                alpha26_snow,
                alpha26_mud,
                motifs,
            )
        except LightmapError:
            rejected = True
        if not rejected:
            fail("the corrected native/all-land gates would accept the measured Alpha 26 failure profile")
        cap_evidence: dict[str, dict] = {}
        for terrain in TERRAINS:
            centre = rgb_to_lab(terrain_luts[terrain][24])
            negative = rgb_to_lab(terrain_luts[terrain][14])
            positive = rgb_to_lab(terrain_luts[terrain][34])
            cap_evidence[terrain] = {
                "scale": terrain_names[terrain],
                "negative_delta_e00": round(delta_e00(centre, negative), 4),
                "negative_delta_e76": round(delta_e76(centre, negative), 4),
                "positive_delta_e00": round(delta_e00(centre, positive), 4),
                "positive_delta_e76": round(delta_e76(centre, positive), 4),
            }
        native_regression = {
            "status": "passed",
            "colorscales": str(colorscale_path),
            "colorscales_sha256": sha256_file(colorscale_path),
            "map_colors": str(map_colours_path),
            "map_colors_sha256": sha256_file(map_colours_path),
            "country_colour": colour_name,
            "alpha26_failure_profile_rejected": True,
            "alpha26_profile": {
                "political": alpha26_political,
                "terrain": alpha26_terrain,
                "snow": alpha26_snow,
                "mud": alpha26_mud,
            },
            "technical_cap_evidence_shade_24_signed_10": cap_evidence,
        }
    else:
        native_regression = {
            "status": "deferred",
            "reason": "supply --colorscales for the native LUT regression; build/compare always use SOURCE-DIR/colorscales.csv",
        }

    report = {
        "status": "passed",
        "mechanical_land_terrains": list(TERRAINS),
        "province_counts": {terrain: counts[terrain] for terrain in TERRAINS},
        "lightmap_dimensions_blocks": {str(level): list(size) for level, size in SPECS.items()},
        "motif_sha256": sha256_file(motif_path),
        "atlas_sha256": sha256_file(atlas_path),
        "moodboard_sha256": sha256_file(moodboard_path),
        "motif_gates": metrics["gates"],
        "all_land_denominator": "every ordinary pixel assigned to one of the eight mechanical land terrains",
        "native_perceptual_regression": native_regression,
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
