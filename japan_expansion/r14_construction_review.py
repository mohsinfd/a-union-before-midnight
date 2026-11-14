"""Coherent per-unit construction stress scenarios from installed primary data.

No game process; no fabricated production-screen measurements. Programme gates
are relaxed deliberately to test strong combinations, never to promise a date.
"""
import csv, json, re
from collections import defaultdict
import build as b
import unique_divisions as divisions
import unique_attachments as attachments
from construction_safety import effective_award


def applications():
    return {b.get(a,'id'):a for p in (b.TARGET/'db/tech').glob('*.txt')
            for t in b.getall(b.parse(b.read(p)),'technology') for a in b.getall(t,'application')}


def research_snapshot(apps, year):
    country=b.get(b.parse(b.read(b.SOURCE/'scenarios/1933/japan.inc')),'country')
    known={v for _,v in b.get(country,'techapps',[])}
    blocked=set()
    def exclusions(tid):
        return {b.get(c,'which') for c in b.getall(b.get(apps.get(tid,[]),'effects',[]),'command')
                if b.get(c,'type')=='deactivate'}
    for tid in known:blocked |= exclusions(tid)
    changed=True
    while changed:
        changed=False
        for tid,a in sorted(apps.items(),key=lambda x:(int(b.get(x[1],'year',0)),int(x[0]))):
            required={v for _,v in b.get(a,'required',[])}
            either={v for _,v in b.get(a,'or_required',[])}
            if tid in known or tid in blocked or int(b.get(a,'year',0))>year:continue
            if not required<=known or (either and not either&known):continue
            if exclusions(tid)&known:continue
            known.add(tid);blocked |= exclusions(tid);changed=True
    return known


def changes(nodes, unit, group, base):
    out=[0.,0.]
    for c in nodes:
        typ=b.get(c,'type')
        if typ not in ('build_cost','build_time') or b.get(c,'which') not in (unit,group):continue
        # A specialist's installed mirrors require its activation flag. These
        # rows describe an unlocked class, so its one native-equivalent mirror
        # applies; research catchup events themselves are never summed here.
        if b.get(c,'trigger') and not unit.startswith(('d_','b_')):continue
        i=0 if typ=='build_cost' else 1
        field='cost' if i==0 else 'buildtime'
        out[i]+=b.num(c,'value')*(b.num(base,field)/100 if b.get(c,'where')=='relative' else 1)
    return out


def cabinet(unit, group, year, traits, attachment=False):
    by_office=defaultdict(list)
    for r in csv.reader(b.read(b.TARGET/'db/ministers/ministers_jap.csv').splitlines(),delimiter=';'):
        if not r or not r[0].isdigit() or not (int(r[3])<=year<=min(int(r[4]),int(r[5]))):continue
        costs=times=0.
        for c in b.getall(traits.get(r[7].lower(),[]),'command'):
            expected='extra' if attachment else 'unit'
            scopes=(unit,) if attachment else (unit,group,'navy' if group=='naval' else group)
            if b.get(c,'type')!=expected or b.get(c,'which') not in scopes:continue
            when=b.get(c,'when','all')
            if when in ('cost','all'):costs+=b.num(c,'value')
            if when in ('time','all'):times+=b.num(c,'value')
        by_office[r[1].lower()].append((costs,times,r[0],r[2],r[7]))
    picks=[]
    for rows in by_office.values():
        candidate=min(rows,key=lambda r:(1+r[0])*(1+r[1]))
        if (1+candidate[0])*(1+candidate[1])<1:picks.append(candidate)
    return sum(r[0] for r in picks),sum(r[1] for r in picks),picks


def policy_tables():
    out={};section=None
    for line in b.read(b.SOURCE/'db/policy_effects.csv').splitlines():
        cells=line.split(';')
        if cells[0].startswith('#_POLICY_'):section=cells[0];out[section]={}
        elif section and cells[0] in ('MODIFIER_PRODUCTION_COST','MODIFIER_PRODUCTION_TIME','MODIFIER_GEARING_BONUS'):
            out[section][cells[0]]=[float(v) for v in cells[1:11]]
    return out


