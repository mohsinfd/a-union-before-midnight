"""Backed-up direct puppet state correction, without an on-load event."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import hashlib
import json
from dh_save_spans import parse,replace,Node

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
DIR=MOD/'scenarios/save games'
BASE=DIR/'SETTLEMENT1_India_1942_September_2.eug'
TARGETS={
    'indonesiaIndia_1942_September_2.eug':'Indonesia - Indian puppet - 2 Sep 1942',
    'SETTLEMENT1P_India_1942_September_2.eug':'SETTLEMENT1P - Indonesia already an Indian puppet',
}


def sha(b):return hashlib.sha256(b).hexdigest()


def scalar(n,key,value):
    f=n.field(key);return f.value_start,f.end,value.encode('latin1')


def make_copy(raw,filename,title):
    r=parse(raw);h=r.get('header');cs={c.get('tag'):c for c in r.all('country')}
    india,ino=cs['IND'],cs['INO']
    if ino.get('puppet') is not None:raise ValueError('Base is already a puppet; refuse double cost')
    supply=Decimal(india.get('supplies'));dissent=Decimal(india.get('dissent'))
    if supply<500 or dissent>96:raise ValueError('Unexpected affordability/dissent')
    tag=ino.field('tag')
    edits=[(tag.end,tag.end,b'\r\n\tpuppet = "IND"'),
           scalar(india,'supplies',f'{supply-500:.4f}'),
           scalar(india,'dissent',f'{dissent+4:.4f}'),
           scalar(h,'name','"'+title+'"'),
           scalar(h,'optionfile','"scenarios\\save games\\'+filename+'.cfg"')]
    result=replace(raw,edits)
    shift=0;undo=[]
    for a,b,new in sorted(edits):
        undo.append((a+shift,a+shift+len(new),raw[a:b]));shift+=len(new)-(b-a)
    assert replace(result,undo)==raw, 'Unexpected gameplay edits'
    v=parse(result);cc={c.get('tag'):c for c in v.all('country')}
    assert cc['INO'].get('puppet')=='IND'
    assert Decimal(cc['IND'].get('supplies'))==supply-500
    assert Decimal(cc['IND'].get('dissent'))==dissent+4
    assert not any(e.get('id')=='9297399' for e in v.get('globaldata').get('queued_events').all('event'))
    assert not any('SETTLEMENT1P_indonesia' in x for x in v.all('event'))
    for p in ['1639','1652','1653','1656']:
        assert p in cc['INO'].get('ownedprovinces').atoms()
        assert p in cc['JAP'].get('controlledprovinces').atoms()
    return result


def main():
    prior=json.loads((ROOT/'build/settlement1p/receipt.json').read_text())
    s1=json.loads((MOD/'SETTLEMENT1.json').read_text())
    raw=BASE.read_bytes()
    if sha(raw)!=s1['recovery_sha256']:raise ValueError('Base was played or changed; inspect before repair')
    expected={'indonesiaIndia_1942_September_2.eug':s1['source_sha256'],
              'SETTLEMENT1P_India_1942_September_2.eug':prior['output_sha256']}
    original={DIR/name:(DIR/name).read_bytes() for name in TARGETS}
    for p,b in original.items():
        if sha(b)!=expected[p.name]:raise ValueError('Target changed since assessment: '+p.name)
    output={DIR/name:make_copy(raw,name,title) for name,title in TARGETS.items()}
    backup=ROOT/'build/settlement1p'/('direct-backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    for p,b in original.items():
        (backup/p.name).write_bytes(b)
        cfg=p.with_suffix('.eug.cfg')
        if cfg.exists():(backup/cfg.name).write_bytes(cfg.read_bytes())
    wrote=[]
    try:
        for p,b in output.items():
            if p.read_bytes()!=original[p]:raise ValueError('Game saved while preparing repair: '+str(p))
            p.write_bytes(b);wrote.append(p)
            if p.read_bytes()!=b:raise IOError('Installed verification failure')
    except Exception:
        for p in wrote:p.write_bytes(original[p])
        raise
    report=dict(build='SETTLEMENT1P-DIRECT',backup=str(backup),source_sha256=sha(raw),
                puppet='INO -> IND',supplies_delta=-500,dissent_delta=4,
                supplies_after='29894.1289',dissent_after='16.7949',
                correction_event_queued=False,correction_event_loaded=False,
                inverse_edit_proof=True,all_other_gameplay_unchanged_from_settlement1=True,
                engine_tested=False,
                files={str(p):{'before':sha(original[p]),'after':sha(b)} for p,b in output.items()})
    (ROOT/'build/settlement1p/direct-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
