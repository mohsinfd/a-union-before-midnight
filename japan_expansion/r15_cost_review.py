"""Independent coherent packet-cost comparisons from native data and programmes.

Arithmetic planning evidence, never a claim of a measured production screen.
"""
import json
from collections import Counter
import build as b
import r15_common as common
from construction_safety import effective_award
from r14_construction_review import applications,research_snapshot,changes,policy_tables


BRIGADES={'cag','light_cag','anti_air'}
AIR={'interceptor','multi_role','naval_bomber','tactical_bomber','cas','transport_plane','cag','light_cag'}
NAVAL={'carrier','light_carrier','escort_carrier','destroyer','light_cruiser','transport','submarine'}


def tech_gate(node,known,year):
    result=[]
    for k,v in node:
        if k=='AND':result.append(tech_gate(v,known,year))
        elif k=='OR':result.append(any(tech_gate([(a,z)],known,year) for a,z in v))
        elif k=='NOT':result.append(not any(tech_gate([(a,z)],known,year) for a,z in v))
        elif k=='year':result.append(year>=int(v))
        elif k=='technology':result.append(str(b.get(v,'value')) in known if isinstance(v,list) else str(v) in known)
        else:raise AssertionError(('Unexpected equipment selector',k,v))
    return all(result)


def packet(commands,known,year):
    chosen=Counter()
    for text in commands:
        n=b.parse(b.resolve(text))
        if b.get(n,'type') not in ('add_division','add_brigade'):continue
        if tech_gate(b.get(n,'trigger',[]),known,year):chosen[b.get(n,'value'),int(b.get(n,'when'))]+=1
    return chosen


def sum_cost(items,modified=None,mult=None):
    return sum(i['count']*(i['cost']+(modified or {}).get(i['unit'],(0,0))[0])*
               (i['days']+(modified or {}).get(i['unit'],(0,0))[1])*
               ((mult or {}).get(i['unit'],1)) for i in items)


def ministers(items,year,traits):
    offices={}
    for line in b.read(b.TARGET/'db/ministers/ministers_jap.csv').splitlines():
        r=line.split(';')
        if not r[0].isdigit() or not(int(r[3])<=year<=min(int(r[4]),int(r[5]))):continue
        effects={}
        for item in items:
            dc=dt=0
            for c in b.getall(traits.get(r[7].lower(),[]),'command'):
                wanted='extra' if item['unit'] in BRIGADES else 'unit'
                scopes=(item['unit'],) if wanted=='extra' else (item['unit'],item['group'],'navy' if item['group']=='naval' else item['group'])
                if b.get(c,'type')!=wanted or b.get(c,'which') not in scopes:continue
                when=b.get(c,'when','all');value=b.num(c,'value')
                if when in ('all','cost'):dc+=value
                if when in ('all','time'):dt+=value
            effects[item['unit']]=(dc,dt)
        score=sum(i['count']*i['cost']*(1+effects[i['unit']][0])*i['days']*(1+effects[i['unit']][1]) for i in items)
        office=r[1].lower()
        if office not in offices or score<offices[office][0]:offices[office]=(score,r[0],r[2],effects)
    selected=[];mod={u:(0,0) for u in {i['unit'] for i in items}}
    initial=sum_cost(items)
    for office,(score,identity,name,effects) in offices.items():
        if score>=initial:continue
        selected.append((office,identity,name))
        for u,(dc,dt) in effects.items():mod[u]=(mod[u][0]+dc,mod[u][1]+dt)
    return selected,mod


