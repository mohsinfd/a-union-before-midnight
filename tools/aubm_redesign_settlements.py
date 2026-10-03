"""Staged, target-wide closure of the two generated settlement families.

Not a peace-engine repair: government creation and coalition war mutation still
need native validation. This pass fixes replay/navigation, without inventing a
government, ending a war, or erasing an earned reward.
"""
from __future__ import annotations

import re
from dh_save_spans import Node, parse, replace

FAMILIES = {"46_regional_campaigns.txt", "47_global_campaign_matrix.txt"}
DIRECT = re.compile(r"ind_aubm_(regional|global)_direct_([a-z0-9]+)$")
MARKER = "# REDESIGN_SETTLEMENT_CLOSURE_V1"


def actions(event):
    return [f for f in event.fields if f.key == "action" or (f.key or "").startswith("action_")]


def closed_gate(tag):
    # Recognise prior builds' outcomes too. A second ledger must not reopen a
    # settlement already chosen in the other generated family. A legacy flag
    # alone does NOT prove that an independence/make_puppet command succeeded.
    # Keep recovery possible when a recorded government was never created.
    def recorded(kind):
        return 'OR = { ' + ' '.join(f'flag = ind_aubm_{family}_{kind}_{tag}'
                                   for family in ('regional', 'global')) + ' }'
    target = tag.upper()
    return ('NOT = { OR = { ' + recorded('direct') +
            f' AND = {{ exists = {target} NOT = {{ ispuppet = {target} }} ' + recorded('sovereign') + ' }' +
            f' AND = {{ puppet = {{ country = {target} country = IND }} ' + recorded('protected') + ' } } }')


def add_gate(node, gate):
    current = node.get("trigger")
    if isinstance(current, Node):
        return current.start + 1, current.start + 1, "\n\t\t\t" + gate + "\n"
    return node.start + 1, node.start + 1, "\n\t\ttrigger = { " + gate + " }\n"


def transform(files):
    result = dict(files)
    reviewed = {}
    for path, text in files.items():
        if path.rsplit("/", 1)[-1] not in FAMILIES:
            continue
        edits = []
        for event in parse(text).all("event"):
            if event.get("country") != "IND":
                continue
            found = [(af, c, DIRECT.fullmatch(c.get("which", "")))
                     for af in actions(event) for c in af.value.all("command")
                     if c.get("type") == "setflag" and DIRECT.fullmatch(c.get("which", ""))]
            if not found:
                continue
            if len(found) != 1:
                raise ValueError(f"Ambiguous settlement in {path}: {event.get('id')}")
            direct_action, _, match = found[0]
            family, tag = match.groups()
            eid = int(event.get("id"))
            reviewed[eid] = [{
                "dimension": "settlement_closure", "status": "reviewed",
                "disposition": "rewrite", "target": tag.upper(),
                "method": "authored family-level rule; per-event pattern checked",
                "changes": ["Both ledgers recognise direct rule and actual recorded governments",
                            "Direct administration closes the original choice",
                            "Settlement choices no longer reopen their ledger",
                            "Effect-free human exit remains available"],
                "remaining": ["Release eligibility and reward/cost ordering on government failure",
                              "Legacy settled-only records do not establish a constitutional outcome",
                              "Coalition peace scope and foreign replies",
                              "Native engine playtest"],
                "engine_tested": False,
            }]
            if MARKER in text[event.start:event.end]:
                continue
            gate = closed_gate(tag)
            edits.append((event.start + 1, event.start + 1, "\n\t" + MARKER + "\n"))
            for af in actions(event):
                a = af.value
                commands = a.all("command")
                # Do not block a genuinely effect-free exit with terminal gates.
                if not commands:
                    continue
                edits.append(add_gate(a, gate))
                terminal = any(c.get("type") == "setflag" and
                               c.get("which") in {
                                   f"ind_aubm_{family}_{kind}_{tag}"
                                   for kind in ("direct", "protected", "sovereign")}
                               for c in commands)
                if terminal:
                    for cf in a.fields:
                        c = cf.value
                        if cf.key == "command" and isinstance(c, Node) and c.get("type") == "event" and c.get("where") == "IND":
                            # Upkeep is effectful, not navigation. Only the two
                            # verified original ledger return IDs are removed.
                            if c.get("which") in {"9282201", "9282300"}:
                                edits.append((cf.start, cf.end, ""))
            a = direct_action.value
            addition = f'\n\t\tcommand = {{ type = setflag which = ind_aubm_{family}_settled_{tag} }}\n'
            for kind in ("current",):
                key = f"ind_aubm_{family}_{kind}_{tag}"
                if not any(c.get("type") == "clrflag" and c.get("which") == key for c in a.all("command")):
                    addition += f'\t\tcommand = {{ type = clrflag which = {key} }}\n'
            edits.append((a.end - 1, a.end - 1, addition))
            if not any(not af.value.all("command") for af in actions(event)):
                edits.append((event.end - 1, event.end - 1,
                              '\n\taction = { trigger = { ai = no } name = "Not now - keep current orders" }\n'))
        result[path] = replace(text, edits)
    return result, reviewed
