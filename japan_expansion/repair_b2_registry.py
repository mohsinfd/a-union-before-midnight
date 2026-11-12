"""Repair only B2's saved event-file registry, with byte-preserving backup."""
import hashlib,json,os,shutil,subprocess
from datetime import datetime
from pathlib import Path
from build import HERE,TARGET,read,parse,get,getall
from save_event_registry import ensure_modules,queued_jx_missing

def sha(raw):return hashlib.sha256(raw).hexdigest()

def run():
    p=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    assert p.returncode==0 and not any(l.lower().startswith('"darkest hour.exe"') for l in p.stdout.splitlines()),'Game is still running; save not touched'
    save=TARGET/'scenarios/save games/JAPAN_B2_1941_December_15.eug'
    raw=save.read_bytes();text=raw.decode('latin1')
    fixed,added=ensure_modules(text,read(TARGET/'db/events.txt'))
    assert added==['db\\events\\japan_rising\\snlf_cabinet.txt','db\\events\\japan_rising\\campaign_balance.txt'],added
    assert fixed.startswith(text),'Only append registry entries; never rewrite campaign data'
    missing_before=queued_jx_missing(text,TARGET);assert len(missing_before)==6,missing_before
    assert queued_jx_missing(fixed,TARGET)==[]
    warnings=[];before=parse(text,warnings);after=parse(fixed,warnings);assert not warnings
    assert [(k,v) for k,v in before if k!='event']==[(k,v) for k,v in after if k!='event']
    assert getall(after,'event')==getall(before,'event')+added
    assert ensure_modules(fixed,read(TARGET/'db/events.txt'))==(fixed,[])
    queue_before=get(get(before,'globaldata'),'queued_events')
    assert queue_before==get(get(after,'globaldata'),'queued_events')
    backup=HERE/'backups'/('before-B2-event-registry-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True);shutil.copy2(save,backup/save.name)
    cfg=save.with_suffix('.eug.cfg')
    if cfg.exists():shutil.copy2(cfg,backup/cfg.name)
    out=fixed.encode('latin1');temp=save.with_suffix('.eug.registry-tmp')
    assert not temp.exists();temp.write_bytes(out)
    assert save.read_bytes()==raw
    os.replace(temp,save)
    stage=HERE/'staged_base_defence_b2';receipt=json.loads((stage/'REVIEW.json').read_text())
    shutil.copy2(stage/save.name,backup/('staged_'+save.name))
    (stage/save.name).write_bytes(out)
    receipt['output_sha256_before_registry_repair']=receipt['output_sha256']
    receipt['output_sha256']=sha(out)
    receipt['save_event_registry_repair']={'added':added,'backup':str(backup),'game_executed':False}
    (stage/'REVIEW.json').write_text(json.dumps(receipt,indent=2))
    report={'result':'PASS','save':str(save),'backup':str(backup),'before_sha256':sha(raw),'after_sha256':sha(out),
      'added_event_files':added,'previously_unresolved_queued_event_ids':missing_before,
      'unresolved_queued_event_ids_after':[],'all_non_registry_campaign_data_identical':True,
      'existing_queue_and_delays_unchanged':True,'idempotence_check_passed':True,'game_executed':False}
    assert sha(save.read_bytes())==report['after_sha256']
    (HERE/'B2_EVENT_REGISTRY_REPAIR.json').write_text(json.dumps(report,indent=2))
    docs=TARGET/'Japan Rising Documentation'
    shutil.copy2(HERE/'B2_EVENT_REGISTRY_REPAIR.json',docs/'B2_EVENT_REGISTRY_REPAIR.json')
    shutil.copy2(stage/'REVIEW.json',docs/'BASE_DEFENCE_B2_INSTALL.json')
    print(json.dumps(report))

if __name__=='__main__':run()
