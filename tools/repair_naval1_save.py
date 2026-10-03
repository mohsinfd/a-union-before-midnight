"""Lossless, explicit ten-order NAVAL1 recovery. Never overwrites the input.

The exceptional recovery uses the original event-requested first-item schedules
and 90% total_progress, with published model/fitting IC costs. It is not an
attempt to emulate the engine's minister/slider price calculator. Costs and
remaining days are recorded in the manifest for inspection and native testing.
"""
from decimal import Decimal
import math
from pathlib import Path
from dh_save_spans import Node, parse, replace, walk
from aubm_naval_clock_fix import CATCHUP, NOTICES, armed, ready

MONTHS = 'january february march april may june july august september october november december'.split()
ORDERS = (
    ('INS Purvasagar', 'battleship', 'naval_fire_controll_l', 360),
    ('INS Chilika', 'light_cruiser', 'naval_fire_controll_s', 150),
    ('INS Coromandel', 'light_cruiser', 'naval_anti_air_s', 150),
    ('1st Bengal Escort Flotilla', 'destroyer', 'naval_asw', 90),
    ('2nd Bengal Escort Flotilla', 'destroyer', 'naval_anti_air_s', 90),
    ('INS Samudra', 'carrier', 'cag', 330),
    ('INS Makran', 'heavy_cruiser', 'naval_fire_controll_s', 210),
    ('INS Malacca', 'heavy_cruiser', 'naval_fire_controll_s', 210),
    ('1st Ocean Escort Flotilla', 'destroyer', 'naval_asw', 90),
    ('2nd Ocean Escort Flotilla', 'destroyer', 'naval_asw', 90),
)
TITLE = 'NAVAL1 - India June 1941 - overdue fleets 90 percent'


def scalar_edit(node, key, value):
    f = node.field(key)
    return f.value_start, f.end, str(value).encode('ascii')


def day_number(date):
    return int(date.get('year')) * 360 + MONTHS.index(date.get('month')) * 30 + int(date.get('day'))


def date_text(number):
    year, left = divmod(number, 360); month, day = divmod(left, 30)
    return f'{{ year = {year} month = {MONTHS[month]} day = {day} hour = 0 }}'


