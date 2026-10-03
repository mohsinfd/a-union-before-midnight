"""Finish the bounded Japan operations/paid Caucasus lifecycle in staging.

Run after navigation. Reuses 9289645..52 and the existing cabinet link; no
new IDs, modules or recurring monitors. Dispatch owns both queued steps: GER
delivery at2 days and IND settlement at4 days. A proven German receipt is
never refunded, even after politics or control change. These delays/provenance
checks are script contracts, not native event-queue verification.
"""
from __future__ import annotations
import json
from dh_save_spans import Node, parse, replace, walk
from aubm_redesign_navigation import JAPAN_CURRENT
from aubm_redesign_campaign_access import predicate_roots
from aubm_redesign_diplomacy import COMPACTS
from aubm_redesign_cooperation import INDEPENDENT, partner

MARKER = "# AUBM_STAGED_ROUTE_FINISH_V1"
BASES = dict(allied=9289500, german=9289540, soviet=9289580,
             japan=9289620, sovereign=9289660)
SELECTORS = {9283210 + i: family for i, family in enumerate(BASES)}
FOCUS_IDS = {base + n: family for family, base in BASES.items()
             for n in (2, *range(4, 25))}
FOCUS_IDS.update(SELECTORS)
EVENT_IDS = (*range(9289645, 9289653), 9281001, *FOCUS_IDS)
FOCUS_MARKER = '# AUBM_STAGED_CURRENT_FOCUS_V1'
OLD_ACCESS_FLAGS = {"ind_aubm_route_japan", "ind_aubm_bespoke_route_contract_alpha23"}
PENDING = "ind_stage_japan_caucasus_delivery_pending"
HANDLED = "ind_aubm_japan_caucasus_relief_handled"
DISPATCHED = "ind_aubm_japan_caucasus_relief_dispatched"
DECLINED = "ind_aubm_japan_caucasus_relief_declined"
RECEIVED = "ger_aubm_indian_caucasus_relief_received"
DELIVERED = "ind_aubm_japan_caucasus_relief_delivered"
PARTNER = JAPAN_CURRENT + " NOT = { ispuppet = JAP } " + ' '.join(
    'NOT = { flag = ' + flag + ' }' for family, flags in COMPACTS.items()
    if family != 'japan' for flag in flags)
CORRIDOR = ("year = 1937 " + PARTNER + " exists = GER NOT = { ispuppet = GER } "
    "NOT = { war = { country = IND country = GER } } "
    "war = { country = IND country = SOV } war = { country = GER country = SOV } "
    "control = { province = 163 data = GER } control = { province = 713 data = IND } "
    "OR = { control = { province = 709 data = IND } control = { province = 706 data = IND } }")
CAN_DISPATCH = (CORRIDOR + " " + " ".join("NOT = { flag = " + f + " }"
                for f in (HANDLED, PENDING, RECEIVED, DELIVERED)))
PAID_PROOF = " ".join("flag = " + f for f in (HANDLED, DISPATCHED, PENDING))
CAN_DELIVER = (PAID_PROOF + " " + CORRIDOR + " NOT = { flag = " + RECEIVED + " } "
               "NOT = { flag = " + DELIVERED + " }")
ACK = PAID_PROOF + " flag = " + RECEIVED + " NOT = { flag = " + DELIVERED + " }"
REFUND = PAID_PROOF + " NOT = { flag = " + RECEIVED + " } NOT = { flag = " + DELIVERED + " }"
UNHANDLED_PLAYER_FAMILIES = (
    "Other coalition, revisionist settlement and political programme opportunities require separate per-family review",
)


def actions(event):
    return [f for f in event.fields if f.key == "action" or (f.key or "").startswith("action_")]


def inside(text, node):
    return "\n" + text[node.start+1:node.end-1].strip() + "\n"


def set_fields(text, fields):
    event = parse(text).get("event")
    edits, extras = [], []
    for key, value in fields.items():
        found = [f for f in event.fields if f.key == key]
        if len(found) > 1: raise ValueError("Duplicate route-finish field: " + key)
        if found:
            f = found[0]
            edits.append((f.start, f.end, "")) if value is None else edits.append((f.value_start, f.end, value))
        elif value is not None: extras.append(f"\n {key} = {value}\n")
    if extras: edits.append((event.end-1, event.end-1, "".join(extras)))
    return replace(text, edits)


