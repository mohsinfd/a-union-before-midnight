"""Read the starting economy and price the optional early content offline."""
import csv
from collections import defaultdict
import json
from build import HERE,SOURCE,GAME,EVENTS,prepare_catalog,parse,get,getall,num,read,resolve


def run():
    prepare_catalog()
    from construction_safety import effective_award
    scenario=parse(read(SOURCE/'scenarios/1933.eug'))
    country=get(parse(read(SOURCE/'scenarios/1933/japan.inc')),'country')
    owned={v for _,v in get(country,'ownedprovinces')}
    national={v for _,v in get(country,'nationalprovinces')}
    mapping={'ic':'IC','energy':'Energy','metal':'Metal','rare_materials':'Rare Materials','oil':'Oil'}
    source_rows={r['Id']:r for r in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';') if r.get('Id','').isdigit()}
    provinces={p:{k:float(source_rows[p].get(col) or 0) for k,col in mapping.items()} for p in owned}
    ports={p:0. for p in owned}
    for include in getall(scenario,'include'):
        for pv in getall(parse(read(SOURCE/include.replace('\\','/'))),'province'):
            pid=get(pv,'id')
            if pid not in provinces:continue
            for k in mapping:
                value=get(pv,k)
                if isinstance(value,str):provinces[pid][k]+=float(value)
            naval=get(pv,'naval_base')
            if naval:ports[pid]=num(naval,'size')
    gross={k:sum(pv[k] for pv in provinces.values()) for k in mapping}
    # Country efficiency modifiers, ministers, research and trade are omitted.
    # The explicit 0.8 non-core and 0.9 global resource settings come from misc.
    indicative={k:sum(pv[k]*(1 if p in national else .8) for p,pv in provinces.items())*.9 for k in mapping if k!='ic'}
    costs=[];maximum_ic=0
    projects=['first_industry','army_supply','merchant_prewar','naval_school','pilot_school','army_school','second_industry','home_docks','snlf','guards']
    for key in projects:
        e=next(e for e in EVENTS if e.key==key)
        paid={'money':0,'supplies':0}
        for command in e.actions[0].commands:
            n=parse(resolve(command));typ=get(n,'type')
            if typ in paid:paid[typ]-=num(n,'value')
        rewards=[]
        for alt in range(2):
            f=next((f for f in EVENTS if f.key==key+'_finish_'+str(alt)),None)
            if f:
                rewards.append(sum(num(n,'value') for n in (parse(resolve(c)) for c in effective_award(f)) if get(n,'type')=='construct' and get(n,'which')=='ic'))
        maximum_ic+=max(rewards or [0]);costs.append({'key':key,'year':e.year,**paid})
    total={k:sum(r[k] for r in costs) for k in ('money','supplies')}
    raw_ic_days=total['money']/.2+total['supplies']/4
    # Early story purchase/production maximums are per-choice upper bounds.
    story_costs=[]
    for e in EVENTS:
        if e.module!='early' or e.triggered or not e.desc:continue
        options=[]
        for action in e.actions:
            amount=defaultdict(float)
            for command in action.commands:
                n=parse(resolve(command));typ=get(n,'type')
                if typ in {'money','supplies','oilpool'}:amount[typ]+=num(n,'value')
            options.append({k:max(0,-amount[k]) for k in ('money','supplies','oilpool')})
        story_costs.append({'key':e.key,**{k:max((o[k] for o in options),default=0) for k in ('money','supplies','oilpool')}})
    story_max={k:sum(r[k] for r in story_costs) for k in ('money','supplies','oilpool')}
    activity_costs=[]
    for e in EVENTS:
        if e.module!='activities' or e.triggered:continue
        payment={'money':0,'supplies':0}
        for command in e.actions[0].commands:
            n=parse(resolve(command));typ=get(n,'type')
            if typ in payment:payment[typ]-=num(n,'value')
        activity_costs.append({'key':e.key,'year':e.year,**payment})
    activity_total={k:sum(r[k] for r in activity_costs) for k in ('money','supplies')}
    scenarios=[]
    for ic in (60,80,100):
        demand={'energy':ic*2,'metal':ic,'rare_materials':ic*.5}
        scenarios.append({'effective_ic_assumption':ic,'demand':demand,'indicative_import_floor':{k:round(max(0,need-indicative[k]),2) for k,need in demand.items()}})
    lines=['# Japan economy and early-content balance review','',
        '**Assessment:** Japan is import-dependent, especially for metal and oil. The source does not support a claim of India-style calibrated balance. New content is priced and bounded; actual Hard balance still needs playtesting.','',
        '## Starting position','',
        '| Quantity | Value | Meaning |','| --- | --- | --- |',
        f"| Gross provincial IC | {gross['ic']:g} | Map IC plus 1933 scenario deltas, before non-core/peace/technology/ministry effects |",
        f"| Gross energy / metal / rares / oil | {gross['energy']:g} / {gross['metal']:g} / {gross['rare_materials']:g} / {gross['oil']:g} | Owned-province map output; not effective daily income |",
        '| Country-file starting stocks | 1,000 energy; 1,000 metal; 500 rares; 500 oil; 500 supplies; 100 money; 200 manpower | Provincial depots and subsequent native events are separate |',
        '| Hard difficulty | Human industry/resources: 0%; AI industry/resources: +10% | AI also receives other difficulty bonuses; no artificial human resource penalty is added |','',
        'Using the source non-core factor (0.8) and global resource efficiency (0.9) gives the following indicative domestic output before country-specific technology/ministry changes: '+', '.join(f'{k} {v:.2f}' for k,v in indicative.items())+'. This is a sensitivity input, not a simulated economy.','',
        '| Assumed effective IC | Energy demand | Metal demand | Rare demand | Indicative metal import floor | Rare import floor |','| --- | --- | --- | --- | --- | --- |']
    for row in scenarios:
        d=row['demand'];i=row['indicative_import_floor']
        lines.append(f"| {row['effective_ic_assumption']} | {d['energy']} | {d['metal']} | {d['rare_materials']:g} | {i['metal']:g} | {i['rare_materials']:g} |")
    lines += ['',
        'Industry uses 2 energy, 1 metal and 0.5 rares per effective IC. Oil demand instead depends on the force and its activity. Navy, air, motorised units, trade efficiency, puppet transfers, convoy capacity and stockpile targets must be read from an actual campaign to predict exhaustion dates. No fixed oil-runout date is claimed here.','',
        '## Cost of the existing preparation programmes','',
        '| Programme | First year | Money | Supplies |','| --- | --- | --- | --- |']
    for row in costs:lines.append(f"| {row['key']} | {row['year']} | {row['money']:g} | {row['supplies']:g} |")
    lines += ['',f"All ten cost **{total['money']:g} money and {total['supplies']:g} supplies** in setup payments. At the unmodified source ratios, this is {raw_ic_days:g} IC-days of money/supply production, about {raw_ic_days/2520:.2f} IC continuously for seven 360-day years. Existing research costs, consumer-goods needs, trade payments, military maintenance and all unit-construction costs are additional. It is not a suggested opening queue.",'',
        f"Choosing every prewar factory alternative can add **{maximum_ic:g} raw IC**, requiring approximately another {maximum_ic*2:g} energy, {maximum_ic:g} metal and {maximum_ic*.5:g} rares daily if it translates into that much additional effective IC. The actual increase is modified in the engine. A factory-heavy opening must fund imports instead of assuming those factories feed themselves.",'',
        '## What the new story content changes','',
        '- No new early story grants IC or free divisions. This avoids compounding the already substantial factory choices.',
        '- The 1933 mixed purchase provides 8 metal and 4 oil daily for 2 supplies and 0.3 money daily over 720 days. The oil-first alternative buys 8 oil for 1 supply and 0.4 money daily.',
        '- The oil-law contract buys 6 oil daily for 1.5 supplies and 0.3 money daily over 1,080 days. These are alternatives to conservation work, not an automatic free fuel stream.',
        '- A separate 1936 commercial review can buy another finite mixed contract. A 1939 northern deal can buy 4 metal and 4 oil daily for 1 supply and 0.2 money daily for a year. None automatically renews.',
        '- American contracts are unavailable at war with America or after the stock embargo. The inherited embargo receiver explicitly ends USA/JAP trades in the Japan expansion. Paid American contracts cannot be cancelled by ordinary AI trade decisions; expiry, embargo and war still end them. Other new commercial contracts remain cancellable.',
        '- Domestic processing can add 2 metal while consuming 4 energy. This is a small industrial supplement rather than a solution to the whole metal deficit.',
        '- Military allocation gives one service a temporary cost advantage and the other an equal premium, with exact expiry reversal. Yard disruptions also expire. The story choices carry no hidden alliance locks.',
        f"- Per-event maximum upfront spending across all {len(story_costs)} new stories is bounded by {story_max['money']:g} money, {story_max['supplies']:g} supplies and {story_max['oilpool']:g} oil. These maxima are separate upper bounds, include incompatible alternatives, and exclude ongoing trade payments. You are not expected to buy every option.",'',
        '## Concrete inherited/setup issues corrected','',
        f"Tokyo (1552) and Hiroshima (1554) both begin at naval-base level {ports['1552']:g}/{ports['1554']:g}. The old new-mod dock programme tried to expand those capped bases. Alpha 2 instead develops Kobe (1555) and Yokohama (1550), whose source starting levels are {ports['1555']:g}/{ports['1550']:g}, or concentrates at Kobe.",
        'The new consolidation receiver now explicitly uses inherit value=1, the documented option that requests transfer of units and production queues. The former default omitted that instruction. This improves the source contract; engine inheritance still needs a playtest.','',
        '## Recommended opening expectations','',
        'Use the mixed import licence if factories/army supply are your priority; use oil-first or the oil-law contract if your fleet/training draw is the limiting factor. Keep a cash and supply reserve before funding another major programme. For a China-first campaign, fund supply/transport and infantry capabilities before every naval preparation. For a carrier-heavy opening, accept slower land preparation and budget for oil/merchant protection. Ordinary trade remains essential.','',
        'The appropriate claim is a more deliberately budgeted and historically grounded candidate. The source arithmetic and model tests do not equal twenty human playthroughs, and do not yet establish that Japan can comfortably sustain every ambition at once.']
    lines += ['','## Specialist and operational activities','',
        f"The {len(activity_costs)} additional optional activities cost {activity_total['money']:g} money and {activity_total['supplies']:g} supplies in total setup payments if every one is funded. No activity grants IC or free completed combat units. Finite new resource trades have continuing payments and ordinary delivery/cancellation risk.",
        'Airborne, specialist, mobile and interceptor orders still need normal IC and manpower. Pure order alternatives receive the common eight-day improvement, included in the updated construction bound. Research blueprints do not unlock a unit by themselves. Cold-weather, attrition and marine training bonuses are one-time class-specific benefits.',
        'Buying every activity is optional. Existing priorities should come first if cash, supply reserves or resources are short.']
    sample_path=HERE/'BASELINE_ECONOMY_SAMPLES.json'
    samples=json.loads(sample_path.read_text()) if sample_path.exists() else []
    if samples:
        lines += ['','## Evidence from the older campaigns','',
            'These are separate older Blood and Iron snapshots, both marked difficulty 2 (Normal). They are not a continuous campaign time series, and do not validate the new build on Hard.','',
            '| Save date | Oil | Metal | Rares | Convoy reserve / assigned |','| --- | --- | --- | --- | --- |']
        for s in samples:
            r=s['resources'];c=s['convoys']
            lines.append(f"| {s['date'].get('year')}-{s['date'].get('month')} | {r['oil']:,.0f} | {r['metal']:,.0f} | {r['rare_materials']:,.0f} | {c['reserve']:g} / {c['assigned']:g} |")
        lines += ['',
            'The 1938 snapshot demonstrates that the inherited economy can accumulate substantial prewar stocks under at least one played strategy. The 1943 snapshot demonstrates extreme oil pressure despite substantial metal/rare stocks. Its empty convoy reserve is not an empty merchant marine: 1,081 transports remain assigned. These facts justify targeting fuel availability, convoy allocation and recovery, rather than granting every raw material indiscriminately. They do not by themselves identify the exact cause of that campaign\'s fuel collapse.','',
            'The native South Manchuria Railway event 9300221 already adds 20% TC and charges the human 50 money. New early story logistics can add at most another 7 TC percentage points across separate choices; the existing native bonus remains part of the combined balance.']
    report={'gross_province_totals':gross,'indicative_domestic_output':indicative,'ic_sensitivity':scenarios,'prewar_programmes':costs,'programme_setup_total':total,'max_prewar_factory_ic':maximum_ic,'early_story_upfront_independent_upper_bounds':story_max,'story_count':len(story_costs),'activity_setup_costs':activity_costs,'activity_setup_total':activity_total,'older_campaign_samples':samples,'engine_tested':False}
    (HERE/'RESOURCE_BALANCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'RESOURCE_BALANCE.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__=='__main__':run()
