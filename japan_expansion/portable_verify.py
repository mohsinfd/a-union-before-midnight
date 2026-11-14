"""Verify and publish a local install without historical snapshots or game execution."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image
import build as b
import unique_divisions as d
import unique_attachments as a


def verify():
    b.prepare_catalog();target=b.TARGET
    manifest_path=target/'JAPAN_RISING_BUILD.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['version']==b.VERSION and Path(manifest['target']).resolve()==target.resolve()
    assert manifest['spec_sha256']==(b.HERE/'SPEC_SHA256.txt').read_text().strip()
    assert target.resolve()!=b.SOURCE.resolve()
    groups={e.module for e in b.EVENTS};index=b.read(target/'db/events.txt')
    actual={}
    for group in groups:
        assert index.count('event = "db\\events\\japan_rising\\'+group+'.txt"')==1
        for event in b.getall(b.parse(b.read(target/'db/events/japan_rising'/(group+'.txt'))),'event'):
            identity=b.get(event,'id');assert identity not in actual;actual[identity]=event
    assert len(actual)==len(b.EVENTS)
    for event in b.EVENTS:assert actual[str(event.id)]==b.get(b.parse(b.compiled_event(event)),'event'),event.key
    expected={r.split(';')[0]:r.split(';')[1] for r in b.localisation().splitlines() if ';' in r and not r.startswith('#')}
    loaded={r.split(';')[0]:r.split(';')[1] for r in b.read(target/'config/mods.csv').splitlines() if ';' in r and not r.startswith('#')}
    assert all(loaded.get(key)==value for key,value in expected.items())
    hashes={}
    for module,entries,folder in ((d,d.CLASSES,'divisions'),(a,a.ATTACHMENTS,'brigades')):
        for unit,info in entries.items():
            path=target/'db/units'/folder/(unit+'.txt')
            assert b.getall(b.parse(b.read(path)),'model')==module.models(unit),unit
            hashes[str(path.relative_to(target))]=hashlib.sha256(path.read_bytes()).hexdigest()
            for model in range(len(info['years'])):
                prefix='div' if folder=='divisions' else 'bri'
                path=target/'gfx/interface/models'/f'ill_{prefix}_JAP_{info["index"]}_{model}.bmp'
                with Image.open(path) as picture:assert picture.size==(192,104)
    with Image.open(target/'gfx/map/hoi_counter_strip.bmp') as image:assert image.size==((53+len(d.CLASSES))*32,34)
    reports={}
    for filename in ('UNIQUE_UNIT_COLD_AUDIT.json','ENEMY_TRANSPORT_AI_AUDIT.json','R14_COLD_AUDIT.json','R15_COLD_AUDIT.json'):
        report=json.loads((b.HERE/filename).read_text());assert report['passed'],filename
        reports[filename]=report
    docs=target/'Japan Rising Documentation';docs.mkdir(exist_ok=True)
    for filename in ('README.md','R13_UNITS.md','R13_1_CHANGES.md','ENEMY_TRANSPORT_AI_REPORT.json',
                     'ENEMY_TRANSPORT_AI_AUDIT.json','UNIQUE_UNIT_COLD_AUDIT.json','PLAYER_COPY_REVIEW.json',
                     'PROGRESS.md','R14_CHANGES.md','R14_CHINA.md','R14_PEACE.md','R14_AFTERWAR.md',
                     'R14_CONSTRUCTION_AUDIT.md','R14_CONSTRUCTION_AUDIT.json','R14_BALANCE_AUDIT.json',
                     'R14_COLD_AUDIT.json','R14_REGRESSION_RESULTS.json','R14_1_PRESTART_REVIEW.md',
                     'R15_README.md','R15_ENEMY.md','R15_RECOVERY.md','R15_STRATEGY.md',
                     'R15_COLD_AUDIT.json','R15_COST_AUDIT.json','R15_COST_AUDIT.md'):
        shutil.copy2(b.HERE/filename,docs/filename)
    receipt=dict(version=b.VERSION,target=str(target),state='installed-offline-validated',
                 events=len(b.EVENTS),modules=len(groups),loaded_english_matches=len(expected),
                 game_launched=False,save_edits=False,source_path=str(b.SOURCE),
                 installed_model_hashes=hashes,fresh_offline_checks=reports,
                 qualification='Source/event/model/localisation/art parity and fresh documented-command tests; no running-engine or long-campaign guarantee.')
    (b.HERE/'R15_INSTALL_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.copy2(b.HERE/'R15_INSTALL_RECEIPT.json',docs/'R15_INSTALL_RECEIPT.json')
    manifest.update(state=receipt['state'],validation_receipt='Japan Rising Documentation/R15_INSTALL_RECEIPT.json')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('version','target','state','events','modules','loaded_english_matches')},indent=2))


if __name__=='__main__':verify()
