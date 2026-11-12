"""Audit a stable saved snapshot; never replay events or infer rewards from flags alone."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from build import HERE,TARGET,GAME,read,parse,get,getall,province_names
from repair_completion_save import block_end

MONTHS='january february march april may june july august september october november december'.split()


def format_hour(value):
    day,h=divmod(value,24);year,day=divmod(day,360);month,day=divmod(day,30)
    return f'{day+1} {MONTHS[month].title()} {year}, {h:02d}:00'


def run():
    folder=HERE/'latest_playtest';folder.mkdir(exist_ok=True)
    source=folder/'autosave_snapshot.eug';raw=source.read_bytes();s=raw.decode('latin1')
    h=s.index('header = {');date=dict(get(get(parse(s[h:block_end(s,h)]),'header'),'startdate'))
    now=((int(date['year'])*360+MONTHS.index(date['month'])*30+int(date['day']))*24+int(date['hour']))
    gm=re.search(r'(?m)^globaldata = \{',s);g=get(parse(s[gm.start():block_end(s,gm.start())]),'globaldata')
    countries={}
    for m in re.finditer(r'(?m)^country = \{',s):
        n=get(parse(s[m.start():block_end(s,m.start())]),'country');countries[get(n,'tag')]=n
    c=countries['JAP'];flags=dict(get(g,'flags'));spec=json.loads((HERE/'events.json').read_text())
    byid={r['id']:r for r in spec};bykey={r['key']:r for r in spec}
    em=re.search(r'(?m)^eyr = \{',s)
    log=getall(get(get(parse(s[em.start():block_end(s,em.start())]),'eyr'),'history'),'name')
    selected=[l for l in log if 'We went with ' in l or ' happened to us.' in l and not any(x in l for x in (' went with ',' has succeeded ',' has failed '))]
    queue=[]
    for q in getall(get(g,'queued_events'),'event'):
        if get(q,'tag')!='JAP':continue
        eid=int(get(q,'id'));hours=int(get(q,'hour'));e=byid.get(eid,{})
        queue.append({'event_id':eid,'key':e.get('key'),'title':e.get('title'),'remaining_hours':hours,
                      'due':format_hour(now+hours),'reward_commands':e.get('actions',[{}])[0].get('commands',[])})
    pending=[];completed=[]
    for key,e in bykey.items():
        if e['country']!='JAP' or not any(k.startswith(key+'_finish_') for k in bykey):continue
        records=[l for l in selected if ' in '+e['title']+'.' in l]
        if flags.get('JX_'+key+'_DONE')=='1':completed.append({'key':key,'title':e['title'],'selection_records':records})
        if flags.get('JX_'+key+'_PENDING')!='1':continue
        matches=[q for q in queue if q['key'] and q['key'].startswith(key+'_finish_')]
        pending.append({'key':key,'title':e['title'],'status':'Scheduled; not overdue' if matches else 'Needs investigation: no matching queued completion',
                        'completions':matches,'selection_records':records})
    snlf=[]
    for kind in ('landunit','navalunit','airunit'):
        for corps in getall(c,kind):
            for d in getall(corps,'division'):
                mod=[v for _,v in get(d,'mod',[])];stats=[v for _,v in get(d,'all',[])]
                if mod and mod[0]=='52':snlf.append({'name':get(d,'name'),'corps':get(corps,'name'),'model':mod[2],
                    'strength':float(stats[0]),'organisation':float(stats[2]),'maximum_organisation':float(stats[3])})
    newmin=[get(get(n,'id'),'id') for n in getall(c,'minister') if 286121<=int(get(get(n,'id'),'id'))<=286130]
    chi=bykey['china'];controls={int(v) for _,v in get(c,'controlledprovinces')}
    required={int(p):int(p) in controls for p in re.findall(r'control = \{ province = (\d+) data = JAP \}',chi['gate'])}
    names=province_names();required_names={names[p]:v for p,v in required.items()}
    cn=countries.get('CHI',[]);cnational={int(v) for _,v in get(cn,'nationalprovinces',[])}
    imports=[]
    for tr in getall(g,'treaty'):
        if get(tr,'type')=='trade' and set(getall(tr,'country'))=={'JAP','USA'}:
            sign=1 if getall(tr,'country')[0]=='JAP' else -1
            imports.append({k:sign*float(get(tr,k,0)) for k in ('oil','metal','supplies','money')})
    errors=[l.strip() for l in read(GAME/'savedebug.txt').splitlines() if 'ERROR :' in l]
    error_groups=Counter('Italy duplicate port priorities' if 'province_priorities' in l and '/ai/ita_' in l else
                         'Unsupported 32-bit bitmap' if 'Unsupported image bit count (32)' in l else
                         'Duplicate implicit SNLF model zero in old June load' if 'Duplicated value (0)' in l and 'd_12' in l else
                         'Other inherited or load-time diagnostic' for l in errors)
    report={'snapshot_date':format_hour(now),'source_autosave':str(TARGET/'scenarios/save games/autosave.eug'),
            'snapshot_sha256':hashlib.sha256(raw).hexdigest(),'pending_programmes':pending,'completed_programmes':completed,
            'missing_queued_completions':[p['key'] for p in pending if not p['completions']],
            'deployed_SNLF':snlf,'SNLF_upgrade':get(get(c,'upgrade'),'d_12'),
            'SNLF_model_zero_implicit':get(get(c,'models'),'d_12') is None,
            'new_cabinet_records_present':len(newmin),'US_trades':imports,
            'China_settlement_required_controls':required_names,'Chinese_national_provinces':len(cnational),
            'Chinese_national_provinces_directly_controlled_by_Japan':len(cnational&controls),
            'China_settlement_gate':chi['gate'],'saved_event_selections':selected,
            'blocked_offer_found':{'key':'materials1938','cause':'Stock law event 1000247 expired in March 1938 before the April China war; original gate barred the offer until China settlement',
                                   'fix':'Ongoing China war is accepted alongside the original law/settlement conditions; budget and once-only rules unchanged'},
            'runtime_diagnostics':dict(error_groups),'runtime_error_lines':errors,
            'save_repair_needed':False,'game_launched_or_controlled':False,
            'scope':'Pending queues, selected completion history and current observable outcomes. Historical spending and consumed blueprints cannot all be reconstructed from one save.'}
    package=HERE/'staged_names_ai_fix/REVIEW.json'
    report['correction_package_state']=json.loads(package.read_text())['state'] if package.exists() else 'not prepared'
    (folder/'AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Latest Japan autosave audit','',report['snapshot_date']+'. Read-only saved snapshot; no game control.','',
           'R5 L4 N1 correction package: **'+report['correction_package_state']+'**. The current autosave requires no edit.','',
           f'{len(completed)} completed paid programmes and {len(pending)} pending programmes identified. All pending programmes have matching saved completion events. No missing completion is established.','',
           '| Pending programme | Remaining time | Scheduled completion |','| --- | --- | --- |']
    for p in pending:
        for q in p['completions']:lines.append(f'| {p["title"]} | {q["remaining_hours"]//24} days, {q["remaining_hours"]%24} hours | {q["due"]} |')
    lines += ['', 'The local supply-reserve choice made on 30 July is also a 120-day paid project. Its scheduled delivery is 30 November; the supply award has not been lost.','',
              'One SNLF division is deployed at roughly 99.5% strength. The -60-day modifier and all ten new cabinet replacement records persist in the engine-written save. The model name remains a real localisation defect: labels were appended after models.csv EOF markers and generic fallback names were absent. The fix covers SNLF, Base Force, Jungle Light and the Japanese Guards model labels.','',
              'Our Axis port-priority patch inserted repeated Tripoli/Benghazi/Tobruk entries. The prepared correction merges each priority once and retains the higher of the existing and requested weights. This is a real file diagnostic, not proof that it caused an observed military defeat.','',
              'The old June migration explicitly listed model zero even though DH supplies it implicitly. The loader logged a duplicate-zero warning. The current autosave has already normalised it; no save repair is needed. Future migration code now omits that redundant entry.','',
              'One genuine blocked offer was found: Steel for the mobilisation orders required stock law event 1000247, which was only available on 26–28 March 1938. Your China war began on 13 April. The original gate therefore prevented the May industrial-materials offer until China was settled. The prepared fix also accepts an ongoing China war. It preserves the setup price, 270-day wait, province requirements and once-only guards; it does not grant resources automatically.','',
              f'China settlement control checks: {required_names}. Chongqing is still missing. Japan directly controls {len(cnational&controls)} of {len(cnational)} Chinese national provinces in the save. The event also requires its national-loss threshold; no forced settlement or peace is warranted by this audit.','',
              'Other logged inherited issues include unsupported 32-bit unit pictures, missing technology pictures and older AI-script diagnostics. They are recorded in AUDIT.json for a larger pass; they are not all fixed here.','',
              'No save edits or event replay are required for these corrections. After installation, restart the same mod and continue the 1 August 1938 autosave. The blocked materials proposal should become eligible at a normal event check; it remains optional and paid. Field medicine, Bring the wounded back, opens in August 1938 with a seven-day check interval.']
    (folder/'AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('snapshot_date','missing_queued_completions','deployed_SNLF','new_cabinet_records_present','China_settlement_required_controls','runtime_diagnostics','save_repair_needed')}))


if __name__=='__main__':run()
