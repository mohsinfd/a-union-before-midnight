"""Repair December 23 garrisons and supply routes without running the game."""
import copy,hashlib,json,os,re,shutil,subprocess
from datetime import datetime
from pathlib import Path
from build import HERE,TARGET,GAME,read,write,parse,get,getall,serialise,province_names
from repair_completion_save import block_end
from garrison_profiles import normalise_detachments,vals
from garrison_supply import supply_routes
from save_event_registry import ensure_modules,queued_jx_missing

SOURCE_NAME='testEmpire of Japan_1941_December_23.eug'
OUTPUT='JAPAN_B3_1941_December_23.eug'
STAGE=HERE/'staged_garrison_b3'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def cs(root):return {get(c,'tag'):c for c in getall(root,'country')}
def ships(c):return int(get(c,'transports'))+sum(int(get(q,'transports',0)) for q in getall(c,'convoy'))

def stage():
    path=TARGET/'scenarios/save games'/SOURCE_NAME;raw=path.read_bytes();text=raw.decode('latin1')
    assert sha(raw)=='230f5d0c73a79ad2bb1464ca67e13885579396fdb67d56c5356fea638d0e4d98','Reassess a changed campaign before repairing it'
    old=parse(text);new=copy.deepcopy(old);oldcs=cs(old);newcs=cs(new)
    assert dict(get(get(old,'header'),'startdate'))=={'year':'1941','month':'december','day':'22','hour':'5'}
    bad=[d for f in getall(newcs['JAP'],'landunit') for d in getall(f,'division') if get(get(d,'id'),'type')=='28632']
    assert len(bad)==31 and all(float(vals(d,'all')[7])==0 and float(vals(d,'land')[4])==0 for d in bad)
    restored=sum(25-float(vals(d,'all')[0]) for d in bad)
    assert normalise_detachments(newcs['JAP'],TARGET,restore=True)==31
    routes=supply_routes(new,GAME)
    affected={r['owner'] for r in routes['added']}|{'JAP'}
    for tag in affected:assert ships(newcs[tag])==ships(oldcs[tag]),tag
    for tag in oldcs:
        if tag not in affected:assert oldcs[tag]==newcs[tag],tag
        else:
            excepts={'convoy','transports'}|({'landunit'} if tag=='JAP' else set())
            for k,v in oldcs[tag]:
                if k not in excepts:assert getall(oldcs[tag],k)==getall(newcs[tag],k),(tag,k)
    for k,v in old:
        if k!='country':assert getall(old,k)==getall(new,k),k
    # Rewrite only the changed countries; province depots, all flags and queues
    # remain exactly as saved. No unshipped supply is conjured into island pools.
    for tag in sorted(affected):
        start=next(m for m in re.finditer(r'(?m)^country = \{',text) if re.search(r'(?m)^\s*tag = '+tag+r'\s*$',text[m.start():m.start()+500]))
        end=block_end(text,start.start());text=text[:start.start()]+'country = {\n'+serialise(newcs[tag],1)+'\n}'+text[end:]
    text=re.sub(r'^name = "[^"]*"','name = "Japan B3 - 23 December 1941 garrison and supply repair"',text,count=1)
    text=text.replace(SOURCE_NAME+'.cfg',OUTPUT+'.cfg',1)
    text,added_modules=ensure_modules(text,read(TARGET/'db/events.txt'));assert queued_jx_missing(text,TARGET)==[]
    warnings=[];check=parse(text,warnings);assert not warnings
    cc=cs(check)
    for tag in newcs:assert cc[tag]==newcs[tag],tag
    # Names/dates are the only header differences. All original flags, timer
    # entries, province stocks and country resources except assigned convoys stay.
    assert get(check,'globaldata')==get(old,'globaldata')
    assert getall(check,'province')==getall(old,'province')
    STAGE.mkdir(exist_ok=True);(STAGE/OUTPUT).write_bytes(text.encode('latin1'))
    shutil.copy2(path.with_suffix('.eug.cfg'),STAGE/(OUTPUT+'.cfg'))
    names=province_names()
    for row in routes['added']:
        row['from_name']=names[row['from']];row['to_name']=names[row['to']]
        row['served_names']=[names[p] for p in row['served_guard_provinces']]
    report={'state':'staged','source':str(path),'source_sha256':sha(raw),'output':OUTPUT,'output_sha256':sha((STAGE/OUTPUT).read_bytes()),
      'repaired_units':31,'restored_strength_points':restored,'new_profile':{'model':4,'strength':25,'max_strength':25,'soft_attack':8,'hard_attack':2,'defensiveness':35,'supply_consumption':0.2,'max_org':66},
      'supply_routes':routes,'convoy_reserve_before':{t:get(oldcs[t],'transports') for t in affected},
      'convoy_reserve_after':{t:get(newcs[t],'transports') for t in affected},'convoy_ships_conserved':True,
      'other_units_countries_resources_and_timers_preserved':True,'additional_event_references':added_modules,'game_executed':False}
    (STAGE/'REVIEW.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

def install():
    proc=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert proc.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in proc.stdout.splitlines())
    r=json.loads((STAGE/'REVIEW.json').read_text());assert r['state']=='staged'
    assert sha(Path(r['source']).read_bytes())==r['source_sha256']
    assert sha((STAGE/OUTPUT).read_bytes())==r['output_sha256']
    dest=TARGET/'scenarios/save games'/OUTPUT;assert not dest.exists()
    backup=HERE/'backups'/('before-garrison-B3-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir(parents=True)
    shutil.copy2(r['source'],backup/SOURCE_NAME)
    shutil.copy2(TARGET/'JAPAN_RISING_BUILD.json',backup/'JAPAN_RISING_BUILD.json')
    for name in (OUTPUT,OUTPUT+'.cfg'):shutil.copy2(STAGE/name,TARGET/'scenarios/save games'/name)
    r.update(state='installed',backup=str(backup));(STAGE/'REVIEW.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({'state':'installed','save':str(dest),'original_unchanged':sha(Path(r['source']).read_bytes())==r['source_sha256'],'game_executed':False}))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['stage','install']);args=ap.parse_args()
    {'stage':stage,'install':install}[args.mode]()
