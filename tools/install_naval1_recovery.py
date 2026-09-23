"""Prepare/install only the NAVAL1 overlay and a separate inspected-save recovery."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from dh_save_spans import parse,Node,walk
from aubm_naval_clock_fix import transform,NEW_EVENT_IDS
from repair_naval1_save import recover

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
SAVE='NAVAL1_India_1941_June_1_90pct.eug'
EXPECTED_CHANGED={'db/events/india_v3/32_navy.txt','db/events/aubm_v4/40_special_units_and_capital_ships.txt'}

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install',action='store_true');args=ap.parse_args()
    paths=[p for folder in ['india_v3','aubm_v4'] for p in (MOD/'db/events'/folder).glob('*.txt')]
    originals={p.relative_to(MOD).as_posix():p.read_bytes() for p in paths}
    texts={p:r.decode('latin1') for p,r in originals.items()}
    updated,_=transform(texts)
    changed={p:t.encode('latin1') for p,t in updated.items() if t!=texts[p]}
    if set(changed)!=EXPECTED_CHANGED: raise ValueError(f'Unexpected overlay diff: {set(changed)}')
    # Every registered callback is in an already-loaded module, once.
    ids=[int(e.get('id')) for t in updated.values() for e in parse(t).all('event')]
    if len(ids)!=len(set(ids)) or not NEW_EVENT_IDS<=set(ids): raise ValueError('Event identity validation failed')
    source=MOD/'scenarios/save games/autosave.eug';raw=source.read_bytes()
    cfg_source=source.with_suffix(source.suffix+'.cfg');cfg=cfg_source.read_bytes()
    repaired,manifest=recover(raw,MOD,SAVE)
    out=ROOT/'build/naval1';out.mkdir(parents=True,exist_ok=True)
    for path,data in changed.items():
        target=out/'mod'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    (out/SAVE).write_bytes(repaired);(out/(SAVE+'.cfg')).write_bytes(cfg)
    # Save evidence about other time-dependent campaigns without modifying them.
    indexed={int(e.get('id')):(path,e) for path,text in texts.items() for e in parse(text).all('event')}
    sources={}
    for target,(path,e) in indexed.items():
        for n in walk(e):
            ref=n.get('event')
            if isinstance(ref,Node) and ref.get('days') is not None:
                prior=int(ref.get('id'))
                if prior in indexed and indexed[prior][1].get('persistent')=='yes':
                    sources.setdefault(prior,dict(name=indexed[prior][1].get('name'),targets=set()))['targets'].add(target)
    source_ids={9271104,9271105,9271106,9271109,9281880}
    manifest.update(build='NAVAL1',source_save=str(source),source_sha256=sha(raw),recovery_sha256=sha(repaired),
                    output_save=str(MOD/'scenarios/save games'/SAVE),
                    installed=False,changed_files={p:dict(before=sha(originals[p]),after=sha(v)) for p,v in changed.items()},
                    other_persistent_clocks={str(i):dict(name=d['name'],targets=sorted(d['targets'])) for i,d in sources.items() if i not in source_ids})
    if args.install:
        target_save=MOD/'scenarios/save games'/SAVE
        if target_save.exists() or target_save.with_suffix(target_save.suffix+'.cfg').exists(): raise FileExistsError('Recovery save already exists')
        if source.read_bytes()!=raw: raise ValueError('Autosave changed during preparation')
        for p in originals:
            if (MOD/p).read_bytes()!=originals[p]: raise ValueError('Installed events changed during preparation')
        backup=ROOT/'tmp'/('naval1-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        backup.mkdir(parents=True,exist_ok=False)
        for p in changed:
            target=backup/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(originals[p])
        (backup/'autosave.eug').write_bytes(raw);(backup/'autosave.eug.cfg').write_bytes(cfg)
        for p,data in changed.items(): (MOD/p).write_bytes(data)
        target_save.write_bytes(repaired);target_save.with_suffix(target_save.suffix+'.cfg').write_bytes(cfg)
        if source.read_bytes()!=raw or cfg_source.read_bytes()!=cfg: raise AssertionError('Original autosave changed')
        for p,r in originals.items():
            if p not in changed and (MOD/p).read_bytes()!=r: raise AssertionError('Unrelated events changed')
        for p,v in changed.items():
            if (MOD/p).read_bytes()!=v: raise AssertionError('Installed file verification failed')
        manifest.update(installed=True,backup=str(backup),original_autosave_unchanged=True,other_event_modules_unchanged=True)
        (MOD/'NAVAL1.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(installed=manifest['installed'],save=manifest['output_save'],orders=len(manifest['orders']),
                         charges=manifest['charges'],other_persistent_clocks=len(manifest['other_persistent_clocks']),
                         manifest=str(out/'manifest.json')),indent=2))

if __name__=='__main__':main()
