"""Explicit campaign adjustment: hand over four islands and withdraw occupiers."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
from dh_save_spans import parse,replace,Node

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
PROVINCES={'1639','1652','1653','1656'}
DESTINATION='1552'  # Tokyo: verified Japanese ownership and control.


def sha(b):return hashlib.sha256(b).hexdigest()


def scalar(n,key,value):
    f=n.field(key);return f.value_start,f.end,value.encode('latin1')


def repair(raw):
    r=parse(raw);cs={c.get('tag'):c for c in r.all('country')};j=cs['JAP'];ino=cs['INO']
    assert ino.get('puppet')=='IND'
    assert PROVINCES<=set(ino.get('ownedprovinces').atoms())
    assert PROVINCES<=set(j.get('controlledprovinces').atoms())
    assert not PROVINCES&set(ino.get('controlledprovinces').atoms())
    assert DESTINATION in j.get('ownedprovinces').atoms() and DESTINATION in j.get('controlledprovinces').atoms()
    for c in cs.values():
        for kind in ['airunit','navalunit']:
            assert not any(u.get('location') in PROVINCES or u.get('base') in PROVINCES for u in c.all(kind)), 'Unexpected aircraft or ships need review'
    troops=[u for u in j.all('landunit') if u.get('location') in PROVINCES]
    assert len(troops)==3 and sum(len(u.all('division')) for u in troops)==3
    for tag,c in cs.items():
        if tag not in ['JAP','IND','INO']:
            assert not any(u.get('location') in PROVINCES for u in c.all('landunit')), 'Unexpected third-country force'
    edits=[];record=[]
    for tag in ['JAP','INO']:
        values=cs[tag].get('controlledprovinces').atoms()
        values=[p for p in values if p not in PROVINCES] if tag=='JAP' else values+sorted(PROVINCES)
        edits.append(scalar(cs[tag],'controlledprovinces','{ '+' '.join(values)+' }'))
    for u in troops:
        record.append(dict(name=u.get('name'),from_province=u.get('location'),to_province=DESTINATION,
                           division_ids=[[(f.key,f.value) for f in d.get('id').fields] for d in u.all('division')]))
        edits.append(scalar(u,'location',DESTINATION))
        if u.get('prevprov') is not None:edits.append(scalar(u,'prevprov',DESTINATION))
        if u.get('dig_in') is not None:edits.append(scalar(u,'dig_in','0'))
        for field in u.fields:
            if field.key in ['movement','movetime','mission','hour','target']:
                edits.append((field.start,field.end,b''))
    result=replace(raw,edits);delta=0;undo=[]
    for a,b,value in sorted(edits):
        undo.append((a+delta,a+delta+len(value),raw[a:b]));delta+=len(value)-(b-a)
    assert replace(result,undo)==raw, 'Unapproved save changes'
    q=parse(result);qc={c.get('tag'):c for c in q.all('country')}
    assert set(qc['INO'].get('ownedprovinces').atoms())==set(qc['INO'].get('controlledprovinces').atoms())
    for p in PROVINCES:
        assert [tag for tag,c in qc.items() if p in c.get('controlledprovinces',Node()).atoms()]==['INO']
        assert [tag for tag,c in qc.items() if p in c.get('ownedprovinces',Node()).atoms()]==['INO']
    before=[raw[d.start:d.end] for u in j.all('landunit') for d in u.all('division')]
    after=[result[d.start:d.end] for u in qc['JAP'].all('landunit') for d in u.all('division')]
    assert before==after, 'Division contents changed'
    assert not any(u.get('location') in PROVINCES for u in qc['JAP'].all('landunit'))
    return result,record


def main():
    prior=json.loads((ROOT/'build/settlement1p/direct-receipt.json').read_text())
    originals={Path(path):Path(path).read_bytes() for path in prior['files']}
    for p,b in originals.items():
        if sha(b)!=prior['files'][str(p)]['after']:raise ValueError('Save changed; review new progress before editing: '+str(p))
    outputs={};records=[]
    for p,b in originals.items():outputs[p],records=repair(b)
    backup=ROOT/'build/settlement1p'/('occupation-backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    for p,b in originals.items():(backup/p.name).write_bytes(b)
    written=[]
    try:
        for p,b in outputs.items():
            if p.read_bytes()!=originals[p]:raise ValueError('Save changed during preparation')
            p.write_bytes(b);written.append(p)
            assert p.read_bytes()==b
    except Exception:
        for p in written:p.write_bytes(originals[p])
        raise
    report=dict(build='SETTLEMENT1P-ISLANDS',backup=str(backup),owner_and_controller='INO',puppet_of='IND',
                provinces=sorted(PROVINCES),withdrawn_to_tokyo=records,
                units_destroyed=0,additional_supplies_or_dissent_charge=0,war_and_alliance_changes=0,
                inverse_edit_proof=True,engine_tested=False,
                files={str(p):dict(before=sha(originals[p]),after=sha(b)) for p,b in outputs.items()})
    (ROOT/'build/settlement1p/occupation-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
