"""Owned eight-country armistices, pure staging; no new event IDs.

The shared retry event serializes the EXISTING global 90-day cooldown. Selected
answer tokens bind each callback to a target/outcome, not an engine generation.
Normal delivery is 2+2+1 days, followed by one day to verify peace and one day
to deliver foreign access/relations. These are script checks, not engine proof.
"""
from __future__ import annotations
import json
from dh_save_spans import Node, parse, replace
from build_aubm_cleanup import peace_gate

MARKER = '# AUBM_STAGED_BESPOKE_REPLIES_V1'
MODULE = '49_bespoke_armistices.txt'
TARGETS = dict(PER=1085, IRQ=1034, SAU=1045, YEM=1050, OMN=1052,
               AFG=2171, TIB=1289, SIK=1281)
NAMES = dict(PER='Persia', IRQ='Iraq', SAU='Saudi Arabia', YEM='Yemen',
             OMN='Oman', AFG='Afghanistan', TIB='Tibet', SIK='Xinjiang')
ROOTS = {9282270+i: tag for i,tag in enumerate(TARGETS)}
FOREIGN = {9282280+i: tag for i,tag in enumerate(TARGETS)}
IDS = (*ROOTS, 9282279, *FOREIGN, *range(9282288,9282293))
OUT = 'ind_aubm_bespoke_armistice_outstanding'
COOLING = 'ind_aubm_bespoke_retry_pending'


def flag(tag, kind):
    if kind in ('target','retry'):return 'ind_aubm_bespoke_'+kind+'_'+tag.lower()
    return 'ind_stage_bespoke_'+kind+'_'+tag.lower()


def has(name):return 'flag = '+name
def not_(predicate):return 'NOT = { '+predicate+' }'
def all_(parts):return 'AND = { '+' '.join(parts)+' }'
def any_(parts):return 'OR = { '+' '.join(parts)+' }'
def cmd(kind, which=None, value=None, guard=None, **extra):
    parts = ['type = '+kind]
    if which is not None:parts.append('which = '+str(which))
    if value is not None:parts.append('value = '+str(value))
    parts += [str(k)+' = '+str(v) for k,v in extra.items()]
    return 'command = { '+('trigger = { '+guard+' } ' if guard else '')+' '.join(parts)+' }'


def action(label, predicate, commands=(), chance=None):
    return ('action = { name = '+json.dumps(label)+' trigger = { '+predicate+' } '+
            (f'ai_chance = {chance} ' if chance is not None else '')+'\n'+'\n'.join(commands)+'\n}')


def actions(e):return [f for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]
def inner(text,node):return '\n'+text[node.start+1:node.end-1].strip()+'\n'


def set_fields(text, values):
    e=parse(text).get('event');edits=[]
    for key,value in values.items():
        f=next((f for f in e.fields if f.key==key),None)
        if f:edits.append((f.start,f.end,'') if value is None else (f.value_start,f.end,value))
        elif value is not None:edits.append((e.end-1,e.end-1,'\n'+key+' = '+value+'\n'))
    return replace(text,edits)


def set_actions(text, aa):
    e=parse(text).get('event')
    return replace(text,[(f.start,f.end,'') for f in actions(e)]+[(e.end-1,e.end-1,'\n'+'\n'.join(aa)+'\n')])


def owner(tag):
    return has(OUT)+' '+has(flag(tag,'target'))+' '+ ' '.join(
        not_(has(flag(other,'target'))) for other in TARGETS if other!=tag)


def authority(tag):
    return f'exists = IND exists = {tag} NOT = {{ ispuppet = IND }}'
def detached(tag):
    return (f'NOT = {{ participant = {{ country = {tag} value = 4 }} }} '
            f'NOT = {{ ispuppet = {tag} }}')
def war(tag):return f'war = {{ country = IND country = {tag} }}'
def battlefield(tag):
    province=TARGETS[tag]
    return (authority(tag)+' '+war(tag)+f' owned = {{ province = {province} data = {tag} }} '
            f'control = {{ province = {province} data = IND }} '
            +not_(has('ind_aubm_regional_settled_'+tag.lower())))


def unanswered(tag):return ' '.join(not_(has(flag(tag,kind))) for kind in ('full','limited','refused','ready','attempt'))
def reply(tag,kind):return owner(tag)+' '+has(flag(tag,kind))


def clear_owned(tag):
    # Action guards prove exact ownership. Global lock clears before target;
    # no unrelated target/cooldown, battlefield or treaty record is touched.
    return [cmd('clrflag',OUT), *[cmd('clrflag',flag(tag,k)) for k in
            ('full','limited','refused','ready','attempt')],
            cmd('clrflag','ind_aubm_bespoke_accept'), cmd('clrflag','ind_aubm_bespoke_counter'),
            cmd('clrflag',flag(tag,'target'))]


def withdraw(tag):
    # A refusal already selected by the respondent carries its authored cost
    # even if India withdraws through another window before reading the reply.
    return [cmd('dissent',value=1,guard=has(flag(tag,'refused'))),
            cmd('setflag',flag(tag,'retry')),cmd('setflag',COOLING),
            cmd('event',9282292,where='IND',when=90),*clear_owned(tag)]


