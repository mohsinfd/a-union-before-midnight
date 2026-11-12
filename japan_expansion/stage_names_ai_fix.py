"""Stage a focused correction; installation refuses an open game."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build import HERE,TARGET,SOURCE,read,write,parse,get,getall,serialise,prepare_catalog,EVENTS,compiled_event
from specialist_units import CLASSES,model_years
from model_names_and_ai import model_names,axis_ai,remove_generic_model_conflicts

STAGE=HERE/'staged_names_ai_fix'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def stage():
    STAGE.mkdir(exist_ok=True);files=[]
    prepare_catalog()
    def add(rel,text):
        write(STAGE/rel,text);files.append(rel)
    add('config/models.csv',model_names(read(SOURCE/'config/models.csv'),CLASSES,model_years))
    add('config/mods.csv',remove_generic_model_conflicts(read(TARGET/'config/mods.csv'),CLASSES,model_years))
    for p in sorted((SOURCE/'ai').glob('*.ai')):
        if p.name.lower().startswith(('ger_','ita_')):add('ai/'+p.name,axis_ai(read(p),p.name))
    early=[e for e in EVENTS if e.module=='early']
    installed={get(e,'id'):e for e in getall(parse(read(TARGET/'db/events/japan_rising/early.txt')),'event')}
    for e in early:
        if e.key!='materials1938':assert installed[str(e.id)]==get(parse(compiled_event(e)),'event'),e.key
    add('db/events/japan_rising/early.txt','\n\n'.join(compiled_event(e) for e in early)+'\n')
    models=read(STAGE/'config/models.csv');before=models.split('#EOF',1)[0]
    names={r[0]:r[1] for l in before.splitlines() if len(r:=l.split(';'))>1}
    assert all(names[f'MODEL{prefix}_{info["index"]}_{i}']==f'{info["name"]} {year}'
               for unit,info in CLASSES.items() for i,year in enumerate(model_years(unit)) for prefix in ('','_JAP'))
    assert all(names[f'MODEL_JAP_41_{i}'] for i in range(5))
    for rel in [r for r in files if r.startswith('ai/')]:
        text=read(STAGE/rel);node=parse(text);g=get(node,'garrison',[])
        priorities=get(g,'province_priorities',[]);keys=[k for k,v in priorities]
        assert len(keys)==len(set(keys)),rel
        # No AI behaviour outside the explicit root settings and priority list changes.
        original=parse(read(SOURCE/rel));oldg=get(original,'garrison',[])
        strip=lambda n,excluded:[(k,v) for k,v in n if k not in excluded]
        assert strip(node,{'reinforcement','max_garrison_prop','min_garrison_prop','garrison'})==strip(original,{'reinforcement','max_garrison_prop','min_garrison_prop','garrison'}),rel
        assert strip(g,{'province_priorities'})==strip(oldg,{'province_priorities'}),rel
    report={'result':'PASS','state':'staged','label':'R5 L4 N1','files':files,
            'stage_hashes':{rel:digest(STAGE/rel) for rel in files},
            'installed_before_hashes':{rel:digest(TARGET/rel) for rel in files},
            'model_keys_before_EOF':35,'AI_files_reviewed':len([r for r in files if r.startswith('ai/')]),
            'event_changes':['materials1938 gate accepts ongoing China war; existing budgets and once-only guards unchanged'],
            'no_save_state_changed':True,'game_executed':False}
    (STAGE/'REVIEW.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in {'files','stage_hashes','installed_before_hashes'}}))


def install():
    proc=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert proc.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in proc.stdout.splitlines()),'Game is running; fixes remain staged'
    report=json.loads((STAGE/'REVIEW.json').read_text());assert report['result']=='PASS'
    assert report['state']=='staged','Package was already installed'
    for rel in report['files']:
        assert digest(STAGE/rel)==report['stage_hashes'][rel]
        assert digest(TARGET/rel)==report['installed_before_hashes'][rel],('Installed file changed; restage',rel)
    backup=HERE/'backups'/('before-names-ai-N1-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    for rel in report['files']:
        (backup/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TARGET/rel,backup/rel)
    shutil.copy2(TARGET/'JAPAN_RISING_BUILD.json',backup/'JAPAN_RISING_BUILD.json')
    for rel in report['files']:shutil.copy2(STAGE/rel,TARGET/rel)
    hashes=json.loads((HERE/'INSTALLED_FILE_HASHES.json').read_text())
    for rel in report['files']:hashes[str(Path(rel))]=digest(TARGET/rel)
    hashes=dict(sorted(hashes.items()));(HERE/'INSTALLED_FILE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    manifest=json.loads((TARGET/'JAPAN_RISING_BUILD.json').read_text())
    manifest.update(model_names_ai_hotfix='L4 N1',fingerprinted_files=len(hashes),
        installed_fingerprint_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
        spec_sha256=(HERE/'SPEC_SHA256.txt').read_text().strip())
    (TARGET/'JAPAN_RISING_BUILD.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='latin1')
    (HERE/'BUILD_HANDOFF.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report.update(state='installed',backup=str(backup));(STAGE/'REVIEW.json').write_text(json.dumps(report,indent=2))
    docs=TARGET/'Japan Rising Documentation'
    for name in ('AUDIT.md','AUDIT.json'):shutil.copy2(HERE/'latest_playtest'/name,docs/('LATEST_'+name))
    shutil.copy2(STAGE/'REVIEW.json',docs/'MODEL_NAMES_AI_N1.json')
    shutil.copy2(HERE/'INSTALLED_FILE_HASHES.json',docs/'INSTALLED_FILE_HASHES.json')
    shutil.copy2(HERE/'BUILD_HANDOFF.json',docs/'BUILD_HANDOFF.json')
    for name in ('EVENT_SPEC.md','events.json'):shutil.copy2(HERE/name,docs/name)
    print(json.dumps({'state':'installed','files':len(report['files']),'save_edits':False,'game_executed':False}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['stage','install']);args=ap.parse_args()
    (stage if args.mode=='stage' else install)()
