"""BALANCE1 fresh-campaign economy overlay. Pure; no save or installation I/O.

Keep India's naval catch-up. Limit the development/resource chains' output
bonuses, substitute productive mines/refineries for temporary stockpile gifts,
and retain finite, paid, mutually exclusive projects. No resource refill loop.
"""
from collections import defaultdict
import json
from dh_save_spans import Node, parse, replace

MARKER = '# AUBM_BALANCE1_ECONOMY'
NEW_EVENT_IDS = {9318200, 9318201}
HULLS = 'carrier light_carrier escort_carrier battleship battlecruiser heavy_cruiser light_cruiser destroyer submarine transport'.split()
RESOURCE_SITES = {'energy': 1476, 'metal': 1472, 'rare_materials': 1503, 'oil': 1441}


def actions(e):
    return [f for f in e.fields if f.key == 'action' or (f.key or '').startswith('action_')]


def key(c):
    t = c.get('type')
    if t in ('construct', 'industrial_modifier'):
        return t + ':' + c.get('which')
    if t == 'add_prov_resource':
        return t + ':' + c.get('where')
    return t


def command(kind, value, which=None, where=None):
    return '{ type = ' + kind + ((' which = ' + str(which)) if which is not None else '') + ((' where = ' + str(where)) if where is not None else '') + ' value = ' + str(value) + ' }'


def resources(**amounts):
    return [command('add_prov_resource', v, RESOURCE_SITES[k], k) for k, v in amounts.items() if v]


def plan(name, changes=None, extra=()):
    return dict(name=name, changes=changes or {}, extra=list(extra))


