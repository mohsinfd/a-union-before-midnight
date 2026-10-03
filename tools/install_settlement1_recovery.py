"""Prepare/validate/install a bounded release-ownership patch and save copy."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from dh_save_spans import Node,parse,replace,walk
from aubm_continue1_portraits import roster,migrate
from aubm_release_ownership import transform_all,CALLBACKS,NEW_EVENT_IDS,TERRITORIES

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
SOURCE='indonesiaIndia_1942_September_2.eug'
SAVE='SETTLEMENT1_India_1942_September_2.eug'
TITLE='SETTLEMENT1 - India 2 September 1942'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def scalar(node,key,value):
    f=node.field(key);return (f.value_start,f.end,value.encode('latin1'))


def migration(raw,mapping):
    root=parse(raw);countries={c.get('tag'):c for c in root.all('country')}
    india=countries['IND'];ino=countries['INO'];head=root.get('header')
    if ino.get('puppet') or not root.get('globaldata').get('flags').get('ind_aubm_regional_settled_u05')=='1':
        raise ValueError('Unexpected Indonesian settlement; reassess latest save')
    owned=set(india.get('ownedprovinces').atoms());cores=set(india.get('nationalprovinces').atoms())
    incores=set(ino.get('nationalprovinces').atoms())
    controls={p:tag for tag,c in countries.items() for p in c.get('controlledprovinces',Node()).atoms()}
    transfer=sorted(p for p in owned & incores if p not in cores and int(p) in TERRITORIES['INO']
                    and controls.get(p) not in [None,'IND','REB'])
    expected=['1639','1652','1653','1656']
    if transfer!=expected or any(controls[p]!='JAP' for p in transfer):
        raise ValueError('Unexpected occupied territory: '+str(transfer))
    oldpics={}
    for n in walk(india):
        ident=n.get('id')
        if isinstance(ident,Node) and ident.get('type')=='6' and int(ident.get('id','-1')) in mapping and n.get('picture'):
            oldpics[int(ident.get('id'))]=n.get('picture')
    updated,count=migrate(raw,mapping)
    r=parse(updated);h=r.get('header');cc={c.get('tag'):c for c in r.all('country')}
    edits=[scalar(h,'name','"'+TITLE+'"'),scalar(h,'optionfile','"scenarios\\save games\\'+SAVE+'.cfg"')]
    for tag in ['IND','INO']:
        ids=cc[tag].get('ownedprovinces').atoms()
        ids=[x for x in ids if x not in transfer] if tag=='IND' else ids+[x for x in transfer if x not in ids]
        edits.append(scalar(cc[tag],'ownedprovinces','{ '+' '.join(ids)+' }'))
    updated=replace(updated,edits)
    # Revert exactly the permitted fields; every other original byte must survive.
    restored,_=migrate(updated,oldpics);r=parse(restored);h=r.get('header');cc={c.get('tag'):c for c in r.all('country')}
    undo=[]
    for key in ['name','optionfile']:
        f=head.field(key);undo.append(scalar(h,key,raw[f.value_start:f.end].decode('latin1')))
    for tag in ['IND','INO']:
        f=countries[tag].field('ownedprovinces');undo.append(scalar(cc[tag],'ownedprovinces',raw[f.value_start:f.end].decode('latin1')))
    if replace(restored,undo)!=raw:raise AssertionError('Unexpected changes outside portrait/header/title ownership fields')
    nr=parse(updated);nc={c.get('tag'):c for c in nr.all('country')}
    for p in transfer:
        owners=[tag for tag,c in nc.items() if p in c.get('ownedprovinces',Node()).atoms()]
        controllers=[tag for tag,c in nc.items() if p in c.get('controlledprovinces',Node()).atoms()]
        if owners!=['INO'] or controllers!=['JAP']:raise AssertionError('Owner/control verification failed')
    return updated,dict(portrait_fields_updated=count,transferred_claims=transfer,
        prior_owner='IND',new_owner='INO',controller_unchanged='JAP',indonesia_remains_independent=True,
        inverse_edit_proof=True,all_wars_units_production_resources_dissent_flags_and_history_unchanged=True)


def prepare():
    out=ROOT/'build/settlement1';out.mkdir(parents=True,exist_ok=True)
    files={p.relative_to(MOD).as_posix():p.read_bytes().decode('latin1')
           for d in ['india_v3','aubm_v4'] for p in (MOD/'db/events'/d).glob('*.txt')}
    fixed,records=transform_all(files)
    if transform_all(fixed)[0]!=fixed:raise AssertionError('Overlay must be idempotent')
    from aubm_redesign_presentation import audit
    changed_paths={p for p in fixed if fixed[p]!=files.get(p)}
    prior_errors={(x['id'],x['field'],x['problem']) for x in audit({p:files[p] for p in changed_paths})['hard_errors']}
    new_errors={(x['id'],x['field'],x['problem']) for x in audit({p:fixed[p] for p in changed_paths})['hard_errors']}-prior_errors
    if new_errors:raise AssertionError('New presentation budget error: '+str(new_errors))
    ids=[]
    for path,text in fixed.items():
        for e in parse(text).all('event'):
            eid=int(e.get('id'));ids.append(eid)
            if eid in NEW_EVENT_IDS:
                if any(e.get(k) is not None for k in ['date','offset','deathdate','decision','trigger']):
                    raise AssertionError('Release callback must be queued only')
                for a in [f.value for f in e.fields if (f.key or '').startswith('action')]:
                    for c in a.all('command'):
                        if c.get('type')!='secedeprovince' or c.get('when')!='1':
                            raise AssertionError('Callback may only safely transfer ownership')
    if len(ids)!=len(set(ids)) or not NEW_EVENT_IDS<=set(ids):raise AssertionError('Callback IDs duplicate/missing')
    # Check every actually loaded stock file for a collision too.
    original=(MOD/'scenarios/save games'/SOURCE).read_bytes();r=parse(original)
    for rel in r.all('event'):
        rel=rel.replace('\\','/')
        if rel in files:continue
        p=MOD/rel
        if p.is_file():
            import re
            if NEW_EVENT_IDS & {int(x) for x in re.findall(rb'^\s*id\s*=\s*(\d+)\s*$',p.read_bytes(),re.M)}:
                raise AssertionError('Collision with loaded stock events: '+rel)
    _,mapping=roster((MOD/'db/leaders/india.csv').read_bytes())
    for picture in set(mapping.values()):
        if not (MOD/'gfx/interface/pics'/(picture+'.bmp')).exists():raise AssertionError('Missing reserve image')
    recovery,report=migration(original,mapping)
    changed={rel:text.encode('latin1') for rel,text in fixed.items() if text!=files[rel]}
    for rel,raw in changed.items():
        target=out/'mod'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    (out/SAVE).write_bytes(recovery)
    cfg=(MOD/'scenarios/save games'/(SOURCE+'.cfg')).read_bytes();(out/(SAVE+'.cfg')).write_bytes(cfg)
    manifest=dict(build='SETTLEMENT1',installed=False,engine_tested=False,source_save=SOURCE,
        source_sha256=sha(original),recovery_save=SAVE,recovery_sha256=sha(recovery),save_changes=report,
        shared_rule_country_count=len(CALLBACKS),new_visible_decisions=0,
        known_unreleasable_tags=['U03','U04'],
        files={rel:dict(before=sha(files[rel].encode('latin1')),after=sha(raw)) for rel,raw in changed.items()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return out,manifest,changed,original,recovery,cfg


def install(out,manifest,changed,original,recovery,cfg):
    if (MOD/'SETTLEMENT1.json').exists():raise ValueError('Already installed; inspect receipt before reapplying')
    targets={MOD/rel:raw for rel,raw in changed.items()}
    targets[MOD/'scenarios/save games'/SAVE]=recovery
    targets[MOD/'scenarios/save games'/(SAVE+'.cfg')]=cfg
    save_inputs={p:p.read_bytes() for p in [MOD/'scenarios/save games'/SOURCE,MOD/'scenarios/save games/autosave.eug']}
    if save_inputs[MOD/'scenarios/save games'/SOURCE]!=original:raise ValueError('Source save changed during preparation')
    for rel,r in manifest['files'].items():
        if sha((MOD/rel).read_bytes())!=r['before']:raise ValueError('Installation changed during preparation: '+rel)
    for name in [SAVE,SAVE+'.cfg']:
        if (MOD/'scenarios/save games'/name).exists():raise ValueError('Recovery target already exists')
    backup=out/('backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir()
    before={p:p.read_bytes() if p.is_file() else None for p in targets}
    for p,raw in before.items():
        if raw is not None:
            b=backup/p.relative_to(MOD);b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(raw)
    for p,raw in save_inputs.items():
        b=backup/p.relative_to(MOD);b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(raw)
    wrote=[]
    try:
        for p,raw in targets.items():
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);wrote.append(p)
            if p.read_bytes()!=raw:raise IOError('Installed bytes differ: '+str(p))
        if any(p.read_bytes()!=raw for p,raw in save_inputs.items()):raise ValueError('Original save changed during installation')
        manifest.update(installed=True,backup=str(backup),original_manual_and_autosave_unchanged=True)
        (MOD/'SETTLEMENT1.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    except Exception:
        for p in reversed(wrote):
            if before[p] is None:
                # Only newly created, explicitly tracked files inside MOD.
                if MOD.resolve() not in p.resolve().parents:raise AssertionError('Unsafe rollback path')
                p.unlink()
            else:p.write_bytes(before[p])
        raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--install',action='store_true');args=ap.parse_args()
    out,manifest,changed,original,recovery,cfg=prepare()
    if args.install:install(out,manifest,changed,original,recovery,cfg)
    print(json.dumps({k:manifest[k] for k in ['build','installed','engine_tested','recovery_save','save_changes','shared_rule_country_count','new_visible_decisions']},indent=2))
