"""Restore only owed training and absent, unexpired paid US contracts.

Original autosave is backed up. The repaired autosave and named copy are
identical. Reward effects are delivered by native receipts after one game hour,
not by changing derived unit-stat arrays. Reapplying is idempotent.
"""
import copy,hashlib,json,re,shutil,subprocess
from pathlib import Path
import build as b
from repair_completion_save import block_end

MONTHS='january february march april may june july august september october november december'.split()
REWARDS=(('prewar_deck_commission',28601743,28603060,240),
         ('prewar_navigation_trials',28601746,28603062,180))
CONTRACTS=(('oil1934',24,0,1080,'Buy a further 24 oil daily','The oil law needs an actual reserve'),
           ('fx1933',24,12,720,'Buy 24 oil and 12 metal daily','Buy oil for a larger fleet'))


def section(text,label,tag=None):
    pattern=(r'\b' if label=='header' else r'(?m)^')+re.escape(label)+r' = \{'
    for m in re.finditer(pattern,text):
        if tag and not re.search(r'\btag = '+tag+r'\b',text[m.start():m.start()+500]):continue
        end=block_end(text,m.start());return m.start(),end,b.get(b.parse(text[m.start():end]),label)
    raise ValueError('Missing section '+label+' '+str(tag))


def stamp(node):
    return ((int(b.get(node,'year'))*360+MONTHS.index(b.get(node,'month'))*30+int(b.get(node,'day',0)))*24+int(b.get(node,'hour',0)))


def expiry(log,action,title,days):
    token='We went with '+action+' in '+title+'.'
    matches=[line for line in log if token in line];assert len(matches)==1,(title,matches)
    m=re.match(r'(\d+):\d+ (\w+) (\d+), (\d+) :',matches[0]);assert m
    hour,month,day,year=int(m[1]),m[2].lower(),int(m[3])-1,int(m[4])
    total=(year*360+MONTHS.index(month)*30+day)+days
    year,rest=divmod(total,360);month,day=divmod(rest,30)
    return [('year',str(year)),('month',MONTHS[month]),('day',str(day)),('hour',str(hour))]


def normalised_trade(node):
    if b.get(node,'type')!='trade':return None
    countries=b.getall(node,'country')
    if len(countries)!=2 or set(countries)!={'USA','JAP'}:return None
    sign=1 if countries[0]=='JAP' else -1
    return tuple(round(sign*float(b.get(node,k,0)),4) for k in ('oil','metal','supplies','money'))