def command(kind, which=None, value=None):
    return "command = { type = " + kind + (" which = " + which if which else "") + (f" value = {value}" if value is not None else "") + " }"


def action(name, guard, commands=(), chance=100):
    return ("action = { name = " + json.dumps(name) + " trigger = { " + guard +
            f" }} ai_chance = {chance}\n" + "\n".join(commands) + "\n}")


def rewrite_actions(text, aa):
    event = parse(text).get("event")
    edits = [(f.start, f.end, "") for f in actions(event)]
    edits.append((event.end-1, event.end-1, "\n" + "\n".join(aa) + "\n"))
    return replace(text, edits)


def prune_access(text):
    event = parse(text).get("event")
    edits = []
    for root in predicate_roots(event):
        for node in walk(root):
            for f in node.fields:
                if f.key == "flag" and f.value in OLD_ACCESS_FLAGS:
                    # A factual tautology keeps any surrounding AND/OR block
                    # well-formed; these flags are positive source conjuncts.
                    edits.append((f.start, f.end, "exists = IND"))
    return replace(text, edits)


def guarded_action_edits(text, event, eid):
    edits = []
    for af in actions(event):
        a = af.value
        commands = a.all("command")
        if not commands: continue
        if eid == 9281001:
            if not any(c.get("type") == "event" and c.get("which") == "9289645" for c in commands): continue
            context = PARTNER
        elif eid == 9289652:
            context = PARTNER + " " + inside(text, event.get("trigger"))
        else:
            # Close any remaining old Back edges if the transform is exercised
            # independently; they must never queue a route board again.
            back = [f for f in a.fields if f.key == "command" and f.value.get("type") == "event"
                    and f.value.get("which") in ("9289620", "9289645")]
            if len(back) == len(commands):
                edits += [(f.start, f.end, "") for f in back]
                f = a.field("name"); edits.append((f.value_start, f.end, '"Close this review"'))
                continue
            context = "year = 1937 " + PARTNER
            if eid == 9289648 and any(c.get("type") == "event" and c.get("which") == "9289649" for c in commands):
                context = CAN_DISPATCH
        tr = a.get("trigger")
        if tr is None:
            edits.append((a.start+1, a.start+1, "\n trigger = { " + context + " }\n"))
        else:
            edits.append((tr.start, tr.end, "{ " + context + " " + inside(text, tr) + " }"))
    return edits


