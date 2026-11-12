"""Publish the R13 offline installation receipt. Never starts the game."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageOps
import build
import unique_divisions as divisions
import unique_attachments as attachments
import unique_art


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build.prepare_catalog()
    manifest_path=build.TARGET/'JAPAN_RISING_BUILD.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['version']==build.VERSION=='JX 1.1 ALPHA 2 R13'
    assert manifest['spec_sha256']==(build.HERE/'SPEC_SHA256.txt').read_text().strip()
    assert len(build.EVENTS)==1822
    hashes={}
    # Compare actual loaded model data against source-generated expectations.
    for module,classes,kind in ((divisions,divisions.CLASSES,'divisions'),
                                (attachments,attachments.ATTACHMENTS,'brigades')):
        for unit,info in classes.items():
            path=build.TARGET/'db/units'/kind/(unit+'.txt')
            actual=build.getall(build.parse(build.read(path)),'model')
            assert actual==module.models(unit),(unit,'installed model mismatch')
            hashes[str(path.relative_to(build.TARGET))]=sha(path)
            for model in range(len(actual)):
                if kind=='divisions':
                    names=[f'ill_div_JAP_{info["index"]}_{model}.bmp',f'JAP_model_{info["index"]}_{model}.bmp']
                else:
                    names=[f'ill_bri_JAP_{info["index"]}_{model}.bmp',f'ill_bri_{info["index"]}_{model}.bmp']
                for name in names:
                    card=build.TARGET/'gfx/interface/models'/name
                    with Image.open(card) as image:
                        assert image.size==((67,44) if name.startswith('JAP_model_') else (192,104))
                    hashes[str(card.relative_to(build.TARGET))]=sha(card)
    # Keep a visible contact sheet of the seven locally retained originals.
    preview=Image.new('RGB',(1200,7*228),(21,29,36));draw=ImageDraw.Draw(preview)
    event_hashes=[]
    for i,key in enumerate(unique_art.SOURCES):
        x=(i%2)*600;y=(i//2)*228
        with Image.open(build.HERE/'art'/(key+'.png')) as original:
            preview.paste(ImageOps.contain(original.convert('RGB'),(590,192)),(x+5,y+24))
        draw.text((x+10,y+5),key.replace('unique_','').replace('_',' ').title(),fill='white')
        path=build.TARGET/'gfx/events_pics'/('jx_'+key+'.bmp')
        with Image.open(path) as image:assert image.size==(400,116)
        event_hashes.append(sha(path));hashes[str(path.relative_to(build.TARGET))]=sha(path)
    assert len(event_hashes)==len(set(event_hashes))==13
    preview.save(build.HERE/'R13_ART_PREVIEW.png')
    unique=json.loads((build.HERE/'UNIQUE_UNIT_COLD_AUDIT.json').read_text())
    assert unique['passed'] and unique['tests']>=13
    revision=json.loads((build.HERE/'R13_COLD_AUDIT.json').read_text())
    assert revision['passed'] and revision['tests']==15 and revision['version']==build.VERSION
    result=subprocess.run(['python','validate.py'],cwd=build.HERE,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    validation=json.loads(result.stdout)
    docs=build.TARGET/'Japan Rising Documentation'
    for name in ('README.md','R12_UNIQUE_UNITS.md','UNIQUE_DIVISIONS_AUDIT.md','UNIQUE_DIVISIONS_REVIEW.json',
                 'UNIQUE_ATTACHMENTS.md','UNIQUE_ATTACHMENTS_REVIEW.json','UNIQUE_UNIT_EVENTS.md',
                 'UNIQUE_UNIT_COLD_AUDIT.json','UNIQUE_ART_MANIFEST.json','UNIQUE_ART_INSTALL.json',
                 'R13_ART_PREVIEW.png','MINISTER_INTEGRITY_AUDIT.md','MINISTER_INTEGRITY_REVIEW.json',
                 'EQUIPMENT_DELIVERY_AUDIT.md','EQUIPMENT_DELIVERY_REVIEW.json','PLAYER_COPY_REVIEW.md',
                 'PLAYER_COPY_REVIEW.json','EVENT_ACCESSIBILITY_MATRIX.json',
                 'R12_1_CHANGES.md','R13_COLD_AUDIT.json','FURTHER_JAPANESE_SPECIALISTS.md','PROGRESS.md',
                 'R13_UNITS.md','R13_ART_SOURCES.json'):
        shutil.copy2(build.HERE/name,docs/name)
    receipt=dict(version=build.VERSION,target=str(build.TARGET),state='installed-offline-validated',
                 game_launched=False,launcher_executed=False,save_edits=False,germany_overhaul_edits=False,
                 all_events=1822,preserved_R11_1_ids=1773,preserved_R12_1_ids=1802,new_events=20,
                 division_models=29,attachment_models=12,free_introductions=10,
                 free_formations=7,free_attachments=6,unique_original_illustrations=13,
                 division_checks=7,attachment_tests=10,integrated_unique_unit_tests=unique,
                 revision_cold_audit=revision,island_garrisons_retained=31,
                 one_time_island_shipping={'transports':180,'escorts':90},
                 paid_merchant_choices=[{'transports':160,'escorts':40},{'transports':100,'escorts':80}],
                 regression_cases=99,native_contract_cases=12,prewar_cases=10,regional_cases=12,
                 us_campaign_cases=11,copy_checks=7,minister_checks=8,accessibility_cases=8,
                 equipment_checks=8,equipment_installed_matches=True,static_validation=validation,
                 installed_models_and_art_hashes=hashes,
                 qualification='Offline documented-command and actual installed-file checks. No engine execution; deployment UI, airborne missions, naval conversion queues and campaign balance need the player playtest.')
    def publish():
        (build.HERE/'R13_INSTALL_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        shutil.copy2(build.HERE/'R13_INSTALL_RECEIPT.json',docs/'R13_INSTALL_RECEIPT.json')
    publish()
    manifest.update(state=receipt['state'],validation_receipt='Japan Rising Documentation/R13_INSTALL_RECEIPT.json')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    result=subprocess.run(['python','FINAL_INSTALL_review.py'],cwd=build.HERE,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    final=json.loads((build.HERE/'FINAL_INSTALL_REVIEW.json').read_text())
    receipt['installation_verified']={key:final[key] for key in ('selected_mod','registered_modules','loaded_english_matches','shortcut','powershell_syntax')}
    publish()
    shutil.copy2(build.HERE/'FINAL_INSTALL_REVIEW.json',docs/'FINAL_INSTALL_REVIEW.json')
    print(json.dumps({k:receipt[k] for k in ('version','target','state','all_events','free_formations','free_attachments','installation_verified')},indent=2))


if __name__=='__main__':main()
