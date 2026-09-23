"""Retire bounded navigation loops without retiring real campaign choices.

Run after crisis/cooperation stages. No IDs, rewards, wars or commitments are
created. Five secondary ledgers are removable only while their 35 mirror flags
have no condition readers in the supplied corpus. All old IDs remain callable
as harmless close pages. Actual Japan operational milestones remain manual:
this stage changes access and return links, not their reward lifecycle.
"""
from __future__ import annotations
import json
from dh_save_spans import Node, parse, replace, walk

MARKER = "# AUBM_STAGED_NAVIGATION_V1"
ROOT_ID = 9281001
BOARDS = (9289500, 9289540, 9289580, 9289620, 9289660)
SECONDARY_LEDGERS = (9289503, 9289543, 9289583, 9289623, 9289663)
RETIRED_IDS = (9289499, *BOARDS, *SECONDARY_LEDGERS, 9281002, 9281003, 9281004)
WAR_REVIEWS = (9289525, 9289565, 9289605, 9289653, 9289685)
JAPAN_PAGES = (9289645, 9289646, 9289647, 9289648)
REVIEWED_IDS = (*RETIRED_IDS, ROOT_ID, 9281012, 9281013, *WAR_REVIEWS, *JAPAN_PAGES)
SOURCES = {"32_national_consolidation.txt", "51_bespoke_route_arcs.txt"}
JAPAN_CURRENT = ("exists = IND exists = JAP NOT = { ispuppet = IND } "
    "NOT = { war = { country = IND country = JAP } } "
    "OR = { alliance = { country = IND country = JAP } "
    "AND = { flag = ind_aubm_commitment_japan flag = ind_aubm_jp_partnership "
    "NOT = { flag = ind_aubm_commitment_allied } "
    "NOT = { flag = ind_aubm_commitment_german } "
    "NOT = { flag = ind_aubm_commitment_soviet } } }")
ROOT_CURRENT = ("ai = no exists = IND NOT = { ispuppet = IND } "
                "OR = { year = 1937 atwar = yes flag = ind_aubm_unrestricted_sandbox }")


def actions(event):
    return [f for f in event.fields if f.key == "action" or (f.key or "").startswith("action_")]


def body(text, node):
    return "\n" + text[node.start + 1:node.end - 1].strip() + "\n"


def nav(label, destination, gate="ai = no"):
    return ('action = { name = ' + json.dumps(label) + ' trigger = { ' + gate +
            ' } ai_chance = 0 command = { type = event which = ' + str(destination) +
            ' where = IND when = 1 } }')


def close_action():
    return 'action = { name = "Close - keep current orders" trigger = { ai = no } ai_chance = 0 }'


def shell(eid, title, desc, picture, aa, decision=None):
    fields = [f"event = {{ id = {eid} country = IND random = no persistent = yes",
              MARKER, "name = " + json.dumps(title), "desc = " + json.dumps(desc),
              "style = 2 picture = " + json.dumps(picture)]
    if decision:
        fields += ["decision = { " + decision + " }",
                   "decision_trigger = { " + decision + " }",
                   "trigger = { " + decision + " }",
                   'decision_desc = "Open a review without changing policy or declaring war. Closing a page is free. Binding choices retain their own safeguards."',
                   "date = { day = 0 month = january year = 1933 } offset = 3",
                   "deathdate = { day = 29 month = december year = 1964 }"]
    return "\n".join([*fields, *aa, "}"])


def ensure_navigation_only(event):
    for af in actions(event):
        if any(c.get("type") != "event" for c in af.value.all("command")):
            raise ValueError("Navigation page acquired a real effect: " + event.get("id"))


def verify_dead_mirrors(files, indexed):
    mirror_flags = set()
    for eid in SECONDARY_LEDGERS:
        if eid not in indexed:
            continue
        event = indexed[eid][1]
        for af in actions(event):
            for c in af.value.all("command"):
                name = c.get("which", "")
                if c.get("type") != "setflag" or not name.startswith("ind_aubm_bespoke_secondary_"):
                    raise ValueError("Secondary ledger acquired a real effect: " + str(eid))
                mirror_flags.add(name)
    for path, text in files.items():
        if "ind_aubm_bespoke_secondary_" not in text:
            continue
        for node in walk(parse(text)):
            for f in node.fields:
                if f.key == "flag" and f.value in mirror_flags:
                    raise ValueError("Secondary ledger now has a live reader: " + f.value)
    return mirror_flags


def root(event):
    ensure_navigation_only(event)
    return shell(ROOT_ID, "Diplomacy and Campaigns",
        "Choose the matter India needs to address now: its partners, a possible opponent, or an active front. "
        "These reviews do not choose a national route or commit troops; binding decisions remain on their own pages.",
        event.get("picture", "aubm_v4_grand_strategy"),
        [close_action(), nav("Treaties, alliances and peaceful withdrawal", 9281910, ROOT_CURRENT),
         nav("Review a possible opponent", 9281012, ROOT_CURRENT),
         nav("Campaign results and settlements", 9281913, ROOT_CURRENT),
         nav("Joint operations with Japan", 9289645, ROOT_CURRENT + " " + JAPAN_CURRENT)], ROOT_CURRENT)


