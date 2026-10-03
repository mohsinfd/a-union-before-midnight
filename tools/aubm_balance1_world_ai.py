"""Small, lossless world-AI overlay for a fresh BALANCE1 campaign.

Pure transform over the installed-baseline text manifest. Does not install,
read saves, run DH, or change difficulty. AI directives and unit commands are
from local DH Modding documentation/AI Files Modifiers.txt and event commands.txt.
"""
from __future__ import annotations

import re
from dh_save_spans import Node, parse, replace

MARKER = "# AUBM_BALANCE1_WORLD_AI_V1"
EVENT_PATH = "db/events/aubm_v4/53_world_ai_balance1.txt"
AI_DIR = "ai/aubm/balance1"
ENEMIES = ("SOV", "JAP", "ENG", "USA", "GER", "ITA", "AST")
PORTS = {483: 70, 488: 55, 493: 60, 495: 65}
NODES = {
    "GER": PORTS,
    "ITA": {359: 70, 377: 80, 382: 60, 750: 65, 761: 65, 765: 60},
    "SOV": {713: 60, 706: 50, 1103: 50, 1105: 40},
    "JAP": {1395: 45, 1399: 55, 1423: 45, 1432: 70, 1647: 65},
    "ENG": {900: 85, 1034: 55, 1415: 60, 1432: 80},
}


def _set(text, path, value):
    """Set a scalar or insert missing blocks, preserving unrelated bytes."""
    root = parse(text)
    parent = root
    for i, key in enumerate(path[:-1]):
        child = parent.get(key)
        if child is None:
            tail = f"{path[-1]} = {value}"
            for name in reversed(path[i:-1]):
                tail = f"{name} = {{ {tail} }}"
            at = len(text) if parent is root else parent.end - 1
            return text[:at] + "\n\t" + tail + "\n" + text[at:]
        if not isinstance(child, Node):
            raise ValueError(f"Expected block {path[:i + 1]}")
        parent = child
    found = [f for f in parent.fields if f.key == path[-1]]
    if len(found) > 1:
        raise ValueError(f"Duplicate field {path}")
    if found:
        f = found[0]
        return replace(text, [(f.value_start, f.end, str(value))])
    at = len(text) if parent is root else parent.end - 1
    return text[:at] + f"\n\t{path[-1]} = {value}\n" + text[at:]


def _floor(text, path, value):
    node = parse(text)
    for key in path[:-1]:
        node = node.get(key) if isinstance(node, Node) else None
    old = node.get(path[-1]) if isinstance(node, Node) else None
    return _set(text, path, max(value, float(old))) if old is not None else _set(text, path, value)


def _enemy_guard(tag):
    return (f"ai = yes exists = {tag} exists = IND NOT = {{ ai = IND }} "
            f"war = {{ country = {tag} country = IND }} "
            f"NOT = {{ alliance = {{ country = {tag} country = IND }} }}")


def _response_command(tag):
    return ('command = { trigger = { ' + _enemy_guard(tag) + ' } '
            'type = ai which = "aubm/balance1/' + tag + '_india_front.ai" }')


def _hook_switches(text):
    """Reapply narrow response after real stock switches; no polling events."""
    if not re.search(r"\btype\s*=\s*ai\b", text):
        return text, 0
    edits = []
    for event in parse(text).all("event"):
        if not isinstance(event, Node) or event.get("country") not in ENEMIES:
            continue
        tag = event.get("country")
        for field in event.fields:
            if not (field.key == "action" or (field.key or "").startswith("action_")) or not isinstance(field.value, Node):
                continue
            action = field.value
            if any(isinstance(c, Node) and c.get("type") == "ai" for c in action.all("command")):
                edits.append((action.end - 1, action.end - 1, "\n\t\t" + _response_command(tag) + "\n\t"))
    return replace(text, edits), len(edits)


def _finland(text):
    edits = []
    for event in parse(text).all("event"):
        if not isinstance(event, Node):
            continue
        eid = event.get("id")
        if eid == "3030010":
            trig = event.get("trigger")
            for f in trig.fields:
                if f.key == "NOT" and isinstance(f.value, Node) and f.value.get("lost_national"):
                    edits.append((f.start, f.end, ""))
        elif eid == "3030011":
            trig = event.get("trigger")
            for f in trig.fields:
                if f.key == "OR" and isinstance(f.value, Node) and f.value.get("lost_national"):
                    edits.append((f.start, f.end, "NOT = { war = { country = SOV } }"))
    if len(edits) != 2:
        raise ValueError("Unexpected Finland homeland switch structure")
    return replace(text, edits)


def _event(eid, tag, trigger, commands, year=1933, month="january", persistent=False):
    return f'''event = {{
    id = {eid}
    country = {tag}
    random = no
    persistent = {"yes" if persistent else "no"}
    trigger = {{ {trigger} }}
    name = "AI_EVENT"
    style = 0
    date = {{ day = 1 month = {month} year = {year} }}
    offset = 3
    deathdate = {{ day = 29 month = december year = 1963 }}
    action_a = {{
        {commands}
    }}
}}
'''


