"""Install the coalition-settlement repair and create a lossless newplay copy.

The original save is never overwritten.  Only Indian-controlled Iraqi release
territory still legally owned by Britain is transferred to India so that the
existing constitutional settlement can create Iraq.  Controller state, units,
wars, resources, production and history are unchanged.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from dh_save_spans import Node, parse, replace

ROOT = Path(__file__).resolve().parents[1]
MOD = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1")
CANDIDATE = ROOT / "build/redesign/candidate8/staged-authored"
SOURCE = "newplayIndia_1941_October_6.eug"
OUTPUT = "WESTERN1_newplayIndia_1941_October_6.eug"
TITLE = "WESTERN1 - India 6 October 1941"
EVENT_FILES = (
    "db/events/aubm_v4/43_wartime_settlements.txt",
    "db/events/aubm_v4/46_regional_campaigns.txt",
    "db/events/aubm_v4/47_global_campaign_matrix.txt",
    "db/events/aubm_v4/49_bespoke_armistices.txt",
    "db/events/india_v3/40_diplomacy.txt",
)
FLAGS = (
    "ind_aubm_regional_pending_irq",
    "ind_aubm_regional_current_irq",
    "ind_aubm_regional_victory_irq",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def scalar(node: Node, key: str, value: str):
    field = node.field(key)
    return field.value_start, field.end, value.encode("latin1")


def migrate_save(raw: bytes, preserve_header: bool = False):
    root = parse(raw)
    countries = {c.get("tag"): c for c in root.all("country")}
    india, britain = countries["IND"], countries["ENG"]
    if "IRQ" in countries:
        raise ValueError("Iraq now exists; reassess instead of replaying this migration")
    irq = set(json.loads((ROOT / "tools/data/release_territories.json").read_text())["IRQ"])
    ind_control = {int(p) for p in india.get("controlledprovinces").atoms()}
    eng_owned = [int(p) for p in britain.get("ownedprovinces").atoms()]
    transfer = sorted(irq & ind_control & set(eng_owned))
    if 1034 not in transfer:
        raise ValueError("India no longer controls British-owned Baghdad")

    ind_owned = [int(p) for p in india.get("ownedprovinces").atoms()]
    new_ind = ind_owned + [p for p in transfer if p not in ind_owned]
    new_eng = [p for p in eng_owned if p not in transfer]
    edits = [
        scalar(india, "ownedprovinces", "{ " + " ".join(map(str, new_ind)) + " }"),
        scalar(britain, "ownedprovinces", "{ " + " ".join(map(str, new_eng)) + " }"),
    ]
    flags = root.get("globaldata").get("flags")
    for name in FLAGS:
        field = flags.field(name)
        if field:
            edits.append((field.value_start, field.end, b"1"))
        else:
            edits.append((flags.end - 1, flags.end - 1, (f"\n\t{name} = 1").encode("ascii")))
    header = root.get("header")
    if not preserve_header:
        edits += [
            scalar(header, "name", '"' + TITLE + '"'),
            scalar(header, "optionfile", '"scenarios\\save games\\' + OUTPUT + '.cfg"'),
        ]
    updated = replace(raw, edits)
    check = parse(updated)
    cc = {c.get("tag"): c for c in check.all("country")}
    for province in transfer:
        owners = [tag for tag, c in cc.items() if str(province) in c.get("ownedprovinces", Node()).atoms()]
        if owners != ["IND"]:
            raise AssertionError((province, owners))
    if any(check.get("globaldata").get("flags").get(f) != "1" for f in FLAGS):
        raise AssertionError("Iraq settlement flags were not armed")
    return updated, transfer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--apply-original", action="store_true")
    args = ap.parse_args()
    save_dir = MOD / "scenarios/save games"
    source = save_dir / SOURCE
    output = save_dir / OUTPUT
    cfg_in = save_dir / (SOURCE + ".cfg")
    cfg_out = save_dir / (OUTPUT + ".cfg")
    raw = source.read_bytes()
    if args.apply_original:
        migrated, transfer = migrate_save(raw, preserve_header=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = ROOT / "build/western-portfolio1" / ("newplay-backup-" + stamp)
        backup.mkdir(parents=True)
        (backup / SOURCE).write_bytes(raw)
        source.write_bytes(migrated)
        if parse(source.read_bytes()).get("header").get("name") != parse(raw).get("header").get("name"):
            raise AssertionError("Original save title changed")
        print(json.dumps({
            "applied_to": str(source),
            "backup": str(backup / SOURCE),
            "before_sha256": sha(raw),
            "after_sha256": sha(migrated),
            "iraq_provinces_transferred": transfer,
            "header_and_optionfile_preserved": True,
            "engine_launched": False,
        }, indent=2))
        return
    migrated, transfer = migrate_save(raw)
    files = {MOD / rel: (CANDIDATE / rel).read_bytes() for rel in EVENT_FILES}
    report = {
        "build": "WESTERN-PORTFOLIO1",
        "source_save": SOURCE,
        "source_sha256": sha(raw),
        "repaired_save": OUTPUT,
        "repaired_sha256": sha(migrated),
        "iraq_provinces_transferred_from_britain_to_india": transfer,
        "original_save_unchanged": True,
        "engine_launched": False,
        "event_files": list(EVENT_FILES),
    }
    if not args.install:
        print(json.dumps(report, indent=2))
        return
    if output.exists() or cfg_out.exists():
        raise FileExistsError("Repaired save already exists")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "build/western-portfolio1" / ("backup-" + stamp)
    backup.mkdir(parents=True)
    for target in files:
        rel = target.relative_to(MOD)
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(target.read_bytes())
    save_backup = backup / "scenarios/save games" / SOURCE
    save_backup.parent.mkdir(parents=True, exist_ok=True)
    save_backup.write_bytes(raw)
    for target, data in files.items():
        target.write_bytes(data)
    output.write_bytes(migrated)
    cfg_out.write_bytes(cfg_in.read_bytes())
    if source.read_bytes() != raw:
        raise AssertionError("Original save changed")
    report["backup"] = str(backup)
    receipt = MOD / "WESTERN-PORTFOLIO1.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
