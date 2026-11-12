"""Append ten small base guards, preserving B1 and every existing event ID."""
import argparse,copy,hashlib,json,re,shutil,subprocess
from datetime import datetime
from pathlib import Path
from build import HERE,TARGET,SOURCE,GAME,read,write,parse,get,getall,serialise,prepare_catalog,EVENTS,compiled_event,documentation,localisation
from repair_completion_save import block_end
from apply_balance_b1 import countries,identity,digest
import campaign_balance as b
import localisation_support

STAGE=HERE/'staged_base_defence_b2'
SOURCE_SAVE='JAPAN_B1_1941_December_15.eug'
OUTPUT='JAPAN_B2_1941_December_15.eug'

def build_save():
    path=TARGET/'scenarios/save games'/SOURCE_SAVE
    stat=path.stat();raw=path.read_bytes();assert path.stat().st_mtime_ns==stat.st_mtime_ns
    text=raw.decode('latin1').replace('\r\n','\n').replace('\r','')
    warnings=[];old=parse(text,warnings);assert not warnings
    cs=countries(old);jap=copy.deepcopy(cs['JAP'])
    existing={identity(d) for d in getall(jap,'landdivision')}
    _,templates=b.scenario_templates(serialise)
    from garrison_profiles import complete,normalise_detachments
    additions=[(k,complete(jap,d,TARGET)) for k,d in templates if int(get(get(d,'id'),'id'))>21]
    assert len(additions)==10 and not any(identity(d) in existing for k,d in additions)
    jap.extend(additions)
    normalise_detachments(jap,TARGET)
    glob=copy.deepcopy(get(old,'globaldata'));queued=get(glob,'queued_events')
    assert queued is not None
    by={e.key:e for e in EVENTS}
    for key in ('base_gaps_b2_apply','haikou_b2_apply'):
        assert not any(get(q,'id')==str(by[key].id) for q in getall(queued,'event'))
        queued.append(('event',[('tag','JAP'),('id',str(by[key].id)),('hour','1')]))
    start=next(m for m in re.finditer(r'(?m)^country = \{',text) if re.search(r'(?m)^\s*tag = JAP\s*$',text[m.start():m.start()+500]))
    end=block_end(text,start.start());text=text[:start.start()]+'country = {\n'+serialise(jap,1)+'\n}'+text[end:]
    start=re.search(r'(?m)^globaldata = \{',text);end=block_end(text,start.start())
    text=text[:start.start()]+'globaldata = {\n'+serialise(glob,1)+'\n}'+text[end:]
    text=re.sub(r'^name = "[^"]*"','name = "Japan B2 - 15 December 1941 base guards"',text,count=1)
    text=text.replace(SOURCE_SAVE+'.cfg',OUTPUT+'.cfg',1)
    from save_event_registry import ensure_modules,queued_jx_missing
    text,added_modules=ensure_modules(text,read(TARGET/'db/events.txt'))
    assert not queued_jx_missing(text,TARGET),'Queued event missing from the save event registry'
    new=parse(text);nc=countries(new)
    for tag in cs:
        if tag!='JAP':assert nc[tag]==cs[tag],tag
    for k,v in cs['JAP']:
        if k!='landdivision':assert getall(nc['JAP'],k)==getall(cs['JAP'],k),k
    expected_old=copy.deepcopy(cs['JAP']);normalise_detachments(expected_old,TARGET)
    assert getall(nc['JAP'],'landdivision')==getall(expected_old,'landdivision')+[d for k,d in additions]
    for k,v in get(old,'globaldata'):
        if k!='queued_events':assert getall(get(new,'globaldata'),k)==getall(get(old,'globaldata'),k),k
    assert getall(get(get(new,'globaldata'),'queued_events'),'event')[:-2]==getall(get(get(old,'globaldata'),'queued_events'),'event')
    ids=[identity(n) for c in nc.values() for k,v in c if k in ('landunit','navalunit','airunit','landdivision','navaldivision','airdivision') for n in ([v] if k.endswith('division') else [v]+getall(v,'division'))]
    assert len(ids)==len(set(ids))
    write(STAGE/OUTPUT,text);shutil.copy2(path.with_suffix('.eug.cfg'),STAGE/(OUTPUT+'.cfg'))
    return {'source':str(path),'source_sha256':hashlib.sha256(raw).hexdigest(),'output':OUTPUT,'output_sha256':digest(STAGE/OUTPUT),
            'added_detachments':10,'all_detachments_after_callups':31,'extra_first_hour_bill':{'manpower':25,'supplies':400,'money':30},
            'preserved':['B1 Chinese army and unlock timers','B1 Italian recovery queue','original 21-island call-up','all existing countries, units, orders, stocks, wars and alliances']}

