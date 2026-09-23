"""Bounded, PURE authored-source diplomatic corrections for staged review.

transform({path: text}) -> (new mapping, {event_id: [review records]}).
Input is authored mod/db/events text, BEFORE the B1 cleanup compiler. No file
I/O, installation, engine execution, new event IDs, global routes or chains.
Records describe script corrections, never native-engine certification.
Repeated application is idempotent. All changed effect-bearing action keys are
reported; unknown multi-partner alliance transactions are explicitly unresolved.
"""
from __future__ import annotations

from dh_save_spans import Node, parse, replace

MARKER = '# AUBM_STAGED_DIPLOMACY_V1'
# Only explicitly reviewed, user-invoked menus/request roots can gain a free
# Cancel. A queued transaction reply must complete or release its own pending
# record, not silently consume its only delivery.
SAFE_CANCEL_IDS = {9281200, 9281135, 9281914, 9281140, 9281910, 9281934}
TREATIES = ('commonwealth', 'naval_compact', 'formal_alliance', 'cobelligerent')
NO_TREATY = ' '.join('NOT = { flag = ind_v4a_treaty_' + t + ' }' for t in TREATIES)
JP_LIVE = ('exists = IND exists = JAP flag = ind_aubm_jp_partnership '
           'NOT = { flag = ind_aubm_jp_rupture } '
           'NOT = { war = { country = IND country = JAP } } '
           'NOT = { ispuppet = IND } NOT = { ispuppet = JAP } '
           'OR = { NOT = { participant = { country = IND value = 4 } } '
           'alliance = { country = IND country = JAP } }')
JP_PENDING = 'flag = ind_aubm_jp_seniority_review_pending ' + JP_LIVE
ALLIED_PROPOSAL = {
    9281201: 'commonwealth', 9281202: 'naval_compact',
    9281203: 'formal_alliance', 9281204: 'cobelligerent',
    **{i: 'commonwealth' for i in range(9281205, 9281208)},
    **{i: 'naval_compact' for i in range(9281208, 9281211)},
    **{i: 'formal_alliance' for i in range(9281211, 9281214)},
    **{i: 'cobelligerent' for i in range(9281214, 9281217)},
}
COMPACTS = {
    'allied': ['ind_aubm_commitment_allied'] + ['ind_v4a_treaty_' + p for p in TREATIES],
    'german': ['ind_aubm_commitment_german', 'ind_gc_formal_axis', 'ind_gc_cobelligerent'],
    'soviet': ['ind_aubm_commitment_soviet', 'ind_v4_sov_equal_compact', 'ind_v4_sov_supervised_compact'],
    'japan': ['ind_aubm_commitment_japan', 'ind_aubm_jp_partnership'],
}


def actions(event):
    return [f for f in event.fields if f.key == 'action' or
            (f.key or '').startswith('action_')]


def gate(node, predicate):
    t = node.get('trigger')
    if isinstance(t, Node):
        return t.start + 1, t.start + 1, '\n ' + predicate + '\n'
    return node.start + 1, node.start + 1, '\n trigger = { ' + predicate + ' }\n'


def fallback(valid, cleanup='', name='Close the obsolete proposal'):
    return ('\n action = { trigger = { NOT = { AND = { ' + valid +
            ' } } } ai_chance = 100 name = "' + name + '"\n' + cleanup + '\n }\n')


def allied_live(proposal):
    partner = 'USA' if proposal == 'naval_compact' else 'ENG'
    return ('flag = ind_aubm_diplomatic_negotiation_pending '
            'flag = ind_aubm_negotiation_allied flag = ind_v4a_proposal_' + proposal +
            ' exists = IND exists = ' + partner +
            ' NOT = { ispuppet = IND } NOT = { ispuppet = ' + partner + ' } '
            'NOT = { participant = { country = IND value = 4 } } '
            'NOT = { war = { country = IND country = ' + partner + ' } } '
            'NOT = { flag = ind_aubm_commitment_german } '
            'NOT = { flag = ind_aubm_commitment_soviet } '
            'NOT = { flag = ind_aubm_commitment_japan } '
            'NOT = { flag = ind_v4a_allied_framework_settled } ' + NO_TREATY +
            (' NOT = { atwar = IND }' if proposal == 'formal_alliance' else ''))


