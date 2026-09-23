"""Twelve existing choices acquire bounded endings; no new events or treaties.

Run after route_finish. Coalition deployment is a presence test, not a claim
that the engine can attribute battles to India. Existing once-only congress
and culmination locks remain authoritative. Native verification is pending.
"""
from __future__ import annotations
import json
from dh_save_spans import Node, parse, replace, walk
from aubm_redesign_campaign_access import canonical, predicate_roots
from aubm_redesign_route_finish import actions, set_fields
from generate_aubm_bespoke_route_arcs import ROUTES

MARKER = '# AUBM_STAGED_FOCUS_OUTCOMES_V1'
SELECTED = {('allied', 1), ('german', 0), ('soviet', 0), ('sovereign', 1)}


def control(province):
    return f'control = {{ province = {province} data = IND }}'


def deployed(province):
    friendly = [control(province)] + [
        f'AND = {{ alliance = {{ country = IND country = {tag} }} '
        f'NOT = {{ war = {{ country = IND country = {tag} }} }} '
        f'control = {{ province = {province} data = {tag} }} }}'
        for tag in ('ENG', 'USA', 'SOV')]
    return (f'AND = {{ OR = {{ {" ".join(friendly)} }} '
            f'garrison = {{ country = IND province = {province} type = land size = 6 area = no }} }}')


MAIN = 'AND = { ' + deployed(195) + ' ' + deployed(163) + ' }'
MED = 'AND = { ' + deployed(419) + ' ' + deployed(377) + ' }'
EXPEDITION = 'AND = { war = { country = IND country = GER } OR = { ' + MAIN + ' ' + MED + ' } }'
REWARDS = {
    'allied': (('research_mod value = 2',), ('tc_mod value = 3',), ('supplies value = 1200',)),
    'german': (('oilpool value = 1500',), ('tc_mod value = 3',), ('supplies value = 1200',)),
    'soviet': (('research_mod value = 2',), ('tc_mod value = 3',), ('supplies value = 1200',)),
    'sovereign': (('dissent value = -3',), ('tc_mod value = 3',), ('supplies value = 1200',)),
}
BRIEFS = {
    'allied': 'Choose your expedition. Main front: deploy six Indian land divisions in both Berlin and Vienna; gain +2 research. Mediterranean: six in both Rome and Athens; gain +3 transport capacity. Separate command: either pair, or the existing German victory milestone; gain 1,200 supplies. Deployment requires war with Germany and Indian or allied control. These are extra one-time rewards, not land or peace rights.',
    'german': 'Choose where the Soviet offensive will end. Caucasus: hold Baku and Astrakhan for 1,500 oil. Central Asia: hold Tashkent and Omsk for +3 transport capacity. Mobile front: reach the existing northern or Soviet victory milestone for 1,200 supplies. These are extra one-time campaign rewards. None of these objectives alone forces Soviet peace or creates puppets.',
    'soviet': 'Choose your expedition. Joint plans: deploy six Indian land divisions in both Berlin and Vienna; gain +2 research. Mediterranean: six in both Rome and Athens; gain +3 transport capacity. Free command: either pair, or the existing German victory milestone; gain 1,200 supplies. Deployment requires war with Germany and Indian or allied control. India earns the reward, not somebody else\'s provinces.',
    'sovereign': 'Your frontier policy now shapes the reward after the existing continental victory objective. Buffer league: an extra -3 dissent. Base network: +3 transport capacity. Mobile guarantees: 1,200 supplies. These are one-time Indian rewards, not automatic treaties, foreign bases or annexations. Actual peace and government agreements are still settled separately.',
}


def guarded_choices(focus, goals):
    return 'OR = { ' + ' '.join(
        'AND = { flag = ' + c.flag + ' ' +
        ' '.join('NOT = { flag = ' + other.flag + ' }' for other in focus.choices if other != c) +
        ' ' + goal + ' }' for c, goal in zip(focus.choices, goals)) + ' }'


def substitute(block, old, new):
    target = canonical(parse(old).fields[0].value)
    key = parse(old).fields[0].key
    edits = []
    for root in predicate_roots(parse(block).get('event')):
        for node in walk(root):
            for f in node.fields:
                if f.key == key and isinstance(f.value, Node) and canonical(f.value) == target:
                    edits.append((f.start, f.end, new))
    if not edits:
        raise ValueError('Expected focus milestone is missing')
    return replace(block, edits)


def transform(files):
    policies = {}
    for route in ROUTES:
        for i, focus in enumerate(route.focuses):
            if (route.key, i) not in SELECTED:
                continue
            policies[route.base + 13 + i] = (route, focus, 'choice')
            policies[route.base + 17 + i] = (route, focus, 'end')
            if route.key in ('allied', 'soviet'):
                policies[route.base + 9 + i] = (route, focus, 'mid')
    output, records = dict(files), {}
    for path, text in files.items():
        edits = []
        for field in parse(text).fields:
            if field.key != 'event':
                continue
            event = field.value
            eid = int(event.get('id'))
            if eid not in policies:
                continue
            block = text[field.start:field.end]
            route, focus, phase = policies[eid]
            if MARKER not in block:
                if phase == 'choice':
                    block = set_fields(block, {'desc': json.dumps(BRIEFS[route.key])})
                elif phase == 'mid':
                    block = substitute(block, focus.intermediate_condition,
                        'OR = { ' + focus.intermediate_condition + ' ' + EXPEDITION + ' }')
                else:
                    old = focus.culmination_condition
                    goals = [old] * 3
                    if route.key in ('allied', 'soviet'):
                        war = 'war = { country = IND country = GER }'
                        goals = [f'AND = {{ {war} {MAIN} }}', f'AND = {{ {war} {MED} }}',
                                 'OR = { ' + old + ' ' + EXPEDITION + ' }']
                    elif route.key == 'german':
                        war = 'war = { country = IND country = SOV }'
                        goals = [f'AND = {{ {war} {control(713)} {control(706)} }}',
                                 f'AND = {{ {war} {control(1103)} {control(1138)} }}', old]
                    block = substitute(block, old, guarded_choices(focus, goals))
                    block = set_fields(block, {'desc': json.dumps('The objective is met. India receives the normal campaign reward and the extra reward promised by your chosen plan. No foreign land changes hands and no war ends here.')})
                    ev = parse(block).get('event')
                    action = actions(ev)[0].value
                    extra = '\n'.join('command = { trigger = { flag = ' + c.flag + ' } type = ' + reward + ' }'
                        for c, rewards in zip(focus.choices, REWARDS[route.key]) for reward in rewards)
                    name = action.field('name')
                    block = replace(block, [(name.value_start, name.end, '"Bring the campaign gains home"'),
                        (action.end - 1, action.end - 1, '\n' + extra + '\n')])
                ev = parse(block).get('event')
                block = replace(block, [(ev.end - 1, ev.end - 1, '\n' + MARKER + '\n')])
            edits.append((field.start, field.end, block))
            records[eid] = [dict(dimension='focus_outcomes', status='reviewed', engine_tested=False,
                detail='Existing choice-specific ending or coalition deployment opportunity; original once-only locks retained.')]
        output[path] = replace(text, edits)
    if records.keys() != policies.keys():
        raise ValueError('Missing focus outcome events')
    return output, records
