"""Correct the confirmed DH load error without changing any save or event effect."""
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from generate_aubm_liberator import ROOT, OUTPUT, apply_to_bytes
from install_aubm_liberator import GAME, TARGET, assert_closed, protected, sha
from validate_v4 import invalid_event_action_keys

REL='db/events/aubm_v4/43_wartime_settlements.txt'


def main():
    assert_closed()
    installed=TARGET/REL
    old=installed.read_bytes();new=OUTPUT.read_bytes()
    main_receipt=TARGET/'LIBERATOR3.json'
    receipt=json.loads(main_receipt.read_text(encoding='utf-8'))
    if hashlib.sha256(old).hexdigest()!=receipt['files'][REL]['after']:
        raise ValueError('Installed event file differs from its receipt; preserve and review')
    # This operation may change only the invalid button-key tokens. No event
    # IDs, text, gates, commands, effects or option order may change.
    expected,count=re.subn(rb'(?m)^(\s*)action_[e-z](\s*=\s*\{)',rb'\1action\2',old)
    if not count:raise ValueError('No invalid labels found; inspect the current installation')
    if expected!=new:raise ValueError('Source has changes beyond the diagnosed syntax repair')
    if new!=apply_to_bytes(new):raise ValueError('Generated source is stale')
    if invalid_event_action_keys(new.decode('cp1252')):raise ValueError('Unsupported action labels remain')
    before=protected()
    for root in (TARGET,GAME/'Mods/A Union Before Midnight V4.2'):
        for rel in ('db/leaders/india.csv','ai/aubm/japan/JAP_india_rupture.ai'):
            p=root/rel
            if p.exists():before[str(p)]=sha(p)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'tmp'/f'liberator3-hotfix1-{stamp}';backup.mkdir(exist_ok=False)
    shutil.copy2(installed,backup/'43_wartime_settlements.txt')
    shutil.copy2(main_receipt,backup/'LIBERATOR3.before.json')
    shutil.copy2(GAME/'savedebug.txt',backup/'savedebug-crash.txt')
    if (backup/'43_wartime_settlements.txt').read_bytes()!=old:raise ValueError('Backup mismatch')
    assert_closed()
    if installed.read_bytes()!=old:raise ValueError('Installed file changed during preflight')
    try:
        shutil.copy2(OUTPUT,installed)
        if installed.read_bytes()!=new:raise ValueError('Deployment mismatch')
        if any(sha(Path(p))!=h for p,h in before.items()):raise ValueError('Protected file changed')
    except Exception:
        shutil.copy2(backup/'43_wartime_settlements.txt',installed)
        raise
    result={'hotfix':'LIBERATOR3-HOTFIX1','installed_utc':stamp,'target':str(installed),
        'backup':str(backup),'invalid_action_keys_replaced':count,
        'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':sha(installed),
        'only_button_key_tokens_changed':True,'all_saves_unchanged':True,
        'protected_files_verified':len(before),'game_launched':False,'engine_retest_performed':False,
        'diagnosis':"savedebug.txt: unknown lhs in game-event: action_e, line 20060"}
    (backup/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (TARGET/'LIBERATOR3-HOTFIX1.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    receipt['files'][REL]['after']=result['after_sha256']
    receipt.setdefault('hotfixes',[]).append(result)
    main_receipt.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