def repair_text(text):
    original=text;hs,he,header=section(text,'header');current=b.get(header,'startdate')
    assert b.get(current,'year')=='1936' and b.get(current,'month')=='april','Inspect a later campaign before migration'
    gs,ge,g=section(text,'globaldata');cs,ce,c=section(text,'country','JAP')
    ls,le,eyr=section(text,'eyr');log=b.getall(b.get(eyr,'history',[]),'name')
    for war in b.getall(g,'war'):
        a=b.getall(b.get(war,'attackers',[]),'participant');d=b.getall(b.get(war,'defenders',[]),'participant')
        assert not ('USA' in a and 'JAP' in d or 'JAP' in a and 'USA' in d),'Cannot restore US contracts during war'
    assert not re.search(r'(?m)^history = \{[^}]*\b2049026\b',text),'US embargo already fired'
    globals_text=text[gs:ge];changes=[]
    fm=re.search(r'\bflags = \{',globals_text);assert fm
    fe=block_end(globals_text,fm.start());ftext=globals_text[fm.start():fe]
    flags=dict(b.get(g,'flags',[]));new_flags={}
    queue=b.get(g,'queued_events',[])
    additions=[];receipts=[]
    for key,target,wrapper,days in REWARDS:
        done=flags.get('JX_'+key+'_DONE')=='1'
        if done:receipts.append(dict(programme=key,status='already_delivered'));continue
        assert flags.get('JX_'+key+'_PENDING')=='1' and flags.get('JX_'+key+'_SELECTED_0')=='1',key
        root=28601742 if key=='prewar_deck_commission' else 28601745
        new_flags['JX_TIME_'+str(root)+'_'+str(days)]=1
        matches=[q for q in b.getall(queue,'event') if b.get(q,'tag')=='JAP' and int(b.get(q,'id')) in (target,wrapper)]
        assert len(matches)<=1,'Ambiguous duplicate owed receipts: '+key
        if matches:
            assert int(b.get(matches[0],'hour'))<=1,'Review an already scheduled later receipt before moving it'
            receipts.append(dict(programme=key,status='already_queued',id=int(b.get(matches[0],'id'))))
        else:
            additions.append('\t\tevent = { tag = JAP id = '+str(target)+' hour = 1 }\n')
            receipts.append(dict(programme=key,status='queued_once',id=target,hours=1))
    # Use fresh global IDs above the saved header allocator and all objects.
    maximum=max(int(x) for x in re.findall(r'id\s*=\s*\{\s*type\s*=\s*4712\s+id\s*=\s*(\d+)',text))
    next_id=maximum+1;new_treaties=[];trade_changes=[]
    for key,oil,metal,days,action,title in CONTRACTS:
        end=expiry(log,action,title,days)
        assert flags.get('JX_EARLY_'+key+'_DONE')=='1'
        if stamp(current)>=stamp(end):trade_changes.append(dict(contract=key,status='expired_not_restored'));continue
        fingerprint=(float(oil),float(metal),-4.,-1.)
        matches=[node for node in b.getall(g,'treaty') if normalised_trade(node)==fingerprint and stamp(b.get(node,'expirydate'))>stamp(current)]
        assert len(matches)<=1,'Duplicate paid agreements already exist: '+key
        new_flags['JX_PAID_US_'+key.upper()]=1
        if matches:
            assert b.get(matches[0],'cancel')=='no','Matching contract exists but needs a separate protection-only migration'
            trade_changes.append(dict(contract=key,status='already_present',expiry=dict(b.get(matches[0],'expirydate'))));continue
        # A partly matching agreement with the original expiry is ambiguous;
        # refuse to silently stack a new full contract over it.
        assert not any(normalised_trade(node) is not None and b.get(node,'expirydate')==end for node in b.getall(g,'treaty')),'Review a changed agreement with the same original expiry'
        expiry_line=' '.join(k+' = '+v for k,v in end)
        entry=('\ttreaty = {\n\t\tid = { type = 4712 id = '+str(next_id)+' }\n'
               '\t\ttype = trade\n\t\tcountry = "USA"\n\t\tcountry = "JAP"\n'
               '\t\texpirydate = { '+expiry_line+' }\n\t\toil = -'+str(oil)+'\n'
               '\t\tmetal = -'+str(metal)+'\n\t\tsupplies = 4\n\t\tmoney = 1\n\t\tcancel = no\n\t}\n')
        new_treaties.append(entry);trade_changes.append(dict(contract=key,status='restored_once',id=next_id,expiry=dict(end),oil_per_day=oil,metal_per_day=metal));next_id+=1
    for key,value in new_flags.items():
        pattern=r'\b'+re.escape(key)+r' = \d+\b'
        if re.search(pattern,ftext):ftext=re.sub(pattern,key+' = '+str(value),ftext,count=1)
        else:ftext=ftext[:-1]+'\n\t\t'+key+' = '+str(value)+'\n\t}'
    globals_text=globals_text[:fm.start()]+ftext+globals_text[fe:]
    if additions:
        qm=re.search(r'\bqueued_events = \{',globals_text);assert qm
        qe=block_end(globals_text,qm.start());globals_text=globals_text[:qe-1]+'\n'+''.join(additions)+'\t'+globals_text[qe-1:]
    if new_treaties:globals_text=globals_text[:-1]+'\n'+''.join(new_treaties)+'}'
    text=text[:gs]+globals_text+text[ge:]
    # Advance the header's allocation high-water mark; do not let subsequent
    # native production reuse either new treaty's global ID.
    if new_treaties:
        hs,he,hnode=section(text,'header');chunk=text[hs:he]
        chunk,n=re.subn(r'id = \{ type = 4712 id = \d+ \}','id = { type = 4712 id = '+str(next_id)+' }',chunk,count=1);assert n==1
        text=text[:hs]+chunk+text[he:]
    module='event = "db\\events\\japan_rising\\purchase_reliability.txt"'
    if module not in text:text+='\n'+module+'\n'
    text=re.sub(r'^name = "[^"]*"','name = "Japan Rising R15.2 - restored purchases - April 1936"',text,count=1)
    # Structural preservation: all countries, units, pools, resources, current
    # production and provinces remain identical. Only global receipt flags,
    # the two receipt callbacks, two treaties, header ID/name and registry move.
    _,_,after_c=section(text,'country','JAP');assert after_c==c
    for pid in (1544,1550,1552,1554,1557):
        pattern=r'(?m)^province = \{\s*\n\s*id = '+str(pid)+r'\b'
        m=re.search(pattern,original);n=re.search(pattern,text)
        assert original[m.start():block_end(original,m.start())]==text[n.start():block_end(text,n.start())]
    _,_,after_g=section(text,'globaldata')
    expected=copy.deepcopy(g)
    expected_flags=b.get(expected,'flags')
    for key,value in new_flags.items():
        expected_flags[:]=[(k,str(value) if k==key else v) for k,v in expected_flags]
        if not any(k==key for k,v in expected_flags):expected_flags.append((key,str(value)))
    expected_queue=b.get(expected,'queued_events')
    for addition in additions:expected_queue.extend(b.parse(addition))
    for entry in new_treaties:expected.extend(b.parse(entry))
    assert after_g==expected,'Unexpected global-state mutation'
    return text,dict(receipts=receipts,contracts=trade_changes,country_state_unchanged=True,
                     shipping_unchanged=True,pending_merchant_delivery_unchanged=True,
                     no_upfront_charge=True,no_backpay_stockpile=True,game_run=False)


