#!/usr/bin/env python3
"""Install India's dedicated pale-jade political-map ramp into the local prototype."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from stamp_aubm_visible_version import badge_matches, write_badge


REPO = Path(__file__).resolve().parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game")
TARGET = GAME / "Mods/AUBM Terrain Prototype P1"
BASE_PALETTE = GAME / "map/Map_1/colorscales.csv"
BUILD = "CANDIDATE-5-JADE1"
FORMER_USERS = ("HAI", "KUR", "NAM", "SYR", "U03", "U04", "U23", "U29", "U46")
JADE = (
    "UserColor2;;;",
    "red;green;blue;index",
    "169;205;182;0",   # #A9CDB6: pale-jade highlight
    "144;179;157;20",  # darker ordinary-map body
    "116;150;130;40",  # relief and clicked-state separation
    "1;1;1;64",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def palette_bytes(source: bytes) -> bytes:
    text = source.decode("cp1252")
    replacement = newline(text).join(JADE) + newline(text)
    pattern = re.compile(
        r"(?m)^UserColor2;;;\r?\nred;green;blue;index\r?\n"
        r"(?:[^\r\n]*\r?\n){4}"
    )
    result, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError("Could not locate the native UserColor2 ramp")
    return result.encode("cp1252")


def country_bytes(source: bytes) -> bytes:
    text = source.decode("cp1252")
    for tag in FORMER_USERS:
        text, count = re.subn(
            rf"(?m)^{tag};(?:UserColor2|LightBlue);",
            f"{tag};LightBlue;",
            text,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Could not isolate former UserColor2 country {tag}")
    text, count = re.subn(
        r"(?m)^IND;(?:Gray|DarkBlue|UserColor2);",
        "IND;UserColor2;",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not isolate India's display colour")
    users = re.findall(r"(?m)^([A-Z0-9]{3});UserColor2;", text)
    if users != ["IND"]:
        raise ValueError(f"Pale jade is not exclusive to India: {users}")
    return text.encode("cp1252")


def scenario_bytes(source: bytes) -> bytes:
    text = source.decode("cp1252")
    pattern = re.compile(
        r'(?m)^(\{ name\s*=\s*")India 1933 - AUBM Candidate 5(?: Jade 1)? \[UNVERIFIED\](")'
    )
    result, count = pattern.subn(r'\1India 1933 - AUBM Candidate 5 Jade 1 [UNVERIFIED]\2', text, count=1)
    if count != 1:
        raise ValueError("Could not identify the Candidate 5 scenario title")
    return result.encode("cp1252")


def main() -> None:
    if not TARGET.is_dir() or not BASE_PALETTE.is_file():
        raise SystemExit("Expected Darkest Hour prototype installation was not found")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = REPO / "build/visual/pale-jade-1" / f"install-backup-{stamp}"
    backup.mkdir(parents=True)
    country = TARGET / "db/country.csv"
    palette = TARGET / "map/Map_1/colorscales.csv"
    scenario = TARGET / "scenarios/1933.eug"
    screens = (TARGET / "gfx/load_1024.bmp", TARGET / "gfx/interface/frontend/bg_start.bmp")
    sources = {
        country: country.read_bytes(),
        palette: palette.read_bytes() if palette.exists() else BASE_PALETTE.read_bytes(),
        scenario: scenario.read_bytes(),
        **{screen: screen.read_bytes() for screen in screens},
    }
    for path, data in sources.items():
        relative = path.relative_to(TARGET)
        saved = backup / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(data)
    country.write_bytes(country_bytes(sources[country]))
    palette.parent.mkdir(parents=True, exist_ok=True)
    palette.write_bytes(palette_bytes(sources[palette]))
    scenario.write_bytes(scenario_bytes(sources[scenario]))
    for screen in screens:
        write_badge(screen, BUILD)
        if not badge_matches(screen, BUILD):
            raise ValueError(f"Visible build badge verification failed: {screen}")
    running = '"Darkest Hour.exe"' in subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq Darkest Hour.exe", "/FO", "CSV", "/NH"],
        check=True,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    ).stdout
    receipt = {
        "build": BUILD,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "india_color": "UserColor2",
        "ramp": list(JADE[2:]),
        "exclusive_usercolor2": True,
        "terrain_lightmaps_changed": False,
        "restart_required": True,
        "game_was_running_during_install": running,
        "backup": str(backup),
        "installed_sha256": {
            str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
            for path in (country, palette, scenario, *screens)
        },
    }
    (TARGET / "AUBM_VISUAL_OVERRIDE.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    (backup / "INSTALL_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
