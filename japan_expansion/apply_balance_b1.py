"""Stage and install a focused B1 patch and a separate December save copy.

Never launches or controls Darkest Hour. Refuses installation under its process.
"""
import argparse,copy,hashlib,json,re,shutil,subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from build import HERE,TARGET,SOURCE,GAME,read,write,parse,get,getall,serialise,compiled_event,localisation,prepare_catalog,EVENTS,documentation
from repair_completion_save import block_end
import campaign_balance as b
import localisation_support

STAGE=HERE/'staged_balance_b1'
SAVE='sdEmpire of Japan_1941_November_5.eug'
OUTPUT='JAPAN_B1_1941_December_15.eug'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,k,v):
    n[:]=[(key,value) for key,value in n if key!=k];n.append((k,str(v)))
def values(n,k):return [v for _,v in get(n,k,[])]
def identity(n):return tuple(int(get(get(n,'id'),k)) for k in ('type','id'))
def countries(root):return {get(c,'tag'):c for c in getall(root,'country')}
def unit_stats(d):return [float(v) for v in values(d,'all')]
def unit_type(d):return int(values(d,'mod')[0])
def division_records(c):return [(f,d) for f in getall(c,'landunit') for d in getall(f,'division')]

def prepare_save():
    source=TARGET/'scenarios/save games'/SAVE
    before=source.stat();raw=source.read_bytes();assert source.stat().st_mtime_ns==before.st_mtime_ns
    original=parse(raw.decode('latin1'));cs=countries(original)
    date=dict(get(get(original,'header'),'startdate'))
    assert date=={'year':'1941','month':'december','day':'14','hour':'23'},date
    assert get(cs['U87'],'puppet')=='JAP' and not any('U87' in str(w) for w in getall(get(original,'globaldata'),'war'))
    cn=copy.deepcopy(cs['U87']);records=division_records(cn)
    assert len(records)==169
    assert not any(get(f,'control') not in (None,'U87','CHI') for f,d in records),'Foreign expeditionary units require separate handling'
    # Retain the better-equipped and more experienced cadres. No Japanese,
    # Chinese air/naval or dormant formations enter this selection.
    selected=[]
    for typ,count in ((0,72),(11,18),(10,4),(1,2)):
        candidates=[d for f,d in records if unit_type(d)==typ]
        candidates.sort(key=lambda d:(int(values(d,'mod')[2]),unit_stats(d)[5],unit_stats(d)[0]),reverse=True)
        assert len(candidates)>=count
        selected.extend(candidates[:count])
    chosen={identity(d) for d in selected};assert len(chosen)==96
    ready=[d for d in selected if unit_type(d) in (10,1)]+[d for d in selected if unit_type(d)==0 and not int(get(d,'flag'))&2][:26]
    assert len(ready)==32
    locked=[d for d in selected if identity(d) not in {identity(x) for x in ready}]
    # Each release wave has 23 infantry and nine militia.
    li=[d for d in locked if unit_type(d)==0];lm=[d for d in locked if unit_type(d)==11]
    waves=[li[:23]+lm[:9],li[23:]+lm[9:]]
    bands={identity(d):0 for d in ready}
    for stage,wave in enumerate(waves,1):
        assert len(wave)==32
        bands.update({identity(d):stage for d in wave})
    # Keep the leader with the original/free formation. Split mixed formations
    # so one locked division does not immobilise the ready group as well.
    next_corps=1;updated=[]
    for f in getall(cn,'landunit'):
        ds=[d for d in getall(f,'division') if identity(d) in chosen]
        for index,band in enumerate(sorted({bands[identity(d)] for d in ds})):
            nf=copy.deepcopy([(k,v) for k,v in f if k!='division'])
            if index:
                nf[:]=[(k,v) for k,v in nf if k not in ('id','leader','mission','movement','movetime')]
                nf.insert(0,('id',[('type','28633'),('id',str(next_corps))]));next_corps+=1
            if band:
                nf[:]=[(k,v) for k,v in nf if k not in ('mission','movement','movetime')]
                put(nf,'name',get(f,'name')+' - Local Defence '+str(band))
            for d in ds:
                if bands[identity(d)]!=band:continue
                nd=copy.deepcopy(d)
                flags=int(get(nd,'flag'));assert not flags&1,(get(nd,'name'),flags)
                put(nd,'flag',flags|2 if band else flags)
                nf.append(('division',nd))
            updated.append(('landunit',nf))
    cn[:]=[(k,v) for k,v in cn if k!='landunit']+updated
    assert Counter(unit_type(d) for f,d in division_records(cn))=={0:72,11:18,10:4,1:2}
    # Store only the identities needed by this save. Events are gated by an
    # explicit legacy marker so new campaigns cannot unlock unrelated units.
    legacy={'source_sha256':hashlib.sha256(raw).hexdigest(),'stages':[[list(identity(d)) for d in wave] for wave in waves]}
    (HERE/'china_legacy_b1.json').write_text(json.dumps(legacy,indent=2))
    prepare_catalog();by={e.key:e for e in EVENTS}
    jap=copy.deepcopy(cs['JAP']);_,islands=b.scenario_templates(serialise)
    from garrison_profiles import complete
    # Saved-game unit records need their full packed stats. The scenario's
    # short model-based definitions are not valid substitutes in a save.
    islands=[(k,complete(jap,d,TARGET)) for k,d in islands if int(get(get(d,'id'),'id'))<=21]
    jap.extend(islands)
    glob=copy.deepcopy(get(original,'globaldata'));flags=get(glob,'flags')
    for name in ('JX_CN_LEGACY','JX_CN_REORG'):put(flags,name,1)
    queued=get(glob,'queued_events')
    if queued is None:queued=[];glob.append(('queued_events',queued))
    for key,tag,hours in [('cn_legacy_release_1','U87',360*24),('cn_legacy_release_2','U87',720*24),
                          ('island_muster_b1','JAP',1),('ita_apply_b1','ITA',1)]:
        queued.append(('event',[('tag',tag),('id',str(by[key].id)),('hour',str(hours))]))
    # Replace just the affected blocks, retaining every other country verbatim.
    text=raw.decode('latin1')
    for tag,node in [('JAP',jap),('U87',cn)]:
        starts=list(re.finditer(r'(?m)^country = \{',text))
        m=next(m for m in starts if re.search(r'(?m)^\s*tag = '+tag+r'\s*$',text[m.start():m.start()+500]))
        end=block_end(text,m.start());text=text[:m.start()]+'country = {\n'+serialise(node,1)+'\n}'+text[end:]
    m=re.search(r'(?m)^globaldata = \{',text);end=block_end(text,m.start())
    text=text[:m.start()]+'globaldata = {\n'+serialise(glob,1)+'\n}'+text[end:]
    text=text.replace('optionfile = "scenarios\\save games\\'+SAVE+'.cfg"','optionfile = "scenarios\\save games\\'+OUTPUT+'.cfg"',1)
    text=re.sub(r'^name = "[^"]*"','name = "Japan B1 - 15 December 1941"',text,count=1)
    from save_event_registry import ensure_modules,queued_jx_missing
    text,_=ensure_modules(text,read(TARGET/'db/events.txt'))
    assert not queued_jx_missing(text,TARGET),'Queued event missing from the save event registry'
    # Verify semantic preservation; compact flag placement alone may reorder.
    warnings=[];result=parse(text,warnings);assert not warnings
    outcs=countries(result)
    for tag in cs:
        if tag not in ('JAP','U87'):assert outcs[tag]==cs[tag],tag
    for kind in ('landunit','navalunit','airunit','division_development','landdivision','navaldivision'):
        assert getall(outcs['JAP'],kind)==getall(cs['JAP'],kind)+(islands and [v for k,v in islands] if kind=='landdivision' else []),kind
    for k,v in cs['JAP']:
        if k!='landdivision':assert getall(outcs['JAP'],k)==getall(cs['JAP'],k),k
    for k,v in cs['U87']:
        if k!='landunit':assert getall(outcs['U87'],k)==getall(cs['U87'],k),k
    for k,v in get(original,'globaldata'):
        if k not in ('flags','queued_events'):assert getall(get(result,'globaldata'),k)==getall(get(original,'globaldata'),k),k
    ids=[identity(n) for c in outcs.values() for k,v in c if k in ('landunit','navalunit','airunit','landdivision','navaldivision','airdivision') for n in ([v] if k.endswith('division') else [v]+getall(v,'division'))]
    assert len(ids)==len(set(ids)), 'Duplicate unit identity'
    assert sum(int(get(d,'flag'))&2!=0 for f,d in division_records(outcs['U87']))==64
    STAGE.mkdir(exist_ok=True);write(STAGE/OUTPUT,text)
    shutil.copy2(source.with_suffix('.eug.cfg'),STAGE/(OUTPUT+'.cfg'))
    return {'source':str(source),'source_sha256':hashlib.sha256(raw).hexdigest(),'output':OUTPUT,
      'retained_chinese_formations':96,'retired_chinese_formations':73,'ready_chinese_formations':32,
      'locked_chinese_formations':64,'unlock_waves_days':[360,720],'island_detachments':21,
      'island_max_strength':25,'island_first_hour_bill':{'manpower':53,'supplies':900,'money':60},
      'first_hour_Italy':{'oil':4000,'supplies':4000,'infantry_up_to':12,'temporary_daily_oil':8,'duration_days':360},
      'other_countries_preserved':True,'existing_Japanese_units_queues_and_stocks_preserved':True}

