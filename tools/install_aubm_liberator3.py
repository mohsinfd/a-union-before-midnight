"""Scoped LIBERATOR3 deployment and separately named, lossless save repair.

Refuses a running game, a changed autosave, an unknown installed baseline or an
existing destination save. Originals are backed up and never overwritten.
"""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import generate_aubm_liberator as lib
import aubm_liberator_v2 as v2
import aubm_command_reserve as reserve
from aubm_menu_safety import event_spans
from dh_save_spans import Node, parse, replace, walk
from install_aubm_liberator import GAME, TARGET, assert_closed, protected, sha

FILES=('db/events/aubm_v4/43_wartime_settlements.txt',
       'ai/aubm/japan/JAP_india_rupture.ai','db/leaders/india.csv')
RECEIPT='LIBERATOR3.json'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def ai_edits(raw,old,new):
    """Merge only fields explicitly present in the approved cleanup fragment.

Empty arrays explicitly clear the old restriction list. Other AI fields (unit
production, research, diplomacy timers, etc.) remain byte-identical.
"""
    edits=[]
    for f in new.fields:
        prior=next((o for o in old.fields if o.key==f.key),None)
        if prior is None:
            text=render_field(f)
            edits.append((old.end-1,old.end-1,('\n\t\t'+text+'\n\t').encode('ascii')))
        elif isinstance(f.value,Node) and isinstance(prior.value,Node) and f.value.fields and all(x.key is not None for x in f.value.fields):
            edits+=ai_edits(raw,prior.value,f.value)
        else:
            edits.append((prior.value_start,prior.end,render_value(f.value).encode('ascii')))
    return edits


def render_value(value):
    if isinstance(value,Node):return '{ '+' '.join(render_field(f) for f in value.fields)+' }'
    return '"'+value+'"' if any(c.isspace() for c in value) else value


def render_field(f):return (f.key+' = ' if f.key else '')+render_value(f.value)


def coalesce_insertions(edits):
    result={}
    for start,end,value in edits:
        key=(start,end)
        if key in result:
            if start!=end:raise ValueError('Duplicate replacement span')
            result[key]+=value
        else:result[key]=value
    return [(s,e,v) for (s,e),v in result.items()]


