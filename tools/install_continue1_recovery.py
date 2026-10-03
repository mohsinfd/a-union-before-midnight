"""Bounded CONTINUE1 overlay and reversible continuation of the NAVAL1 save."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from dh_save_spans import Node,parse,replace,walk
import aubm_campaign_clock_fix as clocks
from aubm_diplomacy_consistency import transform as diplomacy
from aubm_continue1_portraits import roster,migrate,pack,ATLAS
from repair_naval1_save import ORDERS,scalar_edit

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
PRIOR='NAVAL1_India_1941_June_1_90pct.eug'
SAVE='CONTINUE1_India_1941_June_1_90pct.eug'
TITLE='CONTINUE1 - India June 1941 - overdue fleets 90 percent'
EXPECTED={'db/events/india_v3/40_diplomacy.txt','db/events/aubm_v4/26_grand_strategy.txt',
          'db/events/aubm_v4/32_national_consolidation.txt','db/events/aubm_v4/43_wartime_settlements.txt'}

def sha(raw):return hashlib.sha256(raw).hexdigest()


def continuation(raw,mapping,records):
    root=parse(raw);header=root.get('header');india=next(c for c in root.all('country') if c.get('tag')=='IND')
    flags=root.get('globaldata').get('flags')
    active=[i for i,r in records.items() if int(flags.get(r[0]['watch'],'0'))]
    if active:raise ValueError('Unexpected active campaign clock; inspect its earned age before migration: '+str(active))
    ships=[n for n in india.all('division_development') if n.get('name') in {o[0] for o in ORDERS}]
    if len(ships)!=10 or len({n.get('name') for n in ships})!=10 or any(Decimal(n.get('total_progress'))!=Decimal('.9') for n in ships):
        raise ValueError('Expected ten unique recovered ships at exactly 90 percent')
    oldmapping={}
    for n in walk(india):
        ident=n.get('id')
        if isinstance(ident,Node) and ident.get('type')=='6' and int(ident.get('id','-1')) in mapping and n.get('picture'):
            i=int(ident.get('id'));oldmapping[i]=n.get('picture')
    if len(oldmapping)!=375:raise ValueError('Expected all 375 existing reserves in the continuation')
    edited=replace(raw,[scalar_edit(header,'name','"'+TITLE+'"'),scalar_edit(header,'optionfile','"scenarios\\save games\\'+SAVE+'.cfg"')])
    updated,changed=migrate(edited,mapping)
    # Undo only allowed picture/header edits and prove every other byte unchanged.
    restored,_=migrate(updated,oldmapping);rh=parse(restored).get('header')
    restored=replace(restored,[scalar_edit(rh,'name','"'+header.get('name')+'"'),scalar_edit(rh,'optionfile','"'+header.get('optionfile')+'"')])
    if restored!=raw:raise AssertionError('Continuation altered bytes outside approved picture/header fields')
    return updated,dict(portrait_fields_changed=changed,active_campaign_clocks=active,overdue_ships=10,
                        progress_each='0.9000',all_production_resources_and_world_state_byte_identical_to_naval1=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install',action='store_true');args=ap.parse_args()
    out=ROOT/'build/continue1';out.mkdir(parents=True,exist_ok=True)
    originals={p.relative_to(MOD).as_posix():p.read_bytes() for d in ['india_v3','aubm_v4'] for p in (MOD/'db/events'/d).glob('*.txt')}
    texts={p:v.decode('latin1') for p,v in originals.items()}
    fixed,records=clocks.transform(texts);fixed,drecords=diplomacy(fixed)
    changed={p:t.encode('latin1') for p,t in fixed.items() if t!=texts[p]}
    if set(changed)!=EXPECTED:raise ValueError('Unexpected/already installed overlay diff: '+str(set(changed)))
    if clocks.transform(fixed)[0]!=fixed or diplomacy(fixed)[0]!=fixed:raise AssertionError('Overlay is not idempotent')
    events=[e for t in fixed.values() for e in parse(t).all('event')];ids=[int(e.get('id')) for e in events]
    if len(ids)!=len(set(ids)) or not clocks.NEW_EVENT_IDS<=set(ids):raise AssertionError('Callback ID collision/missing event')
    for e in events:
        for n in walk(e):
            q=n.get('event')
            if isinstance(q,Node) and q.get('days') is not None and int(q.get('id')) in clocks.SOURCES:raise AssertionError('Residual elapsed timestamp')
        if int(e.get('id')) in clocks.CALLBACKS.values():
            if any(e.get(k) is not None for k in ('date','offset','deathdate','trigger','save_date')):raise AssertionError('Invalid queued callback')
            if any(c.get('type') not in ('setflag','clrflag','event') for a in clocks.acts(e) for c in a.all('command')):raise AssertionError('Clock helper grants effects')
    print('Event overlay validated: four modules, fourteen clocks, fifteen helpers.',flush=True)
    csv='db/leaders/india.csv';oldroster=(MOD/csv).read_bytes();newroster,mapping=roster(oldroster)
    source_roster=(ROOT/'mod'/csv).read_bytes();newsource,smapping=roster(source_roster)
    if smapping!=mapping:raise AssertionError('Installed/source reserve identities differ')
    changed[csv]=newroster
    pack(out/'mod/gfx/interface/pics').save(out/'portraits-preview.png')
    for p in (out/'mod/gfx/interface/pics').glob('aubm_c1_reserve_*.bmp'):changed[p.relative_to(out/'mod').as_posix()]=p.read_bytes()
    for name in set(mapping.values()):
        rel='gfx/interface/pics/'+name+'.bmp'
        if rel not in changed and not (MOD/rel).exists():raise AssertionError('Missing reserve portrait '+name)
    prior=MOD/'scenarios/save games'/PRIOR;raw=prior.read_bytes();cfg=prior.with_suffix('.eug.cfg').read_bytes()
    naval=json.loads((MOD/'NAVAL1.json').read_text(encoding='utf8'))
    if sha(raw)!=naval['recovery_sha256']:raise ValueError('NAVAL1 has changed or been played; inspect the current campaign first')
    auto=MOD/'scenarios/save games/autosave.eug';autohash=sha(auto.read_bytes())
    if autohash!=naval['source_sha256']:raise ValueError('Autosave changed since the inspected campaign')
    updated,save_report=continuation(raw,mapping,records)
    print('Save verified: 90% queues and all world/resource bytes preserved; reserve pictures updated.',flush=True)
    for p,v in changed.items():
        target=out/'mod'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(v)
    (out/SAVE).write_bytes(updated);(out/(SAVE+'.cfg')).write_bytes(cfg)
    sourcewrites={csv:newsource,**{p:v for p,v in changed.items() if p.startswith('gfx/')}}
    writes={MOD/p:v for p,v in changed.items()}
    writes.update({ROOT/'mod'/p:v for p,v in sourcewrites.items()})
    target=MOD/'scenarios/save games'/SAVE
    if target.exists() or target.with_suffix('.eug.cfg').exists():raise FileExistsError('CONTINUE1 save already exists')
    writes[target]=updated;writes[target.with_suffix('.eug.cfg')]=cfg
    snapshots={p:p.read_bytes() if p.exists() else None for p in writes}
    report=dict(build='CONTINUE1',installed=False,source_save=str(prior),source_sha256=sha(raw),
        output_save=str(target),recovery_sha256=sha(updated),original_autosave_sha256=autohash,
        campaign_clocks=records,diplomacy=drecords,portrait_pool=64,new_portraits=16,
        atlas_sha256=sha(ATLAS.read_bytes()),save=save_report,engine_tested=False,
        validation='12 protocol/diplomacy/portrait tests; build/naval/save suite; installed overlay syntax, IDs, callback format, idempotence and lossless-save assertions',
        changed_files={str(p):dict(before=None if snapshots[p] is None else sha(snapshots[p]),after=sha(v)) for p,v in writes.items()})
    if args.install:
        # Optimistic preflight prevents clobbering concurrent user/game changes.
        if sha(auto.read_bytes())!=autohash or prior.read_bytes()!=raw:raise ValueError('Campaign changed during preparation')
        for p,v in originals.items():
            if (MOD/p).read_bytes()!=v:raise ValueError('Installed events changed during preparation')
        if (MOD/csv).read_bytes()!=oldroster or (ROOT/'mod'/csv).read_bytes()!=source_roster:raise ValueError('Roster changed during preparation')
        backup=ROOT/'tmp'/('continue1-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(parents=True,exist_ok=False)
        for p,v in snapshots.items():
            if v is None:continue
            rel=Path('installed')/p.relative_to(MOD) if p.is_relative_to(MOD) else Path('source')/p.relative_to(ROOT)
            b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(v)
        (backup/PRIOR).write_bytes(raw);(backup/(PRIOR+'.cfg')).write_bytes(cfg)
        (backup/'transaction.json').write_text(json.dumps(report['changed_files'],indent=2)+'\n',encoding='utf8')
        applied=[]
        try:
            for p,v in writes.items():
                p.parent.mkdir(parents=True,exist_ok=True);applied.append(p);p.write_bytes(v)
            for p,v in writes.items():
                if p.read_bytes()!=v:raise AssertionError('Written file mismatch: '+str(p))
            if sha(auto.read_bytes())!=autohash or prior.read_bytes()!=raw:raise AssertionError('Original campaign changed')
            for p,v in originals.items():
                if p not in changed and (MOD/p).read_bytes()!=v:raise AssertionError('Unrelated event module changed')
        except Exception:
            for p in reversed(applied):
                if snapshots[p] is None:p.unlink()
                else:p.write_bytes(snapshots[p])
            raise
        report.update(installed=True,backup=str(backup),original_autosave_and_naval1_unchanged=True)
        (MOD/'CONTINUE1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(installed=report['installed'],save=str(target),manifest=str(out/'manifest.json')),indent=2))

if __name__=='__main__':main()