PLANS = {
 9270200: ('New factories need coal, steel and alloys. City plants give the most capacity. Provincial works combine mines and roads with relief. Business contracts deliver a smaller industrial base and ready stores. Each choice is a lasting investment, not a free annual grant.', [
    plan('City plants: 20 IC and supporting mines', {'construct:ic':[3,3,3,3,2,2,2,2], 'dissent':[0]}, resources(energy=30, metal=15, rare_materials=6)),
    plan('Provincial works: 14 IC, mines and relief', {'construct:ic':[2,2,2,2,2,2,1,1]}, resources(energy=40, metal=20, rare_materials=10)),
    plan('Business contracts: 10 IC and ready stores', {'construct:ic':[2,2,2,2,2], 'dissent':[0]}, resources(energy=20, metal=10, rare_materials=5)),
 ]),
 9270202: ('Factories and raw materials must grow together. State combines build the most workshops. Mixed combines put more money into coal, metal and alloys. Private contracts cost less and conserve manpower. The smaller industrial plans leave more resources for the rest of the economy.', [
    plan('State combines: 24 IC; coal, steel and alloys', {'construct:ic':[3]*8, 'add_prov_resource:metal':[32], 'add_prov_resource:energy':[60], 'industrial_modifier:ic':[1]}, resources(rare_materials=10)),
    plan('Mixed combines: 18 IC; stronger mining output', {'construct:ic':[2,2,3,2,2,2,2,3], 'add_prov_resource:metal':[42], 'add_prov_resource:energy':[72]}, resources(rare_materials=18)),
    plan('Private contracts: 12 IC; lower outlay', {'construct:ic':[3,3,2,2,2], 'add_prov_resource:metal':[28], 'dissent':[0]}, resources(energy=40, rare_materials=8)),
 ]),
 9270203: ('The power budget can build more factories or keep existing ones supplied. River authorities combine industry and power. Coal grids deliver the largest energy increase. District electrification costs less, improves roads and eases discontent. Energy figures are lasting additions to provincial output.', [
    plan('River authorities: 18 IC and 70 energy', {'construct:ic':[3]*6, 'add_prov_resource:energy':[40,30], 'industrial_modifier:energy':[3]}),
    plan('Coal grids: 14 IC and 95 energy', {'construct:ic':[3,3,2,2,2,2], 'add_prov_resource:energy':[95], 'industrial_modifier:energy':[1]}),
    plan('District power: 10 IC, 45 energy and relief', {'construct:ic':[2,2,1,1,1,1,1,1], 'dissent':[-2]}, resources(energy=45)),
 ]),
 9270205: ('The second plan decides what India can sustain. Maximum expansion adds the most factories and a small output bonus. Balanced investment favours fuel, mines and transport. The technology plan builds less but funds research. None makes foreign resources or sea lanes irrelevant.', [
    plan('Maximum plan: 26 IC and supporting resources', {'construct:ic':[3,3,3,3,3,3,3,3,2], 'industrial_modifier:ic':[2]}, resources(energy=50, metal=26, rare_materials=13)),
    plan('Balanced plan: 20 IC, mines and refineries', {'tc_mod':[3]}, resources(energy=65, metal=35, rare_materials=18, oil=15)),
    plan('Technology plan: 12 IC and research', {'industrial_modifier:ic':[0]}, resources(energy=24, metal=12, rare_materials=6)),
 ]),
 9270206: ('India now has a substantial industrial base. The final works add eight factories and a small output improvement. Coal, steel and alloy production expand with them. Further growth still needs investment, trade and secure transport.', [
    plan('Complete the industrial foundation', {'industrial_modifier:ic':[1]}, resources(energy=16, metal=8, rare_materials=4)),
 ]),
 9271400: ('Surveyors have found workable coal, metal and alloy deposits. A national survey diversifies supply; an eastern survey develops more coal and steel first. These investments increase daily provincial production. They do not fill the treasury or create factories.', [
    plan('Survey the Union: diversified deposits', {'add_prov_resource:energy':[24], 'add_prov_resource:metal':[12], 'add_prov_resource:rare_materials':[6]}),
    plan('Develop the eastern coal and metal belt', {'add_prov_resource:energy':[32], 'add_prov_resource:metal':[16]}),
 ]),
 9271401: ('Coal trains cannot keep up with factory orders. A public corridor provides the most coal, metal and better tracks. Private contracts need less money and labour but deliver less output. Both improve lasting production; neither adds another factory-output bonus.', [
    plan('Public corridor: 70 energy, 20 metal, railways', {'add_prov_resource:energy':[70], 'add_prov_resource:metal':[20]}),
    plan('Private mines: 50 energy, 14 metal; lower cost', {'add_prov_resource:energy':[50], 'add_prov_resource:metal':[14], 'dissent':[0]}),
 ]),
 9271402: ('Steelworks need ore, power and reliable railways. Two national centres deliver more metal and stronger transport. A Tata purchase guarantee costs less and preserves labour. The reward is steel supply, not another general factory-output multiplier.', [
    plan('Two steel centres: 60 metal and better railways', {'add_prov_resource:metal':[36,24], 'add_prov_resource:energy':[35], 'industrial_modifier:total':[0]}),
    plan('Tata guarantee: 45 metal; lower cost, no labour levy', {'add_prov_resource:metal':[45], 'add_prov_resource:energy':[28], 'dissent':[0]}, [command('money',-175)]),
 ]),
 9271403: ('A larger fleet needs fuel before war begins. Protected Assam works provide 50 oil and better transport. Faster extraction provides 65 oil but leaves the roads unimproved and adds unrest. Output belongs to the province: losing the oilfields still matters.', [
    plan('Protected Assam works: 50 oil and better roads', {'add_prov_resource:oil':[50], 'add_prov_resource:energy':[24]}),
    plan('Rapid extraction: 65 oil; unrest and no road works', {'add_prov_resource:oil':[65]}),
 ]),
 9271404: ('The central grid can support mines and factories together. The integrated plan adds transport and metal. The power-first plan produces more energy at lower cost but leaves more work for the railway board.', [
    plan('Integrated grid: 80 energy, 25 metal and roads', {'add_prov_resource:energy':[45,35], 'add_prov_resource:metal':[25]}),
    plan('Power first: 105 energy and 16 metal', {'add_prov_resource:energy':[60,45], 'add_prov_resource:metal':[16]}),
 ]),
 9271405: ('India needs a fuel industry large enough to support its new ships and aircraft. Coastal refineries add 90 oil across three ports. Inland synthetic plants add 80 oil, away from the coast, but permanently commit 20 coal output to fuel production. Both need protection and working transport.', [
    plan('Coastal refineries: 90 oil across three ports', {'add_prov_resource:oil':[35,30,25]}),
    plan('Inland synthetic fuel: 80 oil; uses 20 energy', {'add_prov_resource:oil':[40,40], 'add_prov_resource:energy':[-20]}),
 ]),
 9271406: ('Alloys and chemicals are becoming the industrial bottleneck. Domestic works add 40 rare materials and 18 metal to daily provincial output. Imports deliver a large one-time reserve immediately, but do not increase production. Choose lasting output or a stockpile for the coming war.', [
    plan('Domestic works: 40 rare materials and 18 metal', {'add_prov_resource:rare_materials':[16,14,10], 'add_prov_resource:metal':[18]}),
    plan('Import reserves: 10000 rares, 6000 metal, 4000 oil', extra=[command('rarematerialspool',10000),command('metalpool',6000),command('oilpool',4000)]),
 ]),
 9271407: ('A great-power economy needs great-power resource supplies. Domestic investment adds coal, metal, alloys and oil without increasing factory demand. Trade contracts conserve capital and provide immediate reserves, but future imports still depend on suppliers and safe routes.', [
    plan('Domestic security: mines, alloys and 30 oil', {'add_prov_resource:energy':[50,40], 'add_prov_resource:metal':[28,22], 'add_prov_resource:oil':[30], 'industrial_modifier:total':[0]}, resources(rare_materials=12)),
    plan('Trade contracts: smaller mines and ready reserves', {'add_prov_resource:energy':[45], 'add_prov_resource:metal':[28]}, [command('oilpool',5000),command('rarematerialspool',3000)]),
 ]),
 9271408: ('The first plans are complete, but resource needs keep growing. This final expansion adds 35 energy, 20 metal, 12 rare materials and 20 oil to provincial production. It also improves transport. Further fuel and industrial projects become available in 1941 and 1943.', [
    plan('Finish the resource grid, including another 20 oil', {'add_prov_resource:energy':[35], 'add_prov_resource:metal':[20], 'add_prov_resource:rare_materials':[12], 'tc_mod':[2]}, resources(oil=20)),
 ]),
 9280118: ('The provinces want useful works, not another ceremony. Shared works improve eight regional links and ease discontent. Trunk routes improve four main links and transport capacity. Local contracts keep the central budget intact, but offer only modest public relief. Choose once.', [
    plan('Shared works: eight rail links and public relief', {'construct:infrastructure':[10]*8}),
    plan('Trunk routes: four stronger links and transport', {'construct:infrastructure':[20]*4, 'tc_mod':[3]}),
    plan('Local contracts: no central spending, modest relief', {'dissent':[-1]}),
 ]),
}


