"""Explicit full-peace authority across the loaded Indian peace commands.

No separate-peace promise: value0 is a coalition settlement. Independent India
must be unallied or lead its alliance. Generic minors must be independent and
unallied. Command effects/territorial terms are retained, but automatic treaty
downgrades matching the old value1 exit are removed. Engine peace outcomes are
not simulated or certified here.
"""
import re
from dh_save_spans import Node, parse, replace
from build_aubm_cleanup import peace_gate
from aubm_redesign_withdrawal import TREATY_DOWNGRADES, GENERIC_MARKER, GENERIC_IDS

MARKER = '# AUBM_STAGED_FULL_PEACE_V1'
MODULES = {'35_japan_partnership.txt','37_german_campaigns.txt','41_wartime_state.txt',
    '43_wartime_settlements.txt','45_enemy_campaigns.txt','46_regional_campaigns.txt',
    '47_global_campaign_matrix.txt','49_bespoke_armistices.txt'}
MAJORS = {'ENG','GER','SOV','JAP','USA'}
TARGET = re.compile(r'ind_aubm_(?:(?:regional_|major_|bespoke_)?armistice_target_|bespoke_target_)([a-z0-9]+)$')
RESTORATIONS = {9282020:'PER',9282022:'IRQ',9282030:'AFG',9282032:'TIB',9282034:'SIK'}


def restore_scope(eid,a,c,tag,module):
    rule=scope(tag,module)
    if RESTORATIONS.get(eid)!=tag:return rule
    creation=[x for x in a.all('command') if x.get('type')=='independence' and x.get('which')==tag]
    if not creation:return rule
    # No peace can execute while the respondent is absent. Prove that peace
    # occurs before restoration; never apply this exception to ordinary replies.
    t=c.get('trigger')
    if c.start>=creation[0].start or not isinstance(t,Node) or t.get('exists')!=tag or not t.get('war'):
        raise ValueError('Restore-before-peace ordering changed '+str(eid))
    return ('OR = { AND = { NOT = { exists = '+tag+' } exists = IND NOT = { ispuppet = IND } } '
            'AND = { '+rule+' } }')


def actions(e):return [f.value for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]
def body(text,n):return text[n.start+1:n.end-1] if isinstance(n,Node) else ''
def gate(text,n,rule):
    t=n.get('trigger')
    return (t.start+1,t.start+1,'\n'+rule+'\n') if isinstance(t,Node) else (n.start+1,n.start+1,'\ntrigger = { '+rule+' }\n')
def all_fields(n):
    for f in n.fields:
        yield f
        if isinstance(f.value,Node):yield from all_fields(f.value)
def selected(c):
    t=c.get('trigger')
    return sorted({f.value for f in all_fields(t) if f.key=='flag' and TARGET.fullmatch(f.value)}) if t else []


def scope(tag,module):
    major=tag in MAJORS and module!='47_global_campaign_matrix.txt'
    return f'exists = IND exists = {tag} '+peace_gate(tag,major=major)