def migrate(raw,destination_name,ai_fragment):
    tree=parse(raw)
    countries={c.get('tag'):c for c in tree.all('country')}
    india,japan=countries['IND'],countries['JAP']
    year=int(tree.get('header').get('startdate').get('year'))
    refs=[str(v).replace('\\','/') for v in tree.all('event')]
    if FILES[0] not in refs:raise ValueError('Save does not load the settlement module')
    flags=tree.get('globaldata').get('flags')
    if flags.get('ind_aubm_jp_rupture')!='1' or flags.get('ind_aubm_jp_partnership')=='1':
        raise ValueError('Save is not the reviewed broken-partnership route')
    pool={int(n.get('id').get('id')) for n in walk(tree)
          if isinstance(n.get('id'),Node) and n.get('id').get('type')=='6'}
    rows=reserve.reserve_rows();newids={int(r[1]) for r in rows}
    if pool&newids:raise ValueError('Reserved leader IDs already exist; do not duplicate a repaired save')
    ai=japan.get('ai')
    # Verify the specific stale profile, not an arbitrary current Japanese AI.
    for section,key,value in (('befriend','IND','200'),('protect','IND','150'),('combat','IND','-1')):
        if ai.get(section).get(key)!=value:raise ValueError('Japan AI differs from the reviewed senior-partner profile')
    nl='\r\n' if b'\r\n' in raw else '\n'
    leaders=''.join(reserve.save_block(r,year,nl) for r in rows).encode('ascii')
    edits=[(india.end-1,india.end-1,leaders)]
    edits+=ai_edits(raw,ai,parse(ai_fragment))
    option=tree.get('header').field('optionfile')
    edits.append((option.value_start,option.end,
        ('"scenarios\\save games\\'+destination_name+'.cfg"').encode('ascii')))
    title=tree.get('header').field('name')
    edits.append((title.value_start,title.end,('"LIBERATOR3 - '+destination_name.removesuffix('.eug')+'"').encode('ascii')))
    edits=coalesce_insertions(edits)
    patched=replace(raw,edits)
    check=parse(patched)
    cs={c.get('tag'):c for c in check.all('country')}
    inserted=[n for n in cs['IND'].all('leader') if int(n.get('id').get('id')) in newids]
    if len(inserted)!=len(rows):raise ValueError('New leader count mismatch')
    if patched[cs['IND'].start:cs['IND'].end].replace(leaders,b'',1)!=raw[india.start:india.end]:
        raise ValueError('An original Indian state byte changed')
    for tag,c in countries.items():
        if tag in ('IND','JAP'):continue
        if raw[c.start:c.end]!=patched[cs[tag].start:cs[tag].end]:raise ValueError('Unrelated country changed: '+tag)
    old_global=tree.get('globaldata');new_global=check.get('globaldata')
    if raw[old_global.start:old_global.end]!=patched[new_global.start:new_global.end]:
        raise ValueError('War, alliance, flag or global history changed')
    # Every byte outside the declared edits must reconstruct the exact source.
    reverse=[];shift=0
    for start,end,value in sorted(edits):
        reverse.append((start+shift,start+shift+len(value),raw[start:end]))
        shift+=len(value)-(end-start)
    if replace(patched,reverse)!=raw:raise ValueError('Lossless edit roundtrip failed')
    return patched,{'source_sha256':digest(raw),'repaired_sha256':digest(patched),
        'added_leaders':len(rows),'added_by_branch':{str(b):sum(int(r[13])==b for r in rows) for b in range(3)},
        'available_reserve_now':{str(b):sum(int(r[13])==b and int(r[15])<=year for r in rows) for b in range(3)},
        'future_reserve':sum(int(r[15])>year for r in rows),
        'existing_indian_state_byte_identical':True,'other_countries_byte_identical':True,
        'global_wars_alliances_flags_byte_identical':True,'lossless_roundtrip':True,
        'changed_scopes':['New unassigned Indian leaders','Japan obsolete partnership AI fields','Save display title and companion-settings filename'],
        'byte_edits':len(edits)}


def verify_source(prior,source):
    receipt=json.loads((TARGET/'LIBERATOR2.json').read_text(encoding='utf-8'))
    expected=receipt['files'][FILES[0]]['after']
    if digest(prior[FILES[0]])!=expected:
        raise ValueError('Installed LIBERATOR2 module differs from its verified receipt; preserve and review')
    if source[FILES[0]]!=lib.apply_to_bytes(source[FILES[0]]):raise ValueError('Stale generated events')
    prefix=source[FILES[0]].split(lib.MARKER.encode())[0]
    prior_prefix=prior[FILES[0]].split(lib.MARKER.encode())[0]
    if prefix.rstrip()!=v2.patch_legacy(prior_prefix).rstrip():raise ValueError('Unrelated settlement prefix changed')
    if reserve.existing_prefix(source[FILES[2]])!=prior[FILES[2]]:
        raise ValueError('Original leader roster changed; cannot deploy append-only reserve')
    if source[FILES[2]]!=reserve.apply_to_bytes(source[FILES[2]]):raise ValueError('Stale commander reserve')
    generated_ids={i for _,_,i in event_spans(source[FILES[0]].decode('cp1252'))}
    for p in (TARGET/'db/events').rglob('*.txt'):
        if p==TARGET/FILES[0]:continue
        ids={i for _,_,i in event_spans(p.read_text(encoding='cp1252',errors='replace'))}
        if ids&generated_ids:raise ValueError(f'Installed event ID collision in {p}: {sorted(ids&generated_ids)}')
    # All IDs must be unique in the *installed* merged database, not just India.
    newids={r[1] for r in reserve.reserve_rows()}
    for p in (TARGET/'db/leaders').glob('*.csv'):
        for line in p.read_text(encoding='cp1252',errors='replace').splitlines():
            cells=line.split(';')
            if len(cells)>1 and cells[1] in newids:raise ValueError('Leader ID collision: '+str(p))
    # Bundled parser spellings and anonymous portrait must actually exist.
    binary=(GAME/'Darkest Hour.exe').read_bytes()
    for trait in reserve.TRAITS.values():
        if (trait+'\0').encode() not in binary:raise ValueError('Unsupported save trait: '+trait)
    if not any((r/'gfx/interface/pics/unknown.bmp').is_file() for r in (TARGET,GAME)):
        raise ValueError('Missing stock anonymous leader portrait')