def stage():
    STAGE.mkdir(exist_ok=True);report=prepare_save();files=[]
    documentation()
    # Old IDs must survive every extension.
    old=json.loads(read(TARGET/'Japan Rising Documentation/events.json'))
    by={e.key:e for e in EVENTS}
    assert all(by[e['key']].id==e['id'] for e in old)
    changed={'china','base_guard','procurement1937_finish_0','procurement1937_finish_1'}
    oldnodes={get(n,'id'):n for p in (TARGET/'db/events/japan_rising').glob('*.txt') for n in getall(parse(read(p)),'event')}
    for e in EVENTS:
        if e.key not in changed and e.module!='campaign_balance':assert oldnodes[str(e.id)]==get(parse(compiled_event(e)),'event'),e.key
    def add(rel,text):write(STAGE/rel,text);files.append(rel)
    for module in sorted({e.module for e in EVENTS if e.key in changed}|{'campaign_balance'}):
        add('db/events/japan_rising/'+module+'.txt','\n\n'.join(compiled_event(e) for e in EVENTS if e.module==module)+'\n')
    index=read(TARGET/'db/events.txt')
    assert 'japan_rising\\campaign_balance.txt' not in index
    add('db/events.txt',index+'\nevent = "db\\events\\japan_rising\\campaign_balance.txt"\n')
    localisation_support.install(SOURCE,STAGE,localisation(),read,write)
    files+=['config/mods.csv','config/japan_rising.csv']
    cn,jp=b.scenario_templates(serialise)
    for rel,entries in [('scenarios/1933/china nationalist.inc',cn),('scenarios/1933/japan.inc',jp)]:
        tree=parse(read(TARGET/rel));assert not any(get(get(d,'id'),'type') in (str(b.CHINA_TYPE),str(b.ISLAND_TYPE)) for d in getall(get(tree,'country'),'landdivision'))
        get(tree,'country').extend(entries);add(rel,serialise(tree)+'\n')
    for rel,text in b.extra_ai(read(TARGET/'ai/jx/partner_land.ai'),parse,get,serialise).items():add(rel,text)
    for path in (TARGET/'ai').rglob('*.ai'):
        if path.name.lower().startswith('ita_') and 'jx' not in path.parts:
            add(path.relative_to(TARGET).as_posix(),b.italy_ai(read(path),parse,get,serialise))
    report.update(state='staged',old_event_ids_preserved=len(old),files=files,
      before={rel:digest(TARGET/rel) if (TARGET/rel).exists() else None for rel in files},
      staged={rel:digest(STAGE/rel) for rel in files},output_sha256=digest(STAGE/OUTPUT),game_executed=False)
    (STAGE/'REVIEW.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('before','staged','files')}))

def install():
    p=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert p.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in p.stdout.splitlines()),'Game running; installation remains staged'
    r=json.loads((STAGE/'REVIEW.json').read_text());assert r['state']=='staged'
    assert digest(Path(r['source']))==r['source_sha256']
    for rel in r['files']:
        assert digest(STAGE/rel)==r['staged'][rel]
        assert (digest(TARGET/rel) if (TARGET/rel).exists() else None)==r['before'][rel],rel
    assert not (TARGET/'scenarios/save games'/OUTPUT).exists()
    backup=HERE/'backups'/('before-balance-B1-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    for rel in r['files']+['JAPAN_RISING_BUILD.json']:
        if (TARGET/rel).exists():
            (backup/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TARGET/rel,backup/rel)
    for rel in r['files']:
        (TARGET/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(STAGE/rel,TARGET/rel)
    for name in (OUTPUT,OUTPUT+'.cfg'):shutil.copy2(STAGE/name,TARGET/'scenarios/save games'/name)
    hashes=json.loads((HERE/'INSTALLED_FILE_HASHES.json').read_text())
    for rel in r['files']:hashes[str(Path(rel))]=digest(TARGET/rel)
    hashes=dict(sorted(hashes.items()));(HERE/'INSTALLED_FILE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    manifest=json.loads(read(TARGET/'JAPAN_RISING_BUILD.json'))
    manifest.update(campaign_balance_hotfix='B1',state='installed-awaiting-offline-checks',spec_sha256=(HERE/'SPEC_SHA256.txt').read_text().strip(),
       events=len(EVENTS),decisions=sum(e.decision for e in EVENTS),fingerprinted_files=len(hashes),
       installed_fingerprint_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest())
    write(TARGET/'JAPAN_RISING_BUILD.json',json.dumps(manifest,indent=2)+'\n')
    r.update(state='installed',backup=str(backup));(STAGE/'REVIEW.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({'state':'installed','files':len(r['files']),'save':str(TARGET/'scenarios/save games'/OUTPUT),'original_unchanged':digest(Path(r['source']))==r['source_sha256'],'game_executed':False}))

def refresh():
    """Apply reviewed eligibility guards without recreating the campaign copy."""
    p=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert p.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in p.stdout.splitlines())
    r=json.loads((STAGE/'REVIEW.json').read_text());assert r['state']=='installed'
    documentation();hashes=json.loads((HERE/'INSTALLED_FILE_HASHES.json').read_text())
    for module in ('settlements','campaign_balance'):
        rel='db/events/japan_rising/'+module+'.txt'
        assert digest(TARGET/rel)==r['staged'][rel]
        delta=Path(r['backup'])/'b1-eligibility-guards'/rel
        delta.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TARGET/rel,delta)
        write(STAGE/rel,'\n\n'.join(compiled_event(e) for e in EVENTS if e.module==module)+'\n')
        shutil.copy2(STAGE/rel,TARGET/rel);r['staged'][rel]=digest(TARGET/rel);hashes[str(Path(rel))]=digest(TARGET/rel)
    (HERE/'INSTALLED_FILE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    manifest=json.loads(read(TARGET/'JAPAN_RISING_BUILD.json'));manifest['spec_sha256']=(HERE/'SPEC_SHA256.txt').read_text().strip()
    write(TARGET/'JAPAN_RISING_BUILD.json',json.dumps(manifest,indent=2)+'\n')
    (STAGE/'REVIEW.json').write_text(json.dumps(r,indent=2));print('Updated two event files; campaign copy unchanged.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['stage','install','refresh']);args=ap.parse_args()
    if args.mode!='stage':prepare_catalog()
    {'stage':stage,'install':install,'refresh':refresh}[args.mode]()
