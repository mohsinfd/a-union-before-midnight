"""Repair the stranded Xinjiang settlement in the latest WESTERN1 save."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

from dh_save_spans import Node, parse, replace

SAVE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games\WESTERN1_newplayIndia_1941_October_6.eug")
ROOT = Path(__file__).resolve().parents[1]
SET_ONE = (
    "ind_aubm_regional_settled_sik",
    "ind_aubm_bespoke_protected_sik",
    "ind_aubm_bespoke_negotiated_sik",
    "ind_aubm_global_campaign_victory",
)
CLEAR = (
    "ind_aubm_bespoke_armistice_outstanding",
    "ind_aubm_bespoke_target_sik",
    "ind_stage_bespoke_full_sik",
    "ind_stage_bespoke_limited_sik",
    "ind_stage_bespoke_refused_sik",
    "ind_stage_bespoke_ready_sik",
    "ind_stage_bespoke_attempt_sik",
    "ind_stage_bespoke_deliver_full_sik",
    "ind_stage_bespoke_deliver_limited_sik",
    "ind_aubm_regional_pending_sik",
    "ind_aubm_regional_current_sik",
    "ind_aubm_regional_victory_sik",
    "ind_aubm_regional_suspended_sik",
)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def scalar(node, key, value):
    f = node.field(key)
    return f.value_start, f.end, str(value).encode("latin1")


def participant_edit(container, tag):
    node = container.get("participant")
    atoms = node.atoms()
    if tag in atoms: return None
    return scalar(container, "participant", "{ " + " ".join(atoms + [tag]) + " }")


def queued_fields(node):
    for field in node.fields:
        if field.key == "event" and isinstance(field.value, Node):
            yield field
        if isinstance(field.value, Node):
            yield from queued_fields(field.value)


def main():
    raw = SAVE.read_bytes()
    root = parse(raw)
    countries = {c.get("tag"): c for c in root.all("country")}
    india, sik = countries["IND"], countries["SIK"]
    flags = root.get("globaldata").get("flags")
    if flags.get("ind_stage_bespoke_full_sik") != "1" or flags.get("ind_aubm_bespoke_target_sik") != "1":
        raise ValueError("Latest save is no longer at the stranded accepted-Xinjiang state")
    edits = []

    # The accepted full settlement becomes the missing useful outcome:
    # protected Xinjiang, Indian access, and participation beside India.
    if sik.get("puppet") is None:
        # Darkest Hour requires tag to be the first field in every country.
        edits.append((sik.field("tag").end, sik.field("tag").end, b"\n\tpuppet = IND"))
    elif sik.get("puppet") != "IND":
        edits.append(scalar(sik, "puppet", "IND"))
    relation = next(x for x in india.get("diplomacy").all("relation") if x.get("tag") == "SIK")
    if relation.get("access") != "yes":
        edits.append((relation.end - 1, relation.end - 1, b" access = yes "))
    axis = root.get("globaldata").get("axis")
    edit = participant_edit(axis, "SIK")
    if edit: edits.append(edit)
    for war in root.get("globaldata").all("war"):
        side = next((war.get(k) for k in ("attackers", "defenders")
                     if isinstance(war.get(k), Node) and "IND" in war.get(k).get("participant").atoms()), None)
        if side:
            edit = participant_edit(side, "SIK")
            if edit: edits.append(edit)

    missing = []
    for name in SET_ONE:
        f = next((x for x in flags.fields if x.key == name), None)
        if f: edits.append((f.value_start, f.end, b"1"))
        else: missing.append(f"\n\t{name} = 1")
    for name in CLEAR:
        f = next((x for x in flags.fields if x.key == name), None)
        if f: edits.append((f.value_start, f.end, b"0"))
        else: missing.append(f"\n\t{name} = 0")
    if missing: edits.append((flags.end - 1, flags.end - 1, "".join(missing).encode("ascii")))

    # Refund the four dissent explicitly reported as part of the broken result.
    dissent = float(india.get("dissent"))
    edits.append(scalar(india, "dissent", f"{max(0.0, dissent - 4.0):.4f}"))
    removed_queue = 0
    for field in queued_fields(root):
        event = field.value
        if event.get("tag") == "IND" and event.get("id") in ("9282288", "9282291"):
            edits.append((field.start, field.end, b"")); removed_queue += 1

    updated = replace(raw, edits)
    check = parse(updated)
    cc = {c.get("tag"): c for c in check.all("country")}
    ff = check.get("globaldata").get("flags")
    assert cc["SIK"].get("puppet") == "IND"
    assert next(x for x in cc["IND"].get("diplomacy").all("relation") if x.get("tag") == "SIK").get("access") == "yes"
    assert "SIK" in check.get("globaldata").get("axis").get("participant").atoms()
    assert all(ff.get(x) == "1" for x in SET_ONE)
    assert all(ff.get(x) == "0" for x in CLEAR)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "build/western-portfolio1" / ("pre-xinjiang-repair-" + stamp)
    backup.mkdir(parents=True)
    backup_file = backup / SAVE.name
    backup_file.write_bytes(raw)
    SAVE.write_bytes(updated)
    print(json.dumps({
        "save": str(SAVE), "backup": str(backup_file),
        "before_sha256": sha(raw), "after_sha256": sha(updated),
        "xinjiang": "Indian puppet and Axis participant",
        "indian_access": True, "dissent_before": dissent,
        "dissent_after": max(0.0, dissent - 4.0),
        "stale_callbacks_removed": removed_queue,
        "units_and_province_control_unchanged": True,
    }, indent=2))


if __name__ == "__main__": main()
