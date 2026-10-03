"""Bounded, non-installing balance pass for the six 1933-38 development choices.

Preserves IDs, branch/completion flags, team unlocks and provincial build caps.
Factory gains are never raised. Permanent research/logistics changes are finite,
mutually exclusive investments, not repeatable boosters. Native balance and UI
testing remain pending: this module only rewrites supplied text in memory.
"""
from dh_save_spans import Node, parse, replace

MARKER = '# AUBM_STAGED_ECONOMY_V1'
MONTHS = 'january february march april may june july august september october november december'.split()


def option(name, changes=None, extra=()):
    return dict(name=name, changes=changes or {}, extra=list(extra))


PLANS = {
    9270200: dict(
        desc='The first reconstruction budget cannot do everything. Large city plants promise the most factory capacity; smaller provincial works ease discontent. Business houses offer fewer factories but deliver field stores immediately, in return for a freer market.',
        options=[
            option('City plants: 24 IC, larger investment', {'money': [-375], 'supplies': [-1000], 'dissent': [2]}),
            option('Provincial works: 16 IC, ease discontent'),
            option('Business contract: 6 IC and ready stores', {'money': [-225], 'supplies': [600], 'dissent': [1], 'construct:ic': [1, 1, 1, 1, 2]}),
        ]),
    9270201: dict(
        desc='Railways, ports and frontier roads compete for the same crews. Trunk lines move the army more efficiently. Port works bring a modest merchant fleet. Frontier roads sacrifice factory growth for ready supplies and fuel near the next emergency.',
        options=[
            option('Trunk rail: 8 IC and transport capacity'),
            option('Ports: 5 IC and a merchant fleet', {'money': [-325], 'construct:ic': [1, 1, 1, 1, 1]},
                   ('type = transport_pool which = IND value = 40',
                    'type = escort_pool which = IND value = 10')),
            option('Frontier roads: 4 IC and field reserves', {'money': [-350], 'supplies': [400], 'construct:ic': [1, 1, 1, 1]},
                   ('type = oilpool value = 500',)),
        ]),
    9270202: dict(
        desc='Steel orders have outgrown the workshops. State combines offer the largest industrial expansion, at a heavy cost and with tighter economic control. Mixed firms build less but fill raw-material depots now. Private contracts conserve labour and capital at the price of a smaller industrial base.',
        options=[
            option('State combines: 32 IC, tighter control', {'dissent': [2]}),
            option('Mixed combines: 16 IC and raw reserves', {'supplies': [-500], 'construct:ic': [2]*8, 'industrial_modifier:ic': [0]},
                   ('type = metalpool value = 1000', 'type = energypool value = 2000')),
            option('Private contracts: 10 IC, lower outlay', {'construct:ic': [2]*5, 'dissent': [1]},
                   ('type = money value = -200',)),
        ]),
    9270203: dict(
        desc='Power shortages reach the cabinet in stacks of factory petitions. River authorities build the largest lasting base. Coal grids trade some factory growth for an emergency fuel reserve. District electrification offers fewer factories but helps settle discontent and improves rural roads.',
        options=[
            option('River authorities: 24 IC, lasting power'),
            option('Coal grids: 18 IC and energy reserves', {'construct:ic': [3]*6},
                   ('type = energypool value = 2500',)),
            option('District power: 8 IC and public relief', {'construct:ic': [1]*8, 'manpowerpool': [-10, 0]},
                   ('type = money value = -150',)),
        ]),
    9270204: dict(
        desc='Scientists ask what the country expects of them. Planning institutes combine applied research with factories. Independent universities concentrate on research alone. Defence laboratories deliver a smaller industrial base and immediate military stores, while strengthening the defence lobby.',
        options=[
            option('Planning institutes: 10 IC, research +2', {'research_mod': [2]}),
            option('Universities: research +4, no factories', {'money': [-350], 'construct:ic': [0, 0, 0]}),
            option('Defence labs: 6 IC, research +2, stores', {'money': [-500], 'supplies': [500], 'research_mod': [2], 'construct:ic': [2, 2, 2]}),
        ]),
    9270205: dict(
        desc='The second plan must choose its ambition. Maximum industrialisation delivers the most factories but strains society and the treasury. Balanced investment favours transport and fuel reserves. A technology-led plan forgoes much of that capacity to support research.',
        options=[
            option('Maximum plan: 34 IC, factory output +5', {'dissent': [3]}),
            option('Balanced plan: 20 IC, transport and fuel', {'supplies': [-1800], 'dissent': [0], 'construct:ic': [2]*10, 'industrial_modifier:ic': [0]},
                   ('type = tc_mod value = 5', 'type = oilpool value = 1000')),
            option('Technology plan: 12 IC, research +3', {'construct:ic': [2]*6, 'industrial_modifier:ic': [1]}),
        ]),
}


