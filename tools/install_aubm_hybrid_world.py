#!/usr/bin/env python3
"""Install a verified local world build ONLY into the existing isolated prototype.

The normal mod, saves, launcher selection and public repository payload are never
changed. Every replaced test file is backed up, and the original is re-hashed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import aubm_hybrid_terrain as hybrid
from aubm_hybrid_world import BUILD
from aubm_lightmap import sha256_file
from stamp_aubm_visible_version import (badge_matches, scenario_title_matches,
                                      set_scenario_title, write_badge)

NORMAL = hybrid.GAME / "Mods/A Union Before Midnight V4.2"
TEST = hybrid.GAME / "Mods/AUBM Terrain Prototype P1"
FULL = hybrid.GAME / "Mods/Darkest Hour Full"


def gameplay(root):
    found = {}
    for directory in ("ai", "config", "db", "scenarios", "map"):
        for path in (root / directory).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative.startswith("scenarios/save games/"):
                continue
            if directory == "map" and path.name in {f"lightmap{i}.tbl" for i in range(1, 5)}:
                continue
            if directory == "map" and "gfx" in path.relative_to(root).parts:
                continue
            found[relative] = sha256_file(path)
    return found


def differences():
    normal, test = gameplay(NORMAL), gameplay(TEST)
    changed = [name for name in sorted(normal.keys() | test.keys()) if normal.get(name) != test.get(name)]
    unexpected = set(changed) - {"db/country.csv", "scenarios/1933.eug"}
    if unexpected:
        raise ValueError(f"Unrelated gameplay differences: {sorted(unexpected)}")
    a = (NORMAL / "db/country.csv").read_bytes()
    b = (TEST / "db/country.csv").read_bytes()
    if a.replace(b"IND;DarkBlue;", b"IND;Gray;").splitlines() != b.splitlines():
        raise ValueError("Country database differs by more than India's display colour")
    import re
    pattern = rb'(A Union Before Midnight: India 1933)(?: \[[^"\r\n]+\])?'
    a = re.sub(pattern, rb'\1', (NORMAL / "scenarios/1933.eug").read_bytes())
    b = re.sub(pattern, rb'\1', (TEST / "scenarios/1933.eug").read_bytes())
    if a != b:
        raise ValueError("Scenario differs by more than its visible build title")
    return {"files_compared": len(normal), "allowed_display_only_differences": changed}


def protected_snapshot():
    snapshot = gameplay(NORMAL)
    for relative in ("gfx/load_1024.bmp", "gfx/interface/frontend/bg_start.bmp",
                     "gfx/map/airfield.bmp", "gfx/map/harbour.bmp",
                     *(f"map/Map_1/lightmap{i}.tbl" for i in range(1, 5))):
        path = NORMAL / relative
        if path.exists():
            snapshot[relative] = sha256_file(path)
    for path in (NORMAL / "scenarios/save games").rglob("*"):
        if path.is_file():
            snapshot[path.relative_to(NORMAL).as_posix()] = sha256_file(path)
    snapshot["EXTERNAL/settings.cfg"] = sha256_file(hybrid.GAME / "settings.cfg")
    return snapshot


def install(source, backup):
    source, backup = source.resolve(), backup.resolve()
    local_tmp = (hybrid.REPO / "tmp").resolve()
    if not source.is_relative_to(local_tmp) or not backup.is_relative_to(local_tmp):
        raise ValueError("Source and backups must be in this repository's ignored tmp directory")
    if backup.exists():
        raise ValueError("Use a fresh backup directory")
    running = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Darkest Hour.exe", "/FO", "CSV", "/NH"],
                             check=True, capture_output=True, text=True,
                             creationflags=subprocess.CREATE_NO_WINDOW).stdout
    if '"Darkest Hour.exe"' in running:
        raise ValueError("Exit the game yourself before installation; no process will be controlled")
    receipt = json.loads((source / "HYBRID_WORLD.json").read_text(encoding="utf-8"))
    if receipt.get("build") != BUILD or set(receipt["levels"]) != {"1", "2", "3", "4"}:
        raise ValueError("Incomplete or wrong world build")
    for level, info in receipt["levels"].items():
        if not info.get("all_written_blocks_verified") or not info.get("geometry_and_render_roundtrip"):
            raise ValueError(f"Unverified L{level}")
        if sha256_file(source / f"lightmap{level}.tbl") != info["sha256"]:
            raise ValueError(f"Staging L{level} does not match its validation receipt")
    for path, expected in receipt["input_sha256"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"Source input changed since compilation: {path}")
    audit = differences()
    before = protected_snapshot()
    save = "scenarios/save games/autosave.eug"
    if sha256_file(TEST / save) != sha256_file(NORMAL / save):
        raise ValueError("Prototype autosave is not the original copy; do not overwrite it")
    replaced = [*(f"map/Map_1/lightmap{i}.tbl" for i in range(1, 5)),
                "gfx/load_1024.bmp", "gfx/interface/frontend/bg_start.bmp",
                "gfx/map/airfield.bmp", "gfx/map/harbour.bmp", "scenarios/1933.eug",
                "HYBRID_PROTOTYPE.json"]
    backup.mkdir(parents=True)
    (backup / "original-install-before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    backup_hashes = {}
    for relative in replaced:
        path = TEST / relative
        if path.exists():
            copy = backup / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, copy)
            backup_hashes[relative] = sha256_file(copy)
            assert backup_hashes[relative] == sha256_file(path)
    # No game process is started or controlled by this installer.
    for level in range(1, 5):
        shutil.copy2(source / f"lightmap{level}.tbl", TEST / f"map/Map_1/lightmap{level}.tbl")
    for name in ("airfield.bmp", "harbour.bmp"):
        shutil.copy2(FULL / "gfx/map" / name, TEST / "gfx/map" / name)
    for relative in ("gfx/load_1024.bmp", "gfx/interface/frontend/bg_start.bmp"):
        write_badge(TEST / relative, BUILD)
        assert badge_matches(TEST / relative, BUILD)
    set_scenario_title(TEST / "scenarios/1933.eug", BUILD)
    assert scenario_title_matches(TEST / "scenarios/1933.eug", BUILD)
    for level, info in receipt["levels"].items():
        assert sha256_file(TEST / f"map/Map_1/lightmap{level}.tbl") == info["sha256"]
    after = protected_snapshot()
    if after != before:
        raise ValueError("Protected original files changed during installation; investigate before use")
    post_audit = differences()
    receipt["installation"] = {
        "path": str(TEST), "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "visible_badge": BUILD, "india_color": "Gray", "facility_icons": "Darkest Hour Full originals",
        "backup": str(backup), "backup_sha256": backup_hashes,
        "original_and_launcher_unchanged": True, "protected_files_checked": len(before),
        "gameplay_audit_before": audit, "gameplay_audit_after": post_audit,
        "autosave_sha256": sha256_file(TEST / save),
        "engine_playtested": False, "new_campaign_required_for_visuals": False,
    }
    payload = json.dumps(receipt, indent=2)
    (TEST / "HYBRID_PROTOTYPE.json").write_text(payload, encoding="utf-8")
    (backup / "INSTALL_RECEIPT.json").write_text(payload, encoding="utf-8")
    print(json.dumps(receipt["installation"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    if args.audit_only:
        print(json.dumps(differences(), indent=2))
    elif not args.source or not args.backup:
        parser.error("--source and --backup are required for installation")
    else:
        install(args.source, args.backup)


if __name__ == "__main__":
    main()
