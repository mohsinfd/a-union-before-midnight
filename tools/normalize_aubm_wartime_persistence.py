#!/usr/bin/env python3
"""Keep reusable AUBM wartime events explicitly persistent.

Darkest Hour events are one-shot unless ``persistent = yes`` is present.  The
lists below contain only menus, recurring lifecycle detectors, callbacks and
cooldown-protected helpers.  Permanent milestones and legacy terminal events
are intentionally excluded.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_ROOT = ROOT / "mod/db/events/aubm_v4"

SAFE_IDS = {
    "42_wartime_theatres.txt": {
        *range(9281930, 9281934),
        *range(9281950, 9281956),
        *range(9281980, 9281983),
    },
    "43_wartime_settlements.txt": {
		*range(9282000, 9282009),
		*range(9282020, 9282046),
        *range(9282050, 9282055),
        9282059,
    },
    "44_wartime_economy.txt": {*range(9282080, 9282094)},
    "45_enemy_campaigns.txt": {
        *range(9282120, 9282126),
        *range(9282130, 9282136),
        *range(9282137, 9282152),
        *range(9282160, 9282167),
        9282169,
        *range(9282170, 9282176),
        *range(9282180, 9282190),
    },
    "46_regional_campaigns.txt": {
		*range(9282200, 9282206),
		*range(9282210, 9282230),
        *range(9282260, 9282267),
    },
}


def event_spans(text: str) -> list[tuple[int, int, int]]:
    spans: list[tuple[int, int, int]] = []
    for match in re.finditer(r"(?m)^\s*event\s*=\s*\{", text):
        opening = text.find("{", match.start())
        depth = 0
        quoted = False
        escaped = False
        for pos in range(opening, len(text)):
            char = text[pos]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    block = text[match.start() : pos + 1]
                    event_id = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
                    if event_id:
                        spans.append((match.start(), pos + 1, int(event_id.group(1))))
                    break
    return spans


def normalize(text: str, safe_ids: set[int]) -> str:
    replacements: list[tuple[int, int, str]] = []
    found: set[int] = set()
    for start, end, event_id in event_spans(text):
        if event_id not in safe_ids:
            continue
        found.add(event_id)
        block = text[start:end]
        if re.search(r"(?m)^\s*persistent\s*=\s*yes\s*$", block):
            continue
        updated, count = re.subn(
            r"(?m)^(\s*random\s*=\s*no\s*)$",
            r"\1\n\tpersistent = yes",
            block,
            count=1,
        )
        if count != 1:
            raise ValueError(f"event {event_id} has no unique random = no line")
        replacements.append((start, end, updated))
    missing = safe_ids - found
    if missing:
        raise ValueError(f"missing expected events: {sorted(missing)}")
    for start, end, updated in reversed(replacements):
        text = text[:start] + updated + text[end:]
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for name, safe_ids in SAFE_IDS.items():
        path = EVENT_ROOT / name
        original = path.read_text(encoding="cp1252")
        updated = normalize(original, safe_ids)
        if original == updated:
            continue
        if args.check:
            stale.append(name)
        else:
            path.write_text(updated, encoding="cp1252", newline="\n")
            print(f"UPDATED: {name}")
    if stale:
        for name in stale:
            print(f"STALE: {name}")
        return 1
    print("OK: reusable wartime events are explicitly persistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
