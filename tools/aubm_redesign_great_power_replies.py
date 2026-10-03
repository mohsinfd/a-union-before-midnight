"""Pure Stage-3 NAM great-power reply lifecycle, AFTER aubm_redesign_replies.

Owns only 9281501 additions and 9281520-35. Country offer and selected-answer
tokens distinguish sibling replies; they do not claim native retry generations.
Existing delays, commands, rewards, costs, political modifiers and treaties are
retained. No new event IDs, polling, installation, file I/O or save migration.
"""
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate
from aubm_redesign_replies import (MARKER as REGIONAL_MARKER, action_extra,
    command, exits, pending, protocol_pending, relation_live)

MARKER = '# AUBM_STAGED_GREAT_POWER_REPLIES_V1'
FAMILIES = {9281520: ('ENG', 'britain'), 9281524: ('USA', 'america'),
            9281528: ('SOV', 'soviet'), 9281532: ('JAP', 'japan')}


def answer(name, eid):
    return 'ind_stage_nam_' + name + '_answer_' + str(eid) + '_pending'


def live(tag, name):
    return (relation_live(tag) + ' flag = ind_v43_nam_doctrine_set '
            'NOT = { flag = ind_v43_nam_' + name + '_resolved }')


def contact(tag):
    return ('exists = ' + tag + ' NOT = { ispuppet = ' + tag + ' } '
            'NOT = { war = { country = IND country = ' + tag + ' } }')


def special_gate(eid, key):
    if eid == 9281523 and key == 'action_b':
        return contact('USA')
    if eid == 9281534 and key == 'action_a':
        # Source has no implemented withdrawal from an accepted China pact.
        # Do not award an exclusion bargain while that contradictory fact exists.
        return ('NOT = { flag = ind_v43_nam_china_partner } '
                'NOT = { alliance = { country = IND country = CHI } } '
                'NOT = { AND = { flag = ind_v42_delhi_pact_consultative '
                'flag = ind_v42_china_accepts_delhi_pact } } '
                'NOT = { flag = ' + pending('china') + ' } '
                'NOT = { flag = ' + protocol_pending('china') + ' }')
    if eid == 9281534 and key == 'action_c':
        return contact('CHI')
    if eid == 9281535 and key == 'action_c':
        return contact('CHI') + ' ' + contact('SIA')
    return ''