def rewrite(text, eid):
    if MARKER in text:
        return text
    text = prune_access(text)
    event = parse(text).get("event")
    if eid == 9289649:
        original = {a.value.get("name"): a.value for a in actions(event)}
        paid = original.get("Dispatch one relief convoy: -1200 supplies/-500 oil")
        if paid is None: raise ValueError("Caucasus paid action not recognized")
        debit = [(c.get("type"), c.get("value")) for c in paid.all("command") if c.get("type") in ("supplies", "oilpool")]
        if debit != [("supplies", "-1200"), ("oilpool", "-500")]: raise ValueError("Caucasus price drift")
        aa = [action("Send convoy: 1200 supplies, 500 oil", CAN_DISPATCH + " supplies = 1200 oil = 500", [
            command("supplies", value=-1200), command("oilpool", value=-500),
            command("setflag", HANDLED), command("setflag", DISPATCHED), command("setflag", PENDING),
            "command = { type = event which = 9289650 where = GER when = 2 }",
            "command = { type = event which = 9289651 where = IND when = 4 }"]),
            action("Not now - keep the convoy option open", "ai = no", chance=0),
            action("Decline this convoy - preserve Indian stocks", CAN_DISPATCH,
                   [command("setflag", HANDLED), command("setflag", DECLINED)], chance=0)]
        text = rewrite_actions(text, aa)
        text = set_fields(text, {"trigger": "{ " + CAN_DISPATCH + " }", "persistent": "yes",
            "desc": json.dumps("A convoy through Baku can support Germany's Soviet front. Pay 1200 supplies and 500 oil; delivery is checked after two days. Four days after dispatch, India records a proven receipt or recovers the full cost if no delivery occurred. Germany receives 900 supplies and 350 oil.")})
    elif eid == 9289650:
        aa = [action("Receive 900 supplies and 350 oil", CAN_DELIVER,
                     [command("supplies", value=900), command("oilpool", value=350), command("setflag", RECEIVED)]),
              action("The convoy cannot be unloaded", "NOT = { AND = { " + CAN_DELIVER + " } }")]
        text = rewrite_actions(text, aa)
        text = set_fields(text, {"trigger": None, "one_action": None, "persistent": "yes",
            "name": json.dumps("An Indian Convoy at the Caucasus Front"),
            "desc": json.dumps("A paid Indian convoy is due at the Caucasus front. It can unload only while the corridor, Soviet war and current non-hostile partners remain valid. If it cannot unload, India's scheduled review returns the cargo budget; no German stocks are granted.")})
    elif eid == 9289651:
        aa = [action("Confirm delivery and Indian coalition credit", ACK,
                     [command("setflag", DELIVERED), command("setflag", "ind_aubm_coalition_credit"), command("clrflag", PENDING)]),
              action("No delivery: return 1200 supplies and 500 oil", REFUND,
                     [command("supplies", value=1200), command("oilpool", value=500),
                      command("clrflag", PENDING), command("clrflag", DISPATCHED), command("clrflag", HANDLED)]),
              action("This convoy has already been accounted for", "NOT = { OR = { AND = { " + ACK + " } AND = { " + REFUND + " } } }")]
        text = rewrite_actions(text, aa)
        text = set_fields(text, {"trigger": None, "one_action": None, "persistent": "yes",
            "name": json.dumps("The Caucasus Convoy Account"),
            "desc": json.dumps("Delhi checks the convoy's receipt. A confirmed delivery earns the existing coalition acknowledgement even if politics or the front have since changed. If nothing reached Germany, the full dispatch cost returns to Indian stocks and a fresh attempt remains possible.")})
    else:
        text = replace(text, guarded_action_edits(text, event, eid))
        if eid in (9289645, 9289652):
            event = parse(text).get("event")
            tr = event.get("trigger")
            text = set_fields(text, {"trigger": "{ " + PARTNER + " " + (inside(text, tr) if tr else "year = 1937") + " }"})
        if eid == 9289652:
            event = parse(text).get("event")
            valid = inside(text, event.get("trigger"))
            paid = next(a.value for a in actions(event) if a.value.all("command"))
            updates = [(event.end-1, event.end-1, "\n" + action(
                "The campaign recognition is not available now", "NOT = { AND = { " + valid + " } }") + "\n")]
            if paid.get("ai_chance") is None:
                updates.append((paid.start+1, paid.start+1, "\n ai_chance = 100\n"))
            text = replace(text, updates)
            text = set_fields(text, {"one_action": None})
    event = parse(text).get("event")
    return replace(text, [(event.end-1, event.end-1, "\n" + MARKER + "\n")])


def canon(value):
    return tuple((f.key, canon(f.value)) for f in value.fields) if isinstance(value, Node) else value


def live(tag):
    return (f'exists = {tag} NOT = {{ ispuppet = {tag} }} '
            f'NOT = {{ war = {{ country = IND country = {tag} }} }}')


def alliance(tag):
    return f'alliance = {{ country = IND country = {tag} }}'


def current_family(family):
    """Binding compacts exclude other doctrines; actual coalition allies may overlap.

    Exile continuation retains a surviving fallback, never a nonexistent partner.
    India can still choose only one primary war achievement (authored global cap).
    """
    if family == 'sovereign': return 'exists = IND ' + INDEPENDENT
    no_other = ' '.join('NOT = { flag = ' + flag + ' }'
        for other, flags in COMPACTS.items() if other != family for flag in flags)
    compact = 'OR = { ' + ' '.join('flag = ' + flag for flag in COMPACTS[family]) + ' }'
    if family == 'allied':
        # The naval compact is American; the other authored treaties are
        # British. A generic old commitment uses its explicit partner record,
        # with Britain as the authored default only when neither was selected.
        default_eng = ('AND = { flag = ind_aubm_commitment_allied '
            'NOT = { flag = ind_aubm_allied_partner_usa } }')
        british = 'OR = { ' + default_eng + ' ' + ' '.join('flag = ind_v4a_treaty_' + t
            for t in ('commonwealth','formal_alliance','cobelligerent')) + ' }'
        american = ('OR = { flag = ind_v4a_treaty_naval_compact AND = { '
            'flag = ind_aubm_commitment_allied flag = ind_aubm_allied_partner_usa } }')
        choices = [f'AND = {{ {live(tag)} OR = {{ {alliance(tag)} {record} }} }}'
                   for tag, record in (('ENG',british),('USA',american))]
    else:
        primary, fallback = {'german': ('GER', 'ITA'), 'soviet': ('SOV', 'CHC'),
                             'japan': ('JAP', 'SIA')}[family]
        choices = [f'AND = {{ {live(primary)} OR = {{ {alliance(primary)} {compact} }} }}',
                   f'AND = {{ NOT = {{ exists = {primary} }} {live(fallback)} '
                   f'OR = {{ {alliance(fallback)} {compact} }} }}']
    return 'exists = IND NOT = { ispuppet = IND } ' + no_other + ' OR = { ' + ' '.join(choices) + ' }'


