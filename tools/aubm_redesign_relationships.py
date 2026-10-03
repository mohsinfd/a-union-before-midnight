"""Pure authored-source relationships pass, after diplomacy/replies/crises.

Fresh-game primary. Existing event IDs and original offers/costs/odds/delays
remain. Local offer, selected-answer and cooldown flags are not global routes.
Native delivery, disappearing recipients and same-offer generation identity
remain unproved; this pass does not migrate already queued save-game events.
"""
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate, JP_LIVE, COMPACTS
from aubm_redesign_replies import command, exits, action_extra

MARKER = '# AUBM_STAGED_RELATIONSHIPS_V1'
NEW_EVENT_IDS = frozenset()
FAMILIES = {
    'persia': (9281314, {'PER': 9281320}, 9281330, 9281339),
    'afghan': (9281315, {'AFG': 9281321}, 9281333, 9281340),
    'xinjiang': (9281316, dict(zip(('SIK', 'UPE', 'CHI', 'CHC', 'CXB'), range(9281322, 9281327))), 9281336, 9281349),
}
JP_REQUEST = 'ind_aubm_jp_seniority_review_pending'
JP_OFFER = 'ind_stage_jp_seniority_offer'
JP_ANSWERS = ['ind_stage_jp_seniority_' + s for s in ('accepted', 'deferred', 'rejected')]
JP_CURRENT = JP_LIVE + ' ' + ' '.join('NOT = { flag = ' + f + ' }'
    for group in ('allied', 'german', 'soviet') for f in COMPACTS[group])


def token(family, stage):
    return 'ind_stage_corridor_' + family + '_' + str(stage)


def oldflag(family, suffix):
    return 'ind_gc_' + family + '_' + suffix


def flag(name):
    return 'flag = ' + name


def either(predicates):
    return 'OR = { ' + ' '.join('AND = { ' + p + ' }' for p in predicates) + ' }'


def corridor_live(family, tag):
    # Sovereign anti-Soviet campaigns are expressly supported by 9281308/09.
    result = ('exists = IND exists = ' + tag + ' flag = ind_gc_campaign_active '
        'war = { country = IND country = SOV } NOT = { ispuppet = IND } '
        'NOT = { ispuppet = ' + tag + ' } '
        'NOT = { war = { country = IND country = ' + tag + ' } } '
        'NOT = { alliance = { country = ' + tag + ' country = SOV } } '
        'NOT = { flag = ' + oldflag(family, 'route') + ' }')
    if family == 'xinjiang':
        result += ' control = { province = 1279 data = ' + tag + ' } control = { province = 1281 data = ' + tag + ' }'
    return result