def stage():
    STAGE.mkdir(exist_ok=True);prepare_catalog();r=build_save();files=[]
    old=json.loads(read(TARGET/'Japan Rising Documentation/events.json'));by={e.key:e for e in EVENTS}
    nodes={get(e,'id'):e for p in (TARGET/'db/events/japan_rising').glob('*.txt') for e in getall(parse(read(p)),'event')}
    for e in old:
        assert by[e['key']].id==e['id']
        assert nodes[str(e['id'])]==get(parse(compiled_event(by[e['key']])),'event'),e['key']
    documentation()
    def add(rel,text):write(STAGE/rel,text);files.append(rel)
    add('db/events/japan_rising/campaign_balance.txt','\n\n'.join(compiled_event(e) for e in EVENTS if e.module=='campaign_balance')+'\n')
    localisation_support.install(SOURCE,STAGE,localisation(),read,write)
    files+=['config/mods.csv','config/japan_rising.csv']
    rel='scenarios/1933/japan.inc';tree=parse(read(TARGET/rel));_,templates=b.scenario_templates(serialise)
    additions=[(k,d) for k,d in templates if int(get(get(d,'id'),'id'))>21]
    assert len(additions)==10
    get(tree,'country').extend(additions);add(rel,serialise(tree)+'\n')
    r.update(state='staged',files=files,old_event_ids_and_definitions_preserved=len(old),
      before={rel:digest(TARGET/rel) for rel in files},staged={rel:digest(STAGE/rel) for rel in files},game_executed=False)
    (STAGE/'REVIEW.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({k:v for k,v in r.items() if k not in ('files','before','staged')}))

def install():
    p=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert p.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in p.stdout.splitlines()),'Game running; patch remains staged'
    r=json.loads((STAGE/'REVIEW.json').read_text());assert r['state']=='staged'
    assert digest(Path(r['source']))==r['source_sha256']
    assert not (TARGET/'scenarios/save games'/OUTPUT).exists()
    for rel in r['files']:
        assert digest(TARGET/rel)==r['before'][rel] and digest(STAGE/rel)==r['staged'][rel],rel
    backup=HERE/'backups'/('before-base-defence-B2-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    for rel in r['files']+['JAPAN_RISING_BUILD.json']:
        (backup/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TARGET/rel,backup/rel)
    for rel in r['files']:shutil.copy2(STAGE/rel,TARGET/rel)
    for name in (OUTPUT,OUTPUT+'.cfg'):shutil.copy2(STAGE/name,TARGET/'scenarios/save games'/name)
    hashes=json.loads((HERE/'INSTALLED_FILE_HASHES.json').read_text())
    for rel in r['files']:hashes[str(Path(rel))]=digest(TARGET/rel)
    (HERE/'INSTALLED_FILE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    manifest=json.loads(read(TARGET/'JAPAN_RISING_BUILD.json'))
    manifest.update(base_defence_hotfix='B2',state='installed-awaiting-offline-checks',events=len(EVENTS),decisions=sum(e.decision for e in EVENTS),spec_sha256=(HERE/'SPEC_SHA256.txt').read_text().strip())
    write(TARGET/'JAPAN_RISING_BUILD.json',json.dumps(manifest,indent=2)+'\n')
    r.update(state='installed',backup=str(backup));(STAGE/'REVIEW.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({'state':'installed','save':OUTPUT,'old_B1_save_unchanged':digest(Path(r['source']))==r['source_sha256'],'game_executed':False}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['stage','install']);args=ap.parse_args()
    if args.mode=='install':prepare_catalog()
    {'stage':stage,'install':install}[args.mode]()