def actions(event):
    return [f for f in event.fields if f.key == 'action' or (f.key or '').startswith('action_')]


def selector(command):
    kind = command.get('type')
    if kind in ('construct', 'industrial_modifier'):
        return kind + ':' + command.get('which')
    return kind


def ledger(commands):
    """Summed exact command deltas; provincial entries remain separately auditable."""
    result = {}
    for c in commands:
        key = selector(c)
        if key in ('setflag', 'waketeam', 'domestic'):
            key += ':' + c.get('which')
        elif key == 'add_prov_resource':
            key += ':' + c.get('which') + ':' + c.get('where')
        val = c.get('value')
        if val is not None:
            result[key] = result.get(key, 0) + int(val)
    return result


def revised_commands(text, action, plan):
    seen = {key: 0 for key in plan['changes']}
    output = []
    for cmd in action.all('command'):
        raw = text[cmd.start:cmd.end]
        key = selector(cmd)
        if key in seen:
            index = seen[key]
            values = plan['changes'][key]
            if index >= len(values):
                raise ValueError('Unexpected extra command for ' + key)
            seen[key] += 1
            if values[index] == 0:
                continue
            field = cmd.field('value')
            raw = replace(raw, [(field.value_start-cmd.start, field.end-cmd.start, str(values[index]))])
        output.append(raw)
    for key, count in seen.items():
        if count != len(plan['changes'][key]):
            raise ValueError('Missing expected command for ' + key)
    output.extend('{ ' + c + ' }' for c in plan['extra'])
    return output


def commands_from(strings):
    return parse('\n'.join('command = ' + c for c in strings)).all('command')


def requirements(commands):
    """Require gross spending, and ownership of every funded provincial site.

    Existing per-command ownership and construction caps are preserved too.
    Owning all sites avoids paying a full national budget for a partial reward.
    """
    costs, provinces = {}, set()
    stocks = {'money': 'money', 'supplies': 'supplies', 'manpowerpool': 'manpower',
              'oilpool': 'oil', 'metalpool': 'metal', 'energypool': 'energy',
              'rarematerialspool': 'rare_materials'}
    for c in commands:
        kind, value = c.get('type'), int(c.get('value', 0))
        if kind in stocks and value < 0:
            key = stocks[kind]
            costs[key] = costs.get(key, 0) - value
        if kind == 'construct':
            provinces.add(int(c.get('where')))
        elif kind == 'add_prov_resource':
            provinces.add(int(c.get('which')))
    return ' '.join(f'{k} = {v}' for k, v in costs.items()) + ' ' + ' '.join(
        f'owned = {{ province = {p} data = IND }}' for p in sorted(provinces))


def date_gate(event):
    date, end = event.get('date'), event.get('deathdate')
    if date.get('day') != '0' or end.get('day') != '29':
        raise ValueError('Unexpected development calendar')
    year, month = int(date.get('year')), MONTHS.index(date.get('month'))
    end_year, end_month = int(end.get('year')), MONTHS.index(end.get('month'))
    end_gate = f'NOT = {{ year = {end_year+1} }}'
    if end_month < 11:
        end_gate += f' NOT = {{ AND = {{ year = {end_year} month = {end_month+1} }} }}'
    return f'OR = {{ year = {year+1} AND = {{ year = {year} month = {month} }} }} ' + end_gate


