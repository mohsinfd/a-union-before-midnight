#!/usr/bin/env python3
"""Synchronize every V4 event with its custom-art provenance record."""

from __future__ import annotations

import csv
import hashlib
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "mod/db/events/aubm_v4"
PICTURE_DIR = ROOT / "mod/gfx/events_pics"
ART_MANIFEST = ROOT / "docs/art_manifest.csv"
OUTPUT = ROOT / "docs/v4_event_art_manifest.csv"

SOURCE_KIND = "generated alternate-history reconstruction"
CREATOR = "OpenAI image generation"
CREDIT = (
    "Original AI-assisted reconstruction created for A Union Before Midnight; "
    "not an archival photograph"
)


def event_catalog() -> list[tuple[int, str, str]]:
    catalog: list[tuple[int, str, str]] = []
    event_pattern = re.compile(r"(?m)^event\s*=\s*\{")
    id_pattern = re.compile(r"(?m)^\s*id\s*=\s*(928\d+)\s*$")
    name_pattern = re.compile(r'(?m)^\s*name\s*=\s*"([^"]+)"\s*$')
    picture_pattern = re.compile(r'(?m)^\s*picture\s*=\s*"([^"]+)"\s*$')
    seen: set[int] = set()
    for path in sorted(EVENT_DIR.glob("*.txt")):
        text = path.read_text(encoding="cp1252")
        starts = [match.start() for match in event_pattern.finditer(text)] + [len(text)]
        for start, end in zip(starts, starts[1:], strict=False):
            block = text[start:end]
            event_id = id_pattern.search(block)
            title = name_pattern.search(block)
            picture = picture_pattern.search(block)
            if not event_id or not title or not picture:
                continue
            numeric_id = int(event_id.group(1))
            if numeric_id in seen:
                raise ValueError(f"duplicate V4 event id {numeric_id}")
            seen.add(numeric_id)
            catalog.append((numeric_id, title.group(1), picture.group(1)))
    return sorted(catalog)


def provenance() -> dict[str, tuple[str, str]]:
    records: dict[str, tuple[str, str]] = {}
    with ART_MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("kind") != "event":
                continue
            asset = row.get("asset") or ""
            source = row.get("source") or ""
            match = re.fullmatch(r"(.+)#panel=(\d+)", source)
            if not asset or not match:
                raise ValueError(f"invalid art provenance for {asset or '<blank>'}")
            records[asset] = (match.group(1), match.group(2))
    return records


def main() -> int:
    sources = provenance()
    rows: list[dict[str, str | int]] = []
    for event_id, title, asset in event_catalog():
        if asset not in sources:
            raise ValueError(f"V4 event {event_id} uses unmanifested custom art {asset}")
        picture = PICTURE_DIR / f"{asset}.bmp"
        if not picture.is_file():
            raise FileNotFoundError(picture)
        source_sheet, panel = sources[asset]
        rows.append(
            {
                "asset": asset,
                "event_id": event_id,
                "event_title": title,
                "source_sheet": source_sheet,
                "panel": panel,
                "source_kind": SOURCE_KIND,
                "creator": CREATOR,
                "credit": CREDIT,
                "sha256": hashlib.sha256(picture.read_bytes()).hexdigest(),
            }
        )

    fieldnames = (
        "asset",
        "event_id",
        "event_title",
        "source_sheet",
        "panel",
        "source_kind",
        "creator",
        "credit",
        "sha256",
    )
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Synchronized {len(rows)} V4 event-art mappings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