def transform(files: dict[str, str]):
    """Return independent output and auditable per-action records; never write."""
    output, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            event = ef.value
            eid = int(event.get('id'))
            raw = text[ef.start:ef.end]
            records = []
            if MARKER in raw:
                reviews[eid] = [{'status': 'ALREADY_APPLIED', 'actions': [], 'path': path}]
                continue
            # Work in event-local coordinates so independent edits cannot drift.
            ev = parse(raw).get('event')
            changes, extras, join_guards = [], [], {}

            def record(keys, detail, status='CORRECTED_SCRIPT'):
                records.append({'status': status, 'actions': list(keys),
                                'detail': detail, 'path': path})

            for af in actions(ev):
                a = af.value
                joins = [c for c in a.all('command') if c.get('type') == 'alliance']
                if ev.get('country') == 'IND' and joins:
                    partners = {c.get('which') for c in joins}
                    valid = ('atwar = no NOT = { ispuppet = IND } '
                             'NOT = { participant = { country = IND value = 4 } }')
                    if len(partners) == 1:
                        partner = next(iter(partners))
                        own = {'ENG': 'allied', 'USA': 'allied', 'GER': 'german',
                               'SOV': 'soviet', 'JAP': 'japan'}.get(partner)
                        valid += (' exists = ' + partner +
                                  ' NOT = { ispuppet = ' + partner + ' } '
                                  'NOT = { war = { country = IND country = ' + partner + ' } }')
                        valid += ' ' + ' '.join('NOT = { flag = ' + flag + ' }'
                            for group, flags in COMPACTS.items() if group != own for flag in flags)
                    else:
                        record([af.key], 'Multiple conditional alliance commands need native '
                               'transaction review; only Indian peace/alliance lock added.', 'UNRESOLVED')
                    changes.append(gate(a, valid))
                    join_guards[af.key] = valid
                    record([af.key], 'Joining leaf checks current Indian peace and alliance; '
                           'single partner also checks existence, sovereignty and bilateral war. '
                           'Same-partner compact/earned-rank flags are not excluded.')

            if eid in (9281304, 9281453):
                kind = 'german' if eid == 9281304 else 'soviet'
                owner = 'flag = ind_aubm_negotiation_' + kind
                keys = ['action_a'] if eid == 9281304 else ['action_a', 'action_b', 'action_c']
                predicates = []
                for key in keys:
                    a = ev.get(key)
                    old = a.get('trigger')
                    original = raw[old.start + 1:old.end - 1]
                    extra = join_guards['action_a']
                    if key != 'action_a':
                        # Soviet separate command/refusal can still conclude at
                        # war. They inherit current relationship checks, not the
                        # formal-entry peace requirement.
                        extra = extra.replace('atwar = no ', '', 1)
                        changes.append(gate(a, extra))
                    predicates.append('AND = { ' + original + ' ' + extra + ' }')
                valid = 'OR = { ' + ' '.join(predicates) + ' }'
                stale = 'NOT = { ' + valid + ' }'
                lapse_key = 'action_b' if eid == 9281304 else 'action_d'
                old_lapse = next(f for f in actions(ev) if f.key == lapse_key)
                changes.append((old_lapse.start, old_lapse.end, ''))
                cleanup_flags = (['ind_gc_berlin_negotiating'] if kind == 'german' else []) + [
                    'ind_aubm_diplomatic_negotiation_pending', 'ind_aubm_negotiation_' + kind]
                cleanup = '\n'.join('command = { type = clrflag which = ' + flag + ' }'
                                    for flag in cleanup_flags)
                extras.append('\n action = { trigger = { ' + stale + ' ' + owner +
                    ' } ai_chance = 100 name = "Release the obsolete owned ' + kind +
                    ' acceptance"\n' + cleanup + '\n }\n')
                extras.append('\n action = { trigger = { ' + stale + ' NOT = { ' + owner +
                    ' } } ai_chance = 100 name = "Close the unrelated old ' + kind + ' reply" }\n')
                record(keys + ['action[obsolete]'], 'Queued acceptance has no free Cancel. '
                       'Obsolete exits negate complete success eligibility and clear only '
                       'their own pending negotiation. An unrelated stale reply is effect-free; '
                       'Soviet separate command/refusal remains possible at war.')
                record(keys, 'Existing country negotiation flags cannot distinguish multiple '
                       'generations of the same country request; that recovery is unresolved.',
                       'UNRESOLVED')

            if eid == 9281200:
                valid = (NO_TREATY + ' NOT = { flag = ind_v4a_allied_framework_started } '
                         'NOT = { flag = ind_v4a_allied_framework_settled } '
                         'NOT = { participant = { country = IND value = 4 } }')
                keys = []
                for af in actions(ev):
                    if af.value.all('command'):
                        partner = 'USA' if af.key == 'action_b' else 'ENG'
                        changes.append(gate(af.value, valid + ' exists = ' + partner +
                            ' NOT = { war = { country = IND country = ' + partner + ' } }'))
                        keys.append(af.key)
                record(keys, 'Initial conference cannot replay after a treaty or completed '
                       'negotiation; explicit formal-entry upgrades remain separate.')

            if eid in ALLIED_PROPOSAL:
                valid = allied_live(ALLIED_PROPOSAL[eid])
                # These are queued replies, not polling roots: eligibility belongs
                # to actions, including failure, per event commands.txt 702-707.
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate'):
                        changes.append((f.start, f.end, ''))
                keys = []
                for af in actions(ev):
                    commands = af.value.all('command')
                    if commands and all(c.get('type') == 'clrflag' for c in commands):
                        # Replace old lapse effects to avoid clearing another
                        # negotiation's shared pending flag after this one ended.
                        changes.append((af.start, af.end, ''))
                    elif commands:
                        changes.append(gate(af.value, valid))
                        keys.append(af.key)
                proposal_flag = 'ind_v4a_proposal_' + ALLIED_PROPOSAL[eid]
                owner = 'flag = ind_aubm_negotiation_allied flag = ' + proposal_flag
                cleanup = '\n'.join('command = { type = clrflag which = ' + flag + ' }'
                    for flag in ['ind_aubm_diplomatic_negotiation_pending',
                                 'ind_v4a_allied_framework_started',
                                 'ind_aubm_negotiation_allied', proposal_flag])
                # Ownership is checked on the action before any command mutates
                # its identity. An old Commonwealth reply must never clear a
                # newer naval negotiation. Do not clear other proposal flags.
                extras.append('\n action = { trigger = { NOT = { AND = { ' + valid +
                    ' } } ' + owner + ' } ai_chance = 100 '
                    'name = "Close the obsolete owned Allied proposal"\n' + cleanup + '\n }\n')
                extras.append('\n action = { trigger = { NOT = { AND = { ' + valid +
                    ' } } NOT = { AND = { ' + owner + ' } } } ai_chance = 100 '
                    'name = "Close the unrelated old Allied reply" }\n')
                record(keys + ['action[obsolete]'], 'Queued Allied replies recheck their own '
                       'pending proposal, current relationship and completion at effect time; '
                       'failure releases only the matching Allied-owned proposal; an '
                       'unrelated stale reply closes without effects.')
                record(keys, 'Same-proposal retry generations cannot be distinguished by '
                       'existing proposal flags; native delivery/generation recovery remains '
                       'unresolved.', 'UNRESOLVED')

            if eid == 9281120:
                a = ev.get('action_b')
                changes.append(gate(a, 'money = 1500 supplies = 3000 oil = 1500'))
                record(['action_b'], 'Full-sphere purchase requires every charged stockpile.')

            if eid == 9281135:
                decision = ev.get('decision')
                if not isinstance(decision, Node):
                    raise ValueError('9281135 requires authored decision prerequisites')
                prerequisite = raw[decision.start + 1:decision.end - 1]
                changes.append(gate(ev.get('action_a'), JP_LIVE + ' ' + prerequisite))
                record(['action_a'], 'Paid request rechecks full authored review eligibility '
                       'and current partnership on the action itself.')

            if eid == 9281136:
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate'):
                        changes.append((f.start, f.end, ''))
                keys = []
                for af in actions(ev):
                    if af.value.all('command'):
                        changes.append(gate(af.value, JP_PENDING))
                        keys.append(af.key)
                extras.append(fallback(JP_PENDING,
                    'command = { type = clrflag which = ind_aubm_jp_seniority_review_pending }'))
                record(keys + ['action[obsolete]'], 'Japan can answer only a pending live '
                       'partnership review; withdrawal, war or loss of sovereignty clears '
                       'pending without rank, relation or AI rewards.')

            if eid == 9281914:
                for c in ev.get('action_a').all('command'):
                    if c.get('type') == 'setflag' and c.get('which') == 'ind_aubm_jp_influence':
                        changes.append(gate(c, 'NOT = { flag = ind_aubm_jp_influence }'))
                record(['action_a'], 'Initialize missing influence only; preserve existing numeric value.')

            if eid == 9281140:
                a = ev.get('action_a')
                removed = []
                for f in a.fields:
                    if f.key == 'command' and f.value.get('type') == 'war':
                        removed.append(f.value.get('which'))
                        changes.append((f.start, f.end, ''))
                changes.append(gate(a, JP_LIVE + ' NOT = { flag = ind_aubm_jp_southern_theatre }'))
                record(['action_a'], 'Ledger activation no longer declares wars against ' +
                       ', '.join(removed) + '; existing war state is untouched.')

            # Known unresolved transactions are surfaced even without an edit.
            if eid in (9281137, 9281160, 9281165, 9281455, 9281456, 9281457,
                       9281458, 9281459) or 9281501 <= eid <= 9281537:
                record([f.key for f in actions(ev)], 'Outside bounded correction: reply identity, '
                       'retry/delivery, pending recovery or government/peace ordering requires '
                       'further lifecycle design and native validation.', 'UNRESOLVED')
            if changes:
                if (eid in SAFE_CANCEL_IDS and
                        not any(not a.value.all('command') for a in actions(ev)) and ev.get('country') == 'IND'):
                    extras.append('\n action = { trigger = { ai = no } ai_chance = 0 '
                                  'name = "Cancel - close without changes" }\n')
                changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n' + ''.join(extras)))
                updated = replace(raw, changes)
                parse(updated)
                edits.append((ef.start, ef.end, updated))
            if records:
                reviews[eid] = records
        output[path] = replace(text, edits)
    return output, reviews