def generated_events():
    text = MARKER + "\n# Hidden AI-only state transitions; no player decisions.\n"
    for index, tag in enumerate(ENEMIES):
        flag = "aubm_b1_india_front_" + tag.lower()
        text += _event(9318000 + 2 * index, tag,
                       _enemy_guard(tag) + f" NOT = {{ local_flag = {flag} }}",
                       f'command = {{ type = local_setflag which = {flag} }}\n'
                       f'        command = {{ type = ai which = "aubm/balance1/{tag}_india_front.ai" }}',
                       persistent=True)
        text += _event(9318001 + 2 * index, tag,
                       f"ai = yes local_flag = {flag} NOT = {{ AND = {{ {_enemy_guard(tag)} }} }}",
                       f'command = {{ type = local_clrflag which = {flag} }}\n'
                       '        command = { type = ai which = "aubm/balance1/india_front_standdown.ai" }',
                       persistent=True)
    # Three mutually exclusive fallback ports share a single permanent latch.
    # Recruited/reserve formations are charged once, not free teleporting replacements.
    for index, port in enumerate((750, 761, 765)):
        earlier = " ".join(f"NOT = {{ control = {{ province = {p} data = ITA }} }}" for p in (750, 761, 765)[:index])
        trigger = f'''ai = yes exists = GER exists = ITA ai = ITA exists = ENG
        alliance = {{ country = GER country = ITA }}
        war = {{ country = GER country = ENG }} war = {{ country = ITA country = ENG }}
        NOT = {{ war = {{ country = GER country = ITA }} }}
        NOT = {{ local_flag = aubm_b1_afrika_deployed }}
        control = {{ province = 55 data = GER }}
        control = {{ province = {port} data = ITA }} {earlier}
        manpower = 30 supplies = 6000 oil = 1500 money = 300'''
        commands = f'''command = {{ type = local_setflag which = aubm_b1_afrika_deployed }}
        command = {{ type = manpowerpool value = -30 }}
        command = {{ type = supplies value = -6000 }}
        command = {{ type = oilpool value = -1500 }}
        command = {{ type = money value = -300 }}
        command = {{ type = add_corps which = "Afrika Reserve Corps" value = land where = {port} }}
        command = {{ type = add_division which = "Afrika Panzer Reserve" value = light_armor when = 1 }}
        command = {{ type = add_division which = "Afrika Motorised Reserve" value = motorized when = 1 }}'''
        text += _event(9318020 + index, "GER", trigger, commands, 1940, "july")
    for index, port in enumerate((517, 525)):
        earlier = "NOT = { control = { province = 517 data = FIN } }" if index else ""
        trigger = f'''ai = yes exists = GER exists = FIN ai = FIN exists = SOV
        alliance = {{ country = GER country = FIN }}
        war = {{ country = GER country = SOV }} war = {{ country = FIN country = SOV }}
        NOT = {{ war = {{ country = GER country = FIN }} }}
        NOT = {{ local_flag = aubm_b1_nordland_deployed }}
        control = {{ province = {port} data = FIN }} {earlier}
        manpower = 30 supplies = 5000 money = 250'''
        commands = f'''command = {{ type = local_setflag which = aubm_b1_nordland_deployed }}
        command = {{ type = manpowerpool value = -30 }}
        command = {{ type = supplies value = -5000 }}
        command = {{ type = money value = -250 }}
        command = {{ type = add_corps which = "Nordland Reserve Corps" value = land where = {port} }}
        command = {{ type = add_division which = "Nordland Mountain Reserve 1" value = bergsjaeger when = 10 }}
        command = {{ type = add_division which = "Nordland Mountain Reserve 2" value = bergsjaeger when = 10 }}'''
        text += _event(9318023 + index, "GER", trigger, commands, 1941, "june")
    return text