CURRENT = {family: current_family(family) for family in BASES}
OLD_SOV = 'OR = { flag = ind_aubm_route_soviet AND = { flag = ind_aubm_route_sovereign flag = ind_aubm_socialist_autonomous } }'
OLD_INDEPENDENT = 'AND = { flag = ind_aubm_route_sovereign NOT = { flag = ind_aubm_socialist_autonomous } }'


def substitute_focus(text, family, relationship_pattern=None):
    """Replace whole predicates, including under NOT; never erase negated flags.

    These substitutions touch only predicates. The contract EFFECT is deliberately
    retained: legacy rewards use NOT-contract to prevent duplicate achievement.
    """
    ev = parse(text).get('event')
    patterns = {canon(parse(OLD_SOV).fields[0].value): CURRENT['soviet'],
                canon(parse(OLD_INDEPENDENT).fields[0].value): CURRENT['sovereign']}
    if relationship_pattern is not None: patterns[relationship_pattern] = CURRENT[family]
    for tag, short in (('SIA', 'siam'), ('CHI', 'china')):
        old = ('OR = { flag = ind_v3_delhi_pact ' + alliance(tag) +
               ' AND = { flag = ind_v42_delhi_pact_consultative flag = ind_v42_' + short + '_accepts_delhi_pact } }')
        patterns[canon(parse(old).fields[0].value)] = partner(tag)
    edits = []
    def visit(node):
        for f in node.fields:
            if isinstance(f.value, Node):
                match = patterns.get(canon(f.value))
                if match is not None and f.key in ('AND', 'OR'):
                    edits.append((f.start, f.end, 'AND = { ' + match + ' }'))
                else: visit(f.value)
            elif f.key == 'flag' and f.value in ('ind_aubm_bespoke_route_contract_alpha23',
                                                'ind_aubm_wartime_framework'):
                edits.append((f.start, f.end, 'exists = IND'))
            elif f.key == 'flag' and f.value in {'ind_aubm_route_' + k for k in BASES}:
                mode = f.value.removeprefix('ind_aubm_route_')
                edits.append((f.start, f.end, 'AND = { ' + CURRENT[mode] + ' }'))
    for root in predicate_roots(ev): visit(root)
    return replace(text, edits)


def guard_all_effects(text, guard):
    ev = parse(text).get('event')
    edits = []
    for af in actions(ev):
        a = af.value
        if not a.all('command'): continue
        tr = a.get('trigger')
        value = '{ ' + guard + (inside(text, tr) if tr else '') + ' }'
        edits.append((tr.start, tr.end, value) if tr else
                     (a.start+1, a.start+1, '\n trigger = ' + value + '\n'))
    return replace(text, edits)


