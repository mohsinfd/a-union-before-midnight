"""Package successful offline evidence. Never launches a game or grants engine status."""
from datetime import datetime,timezone
import hashlib
import json
import shutil
from build import HERE,TARGET,GAME,VERSION,read,localisation,prepare_catalog


def run():
    from localisation_support import review as localisation_review
    prepare_catalog()
    strings=localisation_review(TARGET,GAME,localisation(),read)
    static=json.loads((HERE/'STATIC_VALIDATION.json').read_text())
    states=json.loads((HERE/'EVENT_STATE_TESTS.json').read_text())
    manifest=json.loads((TARGET/'JAPAN_RISING_BUILD.json').read_text())
    assert static['result']=='PASS' and not static['errors'] and states['passed']
    assert manifest['version']==VERSION
    assert manifest['spec_sha256']==(HERE/'SPEC_SHA256.txt').read_text().strip()
    assert manifest['events']==static['new_event_blocks']
    specialist=json.loads((HERE/'SPECIALIST_REVIEW.json').read_text())
    assert specialist['result']=='PASS' and specialist['version']==VERSION
    readiness=json.loads((HERE/'READINESS_REVIEW.json').read_text())
    assert readiness['result']=='PASS' and readiness['version']==VERSION
    personnel=json.loads((HERE/'PERSONNEL_REVIEW.json').read_text())
    assert personnel['result']=='PASS' and personnel['version']==VERSION
    invasion=json.loads((HERE/'US_INVASION_REVIEW.json').read_text())
    assert invasion['result']=='PASS' and invasion['version']==VERSION
    programmes=json.loads((HERE/'PROGRAMME_REVIEW.json').read_text())
    assert programmes['result']=='PASS' and programmes['version']==VERSION
    migration=json.loads((HERE/'SNLF_JUNE_MIGRATION.json').read_text())
    assert migration['result']=='PASS' and migration['old_event_ids_preserved']==1655
    from pathlib import Path
    assert hashlib.sha256(Path(migration['save']).read_bytes()).hexdigest()==migration['save_sha256']
    patterns=['db/events/japan_rising/*.txt','ai/jx/*.ai','ai/ger_*.ai','ai/ita_*.ai','config/japan_rising.csv','config/models.csv','db/tech/teams/teams_jap.csv','db/tech/teams/teams_U87.csv','db/tech/infantry_tech.txt','scenarios/1933.eug','db/events.txt','db/revolt.txt','db/events/japan.txt','db/events/USA.txt','db/events/UK.txt','db/events/Gameplay.txt','db/events/Add_on.txt','gfx/events_pics/jx_*.bmp','gfx/interface/pics/jx_*.bmp','gfx/interface/models/ill_div_JAP_41_*.bmp','gfx/interface/models/JAP_model_41_*.bmp','gfx/load_1024.bmp','gfx/skins/JAP/fullscreen.bmp']
    from specialist_units import MIRRORS
    patterns+=['db/leaders/japan.csv','db/ministers/ministers_jap.csv','db/ministers/minister_personalities.txt','config/mods.csv']
    patterns += ['db/units/divisions/d_01.txt','db/units/divisions/d_10.txt','db/units/divisions/d_11.txt','db/units/divisions/d_12.txt','db/units/division_types.txt','db/units/modifiers.csv','gfx/map/hoi_counter_strip.bmp','gfx/interface/models/*JAP_50_*.bmp','gfx/interface/models/*JAP_51_*.bmp','gfx/interface/models/*JAP_52_*.bmp','gfx/interface/models/JAP_model_50_*.bmp','gfx/interface/models/JAP_model_51_*.bmp','gfx/interface/models/JAP_model_52_*.bmp']+[f'db/tech/{name}' for name in {p for p,_,_,_ in MIRRORS}]
    patterns+=['scenarios/1933/japan.inc','scenarios/1933/china nationalist.inc','ai/switch/ITA*.ai']
    hashes={str(p.relative_to(TARGET)):hashlib.sha256(p.read_bytes()).hexdigest() for pattern in patterns for p in TARGET.glob(pattern) if p.is_file()}
    hashes=dict(sorted(hashes.items()))
    manifest.update(state='offline-validated-awaiting-user-playtest',validation={'static':static,'event_state_model':states,'readiness_corrections':{k:v for k,v in readiness.items() if k not in {'support_tiers','construction_transactions'}},'personnel':{k:v for k,v in personnel.items() if k not in {'leader_changes','promotions'}},'us_invasion':{k:v for k,v in invasion.items() if k not in {'claims','transfer_requirements'}},'engine_tested':False,'game_launches_delegated_to_user':True,'shortcut_syntax_checked':True},completed_utc=datetime.now(timezone.utc).isoformat(),fingerprinted_files=len(hashes),installed_fingerprint_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest())
    manifest['validation']['engine_loaded_localisation']=strings
    manifest['localisation_hotfix']='L1'
    manifest['completion_hotfix']='L2'
    manifest['programme_hotfix']='L3'
    manifest['snlf_cabinet_hotfix']='L4'
    manifest['display_version']=VERSION+' L4'
    if manifest.get('campaign_balance_hotfix')=='B1':
        b1=json.loads((HERE/'BALANCE_B1_TESTS.json').read_text());assert b1['passed']
        manifest['display_version']+=' N1 B1'
        manifest['validation']['campaign_balance_b1']=b1
    if manifest.get('base_defence_hotfix')=='B2':
        b2=json.loads((HERE/'BASE_DEFENCE_B2_TESTS.json').read_text());assert b2['passed']
        manifest['display_version']+=' B2'
        manifest['validation']['base_defence_b2']=b2
    manifest['validation']['june_snlf_migration']={k:v for k,v in migration.items() if k!='countries'}
    manifest['validation']['production_programmes']={k:v for k,v in programmes.items() if k!='programmes'}
    (HERE/'INSTALLED_FILE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    (HERE/'BUILD_HANDOFF.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (TARGET/'JAPAN_RISING_BUILD.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='latin1')
    docs=TARGET/'Japan Rising Documentation';docs.mkdir(exist_ok=True)
    for name in ['README.md','PROGRESS.md','COMPLETION_AUDIT.md','EVENT_SPEC.md','events.json','early_spec.md','EARLY_HISTORY_SOURCES.md','ART_PROMPTS.md','EARLY_ART_REQUESTS.json','RESOURCE_BALANCE.md','RESOURCE_BALANCE.json','BASELINE_ECONOMY_SAMPLES.json','OFFLINE_REVIEW.md','OFFLINE_REVIEW.json','CONSTRUCTION_BALANCE.md','CONSTRUCTION_BALANCE.json','STATIC_VALIDATION.json','EVENT_STATE_TESTS.json','BUILD_HANDOFF.json','INSTALLED_FILE_HASHES.json']:
        shutil.copy2(HERE/name,docs/name)
    shutil.copy2(HERE/'README.md',TARGET/'README_JAPAN_RISING.md')
    shutil.copy2(HERE/'ACTIVITIES_AND_UNITS.md',docs/'ACTIVITIES_AND_UNITS.md')
    for name in ['MORE_CONTENT_SPEC.md','SPECIALIST_REVIEW.md','SPECIALIST_REVIEW.json','SPECIALIST_ART_REQUESTS.json']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['READINESS_FIXES.md','READINESS_REVIEW.json','COLD_REVIEW_R2_2026-10-31.md']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['PERSONNEL_SPEC.md','PERSONNEL_REVIEW.md','PERSONNEL_REVIEW.json','PERSONNEL_SOURCES.md','PERSONNEL_ART_REQUESTS.json','PERSONNEL_ART_QA.png']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['US_INVASION_REPAIR.md','US_INVASION_REVIEW.json']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['LOCALISATION_FIX.md','LOCALISATION_REVIEW.json']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['COMPLETION_FIX.md','COMPLETION_FIX_INSTALL.json','COMPLETION_SAVE_REPAIR.json']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['PROGRAMME_REVIEW.json','PROGRAMME_SAVE_REPAIR.json','PLAYTEST_1937_AUDIT.json','PLAYTEST_1937_AUDIT.md','PRODUCTION_AND_UI_L3.md']:
        shutil.copy2(HERE/name,docs/name)
    for name in ['SNLF_AND_CABINET_L4.md','SNLF_JUNE_MIGRATION.json','SNLF_ART_REQUEST.json']:
        shutil.copy2(HERE/name,docs/name)
    if manifest.get('campaign_balance_hotfix')=='B1':
        for name in ['BALANCE_B1.md','BALANCE_B1_TESTS.json']:shutil.copy2(HERE/name,docs/name)
        shutil.copy2(HERE/'staged_balance_b1/REVIEW.json',docs/'BALANCE_B1_INSTALL.json')
    if manifest.get('base_defence_hotfix')=='B2':
        for name in ['BASE_DEFENCE_B2.md','BASE_DEFENCE_B2_TESTS.json']:shutil.copy2(HERE/name,docs/name)
        shutil.copy2(HERE/'staged_base_defence_b2/REVIEW.json',docs/'BASE_DEFENCE_B2_INSTALL.json')
    for rel,digest in hashes.items():assert hashlib.sha256((TARGET/rel).read_bytes()).hexdigest()==digest,rel
    print(json.dumps({'version':VERSION,'state':manifest['state'],'events':manifest['events'],'model_tests':states['tests'],'fingerprinted_files':len(hashes),'game_executed':False}))


if __name__=='__main__':run()
