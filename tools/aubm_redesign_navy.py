"""Bounded naval procurement changes; pure staged transform, no file I/O.

DH local event commands documentation: build_division.value attaches ONE
brigade; add_brigade creates a separate deployment-pool brigade. Its where
value is requested days for the first queue item, capped by normal build time.
Elapsed event checks require save_date=yes. These are schedule proxies, never
queue-progress checks. Existing paid orders without this stage's provenance
retain the old calendar gate; no missing timestamp is treated as elapsed time.
"""
from __future__ import annotations

import json
import math
from dh_save_spans import Node, parse, replace, walk

MARKER = "# AUBM_STAGED_NAVY_V1"
NAVY_MODULE = "32_navy.txt"
CAPITAL_MODULE = "40_special_units_and_capital_ships.txt"
EDITED_IDS = (*range(9271100, 9271111), 9281880, 9281881)
INSPECTED_UNCHANGED_IDS = (9271111, 9271112)
COST_CHANGES = {9271104: ((650, 1500), (450, 1000)),
                9271105: ((700, 1600), (500, 1100)),
                9281880: ((900, 2200), (600, 1500)),
                9281881: ((1000, 2400), (550, 1400))}
PROGRAMMES = ("ind_v3_fleet_carrier_authorized", "ind_v3_two_light_carriers",
              "ind_v3_submarine_navy")
# ceil(maximum MP over locally resolved authored/installed/stock hull models).
# Brigade manpower is zero except CAG=.15 and light CAG=.07. Queue creation
# consumes its own manpower; these are reserves, NOT an extra event MP debit.
QUEUE_RESERVES = {9271104: 8, 9271105: 8, 9281880: 3, 9281881: 3}
OCEAN_RESERVES = (13, 9, 6)
TIMING = {
    9271105: dict(previous=9271104, days=225, scheduled=360, legacy=(1938, 3, 0)),
    9271106: dict(previous=9271105, days=225, scheduled=360, legacy=(1938, 9, 0)),
    9271107: dict(previous=9271106, days=(210, 170, 210), scheduled=(330, 270, 330), legacy=(1940, 0, 0)),
    9271110: dict(previous=9271109, days=60, scheduled=90, legacy=(1942, 6, 0)),
    9281881: dict(previous=9281880, days=265, scheduled=420, legacy=(1941, 0, 0)),
}
PROJECT_NAMES = {9271104: "Arabian Sea Fleet", 9271105: "Bay of Bengal Fleet",
                 9271106: "Oceanic Fleet", 9271109: "Naval Board orders",
                 9281880: "Project Himalaya"}
NEW_DESCRIPTIONS = {
    9271104: "Karachi's command proposes a battleship, two light cruisers and two destroyer flotillas for the Gulf approaches. The appropriation places five current-model hulls in normal production, each with its listed attached fitting. The player must still fund their daily industrial cost.",
    9271105: "Vizagapatam's command must protect Calcutta, Rangoon and the approaches to Malaya. A battleship, two light cruisers and two destroyer flotillas will enter normal production, each with its listed attached fitting. Work on this fleet can begin while the western programme is still under way.",
    9281880: "Naval constructors propose state funding for the armour forgings and design work of INS Meru. The order requests a current-buildable-model battleship with fire control and a 420-day first-hull schedule, subject to the engine's normal-time cap. Daily production IC remains the player's responsibility.",
    9281881: "The Himalaya design can support a sister ship while its heavy tooling remains in use. A smaller appropriation orders INS Trikuta as a current-buildable-model battleship with fire control and the same requested 420-day schedule. Daily production IC remains the player's responsibility.",
}
MONTHS = "january february march april may june july august september october november december".split()


def paid_flag(eid):
    return "ind_redesign_navy_paid_" + str(eid)


def calendar_gate(year, month=0, day=0):
    return (f"OR = {{ year = {year + 1} AND = {{ year = {year} "
            f"OR = {{ month = {month + 1} AND = {{ month = {month} day = {day} }} }} }} }}"
            if month < 11 else f"OR = {{ year = {year + 1} AND = {{ year = {year} month = 11 day = {day} }} }}")


def exact_programme(index):
    return "flag = " + PROGRAMMES[index] + " " + " ".join(
        "NOT = { flag = " + other + " }" for n, other in enumerate(PROGRAMMES) if n != index)


def timing_gate(eid):
    info = TIMING[eid]
    previous = info["previous"]
    if isinstance(info["days"], tuple):
        elapsed = "OR = { " + " ".join(
            "AND = { " + exact_programme(i) + f" event = {{ id = {previous} days = {days} }} }}"
            for i, days in enumerate(info["days"])) + " }"
    else:
        elapsed = f"event = {{ id = {previous} days = {info['days']} }}"
    return ("OR = { AND = { flag = " + paid_flag(previous) + " " + elapsed + " } "
            "AND = { NOT = { flag = " + paid_flag(previous) + " } "
            + calendar_gate(*info["legacy"]) + " } }")


def inner(text, node):
    # A final source comment must not swallow a newly appended closing brace.
    return "\n" + text[node.start + 1:node.end - 1].strip() + "\n"


