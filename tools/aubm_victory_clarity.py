"""Remove the opaque coalition-credit roll after named battlefield victories."""
from __future__ import annotations

import json
from dh_save_spans import parse, replace

MODULE = "45_enemy_campaigns.txt"
SOVIET_MODULE = "43_wartime_settlements.txt"
MARKER = "# AUBM_VICTORY_CLARITY_V1"
RATIFY = 'OR = { NOT = { participant = { country = IND value = 4 } } alliance_leader = { country = IND value = 0 } }'


def action(name, commands="", trigger=None):
    gate=f'\n\t\ttrigger = {{ {trigger} }}' if trigger else ''
    return f'\taction = {{{gate}\n\t\tname = {json.dumps(name)}\n{commands}\n\t}}'


def event(eid, country, name, desc, actions):
    return f'''event = {{
\tid = {eid}
\trandom = no
\tpersistent = yes
\tone_action = yes
\tcountry = {country}
\tname = {json.dumps(name)}
\tdesc = {json.dumps(desc)}
\tstyle = 2
\tpicture = "aubm_v4_war_aims"
{actions}
{MARKER}
}}'''


def command(kind, which=None, when=None, where=None):
    bits=[f'type = {kind}']
    if which is not None: bits.append(f'which = {which}')
    if where is not None: bits.append(f'where = {where}')
    if when is not None: bits.append(f'when = {when}')
    return '\t\tcommand = { '+' '.join(bits)+' }'


def replacement(eid, country):
    if eid == 9282170:
        aa=action('Open the decisive armistice board now',
                  command('clrflag','ind_aubm_major_victory_pending')+'\n'+command('event',9282180,1,'IND'),
                  'flag = ind_aubm_major_victory_pending')
        aa+='\n'+action('The named victory and its rewards are already recorded','',
                         'NOT = { flag = ind_aubm_major_victory_pending }')
        return event(eid,country,'Victory Recorded: Choose the Next Step',
            'The preceding event named the opponent, the required cities and the reward. A decisive result opens that opponent\'s armistice board. A limited result needs no second ledger or partner roll.',aa)
    if 9282171 <= eid <= 9282175:
        aa=action('Return the obsolete request to Delhi',command('event',9282170,1,'IND'))
        return event(eid,country,'Old Coalition Roll Retired',
            'The random recognition roll has been removed. The battlefield result stands without asking an ally to validate it.',aa)
    aa=action('Close this obsolete notice','')
    return event(eid,country,'Old Coalition Credit Notice Retired',
        'This result belonged to the removed random partner-recognition system. It has no new effect; the original named battlefield reward remains valid.',aa)


def deterministic_reply(raw, desc):
    """Keep the accepted and invalid branches, removing the diplomatic dice roll."""
    e=parse(raw).get('event'); edits=[]; action_fields=[f for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]
    first=action_fields[0]
    chance=first.value.field('ai_chance')
    if chance: edits.append((chance.value_start,chance.end,'100'))
    for field in action_fields[1:]:
        if 'no longer valid' not in (field.value.get('name') or '').lower(): edits.append((field.start,field.end,''))
    df=e.field('desc'); edits.append((df.value_start,df.end,json.dumps(desc)))
    return replace(raw,edits)


def text_edits(raw, desc=None, action_names=None):
    e=parse(raw).get('event'); edits=[]
    if desc is not None:
        f=e.field('desc'); edits.append((f.value_start,f.end,json.dumps(desc)))
    for field in e.fields:
        if not (field.key=='action' or (field.key or '').startswith('action_')): continue
        old=field.value.get('name') or ''
        for needle,new in (action_names or {}).items():
            if needle in old:
                f=field.value.field('name'); edits.append((f.value_start,f.end,json.dumps(new)))
    return replace(raw,edits)


def require_ratification_authority(raw, indexes):
    e=parse(raw).get('event'); actions=[f.value for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]; edits=[]
    for index in indexes:
        trigger=actions[index].field('trigger')
        if trigger: edits.append((trigger.end-1,trigger.end-1,' '+RATIFY+' '))
    return replace(raw,edits)


