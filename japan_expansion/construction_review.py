"""Bound new construction modifiers against real templates and assembly techs.

No executable is started. Each row optimises its own programme alternatives;
the whole table is not one simultaneously achievable campaign build.
"""
from collections import defaultdict
import json
from build import HERE,SOURCE,TARGET,EVENTS,prepare_catalog,parse,get,getall,read,resolve,num


def run():
    prepare_catalog()
    from construction_safety import effective_award
    apps={}
    for p in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for a in getall(tree,'application'):apps[get(a,'id')]=a
    all_teams=[]
    for name in ('jap','U87','ind'):
        p=TARGET/'db/tech/teams'/('teams_'+name+'.csv')
        if p.exists():all_teams.append(p)
    unit_groups={
        'carrier':'naval','light_carrier':'naval','destroyer':'naval','light_cruiser':'naval','submarine':'naval','transport':'naval',
        'interceptor':'air','multi_role':'air','cas':'air','naval_bomber':'air','tactical_bomber':'air','cag':'air','light_cag':'air',
        'infantry':'land','marine':'land','bergsjaeger':'land','armor':'land','motorized':'land',
        'paratrooper':'land','cavalry':'land','transport_plane':'air','d_10':'land','d_11':'land','d_12':'land',
    }
    event_lookup={e.key:e for e in EVENTS}
    records=[]
    for year in (1939,1941,1945,1950):
        for unit,group in unit_groups.items():
            path=SOURCE/'db/units/divisions'/(unit+'.txt')
            if not path.exists():path=(TARGET/'db/units/divisions'/(unit+'.txt')) if unit in {'d_10','d_11','d_12'} else SOURCE/'db/units/brigades'/(unit+'.txt')
            models=getall(parse(read(path)),'model');base=num(models[0],'buildtime')
            unlocks=[]
            for tid,a in apps.items():
                if int(get(a,'year',0))>year:continue
                for c in getall(get(a,'effects',[]),'command'):
                    if get(c,'type')=='new_model' and get(c,'which')==unit and not get(c,'trigger'):
                        unlocks.append((int(get(a,'year',0)),int(get(c,'value')),tid))
            if unit in {'d_10','d_11','d_12'}:
                from specialist_units import model_years,model_techs
                unlocks=[(y,i,str(model_techs(unit)[i])) for i,y in enumerate(model_years(unit)) if y<=year]
            if not unlocks:continue
            _,index,tech=max(unlocks)
            if index>=len(models):raise AssertionError((unit,index,len(models)))
            template=models[index];raw=num(template,'buildtime');cost=num(template,'cost')
            assembly_delta=0;assembly_ids=[]
            if year>=1940:
                from specialist_units import CLASSES
                assembly_unit=CLASSES[unit]['base'] if unit in CLASSES else unit
                for tid in ('5140','5150','5160','5180'):
                    app=apps[tid]
                    for c in getall(get(app,'effects',[]),'command'):
                        if get(c,'type')=='build_time' and get(c,'which')==assembly_unit:
                            assert get(c,'where')=='relative'
                            assembly_delta+=base*num(c,'value')/100
                            assembly_ids.append(tid)
            programme=0;programme_cost=0;selected=[]
            for parent in EVENTS:
                if parent.triggered or parent.year>year or parent.gate=='ai = yes ai = no':continue
                alternatives=[]
                cost_alternatives=[]
                for i,action in enumerate(parent.actions):
                    finish=event_lookup.get(parent.key+'_finish_'+str(i))
                    if finish is None:continue
                    delta=0
                    cost_delta=0
                    for text in effective_award(finish):
                        c=parse(resolve(text))
                        if get(c,'type')=='build_time' and get(c,'which') in {unit,group}:
                            delta+=num(c,'value')*(base/100 if get(c,'where')=='relative' else 1)
                        if get(c,'type')=='build_cost' and get(c,'which') in {unit,group}:
                            cost_delta+=num(c,'value')*(num(models[0],'cost')/100 if get(c,'where')=='relative' else 1)
                    alternatives.append((delta,i))
                    cost_alternatives.append(cost_delta)
                if alternatives:
                    delta,choice=min(alternatives)
                    if delta<0:programme+=delta;selected.append((parent.key,choice,delta))
                    programme_cost+=min(cost_alternatives)
            subtotal=raw+assembly_delta
            total=subtotal+programme
            records.append({'year':year,'unit':unit,'model':index,'model_tech':tech,'model_zero_days':base,'template_days':raw,'template_ic':cost,'assembly_techs':assembly_ids,'assembly_days_delta':round(assembly_delta,2),'new_programme_days_delta':programme,'subtotal_days':round(subtotal,2),'bounded_days':round(total,2),'bounded_ic':round(cost+programme_cost,2),'bounded_ic_days':round(total*(cost+programme_cost),2),'programmes':selected})
    nonpositive=[r for r in records if r['bounded_days']<=0 or r['bounded_ic']<=0]
    lines=['# Construction stacking review','',
        'Read-only review of Blood and Iron templates/assembly technologies and the prepared Japan Rising catalogue. This is an arithmetic bound, not a production-screen measurement.','',
        '## Command semantics','',
        'The installed engine manual states that build_time without `where = relative` is an absolute addition. Japan Rising uses direct days. A value of -40 therefore removes 40 days, not 40 percent. Blood and Iron assembly commands use `where = relative`: -26 means subtract 26% of model-zero time from every model. The previous wording “model-zero days” for the new absolute modifiers was imprecise.','',
        '## Method and limits','',
        '- Select the latest dated unconditional unit-model unlock at each snapshot. This does not prove the player researched it by that year.',
        '- From 1940, include applicable assembly technology 5140/5150/5160/5180, assuming its prerequisites were researched. The year is a comparison snapshot, not a promised research schedule.',
        '- For each eligible-year programme, choose whichever funded alternative gives the largest time reduction to the row\'s unit. Each programme is counted once. Map, victory, peace and other availability gates are deliberately relaxed for this upper bound.',
        '- The rows do not form one joint set of choices. Land-doctrine modifiers, ministers, sliders, difficulty, gearing, attachments, upgrade/conversion rules and engine rounding are excluded. CAG inclusion in the air category is a conservative bound that still requires engine confirmation.',
        '- Template IC-days illustrate only these inputs. They are not actual campaign IC-days. Research, doctrine and industrial throughput still constrain production.','',
        '| Year | Unit | Model | Raw days | Assembly reduction | Maximum new reduction | Subtotal days | Illustrative IC-days |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['year']} | {r['unit']} | {r['model']} | {r['template_days']:g} | {-r['assembly_days_delta']:g} | {-r['new_programme_days_delta']:g} | {r['bounded_days']:g} | {r['bounded_ic_days']:g} |")
    lines += ['',f'{len(records)} unit/year combinations inspected. {len(nonpositive)} nonpositive subtotal(s) under this stated bound. This does not certify the total game stacking or Hard difficulty.','',
        '## Affordability correction','',
        'R3 moved shared budget and manpower requirements onto the applicable funded actions. L3 replaces Japanese paid military queue grants with construction-time reductions and manual ordering, so those programmes no longer require manpower to insert an order. The player\'s own construction still requires normal manpower and IC. Setup budgets and programme prerequisites remain; delay and dismissal remain available without funding.']
    (HERE/'CONSTRUCTION_BALANCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'CONSTRUCTION_BALANCE.json').write_text(json.dumps({'scope':'Arithmetic upper bound, not engine production verification','nonpositive_subtotals':nonpositive,'rows':records},indent=2))
    print(json.dumps({'unit_year_rows':len(records),'nonpositive_subtotals':len(nonpositive),'game_executed':False}))


if __name__=='__main__':run()
