"""Historical Japanese aggression, witnessed by the existing country observers.

Pure authored-source pass over the complete 684-event observation/response unit.
No new IDs, attacker predicate, country counter-chain, installation or save I/O.
The installed engine docs define country-relative attack=JAP as 'Country [tag]
has attacked this country'. We retain the existing armed peaceful baseline plus
current bilateral war plus attack=JAP test, not war alone. Observation starts
in1933 independently of India's old route/manual opt-in; existing wars are not
armed until peace is observed. First proof stops all observers permanently.

Historical proof survives peace/annexation and permits ONE optional independent
response. This deliberately replaces the source's current-war/re-notify cycle.
Native attack-predicate lifetime, daily polling order and alliance war entry
remain untested. Existing saves' old live/armed flags are not migrated as proof.
"""
import json
from dh_save_spans import Node, parse, replace, walk
from aubm_redesign_diplomacy import actions
from aubm_redesign_cooperation import INDEPENDENT

MARKER = '# AUBM_STAGED_AGGRESSION_V1'
NEW_EVENT_IDS = frozenset()
OBSERVER_IDS = frozenset(range(9295000, 9295680))
PAGE_IDS = frozenset(range(9294002, 9294006))
EDITED_IDS = OBSERVER_IDS | PAGE_IDS
PROOF = 'ind_stage_japan_aggression_proven'
NOTIFIED = 'ind_lib1_aggression_notified'
USED = 'ind_lib1_reactive_intervention'
RESPONSE = ('flag = ' + PROOF + ' exists = IND exists = JAP '
    'NOT = { ispuppet = JAP } ' + INDEPENDENT +
    ' NOT = { war = { country = IND country = JAP } } '
    'NOT = { flag = ' + USED + ' }')


def command(kind, which):
    return 'command = { type = ' + kind + ' which = ' + which + ' }'


def action(key, title, commands='', valid=None):
    return ('\n ' + key + ' = { ' + ('trigger = { ' + valid + ' } ' if valid else '') +
        'name = ' + json.dumps(title) + '\n' + commands + '\n }\n')


def event(eid, title, desc, choices, valid=None, decision=False, country='IND', picture='aubm_v4_liberated_territory'):
    header = ('event = {\n' + MARKER + '\n id = ' + str(eid) + '\n random = no persistent = yes country = ' + country + '\n')
    if valid:
        header += ' trigger = { ' + ('ai = no ' if decision else '') + valid + ' }\n'
        if decision: header += ' decision = { ai = no ' + valid + ' }\n'
        else: header += ' one_action = yes\n'
        header += ' date = { day = 0 month = january year = 1933 } offset = 1 deathdate = { day = 29 month = december year = 1964 }\n'
    return (header + ' name = ' + json.dumps(title) + '\n desc = ' + json.dumps(desc) + '\n style = 2 picture = ' + json.dumps(picture) + '\n' + choices + '}\n')


def pages():
    notify = 'exists = IND flag = ' + PROOF + ' NOT = { flag = ' + NOTIFIED + ' }'
    return {
        9294002: event(9294002, 'Japan Has Crossed the Line',
            'Observers witnessed Japan attack a country previously at peace with it. This record will survive the war. India may later choose one independent intervention if its current commitments permit it. This notice changes no war, alliance or mobilisation policy.',
            action('action_a', 'Keep the evidence; let India choose its moment', command('setflag', NOTIFIED), notify), notify),
        9294003: event(9294003, 'The Record of Japanese Aggression Remains',
            'A later peace does not erase the witnessed attack. The evidence and the one-time notice remain recorded. Closing this page changes nothing.',
            action('action_a', 'Keep the historical record')),
        9294004: event(9294004, 'Respond to Japanese Aggression',
            'Japan has a witnessed aggression record. India may make one independent response, even if that war has ended. Reviewing this page declares no war. Final confirmation costs 2 dissent and declares war on Japan; its allies and puppets may join under normal rules. Cancel changes nothing.',
            action('action_a', 'Cancel - remain at peace with Japan') +
            action('action_b', 'Review an independent declaration: +2 dissent', command('event', '9294005 where = IND when = 0'), RESPONSE), RESPONSE, True),
        9294005: event(9294005, 'India Chooses Its Response',
            'DECLARE WAR: India attacks Japan, adding 2 dissent. Japan\'s allies and puppets may join under normal rules. India joins no coalition and keeps its existing wars. The witnessed attack remains historical evidence, but this response can be used only once. Cancel changes nothing.',
            action('action_a', 'Cancel - no declaration') +
            action('action_b', 'Declare war on Japan now: +2 dissent',
                'command = { type = dissent value = 2 }\ncommand = { type = war which = JAP }\n' +
                command('setflag', 'ind_lib1_japan_war') + '\n' + command('setflag', USED), RESPONSE)),
    }


