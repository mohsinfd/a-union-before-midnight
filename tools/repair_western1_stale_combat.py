"""Remove hostile combat state left behind after Persia became India's puppet."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import Node, parse, replace

SAVE_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games")
SOURCE = SAVE_DIR / "PLAY_WESTERN1_FIXED_India_1941_October_15.eug"
OUTPUT = SAVE_DIR / "PLAY_WESTERN1_RUNTIME_FIXED_India_1941_October_15.eug"


def identifier(node):
    value = node.get("id")
    if isinstance(value, Node):
        return value.get("type"), value.get("id")
    if node.get("type") is not None and value is not None:
        return node.get("type"), value
    return None


def main():
    raw = SOURCE.read_bytes()
    root = parse(raw)
    countries = {c.get("tag"): c for c in root.all("country")}
    coalition = {"IND", "PER", "SIK"}
    controlled = {
        tag: set(country.get("controlledprovinces").atoms())
        for tag, country in countries.items()
        if country.get("controlledprovinces")
    }
    unit_owner = {}
    for tag, country in countries.items():
        for kind in ("landunit", "airunit", "navalunit"):
            for unit in country.all(kind):
                unit_owner[identifier(unit)] = tag

    edits = []
    removed_combats = []
    combat_fields = [field for field in root.fields
                     if field.key == "combat" and isinstance(field.value, Node)]
    for combat_field in combat_fields:
        combat = combat_field.value
        sides = []
        for side_name in ("attackers", "defenders"):
            owners = set()
            for field in combat.get(side_name).fields:
                if isinstance(field.value, Node):
                    owners.add(unit_owner.get(identifier(field.value), "UNKNOWN"))
            sides.append(owners)
        if sides[0] and sides[1] and sides[0] <= coalition and sides[1] <= coalition:
            edits.append((combat_field.start, combat_field.end, b""))
            removed_combats.append({"province": combat.get("province"),
                                    "attackers": sorted(sides[0]),
                                    "defenders": sorted(sides[1])})

    cancelled_orders = []
    removable = {"mission", "movetime", "movement", "attack", "hour"}
    for owner in coalition:
        for unit in countries[owner].all("landunit"):
            mission = unit.get("mission")
            if not isinstance(mission, Node) or mission.get("type") != "attack":
                continue
            target = str(mission.get("target"))
            target_allies = {tag for tag in coalition if target in controlled.get(tag, set())}
            stale = (owner == "IND" and bool(target_allies & {"PER", "SIK"}))
            stale = stale or (owner in {"PER", "SIK"} and bool(target_allies))
            if not stale:
                continue
            cancelled_orders.append({"owner": owner, "unit": unit.get("name"),
                                     "location": unit.get("location"), "target": target})
            for field in unit.fields:
                if field.key in removable:
                    edits.append((field.start, field.end, b""))

    optionfile = root.get("header").field("optionfile")
    display_name = root.get("header").field("name")
    edits.append((optionfile.value_start, optionfile.end,
                  b'"scenarios\\save games\\PLAY_WESTERN1_RUNTIME_FIXED_India_1941_October_15.eug.cfg"'))
    edits.append((display_name.value_start, display_name.end,
                  b'"PLAY WESTERN1 RUNTIME FIXED - India 15 October 1941"'))

    updated = replace(raw, edits)
    check = parse(updated)
    checked_countries = {c.get("tag"): c for c in check.all("country")}
    assert checked_countries["PER"].get("puppet") == "IND"
    assert checked_countries["SIK"].get("puppet") == "IND"
    assert len(check.all("combat")) == len(root.all("combat")) - len(removed_combats)
    for unit in checked_countries["IND"].all("landunit"):
        mission = unit.get("mission")
        if isinstance(mission, Node) and mission.get("type") == "attack":
            target = str(mission.get("target"))
            assert target not in controlled["PER"] and target not in controlled["SIK"]

    OUTPUT.write_bytes(updated)
    shutil.copy2(SOURCE.with_suffix(".eug.cfg"), OUTPUT.with_suffix(".eug.cfg"))
    print(json.dumps({
        "play_this": str(OUTPUT),
        "source_unchanged": str(SOURCE),
        "removed_stale_combats": removed_combats,
        "cancelled_stale_orders": cancelled_orders,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": hashlib.sha256(updated).hexdigest(),
        "diplomacy_unit_composition_provinces_production_changed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