def close():return action('Close window - change nothing','ai = no',chance=0)
def close_unmatched(proofs):
    return action('Close unmatched reply - change nothing','ai = no '+not_(any_([all_([p]) for p in proofs])),chance=0)
def owned_exits():
    # This helper belongs only to the shared ratifier. An unrelated old
    # ratifier callback must not expose withdrawal of a new unanswered offer.
    # The country's root decision retains broad owned recovery separately.
    return [action('Withdraw '+NAMES[tag]+' offer: 90-day wait',
            owner(tag)+' '+has(flag(tag,'ready'))+' '+any_([
                has(flag(tag,'full')),has(flag(tag,'limited'))]),withdraw(tag),0)
            for tag in TARGETS]+[close()]


def rewrite_root(text,tag):
    e=parse(text).get('event');offer=actions(e)[0]
    if offer.value.get('name')!='Submit an armistice: 60/25/15':raise ValueError('Bespoke offer changed')
    guard=inner(text,offer.value.get('trigger'))+' '+authority(tag)+' '+not_(has(COOLING))
    guard+=' '+' '.join(not_(has(flag(t,'target'))) for t in TARGETS)
    effects=[text[f.start:f.end] for f in offer.value.fields if f.key=='command'
             and not(f.value.get('type')=='setflag' and f.value.get('which')=='ind_aubm_global_campaign_victory')]
    availability=any_([all_([owner(tag)]),all_([guard]),*[all_([inner(text,f.value.get('trigger'))])
                      for f in actions(e)[1:] if isinstance(f.value.get('trigger'),Node)]])
    aa=[action('Offer peace: 60% full / 25% limited / 15% refusal',guard,effects)]
    aa += [text[f.start:f.end] for f in actions(e)[1:]]
    aa += [action('Withdraw this offer: 90-day wait',owner(tag),withdraw(tag),0),close()]
    text=set_actions(text,aa)
    return set_fields(text,{'persistent':'yes','decision':'{ ai = no '+availability+' }',
        'decision_trigger':'{ '+availability+' }','trigger':None,
        'decision_desc':json.dumps(
        'India may submit terms while serving in a coalition. If an affiliated opponent accepts, it first leaves its master and alliance; Delhi then ratifies peace without leaving its own coalition. Refusal or withdrawal pauses all eight bespoke offers for 90 days. Close changes nothing.')})


def rewrite_foreign(text,tag):
    valid=owner(tag)+' '+battlefield(tag)+' '+unanswered(tag)
    aa=[]
    for kind,chance,destination,label in (
        ('full',60,9282288,'Accept peace and Indian strategic access'),
        ('limited',25,9282289,'Counter with peace but no access'),
        ('refused',15,9282290,'Refuse this armistice')):
        # Acceptance benefits wait for the verified peace delivery phase.
        effects=[cmd('setflag',flag(tag,kind))]
        if kind in ('full','limited'):
            effects += [cmd('end_puppet',guard=f'ispuppet = {tag}'),
                        cmd('leave_alliance',guard=f'participant = {{ country = {tag} value = 4 }}',when=1)]
        if kind=='refused':effects.append(cmd('relation','IND',-30))
        effects.append(cmd('event',destination,where='IND',when=2))
        aa.append(action(label,valid,effects,chance))
    for kind in ('full','limited'):
        delivery=has(flag(tag,'deliver_'+kind))+' '+authority(tag)+' '+not_(war(tag))
        effects=([cmd('access','IND')] if kind=='full' else [])+[cmd('relation','IND',30 if kind=='full' else 10),
            cmd('clrflag',flag(tag,'deliver_'+kind))]
        aa.append(action('Deliver the signed '+kind+' settlement',delivery,effects,100))
    invalid=owner(tag)+' '+unanswered(tag)+' '+not_(all_([battlefield(tag)]))
    aa.append(action('The armistice conditions no longer hold',invalid,withdraw(tag),100))
    # A stale or displaced response cannot consume another offer or queue it.
    # General effect-free close also covers changed delivery authority; pending
    # delivery is not a campaign lock and can never grant goods without peace.
    aa.append(action('No applicable reply or delivery',not_(any_([
        all_([valid]),all_([invalid]),*[all_([has(flag(tag,'deliver_'+k)),authority(tag),not_(war(tag))])
                                    for k in ('full','limited')]])),(),0))
    return set_actions(text,aa)


def rewrite_receipt(text,kind):
    aa=[];proofs=[]
    for tag in TARGETS:
        proof=reply(tag,kind)+' '+not_(has(flag(tag,'ready')))+' '+not_(has(flag(tag,'attempt')))
        proofs.append(proof)
        valid=proof+' '+battlefield(tag)
        if kind=='refused':
            effects=withdraw(tag)
        else:
            effects=[cmd('setflag',flag(tag,'ready')),cmd('event',9282291,where='IND',when=1)]
        aa.append(action(NAMES[tag]+': record '+kind+' answer',valid,effects,100))
        aa.append(action(NAMES[tag]+': close invalid answer',proof+' '+not_(all_([battlefield(tag)])),withdraw(tag),100))
    return set_actions(text,aa+[close_unmatched(proofs)])