def transform(files: dict[str, str]):
    output, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            row = next(((base, data) for base, data in FAMILIES.items() if base <= eid <= base + 3), None)
            if eid != 9281501 and row is None:
                continue
            raw = text[ef.start:ef.end]
            ev = parse(raw).get('event')
            changes, records = [], []

            def record(keys, detail, status='CORRECTED_SCRIPT'):
                records.append({'dimension': 'great_power_replies', 'status': status,
                                'actions': list(keys), 'path': path, 'detail': detail})

            if MARKER in raw:
                record([], 'Already transformed.', 'ALREADY_APPLIED')
                reviews[eid] = records
                continue
            if eid == 9281501:
                if REGIONAL_MARKER not in raw:
                    raise ValueError('Great-power replies require prior aubm_redesign_replies dispatch transform')
                found = set()
                for cf in ev.get('action_a').fields:
                    if cf.key != 'command' or cf.value.get('type') != 'event':
                        continue
                    target = int(cf.value.get('which'))
                    if target not in FAMILIES:
                        continue
                    tag, name = FAMILIES[target]
                    eligible = live(tag, name)
                    changes.append(gate(cf.value, eligible))
                    changes.append((cf.start, cf.start,
                        'command = { trigger = { ' + eligible + ' } type = setflag which = ' + pending(name) + ' }\n'
                        'command = { trigger = { NOT = { AND = { ' + eligible + ' } } } '
                        'type = setflag which = ind_v43_nam_' + name + '_resolved }\n'))
                    found.add(target)
                if found != set(FAMILIES):
                    raise ValueError('Great-power dispatch contract changed: ' + str(found))
                record(['action_a'], 'Four existing great-power dispatch commands and their '
                       'offer-token writes share current eligibility. Unavailable offers close '
                       'their own existing resolution record; regional dispatch additions and '
                       'all original delays remain intact.')
                extra = ''
            else:
                base, (tag, name) = row
                is_foreign = eid == base
                offer = pending(name)
                if is_foreign:
                    owner = ('AND = { flag = ' + offer + ' NOT = { OR = { ' +
                        ' '.join('flag = ' + answer(name, i) for i in range(base + 1, base + 4)) + ' } } }')
                else:
                    owner = 'AND = { flag = ' + offer + ' flag = ' + answer(name, eid) + ' }'
                cleanup = '\n'.join([command('clrflag', offer),
                    command('setflag', 'ind_v43_nam_' + name + '_resolved')] +
                    ([] if is_foreign else [command('clrflag', answer(name, eid))]))
                predicates, keys = [], []
                for af in actions(ev):
                    a = af.value
                    if not a.all('command'):
                        changes.append((af.start, af.end, ''))
                        continue
                    original = a.get('trigger')
                    original_text = raw[original.start + 1:original.end - 1] if isinstance(original, Node) else ''
                    predicate = owner + ' ' + live(tag, name) + ' ' + action_extra(a) + ' ' + special_gate(eid, af.key)
                    changes.append(gate(a, predicate))
                    predicates.append('AND = { ' + predicate + ' ' + original_text + ' }')
                    keys.append(af.key)
                    if is_foreign:
                        calls = [cf for cf in a.fields if cf.key == 'command' and cf.value.get('type') == 'event']
                        if len(calls) != 1 or int(calls[0].value.get('which')) not in range(base + 1, base + 4):
                            raise ValueError('Unexpected NAM answer callback in ' + str(eid) + '.' + af.key)
                        cf = calls[0]
                        changes.append((cf.start, cf.start, command('setflag', answer(name, int(cf.value.get('which')))) + '\n'))
                    else:
                        changes.append((a.end - 1, a.end - 1, '\n' + command('clrflag', offer) + '\n' +
                                        command('clrflag', answer(name, eid)) + '\n'))
                extra = exits('OR = { ' + ' '.join(predicates) + ' }', owner, cleanup, not is_foreign)
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate'):
                        changes.append((f.start, f.end, ''))
                record(keys + ['action[owned-lapse]', 'action[withdrawal]'],
                       'Own offer and selected-answer tokens guard this exact reply stage. '
                       'Current war, sovereignty, actual alliance/treaty commitment, doctrine '
                       'and existing completion are checked at each effect-bearing action. '
                       'Fixed costs have affordability gates. Original commands/amounts remain; '
                       'success or explicit withdrawal consumes only this offer/answer. '
                       'Sibling or already-completed replies close without effects; no free '
                       'Cancel strands a pending callback.')
                if eid == 9281534:
                    record(['action_a', 'action_c'], 'China exclusion cannot contradict a '
                           'current accepted/allied/pending China partnership; mediation '
                           'requires existing sovereign nonhostile China. Future enforcement '
                           'of the China-exclusion promise across other decisions is unresolved.', 'UNRESOLVED')
            record([], 'No native delivery, retry-generation, elapsed-time promise-expiry or '
                   'existing-save token migration guarantee. Country disappearance can prevent '
                   'queued delivery. Relationship changes invalidate promises on delivered '
                   'replies; no unsupported time expiry or polling was invented. Prior foreign '
                   'debits, embargoes, treaties and earned modifiers are not rolled back on '
                   'later lapse/withdrawal.', 'UNRESOLVED')
            changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n' + extra))
            updated = replace(raw, changes)
            parse(updated)
            edits.append((ef.start, ef.end, updated))
            reviews[eid] = records
        output[path] = replace(text, edits)
    return output, reviews
