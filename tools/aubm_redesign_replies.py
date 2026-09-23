"""Pure staged reply lifecycle corrections; run after diplomacy + cooperation.

Bounded families: Soviet eastern replies 9281456-59 and NAM regional offers
9281501-17, including their accepted-protocol callbacks 9281536-39. Great-power
NAM replies 9281520-35 remain unmodified. Transaction-local flags identify each
regional offer/protocol, not a route or native delivery generation. No new IDs,
timers, daily polling, rewards, file I/O, deployment or save mutations.
"""
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate
from aubm_redesign_cooperation import INDEPENDENT

MARKER = '# AUBM_STAGED_FOREIGN_REPLIES_V1'
REGIONAL = {9281502: ('CHI', 'china', 9281536),
            9281506: ('SIA', 'siam', 9281537),
            9281510: ('PER', 'persia', 9281538),
            9281514: ('AFG', 'afghan', 9281539)}
REQUEST = 'ind_v4_sov_east_requested'
ACTIVE = 'ind_v4_sov_east_active'
DEFERRED = 'ind_v4_sov_east_deferred'
EAST_LIVE = ('exists = IND exists = SOV NOT = { ispuppet = IND } '
    'NOT = { ispuppet = SOV } NOT = { war = { country = IND country = SOV } } '
    'NOT = { alliance = { country = IND country = JAP } } '
    'NOT = { alliance = { country = SOV country = JAP } } '
    'NOT = { flag = ind_aubm_commitment_japan } '
    'NOT = { flag = ind_aubm_jp_partnership } '
    'OR = { war = { country = IND country = JAP } '
    'war = { country = CHI country = JAP } war = { country = SOV country = JAP } }')


def flag(name):
    return 'flag = ' + name


def pending(name):
    return 'ind_stage_nam_' + name + '_offer_pending'


def protocol_pending(name):
    return 'ind_stage_nam_' + name + '_protocol_pending'


def relation_live(tag):
    return ('exists = IND exists = ' + tag + ' ' + INDEPENDENT +
            ' NOT = { ispuppet = ' + tag + ' } '
            'NOT = { war = { country = IND country = ' + tag + ' } }')


def command(kind, name):
    return 'command = { type = ' + kind + ' which = ' + name + ' }'


def action_extra(a):
    """Documented fixed debits and peace treaties must be executable together."""
    amounts, checks = {}, []
    for c in a.all('command'):
        if c.get('trigger'):
            continue
        kind, value = c.get('type'), c.get('value')
        if kind in ('money', 'supplies', 'oilpool') and value and float(value) < 0:
            key = 'oil' if kind == 'oilpool' else kind
            amounts[key] = amounts.get(key, 0) - float(value)
        if kind == 'non_aggression':
            checks.append('NOT = { war = { country = ' + c.get('which') +
                          ' country = ' + c.get('where') + ' } }')
    return ' '.join(k + ' = ' + str(int(v)) for k, v in amounts.items()) + ' ' + ' '.join(checks)


def exits(valid, owner, cleanup, human_withdraw):
    """Check ownership before mutations; never touch shared pending records."""
    obsolete = 'NOT = { ' + valid + ' }'
    result = ('\n action = { trigger = { ' + obsolete + ' ' + owner +
        ' } ai_chance = 100 name = "Close this obsolete offer without agreement"\n' +
        cleanup + '\n }\n action = { trigger = { ' + obsolete + ' NOT = { ' + owner +
        ' } } ai_chance = 100 name = "Close an unrelated or completed reply" }\n')
    if human_withdraw:
        result += ('\n action = { trigger = { ai = no ' + owner + ' ' + valid +
            ' } ai_chance = 0 name = "Withdraw this offer without agreement"\n' + cleanup + '\n }\n')
    return result