def rewrite_ratifier(text):
    aa=[]
    for tag in TARGETS:
        for kind,dissent in (('full',-2),('limited',-1)):
            proof=reply(tag,kind)+' '+has(flag(tag,'ready'))
            execute=proof+' '+not_(has(flag(tag,'attempt')))+' '+battlefield(tag)+' '+detached(tag)
            aa.append(action('Sign '+NAMES[tag]+' '+kind+' peace',execute,[
                cmd('peace',tag,0),cmd('setflag',flag(tag,'attempt')),
                cmd('event',9282291,where='IND',when=1)],100))
            success=proof+' '+has(flag(tag,'attempt'))+' '+authority(tag)+' '+not_(war(tag))
            effects=[cmd('dissent',value=dissent),cmd('setflag','ind_aubm_global_campaign_victory'),
                cmd('setflag','ind_aubm_bespoke_armistice'),
                cmd('setflag','ind_aubm_regional_settled_'+tag.lower()),
                cmd('setflag','ind_aubm_bespoke_negotiated_'+tag.lower())]
            effects += [cmd('clrflag','ind_aubm_regional_'+k+'_'+tag.lower())
                        for k in ('pending','current','victory','suspended')]
            effects += [cmd('setflag',flag(tag,'deliver_'+kind)),
                cmd('event',next(eid for eid,t in FOREIGN.items() if t==tag),where=tag,when=1),*clear_owned(tag)]
            aa.append(action(NAMES[tag]+': confirm observed '+kind+' peace',success,effects,100))
    return set_actions(text,aa+owned_exits())


def rewrite(text,eid):
    if MARKER in text:return text
    if eid in ROOTS:text=rewrite_root(text,ROOTS[eid])
    elif eid in FOREIGN:text=rewrite_foreign(text,FOREIGN[eid])
    elif eid in (9282288,9282289,9282290):text=rewrite_receipt(text,{9282288:'full',9282289:'limited',9282290:'refused'}[eid])
    elif eid==9282291:
        text=rewrite_ratifier(text)
        text=set_fields(text,{'desc':json.dumps("India signs for its side; this can end its coalition's war with the opponent. India keeps its alliance. Recognition waits for a next-day check that the war has ended; foreign access and relations arrive one day later. An uncompleted offer can be withdrawn, starting the eight-country 90-day cooling period.")})
    elif eid==9282279:
        aa=[]
        for tag in TARGETS:
            aa.append(action('Close vanished '+NAMES[tag]+' response',owner(tag)+' '+not_(f'exists = {tag}'),withdraw(tag),100))
        text=set_actions(text,aa+[close()])
    elif eid==9282292:
        aa=[]
        for tag in TARGETS:
            guard=has(COOLING)+' '+has(flag(tag,'retry'))+' '+not_(has(OUT))
            guard+=' '+' '.join(not_(has(flag(t,'target'))) for t in TARGETS)
            guard+=' '+' '.join(not_(has(flag(t,'retry'))) for t in TARGETS if t!=tag)
            aa.append(action('End '+NAMES[tag]+' cooling period',guard,
                [cmd('clrflag',flag(tag,'retry')),cmd('clrflag',COOLING)],100))
        text=set_actions(text,aa+[close()])
    if eid not in ROOTS:
        # Queued callbacks are never advertised as decisions. Vanished-country
        # polling remains authored and still requires its matching root trigger.
        text=set_fields(text,{'one_action':None,'decision':None,'decision_trigger':None,'persistent':'yes'})
    e=parse(text).get('event')
    return replace(text,[(e.end-1,e.end-1,'\n'+MARKER+'\n')])


def transform(files):
    output,records=dict(files),{}
    for path,text in files.items():
        if path.replace('\\','/').rsplit('/',1)[-1]!=MODULE:continue
        edits=[]
        for f in parse(text).fields:
            if f.key!='event':continue
            eid=int(f.value.get('id'))
            if eid not in IDS:continue
            if eid in records:raise ValueError('Duplicate bespoke reply '+str(eid))
            edits.append((f.start,f.end,rewrite(text[f.start:f.end],eid)))
            records[eid]=[dict(dimension='bespoke_replies',status='reviewed',path=path,
                changes='Exact owned target/outcome, current minor authority, peace-before-reward verification, serialized 90-day withdrawal',
                remaining=['Native peace, command reevaluation and queued callbacks require testing',
                    'Shared same-target/same-answer callbacks lack generation identity for arbitrary old saves',
                    'Constitutional restoration/protection action outcomes remain owned by other stages',
                    'No-owner or ambiguous old records close without clearing another transaction'],engine_tested=False)]
        output[path]=replace(text,edits)
    if set(records)!=set(IDS):raise ValueError('Incomplete bespoke replies: '+str(sorted(set(IDS)-set(records))))
    return output,records