def transform(files: dict[str, str]):
    """Return full manifest and changed-file records; fail closed on collisions."""
    out = dict(files)
    records = []
    lookup = {key.replace("\\", "/").lower(): key for key in out}
    for required in ("db/events.txt", "db/events/ai/ai_fin.txt", "ai/switch/ita_homeland.ai", "ai/switch/eng_attack.ai"):
        if required not in lookup:
            raise ValueError("Missing installed baseline: " + required)
    loaded = {str(p).replace("\\", "/").lower() for p in parse(files[lookup["db/events.txt"]]).all("event")}
    # These are direct event includes in scenarios/1933.eug, not db/events.txt.
    loaded.update(f"db/events/ai/ai_{tag.lower()}.txt" for tag in ENEMIES)
    event_ids = {str(9318000 + n) for n in range(14)} | {str(9318020 + n) for n in range(5)}
    for key, text in files.items():
        norm = key.replace("\\", "/").lower()
        if norm.startswith("db/events/") and norm.endswith(".txt") and norm != EVENT_PATH.lower():
            # Also inspect inactive source copies without attempting to parse
            # old, unloaded or engine-tolerated legacy syntax unrelated to us.
            for eid in re.findall(r"(?m)^\s*id\s*=\s*(\d+)", text):
                if eid in event_ids:
                    raise ValueError(f"Reserved event ID collision in {key}: {eid}")

    for key, original in files.items():
        norm = key.replace("\\", "/").lower()
        if MARKER in original:
            continue
        text = original
        reasons = []
        if norm == "db/events/ai/ai_fin.txt":
            text = _finland(text)
            reasons.append("Finland retains homeland defence until Soviet war ends")
        if norm.startswith("ai/") and norm.endswith(".ai") and "1914" not in norm:
            basename = norm.rsplit("/", 1)[-1]
            tag = basename[:3].upper()
            node = parse(text)
            if basename[3:4] == "_" and tag in NODES and isinstance(node.get("garrison"), Node):
                for prov, priority in NODES[tag].items():
                    text = _floor(text, ("garrison", "province_priorities", str(prov)), priority)
                reasons.append(tag + " strategic port/theatre garrison priorities retained across switches")
            if norm == "ai/switch/ger_norway_end.ai":
                for prov, priority in PORTS.items():
                    text = _floor(text, ("garrison", "province_priorities", str(prov)), priority)
                reasons.append("Norway occupation garrison after invasion")
            if norm == "ai/switch/ger_russia.ai":
                blocked = parse(text).get("no_exp_forces_to")
                if isinstance(blocked, Node):
                    text = replace(text, [(f.start, f.end, "") for f in blocked.fields if f.value == "FIN"])
                    reasons.append("Remove Finnish expeditionary prohibition during Barbarossa")
            if norm == "ai/switch/ita_homeland.ai":
                text = _set(text, ("garrison", "defend_overseas_beaches"), "yes")
                text = _set(text, ("garrison", "overseas_multiplier"), "0.5")
                text = _set(text, ("garrison", "reserves"), "40")
                reasons.append("Preserve viable overseas defence and nearby reserves after Libya losses")
            if basename.startswith("eng_") and isinstance(node.get("front"), Node):
                front = parse(text).get("front")
                if front.get("recklessness") == "3":
                    text = _set(text, ("front", "recklessness"), "2")
                if front.get("min_attack_odds") is not None and float(front.get("min_attack_odds")) < 1:
                    text = _set(text, ("front", "min_attack_odds"), "1.0")
                if front.get("base_attack_odds") is not None and float(front.get("base_attack_odds")) < 1.2:
                    text = _set(text, ("front", "base_attack_odds"), "1.2")
                reasons.append("British attacks require less speculative odds")
            if basename.startswith("eng_") and isinstance(node.get("invasion"), Node):
                invasion = parse(text).get("invasion")
                if invasion.get("enemy") is not None:
                    text = _floor(text, ("invasion", "enemy"), 1.5)
                if invasion.get("adjacentenemy") is not None:
                    text = _floor(text, ("invasion", "adjacentenemy"), 1.0)
                reasons.append("British landing selection weighs defending reserves")
        if norm in loaded and norm.startswith("db/events/") and norm.endswith(".txt"):
            text, count = _hook_switches(text)
            if count:
                reasons.append(f"{count} stock AI-switch actions preserve active India-front response")
        if text != original:
            out[key] = MARKER + "\n" + text
            parse(out[key])
            records.append({"path": key, "changes": reasons})

    generated = {EVENT_PATH: generated_events()}
    for tag in ENEMIES:
        generated[f"{AI_DIR}/{tag}_india_front.ai"] = MARKER + '''
# Narrow partial switch, only loaded for an AI fighting human India.
# Does not replace diplomacy, target lists, production, existing front priorities,
# historical AI-vs-AI distribution, or fleets. Existing forces must do the work.
garrison = { human_border = 150 }
front = {
    distrib_vs_human = reactive
    panic_ratio_vs_human = 2.0
}
'''
    generated[f"{AI_DIR}/india_front_standdown.ai"] = MARKER + '''
# No anti-India diplomacy/territorial objectives survive peace or alliance.
# Restore conservative, generic human-front settings only; stock files may
# subsequently refine these. No historical target or priority list is cleared.
garrison = { human_border = 0 }
front = { distrib_vs_human = op_defensive panic_ratio_vs_human = 3.0 }
'''
    for key, content in generated.items():
        old_key = lookup.get(key.lower(), key)
        if old_key in out and out[old_key] != content and MARKER not in out[old_key]:
            raise ValueError("Refusing to overwrite foreign content at " + key)
        if out.get(old_key) != content:
            out[old_key] = content
            parse(content)
            records.append({"path": old_key, "changes": ["Hidden, bounded BALANCE1 AI support"]})
    loader_key = lookup["db/events.txt"]
    loader = out[loader_key]
    entry = 'event = "' + EVENT_PATH.replace("/", "\\") + '"'
    if EVENT_PATH.lower() not in loader.lower().replace("\\", "/"):
        out[loader_key] = loader.rstrip() + "\n" + MARKER + "\n" + entry + "\n"
        records.append({"path": loader_key, "changes": ["Register hidden world-AI module once"]})
    return out, records