def actions(event):
    return [f for f in event.fields if f.key and f.key.startswith("action") and isinstance(f.value, Node)]


def substantive(action):
    return any(c.get("type") for c in action.all("command"))


def set_fields(text, values):
    event = parse(text).get("event")
    edits, additions = [], []
    for key, value in values.items():
        matches = [f for f in event.fields if f.key == key]
        if len(matches) > 1:
            raise ValueError("Duplicate naval event field " + key)
        if matches:
            f = matches[0]
            edits.append((f.value_start, f.end, value))
        else:
            additions.append(f"\n {key} = {value}\n")
    if additions:
        edits.append((event.end - 1, event.end - 1, "".join(additions)))
    return replace(text, edits)


def option_stock(action):
    costs = {}
    for c in action.all("command"):
        resource = {"money": "money", "supplies": "supplies", "manpowerpool": "manpower"}.get(c.get("type"))
        if resource and float(c.get("value", 0)) < 0:
            costs[resource] = costs.get(resource, 0) - float(c.get("value"))
    return " ".join(f"{key} = {math.ceil(value)}" for key, value in costs.items())


def rewrite_event(text, eid):
    event = parse(text).get("event")
    if MARKER in text:
        validate_event(event, eid)
        return text
    edits = []
    # Change only the named appropriation stock thresholds and deductions.
    if eid in COST_CHANGES:
        before, after = COST_CHANGES[eid]
        expected = dict(zip(("money", "supplies"), before))
        desired = dict(zip(("money", "supplies"), after))
        for node in walk(event):
            for f in node.fields:
                if f.key in expected and f.value == str(expected[f.key]):
                    edits.append((f.value_start, f.end, str(desired[f.key])))
            if node.get("type") in expected:
                resource = node.get("type")
                if node.get("value") != str(-expected[resource]):
                    raise ValueError(f"Naval appropriation drift: {eid} {resource}")
                f = node.field("value")
                edits.append((f.value_start, f.end, str(-desired[resource])))
    for af in actions(event):
        for f in af.value.fields:
            if f.key == "command" and f.value.get("type") == "add_brigade":
                edits.append((f.start, f.end, ""))
        if eid == 9271106 and isinstance(af.value.get("trigger"), Node):
            # Replace the old one-size 8 MP reserve with the complete branch
            # crew calculation, rather than leaving it overcharging the gate
            # for the 6-MP submarine option or underchecking the 13-MP carrier.
            for node in walk(af.value.get("trigger")):
                for f in node.fields:
                    if f.key == "manpower" and f.value == "8":
                        edits.append((f.start, f.end, ""))
    text = replace(text, edits)
    event = parse(text).get("event")
    # Retain all existing event context, including done flags and territory.
    roots = [event.get(k) for k in ("decision", "trigger") if isinstance(event.get(k), Node)]
    context = " ".join("AND = { " + inner(text, root) + " }" for root in roots)
    if eid in TIMING:
        # Calendar floors become an elapsed contract gate for newly paid work.
        # The pre-stage calendar survives in the explicit legacy branch.
        context = context.replace("year = 1940", "exists = IND") if eid == 9271107 else context
        context = context.replace("year = 1941", "exists = IND") if eid == 9281881 else context
        context += " " + timing_gate(eid)
    else:
        date = event.get("date")
        if isinstance(date, Node):
            month = date.get("month")
            if eid == 9271104:
                context += " " + calendar_gate(1937, 2, 0)
            else:
                context += " " + calendar_gate(int(date.get("year")), MONTHS.index(month) if month in MONTHS else int(month), int(date.get("day", 0)))
    if eid in (9271106, 9271107):
        context += " OR = { " + " ".join("AND = { " + exact_programme(i) + " }" for i in range(3)) + " }"
    if eid in QUEUE_RESERVES:
        context += f" manpower = {QUEUE_RESERVES[eid]}"
    if eid == 9271106:
        context += " OR = { " + " ".join("AND = { " + exact_programme(i) + f" manpower = {mp} }}" for i, mp in enumerate(OCEAN_RESERVES)) + " }"
    option_gates = []
    edits = []
    for af in actions(event):
        a = af.value
        if not substantive(a):
            continue
        gate = inner(text, a.get("trigger")) if isinstance(a.get("trigger"), Node) else ""
        # The original queue thresholds on the Naval Board underestimated the
        # latest DD models. Three reserve covers one DD; four covers two.
        if eid == 9271109:
            gate += " manpower = " + ("3" if sum(c.get("type") == "build_division" for c in a.all("command")) == 1 else "4")
        if eid == 9271103 and any(c.get("type") == "build_division" for c in a.all("command")):
            # The original source already has a 2-MP guard; make the queue
            # contract explicit here so guarded source variants cannot lose it.
            gate += " manpower = 2"
        gate += " " + option_stock(a)
        option_gates.append("AND = { " + gate + " }")
        new_gate = "{ " + context + " " + gate + " }"
        if a.get("trigger") is not None:
            f = a.field("trigger")
            edits.append((f.value_start, f.end, new_gate))
        else:
            edits.append((a.start + 1, a.start + 1, "\n trigger = " + new_gate + "\n"))
        edits.append((a.end - 1, a.end - 1, "\n command = { type = setflag which = " + paid_flag(eid) + " }\n"))
    text = replace(text, edits)
    event = parse(text).get("event")
    if not any(not substantive(a.value) for a in actions(event)):
        used = {a.key for a in actions(event)}
        label = next(("action_" + letter for letter in "abcd" if "action_" + letter not in used), "action")
        text = replace(text, [(event.end - 1, event.end - 1,
            f'\n {label} = {{ name = "Not now - keep this project open" trigger = {{ ai = no }} ai_chance = 0 }}\n')])
    tooltip = "Optional project. Not now is free. "
    if eid in COST_CHANGES:
        money, supplies = COST_CHANGES[eid][1]
        tooltip += f"Appropriation: {money} money, {supplies} supplies. Normal daily production IC remains payable. "
    if eid in TIMING:
        info = TIMING[eid]
        days = "/".join(map(str, info["days"])) if isinstance(info["days"], tuple) else str(info["days"])
        tooltip += f"New contracts: {days} days after {PROJECT_NAMES[info['previous']]} authorization; elapsed time, not queue progress. Legacy contracts retain their original calendar gate. "
    if eid in (9271104, 9271105, 9271106, 9281880, 9281881):
        tooltip += "One listed attachment per hull; no loose fittings granted. "
    if eid in QUEUE_RESERVES:
        tooltip += f"Reserve {QUEUE_RESERVES[eid]} manpower for queue crews, not an extra event debit. "
    if eid == 9271106:
        tooltip += "Crew reserves: fleet carrier 13, light carriers 9, submarine plan 6; queue consumes its own crews. "
    if eid in (9281880, 9281881):
        tooltip += "+2 dissent." if eid == 9281880 else "+1 dissent."
    values = {"persistent": "yes", "save_date": "yes",
              "decision": "{ " + context + " }",
              "decision_trigger": "{ " + context + " OR = { " + " ".join(option_gates) + " } }",
              "trigger": "{ " + context + " OR = { " + " ".join(option_gates) + " } }",
              "decision_desc": json.dumps(tooltip)}
    if eid in TIMING:
        values["date"] = "{ day = 0 month = january year = 1933 }"
    if eid == 9271104:
        values["date"] = "{ day = 0 month = march year = 1937 }"
    if eid in NEW_DESCRIPTIONS:
        values["desc"] = json.dumps(NEW_DESCRIPTIONS[eid])
    text = set_fields(text, values)
    event = parse(text).get("event")
    text = replace(text, [(event.start + 1, event.start + 1, "\n " + MARKER + "\n")])
    validate_event(parse(text).get("event"), eid)
    return text