def transform(files: dict[str, str]):
    output, records, seen, countries = dict(files), {}, {}, {}
    for path, text in files.items():
        for ef in parse(text).fields:
            if ef.key == 'event' and int(ef.value.get('id')) in EDITED_IDS:
                eid = int(ef.value.get('id'))
                if eid in seen: raise ValueError('Duplicate aggression ID ' + str(eid))
                seen[eid] = path
                countries[eid] = ef.value.get('country')
    if set(seen) != EDITED_IDS or len(set(seen.values())) != 1:
        raise ValueError('Complete observer/response unit must share its loaded source module')
    page_text = pages()
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event': continue
            ev, eid = ef.value, int(ef.value.get('id'))
            if eid not in EDITED_IDS: continue
            raw = text[ef.start:ef.end]
            if MARKER in raw:
                records[eid] = [dict(dimension='aggression', status='ALREADY_APPLIED', path=path, actions=[])]
                continue
            if eid in PAGE_IDS:
                updated = page_text[eid]
                keys = ['action_a', 'action_b'] if eid in (9294004, 9294005) else ['action_a']
                detail = 'Permanent foreign-witness proof, one notice, and one optional explicit response. Current independent sovereignty/relationships/commitments rechecked at declaration; prior evidence is not erased by peace. The old340-country current-war OR and reset watcher are retired.'
            else:
                tag = ev.get('country')
                partner = countries[eid + (1 if eid % 2 == 0 else -1)]
                if tag != partner or tag in ('IND', 'JAP'):
                    raise ValueError('Observer country pair changed: ' + str(eid))
                armed = 'ind_lib1_aggression_armed_' + tag.lower()
                live = 'ind_lib1_aggression_live_' + tag.lower()
                pair_war = 'war = { country = JAP country = ' + tag + ' }'
                base = 'exists = IND exists = JAP NOT = { flag = ' + PROOF + ' } '
                original = actions(ev)
                if len(original) != 1: raise ValueError('Unexpected observer actions')
                a = original[0].value
                if eid % 2 == 0:
                    valid = base + 'NOT = { ' + pair_war + ' } OR = { NOT = { flag = ' + armed + ' } flag = ' + live + ' }'
                    expected = [('setflag', armed), ('clrflag', live)]
                else:
                    valid = base + 'flag = ' + armed + ' ' + pair_war + ' attack = JAP'
                    expected = [('clrflag', armed), ('setflag', live)]
                    if not any(f.key == 'attack' and f.value == 'JAP' for n in walk(a.get('trigger')) for f in n.fields):
                        raise ValueError('Foreign attacker witness contract changed')
                if [(c.get('type'), c.get('which')) for c in a.all('command')] != expected:
                    raise ValueError('Foreign witness payload changed')
                commands = '\n'.join(command(kind, which) for kind, which in expected)
                if eid % 2: commands += '\n' + command('setflag', PROOF)
                updated = event(eid, ev.get('name'), ev.get('desc'),
                    action('action_a', a.get('name'), commands, valid), valid, country=tag, picture=ev.get('picture'))
                keys = ['action_a']
                detail = 'Existing country-relative peaceful-baseline + attack=JAP witness retained. Observation begins1933 without route/manual opt-in; existing wars never arm the baseline. First attack adds permanent proof and stops all observer activity; no observer declares war or grants rewards.'
            parse(updated)
            edits.append((ef.start, ef.end, updated))
            records[eid] = [dict(dimension='aggression', status='CORRECTED_SCRIPT', path=path, actions=keys, detail=detail),
                dict(dimension='aggression', status='UNRESOLVED', path=path, actions=[], detail='No native proof of attack-predicate lifetime, observer polling order or alliance entry behavior. Existing saves are not migrated from historical live/armed flags. All680 country observers remain until first proof; this simplifies predicates and stops later polling, not the native event count.')]
        if edits: output[path] = replace(text, edits)
    return output, records
