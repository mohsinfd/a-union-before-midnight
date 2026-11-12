"""Evidence-led audit of the user's saved event history and actual rewards."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
from build import HERE,TARGET,GAME,read,parse,get,getall,province_names
from repair_completion_save import block_end,industry_totals


def snapshot():
    path=TARGET/'scenarios/save games/autosave.eug';raw=path.read_bytes();s=raw.decode('latin1')
    h=s.index('header = {');date=dict(get(get(parse(s[h:block_end(s,h)]),'header'),'startdate'))
    m=next(m for m in re.finditer(r'(?m)^country = \{',s) if re.search(r'(?m)^\s*tag = JAP\s*$',s[m.start():m.start()+500]))
    c=get(parse(s[m.start():block_end(s,m.start())]),'country')
    m=re.search(r'(?m)^globaldata = \{',s);g=get(parse(s[m.start():block_end(s,m.start())]),'globaldata')
    m=re.search(r'(?m)^eyr = \{',s);log=getall(get(get(parse(s[m.start():block_end(s,m.start())]),'eyr'),'history'),'name')
    return path,raw,s,date,c,g,log


def run():
    path,raw,s,date,c,g,log=snapshot()
    backup=Path((HERE/'PROGRAMME_FIX_BACKUP.txt').read_text())
    spec=json.loads((backup/'sources/events.json').read_text());bykey={e['key']:e for e in spec}
    byid={e['id']:e for e in spec}
    flags=dict(get(g,'flags',[]));upgrades=dict(get(c,'upgrade',[]))
    fired=set(int(x) for x in re.search(r'(?m)^history = \{([^}]*)\}',s)[1].split())
    # Persistent events need not stay in the one-shot history list. Their
    # saved-date entries are essential evidence of execution.
    sd=re.search(r'(?m)^save_date = \{',s)
    dates=get(parse(s[sd.start():block_end(s,sd.start())]),'save_date') if sd else []
    fired.update(int(k) for k,v in dates if str(k).isdigit())
    player=[l for l in log if 'We went with ' in l or ' happened to us.' in l and not any(x in l for x in (' went with ',' has succeeded ',' has failed '))]
    selections={}
    for key,e in bykey.items():
        if e['country']!='JAP':continue
        for l in player:
            if e['title'] and (' in '+e['title']+'.' in l or e['title']+' happened to us.' in l):
                selections.setdefault(key,[]).append(l)
    completed=[]
    for key,e in bykey.items():
        if e['country']!='JAP' or key.endswith(('_return','_reconsider')) or not any(k.startswith(key+'_finish_') for k in bykey):continue
        if flags.get('JX_'+key+'_DONE')!='1':continue
        parent_choices=[i for i,a in enumerate(e['actions'][:2]) if any('We went with '+a['name']+' in '+e['title']+'.' in l for l in selections.get(key,[]))]
        selected=[(i,bykey[key+'_finish_'+str(i)]) for i in parent_choices if key+'_finish_'+str(i) in bykey]
        completed.append({'key':key,'title':e['title'],'selected_completions':[i for i,f in selected],
                          'completion_evidence':[f['id'] for i,f in selected],
                          'old_reward_commands':[f['actions'][0]['commands'] for i,f in selected],
                          'history':selections.get(key,[]),'status':'Completion recorded; reward-specific evidence below'})
        fired.add(e['id']);fired.update(f['id'] for i,f in selected)
    title_counts=Counter(e['title'] for e in spec if e['country']=='JAP')
    fired.update(bykey[key]['id'] for key in selections if '_finish_' not in key and title_counts[bykey[key]['title']]==1)
    jx=[byid[x] for x in sorted(fired&byid.keys())]
    # Include the inherited political/military events, rather than treating the
    # new catalogue as the whole campaign. A saved current state cannot prove a
    # cabinet effect that a later cabinet deliberately superseded.
    from localisation_support import loaded_names
    texts=loaded_names(TARGET,GAME,read);native=[]
    paths=getall(parse(read(TARGET/'db/events.txt')),'event')
    for rel in dict.fromkeys(paths):
        if not isinstance(rel,str) or 'japan_rising' in rel:continue
        p=TARGET/rel.replace('\\','/')
        if not p.exists():continue
        for node in getall(parse(read(p)),'event'):
            eid=get(node,'id')
            if not str(eid).isdigit() or int(eid) not in fired:continue
            title=texts.get(get(node,'name'),get(node,'name','')).strip()
            own=get(node,'country')=='JAP'
            lines=[l for l in player if ' in '+title+'.' in l or title+' happened to us.' in l] if title and title!='AI_EVENT' else []
            if not own and (get(node,'country') or not lines):continue
            actions=getall(node,'action')+getall(node,'action_a')+getall(node,'action_b')+getall(node,'action_c')+getall(node,'action_d')
            selected=[]
            for action in actions:
                label=texts.get(get(action,'name'),get(action,'name','')).strip()
                if len(actions)==1 or any('We went with '+label+' in '+title+'.' in l for l in lines):selected.append(action)
            native.append({'id':int(eid),'file':rel,'title':title,'recipient':get(node,'country','generic - matching player log'),
                           'history':lines,'selected_actions':selected,
                           'scope':'Execution or matching player history recorded; selected effects listed. Overwritten cabinet/stat changes are not individually certified from the final snapshot.'})
    units=[]
    for kind in ('landunit','navalunit','airunit'):
        for corps in getall(c,kind):
            for d in getall(corps,'division'):
                packed=[v for _,v in get(d,'all',[])];mod=[v for _,v in get(d,'mod',[])]
                strength=float(get(d,'strength',packed[0] if packed else 100))
                if strength<1 or mod and mod[0]=='7':units.append({'corps':get(corps,'name'),'name':get(d,'name'),'strength':strength,'type_index':mod[0] if mod else None})
    imports=[]
    for tr in getall(g,'treaty'):
        if get(tr,'type')=='trade' and set(getall(tr,'country'))=={'USA','JAP'}:
            tags=getall(tr,'country');factor=1 if tags[0]=='JAP' else -1
            imports.append({'id':get(tr,'id'),'oil_to_japan':factor*float(get(tr,'oil',0)),
                            'metal_to_japan':factor*float(get(tr,'metal',0)),
                            'supplies_to_japan':factor*float(get(tr,'supplies',0)),
                            'money_to_japan':factor*float(get(tr,'money',0)),
                            'expiry':dict(get(tr,'expirydate')),'cancel':get(tr,'cancel','yes')})
    queues=[dict(q) for q in getall(c,'division_development') if get(q,'type') in ('marine','d_10','d_11')]
    base={int(r['Id']):float(r['IC'] or 0) for r in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';') if r['Id'].isdigit()}
    report={'date':date,'source':str(path),'source_sha256':hashlib.sha256(raw).hexdigest(),
            'new_event_records_in_history':len(jx),'completed_paid_programmes':completed,
            'jx_fired_events':[{'id':e['id'],'key':e['key'],'country':e['country'],'title':e['title'],'module':e['module']} for e in jx],
            'player_event_history':player,'japanese_event_selections':selections,
            'inherited_fired_event_review':native,
            'active_jx_flags':{k:v for k,v in flags.items() if k.startswith('JX_') and v!='0'},
            'upgrades':upgrades,'base_IC':industry_totals(s,base),'US_imports':imports,
            'relevant_production_queues':queues,'marine_and_understrength_units':units,
            'convoy_reserve':get(c,'transports'),'escort_reserve':get(c,'escorts'),
            'blueprints':[v for _,v in get(c,'blueprints',[])],
            'scope':'Actual saved evidence. Completed flags do not prove each reward; historical stockpiles and money cannot be attributed exactly without an earlier snapshot.'}
    (HERE/'PLAYTEST_1937_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Japan playtest audit: 1 June 1937','',
           'Reads the latest autosave and its full saved history, not just the current session log. No engine was launched. The original save is unchanged.','',
           '## Findings','',
           '- SNLF created a serial line of three stock Marine divisions. The first has 357 days remaining and no stored production progress. This is an unfunded construction order, not three deployed zero-strength units. The programme gave blueprint 1600, which is present, but no Marine time/cost modifier. Its blueprint excluded it from the former eight-day bonus rule.',
           '- Naval Base Force was unlocked correctly. The save contains three earlier, named single-item Base Force orders with AA, but no separate two-item order matching the later funded programme. Its eight-day build-time modifier is present. Delivery of its promised two-unit order is not established; the order appears absent.',
           '- Five existing Marine formations are at 10–17% strength and one is at 100%. The five small cadres start at those strengths in Blood and Iron. The current reinforcement slider is zero. These are separate from the new three-item production line; no deployed formation is at 0%. The packed save format must be decoded to see them.',
           '- The 1934 six-oil contract and 1936 mixed eight-metal/four-oil contract are present and non-cancellable. The earlier eight-oil licence has expired, as expected. The six-oil purchase expires on 2 July 1937, so the daily total can fall soon. These are import flows subject to delivery and payment, not domestic oil output.',
           '- The sidebar comparison found that the base plate already matches vanilla cream. The new 224 x 48 illustrations overwrote the first fourteen transparent rows, putting black titles on dark artwork. The fix restores the vanilla transparency/header strip while keeping the illustration below it.',
           '- The user selected time discounts and manual ordering. The repaired programmes award explicit construction-day savings without creating queue entries. Existing queues are preserved so the player can cancel or move them through the engine, retaining its normal manpower refund rules.','',
           '## Recorded paid completions','',
           '| Programme | Chosen completion | What the save establishes |','| --- | --- | --- |']
    for row in completed:
        key=row['key'];evidence='Completion flag and event history present; see exact commands in JSON.'
        if key=='snlf':evidence='Blueprint 1600 present; three-item Marine line present; no Marine build-time discount.'
        elif key=='base_force_orders':evidence='Base Force buildtime -8 recorded; matching two-item queue absent.'
        elif key in {'first_industry','army_supply'}:evidence='Completed; current IC inventory includes the saved repair and later native award. Exact aggregate is below.'
        elif key in {'naval_school','pilot_school','winter_school','landing_rehearsal'}:evidence='Completion recorded; blueprints/unit modifiers listed in JSON. Research can consume blueprints, so absence alone is not failure.'
        elif key in {'merchant_prewar','merchant_reserve','manchurian_contract'}:evidence='Completion recorded; pooled merchant shipping cannot be attributed exactly after later production/allocation. Earlier +120/+25 delivery was independently confirmed.'
        lines.append('| '+row['title']+' | '+','.join(str(i+1) for i in row['selected_completions'])+' | '+evidence+' |')
    lines+=['','## Current evidence','',
            'IC inventory (map defaults included): `'+json.dumps(report['base_IC'])+'`. This is not the top-bar usable IC calculation.',
            '', 'US import contracts:','', '```json',json.dumps(imports,indent=2),'```','',
            'Marine formations and any formations below 1% strength:','', '```json',json.dumps(units,indent=2),'```','',
            '## All recorded new events','', '| ID | Country | Event |','| --- | --- | --- |']
    for e in jx:lines.append('| '+str(e['id'])+' | '+e['country']+' | '+e['title']+' |')
    lines+=['','## Inherited Japanese and matching generic events','',
            'Each row has a fired-ID or matching player-log record. Selected command lists are retained in JSON. A later cabinet, technology or expiry can supersede an earlier change; these rows do not claim every historical modifier can be reconstructed from one final save.','',
            '| ID | Event | Selection evidence |','| --- | --- | --- |']
    for e in native:lines.append('| '+str(e['id'])+' | '+e['title']+' | '+('Player log / selected commands' if e['selected_actions'] else 'Fired record; exact action not isolated')+' |')
    lines+=['','## Full player event log','']+['- '+l for l in player]
    (HERE/'PLAYTEST_1937_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'date':date,'new_fired_event_records':len(jx),'inherited_event_records_reviewed':len(native),'completed_paid_programmes':len(completed),'relevant_queues':len(queues),'zero_strength_units':sum(u['strength']<1 for u in units),'marine_units':[u for u in units if u['type_index']=='7'],'IC':report['base_IC'],'US_imports':imports}))


if __name__=='__main__':run()