def validate_event(event, eid):
    if event.get("persistent") != "yes" or event.get("save_date") != "yes":
        raise ValueError("Naval cancel/timer contract missing: " + str(eid))
    for key in ("decision", "decision_trigger", "trigger"):
        if not isinstance(event.get(key), Node):
            raise ValueError("Naval context missing: " + str(eid))
    for a in actions(event):
        if substantive(a.value):
            if not isinstance(a.value.get("trigger"), Node):
                raise ValueError("Naval action gate missing: " + str(eid))
            commands = a.value.all("command")
            if any(c.get("type") == "add_brigade" for c in commands):
                raise ValueError("Loose naval brigade returned: " + str(eid))
            if not any(c.get("type") == "setflag" and c.get("which") == paid_flag(eid) for c in commands):
                raise ValueError("Naval paid provenance missing: " + str(eid))


def transform(files: dict[str, str]):
    output, records, seen = dict(files), {}, set()
    for path, text in files.items():
        basename = str(path).replace("\\", "/").rsplit("/", 1)[-1]
        if basename not in (NAVY_MODULE, CAPITAL_MODULE):
            continue
        edits = []
        for f in parse(text).fields:
            if f.key != "event" or not isinstance(f.value, Node):
                continue
            eid = int(f.value.get("id"))
            if eid not in (*EDITED_IDS, *INSPECTED_UNCHANGED_IDS):
                continue
            seen.add(eid)
            if eid in EDITED_IDS:
                revised = rewrite_event(text[f.start:f.end], eid)
                edits.append((f.start, f.end, revised))
            records[eid] = [dict(dimension="navy", status="reviewed", path=path,
                changes=("Affordability/current context/cancel guarded; paid provenance and dated authorization" if eid in EDITED_IDS else "Existing dockyard speed modifiers inspected, unchanged"),
                costs=COST_CHANGES.get(eid), timing=TIMING.get(eid),
                caveats=["Native queue creation and event-date persistence require playtesting",
                         "Timers measure authorization age, not queue funding, cancellations or completion",
                         "Legacy orders retain prior calendar access; existing loose brigades are not removed",
                         "Other naval procurement families outside modules 32/40 remain pending"])]
        output[path] = replace(text, edits)
    for eid in set(EDITED_IDS) - seen:
        records[eid] = [dict(dimension="navy", status="pending", changes="Authored event absent")]
    return output, records