def recover(raw, mod, output_name):
    root = parse(raw)
    india = next(c for c in root.all('country') if c.get('tag') == 'IND')
    globaldata = root.get('globaldata'); flags = globaldata.get('flags')
    if not isinstance(flags, Node): raise ValueError('Missing global flags')
    required = {'ind_v3_arabian_fleet': '1', 'ind_v3_fleet_carrier_authorized': '1',
                'ind_v3_bay_fleet': '0', 'ind_v3_carrier_keels': '0'}
    for key, val in required.items():
        if flags.get(key) != val: raise ValueError(f'Campaign state differs: {key}={flags.get(key)}')
    if flags.get(CATCHUP) == '1': raise ValueError('This save was already recovered')
    if flags.get('ind_v3_two_light_carriers') == '1' or flags.get('ind_v3_submarine_navy') == '1':
        raise ValueError('Conflicting carrier doctrines; do not guess')
    if set(n.get('name') for n in walk(india)) & {o[0] for o in ORDERS}:
        raise ValueError('An overdue named ship already exists; refuse duplication')
    if any(flags.get('ind_redesign_navy_paid_' + str(eid)) == '1' for eid in [9271105,9271106]):
        raise ValueError('Overdue stage already paid; refuse a second charge')
    id_nodes = [n for n in walk(root) if n.get('type') == '4712' and isinstance(n.get('id'), str)]
    next_id = max(int(n.get('id')) for n in id_nodes) + 1
    header = root.get('header'); start = header.get('startdate')
    if (start.get('year'), start.get('month'), start.get('day')) != ('1941','june','0'):
        raise ValueError('Recovery is scoped to the inspected June 1941 autosave')
    now = day_number(start)
    models = india.get('models'); obsolete = india.get('obsolete_models')
    upgrades = india.get('upgrade')
    edits = []
    records = []
    crew_total = Decimal('0')
    blocks = []
    for number, (name, kind, brigade, days) in enumerate(ORDERS):
        unit = parse((mod/'db/units/divisions'/f'{kind}.txt').read_bytes())
        fitting = parse((mod/'db/units/brigades'/f'{brigade}.txt').read_bytes())
        if brigade not in unit.all('allowed_brigades'): raise ValueError(f'Invalid fitting {kind}/{brigade}')
        if india.get('allowed_divisions').get(kind) != 'yes': raise ValueError(f'Locked hull {kind}')
        if india.get('allowed_brigades').get(brigade) != 'yes': raise ValueError(f'Locked fitting {brigade}')
        available = {0} | {int(x) for x in models.get(kind, Node()).atoms()}
        available -= {int(x) for x in obsolete.get(kind, Node()).atoms()}
        model = max(available)
        brigade_model = max({0} | {int(x) for x in models.get(brigade, Node()).atoms()})
        stats = unit.all('model')[model]; bst = fitting.all('model')[brigade_model]
        crew = Decimal(stats.get('manpower','0')) + Decimal(bst.get('manpower','0'))
        for typ in (kind,brigade):
            crew += Decimal(upgrades.get(typ,Node()).get('manpower','0'))
        cost = Decimal(stats.get('cost')) + Decimal(bst.get('cost'))
        cost += Decimal(upgrades.get(kind,Node()).get('cost','0')) + Decimal(upgrades.get(brigade,Node()).get('cost','0'))
        if crew <= 0 or cost <= 0: raise ValueError('Invalid crew/cost')
        crew_total += crew
        remaining = math.ceil(days * .1)
        blocks.append(f'''\n\tdivision_development = {{
        id = {{ type = 4712 id = {next_id + number} }}
        name = "{name}"
        progress = 2
        location = {india.get('capital')}
        cost = {cost:.4f}
        date = {date_text(now + remaining)}
        manpower = {crew:.4f}
        total_progress = 0.9000
        size = 1
        days = {days}
        days_for_first = {days}
        type = {kind}
        model = {model}
        extra = {brigade}
        brigade_model = {brigade_model}
    }}\n''')
        records.append(dict(name=name,kind=kind,model=model,brigade=brigade,brigade_model=brigade_model,
                            progress=0.9,days=days,remaining_days=remaining,ic_cost=str(cost),crew=str(crew),id=next_id+number))
    for key, charge in [('money',Decimal(1400)),('supplies',Decimal(3200)),('manpower',crew_total)]:
        value = Decimal(india.get(key))
        if value < charge: raise ValueError(f'Insufficient {key}')
        edits.append(scalar_edit(india,key,f'{value-charge:.4f}'))
    edits.append((india.end-1,india.end-1,''.join(blocks).encode('ascii')))
    new_flags = {CATCHUP:'1','ind_v3_bay_fleet':'1','ind_v3_carrier_keels':'1',
                 'ind_redesign_navy_paid_9271105':'1','ind_redesign_navy_paid_9271106':'1',
                 armed(9271105):'1',ready(9271105):'1',armed(9271106):'1',ready(9271106):'1',
                 # 90% of the 330-day carrier schedule exceeds the 210-day
                 # authorization interval for the next fleet review.
                 armed(9271107):'1',ready(9271107):'1'}
    additions = []
    for key,val in new_flags.items():
        if flags.get(key) is None: additions.append(f'\n\t\t{key} = {val}')
        else: edits.append(scalar_edit(flags,key,val))
    edits.append((flags.end-1,flags.end-1,(''.join(additions)+'\n\t').encode('ascii')))
    queue = globaldata.get('queued_events')
    if not isinstance(queue,Node): raise ValueError('Missing queued_events block')
    if any(e.get('id') in map(str,NOTICES) for e in queue.all('event')): raise ValueError('Notices already queued')
    notices = ''.join(f'\n\t\tevent = {{ tag = IND id = {eid} hour = {i+1} }}' for i,eid in enumerate(NOTICES))
    edits.append((queue.end-1,queue.end-1,(notices+'\n\t').encode('ascii')))
    edits.append(scalar_edit(header.get('id'),'id',next_id+len(ORDERS)))
    edits.append(scalar_edit(header,'name','"'+TITLE+'"'))
    edits.append(scalar_edit(header,'optionfile','"scenarios\\save games\\'+output_name+'.cfg"'))
    output = replace(raw,edits)
    # Reversibility proof: all bytes outside the explicit edits are preserved.
    reverse=[];delta=0
    for a,b,new in sorted(edits):
        reverse.append((a+delta,a+delta+len(new),raw[a:b]));delta+=len(new)-(b-a)
    if replace(output,reverse) != raw: raise AssertionError('Lossless-save check failed')
    repaired=parse(output);ri=next(c for c in repaired.all('country') if c.get('tag')=='IND')
    prior=[raw[n.start:n.end] for n in india.all('division_development')]
    current=[output[n.start:n.end] for n in ri.all('division_development')[:len(prior)]]
    if current != prior: raise AssertionError('Existing production changed')
    return output, dict(orders=records,charges=dict(money=1400,supplies=3200,manpower=str(crew_total)),
                       existing_production_byte_identical=True,unrelated_bytes_preserved=True,
                       notices_first_game_hours=[1,2],engine_tested=False,
                       initial_cost_basis='Published current hull plus single fitting cost and saved technology cost adjustments; native slider/minister recalculation not emulated',
                       timing_basis='Original requested event first-item schedules; 90 percent complete, 9-36 funded days remaining')
