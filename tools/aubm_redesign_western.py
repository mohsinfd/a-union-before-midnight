"""Bounded alternative British campaign, pure staged text transformation.

Western limited victory takes Aden, Suez and Mombasa; major victory adds Cape
Town. The original eastern route and its two-hinge major objective survive.
Historical milestone rewards are unchanged and do not repeat on recovery.
No peace commands or event IDs are added. Native play remains unverified.
"""
from itertools import combinations
from dh_save_spans import Node, parse, replace

MODULE = '45_enemy_campaigns.txt'
MARKER = '# AUBM_STAGED_WESTERN_BRITAIN_V1'
EDITED_IDS = frozenset((9282120,9282130,9282131,9282141,9282142))
CURRENT = 'ind_aubm_britain_current'
SUSPENDED = 'ind_aubm_britain_suspended'


def controls(*provinces):
    return ' '.join(f'control = {{ province = {p} data = IND }}' for p in provinces)


EAST = controls(1432,1438)+' OR = { '+controls(1053,900,842)+' }'
WEST = controls(1053,900,842)
LIMITED = 'OR = { AND = { '+EAST+' } AND = { '+WEST+' } }'
TWO_HINGES = 'OR = { '+' '.join('AND = { '+controls(*pair)+' }'
                              for pair in combinations((1053,900,880,29),2))+' }'
WEST_MAJOR = controls(900,880)+' OR = { '+controls(1053,29)+' }'
MAJOR = LIMITED+' OR = { AND = { '+EAST+' '+TWO_HINGES+' } AND = { '+WEST_MAJOR+' } }'
DESCRIPTIONS = {
    9282120: 'Limited victory: hold Singapore and Kuala Lumpur plus Aden, Suez or Mombasa; alternatively hold Aden, Suez and Mombasa. Major victory: keep a limited-victory map, then either the Straits and two imperial hinges, or Suez, Cape Town and Aden or London. Losing both qualifying routes suspends leverage, not earned history.',
    9282130: 'Britain has lost a vital sea route. India holds either Singapore and Kuala Lumpur with a western hinge, or the Aden-Suez-Mombasa corridor. Delhi can claim limited victory and bargaining leverage without fighting in both theatres. Earned victory credit survives a later reversal.',
    9282131: 'India holds a qualifying limited-victory map and deeper imperial objectives: the Straits with two hinges among Aden, Suez, Cape Town and London, or Suez and Cape Town with Aden or London. Britain faces a major Indian victory. Any negotiated peace still requires the separate armistice process.',
}


def aa(e):return [f.value for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]
def inner(text,n):return text[n.start+1:n.end-1]
def add_gate(text,n,rule):
    t=n.get('trigger')
    if not isinstance(t,Node):raise ValueError('Expected existing guarded command')
    return (t.start+1,t.start+1,' '+rule+' ')


def rewrite(raw,eid):
    if MARKER in raw:return raw
    e=parse(raw).get('event');edits=[]
    if eid in DESCRIPTIONS:
        f=e.field('desc');edits.append((f.value_start,f.end,'"'+DESCRIPTIONS[eid]+'"'))
    if eid==9282130:
        t=e.get('trigger')
        objectives=[f for f in t.fields if f.key in ('control','OR')]
        if len(objectives)!=3:raise ValueError('British limited objective drift')
        for f in objectives:edits.append((f.start,f.end,''))
        edits.append((t.end-1,t.end-1,'\n'+LIMITED+'\n'))
    elif eid==9282131:
        t=e.get('trigger');choices=[f for f in t.fields if f.key=='OR']
        if len(choices)!=1:raise ValueError('British major objective drift')
        f=choices[0];edits.append((f.start,f.end,MAJOR))
    elif eid in (9282141,9282142):
        losing=eid==9282141;identity=CURRENT if losing else SUSPENDED
        condition=('NOT = { '+LIMITED+' }') if losing else LIMITED
        branches=[f for f in e.get('trigger').get('OR').fields
                  if isinstance(f.value,Node) and f.value.get('flag')==identity]
        if len(branches)!=1:raise ValueError('British leverage branch drift')
        f=branches[0]
        edits.append((f.value.start+1,f.value.end-1,' flag = '+identity+' '+condition+' '))
        cs=[c for a in aa(e) for c in a.all('command')]
        clearing=[c for c in cs if c.get('type')=='clrflag' and c.get('which')==identity]
        if len(clearing)!=1:raise ValueError('British leverage clear drift')
        t=clearing[0].get('trigger')
        edits.append((t.start+1,t.end-1,' flag = '+identity+' '+condition+' '))
        companion=SUSPENDED if losing else CURRENT
        setting=[c for c in cs if c.get('type')=='setflag' and c.get('which')==companion]
        if len(setting)!=1:raise ValueError('British leverage restore drift')
        # Shared events may have fired for another opponent. Do not infer the
        # British map from a cleared/missing historical flag alone.
        edits.append(add_gate(raw,setting[0],condition))
    edits.append((e.end-1,e.end-1,'\n'+MARKER+'\n'))
    return replace(raw,edits)


def transform(files):
    output,records=dict(files),{}
    for path,text in files.items():
        if path.replace('\\','/').rsplit('/',1)[-1]!=MODULE:continue
        edits=[]
        for f in parse(text).fields:
            if f.key!='event':continue
            eid=int(f.value.get('id'))
            if eid not in EDITED_IDS:continue
            edits.append((f.start,f.end,rewrite(text[f.start:f.end],eid)))
            records[eid]=[dict(dimension='british_western_campaign',status='CORRECTED_SCRIPT',path=path,
                detail='Alternative three-objective western limited victory; Cape Town progression; shared loss/recovery use the same live map. Original reward amounts and historical one-time gates retained.',
                engine_tested=False,remaining=['Native campaign timing and player-visible presentation need validation.'])]
        output[path]=replace(text,edits)
    return output,records
