"""Read-only reconciliation of the April 1936 campaign's paid programmes.

Writes evidence/report files beside this script; never edits a save, installed
event, manifest or release, and never starts the game.
"""
import csv,hashlib,json,re
from pathlib import Path
from audit_1937_playtest import snapshot
from build import HERE,TARGET,GAME,parse,get,getall,read
from repair_completion_save import block_end

MONTHS='january february march april may june july august september october november december'.split()


def run():
    path,raw,text,date,c,g,log=snapshot()
    assert path.read_bytes()==raw,'Save changed while being read; retry the audit'
    flags=dict(get(g,'flags',[]));events=json.loads((HERE/'events.json').read_text(encoding='utf-8'))
    by={e['key']:e for e in events};byid={str(e['id']):e for e in events}
    queue=[dict((k,v) for k,v in e) for e in getall(get(g,'queued_events',[]),'event')]
    upgrade=get(c,'upgrade',[])
    allocated=sum(int(get(e,'transports',0)) for e in getall(c,'convoy'))
    assigned_escorts=sum(int(get(e,'escorts',0)) for e in getall(c,'convoy'))
    shipping=dict(free_transports=int(get(c,'transports')),assigned_transports=allocated,
                  total_transports=int(get(c,'transports'))+allocated,
                  free_escorts=int(get(c,'escorts')),assigned_escorts=assigned_escorts,
                  total_escorts=int(get(c,'escorts'))+assigned_escorts,
                  scenario_transports=640,scenario_escorts=100,
                  completed_transports=160,completed_escorts=65)
    assert shipping['total_transports']==800 and shipping['total_escorts']==165
    facts={
      'first_industry':('delivered','Tokyo/Hiroshima factory additions are present; the February 1934 checkpoint already has 13 and 10 IC respectively.'),
      'army_supply':('consistent','Done; saved supply modifier 1.38 and TC modifier 1.89. These totals include research and other effects, so the individual 15-point contributions are not isolated by the completion flag alone.'),
      'army_production':('delivered','Saved unit cost modifiers: Infantry -1 IC, Mountain Infantry -1.2 IC, Marines -1.6 IC; Marine build time -63 days. This choice awards production savings, not completed divisions.'),
      'prewar_rural_works':('previously_repaired','The original completion failed. The February repaired save closes it and restores 3 IC; the current save retains DONE=1.'),
      'strategic_storage':('delivered','Oil/supply storage modifier is 2.8 in peace and 3 in war, consistent with the selected +200 percentage-point addition.'),
      'merchant_prewar':('delivered','Starting 640 transports + purchased 160 = 800 total now. Starting 100 escorts + purchased 40 + later Manchukuo 25 = 165 now.'),
      'air_production':('delivered','Saved bomber-priority modifiers: Tactical bomber -5 IC/-46 days; Naval bomber -4 IC/-48 days; Transport aircraft -5 IC/-48 days; fighters -1.5 IC/-18 days.'),
      'tomozuru1934':('delivered','Stability study retained; destroyer sea-defence vulnerability is -1 after both structural events. The temporary production penalty has expired.'),
      'prewar_deck_commission':('failed_overdue','Selected aircrew school remains PENDING=1, DONE=0, CANCELLED=0. No completion or callback is queued. CAG/light-CAG +8 morale and +5 organisation were not delivered.'),
      'oil1934':('contract_missing','The purchased additional 24 oil/day agreement should run until August 1937, but is absent. Its script permits cancellation (value=0). The save cannot prove whether it never appeared or was later cancelled/merged.'),
      'manchurian_contract':('delivered','Selected 25 convoy escorts; the escort pool increased from 140 at the February 1934 checkpoint to 165 now.'),
      'fx1933':('contract_missing','The selected 24 oil/day plus 12 metal/day agreement should run until November 1936, but is absent. Its script permits cancellation (value=0); who/what ended it is not established.'),
      'naval_production':('delivered','Saved fleet/light carrier cost and time modifiers are -0.38 IC/-153 days and -0.23 IC/-147 days. CAG savings are also present; fractional day values are stored as whole days.'),
      'prewar_navigation_trials':('failed_overdue','Selected maritime trials remain PENDING=1, DONE=0, CANCELLED=0. No completion or callback is queued; Naval Bomber range +300 km and surface detection +2 are absent.'),
      'home_fuel':('delivered','Kushiro base resources are now 217 energy/40 metal/12 rares, matching +160/+40/+10. Tokyo oil is 20; Yokohama energy is 27, matching the -20 input.'),
      'typhoon1935':('delivered','Second structural study completed; destroyer/light-cruiser vulnerability is reduced. Temporary +8-day destroyer construction penalty ended on 26 March 1936.'),
      'merchant_reserve':('not_due','The +60-transports delivery is still queued: event 28600667, 105 game hours from the 1 April save, due 5 April 1936 at 09:00.'),
    }
    rows=[]
    for key,(status,evidence) in facts.items():
        e=by[key];selected=[]
        for i,a in enumerate(e['actions']):
            token='We went with '+a['name']+' in '+e['title']+'.'
            selected.extend((line,i) for line in log if token in line)
        assert len(selected)==1,(key,selected)
        line,index=selected[0];a=e['actions'][index]
        costs={}
        for command in a['commands']:
            node=parse(command);value=get(node,'value');kind=get(node,'type')
            if kind in ('money','supplies','oilpool','metalpool','energypool','manpowerpool') and value and float(value)<0:
                costs[kind]=costs.get(kind,0)-float(value)
        rows.append(dict(key=key,title=e['title'],selection=a['name'],history=line,upfront_cost=costs,
                         status=status,evidence=evidence,selected_commands=a['commands'],
                         programme_flags={k:v for k,v in flags.items() if k.startswith('JX_'+key+'_')}))
    stalled=[]
    for key,due,bonus in (
        ('prewar_deck_commission','20 March 1935','Fleet and light CAG: +8 morale, +5 maximum organisation'),
        ('prewar_navigation_trials','23 September 1935','Naval Bomber: +300 km range, +2 surface detection')):
        parent=by[key];target=by[key+'_finish_0'];dispatch=parse(parent['actions'][0]['commands'][-1])
        expected=str(get(dispatch,'which'));wrapper=byid[expected]
        assert flags.get('JX_'+key+'_PENDING')=='1' and flags.get('JX_'+key+'_DONE')=='0'
        assert not any(str(q['id']) in (str(target['id']),expected) and q.get('tag')=='JAP' for q in queue)
        stalled.append(dict(programme=key,due=due,owed=bonus,receiver=target['id'],wrapper=wrapper['id'],
                            command=parent['actions'][0]['commands'][-1],completion_present=False))
    suspect=[]
    for e in events:
        for index,a in enumerate(e['actions']):
            for command in a['commands']:
                match=re.search(r'\bwhich\s*=\s*"(286\d+)"',command)
                kind=re.search(r'\btype\s*=\s*(event|trigger)\b',command)
                if match and kind:
                    suspect.append(dict(event=e['key'],module=e['module'],choice=index,type=kind[1],
                                        target=byid[match[1]]['key'],command=command))
    trades=[]
    for treaty in getall(g,'treaty'):
        if get(treaty,'type')=='trade' and set(getall(treaty,'country'))=={'USA','JAP'}:
            trades.append(dict(countries=getall(treaty,'country'),oil=get(treaty,'oil','0'),
                               metal=get(treaty,'metal','0'),supplies=get(treaty,'supplies','0'),
                               money=get(treaty,'money','0'),cancel=get(treaty,'cancel'),
                               expiry=dict(get(treaty,'expirydate',[]))))
    base={r['Id']:r for r in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';') if r['Id'].isdigit()}
    provinces={}
    for pid in (1544,1550,1552,1554,1557):
        m=re.search(r'(?m)^province = \{\s*\n\s*id = '+str(pid)+r'\b',text)
        node=get(parse(text[m.start():block_end(text,m.start())]),'province')
        provinces[pid]=dict(ic=get(node,'ic',base[str(pid)]['IC']),
                            resources={kind:get(node,kind) for kind in ('energy','metal','rare_materials','oil')})
    attachment_entries=getall(c,'navaldivision')
    torpedoes=[d for d in attachment_entries if any(v=='41' for _,v in get(d,'brig',[])[:1])]
    assert len(torpedoes)==2
    engine_log=GAME/'savedebug.txt';engine_raw=engine_log.read_bytes()
    commands_quoted=len(suspect);timing_quotes=sum(r['target'].startswith('time_delivery_') for r in suspect)
    report=dict(date=date,source=str(path),source_sha256=hashlib.sha256(raw).hexdigest(),
        installed_version=json.loads((TARGET/'JAPAN_RISING_BUILD.json').read_text())['version'],
        source_unchanged=path.read_bytes()==raw,save_edits=False,installation_edits=False,game_run=False,
        shipping=shipping,purchases=rows,stalled_purchases=stalled,
        paid_oil_contracts_missing=2,current_us_trades=trades,
        upgrade_evidence={kind:get(upgrade,kind,[]) for kind in ('marine','infantry','bergsjaeger','carrier','light_carrier','cag','light_cag','interceptor','tactical_bomber','naval_bomber','transport_plane')},
        provinces=provinces,free_type93_attachments_present=len(torpedoes),queued_events=queue,
        dispatch_risk=dict(quoted_references=commands_quoted,affected_events=len({r['event'] for r in suspect}),
            timing_handoffs=timing_quotes,findings=suspect,
            confidence='Confirmed missing deliveries; quoted-numeric callback formatting is the leading explanation, not a running-engine proof.',
            audit_gap='The Python parser/simulator normalises quoted IDs into strings, hiding this native-format difference from AST parity and simulation checks.'),
        engine_log_sha256=hashlib.sha256(engine_raw).hexdigest())
    (HERE/'PURCHASE_AUDIT_1936_APRIL.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# Purchase audit — 1 April 1936','',
        'Read-only audit of the latest autosave. No game launch, save repair or installation change.','',
        'The convoy purchases reconcile exactly. Two paid training programmes are overdue and undelivered; two paid oil contracts are absent before their intended expiry. R15.1 cannot be described as fully repaired.','',
        '| Purchase | Finding | Evidence |','|---|---|---|']
    for row in rows:lines.append('| '+row['title']+' | '+row['status']+' | '+row['evidence']+' |')
    lines+=['','## Shipping ledger','',
        '- Start: 640 convoy transports and 100 escorts.',
        '- Completed merchant expansion: +160 transports and +40 escorts.',
        '- Completed Manchukuo choice: +25 escorts.',
        '- Current: 716 free +84 assigned =800 transports; 165 escorts. No failure demonstrated for these rewards.',
        '- Merchant reserve: +60 transports is not due yet; 105 game hours remain, to 5 April at 09:00.','',
        '## Confirmed missing training rewards','',
        '- Aircrew school, funded 20 July 1934: due 20 March 1935. Owed +8 morale/+5 organisation to CAG and light CAG. Paid 60 money, 450 supplies and 250 oil; pending, without refund or queued completion.',
        '- Maritime trials, funded 23 March 1935: due 23 September 1935. Owed Naval Bomber range +300 km and surface detection +2. Paid 75 money, 600 supplies, 500 metal and 1,000 energy; pending, without refund or queued completion.','',
        '## Wider dispatch risk','',
        f'{commands_quoted} event/trigger commands across {len({r["event"] for r in suspect})} events contain quoted numeric targets; {timing_quotes} target the new timing handoffs. Both stalled purchases use that formatting. Their completions are absent from the saved queue, completion flags and player log. The ordinary shipping rewards use unquoted targets and reconcile.',
        '', 'This is the leading source-level explanation. It has not been proved by launching the engine. The existing Python parser strips the quotation distinction, so its simulated deliveries and installed AST comparisons did not validate that behaviour.',
        '', 'Risk extends to regional purchases, American campaign support, recovery/strategic preparations, enemy response deliveries and postwar grants/refunds. Those future outcomes have not occurred in this campaign; they are exposed paths, not claimed observed failures.','',
        '## Oil contracts','',
        'The August 1934 +24-oil/day and November 1934 +24-oil/+12-metal/day purchases should still be active (until August 1937 and November 1936). Neither promised treaty is in the save. The scripts create cancellable trades and close the offers as DONE. The only US oil agreement present is the inherited 50-oil trade. Current evidence does not establish whether the paid contracts never appeared, were cancelled, or were replaced by trade automation.','',
        '## Other verified effects','',
        'Army, bomber-priority aircraft and carrier production savings are present. The home-resource project changed the named provincial outputs exactly. The storage expansion is present. The two free Type 93 torpedo attachments are in the deployment pool; they are not missing units.','',
        '## Repair scope recommended','',
        'Correct event-target integer rendering centrally; audit compiled text rather than only parsed equivalence. Recover only the two confirmed unpaid training outcomes in a separate current-save copy, without charging again. Reconcile the missing oil contracts separately before restoring any trade or backpay. Preserve shipping already delivered and the +60 reward still awaiting its due date. Do not add those shipping pools again.','',
        'The original autosave and installation were left untouched.']
    (HERE/'PURCHASE_AUDIT_1936_APRIL.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(date=date,paid_selections=len(rows),shipping=shipping,
        statuses={status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})},
        confirmed_stalled=stalled,quoted_callback_references=commands_quoted,
        source_unchanged=report['source_unchanged'],game_run=False),indent=2))


if __name__=='__main__':run()