def revise_existing(text, eid):
    event = parse(text).get("event")
    if MARKER in text:
        return text, []
    changes, cuts = [], []
    for af in actions(event):
        action = af.value
        removed = []
        for cf in action.fields:
            if cf.key != "command" or cf.value.get("type") != "event":
                continue
            target = int(cf.value.get("which"))
            back = target in RETIRED_IDS or (
                eid in (*JAPAN_PAGES, 9281013) and target in (9289645, ROOT_ID))
            self_loop = eid == 9281013 and target == eid
            duplicate = eid == 9281012 and target == 9281913
            if back or self_loop or duplicate:
                changes.append((cf.start, cf.end, ""))
                removed.append(cf)
                cuts.append(dict(source=eid, target=target))
        if removed and len(removed) == len(action.all("command")):
            # Free return becomes a free close, never another queued popup.
            f = action.field("name")
            changes.append((f.value_start, f.end, '"Close this review"'))
        if eid in JAPAN_PAGES and action.all("command") and not removed:
            gate = action.get("trigger")
            if gate is None:
                changes.append((action.start + 1, action.start + 1,
                                "\n trigger = { " + JAPAN_CURRENT + " }\n"))
            else:
                # Preserve chapter/transaction predicates verbatim. In
                # particular, the relief gateway must not advertise access
                # broader than its still-unreviewed paid callback permits.
                old = body(text, gate)
                changes.append((gate.start, gate.end, "{ " + JAPAN_CURRENT + " " + old + " }"))
    if eid == 9289645:
        tr = event.get("trigger")
        if tr:
            changes.append((tr.start, tr.end, "{ year = 1937 " + JAPAN_CURRENT + " }"))
        f = event.field("name")
        changes.append((f.value_start, f.end, '"Joint Campaigns with Japan"'))
        f = event.field("desc")
        changes.append((f.value_start, f.end,
            '"Review operational milestones and a possible Caucasus relief convoy while India has a current Japanese alliance or compact. Each chapter retains its battlefield requirements; opening it records no victory or policy change."'))
    if eid == 9281012:
        f = event.field("name")
        changes.append((f.value_start, f.end, '"Review a Possible Opponent"'))
        f = event.field("desc")
        changes.append((f.value_start, f.end,
            '"Choose a great power, a regional campaign or the optional unrestricted catalogue. This page declares no war; the existing opponent review still checks alliances and binding commitments before a declaration."'))
    if eid in WAR_REVIEWS:
        f = event.field("name")
        changes.append((f.value_start, f.end, '"Review India\'s War Options"'))
    # Callback-only pages remain callback-only. No new decision blocks here.
    changes.append((event.end - 1, event.end - 1, "\n" + MARKER + "\n"))
    return replace(text, changes), cuts


def transform(files: dict[str, str]):
    output, records = dict(files), {}
    indexed = {}
    for path, text in files.items():
        if str(path).replace("\\", "/").rsplit("/", 1)[-1] not in SOURCES:
            continue
        for f in parse(text).fields:
            if f.key == "event" and isinstance(f.value, Node):
                indexed[int(f.value.get("id"))] = (path, f.value)
    mirrors = verify_dead_mirrors(files, indexed)
    for path, text in files.items():
        if str(path).replace("\\", "/").rsplit("/", 1)[-1] not in SOURCES:
            continue
        edits = []
        for f in parse(text).fields:
            if f.key != "event" or not isinstance(f.value, Node): continue
            eid = int(f.value.get("id"))
            if eid not in REVIEWED_IDS: continue
            event, raw = f.value, text[f.start:f.end]
            cuts = []
            if eid in RETIRED_IDS:
                if eid not in SECONDARY_LEDGERS: ensure_navigation_only(event)
                cuts = [dict(source=eid, target=int(c.get("which"))) for a in actions(event)
                        for c in a.value.all("command") if c.get("type") == "event"]
                revised = shell(eid, "This Review Is Closed",
                    "This older navigation page is no longer needed. Use Diplomacy and Campaigns or the available partner decision when there is a concrete choice to make. Closing changes nothing.",
                    event.get("picture", "aubm_v4_grand_strategy"), [close_action()])
            elif eid == ROOT_ID:
                cuts = [dict(source=eid, target=int(c.get("which"))) for a in actions(event)
                        for c in a.value.all("command") if c.get("type") == "event" and int(c.get("which")) == 9289499]
                revised = root(event)
            else:
                revised, cuts = revise_existing(raw, eid)
            edits.append((f.start, f.end, revised))
            records[eid] = [dict(dimension="navigation", status="reviewed", path=path,
                retired=eid in RETIRED_IDS, retired_links=cuts,
                changes=("Retired navigation/manual mirror recording to free close" if eid in RETIRED_IDS else
                         "Current-state gateway and/or non-recursive close links"),
                mirror_writes_retired=(len(mirrors)//5 if eid in SECONDARY_LEDGERS else 0),
                caveats=["Native UI testing pending", "Actual partner, war, reward and Japan chapter milestones remain in their existing nodes",
                         "Other campaign indices and route reward eligibility, including paid Caucasus relief, remain outside this bounded pass"])]
        output[path] = replace(text, edits)
    return output, records