def transform(files):
    result, records = dict(files), {}
    occurrences = {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event' or not isinstance(ef.value, Node):
                continue
            event = ef.value
            eid = int(event.get('id'))
            if eid not in PLANS:
                continue
            if eid in occurrences:
                raise ValueError(f'Duplicate economy event {eid}')
            occurrences[eid] = path
            raw = text[ef.start:ef.end]
            if MARKER in raw:
                # Reconstruct the report from the marked result without changing it.
                records[eid] = [{'dimension': 'economy_choices', 'status': 'reviewed',
                    'detail': 'Already staged bounded development choices; no further rewrite.',
                    'engine_tested': False, 'path': path,
                    'after': [ledger(a.value.all('command')) for a in actions(event)[:3]],
                    'remaining': ['Native UI and comparative campaign balance testing pending.']}]
                continue
            source_actions = actions(event)
            if event.get('country') != 'IND' or len(source_actions) != 3:
                raise ValueError(f'Unexpected economy definition {eid}')
            spec = PLANS[eid]
            context = event.get('decision')
            if not isinstance(context, Node):
                raise ValueError(f'Missing development decision {eid}')
            context_text = text[context.start+1:context.end-1].strip() + ' ' + date_gate(event)
            terminal = set.intersection(*[
                {c.get('which') for c in af.value.all('command') if c.get('type') == 'setflag'}
                for af in source_actions])
            if len(terminal) != 1 or f'NOT = {{ flag = {next(iter(terminal))} }}' not in context_text:
                raise ValueError(f'Missing common one-time completion guard {eid}')
            updated_actions, option_gates, before, after = [], [], [], []
            for af, plan in zip(source_actions, spec['options']):
                strings = revised_commands(text, af.value, plan)
                commands = commands_from(strings)
                gate = requirements(commands)
                option_gates.append('AND = { ' + gate + ' }')
                before.append(ledger(af.value.all('command')))
                after.append(ledger(commands))
                updated_actions.append(f'{af.key} = {{\n'
                    f' trigger = {{ {context_text} {gate} }}\n'
                    f' ai_chance = {af.value.get("ai_chance", "33")}\n'
                    f' name = "{plan["name"]}"\n' +
                    '\n'.join(' command = ' + c for c in strings) + '\n}')
            # Persistent + completion flag means defer does not consume the offer,
            # while even a direct/repeated call cannot grant another paid reward.
            updated_actions.append('action_d = { trigger = { ai = no } ai_chance = 0 '
                                   'name = "Not now - keep the budget uncommitted" }')
            tooltip = ('Choose one programme. Costs and effects are shown on each option. '
                       'All funded provincial sites must still belong to India; capped buildings may not increase. '
                       'Deferring spends nothing and leaves this programme available. Completed programmes cannot be repeated.')
            changes = [(a.start, a.end, '') for a in source_actions]
            for key, value in [('desc', '"' + spec['desc'] + '"'),
                               ('decision_desc', '"' + tooltip + '"'),
                               ('decision_trigger', '{ OR = { ' + ' '.join(option_gates) + ' } }'),
                               ('decision', '{ ' + context_text + ' }')]:
                field = event.field(key)
                changes.append((field.value_start, field.end, value))
            persistent = [f for f in event.fields if f.key == 'persistent']
            if persistent:
                changes.append((persistent[0].value_start, persistent[0].end, 'yes'))
            else:
                changes.append((event.start+1, event.start+1, '\n persistent = yes\n'))
            changes.append((event.end-1, event.end-1, '\n' + MARKER + '\n' + '\n'.join(updated_actions) + '\n'))
            raw = replace(raw, [(s-ef.start, e-ef.start, val) for s, e, val in changes])
            edits.append((ef.start, ef.end, raw))
            records[eid] = [{'dimension': 'economy_choices', 'status': 'reviewed',
                'detail': 'Three exclusive investments: capacity, logistics/reserves or research; current-state spending guards and free defer.',
                'path': path, 'engine_tested': False, 'before': before, 'after': after,
                'completion_flag': next(iter(terminal)),
                'remaining': ['Native UI and comparative campaign balance testing pending.',
                              'Other economy/resource/boost families are outside this six-event pass.']}]
        if edits:
            result[path] = replace(text, edits)
    return result, records
