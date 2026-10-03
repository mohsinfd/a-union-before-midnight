"""Save-specific, one-time respec from sovereign Indonesia to an Indian puppet."""
from pathlib import Path
import hashlib
import json
import re
from decimal import Decimal
from dh_save_spans import Node,parse,replace

ROOT=Path(__file__).resolve().parents[1]
MOD=Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')
SOURCE='SETTLEMENT1_India_1942_September_2.eug'
DEST='SETTLEMENT1P_India_1942_September_2.eug'
TITLE='SETTLEMENT1P - Indonesia as Indian Puppet'
REL='db/events/SETTLEMENT1P_indonesia.txt'
EID=9297399
EVENT='''# Save-specific correction; not registered for ordinary new campaigns.
event = {
 id = 9297399
 random = no
 country = IND
 name = "Indonesia Under Indian Protection"
 desc = "You chose an independent Indonesia at Batavia but intended an Indian puppet. This correction places Indonesia under Indian protection for the original cost: 500 supplies and 4 dissent. Japanese-held islands remain occupied. India keeps its existing alliances and wars."
 style = 2
 picture = "aubm_v4_indian_ocean_war"
 action_a = {
  trigger = { exists = INO NOT = { ispuppet = IND } NOT = { ispuppet = INO } NOT = { war = { country = IND country = INO } } supplies = 500 }
  name = "Make Indonesia our puppet: -500 supplies, +4 dissent"
  command = { type = supplies value = -500 }
  command = { type = dissent value = 4 }
  command = { type = make_puppet which = INO }
 }
 action_b = {
  name = "Keep Indonesia independent; change nothing"
 }
}
'''


def scalar(n,key,value):
    f=n.field(key);return f.value_start,f.end,value.encode('latin1')


def main():
    source=MOD/'scenarios/save games'/SOURCE;dest=source.with_name(DEST)
    raw=source.read_bytes();root=parse(raw);g=root.get('globaldata');h=root.get('header')
    countries={c.get('tag'):c for c in root.all('country')};india=countries['IND'];ino=countries['INO']
    if ino.get('puppet') or india.get('puppet'):raise ValueError('Unexpected existing puppet relationship')
    if Decimal(india.get('supplies'))<500:raise ValueError('Cannot cover the selected option cost')
    for war in g.all('war'):
        sides=[set(war.get(side,Node()).get('participant',Node()).atoms()) for side in ['attackers','defenders']]
        if ('IND' in sides[0] and 'INO' in sides[1]) or ('INO' in sides[0] and 'IND' in sides[1]):raise ValueError('India and Indonesia are at war')
    if str(EID) in g.get('history',Node()).atoms():raise ValueError('Correction already completed')
    queue=g.get('queued_events')
    if not isinstance(queue,Node) or any(e.get('id')==str(EID) for e in queue.all('event')):raise ValueError('Missing or already repaired queue')
    for rel in root.all('event'):
        p=MOD/rel.replace('\\','/')
        if p.is_file() and re.search(rb'^\s*id\s*=\s*9297399\s*$',p.read_bytes(),re.M):raise ValueError('Event ID already loaded')
    pe=parse(EVENT).get('event')
    assert pe.get('id')==str(EID) and pe.get('persistent') is None
    assert all(pe.get(k) is None for k in ['date','offset','deathdate','trigger'])
    assert [c.get('type') for c in pe.get('action_a').all('command')]==['supplies','dissent','make_puppet']
    assert not pe.get('action_b').all('command')
    assert len(pe.get('desc'))<=500 and len(pe.get('action_a').get('name'))<=58
    addition=f'\r\n\t\tevent = {{ tag = IND id = {EID} hour = 1 }}\r\n'.encode('ascii')
    reference=('\r\nevent = "'+REL.replace('/','\\')+'"\r\n').encode('ascii')
    edits=[scalar(h,'name','"'+TITLE+'"'),scalar(h,'optionfile','"scenarios\\save games\\'+DEST+'.cfg"'),
           (queue.end-1,queue.end-1,addition),(len(raw),len(raw),reference)]
    updated=replace(raw,edits)
    # Inverse edit proof without normalising or rewriting any game state.
    ordered=sorted(edits);shift=0;undo=[]
    for start,end,value in ordered:
        undo.append((start+shift,start+shift+len(value),raw[start:end]));shift+=len(value)-(end-start)
    assert replace(updated,undo)==raw
    check=parse(updated);assert check.all('event')[-1]==REL.replace('/','\\')
    q=check.get('globaldata').get('queued_events').all('event')
    assert sum(e.get('id')==str(EID) and e.get('hour')=='1' for e in q)==1
    out=ROOT/'build/settlement1p';out.mkdir(parents=True,exist_ok=True)
    files={MOD/REL:EVENT.encode('ascii'),dest:updated,dest.with_suffix('.eug.cfg'):source.with_suffix('.eug.cfg').read_bytes()}
    if any(p.exists() for p in files):raise ValueError('Correction output already exists; inspect before reapplying')
    sha=lambda b:hashlib.sha256(b).hexdigest()
    if source.read_bytes()!=raw:raise ValueError('Continuation save changed during preparation')
    report=dict(build='SETTLEMENT1P',source=str(source),output=str(dest),source_sha256=sha(raw),output_sha256=sha(updated),
                event_file=REL,event_id=EID,queued_hours_after_load=1,engine_tested=False,inverse_edit_proof=True,
                supplies_before=india.get('supplies'),supplies_after_accepting=str(Decimal(india.get('supplies'))-500),
                dissent_before=india.get('dissent'),dissent_after_accepting=str(Decimal(india.get('dissent'))+4),
                original_save_unchanged=True,scope='Save-specific native make_puppet command; no global event changes')
    for p,b in files.items():
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        if p.read_bytes()!=b:raise IOError('Write verification failed: '+str(p))
    assert source.read_bytes()==raw
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
