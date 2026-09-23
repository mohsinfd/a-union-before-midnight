"""CONTINUE1: one coherent orientation; negotiations retain their own guards."""
import json
from dh_save_spans import Node,parse,replace

MARKER='# AUBM_CONTINUE1_DIPLOMACY'
ORIENTATIONS=('ind_v3_non_aligned','ind_v3_allied_orientation','ind_v3_axis_orientation',
              'ind_v3_soviet_orientation','ind_v3_japanese_orientation','ind_v3_independent_asia')
PROGRAMS=('ind_v3_european_balance','ind_v3_asian_security','ind_v3_socialist_compact',
          'ind_v42_program_european','ind_v42_program_asian','ind_v42_program_socialist','ind_v42_program_nam')
EUROPE_GUARD=' '.join('NOT = { flag = '+f+' }' for f in (
    'ind_aubm_commitment_allied','ind_aubm_commitment_german','ind_aubm_commitment_soviet','ind_aubm_commitment_japan',
    'ind_aubm_diplomatic_negotiation_pending','ind_aubm_realignment_cooldown',
    'ind_v4_strategy_soviet','ind_v4_strategy_japan','ind_v4_strategy_nam','ind_v4_strategy_independent_asia',
    'ind_v3_non_aligned','ind_v3_soviet_orientation','ind_v3_japanese_orientation','ind_v3_independent_asia',
    'ind_v4a_treaty_commonwealth','ind_v4a_treaty_naval_compact','ind_v4a_treaty_formal_alliance','ind_v4a_treaty_cobelligerent',
    'ind_gc_formal_axis','ind_gc_cobelligerent','ind_v4_sov_equal_compact','ind_v4_sov_supervised_compact','ind_aubm_jp_partnership'))
EUROPE_GUARD+=' NOT = { participant = { country = IND value = 4 } }'
def command(kind,name):return f'command = {{ type = {kind} which = {name} }}'
def sync_program(orientation):
    selected=({'ind_v3_european_balance','ind_v42_program_european'} if orientation in ORIENTATIONS[1:3]
              else {'ind_v3_socialist_compact','ind_v42_program_socialist'} if orientation==ORIENTATIONS[3]
              else {'ind_v3_asian_security','ind_v42_program_asian'} if orientation in ORIENTATIONS[4:]
              else {'ind_v42_program_nam'})
    return '\n'.join(command('setflag' if f in selected else 'clrflag',f) for f in PROGRAMS)

def transform(files):
    out=dict(files);records={}
    for p,t in files.items():
        edits=[]
        for e in parse(t).all('event'):
            eid=int(e.get('id'))
            if eid not in {9270401,9280501,9280502,9281001}:continue
            if MARKER in t[e.start:e.end]:continue
            edits.append((e.start+1,e.start+1,'\n'+MARKER+'\n'))
            for af in e.fields:
                if not (af.key or '').startswith('action'):continue
                a=af.value
                if eid in {9280501,9280502}:
                    selected=[c.get('which') for c in a.all('command') if c.get('type')=='setflag' and c.get('which') in ORIENTATIONS]
                    if not selected:continue
                    if set(selected)=={'ind_v3_non_aligned','ind_v3_independent_asia'}:
                        orientation='ind_v3_independent_asia'
                    elif len(selected)==1:
                        orientation=selected[0]
                    else:raise ValueError('Ambiguous strategic orientation')
                    edits.append((a.end-1,a.end-1,'\n'+sync_program(orientation)+'\n'))
                if eid==9270401:
                    selected=[c.get('which') for c in a.all('command') if c.get('type')=='setflag' and c.get('which') in ORIENTATIONS]
                    if len(selected)!=1:raise ValueError('European option drift')
                    partner='ENG' if selected[0]==ORIENTATIONS[1] else 'GER'
                    guard=EUROPE_GUARD+' flag = ind_v3_european_balance NOT = { flag = ind_v3_european_partner } exists = '+partner+' NOT = { war = { country = IND country = '+partner+' } }'
                    tr=a.get('trigger')
                    if not isinstance(tr,Node):raise ValueError('European affordability guard missing')
                    edits.append((tr.start+1,tr.start+1,'\n'+guard+'\n'))
                    cmds='\n'.join(command('clrflag',f) for f in ORIENTATIONS if f!=selected[0])
                    edits.append((a.end-1,a.end-1,'\n'+cmds+'\n'+sync_program(selected[0])+'\n'))
            if eid==9270401:
                for key in ('decision','decision_trigger'):
                    n=e.get(key)
                    if not isinstance(n,Node):raise ValueError('European decision gate missing')
                    edits.append((n.start+1,n.start+1,'\n'+EUROPE_GUARD+'\n'))
            if eid==9281001:
                f=e.field('decision_desc');text='Permanent navigation menu, not an unresolved commitment. Opening or closing it changes no policy. Partner negotiations, strategic orientation and declarations of war remain separate choices.'
                edits.append((f.value_start,f.end,json.dumps(text)))
            records[eid]=[dict(dimension='diplomacy_consistency',status='reviewed',changes='Coherent legacy/current programme flags; stale European offers cannot overwrite another posture or commitment')]
        if edits:out[p]=replace(t,edits)
    return out,records