def transform(files: dict[str, str]):
    output, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            row = next(((base, data) for base, data in REGIONAL.items()
                        if base <= eid <= base + 3 or eid == data[2]), None)
            if eid not in (9281501, 9281456, 9281457, 9281458, 9281459) and row is None:
                if eid in (9281435, 9281444, 9281445):
                    reviews[eid] = [{'dimension': 'foreign_replies', 'status': 'UNRESOLVED',
                        'actions': ['action_c'], 'path': path,
                        'detail': 'Legacy corridor redirection also writes east_requested; '
                        'its original costs/effects remain. Reply guards prevent invalid '
                        'cooperation awards, but request-generation identity and these '
                        'upstream redirect transactions need separate review.'}]
                elif 9281520 <= eid <= 9281535:
                    reviews[eid] = [{'dimension': 'foreign_replies', 'status': 'UNRESOLVED',
                        'actions': [a.key for a in actions(ef.value)], 'path': path,
                        'detail': 'Great-power NAM family outside bounded regional reply implementation.'}]
                continue
            raw = text[ef.start:ef.end]
            ev = parse(raw).get('event')
            records, changes = [], []

            def record(keys, detail, status='CORRECTED_SCRIPT'):
                records.append({'dimension': 'foreign_replies', 'status': status,
                                'actions': list(keys), 'path': path, 'detail': detail})

            if MARKER in raw:
                record([], 'Already transformed.', 'ALREADY_APPLIED')
                reviews[eid] = records
                continue
            if eid == 9281501:
                a = ev.get('action_a')
                valid = ('flag = ind_v43_nam_doctrine_set NOT = { flag = ind_v43_nam_outreach_started } ' +
                         INDEPENDENT)
                changes.append(gate(a, valid))
                for f in a.fields:
                    if f.key != 'command' or f.value.get('type') != 'event':
                        continue
                    target = int(f.value.get('which'))
                    if target not in REGIONAL:
                        continue
                    tag, name, _ = REGIONAL[target]
                    changes.append((f.start, f.start,
                        'command = { trigger = { exists = ' + tag + ' } type = setflag which = ' + pending(name) + ' }\n'))
                # This synchronous dispatch has spent no additional resources;
                # an overtaken dispatch closes without creating pending offers.
                extra = ('\n action = { trigger = { NOT = { AND = { ' + valid +
                    ' } } } ai_chance = 100 name = "Close the overtaken conference dispatch" }\n')
                record(['action_a'], 'Dispatch creates four country-owned pending records before '
                       'existing delayed calls. Outreach_started prevents redispatch; existing '
                       'eight calls/delays remain, great-power chains unmodified.')
            else:
                if row:
                    base, (tag, name, protocol) = row
                    is_protocol = eid == protocol
                    p = protocol_pending(name) if is_protocol else pending(name)
                    owner = flag(p)
                    live = relation_live(tag)
                    if is_protocol:
                        live += ' ' + flag('ind_v43_nam_' + name + '_partner')
                        cleanup = command('clrflag', p)
                    else:
                        live += (' flag = ind_v43_nam_doctrine_set '
                                 'NOT = { flag = ind_v43_nam_' + name + '_resolved }')
                        cleanup = command('clrflag', p) + '\n' + command('setflag', 'ind_v43_nam_' + name + '_resolved')
                    terminal = eid != base
                else:
                    owner = flag(REQUEST)
                    live = (EAST_LIVE + ' NOT = { flag = ' + ACTIVE + ' } '
                            'NOT = { flag = ' + DEFERRED + ' }')
                    cleanup = command('clrflag', REQUEST)
                    terminal = eid != 9281456
                    # Retry callbacks must be reusable after an earlier stale or
                    # deferred delivery; terminal flags prevent reward replay.
                    persistent = next((f for f in ev.fields if f.key == 'persistent'), None)
                    changes.append((persistent.value_start, persistent.end, 'yes') if persistent else
                                   (ev.start + 1, ev.start + 1, '\n persistent = yes\n'))
                keys, available = [], []
                for af in actions(ev):
                    a = af.value
                    if not a.all('command'):
                        # No generic effect-free Cancel on a pending callback.
                        changes.append((af.start, af.end, ''))
                        continue
                    old = a.get('trigger')
                    old_body = raw[old.start + 1:old.end - 1] if isinstance(old, Node) else ''
                    predicate = owner + ' ' + live + ' ' + action_extra(a)
                    if ((eid == 9281458 and af.key == 'action_c') or
                            (eid == 9281459 and af.key == 'action_a')):
                        # These choices specifically guarantee China and record
                        # a bilateral command, not merely historical China aid.
                        predicate += (' exists = CHI NOT = { ispuppet = CHI } '
                            'NOT = { war = { country = IND country = CHI } }')
                    changes.append(gate(a, predicate))
                    available.append('AND = { ' + predicate + ' ' + old_body + ' }')
                    keys.append(af.key)
                    if row and not is_protocol:
                        for cf in a.fields:
                            if (cf.key == 'command' and cf.value.get('type') == 'event'
                                    and cf.value.get('which') == str(protocol)):
                                changes.append((cf.start, cf.start, command('setflag', protocol_pending(name)) + '\n'))
                    if terminal:
                        changes.append((a.end - 1, a.end - 1, '\n' + command('clrflag', p if row else REQUEST) + '\n'))
                valid = 'OR = { ' + ' '.join(available) + ' }'
                extra = exits(valid, owner, cleanup, ev.get('country') == 'IND')
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate'):
                        changes.append((f.start, f.end, ''))
                record(keys + ['action[owned-lapse]', 'action[withdrawal]'],
                       'Every original outcome rechecks its own pending record, current '
                       'nonhostility/sovereignty and relevant current commitments. Fixed '
                       'debits require affordability. Original effects and nonjoining options '
                       'are retained; success and owned lapse consume only this transaction. '
                       'Human withdrawal explicitly resolves the offer without agreement. '
                       'No shared diplomatic pending flag, war or earned partner record is cleared.')
                if not row:
                    record(keys, 'Eastern reply effects require a continuing IND/CHI/SOV war '
                           'with Japan. Explicit China-bilateral choices 9281458.action_c and '
                           '9281459.action_a additionally require existing sovereign nonhostile '
                           'China. Other China relation modifiers remain original incidental '
                           'effects; no broader foreign-policy redesign is claimed.')
            record([], 'No claim of native delivery or same-offer generation identity. '
                   'A country disappearing before its foreign callback can leave a pending '
                   'record; no polling recovery added. Existing-save queued NAM offers lack '
                   'the new pending tokens and must not be treated as migrated. Prior foreign '
                   'effects are not rolled back on later withdrawal.', 'UNRESOLVED')
            changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n' + extra))
            updated = replace(raw, changes)
            parse(updated)
            edits.append((ef.start, ef.end, updated))
            reviews[eid] = records
        output[path] = replace(text, edits)
    return output, reviews