def requirements(cmds):
    spend = defaultdict(float)
    resource_keys = {'money':'money','supplies':'supplies','manpowerpool':'manpower','oilpool':'oil','energypool':'energy','metalpool':'metal','rarematerialspool':'rare_materials'}
    provinces = set()
    for c in cmds:
        typ = c.get('type'); amount = float(c.get('value','0'))
        if typ in resource_keys and amount < 0:
            spend[resource_keys[typ]] -= amount
        if typ == 'construct': provinces.add(int(c.get('where')))
        if typ == 'add_prov_resource': provinces.add(int(c.get('which')))
    return ' '.join(f'{k} = {v:g}' for k,v in sorted(spend.items())) + ' ' + ' '.join(f'owned = {{ province = {p} data = IND }} control = {{ province = {p} data = IND }}' for p in sorted(provinces))


def modify_commands(text, a, p):
    seen = defaultdict(int); result = []
    for c in a.all('command'):
        raw = text[c.start:c.end]; selector = key(c)
        if selector in p['changes']:
            index = seen[selector]; seen[selector] += 1
            vals = p['changes'][selector]
            if index >= len(vals): raise ValueError('Extra command: '+selector)
            if not vals[index]: continue
            f = c.field('value'); raw = replace(raw,[(f.value_start-c.start, f.end-c.start, str(vals[index]))])
            # Do not allow larger infrastructure increments to overflow 100%.
            if selector == 'construct:infrastructure':
                import re
                raw = re.sub(r'(type\s*=\s*infrastructure\s+value\s*=\s*)0\.\d+', lambda m: m[1]+f'{1-vals[index]/100+.01:.2f}', raw)
        result.append(raw)
    if any(seen[k] != len(v) for k,v in p['changes'].items()):
        raise ValueError('Missing planned command: '+str(p['changes'])+' seen='+str(dict(seen)))
    result.extend(p['extra'])
    return result


