#!/usr/bin/env python3
"""Focused static contract tests for the additive Delhi-Berlin compact."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "mod" / "db" / "events" / "aubm_v4" / "52_delhi_berlin_compact.txt"
REGISTRY = ROOT / "mod" / "db" / "events.txt"
ID_MIN, ID_MAX = 9281600, 9281699


def blocks(text: str) -> list[str]:
    starts = [m.start() for m in re.finditer(r"(?m)^event\s*=\s*\{", text)]
    result: list[str] = []
    for start in starts:
        depth = 0
        quoted = False
        escaped = False
        for pos in range(start, len(text)):
            char = text[pos]
            if escaped:
                escaped = False
                continue
            if char == "\\" and quoted:
                escaped = True
            elif char == '"':
                quoted = not quoted
            elif not quoted and char == "{":
                depth += 1
            elif not quoted and char == "}":
                depth -= 1
                if depth == 0:
                    result.append(text[start : pos + 1])
                    break
        else:
            raise AssertionError(f"Unclosed event beginning at byte {start}")
    return result


def event_id(block: str) -> int:
    match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
    assert match
    return int(match.group(1))


def validate_live(live_root: Path) -> None:
    live_event = live_root / "db" / "events" / "aubm_v4" / EVENTS.name
    assert live_event.is_file(), f"live compact missing: {live_event}"
    assert hashlib.sha256(live_event.read_bytes()).digest() == hashlib.sha256(EVENTS.read_bytes()).digest()

    registry_path = live_root / "db" / "events.txt"
    registry = registry_path.read_text(encoding="latin-1")
    entries = re.findall(r'(?m)^\s*event\s*=\s*"([^"]+)"', registry)
    assert entries.count(r"db\events\aubm_v4\52_delhi_berlin_compact.txt") == 1
    seen: dict[int, Path] = {}
    for entry in entries:
        path = live_root / Path(entry.replace("\\", "/"))
        assert path.is_file(), f"registered event file missing: {path}"
        for raw in re.findall(r"(?m)^\s*id\s*=\s*(\d+)\s*$", path.read_text(encoding="latin-1", errors="replace")):
            value = int(raw)
            assert value not in seen, f"live duplicate event {value}: {seen[value]} and {path}"
            seen[value] = path

    for name in (
        "aubm_ger_compact_signing.bmp", "aubm_ger_machines_for_ore.bmp",
        "aubm_ger_monsoon_armour.bmp", "aubm_ger_three_capitals.bmp",
        "aubm_ger_caucasus_lifeline.bmp", "aubm_ger_suez_road.bmp",
        "aubm_ger_independent_command.bmp",
    ):
        picture = live_root / "gfx" / "events_pics" / name
        assert picture.is_file() and picture.stat().st_size == 139254, f"bad live picture: {picture}"

    assert "28-GERCOMPACT1" in (live_root / "scenarios" / "1933.eug").read_text(encoding="latin-1")
    assert "28-GERCOMPACT1" in (live_root / "db" / "events" / "india_v3" / "00_bootstrap.txt").read_text(encoding="latin-1")
    assert "PLAY 28-GERCOMPACT1" in (live_root / "config" / "text.csv").read_text(encoding="latin-1")
    print(f"PASS: live registry has {len(seen)} unique events and 7 compact pictures")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-root", type=Path)
    args = parser.parse_args()
    text = EVENTS.read_text(encoding="utf-8-sig")
    assert text.count("{") == text.count("}"), "unbalanced braces"
    parsed = blocks(text)
    ids = [event_id(block) for block in parsed]
    assert len(ids) >= 45, f"compact is too thin: only {len(ids)} events"
    assert len(ids) == len(set(ids)), "duplicate event id inside compact"
    assert all(ID_MIN <= value <= ID_MAX for value in ids), "event outside reserved block"

    registry = REGISTRY.read_text(encoding="utf-8-sig")
    assert registry.count('event = "db\\events\\aubm_v4\\52_delhi_berlin_compact.txt"') == 1

    all_source = "\n".join(
        path.read_text(encoding="utf-8-sig", errors="replace")
        for path in (ROOT / "mod" / "db" / "events").rglob("*.txt")
        if path != EVENTS
    )
    for value in ids:
        assert not re.search(rf"(?m)^\s*id\s*=\s*{value}\s*$", all_source), f"event {value} collides"

    callback_ids = {int(value) for value in re.findall(r"type\s*=\s*event\s+which\s*=\s*(\d+)", text)}
    local_callbacks = {value for value in callback_ids if ID_MIN <= value <= ID_MAX}
    assert local_callbacks <= set(ids), f"missing local callbacks: {sorted(local_callbacks - set(ids))}"

    forbidden = ("type = peace", "type = puppet", "type = inherit", "type = secedeprovince", "type = independence")
    lower = text.lower()
    for token in forbidden:
        assert token not in lower, f"compact must not own settlements: {token}"

    for value in (9281605, 9281606):
        block = next(item for item in parsed if event_id(item) == value)
        assert "type = alliance" not in block and "type = war" not in block, f"{value} breaks separate command"

    docket_targets = {9281634: "ENG", 9281635: "SOV", 9281636: "USA", 9281637: "JAP"}
    for value, target in docket_targets.items():
        block = next(item for item in parsed if event_id(item) == value)
        assert 'name = "Cancel' in block, f"{value} has no safe cancel"
        wars = re.findall(r"type\s*=\s*war\s+which\s*=\s*(\w+)", block)
        assert wars == [target], f"{value} must declare only {target}; got {wars}"
        assert "type = alliance" not in block, f"{value} silently forms an alliance"

    for suffix in ("eng", "sov", "usa"):
        assert f"ind_db_crisis_{suffix}_seen" in text, f"missing target crisis state for {suffix}"

    assert "type = sleepevent which = 9281300" in text, "legacy war conference is not suppressed"
    print(f"PASS: {len(ids)} Delhi-Berlin events; separate-war and settlement invariants hold")
    if args.live_root:
        validate_live(args.live_root)


if __name__ == "__main__":
    main()
