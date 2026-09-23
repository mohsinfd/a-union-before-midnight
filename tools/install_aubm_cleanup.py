"""Install the compiled CLEANUP1 playtest overlay with verified backups.

Does not launch/stop the game or overwrite an autosave. A separate save copy
updates only reserve portrait references and its menu title/options path.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import shutil
from install_aubm_liberator import TARGET,assert_closed,protected,sha
from build_aubm_cleanup import ROOT,OUTPUT
from aubm_reserve_portraits import roster,migrate_pictures
from dh_save_spans import parse,replace
from stamp_aubm_visible_version import write_badge,badge_matches


def prepare_identity(target):
    for rel in ('gfx/load_1024.bmp','gfx/interface/frontend/bg_start.bmp'):
        dest=OUTPUT/'mod'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target/rel,dest);write_badge(dest,'27-CLEANUP1-B1')
        assert badge_matches(dest,'27-CLEANUP1-B1')


def copy_save(raw,name):
    _,mapping=roster((ROOT/'mod/db/leaders/india.csv').read_bytes())
    updated,count=migrate_pictures(raw,mapping)
    tree=parse(updated);header=tree.get('header')
    fields=[(header.field('name'),'CLEANUP1 - India 1942-02-01'),
            (header.field('optionfile'),'scenarios\\save games\\'+name+'.cfg')]
    edits=[(f.value_start,f.end,('"'+v+'"').encode('ascii')) for f,v in fields]
    result=replace(updated,edits)
    old,new=parse(raw),parse(result)
    # Independent invariants: no wars/alliances/flags/history or non-Indian
    # country bytes, and no Indian fields other than reserve picture values.
    for key in ('globaldata','history','sleepevent'):
        a,b=old.get(key),new.get(key)
        if a is not None and hasattr(a,'start'):
            assert raw[a.start:a.end]==result[b.start:b.end],key
    oldcountries={c.get('tag'):c for c in old.all('country')}
    newcountries={c.get('tag'):c for c in new.all('country')}
    for tag,a in oldcountries.items():
        if tag=='IND':continue
        b=newcountries[tag]
        assert raw[a.start:a.end]==result[b.start:b.end],tag
    # Reversal is exact: strip only the specified picture replacements from
    # the changed Indian block using the original ID->picture map.
    def pictures(node):
        from dh_save_spans import Node,walk
        return {int(n.get('id').get('id')):n.get('picture') for n in walk(node)
                if isinstance(n.get('id'),Node) and n.get('id').get('type')=='6' and n.get('picture')}
    originals=pictures(oldcountries['IND'])
    restored,_=migrate_pictures(result,{i:p for i,p in originals.items() if i in mapping})
    back=parse(restored);a=oldcountries['IND'];b=next(c for c in back.all('country') if c.get('tag')=='IND')
    assert raw[a.start:a.end]==restored[b.start:b.end],'Indian state outside portraits changed'
    return result,count


def install(target,with_save):
    assert_closed()
    manifest=json.loads((OUTPUT/'manifest.json').read_text(encoding='utf8'))
    for rel,record in manifest['files'].items():
        src=target/rel if record.get('origin')=='installed' else ROOT/'mod'/rel
        assert sha(src)==record['source'],f'Source changed since compilation: {rel}'
        assert sha(OUTPUT/'mod'/rel)==record['compiled'],f'Compiled file changed: {rel}'
    assert (OUTPUT/'validation.json').is_file(),'Run validate_aubm_cleanup.py first'
    validation=json.loads((OUTPUT/'validation.json').read_text())
    assert validation['manifest_sha256']==sha(OUTPUT/'manifest.json'),'Validation is stale'
    for rel,digest in validation['payload_hashes'].items():
        assert sha(OUTPUT/'mod'/rel)==digest,'Validated payload changed: '+rel
    prepare_identity(target)
    files={p.relative_to(OUTPUT/'mod').as_posix():p for p in (OUTPUT/'mod').rglob('*') if p.is_file()}
    assert all(r.startswith(('db/events/','db/leaders/','gfx/interface/pics/','gfx/load_1024.bmp','gfx/interface/frontend/bg_start.bmp')) for r in files)
    before=protected() if target==TARGET else {str(p):sha(p) for p in (target/'scenarios').rglob('*') if p.is_file()}
    before={p:h for p,h in before.items() if p not in {str(target/'gfx/load_1024.bmp'),str(target/'gfx/interface/frontend/bg_start.bmp')}}
    save=target/'scenarios/save games/autosave.eug'
    raw=save.read_bytes() if with_save else None
    new_save=None;portrait_count=0;name='CLEANUP1_India_1942-02-01.eug'
    if with_save:
        sd=parse(raw).get('header').get('startdate')
        assert (sd.get('year'),sd.get('month'),sd.get('day'))==('1942','february','0'),'A different autosave needs review before creating the copy'
        refs={str(v).replace('\\','/') for v in parse(raw).all('event')}
        assert 'db/events/aubm_v4/43_wartime_settlements.txt' in refs
        new_save,portrait_count=copy_save(raw,name)
        assert not save.with_name(name).exists(),'Named save already exists; do not overwrite it'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'tmp'/('cleanup1-install-'+stamp);backup.mkdir(parents=True,exist_ok=False)
    changed={r:p for r,p in files.items() if not (target/r).exists() or sha(target/r)!=sha(p)}
    existing=set();receipt={'build':'27-CLEANUP1','hotfix':'B1','visible_version':'27-CLEANUP1-B1','target':str(target),'backup':str(backup),
        'installed_utc':stamp,'engine_playtested':False,'game_launched':False,'files':{},
        'original_saves_unchanged':True,'portrait_references_in_new_copy':portrait_count,
        'new_save':str(save.with_name(name)) if with_save else None}
    for rel,p in changed.items():
        old=target/rel
        if old.exists():
            copy=backup/rel;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,copy)
            assert sha(copy)==sha(old);existing.add(rel)
        receipt['files'][rel]={'before':sha(old) if old.exists() else None,'after':sha(p)}
    for p in (save,save.with_name('autosave.eug.cfg'),target/'CLEANUP1.json'):
        if p.exists():shutil.copy2(p,backup/p.name)
    assert_closed()
    if with_save:assert save.read_bytes()==raw,'Autosave changed during preflight'
    try:
        for rel,p in changed.items():
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
            assert sha(dest)==sha(p),'Deployment verification failed: '+rel
        assert all(sha(Path(p))==h for p,h in before.items()),'Protected file changed'
        if with_save:
            save.with_name(name).write_bytes(new_save)
            cfg=save.with_name('autosave.eug.cfg')
            if cfg.exists():shutil.copy2(cfg,save.with_name(name+'.cfg'))
            assert save.read_bytes()==raw
    except Exception:
        for rel in existing:shutil.copy2(backup/rel,target/rel)
        # New payload files are harmless but retained for inspection on failure;
        # no recursive deletion or broad rollback touches the game installation.
        raise
    serialized=json.dumps(receipt,indent=2)+'\n'
    (backup/'receipt.json').write_text(serialized,encoding='utf8')
    (target/'CLEANUP1.json').write_text(serialized,encoding='utf8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
    print('Verified installed files:',len(files),'changed:',len(changed))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--target',type=Path,default=TARGET)
    ap.add_argument('--without-save',action='store_true')
    args=ap.parse_args();install(args.target,not args.without_save)
