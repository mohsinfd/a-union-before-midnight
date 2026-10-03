"""Migrate COMMAND-RESERVE names and ROSTER1 team skills into a live save.

The migration is deliberately bounded: leader IDs, portraits, ranks, skills,
traits, experience and unit assignments are untouched.  Tech-team IDs, skill,
dates and active research progress are also untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import shutil
from pathlib import Path

from aubm_command_reserve import reserve_rows
from dh_save_spans import Node, parse, replace, walk


TEAM_SPECIALTIES = {
    250005: "training",
    250011: "medicine",
    250022: "seamanship",
    250026: "blitzkrieg_tactics",
    250032: "marine_training",
    250033: "naval_artillery",
    250034: "aeronautics",
    250035: "chemistry",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leader_id(node: Node) -> int | None:
    ident = node.get("id")
    if not isinstance(ident, Node) or ident.get("type") != "6":
        return None
    value = ident.get("id")
    return int(value) if value and value.isdigit() else None


def team_id(node: Node) -> int | None:
    ident = node.get("id")
    if not isinstance(ident, Node) or ident.get("type") != "10":
        return None
    value = ident.get("id")
    return int(value) if value and value.isdigit() else None


def rewrite_roster(raw: bytes, names: dict[int, str]) -> tuple[bytes, int]:
    out = []
    changed = 0
    for line in raw.decode("cp1252").splitlines(keepends=True):
        cells = line.rstrip("\r\n").split(";")
        if len(cells) > 1 and cells[1].isdigit() and int(cells[1]) in names:
            if cells[0] != names[int(cells[1])]:
                cells[0] = names[int(cells[1])]
                changed += 1
            ending = "\r\n" if line.endswith("\r\n") else "\n"
            line = ";".join(cells) + ending
        out.append(line)
    return "".join(out).encode("cp1252"), changed


def migrate_save(raw: bytes, names: dict[int, str]) -> tuple[bytes, dict]:
    root = parse(raw)
    india = next(c for c in root.all("country") if c.get("tag") == "IND")
    edits = []
    renamed_ids = set()
    renamed_occurrences = 0
    team_changes = {}

    for node in walk(india):
        lid = leader_id(node)
        if lid in names and node.get("name"):
            field = node.field("name")
            desired = names[lid]
            if field.value != desired:
                edits.append((field.value_start, field.end,
                              ('"' + desired + '"').encode("ascii")))
                renamed_occurrences += 1
            renamed_ids.add(lid)

        tid = team_id(node)
        specialty = TEAM_SPECIALTIES.get(tid)
        research = node.get("research_types")
        if specialty and isinstance(research, Node):
            current = research.atoms()
            if specialty not in current:
                field = node.field("research_types")
                desired = b"{ " + " ".join(current + [specialty]).encode("ascii") + b" }"
                edits.append((field.value_start, field.end, desired))
                team_changes[tid] = specialty

    if renamed_ids != set(names):
        missing = sorted(set(names) - renamed_ids)
        raise ValueError(f"Save is missing reserve leader IDs: {missing[:12]}")
    if set(team_changes) != set(TEAM_SPECIALTIES):
        missing = sorted(set(TEAM_SPECIALTIES) - set(team_changes))
        raise ValueError(f"Expected stale team specialties were not found: {missing}")

    result = replace(raw, edits)
    check = parse(result)
    check_india = next(c for c in check.all("country") if c.get("tag") == "IND")
    for node in walk(check_india):
        lid = leader_id(node)
        if lid in names and node.get("name") != names[lid]:
            raise AssertionError(f"Leader rename validation failed for {lid}")
        tid = team_id(node)
        if tid in TEAM_SPECIALTIES:
            if TEAM_SPECIALTIES[tid] not in node.get("research_types").atoms():
                raise AssertionError(f"Team migration validation failed for {tid}")
    return result, {
        "reserve_leaders": len(renamed_ids),
        "leader_name_occurrences": renamed_occurrences,
        "team_specialties": team_changes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--source-roster", type=Path, required=True)
    parser.add_argument("--live-roster", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--copy", type=Path, required=True)
    args = parser.parse_args()

    names = {int(row[1]): row[0] for row in reserve_rows()}
    if len(names) != 375 or len(set(names.values())) != 375:
        raise ValueError("Reserve-name plan must contain 375 unique full names")

    original = args.save.read_bytes()
    migrated, report = migrate_save(original, names)
    if args.backup.exists():
        if args.backup.read_bytes() != original:
            raise FileExistsError(f"Refusing to replace different backup: {args.backup}")
    else:
        shutil.copy2(args.save, args.backup)

    for roster_path in (args.source_roster, args.live_roster):
        roster, count = rewrite_roster(roster_path.read_bytes(), names)
        roster_path.write_bytes(roster)
        report[str(roster_path)] = count

    args.save.write_bytes(migrated)
    args.copy.write_bytes(migrated)
    if digest(args.save) != digest(args.copy):
        raise AssertionError("Named migrated save differs from autosave")
    print({
        **report,
        "before_sha256": hashlib.sha256(original).hexdigest(),
        "after_sha256": digest(args.save),
        "backup": str(args.backup),
        "copy": str(args.copy),
    })


if __name__ == "__main__":
    main()