def run():
    process=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert process.returncode==0 and not any(x.lower().startswith('"darkest hour.exe"') for x in process.stdout.splitlines()),'Close the game before repairing its autosave'
    folder=b.TARGET/'scenarios/save games';source=folder/'autosave.eug';raw=source.read_bytes()
    previous=b.HERE/'R15_2_SAVE_REPAIR.json'
    if previous.exists():
        existing=json.loads(previous.read_text(encoding='utf-8'))
        if existing.get('repaired_sha256')==hashlib.sha256(raw).hexdigest():
            print(json.dumps(dict(already_repaired=True,load_save=existing['load_save'],game_run=False)));return
    backup=b.HERE/'backups/before_R15_2_purchase_repair/original_autosave.eug'
    assert backup.read_bytes()==raw,'The audited source changed; reassess the latest save'
    repaired,report=repair_text(raw.decode('latin1'))
    # Idempotence is checked before writing either output.
    repeated,_=repair_text(repaired);assert repeated==repaired,'Repair would duplicate a reward or trade'
    output=repaired.encode('latin1');named=folder/'JAPAN_R15_2_PURCHASES_RESTORED_1936_APR_1.eug'
    assert source.read_bytes()==raw
    named.write_bytes(output)
    temporary=source.with_suffix('.eug.r15_2.tmp');temporary.write_bytes(output);temporary.replace(source)
    cfg=source.with_suffix('.eug.cfg')
    if cfg.exists():shutil.copy2(cfg,named.with_suffix('.eug.cfg'))
    report.update(source=str(source),backup=str(backup),load_save=str(named),
                  source_sha256=hashlib.sha256(raw).hexdigest(),repaired_sha256=hashlib.sha256(output).hexdigest(),
                  autosave_updated=True,idempotence_passed=True)
    (b.HERE/'R15_2_SAVE_REPAIR.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