def transform(files: dict[str, str]):
    output, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            row = next(((name, data) for name, data in FAMILIES.items()
                        if eid in (data[0], data[3], *data[1].values(), *range(data[2], data[2] + 3))), None)
            if not row and eid not in (9281135, 9281136, 9281137):
                continue
            raw = text[ef.start:ef.end]
            if MARKER in raw:
                reviews[eid] = [dict(dimension='relationships', status='ALREADY_APPLIED', actions=[], path=path, detail='Already transformed.')]
                continue
            ev = parse(raw).get('event')
            changes, extras, covered = [], '', []
            root = eid == 9281135 or (row and eid == row[1][0])
            if not root:
                p = next((f for f in ev.fields if f.key == 'persistent'), None)
                changes.append((p.value_start, p.end, 'yes') if p else (ev.start + 1, ev.start + 1, '\n persistent = yes\n'))
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate', 'one_action'):
                        changes.append((f.start, f.end, ''))
            if row:
                name, (request, responders, base, reset) = row
                requested, cooldown = oldflag(name, 'requested'), token(name, 'cooldown')
                if root:
                    valid = either([corridor_live(name, tag) for tag in responders]) + ' NOT = { flag = ' + cooldown + ' }'
                    changes.append((ev.get('decision').start + 1, ev.get('decision').start + 1, '\n' + valid + '\n'))
                    decision = ev.get('decision')
                    a = ev.get('action_a')
                    changes.append(gate(a, valid + ' ' + raw[decision.start + 1:decision.end - 1]))
                    for cf in a.fields:
                        if cf.key != 'command' or cf.value.get('type') != 'event':
                            continue
                        tag = cf.value.get('where')
                        if tag in responders:
                            predicate = corridor_live(name, tag)
                            changes.append((cf.value.start + 1, cf.value.start + 1, '\n trigger = { ' + predicate + ' }\n') if not cf.value.get('trigger') else gate(cf.value, predicate))
                            changes.append((cf.start, cf.start, 'command = { trigger = { ' + predicate + ' } type = setflag which = ' + token(name, 'offer_' + tag) + ' }\n'))
                    extras = '\n action = { ai_chance = 0 name = "Leave the proposal on the cabinet table" }\n'
                    covered = ['action_a']
                elif eid == reset:
                    # Timer owns only its cooldown, never a newly dispatched offer.
                    a = ev.get('action_a')
                    for cf in a.fields:
                        if cf.key == 'command':
                            changes.append((cf.start, cf.end, ''))
                    owner = flag(cooldown)
                    changes.append(gate(a, owner))
                    changes.append((a.end - 1, a.end - 1, '\n' + command('clrflag', cooldown) + '\n' + command('clrflag', oldflag(name, 'rejected'))))
                    extras = '\n action = { trigger = { NOT = { ' + owner + ' } } ai_chance = 100 name = "These talks have already moved on" }\n'
                    covered = ['action_a']
                else:
                    foreign = eid in responders.values()
                    tags = [tag for tag, i in responders.items() if i == eid] if foreign else list(responders)
                    tokens = {tag: token(name, 'offer_' + tag if foreign else str(eid) + '_' + tag) for tag in tags}
                    owner = either([flag(t) for t in tokens.values()])
                    live = either([flag(tokens[tag]) + ' ' + corridor_live(name, tag) for tag in tags])
                    predicate = flag(requested) + ' ' + live
                    cleanup = '\n'.join(command('clrflag', t) for t in tokens.values()) + '\n' + command('clrflag', requested)
                    available = []
                    for af in actions(ev):
                        a = af.value
                        if not a.all('command'):
                            changes.append((af.start, af.end, ''))
                            continue
                        old = a.get('trigger')
                        full = predicate + ' ' + action_extra(a) + (' ' + raw[old.start + 1:old.end - 1] if old else '')
                        changes.append(gate(a, predicate + ' ' + action_extra(a)))
                        available.append(full)
                        covered.append(af.key)
                        if foreign:
                            for cf in a.fields:
                                if cf.key == 'command' and cf.value.get('type') == 'event':
                                    answer = token(name, cf.value.get('which') + '_' + tags[0])
                                    changes.append((cf.start, cf.start, command('setflag', answer) + '\n'))
                            tail = command('clrflag', tokens[tags[0]])
                        else:
                            tail = cleanup
                            if eid != base:
                                tail += '\n' + command('setflag', cooldown)
                            if eid == base + 1:
                                # Retrying a limited deal must not stack permanent bonuses.
                                for cf in a.fields:
                                    if cf.key == 'command' and cf.value.get('type') in ('tc_mod', 'intelligence'):
                                        changes.append(gate(cf.value, 'NOT = { flag = ' + oldflag(name, 'limited') + ' }'))
                        changes.append((a.end - 1, a.end - 1, '\n' + tail + '\n'))
                    extras = exits(either(available), owner, cleanup, ev.get('country') == 'IND')
            elif eid == 9281135:
                no_notice = ' '.join('NOT = { flag = ' + t + ' }' for t in JP_ANSWERS)
                no_notice += ' NOT = { flag = ' + JP_OFFER + ' }'
                changes.append((ev.get('decision').start + 1, ev.get('decision').start + 1, '\n' + no_notice + ' ' + JP_CURRENT + '\n'))
                a = ev.get('action_a')
                changes.append(gate(a, no_notice + ' ' + JP_CURRENT))
                changes.append((a.end - 1, a.end - 1, '\n' + command('setflag', JP_OFFER) + '\n'))
                covered = ['action_a']
            else:
                foreign = eid == 9281136
                owner = flag(JP_OFFER) if foreign else either([flag(t) for t in JP_ANSWERS])
                valid = 'AND = { ' + owner + ' ' + (flag(JP_REQUEST) if foreign else '') + ' ' + JP_CURRENT + ' }'
                cleanup = '\n'.join(command('clrflag', t) for t in ([JP_OFFER, JP_REQUEST] if foreign else JP_ANSWERS))
                for af in actions(ev):
                    if af.key == 'action':
                        changes.append((af.start, af.end, ''))
                        continue
                    a = af.value
                    changes.append(gate(a, valid))
                    covered.append(af.key)
                    if foreign:
                        answer = JP_ANSWERS[['action_a', 'action_b', 'action_c'].index(af.key)]
                        changes.append((a.end - 1, a.end - 1, '\n' + command('clrflag', JP_OFFER) + '\n' + command('setflag', answer) + '\n'))
                    else:
                        for cf in a.fields:
                            if cf.key != 'command':
                                continue
                            c = cf.value
                            if c.get('type') == 'clrflag' and c.get('which') == JP_REQUEST:
                                changes.append((cf.start, cf.end, ''))
                                continue
                            tr = c.get('trigger')
                            if tr:
                                body = raw[tr.start:tr.end]
                                index = 0 if 'ind_aubm_jp_india_full_sphere' in body else 1 if 'ind_aubm_jp_seniority_deferred' in body else 2
                                changes.append(gate(c, flag(JP_ANSWERS[index])))
                        changes.append((a.end - 1, a.end - 1, '\n' + cleanup + '\n'))
                extras = exits(valid, owner, cleanup, not foreign)
            changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n' + extras))
            updated = replace(raw, changes)
            parse(updated)
            edits.append((ef.start, ef.end, updated))
            reviews[eid] = [dict(dimension='relationships', status='CORRECTED_SCRIPT', actions=covered + ([] if root else ['action[owned-lapse/withdrawal]']), path=path,
                detail='Current relationship/action checks; offer and selected-answer ownership; persistent callbacks; owned lapse/withdrawal. Corridor retries retain original costs, odds and 180/360-day cooldowns; only first limited deal grants its permanent bonus. Sovereign anti-Soviet campaigning remains valid. Japan deferral can retry after its notice; explicit Japanese rejection remains the original permanent review_failed gate. Existing wars and earned effects are never rolled back.'),
                dict(dimension='relationships', status='UNRESOLVED', actions=[], path=path,
                detail='Fresh-game tokens do not migrate old queued offers. Native recipient disappearance and same-offer/same-cooldown delivery generations remain unproved. No timer polling/recovery or historical access rollback. These are script checks, not native-engine execution certification.')]
        output[path] = replace(text, edits)
    return output, reviews