def rewrite_focus(text, eid, relationship_pattern):
    if FOCUS_MARKER in text: return text
    family = FOCUS_IDS[eid]
    text = substitute_focus(text, family, relationship_pattern)
    ev = parse(text).get('event')
    offset = eid - BASES[family]
    if eid in SELECTORS or 4 <= offset <= 20:
        # Keep each local focus, actual war/control/victory milestone, stock
        # reserve, terminal flag and reward cap. Only real choice roots become
        # manual: activation/intermediate/earned rewards still resolve normally.
        root = inside(text, ev.get('trigger'))
        text = guard_all_effects(text, root)
        if eid in SELECTORS or offset == 4 or 13 <= offset <= 16:
            text = set_fields(text, {'persistent': 'yes', 'decision': '{ ai = no ' + root + ' }',
                'decision_trigger': '{ ' + root + ' }', 'date': None, 'offset': None,
                'deathdate': None, 'one_action': None})
            ev = parse(text).get('event')
            text = replace(text, [(ev.end-1, ev.end-1, '\n' +
                action('Not now - keep this choice open', 'ai = no', chance=0) + '\n')])
    else:
        pending = 'ind_aubm_bespoke_partner_response_' + family + '_pending'
        done = 'ind_aubm_bespoke_partner_response_' + family + '_done'
        proof = f'flag = {pending} NOT = {{ flag = {done} }}'
        valid = proof + ' ' + CURRENT[family]
        if offset in (2, 21):
            tag = ev.get('country')
            valid += ' ' + (partner(tag) if family == 'sovereign' else live(tag))
            if offset == 21 and family in ('german', 'soviet', 'japan'):
                # Authored fallback dispatch requires this actual alliance;
                # it must still hold when the foreign response is chosen.
                valid += ' ' + alliance(tag)
        text = guard_all_effects(text, valid)
        # Explicit invalidation consumes only its owned request, not a focus,
        # reward milestone or payment; stale duplicate calls do nothing.
        absent = [command('clrflag', pending), command('setflag', done),
                  command('setflag', 'ind_aubm_bespoke_partner_response_' + family + '_absent')]
        ev = parse(text).get('event')
        text = replace(text, [(ev.end-1, ev.end-1, '\n' + action(
            'The requested cooperation is no longer available',
            proof + ' NOT = { AND = { ' + valid + ' } }', absent) + '\n' + action(
            'This request has already been settled', 'NOT = { AND = { ' + proof + ' } }') + '\n')])
        text = set_fields(text, {'trigger': None, 'one_action': None, 'decision': None,
                                'decision_trigger': None, 'persistent': 'yes'})
    ev = parse(text).get('event')
    return replace(text, [(ev.end-1, ev.end-1, '\n' + FOCUS_MARKER + '\n')])


def transform(files: dict[str, str]):
    output, records = dict(files), {}
    # The same authored relationship expressions also guard conditional request
    # commands. Capture the whole expression once so negated invalidations stay
    # the logical complement, rather than deleting historical flag leaves.
    relation_patterns = {}
    for text in files.values():
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            if eid not in {b + 4 for b in BASES.values()} or FOCUS_MARKER in text[ev.start:ev.end]: continue
            family = FOCUS_IDS[eid]
            for f in ev.get('trigger').fields:
                if isinstance(f.value, Node):
                    flags = [ff.value for n in walk(f.value) for ff in n.fields if ff.key == 'flag']
                    if 'ind_aubm_commitment_' + family in flags:
                        relation_patterns[family] = canon(f.value)
    for path, text in files.items():
        if not any(str(eid) in text for eid in EVENT_IDS): continue
        edits = []
        for f in parse(text).fields:
            if f.key != "event" or not isinstance(f.value, Node): continue
            eid = int(f.value.get("id"))
            if eid not in EVENT_IDS: continue
            if eid in records: raise ValueError("Duplicate Japan route-finish event: " + str(eid))
            raw = text[f.start:f.end]
            edits.append((f.start, f.end, rewrite_focus(raw, eid, relation_patterns.get(FOCUS_IDS[eid]))
                          if eid in FOCUS_IDS else rewrite(raw, eid)))
            records[eid] = [dict(dimension="route_finish", status="reviewed", path=path,
                changes=("Current relationship focus, optional local objectives and guarded partner replies; authored effects and earned milestones preserved"
                         if eid in FOCUS_IDS else "Current Japan relationship replaces route/contract access; paid receipt and one-time settlement proof"),
                dispatch_cost={"supplies":1200, "oil":500} if eid == 9289649 else None,
                remaining=["Native callback ordering, country disappearance and stock delivery require engine testing",
                    "Same-ID legacy duplicate callbacks have no independent generation number; tokens prevent unpaid/double rewards",
                    "Remaining coalition/settlement programme families need separate review"])]
        output[path] = replace(text, edits)
    missing = set(range(9289645, 9289653)) - set(records)
    if missing: raise ValueError("Japan operations family incomplete: " + str(sorted(missing)))
    missing = set(FOCUS_IDS) - set(records)
    if missing: raise ValueError('Current-focus family incomplete: ' + str(sorted(missing)))
    return output, records