def transform(files):
    output,records=dict(files),{}
    for path,text in files.items():
        module=path.replace('\\','/').rsplit('/',1)[-1]
        edits=[]
        for ef in parse(text).fields:
            if ef.key!='event' or ef.value.get('country')!='IND':continue
            e=ef.value;eid=int(e.get('id'))
            peace=[c for a in actions(e) for c in a.all('command') if c.get('type')=='peace']
            if not peace:continue
            if module not in MODULES:raise ValueError('Unregistered Indian peace module '+module)
            if eid in GENERIC_IDS and GENERIC_MARKER in text[ef.start:ef.end]:
                # The composed shared-minor pass already guards these complete
                # actions (including every regional selector). Do not double
                # the ten-country predicate in the same human tooltip.
                if any(c.get('value')!='0' for c in peace):raise ValueError('Minor peace scope drift')
                records[eid]=[dict(dimension='peace_scope',status='shared_minor_scope_preserved',path=path,
                    peace_commands=len(peace),engine_tested=False)]
                continue
            if MARKER in text[ef.start:ef.end]:
                records[eid]=[dict(dimension='peace_scope',status='already_applied',engine_tested=False)]
                continue
            targets=sorted({c.get('which') for c in peace})
            if any(not re.fullmatch('[A-Z][A-Z0-9]{2}',t or '') for t in targets):
                raise ValueError('Unsupported peace target '+str(eid))
            for a in actions(e):
                ps=[c for c in a.all('command') if c.get('type')=='peace']
                if not ps:continue
                rules=['exists = IND NOT = { ispuppet = IND }']
                selectors=sorted({s for c in ps for s in selected(c)})
                if selectors:
                    # Exactly one target owns a multi-country ratification.
                    rules.append('OR = { '+' '.join('flag = '+s for s in selectors)+' }')
                    for i,s in enumerate(selectors):
                        for other in selectors[i+1:]:rules.append('NOT = { AND = { flag = '+s+' flag = '+other+' } }')
                for c in ps:
                    tag=c.get('which');s=selected(c);rule=restore_scope(eid,a,c,tag,module)
                    if s:
                        if len(s)!=1:raise ValueError('Ambiguous peace selector '+str(eid))
                        rules.append('OR = { NOT = { flag = '+s[0]+' } AND = { '+rule+' } }')
                    elif len(ps)>1:
                        # Southern conference can settle several live wars;
                        # absent non-selected opponents must not block it.
                        original=body(text,c.get('trigger'))
                        if not original:raise ValueError('Unselected multi-peace '+str(eid))
                        rules.append('OR = { NOT = { AND = { '+original+' } } AND = { '+rule+' } }')
                    else:rules.append(rule)
                    f=next((f for f in c.fields if f.key=='value'),None)
                    edits.append((f.value_start,f.end,'0') if f else (c.end-1,c.end-1,' value = 0 '))
                edits.append(gate(text,a,' '.join(dict.fromkeys(rules))))
                # Full peace does not imply abandoning India's alliance.
                for f in a.fields:
                    if f.key!='command':continue
                    c=f.value
                    if (c.get('type') in ('setflag','clrflag') and c.get('which') in TREATY_DOWNGRADES) or c.get('type')=='leave_alliance':
                        edits.append((f.start,f.end,''))
            major=any(t in MAJORS for t in targets) and module!='47_global_campaign_matrix.txt'
            warning=('Signing settles the war between India\'s side and the named opponent\'s coalition. '
                     'India must be sovereign and either unallied or alliance leader. This is not a local ceasefire; India keeps its alliance.' if major else
                     'India must be sovereign and either unallied or alliance leader; the respondent must be independent and unallied. Signing ends this war for India\'s side without leaving its alliance. A Japanese-backed minor needs its withdrawal settlement first.')
            # Keep the actual narrative, move the clear scope warning into the
            # supported tooltip field. Contradictory legacy claims are replaced
            # explicitly only on central ratifiers/conference.
            if eid in (9281160,9282160,9282260,9282291):
                f=e.field('desc');edits.append((f.value_start,f.end,'"'+warning+'"'))
            elif 9286400<=eid<=9286609:
                f=e.field('desc')
                original=f.value
                needle='Delhi alone ratifies this pairwise settlement; every other Indian war and every earned route achievement remains live.'
                if needle not in original:raise ValueError('Global peace prose drift '+str(eid))
                revised=original.replace(needle,"India signs for its side, without leaving its alliance. India must be sovereign and unallied or alliance leader; the respondent must be independent and unallied. This is not a promise to preserve every other war.")
                edits.append((f.value_start,f.end,'"'+revised+'"'))
            elif eid==9281353:
                f=e.field('desc');edits.append((f.value_start,f.end,'"Germany is losing its hold on Europe. India can continue under sovereign command or seek a Soviet settlement. Signing peace requires India to be unallied or alliance leader and can end the wider coalition war; it is not a separate ceasefire."'))
                for a in actions(e):
                    if any(c.get('type')=='peace' for c in a.all('command')):
                        f=a.field('name');edits.append((f.value_start,f.end,'"Seek peace with Moscow for India\'s side"'))
            d=next((f for f in e.fields if f.key=='decision_desc'),None)
            if d:edits.append((d.value_start,d.end,'"'+warning+'"'))
            else:edits.append((e.start+1,e.start+1,'\ndecision_desc = "'+warning+'"\n'))
            if not any(not a.all('command') for a in actions(e)):
                edits.append((e.end-1,e.end-1,'\naction = { trigger = { ai = no } ai_chance = 0 name = "Close - sign nothing" }\n'))
            edits.append((e.end-1,e.end-1,'\n'+MARKER+'\n'))
            records[eid]=[dict(dimension='peace_scope',status='CORRECTED_SCRIPT',path=path,
                targets=targets,peace_commands=len(peace),engine_tested=False,
                detail='Whole-action full-peace authority, single selected target, alliance/treaty preservation. No guarantee of unrelated war preservation.',
                remaining=['Native full-peace, post-peace government rewards and foreign request/reply ownership need validation.'])]
        output[path]=replace(text,edits)
    return output,records
