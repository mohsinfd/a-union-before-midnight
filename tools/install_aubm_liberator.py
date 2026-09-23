#!/usr/bin/env python3
"""Install only LIBERATOR2's three event modules into the active local prototype.

No game process is controlled. Saves, visuals, scenario, launcher selection and
the separate normal installation are protected. Every replaced file is backed up.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from aubm_menu_safety import event_spans
import generate_aubm_liberator as lib
import aubm_liberator_v2 as v2
from generate_aubm_bespoke_route_arcs import render as render_routes

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game')
TARGET = GAME / 'Mods/AUBM Terrain Prototype P1'
FILES = ('db/events/aubm_v4/43_wartime_settlements.txt', 'db/events/aubm_v4/51_bespoke_route_arcs.txt', 'db/events/aubm_v4/45_enemy_campaigns.txt')
ROUTE_IDS = {9289667,9289671,9289675,9289679}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_closed():
    proc = subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    if any(line.lower().startswith('"darkest') for line in proc.stdout.splitlines()):
        raise RuntimeError('Exit Darkest Hour yourself before installation. Nothing was changed or closed.')


def protected():
    paths = [GAME/'settings.cfg']
    for root in (TARGET, GAME/'Mods/A Union Before Midnight V4.2'):
        paths += [p for p in (root/'scenarios').rglob('*') if p.is_file()]
        for rel in ('db/country.csv','map/Map_1/colorscales.csv',
                    'gfx/map/airfield.bmp','gfx/map/harbour.bmp',
                    'gfx/load_1024.bmp','gfx/interface/frontend/bg_start.bmp',
                    *(f'map/Map_1/lightmap{i}.tbl' for i in range(1,5))):
            if (root/rel).exists(): paths.append(root/rel)
        if root != TARGET:
            paths += [root/r for r in FILES]
    return {str(p):sha(p) for p in paths if p.is_file()}


def blocks(raw):
    text=raw.decode('cp1252').replace('\r\n','\n')
    return {i:text[s:e] for s,e,i in event_spans(text)}


def verify_map_contract():
    revolt='\n'.join(line.split('#',1)[0] for line in (TARGET/'db/revolt.txt').read_text(encoding='cp1252').splitlines())
    for r in lib.REGIONS:
        match=re.search(rf'(?ms)^\s*{r.tag}\s*=\s*\{{.*?\bminimum\s*=\s*\{{([^}}]+)\}}',revolt)
        if not match or set(map(int,re.findall(r'\d+',match.group(1)))) != set(r.minimum):
            raise ValueError(f'The installed {r.tag} release definition differs from the tested contract')
    for tag,minimum in v2.CA_MIN.items():
        match=re.search(rf'(?ms)^\s*{tag}\s*=\s*\{{.*?\bminimum\s*=\s*\{{([^}}]+)\}}',revolt)
        if not match or set(map(int,re.findall(r'\d+',match.group(1)))) != set(minimum):
            raise ValueError(f'The installed {tag} release definition differs from the tested contract')
    names={}
    for line in (TARGET/'map/Map_1/province_names.csv').read_text(encoding='cp1252').splitlines():
        cells=line.split(';')
        if len(cells)>1 and re.fullmatch(r'PROV\d+',cells[0]): names[int(cells[0][4:])]=cells[1]
    for province,name in {900:'Suez',791:'Port Said',783:'El Alamein',789:'Alexandria',787:'Cairo',1337:'Nanjing',1338:'Shanghai',1317:'Wuhan',1299:'Chongqing',713:'Baku',1103:'Tashkent',706:'Astrakhan',663:'Stalingrad',1151:'Sverdlovsk',1138:'Omsk',572:'Moscow',1552:'Tokyo',1553:'Osaka',1554:'Hiroshima',1459:'Delhi',1517:'Bombay',1447:'Calcutta',1289:'Lhasa',1085:'Teheran',2171:'Kabul'}.items():
        if names.get(province)!=name: raise ValueError(f'Wrong map layout for {name}')


def install(expected_save_sha):
    assert_closed()
    verify_map_contract()
    save=TARGET/'scenarios/save games/autosave.eug'
    if sha(save) != expected_save_sha:
        raise ValueError('The autosave changed after review; inspect the new save before deploying.')
    # Save names can contain undefined CP1252 bytes; only ASCII file references
    # are needed here. Never decode/re-encode or repair unrelated save contents.
    text=save.read_bytes().replace(b'\\',b'/')
    if not all(rel.encode('ascii') in text for rel in FILES):
        raise ValueError('This save does not load all three existing modules; do not edit it automatically.')
    source={r:(lib.ROOT/'mod'/r).read_bytes() for r in FILES}
    prior={r:(TARGET/r).read_bytes() for r in FILES}
    if source[FILES[0]] != lib.apply_to_bytes(source[FILES[0]]):
        raise ValueError('Liberator source is stale')
    if source[FILES[1]].decode('ascii').replace('\r\n','\n') != render_routes():
        raise ValueError('Route source is stale')
    base = source[FILES[0]].split(lib.MARKER.encode('ascii'))[0]
    prior_base = prior[FILES[0]].split(lib.MARKER.encode('ascii'))[0]
    if base.rstrip() != v2.patch_legacy(prior_base).rstrip():
        raise ValueError('Unrelated differences in the installed settlement module')
    old45,new45=blocks(prior[FILES[2]]),blocks(source[FILES[2]])
    changed45={i for i in old45.keys()|new45.keys() if old45.get(i)!=new45.get(i)}
    if not changed45 <= {9282150}:
        raise ValueError(f'Unexpected major-campaign changes: {sorted(changed45)}')
    old,new=blocks(prior[FILES[1]]),blocks(source[FILES[1]])
    changed={i for i in old.keys()|new.keys() if old.get(i)!=new.get(i)}
    if not changed <= ROUTE_IDS:
        raise ValueError(f'Unexpected route changes: {sorted(changed-ROUTE_IDS)}')
    before=protected()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=lib.ROOT/'tmp'/f'liberator2-install-{stamp}'
    backup.mkdir(exist_ok=False)
    for rel in FILES:
        copy=backup/rel; copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(TARGET/rel,copy)
        if sha(copy)!=sha(TARGET/rel): raise ValueError('Backup hash mismatch')
    for p in (save,save.with_name('autosave.eug.cfg')):
        if p.exists(): shutil.copy2(p,backup/p.name)
    old_receipt=TARGET/'LIBERATOR2.json'
    if old_receipt.exists(): shutil.copy2(old_receipt,backup/'previous-receipt.json')
    receipt={'build':'LIBERATOR2','base':'Alpha 27 / HYBRID-WORLD1 / MENU-SAFETY1',
             'installed_utc':stamp,'target':str(TARGET),'backup':str(backup),
             'save_sha256':expected_save_sha,'save_modified':False,'game_launched':False,
             'engine_playtested':False,'changed_existing_route_ids':sorted(changed),
             'changed_existing_settlement_ids':sorted(v2.LEGACY_IDS),
             'changed_existing_major_ids':sorted(changed45),
             'new_event_ids':[i for _,_,i in event_spans(lib.render())],
             'files':{},'protected_before':before}
    assert_closed()
    try:
        for rel in FILES:
            shutil.copy2(lib.ROOT/'mod'/rel,TARGET/rel)
            receipt['files'][rel]={'before':hashlib.sha256(prior[rel]).hexdigest(),'after':sha(TARGET/rel)}
            if sha(TARGET/rel)!=hashlib.sha256(source[rel]).hexdigest(): raise ValueError('Deployment hash mismatch')
        after=protected()
        if before != after: raise ValueError('Protected files changed during installation')
    except Exception:
        for rel in FILES: shutil.copy2(backup/rel,TARGET/rel)
        raise
    receipt['protected_unchanged']=True
    serialized=json.dumps(receipt,indent=2)+'\n'
    (backup/'receipt.json').write_text(serialized,encoding='utf-8')
    old_receipt.write_text(serialized,encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='protected_before'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--expected-save-sha',required=True)
    args=parser.parse_args()
    install(args.expected_save_sha)
