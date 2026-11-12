"""Write a separate copy of the user's post-failure save; never overwrite it."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import csv
from build import HERE,TARGET,GAME,read,parse,get,getall,prepare_catalog,IDS


def block_end(text,start):
    depth=0;quoted=False
    for i in range(text.index('{',start),len(text)):
        if text[i]=='"':quoted=not quoted
        if quoted:continue
        depth+=(text[i]=='{')-(text[i]=='}')
        if depth==0:return i+1
    raise ValueError('Unclosed save block')


def effective_ic(node,base):
    ic=get(node,'ic')
    if ic is None:return base,base
    size=float(get(ic,'size',base))
    return size,float(get(ic,'current_size',size))


def industry_totals(text,mapic):
    sizes=mapic.copy();current=mapic.copy()
    for m in re.finditer(r'(?m)^province = \{',text):
        node=get(parse(text[m.start():block_end(text,m.start())]),'province');pid=int(get(node,'id'))
        sizes[pid],current[pid]=effective_ic(node,mapic.get(pid,0))
    m=next(m for m in re.finditer(r'(?m)^country = \{',text) if re.search(r'(?m)^\s*tag = JAP\s*$',text[m.start():m.start()+500]))
    chunk=text[m.start():block_end(text,m.start())]
    groups={}
    for key in ('ownedprovinces','controlledprovinces','nationalprovinces'):
        groups[key]={int(x) for x in re.search(r'(?m)^\t'+key+r' = \{([^}]*)\}',chunk)[1].split()}
    working=groups['ownedprovinces']&groups['controlledprovinces'];core=working&groups['nationalprovinces']
    return {'core':sum(sizes[p] for p in core),'current_core':sum(current[p] for p in core),
            'noncore':sum(sizes[p] for p in working-core),'physical_total':sum(sizes[p] for p in working)}


def run(source_name='autosave.eug'):
    prepare_catalog()
    assert Path(source_name).name==source_name and source_name.endswith('.eug')
    source=TARGET/'scenarios/save games'/source_name
    before=source.stat();raw=source.read_bytes();after=source.stat()
    assert before.st_mtime_ns==after.st_mtime_ns and len(raw)==after.st_size,'Save was being written; retry'
    text=raw.decode('latin1').replace('\r\n','\n');original=text;changes=[]
    header_start=text.index('header = {');header_end=block_end(text,header_start)
    header=get(parse(text[header_start:header_end]),'header');date=dict(get(header,'startdate'))
    assert date['year']=='1934' and date['month'] in {'april','may'},'Review an uninspected campaign date first'
    source_snapshot=Path((HERE/'COMPLETION_FIX_BACKUP.txt').read_text())/('source_'+source_name)
    assert not source_snapshot.exists() or source_snapshot.read_bytes()==raw
    source_snapshot.write_bytes(raw)
    def set_flag(key,value):
        nonlocal text
        pattern=r'(?m)^(\s*'+re.escape(key)+r'\s*=\s*)\d+(\s*)$'
        text,count=re.subn(pattern,lambda m:m[1]+str(value)+m[2],text)
        assert count==1,(key,count)
    assert re.search(r'JX_first_industry_WAIT\s*=\s*1\b',text)
    assert re.search(r'JX_first_industry_DONE\s*=\s*0\b',text)
    assert re.search(r'JX_merchant_prewar_DONE\s*=\s*1\b',text)
    mapfile=TARGET/'map/Map_1/Province.csv'
    if not mapfile.exists():mapfile=GAME/'map/Map_1/Province.csv'
    mapic={int(r['Id']):float(r['IC'] or 0) for r in csv.DictReader(read(mapfile).splitlines(),delimiter=';') if r['Id'].isdigit()}
    for p in (1552,1554):
        m=re.search(r'(?m)^province = \{\s*\n\s*id = '+str(p)+r'\b',text);assert m
        end=block_end(text,m.start());chunk=text[m.start():end]
        old=get(parse(chunk),'province');ic=get(old,'ic',[]);oldsize,current=effective_ic(old,mapic[p])
        if ic:
            chunk,n=re.subn(r'ic = \{ size = [-\d.]+ current_size = [-\d.]+ \}',f'ic = {{ size = {oldsize+3:g} current_size = {current+3:g} }}',chunk);assert n==1
        else:
            entry=f'\tic = {{ size = {oldsize+3:g} current_size = {current+3:g} }}\n'
            chunk,n=re.subn(r'(id = '+str(p)+r'\s*\n)',lambda m:m[1]+entry,chunk,count=1);assert n==1
        assert float(get(get(get(parse(chunk),'province'),'ic'),'size'))==oldsize+3
        text=text[:m.start()]+chunk+text[end:]
        changes.append({'province':p,'ic_before':oldsize,'ic_after':oldsize+3})
    # The failed event refunded its original setup bill. Restore that bill when
    # delivering the missed six factories, rather than granting free industry.
    country_starts=list(re.finditer(r'(?m)^country = \{',text));chosen=None
    for m in country_starts:
        if re.search(r'(?m)^\s*tag = JAP\s*$',text[m.start():m.start()+500]):chosen=m;break
    assert chosen
    end=block_end(text,chosen.start());chunk=text[chosen.start():end]
    for key,cost in (('money',200),('supplies',900)):
        m=re.search(r'(?m)^\t'+key+r' = ([-\d.]+)\s*$',chunk);assert m
        amount=float(m[1]);assert amount>=cost
        chunk=chunk[:m.start(1)]+f'{amount-cost:.4f}'+chunk[m.end(1):]
        changes.append({'resource':key,'before':amount,'after':amount-cost,'reason':'Restore refunded industrial setup payment'})
    text=text[:chosen.start()]+chunk+text[end:]
    for key,value in {'JX_first_industry_DONE':1,'JX_first_industry_PENDING':0,'JX_first_industry_WAIT':0,'JX_CS_0_DONE':1,'JX_CS_0_ACTIVE':0}.items():set_flag(key,value)
    return_id=IDS['first_industry_return']
    text=re.sub(r'(?m)^\s*event = \{ tag = JAP id = '+str(return_id)+r' hour = \d+ \}\s*\n','',text)
    # Keep the native 50-oil treaty untouched and add the missing 8-oil contract.
    contracts=[]
    for m in re.finditer(r'(?m)^\s*treaty = \{',text):
        end=block_end(text,m.start());node=get(parse(text[m.start():end]),'treaty')
        if get(node,'type')=='trade' and set(getall(node,'country'))=={'USA','JAP'}:contracts.append((m.start(),end,node))
    assert len(contracts)==1 and float(get(contracts[0][2],'oil'))==-50,'Unexpected US trade state; do not duplicate an agreement'
    maxid=max(int(x) for x in re.findall(r'id = \{ type = 4712 id = (\d+) \}',text));tid=maxid+1
    treaty='\n\ttreaty = {\n\t\tid = { type = 4712 id = '+str(tid)+' }\n\t\ttype = trade\n\t\tcountry = "USA"\n\t\tcountry = "JAP"\n\t\texpirydate = { year = 1935 month = may day = 0 hour = 0 }\n\t\toil = -8\n\t\tsupplies = 1\n\t\tmoney = 0.4\n\t\tcancel = no\n\t}\n'
    start=contracts[0][0];text=text[:start]+treaty+text[start:]
    header_end=block_end(text,text.index('header = {'))
    head=text[:header_end]
    head,n=re.subn(r'(id = \{ type = 4712 id = )\d+( \})',lambda m:m[1]+str(tid+1)+m[2],head,count=1);assert n==1
    text=head+text[header_end:]
    day=int(date['day'])+1;month=date['month'].capitalize()
    text=re.sub(r'^name = "[^"]*"',f'name = "Japan Rising R5 L2 - {day} {month} 1934 IC fixed"',text,count=1)
    changes.append({'trade':'USA to JAP','oil_per_day':8,'supplies_per_day':-1,'money_per_day':-.4,'expiry':'1935-05-01','cancel':'no','setup_charged_again':False,'retroactive_stockpile_credit':False})
    destination=source.with_name(f'JAPAN_R5_L2_1934_{month}_{day}_ICFIX.eug')
    assert not destination.exists(),'Refusing to overwrite an existing repaired campaign'
    original_industry=industry_totals(original,mapic);repaired_industry=industry_totals(text,mapic)
    assert repaired_industry['core']-original_industry['core']==6
    assert repaired_industry['current_core']-original_industry['current_core']==6
    assert repaired_industry['noncore']==original_industry['noncore']
    assert repaired_industry['physical_total']-original_industry['physical_total']==6
    # Check brace structure without serialising/reformatting the whole save.
    for name,data in (('source',original),('repaired',text)):
        masked=re.sub(r'"[^"\n]*"|#[^\n]*','',data)
        assert masked.count('{')==masked.count('}'),name+' unbalanced braces'
    destination.write_bytes(text.replace('\n','\r\n').encode('latin1'))
    assert source.read_bytes()==raw,'Source save changed during repair; original was not written by this script'
    report={'result':'PASS','source':str(source),'source_snapshot':str(source_snapshot),'source_sha256':hashlib.sha256(raw).hexdigest(),
            'repaired_save':str(destination),'repaired_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'date':date,'changes':changes,'convoy_reward_not_added_twice':True,'seamanship_morale_unchanged':True,
            'industry_before':original_industry,'industry_after':repaired_industry,
            'game_executed':False,'scope':'Text/save structure verification, not an engine load test'}
    previous=HERE/'COMPLETION_SAVE_REPAIR.json'
    if previous.exists():
        old=json.loads(previous.read_text());d=old['date']
        shutil.copy2(previous,HERE/('COMPLETION_SAVE_REPAIR_'+d['year']+'_'+d['month']+'_'+str(int(d['day'])+1)+'.json'))
    previous.write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'autosave.eug')