def ledger(e):
    out=[]
    for af in actions(e):
        sums=defaultdict(float)
        for c in af.value.all('command'):
            try:sums[key(c)]+=float(c.get('value','0'))
            except ValueError:pass
        out.append(dict(name=af.value.get('name'),effects=dict(sums)))
    return out


def project(eid, year, prerequisite, flag, title, oil, cost):
    valid=f'year = {year} flag = {prerequisite} NOT = {{ flag = {flag} }}'
    a=resources(oil=oil,energy=20)+[command('money',-cost),command('supplies',-cost*2),command('manpowerpool',-10),'{ type = setflag which = '+flag+' }']
    b=resources(oil=oil//2,energy=80,metal=40,rare_materials=20)+[command('money',-(cost-200)),command('supplies',-(cost-200)*2),command('manpowerpool',-8),'{ type = setflag which = '+flag+' }']
    choices=[]; gates=[]
    for i,(name,cmds) in enumerate([(f'Fuel first: {oil} oil and 20 energy',a),(f'Balanced works: {oil//2} oil and more industrial materials',b)]):
        gate=requirements(parse(' '.join('command = '+c for c in cmds)).all('command'));gates.append('AND = { '+gate+' }')
        choices.append('action = { ai_chance = 50 trigger = { '+valid+' '+gate+' } name = '+json.dumps(name)+'\n'+'\n'.join('command = '+c for c in cmds)+'\n}')
    return f'''\nevent = {{
 {MARKER}
 id = {eid} random = no persistent = yes country = IND
 decision = {{ {valid} }}
 decision_trigger = {{ OR = {{ {' '.join(gates)} }} }}
 trigger = {{ ai = yes {valid} OR = {{ {' '.join(gates)} }} }}
 name = "{title}"
 desc = "The services need fuel; the factories need coal, metal and alloys. Fund one lasting expansion: a larger fuel industry, or a mixed resource programme. Both consume money, supplies and manpower. No factories or combat bonuses are added. Production belongs to the improved provinces. You may wait."
 style = 2 picture = "india_v3_industry" decision_picture = "decision_invest_infrastructures"
 date = {{ day = 0 month = january year = {year} }} offset = 15 deathdate = {{ day = 29 month = december year = 1964 }}
 {' '.join(choices)}
 action = {{ ai_chance = 0 name = "Not now - keep the budget uncommitted" }}
}}
'''


def transform(files):
    output=dict(files); records=[]; found=set()
    navy_ids={9271111,9271112,9297180,9297181,9297182}
    for path,text in files.items():
        if not path.startswith('db/events/') or not path.endswith('.txt'):continue
        edits=[]
        for e in parse(text).all('event'):
            eid=int(e.get('id'))
            if eid not in PLANS and eid not in navy_ids:continue
            if eid in found:raise ValueError('Duplicate balance event '+str(eid))
            found.add(eid)
            if MARKER in text[e.start:e.end]:continue
            if eid in navy_ids:
                changes=[]
                for a in actions(e):
                    for c in a.value.all('command'):
                        if c.get('type')!='build_time':continue
                        value=int(c.get('value')); tr=c.get('trigger',Node())
                        # The initial/legacy peace standards remain -25. War adds -15.
                        if eid in (9271111,9271112) and tr.get('atwar')=='yes': new=-15
                        elif eid==9297181:new=15
                        elif eid==9297182:new=-15
                        else:continue
                        f=c.field('value');changes.append((f.value_start,f.end,str(new)))
                # Legacy mature saves are deliberately not migrated by this fresh-game patch.
                desc='National yards keep a 25 percent base-schedule discount in peace. Wartime shifts add 15 points, for 40 percent in total. Normal technology discounts still apply. Daily IC cost is unchanged. This standard is for new campaigns; existing orders may retain their dates.'
                f=e.field('desc');changes.append((f.value_start,f.end,json.dumps(desc)))
                changes.append((e.start+1,e.start+1,'\n'+MARKER+'\n'))
                edits.extend(changes);records.append(dict(id=eid,kind='naval_schedule',peace=25,war=40,legacy_migration=False))
                continue
            prose,plans=PLANS[eid]; original=actions(e)
            if len(original)<len(plans):raise ValueError('Missing options '+str(eid))
            context=e.get('decision') or e.get('trigger')
            if not isinstance(context,Node):raise ValueError('Missing context '+str(eid))
            ctx=text[context.start+1:context.end-1]
            gates=[]
            for af,p in zip(original,plans):
                cmds=modify_commands(text,af.value,p)
                parsed=parse('\n'.join('command = '+c for c in cmds)).all('command')
                gate=requirements(parsed);gates.append('AND = { '+gate+' }')
                body=af.key+' = {\n trigger = { '+ctx+' '+gate+' }\n ai_chance = '+af.value.get('ai_chance','50')+'\n name = '+json.dumps(p['name'])+'\n'+'\n'.join(' command = '+c for c in cmds)+'\n}'
                edits.append((af.start,af.end,body))
            f=e.field('desc');edits.append((f.value_start,f.end,json.dumps(prose)))
            edits.append((e.start+1,e.start+1,'\n'+MARKER+'\n'))
            # Resource popups cannot arrive with every funded action unavailable.
            if e.get('decision') is None:
                tr=e.get('trigger');edits.append((tr.end-1,tr.end-1,'\n OR = { '+' '.join(gates)+' }\n'))
            elif e.get('decision_trigger') is not None:
                tr=e.get('decision_trigger');edits.append((tr.start,tr.end,'{ OR = { '+' '.join(gates)+' } }'))
            records.append(dict(id=eid,kind='paid_economy_choice',before=ledger(e)))
        output[path]=replace(text,edits)
    expected=set(PLANS)|navy_ids
    if not expected<=found:raise ValueError('Missing installed baseline events '+str(expected-found))
    rel='db/events/india_v3/22_resources.txt'
    present={int(e.get('id')) for p,t in output.items() if p.startswith('db/events/') for e in parse(t).all('event') if isinstance(e,Node)}
    if NEW_EVENT_IDS & present and not NEW_EVENT_IDS<=present:raise ValueError('Partial late project installation')
    if not NEW_EVENT_IDS & present:
        output[rel]+=project(9318200,1941,'ind_v3_refinery_program','ind_balance1_resource_1941','Fuel for a World Fleet',80,1000)
        output[rel]+=project(9318201,1943,'ind_balance1_resource_1941','ind_balance1_resource_1943','Resources for a Long War',100,1400)
        records.append(dict(kind='late_resource_projects',ids=sorted(NEW_EVENT_IDS),repeatable=False))
    return output,records
