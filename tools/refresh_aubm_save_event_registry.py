#!/usr/bin/env python3
"""Clone an old AUBM save with the currently active India event registry.

Darkest Hour serializes the event-file list into every save.  Adding or
retiring a module in db/events.txt therefore does not affect an older save.
This tool changes only the cloned save's display name, option-file reference
and contiguous india_v3/aubm_v4 event registry.  Campaign state is untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import parse, replace


ROOT = Path(__file__).resolve().parents[1]
EVENT_INDEX = ROOT / "mod/db/events.txt"
MOD_PREFIXES = ('event = "db\\events\\india_v3\\', 'event = "db\\events\\aubm_v4\\')
REGISTRY_PATTERN = re.compile(
    rb'^event = "db\\events\\(?:india_v3|aubm_v4)\\[^"\r\n]+"[ \t]*\r?\n(?:\r?\n)?',
    re.MULTILINE,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active_registry() -> list[str]:
    lines = EVENT_INDEX.read_text(encoding="cp1252").splitlines()
    active = [line.strip() for line in lines if line.strip().startswith(MOD_PREFIXES)]
    if not active:
        raise ValueError("No active AUBM event modules found in mod/db/events.txt")
    required = {
        'event = "db\\events\\india_v3\\60_postwar.txt"',
        'event = "db\\events\\aubm_v4\\53_country_resolutions.txt"',
        'event = "db\\events\\aubm_v4\\54_country_relations.txt"',
    }
    missing = sorted(required - set(active))
    if missing:
        raise ValueError(f"Active registry lacks required Alpha 31 modules: {missing}")
    return active


def refresh(raw: bytes, output_name: str) -> tuple[bytes, dict[str, object]]:
    matches = list(REGISTRY_PATTERN.finditer(raw))
    if not matches:
        raise ValueError("Save contains no serialized AUBM event registry")
    old_lines = [match.group(0).decode("cp1252").strip() for match in matches]
    active = active_registry()
    newline = b"\r\n" if b"\r\n" in raw[:4096] else b"\n"
    registry = b"".join(line.encode("cp1252") + b" " + newline + newline for line in active)

    root = parse(raw)
    header = root.get("header")
    display = header.field("name")
    optionfile = header.field("optionfile")
    if display is None or optionfile is None:
        raise ValueError("Save header lacks name or optionfile")

    label = f"ALPHA 31 COUNTRY FIX - India 1 May 1942"
    option = f'"scenarios\\save games\\{output_name}.cfg"'
    edits = [
        (matches[0].start(), matches[-1].end(), registry),
        (display.value_start, display.end, f'"{label}"'.encode("cp1252")),
        (optionfile.value_start, optionfile.end, option.encode("cp1252")),
    ]
    updated = replace(raw, edits)

    reparsed = parse(updated)
    if reparsed.get("header").get("name") != label:
        raise AssertionError("Updated display name did not parse")
    new_matches = list(REGISTRY_PATTERN.finditer(updated))
    new_lines = [match.group(0).decode("cp1252").strip() for match in new_matches]
    if new_lines != active:
        raise AssertionError("Serialized event registry does not match the active build")
    if b"53_country_resolutions.txt" not in updated or b"54_country_relations.txt" not in updated:
        raise AssertionError("Country modules are absent after refresh")

    report = {
        "old_module_count": len(old_lines),
        "new_module_count": len(new_lines),
        "added_modules": sorted(set(new_lines) - set(old_lines)),
        "removed_modules": sorted(set(old_lines) - set(new_lines)),
        "campaign_state_changed": False,
        "changed_fields": ["header.name", "header.optionfile", "event_file_registry"],
    }
    return updated, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if source == output:
        raise ValueError("Output must be a new save; the source is never overwritten")
    if output.exists():
        raise FileExistsError(output)
    if output.suffix.lower() != ".eug":
        raise ValueError("Output must use the .eug extension")

    original = source.read_bytes()
    updated, report = refresh(original, output.name)
    if source.read_bytes() != original:
        raise RuntimeError("Source save changed during migration")

    output.write_bytes(updated)
    source_cfg = source.with_suffix(source.suffix + ".cfg")
    output_cfg = output.with_suffix(output.suffix + ".cfg")
    if source_cfg.is_file():
        shutil.copy2(source_cfg, output_cfg)
    if output.read_bytes() != updated or source.read_bytes() != original:
        raise RuntimeError("Post-write verification failed")

    report.update(
        {
            "play_this": str(output),
            "source_unchanged": str(source),
            "source_sha256": digest(original),
            "output_sha256": digest(updated),
            "config_copied": output_cfg.is_file(),
        }
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