def install(expected_save_sha,expected_ai_sha):
    assert_closed()
    save=TARGET/'scenarios/save games/autosave.eug'
    raw=save.read_bytes()
    if digest(raw)!=expected_save_sha:raise ValueError('Autosave changed: review before deployment')
    prior={r:(TARGET/r).read_bytes() for r in FILES}
    source={r:(lib.ROOT/'mod'/r).read_bytes() for r in FILES}
    if digest(prior[FILES[1]])!=expected_ai_sha:raise ValueError('Installed AI fragment changed')
    verify_source(prior,source)
    date=parse(raw).get('header').get('startdate')
    months='january february march april may june july august september october november december'.split()
    name=f'LIBERATOR3_India_{date.get("year")}-{months.index(date.get("month"))+1:02d}-{int(date.get("day"))+1:02d}.eug'
    target_save=save.with_name(name);target_cfg=save.with_name(name+'.cfg')
    if target_save.exists() or target_cfg.exists() or (TARGET/RECEIPT).exists():
        raise ValueError('LIBERATOR3 destination already exists; inspect instead of overwriting it')
    patched,details=migrate(raw,name,source[FILES[1]])
    cfg=save.with_name('autosave.eug.cfg').read_bytes()
    before=protected()
    # Protect the separate normal installation's equivalent files as well.
    normal=GAME/'Mods/A Union Before Midnight V4.2'
    for rel in FILES:
        if (normal/rel).exists():before[str(normal/rel)]=sha(normal/rel)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=lib.ROOT/'tmp'/f'liberator3-install-{stamp}';backup.mkdir(exist_ok=False)
    for rel in FILES:
        p=backup/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TARGET/rel,p)
        if p.read_bytes()!=prior[rel]:raise ValueError('Backup verification failed')
    shutil.copy2(save,backup/'autosave.eug');shutil.copy2(save.with_name('autosave.eug.cfg'),backup/'autosave.eug.cfg')
    assert_closed()
    if sha(save)!=expected_save_sha:raise ValueError('Save changed during preflight; nothing deployed')
    created=[]
    try:
        for rel in FILES:
            shutil.copy2(lib.ROOT/'mod'/rel,TARGET/rel)
            if (TARGET/rel).read_bytes()!=source[rel]:raise ValueError('Installed file hash mismatch')
        for path,content in ((target_cfg,cfg),(target_save,patched)):
            with path.open('xb') as f:f.write(content)
            created.append(path)
            if path.read_bytes()!=content:raise ValueError('Save-copy verification failed')
        if any(sha(Path(p))!=h for p,h in before.items()):raise ValueError('Protected file changed')
    except Exception:
        for rel in FILES:shutil.copy2(backup/rel,TARGET/rel)
        # Only exact newly created output files; keep failed artifacts in backup.
        for p in created:shutil.move(str(p),str(backup/('failed-'+p.name)))
        raise
    receipt={'build':'LIBERATOR3 / COMMAND-RESERVE1','installed_utc':stamp,
        'target':str(TARGET),'backup':str(backup),'source_save':str(save),
        'repaired_save':str(target_save),'original_save_unchanged':sha(save)==expected_save_sha,
        'normal_install_unchanged':True,'game_launched':False,'engine_playtested':False,
        'files':{r:{'before':digest(prior[r]),'after':sha(TARGET/r)} for r in FILES},
        'migration':details,'protected_files_verified':len(before)}
    data=json.dumps(receipt,indent=2)+'\n'
    (backup/'receipt.json').write_text(data,encoding='utf-8')
    (TARGET/RECEIPT).write_text(data,encoding='utf-8')
    print(data)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--expected-save-sha',required=True);p.add_argument('--expected-ai-sha',required=True)
    args=p.parse_args();install(args.expected_save_sha,args.expected_ai_sha)
