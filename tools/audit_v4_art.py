#!/usr/bin/env python3
"""Audit A Union Before Midnight's Darkest Hour artwork and provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import pathlib
import re
import struct
import sys
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD = ROOT / "mod"
EVENT_DIRS = (
    MOD / "db/events/india_v3",
    MOD / "db/events/aubm_v4",
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bmp_info(path: pathlib.Path) -> tuple[int, int, int]:
    data = path.read_bytes()[:30]
    if len(data) < 30 or data[:2] != b"BM":
        raise ValueError("not a Windows BMP")
    width, height = struct.unpack_from("<ii", data, 18)
    bits = struct.unpack_from("<H", data, 28)[0]
    return width, abs(height), bits


def event_picture_references() -> list[tuple[pathlib.Path, int, str]]:
    references: list[tuple[pathlib.Path, int, str]] = []
    pattern = re.compile(r'(?m)^\s*picture\s*=\s*"([^"]+)"')
    for event_dir in EVENT_DIRS:
        for path in sorted(event_dir.glob("*.txt")):
            text = path.read_text(encoding="cp1252")
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                references.append((path, line, match.group(1)))
    return references


def custom_personnel_references() -> dict[str, set[str]]:
    references: dict[str, set[str]] = {
        "leaders": set(),
        "ministers": set(),
        "teams": set(),
    }
    with (MOD / "db/leaders/india.csv").open(encoding="cp1252", newline="") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            picture = (row.get("Picture") or "").strip()
            if picture.startswith("INDL"):
                references["leaders"].add(picture)

    with (MOD / "db/ministers/ministers_ind.csv").open(
        encoding="cp1252",
        newline="",
    ) as stream:
        for row in csv.reader(stream, delimiter=";"):
            if len(row) > 9 and row[0].isdigit() and row[9].startswith("INDM_"):
                references["ministers"].add(row[9])

    with (MOD / "db/tech/teams/teams_ind.csv").open(
        encoding="cp1252",
        newline="",
    ) as stream:
        for row in csv.reader(stream, delimiter=";"):
            if len(row) > 2 and row[0].isdigit() and row[2].startswith("TT"):
                references["teams"].add(row[2])
    return references


def duplicate_groups(paths: list[pathlib.Path]) -> list[list[pathlib.Path]]:
    groups: dict[str, list[pathlib.Path]] = defaultdict(list)
    for path in paths:
        groups[sha256(path)].append(path)
    return [group for group in groups.values() if len(group) > 1]


def art_manifest_issues() -> list[str]:
    path = ROOT / "docs/art_manifest.csv"
    if not path.is_file():
        return ["docs/art_manifest.csv is missing"]
    issues: list[str] = []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            rows.append(row)
            output = (row.get("output") or "").replace("\\", "/")
            source = re.sub(r"#panel=\d+$", "", row.get("source") or "")
            expected = (row.get("sha256") or "").lower()
            if not output:
                issues.append(f"line {line}: missing output path")
                continue
            asset = MOD / output
            if not asset.is_file():
                issues.append(f"line {line}: missing {output}")
            elif expected and sha256(asset) != expected:
                issues.append(f"line {line}: stale hash for {output}")
            if not source:
                issues.append(f"line {line}: missing source path")
            elif not (ROOT / source).is_file():
                issues.append(f"line {line}: missing source {source}")

    assets = [row.get("asset") or "" for row in rows]
    outputs = [row.get("output") or "" for row in rows]
    if len(assets) != len(set(assets)):
        issues.append("docs/art_manifest.csv contains duplicate asset rows")
    if len(outputs) != len(set(outputs)):
        issues.append("docs/art_manifest.csv contains duplicate output rows")

    kinds = Counter(row.get("kind") or "" for row in rows)
    if kinds != Counter(
        {"event": 102, "tech_team": 31, "loading_screen": 1, "frontend": 1}
    ):
        issues.append(f"unexpected art-manifest kind counts: {dict(kinds)}")

    loading_rows = [row for row in rows if row.get("kind") == "loading_screen"]
    if len(loading_rows) == 1:
        loading_output = (loading_rows[0].get("output") or "").replace("\\", "/")
        loading_path = MOD / loading_output
        if loading_output != "gfx/load_1024.bmp":
            issues.append(f"unexpected loading-screen output: {loading_output}")
        elif loading_path.is_file():
            dimensions = bmp_info(loading_path)
            if dimensions != (1024, 768, 24):
                issues.append(
                    "gfx/load_1024.bmp must be a 1024x768 24-bit BMP, got "
                    f"{dimensions[0]}x{dimensions[1]} {dimensions[2]}-bit"
                )

    frontend_rows = [row for row in rows if row.get("kind") == "frontend"]
    if len(frontend_rows) == 1:
        frontend_output = (frontend_rows[0].get("output") or "").replace("\\", "/")
        frontend_path = MOD / frontend_output
        if frontend_output != "gfx/interface/frontend/bg_start.bmp":
            issues.append(f"unexpected frontend output: {frontend_output}")
        elif frontend_path.is_file():
            dimensions = bmp_info(frontend_path)
            if dimensions != (1024, 768, 24):
                issues.append(
                    "gfx/interface/frontend/bg_start.bmp must be a 1024x768 "
                    f"24-bit BMP, got {dimensions[0]}x{dimensions[1]} "
                    f"{dimensions[2]}-bit"
                )

    referenced_custom = {
        name
        for _, _, name in event_picture_references()
        if (MOD / "gfx/events_pics" / f"{name}.bmp").is_file()
    }
    manifest_events = {
        row.get("asset") or "" for row in rows if row.get("kind") == "event"
    }
    if referenced_custom != manifest_events:
        issues.append(
            "event-art manifest coverage mismatch: "
            f"unmapped={sorted(referenced_custom - manifest_events)}, "
            f"stale={sorted(manifest_events - referenced_custom)}"
        )
    return issues


def v4_manifest_issues() -> list[str]:
    path = ROOT / "docs/v4_event_art_manifest.csv"
    if not path.is_file():
        return ["docs/v4_event_art_manifest.csv is missing"]

    catalog: dict[int, tuple[str, str]] = {}
    event_pattern = re.compile(r"(?m)^event\s*=\s*\{")
    id_pattern = re.compile(r"(?m)^\s*id\s*=\s*(928\d+)\s*$")
    name_pattern = re.compile(r'(?m)^\s*name\s*=\s*"([^"]+)"\s*$')
    picture_pattern = re.compile(r'(?m)^\s*picture\s*=\s*"([^"]+)"\s*$')
    for event_file in sorted((MOD / "db/events/aubm_v4").glob("*.txt")):
        text = event_file.read_text(encoding="cp1252")
        starts = [match.start() for match in event_pattern.finditer(text)] + [len(text)]
        for start, end in zip(starts, starts[1:], strict=False):
            block = text[start:end]
            event_id = id_pattern.search(block)
            title = name_pattern.search(block)
            picture = picture_pattern.search(block)
            if event_id and title and picture:
                catalog[int(event_id.group(1))] = (title.group(1), picture.group(1))

    issues: list[str] = []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows.extend(csv.DictReader(stream))
    if len(rows) != len(catalog):
        issues.append(
            f"expected {len(catalog)} V4 event-art rows, found {len(rows)}"
        )

    ids: list[int] = []
    assets: list[str] = []
    for line, row in enumerate(rows, 2):
        try:
            event_id = int(row.get("event_id") or "")
        except ValueError:
            issues.append(f"V4 manifest line {line}: invalid event id")
            continue
        asset = row.get("asset") or ""
        ids.append(event_id)
        assets.append(asset)
        expected = catalog.get(event_id)
        if expected is None:
            issues.append(f"V4 manifest line {line}: unknown event {event_id}")
        elif expected != (row.get("event_title") or "", asset):
            issues.append(
                f"V4 manifest line {line}: event mapping disagrees with script"
            )
        picture = MOD / "gfx/events_pics" / f"{asset}.bmp"
        if not picture.is_file():
            issues.append(f"V4 manifest line {line}: missing {picture.name}")
        elif sha256(picture) != (row.get("sha256") or "").lower():
            issues.append(f"V4 manifest line {line}: stale hash for {picture.name}")
        source = ROOT / (row.get("source_sheet") or "")
        if not source.is_file():
            issues.append(f"V4 manifest line {line}: missing source sheet {source}")
        if row.get("source_kind") != "generated alternate-history reconstruction":
            issues.append(f"V4 manifest line {line}: invalid source-kind disclosure")
        if "not an archival photograph" not in (row.get("credit") or ""):
            issues.append(f"V4 manifest line {line}: missing reconstruction disclosure")

    if len(ids) != len(set(ids)):
        issues.append("V4 event-art manifest contains duplicate event ids")
    if set(ids) != set(catalog):
        issues.append(
            "V4 event-art event coverage mismatch: "
            f"unmapped={sorted(set(catalog) - set(ids))}, "
            f"stale={sorted(set(ids) - set(catalog))}"
        )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail until every India event has validated custom art and all manifests agree",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    event_root = MOD / "gfx/events_pics"
    stock_root = pathlib.Path(
        r"C:\Program Files (x86)\Steam\steamapps\common"
        r"\Darkest Hour A HOI Game\Mods\Darkest Hour Full\gfx\events_pics"
    )
    references = event_picture_references()
    picture_counts = Counter(name for _, _, name in references)
    custom_event_paths: list[pathlib.Path] = []
    unresolved: list[tuple[pathlib.Path, int, str]] = []
    for source, line, name in references:
        custom = event_root / f"{name}.bmp"
        stock = stock_root / f"{name}.bmp"
        if custom.is_file():
            custom_event_paths.append(custom)
        elif not stock.is_file():
            unresolved.append((source, line, name))

    for source, line, name in unresolved:
        errors.append(f"{source.relative_to(ROOT)}:{line}: unresolved event picture {name}")

    for path in sorted(set(custom_event_paths)):
        try:
            dimensions = bmp_info(path)
        except ValueError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if dimensions != (400, 116, 24):
            errors.append(
                f"{path.relative_to(ROOT)}: expected 400x116 24-bit BMP, got "
                f"{dimensions[0]}x{dimensions[1]} {dimensions[2]}-bit"
            )

    duplicate_events = duplicate_groups(sorted(set(custom_event_paths)))
    for group in sorted(duplicate_events, key=lambda item: -len(item)):
        names = ", ".join(path.stem for path in group)
        warnings.append(f"{len(group)} event-picture names share identical bytes: {names}")

    personnel = custom_personnel_references()
    personnel_paths: list[pathlib.Path] = []
    expected = {
        "leaders": (36, 50, 8),
        "ministers": (36, 50, 8),
        "teams": (96, 96, 8),
    }
    for kind, names in personnel.items():
        for name in sorted(names):
            path = MOD / "gfx/interface/pics" / f"{name}.bmp"
            if not path.is_file():
                errors.append(f"missing {kind} portrait {name}.bmp")
                continue
            personnel_paths.append(path)
            dimensions = bmp_info(path)
            if dimensions != expected[kind]:
                errors.append(
                    f"{path.relative_to(ROOT)}: expected "
                    f"{expected[kind][0]}x{expected[kind][1]} {expected[kind][2]}-bit BMP, "
                    f"got {dimensions[0]}x{dimensions[1]} {dimensions[2]}-bit"
                )

    duplicate_personnel = duplicate_groups(personnel_paths)
    for group in duplicate_personnel:
        errors.append(
            "personnel portraits reuse identical bytes: "
            + ", ".join(path.stem for path in group)
        )

    manifest_issues = art_manifest_issues() + v4_manifest_issues()
    warnings.extend(manifest_issues)

    print("A Union Before Midnight V4 art audit")
    print(f"  Event entries with pictures: {len(references)}")
    print(f"  Unique picture names referenced: {len(picture_counts)}")
    print(f"  Custom event-picture files referenced: {len(set(custom_event_paths))}")
    print(f"  Duplicate custom event-art groups: {len(duplicate_events)}")
    print(
        "  Custom personnel assets: "
        f"{len(personnel['leaders'])} leaders, "
        f"{len(personnel['ministers'])} ministers, "
        f"{len(personnel['teams'])} technology teams"
    )
    print(f"  Duplicate personnel groups: {len(duplicate_personnel)}")
    print(f"  Art-manifest issues: {len(manifest_issues)}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1
    if args.strict and (duplicate_events or manifest_issues):
        print("ERROR: strict V4 art-release criteria are not yet satisfied.")
        return 1
    print("V4 ART INVENTORY PASSED" if not args.strict else "V4 ART RELEASE GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