def transform(files):
    output=dict(files); reviewed={}
    for path,text in files.items():
        module=path.replace('\\','/').rsplit('/',1)[-1]
        if module not in (MODULE,SOVIET_MODULE): continue
        if MARKER in text: continue
        root=parse(text); edits=[]
        for field in root.fields:
            if field.key != 'event': continue
            e=field.value; eid=int(e.get('id'))
            raw=text[field.start:field.end]
            if module==MODULE and 9282130 <= eid <= 9282140:
                node=parse(raw).get('event'); local=[]
                decisive='ind_aubm_major_victory_pending' in raw
                for cfield in node.fields:
                    if not (cfield.key=='action' or (cfield.key or '').startswith('action_')): continue
                    for cf in cfield.value.fields:
                        if cf.key=='command' and cf.value.get('type')=='event' and cf.value.get('which')=='9282170':
                            if decisive:
                                wf=cf.value.field('which'); local.append((wf.value_start,wf.end,'9282180'))
                                reviewed[eid]=[dict(dimension='victory_clarity',status='CORRECTED_SCRIPT',detail='Decisive victory opens its armistice board directly; no partner roll.',engine_tested=False)]
                            else:
                                local.append((cf.start,cf.end,''))
                                reviewed[eid]=[dict(dimension='victory_clarity',status='CORRECTED_SCRIPT',detail='Limited victory ends after its named tangible reward; no second ledger.',engine_tested=False)]
                edits.append((field.start,field.end,replace(raw,local)))
            elif module==MODULE and eid in set(range(9282170,9282176)) | {9282143,9282144,9282145}:
                edits.append((field.start,field.end,replacement(eid,e.get('country'))))
                reviewed[eid]=[dict(dimension='victory_clarity',status='CORRECTED_SCRIPT',detail='Opaque coalition-credit roll retired.',engine_tested=False)]
            elif module==MODULE and eid in (9282184,9282185,9282186,9282187):
                edits.append((field.start,field.end,deterministic_reply(raw,'The opponent accepts the full terms earned by India\'s decisive victory. No hidden acceptance roll remains. Delhi still performs the final peace and alliance-validity check.')))
                reviewed[eid]=[dict(dimension='victory_clarity',status='CORRECTED_SCRIPT',detail='Decisive great-power terms now receive a deterministic full reply.',engine_tested=False)]
            elif module==MODULE and eid in (9282181,9282182,9282188,9282189):
                updated=text_edits(raw,'A decisive Indian victory has unlocked full terms. Submit them for guaranteed acceptance, or continue the war. Final ratification still obeys the displayed alliance rule.',{'Submit the terms:':'Demand the full terms now'})
                updated=require_ratification_authority(updated,(0,))
                edits.append((field.start,field.end,updated))
            elif module==MODULE and eid==9282183:
                updated=text_edits(raw,'India may open the Japanese or American terms earned by its decisive Pacific victories. Each full offer is deterministic; unrelated wars continue.',{'Submit terms to Japan:':'Open Japan\'s full terms','Submit terms to America:':'Open America\'s full terms'})
                edits.append((field.start,field.end,updated))
            elif module==SOVIET_MODULE and eid in (9282037,9282038,9282039):
                edits.append((field.start,field.end,deterministic_reply(raw,'Moscow accepts the exact terms India selected after the required deep campaign. No hidden acceptance roll remains; invalid or lapsed claims still close safely.')))
                reviewed[eid]=[dict(dimension='victory_clarity',status='CORRECTED_SCRIPT',detail='Qualified Soviet settlement terms now receive a deterministic reply.',engine_tested=False)]
            elif module==SOVIET_MODULE and eid==9282036:
                updated=text_edits(raw,'Choose the constitutional result directly. Sovereign republics, protected republics and base rights retain their stated military requirements and costs; Moscow no longer rolls hidden acceptance odds. A formal alliance member must be alliance leader to sign.',{'Sovereign republics:':'Demand sovereign republics','Base-rights armistice:':'Demand a base-rights armistice'})
                updated=require_ratification_authority(updated,(0,1,2))
                edits.append((field.start,field.end,updated))
        output[path]=replace(text,edits)+'\n'+MARKER+'\n'
    return output,reviewed
