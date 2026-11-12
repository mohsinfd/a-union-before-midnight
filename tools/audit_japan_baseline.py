"""Read-only Blood and Iron source/save inspection for the Japan design spec.

Only stdout is written. This is a structural reader, not the game's validator.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'japan_expansion'))
from runtime_paths import GAME as ROOT, SOURCE as BASE
SAVE_BASE = ROOT / "Mods" / "Blood and Iron v1.1"
TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#"]+')
TYPE_IDS = {}
for unit_path in (BASE / "db/units/divisions").glob("*.txt"):
    match = re.search(r"MODEL_(\d+)_", unit_path.read_text(encoding="cp1252", errors="replace")[:100])
    if match:
        TYPE_IDS[match.group(1)] = unit_path.stem


def parse(text, warnings=None):
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith("#")]
    index = 0

    def block(end=False):
        nonlocal index
        result = []
        while index < len(tokens):
            item = tokens[index]
            index += 1
            if item == "}":
                if end:
                    return result
                if warnings is not None:
                    warnings.append("Unexpected top-level closing brace near token " + str(index))
                continue
            if index < len(tokens) and tokens[index] == "=":
                index += 1
                if index >= len(tokens):
                    break
                value = tokens[index]
                index += 1
                if value == "{":
                    value = block(True)
                else:
                    value = value.strip('"')
                result.append((item, value))
            elif item == "{":
                result.append((None, block(True)))
            else:
                result.append((None, item.strip('"')))
        if end:
            raise ValueError("Unclosed block")
        return result

    return block()


def getall(node, key):
    return [v for k, v in node if k == key]


def get(node, key, default=None):
    return next((v for k, v in node if k == key), default)


def num(node, key, default=0):
    try:
        return round(float(get(node, key, default)), 3)
    except (TypeError, ValueError):
        return default


def direct_summary(node):
    return {k: v for k, v in node if k is not None and not isinstance(v, list)}


def units(country, kind, child):
    return [div for unit in getall(country, kind) for div in getall(unit, child)]


def unit_type(unit):
    explicit = get(unit, "type")
    if explicit:
        return explicit
    compact = get(unit, "mod", [])
    return TYPE_IDS.get(compact[0][1], "unknown_" + compact[0][1]) if compact else "unknown"


def strength(unit):
    explicit = get(unit, "strength")
    compact = get(unit, "all", [])
    return float(explicit) if explicit else float(compact[1][1]) if len(compact) > 1 else 0


def save_summary(path):
    data = parse(path.read_text(encoding="cp1252", errors="replace"))
    header = get(data, "header", [])
    globaldata = get(data, "globaldata", [])
    provinces = {get(p,"id"): p for p in getall(data,"province")}
    result = {"file": path.name, "player": get(data, "saved"),
              "date": direct_summary(get(globaldata, "startdate", [])),
              "difficulty": get(header, "set_difficulty"),
              "ic_takeover": get(header, "ictakeover"),
              "team_takeover": get(header, "teamtakeover"), "countries": {}}
    for country in getall(data, "country"):
        tag = get(country, "tag")
        if tag not in {"JAP", "GER", "SOV", "USA", "ENG", "ITA", "CHI", "U87", "IND", "U02", "MAN"}:
            continue
        land = units(country, "landunit", "division")
        ships = units(country, "navalunit", "division")
        air = units(country, "airunit", "division")
        stock = {k: num(country, k) for k in ("oil", "supplies", "energy", "metal", "rare_materials", "money", "manpower", "dissent", "transports", "escorts", "free_ic", "free_oil", "industrial_modifier", "relative_manpower")}
        summary = {"resources": stock, "puppet": get(country, "puppet"),
                   "capital": get(country, "capital"), "ai_file": get(country, "ai_file"),
                   "land": dict(Counter(unit_type(d) for d in land)),
                   "navy": dict(Counter(unit_type(d) for d in ships)),
                   "air": dict(Counter(unit_type(d) for d in air)),
                   "mean_ship_strength": round(sum(strength(s) for s in ships) / max(1, len(ships)), 2),
                   "mean_land_strength": round(sum(strength(s) for s in land) / max(1, len(land)), 2),
                   "owned_provinces": len(get(country, "ownedprovinces", [])),
                   "controlled_provinces": len(get(country, "controlledprovinces", []))}
        national = {v for _,v in get(country,"nationalprovinces",[])}
        controlled = {v for _,v in get(country,"controlledprovinces",[])}
        summary["controlled_national_ic"] = round(sum(num(get(p,"ic",[]),"current_size") for pid,p in provinces.items() if pid in national and pid in controlled),2)
        summary["controlled_foreign_ic"] = round(sum(num(get(p,"ic",[]),"current_size") for pid,p in provinces.items() if pid not in national and pid in controlled),2)
        summary["techapps_count"] = len(get(country,"techapps",[]))
        summary["national_provinces"] = len(national)
        convoys = getall(country,"convoy")
        summary["convoys"] = {"reserve":num(country,"transports"), "assigned":sum(num(c,"transports") for c in convoys), "routes":len(convoys), "routes_without_transports":sum(num(c,"transports")==0 for c in convoys)}
        queue = getall(country, "division_development")
        summary["queue"] = dict(Counter(get(d, "type") for d in queue))
        summary["queue_total_ic"] = round(sum(num(d, "cost") for d in queue), 2)
        summary["queued_carriers"] = [{k: get(d, k) for k in ("name", "type", "cost", "progress", "days", "days_for_first", "date")} for d in queue if get(d, "type") in {"carrier", "light_carrier", "escort_carrier"}]
        ai = get(country, "ai", [])
        summary["ai_settings"] = {k: get(ai, k) for k in ("reinforcement", "upgrading", "min_garrison_prop", "max_garrison_prop", "max_front_ratio")}
        modifiers = get(country, "modifiers", [])
        summary["modifier_scalars"] = direct_summary(modifiers)
        summary["direct_ic_fields"] = {k: v for k,v in country if k and ("ic" in k or "repair" in k) and not isinstance(v, list)}
        if tag == "JAP":
            summary["fleets"] = [{"name": get(u, "name"), "location": get(u, "location"), "ships": dict(Counter(unit_type(d) for d in getall(u, "division")))} for u in getall(country, "navalunit")]
        result["countries"][tag] = summary
    result["wars"] = [{"attackers": [v for k,v in get(get(w, "attackers", []), "participant", [])], "defenders": [v for k,v in get(get(w, "defenders", []), "participant", [])]} for w in getall(globaldata, "war")]
    result["alliances"] = [{"kind": k, "members": [v for _,v in get(v, "participant", [])]} for k,v in globaldata if k in {"axis", "allies", "comintern", "alliance"}]
    return result


def source_events():
    registry = parse((BASE / "db/events.txt").read_text(encoding="cp1252", errors="replace"))
    scenario = parse((BASE / "scenarios/1933.eug").read_text(encoding="cp1252", errors="replace"))
    paths = getall(registry, "event") + [p for p in getall(scenario,"event") if isinstance(p,str)]
    files = list(dict.fromkeys(BASE / p.replace("\\", "/") for p in paths))
    events = []
    missing = []
    errors = []
    for path in files:
        if not path.exists():
            missing.append(str(path.relative_to(BASE)))
            continue
        try:
            warnings = []
            tree = parse(path.read_text(encoding="cp1252", errors="replace"), warnings)
            if warnings:
                errors.append({"file": str(path.relative_to(BASE)), "warnings": warnings})
        except ValueError as exc:
            errors.append({"file": str(path.relative_to(BASE)), "error": str(exc)})
            continue
        for node in getall(tree, "event"):
            events.append((path, node))
    ids = Counter(get(e,"id") for _,e in events)
    return files, events, missing, errors, ids


def events_summary(tags, ids_wanted):
    files, events, missing, errors, ids = source_events()
    result = {"registered_files": len(files), "events": len(events), "missing_files": missing, "parse_errors": errors,
              "duplicate_ids": {k:v for k,v in ids.items() if v>1},
              "country_counts": dict(Counter(get(e,"country","GLOBAL") for _,e in events)), "selected": []}
    for path, event in events:
        if get(event,"country") not in tags and get(event,"id") not in ids_wanted:
            continue
        actions = getall(event,"action") + getall(event,"action_a") + getall(event,"action_b") + getall(event,"action_c") + getall(event,"action_d")
        item = {"id": get(event,"id"), "country": get(event,"country"), "name": get(event,"name"), "file": str(path.relative_to(BASE)),
                "decision": bool(get(event,"decision")), "date": get(event,"date"), "trigger": get(event,"trigger"),
                "actions": [{"name":get(a,"name"), "ai_chance":get(a,"ai_chance"), "commands":getall(a,"command")} for a in actions]}
        result["selected"].append(item)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["save", "events", "inventory", "node"])
    parser.add_argument("target", nargs="*", default=[])
    args = parser.parse_args()
    if args.mode == "save":
        for name in args.target:
            print(json.dumps(save_summary(SAVE_BASE / "scenarios/save games" / name)))
    elif args.mode in {"events", "inventory"}:
        result = events_summary(set(t for t in args.target if not t.isdigit()), set(t for t in args.target if t.isdigit()))
        if args.mode == "inventory":
            for event in result["selected"]:
                event.pop("trigger", None)
                for action in event["actions"]:
                    action["command_types"] = dict(Counter(get(c,"type") for c in action.pop("commands")))
        print(json.dumps(result))
    else:
        path = BASE / args.target[0]
        tree = parse(path.read_text(encoding="cp1252", errors="replace"))
        for key in args.target[1:]:
            if ":" in key:
                field, value = key.split(":",1)
                tree = next(v for k,v in tree if isinstance(v,list) and get(v,field)==value)
            else:
                tree = get(tree,key,[])
        print(json.dumps(tree))


if __name__ == "__main__":
    main()