def run():
    b.prepare_catalog();apps=applications();by={e.key:e for e in b.EVENTS};rows=[]
    traits={b.get(m,'trait').lower():m for m in b.getall(b.parse(b.read(b.TARGET/'db/ministers/minister_personalities.txt')),'minister')}
    policies=policy_tables();positions={'#_POLICY_FREE_MARKET_':10,'#_POLICY_PROFESSIONAL_ARMY_':6,'#_POLICY_DEFENSE_LOBBY_':10}
    sc=sum(policies[k]['MODIFIER_PRODUCTION_COST'][v-1] for k,v in positions.items())
    st=sum(policies[k]['MODIFIER_PRODUCTION_TIME'][v-1] for k,v in positions.items())
    for year in (1942,1945,1950):
        known=research_snapshot(apps,year)
        for key,project in common.REPORT.items():
            if key.startswith('r15_test_'):continue
            for choice in project['choices']:
                members=packet(choice['rewards'],known,year);items=[]
                for (unit,model),count in members.items():
                    models=b.getall(b.parse(b.read(b.SOURCE/'db/units'/('brigades' if unit in BRIGADES else 'divisions')/(unit+'.txt'))),'model')
                    group='air' if unit in AIR else 'naval' if unit in NAVAL else 'land'
                    item=dict(unit=unit,model=model,count=count,zero=models[0],group=group,cost=b.num(models[model],'cost'),days=b.num(models[model],'buildtime'))
                    items.append(item)
                raw=sum_cost(items);techs=[]
                for item in items:
                    for tid in sorted(known,key=int):
                        dc,dt=changes(b.getall(b.get(apps.get(tid,[]),'effects',[]),'command'),item['unit'],item['group'],item['zero'])
                        item['cost']+=dc;item['days']+=dt
                        if dc or dt:techs.append((item['unit'],tid,dc,dt))
                choices=[]
                for parent in b.EVENTS:
                    if parent.triggered or parent.year>year or parent.gate=='ai = yes ai = no' or parent.key.startswith('r15_'):continue
                    alternatives=[(sum_cost(items),None,{})]
                    for index in range(len(parent.actions)):
                        finish=by.get(parent.key+'_finish_'+str(index))
                        if not finish:continue
                        nodes=[b.parse(b.resolve(t)) for t in effective_award(finish)]
                        delta={i['unit']:tuple(changes(nodes,i['unit'],i['group'],i['zero'])) for i in items}
                        if all(i['cost']+delta[i['unit']][0]>0 and i['days']+delta[i['unit']][1]>0 for i in items):alternatives.append((sum_cost(items,delta),index,delta))
                    best,index,delta=min(alternatives,key=lambda a:a[0])
                    if index is not None:
                        choices.append((parent.key,index))
                        for item in items:item['cost']+=delta[item['unit']][0];item['days']+=delta[item['unit']][1]
                programmes=sum_cost(items)
                cabinet,mods=ministers(items,year,traits)
                multipliers={u:(1+sc+v[0])*(1+st+v[1])*.65 for u,v in mods.items()}
                assert all(v>0 for v in multipliers.values())
                stress=sum_cost(items,mult=multipliers)
                cost=choice['cost'];gross=cost.get('supplies',0)/4+cost.get('money',0)/.2
                rows.append(dict(year=year,proposal=key,choice=choice['choice'],units=[{k:v for k,v in i.items() if k!='zero'} for i in items],
                    raw_ic_days=round(raw,2),research_programme_ic_days=round(programmes,2),stressed_ic_days=round(stress,2),
                    programme_choices=choices,cabinet=cabinet,paid_resources=cost,days=choice['days'],gross_stock_ic_days=round(gross,2)))
    report=dict(passed=True,game_run=False,rows=rows,
       scope='One actual choice per programme and one date-eligible minister per office for the entire packet. Research follows compatible Japanese prerequisites; map and political appointment constraints relaxed as a generous stress bound. Includes fixed native-model-zero research changes, explicit programme reductions, named slider positions and65% serial-gearing floor. CAG in air group is conservative. Gross stock conversion uses unmodified4supplies/IC and0.2money/IC, excludes oil/material value and payments returned at delivery. No engine timing, rounding or exact campaign exchange rate asserted.')
    (b.HERE/'R15_COST_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# R15 packet cost audit','',report['scope'],'','| Year | Plan / alternative | Raw IC-days | After research/programmes | Stress bound | Paid stock illustration | Wait |','|---|---|---|---|---|---|---|']
    for r in rows:lines.append(f"| {r['year']} | {r['proposal']} / {r['choice']} | {r['raw_ic_days']:g} | {r['research_programme_ic_days']:g} | {r['stressed_ic_days']:g} | {r['gross_stock_ic_days']:g} | {r['days']} |")
    lines+=['','The carrier-recovery branch was enlarged after this comparison exposed an excessively favourable shore-air alternative. The paid fleet now contains two Light Carriers, two Light CAGs and four Destroyers, takes330days and ties up the major commitment. Shore aviation remains quicker and cheaper, and depends on usable airfields. The fleet buys mobile sea coverage and escorted hulls rather than matching bomber firepower on land.','',
       'Packets are finite. Stock purchases do not consume a normal production slot after payment; the extra commitment delay, crew requirements, location and alternative forgone are part of the price. These calculations support comparisons; they do not prove equal combat utility.']
    (b.HERE/'R15_COST_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,rows=len(rows),recovery=[r for r in rows if r['proposal']=='r15_carrier_recovery'])))
    return report


if __name__=='__main__':run()
