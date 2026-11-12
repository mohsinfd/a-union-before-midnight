"""Read-only snapshot audit of the user's December 1941 manual save."""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from build import HERE, TARGET, GAME, SOURCE, read, parse, get, getall, province_names
from repair_completion_save import effective_ic


def vals(n, k):
    return [v for _, v in get(n, k, [])]


def scalar(n):
    return {k: v for k, v in n if not isinstance(v, list)}


def run():
    source = TARGET/'scenarios/save games/sdEmpire of Japan_1941_November_5.eug'
    before = source.stat(); raw = source.read_bytes(); after = source.stat()
    assert before.st_mtime_ns == after.st_mtime_ns and len(raw) == after.st_size
    folder = HERE/'dec1941_assessment'; folder.mkdir(exist_ok=True)
    (folder/'manual_snapshot.eug').write_bytes(raw)
    warnings = []; root = parse(raw.decode('latin1'), warnings)
    cs = {get(c, 'tag'): c for c in getall(root, 'country')}
    ps = {int(get(p, 'id')): p for p in getall(root, 'province')}
    names = province_names()
    mp = TARGET/'map/Map_1/Province.csv'
    if not mp.exists(): mp = GAME/'map/Map_1/Province.csv'
    rows = {int(r['Id']): r for r in csv.DictReader(read(mp).splitlines(), delimiter=';') if r['Id'].isdigit()}
    type_nodes = [(k,v) for k,v in parse(read(TARGET/'db/units/division_types.txt')) if k != 'eyr']
    types = [k for k,v in type_nodes]
    engine_types = {k:get(v,'type') for k,v in type_nodes}
    brigtypes = [k for k, v in parse(read(TARGET/'db/units/brigade_types.txt')) if k != 'eyr']
    def describe(d, formation=None, kind=None):
        mod = vals(d, 'mod'); a = [float(v) for v in vals(d, 'all')]
        index = int(mod[0]) if mod else -1
        loc = get(formation or [], 'location', get(d, 'location'))
        loc = int(loc) if loc is not None else None
        return {'name': get(d, 'name'), 'id': get(d, 'id'), 'class': get(d, 'type', types[index] if 0 <= index < len(types) else str(index)),
                'model': int(mod[2]) if mod else get(d, 'model'), 'mod': mod,
                'strength': float(get(d, 'strength', a[0] if a else 0)),
                'max_strength': a[1] if len(a)>1 else None,
                'org': a[2] if len(a)>2 else None, 'max_org': a[3] if len(a)>3 else None,
                'supply_use': a[7] if len(a)>7 else None, 'fuel_use': a[8] if len(a)>8 else None,
                'all': a, 'brig': vals(d, 'brig'), 'land': vals(d, 'land'), 'naval': vals(d, 'naval'), 'air': vals(d, 'air'),
                'location': loc, 'province': names.get(loc), 'area': rows.get(loc, {}).get('Area'),
                'region': rows.get(loc, {}).get('Region'), 'continent': rows.get(loc, {}).get('Continent'),
                'formation': get(formation or [], 'name'), 'base': get(formation or [], 'base'),
                'leader': scalar(get(formation or [], 'leader', [])), 'mission': get(formation or [], 'mission'), 'kind': kind}
    allunits = {}
    summaries = {}
    for tag, c in cs.items():
        us = [describe(d, f, kind) for kind in ('landunit', 'navalunit', 'airunit') for f in getall(c, kind) for d in getall(f, 'division')]
        pools = [describe(d, kind=kind) for kind in ('landdivision', 'navaldivision', 'airdivision') for d in getall(c, kind)]
        allunits[tag] = us
        controlled = {int(v) for v in vals(c, 'controlledprovinces')}
        owned = {int(v) for v in vals(c, 'ownedprovinces')}
        cores = {int(v) for v in vals(c, 'nationalprovinces')}
        sizes = {p: effective_ic(ps.get(p, []), float(rows.get(p, {}).get('IC') or 0))[0] for p in controlled & owned}
        queues = [dict(q) for q in getall(c, 'division_development')]
        summaries[tag] = {'scalars': scalar(c), 'puppet': get(c, 'puppet'), 'deployed': dict(Counter(u['class'] for u in us)),
                          'deployed_land': sum(u['kind']=='landunit' for u in us),
                          'pool': dict(Counter(u['class'] for u in pools)), 'pool_units': pools,
                          'strength_below_90': [{'name':u['name'], 'class':u['class'], 'strength':u['strength'], 'province':u['province']} for u in us if u['strength']<90],
                          'physical_core_ic': sum(v for p,v in sizes.items() if p in cores),
                          'physical_noncore_ic': sum(v for p,v in sizes.items() if p not in cores),
                          'controlled_count':len(controlled), 'owned_count':len(owned), 'queues':queues}
    # Flat saved landdivision records also contain unavailable dormant scenario
    # units. They must never be described as deployable reserves merely because
    # they sit outside landunit formations. Cross-check the original identities.
    initial = get(parse(read(SOURCE/'scenarios/1933/japan.inc')), 'country')
    dormant_ids = {json.dumps(get(d,'id')):d for d in getall(initial,'landdivision') if get(d,'dormant')=='yes'}
    for u in summaries['JAP']['pool_units']:
        initial_unit = dormant_ids.get(json.dumps(u['id']))
        if initial_unit:
            u['initial_dormant'] = True
            u['initial_locked'] = get(initial_unit,'locked')=='yes'
            u['availability'] = 'Unactivated dormant scenario unit; not an available deployment reserve'
    summaries['JAP']['unactivated_scenario_units'] = dict(Counter(u['class'] for u in summaries['JAP']['pool_units'] if u.get('initial_dormant')))
    summaries['JAP']['flat_records_not_established_deployable'] = summaries['JAP'].pop('pool')
    jap = cs['JAP']; g = get(root, 'globaldata'); flags = dict(get(g, 'flags', []))
    spec = json.loads((HERE/'events.json').read_text()); byid = {e['id']:e for e in spec}
    queued = [{'id':get(q,'id'), 'tag':get(q,'tag'), 'hours':get(q,'hour'), 'key':byid.get(int(get(q,'id')),{}).get('key')} for q in getall(get(g,'queued_events',[]),'event')]
    pending = [k for k,v in flags.items() if k.startswith('JX_') and k.endswith('_PENDING') and v=='1']
    pending_matches = {k:[q for q in queued if q['key'] and q['key'].startswith(k[3:-8]+'_finish_')] for k in pending}
    history = getall(get(get(root, 'eyr', []),'history',[]),'name')
    selected = [l for l in history if 'We went with ' in l or ' happened to us.' in l and ' went with ' not in l]
    def members(n): return vals(n,'participant')
    wars = [{'attackers':members(get(w,'attackers',[])), 'defenders':members(get(w,'defenders',[])), 'startdate':get(w,'date')} for w in getall(g,'war')]
    alliances = [{'type':k, 'members':members(v)} for k,v in g if k in ('axis','allies','comintern','alliance')]
    # All controlled Japanese provinces with a coast or a base; units from any ally count separately.
    bases = []
    for pid in map(int, vals(jap,'controlledprovinces')):
        row = rows.get(pid,{}); p=ps.get(pid,[])
        if not (get(p,'naval_base') or get(p,'air_base') or row.get('Beaches')=='1'): continue
        own = [u for u in allunits['JAP'] if u['kind']=='landunit' and u['location']==pid]
        other = [{'tag':tag,'count':sum(u['kind']=='landunit' and u['location']==pid for u in us)} for tag,us in allunits.items() if tag!='JAP']
        bases.append({'id':pid,'name':names.get(pid),'area':row.get('Area'),'region':row.get('Region'),'continent':row.get('Continent'),
                      'beach':row.get('Beaches'),'naval_base':get(p,'naval_base'), 'air_base':get(p,'air_base'),
                      'coastal_fort':get(p,'coastalfort',get(p,'coastal_fort')), 'supplypool':get(p,'supplypool'), 'oilpool':get(p,'oilpool'),
                      'japanese_defenders':[{'name':u['name'],'class':u['class'],'strength':u['strength'],'org':u['org']} for u in own],
                      'other_defenders':[x for x in other if x['count']]})
    fleets=[]
    for f in getall(jap,'navalunit'):
        us=[describe(d,f,'navalunit') for d in getall(f,'division')]
        # B&I heavy cruisers use the light_cruiser engine type and count as
        # screens. CVLs use carrier. Vanilla assumptions give false shortages.
        caps=sum(engine_types.get(u['class']) in ('carrier','escort_carrier','battleship','battlecruiser','heavy_cruiser') for u in us)
        screens=sum(engine_types.get(u['class']) in ('destroyer','light_cruiser') for u in us)
        fleets.append({'name':get(f,'name'),'location':names.get(int(get(f,'location',0))), 'base':names.get(int(get(f,'base',0))),
                       'ships':dict(Counter(u['class'] for u in us)), 'capital_count':caps,'screens':screens,'leader':scalar(get(f,'leader',[])),
                       'mission':get(f,'mission'), 'strength_min':min((u['strength'] for u in us),default=0),
                       'org_min':min((u['org'] for u in us),default=0), 'units':us})
    (folder/'EVIDENCE.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),
        'date':dict(get(get(root,'header'),'startdate')),'parse_warnings':warnings,'summaries':summaries,
        'units':allunits,'bases':bases,'fleets':fleets,'wars':wars,'alliances':alliances,'flags':flags,'queued':queued,
        'pending_matches':pending_matches,'player_event_history':selected,'history_tail':history[-100:],
        'japan_upgrades':get(jap,'upgrade'),'japan_local_flags':get(get(jap,'ai',[]),'flags',[]),'japan_keys':[k for k,v in jap],
        'type_index':types, 'brigade_index':brigtypes,
        'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()},indent=2),encoding='utf8')
    print(json.dumps({'date':dict(get(get(root,'header'),'startdate')), 'warnings':warnings,
      'countries':{tag:{k:summaries[tag][k] for k in ('deployed','deployed_land','physical_core_ic','physical_noncore_ic')} for tag in ('JAP','U87','MAN','ENG','USA','GER','SOV','U02','AST') if tag in summaries},
      'wars':wars,'alliances':alliances,'pending_matches':pending_matches},indent=2))


if __name__=='__main__': run()