def run():
    b.prepare_catalog();apps=applications();by={e.key:e for e in b.EVENTS}
    traits={b.get(m,'trait').lower():m for m in b.getall(b.parse(b.read(b.TARGET/'db/ministers/minister_personalities.txt')),'minister')}
    policies=policy_tables()
    # One explicit legal slider position for each axis, shared by all rows.
    positions={'#_POLICY_FREE_MARKET_':10,'#_POLICY_PROFESSIONAL_ARMY_':6,'#_POLICY_DEFENSE_LOBBY_':10}
    slider_cost=sum(policies[k]['MODIFIER_PRODUCTION_COST'][v-1] for k,v in positions.items())
    slider_time=sum(policies[k]['MODIFIER_PRODUCTION_TIME'][v-1] for k,v in positions.items())
    misc=b.read(b.SOURCE/'db/misc.txt')
    gear=float(re.search(r'# Max Gearing Bonus[^\n]*\n\s*([\d.]+)',misc).group(1))
    entries={**{u:dict(info,folder='divisions') for u,info in divisions.CLASSES.items()},
             **{u:dict(info,folder='brigades') for u,info in attachments.ATTACHMENTS.items()}}
    rows=[]
    for year in (1939,1941,1942,1944,1945,1950):
        known=research_snapshot(apps,year)
        for unit,info in entries.items():
            available=[i for i,y in enumerate(info['years']) if y<=year and str(info['techpairs'][i][0]) in known]
            if not available:continue
            model=max(available);baseunit=info['base'];folder=info['folder']
            native=b.getall(b.parse(b.read(b.SOURCE/'db/units'/folder/(baseunit+'.txt'))),'model')
            custom=(divisions.models(unit) if folder=='divisions' else attachments.models(unit))
            if folder=='divisions':native_index=info['base_models'][model]
            else:
                unlocks=[int(b.get(c,'value')) for tid in known for c in b.getall(b.get(apps[tid],'effects',[]),'command') if b.get(c,'type')=='new_model' and b.get(c,'which')==baseunit and not b.get(c,'trigger')]
                native_index=max(unlocks) if unlocks else min(model,len(native)-1)
            group=info.get('branch') or ('naval' if baseunit=='destroyer' else 'air' if baseunit in ('naval_bomber','multi_role') else 'land')
            pair=[]
            for member,template,zero in ((baseunit,native[native_index],native[0]),(unit,custom[model],custom[0])):
                cost=b.num(template,'cost');days=b.num(template,'buildtime');tech_details=[]
                for tid in sorted(known,key=int):
                    nodes=b.getall(b.get(apps.get(tid,[]),'effects',[]),'command')
                    dc,dt=changes(nodes,member,group,zero)
                    if dc or dt:cost+=dc;days+=dt;tech_details.append((tid,dc,dt))
                selected=[]
                for parent in b.EVENTS:
                    if parent.triggered or parent.year>year or parent.gate=='ai = yes ai = no':continue
                    alternatives=[(cost*days,0.,0.,None)]
                    for index in range(len(parent.actions)):
                        finish=by.get(parent.key+'_finish_'+str(index))
                        if not finish:continue
                        dc,dt=changes([b.parse(b.resolve(c)) for c in effective_award(finish)],member,group,zero)
                        if cost+dc>0 and days+dt>0:alternatives.append(((cost+dc)*(days+dt),dc,dt,index))
                    _,dc,dt,index=min(alternatives,key=lambda option:option[0])
                    if index is not None and (dc or dt):
                        cost+=dc;days+=dt;selected.append((parent.key,index,dc,dt))
                mc,mt,picks=cabinet(member,group,year,traits,folder=='brigades')
                # Both orders bound the undocumented cross-system rounding/order;
                # use no engine clamp to hide a negative component.
                assert cost>0 and days>0,(member,year,cost,days)
                combined_cost=1+slider_cost+mc;combined_time=1+slider_time+mt
                multiplied_cost=(1+slider_cost)*(1+mc);multiplied_time=(1+slider_time)*(1+mt)
                assert min(combined_cost,combined_time,multiplied_cost,multiplied_time)>0
                pair.append(dict(unit=member,model=native_index if member==baseunit else model,
                    template_ic=b.num(template,'cost'),template_days=b.num(template,'buildtime'),
                    technology_effects=tech_details,programme_choices=selected,ic=round(cost,4),days=round(days,4),
                    cabinet=picks,cabinet_cost_modifier=mc,cabinet_time_modifier=mt,
                    stressed_ic_days_additive=round(cost*combined_cost*days*combined_time*gear,4),
                    stressed_ic_days_multiplicative=round(cost*multiplied_cost*days*multiplied_time*gear,4)))
            rows.append(dict(year=year,unit=unit,parent=baseunit,models=pair,
                ratio=round(pair[1]['ic']*pair[1]['days']/(pair[0]['ic']*pair[0]['days']),4),
                stress_ratio=round(pair[1]['stressed_ic_days_additive']/pair[0]['stressed_ic_days_additive'],4)))
    assert set(entries)=={r['unit'] for r in rows}
    assert all(.45<=r['stress_ratio']<=1.8 for r in rows if r['unit']=='d_18')
    report=dict(passed=True,game_executed=False,unit_families=len(entries),rows=rows,
        slider_positions=positions,slider_cost=slider_cost,slider_time=slider_time,gearing_time_floor=gear,
        human_hard_industry_modifier=0,ai_hard_industry_bonus=.10,ai_hard_manpower_bonus=.20,
        limits='Researched dated prerequisites and mutually exclusive technology branches respected. Programme map/peace gates relaxed per unit. One actual option per programme and one date-eligible Japanese appointment per office; ideology and government restrictions relaxed as a generous bound. Different rows are different choices. Additive and multiplicative cross-system orders reported, no engine rounding asserted. Difficulty changes output, not these templates. Research time, actual IC allocation and engine floor remain playtest checks. Generated model parity is separately verified against the installed files.')
    (b.HERE/'R14_CONSTRUCTION_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# R14 construction review','',report['limits'],'',
           'All seven specialist classes and all three attachments are included. Native assembly reductions mirrored as absolute native-model-zero deltas are read from installed technologies. Doctrine effects enter only on the compatible researched branch. Minister selections use the installed Japanese roster and traits. The stress sliders are free market 10, mobilisation 6 and hawk 10; serial gearing is 65% of initial time. Hard gives the human no direct industry bonus and gives AI +10% industry/+20% manpower.','',
           '| Year | Specialist | Parent | Cost × time after research/programmes | Stressed ratio to parent |','|---|---|---|---|---|']
    for r in rows:
        m=r['models'][1];lines.append(f"| {r['year']} | {r['unit']} | {r['parent']} | {m['ic']:g} × {m['days']:g} | {r['stress_ratio']:.1%} |")
    lines+=['','Matsu keeps its escort role, lower fuel demand and shorter construction, but now uses 80% parent IC and 80% parent time before modifiers. Former values were 75% and 65%. Its reduced range, speed and surface armament remain. This removes the extreme stacked discount while preserving an inexpensive replacement escort.']
    (b.HERE/'R14_CONSTRUCTION_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,rows=len(rows),families=len(entries),matsu=[(r['year'],r['stress_ratio']) for r in rows if r['unit']=='d_18'])))
    return report


if __name__=='__main__':run()
