"""Pure module46 regional armistice lifecycle; apply AFTER withdrawal safety.

Ten country-owned offer/selected-answer/ratification tokens; one outstanding
regional proposal and the existing90-day retry timer. No new IDs or new queues
beyond the existing response/ratification/retry calls. Full/limited dissent
rewards are deferred to actual peace, not paid before a cancellable ratification.
Foreign access already granted is not silently revoked on withdrawal.

Shared callback IDs have no native sender/generation payload. Selected tokens
separate an old reply from a new unanswered offer, but cannot prove provenance
when an old delivery coincides with a new SAME OUTCOME selected token. This is
explicitly unresolved, including shared retry delivery generations. Native
peace and sequential post-peace command checks need engine validation.
"""
import json
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate

MARKER='# AUBM_STAGED_REGIONAL_REPLIES_V1'
NEW_EVENT_IDS=frozenset()
TAGS=('CHI','CHC','SIA','ITA','FRA','TUR','POR','NZL','ETH','SAF')
NAMES=dict(zip(TAGS,('China','Communist China','Siam','Italy','France','Turkey','Portugal','New Zealand','Ethiopia','South Africa')))
PHASES=('offer','full','limited','refused','ratify_full','ratify_limited')
CAPITALS=dict(zip(TAGS,(1337,1354,1423,419,55,1075,476,1721,825,876)))
ROOTS=dict(zip(range(9282210,9282220),TAGS))
FOREIGN=dict(zip(range(9282220,9282230),TAGS))
LEGACY_IDS=frozenset(range(9282230,9282250))
SHARED_IDS=frozenset(range(9282260,9282265))
EDITED_IDS=frozenset(ROOTS)|frozenset(FOREIGN)|LEGACY_IDS|SHARED_IDS
OUT='ind_aubm_regional_armistice_outstanding'
RETRY='ind_aubm_regional_armistice_retry_pending'


def token(tag,phase):return 'ind_stage_regional_'+tag.lower()+'_'+phase
def target(tag):return 'ind_aubm_regional_armistice_target_'+tag.lower()
def flag(f):return 'flag = '+f
def either(parts):return 'OR = { '+' '.join('AND = { '+p+' }' for p in parts)+' }'
def cmd(kind,which='',value=None,trigger=None,when=None):
    return 'command = { '+('trigger = { '+trigger+' } ' if trigger else '')+'type = '+kind+(' which = '+which if which else '')+(' value = '+str(value) if value is not None else '')+(' when = '+str(when) if when is not None else '')+' }'
def later(eid,days):return cmd('event',str(eid)+' where = IND when = '+str(days))
def select(tag):
    return flag(OUT)+' '+flag(target(tag))+' '+' '.join('NOT = { '+flag(target(t))+' }' for t in TAGS if t!=tag)
def scope(tag):return f'exists = IND exists = {tag} NOT = {{ ispuppet = IND }}'
def detached(tag):return (f'NOT = {{ participant = {{ country = {tag} value = 4 }} }} '
                           f'NOT = {{ ispuppet = {tag} }}')
def live(tag):
    return (scope(tag)+' flag = ind_aubm_regional_current_'+tag.lower()+' owned = { province = '+str(CAPITALS[tag])+' data = '+tag+' } control = { province = '+str(CAPITALS[tag])+' data = IND } '+
        ('NOT = { flag = ind_exit_sia_verifying }' if tag=='SIA' else ''))
def owned(tag,phase):return flag(token(tag,phase))+' '+select(tag)
def valid(tag,phase):return owned(tag,phase)+' '+live(tag)


def cleanup(tag,phase,retry=False):
    # Shared flags belong to this selector, not merely any historical local token.
    identity=select(tag)
    commands=[]
    if retry:
        commands += [cmd('dissent',value=1,trigger=identity+' '+flag(token(tag,'refused'))),
            cmd('setflag',token(tag,'cooldown'),trigger=identity),
            cmd('setflag','ind_aubm_regional_retry_'+tag.lower(),trigger=identity),
            cmd('setflag',RETRY,trigger=identity),
            cmd('event','9282264 where = IND when = 90',trigger=identity)]
    for f in ('ind_aubm_regional_armistice_full','ind_aubm_regional_armistice_limited',OUT):
        # Clear OUT last among shared records; selector remains until afterward.
        commands.append(cmd('clrflag',f,trigger=identity))
    commands += [cmd('clrflag',target(tag)),cmd('clrflag',token(tag,phase))]
    return '\n'.join(commands)


def button(name,commands='',guard=None,chance=None,key='action'):
    for tag,label in NAMES.items():
        if name.startswith(tag+':'):name=label+name[len(tag):];break
    name=name.replace('agreement for ratification','terms to Delhi')
    return '\n '+key+' = { '+('trigger = { '+guard+' } ' if guard else '')+('ai_chance = '+str(chance)+' ' if chance is not None else '')+'name = '+json.dumps(name)+'\n'+commands+'\n }\n'
def shell(ev,choices,desc=None):
    return ('event = {\n'+MARKER+'\n id = '+ev.get('id')+' random = no persistent = yes country = '+ev.get('country')+'\n name = '+json.dumps(ev.get('name'))+'\n desc = '+json.dumps(desc or ev.get('desc'))+'\n style = 2 picture = '+json.dumps(ev.get('picture'))+'\n'+choices+'}\n')
def exits(tag,phase,human=True):
    v=valid(tag,phase)
    body=button(tag+': close the lapsed offer; retry in 90 days',cleanup(tag,phase,True),flag(token(tag,phase))+' NOT = { AND = { '+v+' } }',100)
    if human:body+=button(tag+': withdraw this offer; retry in 90 days',cleanup(tag,phase,True),'ai = no '+v,0)
    return body
def unowned(phases,tags=TAGS):
    return button('This reply has no matching offer; close without changes',guard='NOT = { '+either([flag(token(t,p)) for t in tags for p in phases])+' }',chance=100)


def shared(ev,eid):
    body=''
    if eid==9282264:
        for tag in TAGS:
            own=flag(token(tag,'cooldown'))
            # Reopen only still-valid original capital/war; expiry itself always
            # releases its token even if that country vanished during cooldown.
            commands=[cmd('event',str(9282210+TAGS.index(tag))+' where = IND when = 1',trigger=live(tag)+' NOT = { '+flag(OUT)+' }'),
                cmd('clrflag','ind_aubm_regional_retry_'+tag.lower()),cmd('clrflag',token(tag,'cooldown')),
                cmd('clrflag',RETRY,trigger='NOT = { '+either([flag(token(t,'cooldown')) for t in TAGS])+' }')]
            body+=button(tag+': the cooling period has ended','\n'.join(commands),own,100)
        return shell(ev,body+unowned(('cooldown',)), 'The recorded ninety-day cooling period has ended. Only that country file can reopen, and only while the current capital and war still support it. This notice cannot close a newer proposal.')
    phases={9282260:('ratify_full','ratify_limited'),9282261:('full',),9282262:('limited',),9282263:('refused',)}[eid]
    for tag in TAGS:
        for phase in phases:
            if eid==9282260:
                peace='NOT = { war = { country = IND country = '+tag+' } }'
                amount=-2 if phase=='ratify_full' else -1
                commands=[cmd('peace',tag,0),cmd('dissent',value=amount,trigger=peace)]
                if phase=='ratify_full':commands.append(cmd('setflag','ind_aubm_regional_armistice',trigger=peace))
                commands.append(cmd('setflag','ind_aubm_regional_settled_'+tag.lower(),trigger=peace))
                for suffix in ('pending','current','victory'):
                    commands.append(cmd('clrflag','ind_aubm_regional_'+suffix+'_'+tag.lower(),trigger=peace))
                commands.append(cmd('event','9282201 where = IND when = 3',trigger=peace))
                # If peace did not take, no settlement reward is paid. A short
                # retry interval still owns the same existing timer, not a loop.
                for command in (cmd('setflag',token(tag,'cooldown')),cmd('setflag',RETRY),cmd('setflag','ind_aubm_regional_retry_'+tag.lower()),later(9282264,90)):
                    n=parse(command).get('command')
                    command=replace(command,[gate(n,'war = { country = IND country = '+tag+' }')])
                    commands.append(command)
                commands.append(cleanup(tag,phase))
                title=tag+': ratify '+('full' if phase=='ratify_full' else 'limited')+' peace'
            elif eid==9282263:
                commands=[cleanup(tag,phase,True)]
                title=tag+': record refusal; retry in 90 days'
            else:
                commands=[cmd('setflag',token(tag,'ratify_'+phase)),cmd('clrflag',token(tag,phase)),later(9282260,1)]
                title=tag+': send the '+phase+' agreement for ratification'
            ratify_gate=valid(tag,phase)+((' '+detached(tag)) if eid==9282260 else '')
            body+=button(title,'\n'.join(commands),ratify_gate,100)+exits(tag,phase)
    descriptions={9282260:'Ratify only the country whose answer is recorded. India may remain in its coalition; an accepting affiliated opponent has already left its former master and alliance. Every unrelated Indian war continues. Settlement rewards follow peace. Withdrawal waits ninety days.',
        9282261:'The named respondent accepted the full terms. Delhi may ratify them or withdraw for ninety days. The original 2-dissent reduction is paid only when peace is made, not for opening this notice.',
        9282262:'The named respondent offered peace without access. Delhi may ratify or withdraw for ninety days. The original 1-dissent reduction follows peace. No unrelated proposal is closed.',
        9282263:'The recorded respondent refused. Recording the answer adds the original 1 dissent and begins a ninety-day cooling period. An obsolete reply cannot claim a newer unanswered proposal.'}
    return shell(ev,body+unowned(phases),descriptions[eid])


def transform(files:dict[str,str]):
    output,records=dict(files),{}
    for path,text in files.items():
        if str(path).replace('\\','/').rsplit('/',1)[-1]!='46_regional_campaigns.txt':continue
        edits=[]
        for ef in parse(text).fields:
            if ef.key!='event':continue
            eid=int(ef.value.get('id'))
            if eid not in EDITED_IDS:continue
            raw=text[ef.start:ef.end];ev=parse(raw).get('event')
            if MARKER in raw:
                records[eid]=[dict(dimension='regional_replies',status='ALREADY_APPLIED',path=path,actions=[])]
                continue
            if eid in ROOTS:
                tag=ROOTS[eid];a=ev.get('action_a')
                serialized='NOT = { '+flag(OUT)+' } NOT = { '+flag(RETRY)+' } NOT = { '+either([flag(token(t,'cooldown')) for t in TAGS])+' }'
                changes=[gate(a,live(tag)+' '+serialized),(a.end-1,a.end-1,'\n'+cmd('setflag',token(tag,'offer'))+'\n'),(ev.end-1,ev.end-1,'\n'+MARKER+'\n')]
                recovery='ai = no '+select(tag)+' '+either([flag(token(tag,p)) for p in PHASES])
                recovery_commands=cleanup(tag,'offer',True)+'\n'+'\n'.join(cmd('clrflag',token(tag,p)) for p in PHASES if p!='offer')
                changes.append((ev.end-1,ev.end-1,button(tag+': withdraw this offer; retry in 90 days',recovery_commands,recovery,0)))
                # These remain queued menus. A manual recovery entry must not
                # add date/offset/event-trigger filters to queued delivery.
                for key in ('decision','decision_trigger'):
                    f=next((f for f in ev.fields if f.key==key),None)
                    rule=recovery if f is None else 'OR = { AND = { '+raw[f.value.start+1:f.value.end-1]+' } AND = { '+recovery+' } }'
                    changes.append((f.value_start,f.end,'{ '+rule+' }') if f else (ev.end-1,ev.end-1,'\n'+key+' = { '+rule+' }\n'))
                if not any(not af.value.all('command') for af in actions(ev)):
                    changes.append((ev.end-1,ev.end-1,button('Leave this country file unchanged')))
                updated=replace(raw,changes);keys=['action_a']
            elif eid in FOREIGN:
                tag=FOREIGN[eid];body=''
                for key,phase in zip(('action_a','action_b','action_c'),('full','limited','refused')):
                    a=ev.get(key)
                    payload='\n'.join(raw[f.start:f.end] for f in a.fields if f.key=='command')
                    if phase in ('full','limited'):
                        payload+='\n'+cmd('end_puppet',trigger='ispuppet = '+tag)
                        payload+='\n'+cmd('leave_alliance',trigger='participant = { country = '+tag+' value = 4 }',when=1)
                    payload+='\n'+cmd('setflag',token(tag,phase))+'\n'+cmd('clrflag',token(tag,'offer'))
                    body+=button(a.get('name'),payload,valid(tag,'offer'),int(a.get('ai_chance')),key)
                updated=shell(ev,body+exits(tag,'offer',False)+unowned(('offer',),(tag,)))
                keys=['action_a','action_b','action_c','action[lapse]']
            elif eid in LEGACY_IDS:
                # No authored caller targets these replaced country-specific
                # reward-only leaves. Keep IDs callable, not an unowned payout.
                updated=shell(ev,button('This superseded reply has no matching offer'),'This old reply has been superseded by the country-owned ratification record. Closing pays no reward and changes no active proposal.')
                keys=['action[compatibility-close]']
            else:
                updated=shared(ev,eid);keys=['action['+tag+']' for tag in TAGS]
            parse(updated);edits.append((ef.start,ef.end,updated))
            records[eid]=[dict(dimension='regional_replies',status='CORRECTED_SCRIPT',path=path,actions=keys,
                detail='Country-owned offer, selected outcome and ratification stages; current sovereign peace scope/capital checks; exact cleanup and existing90-day retry. Foreign odds/access/relation retained. No free Cancel strands callbacks. Full/limited dissent rewards follow peace; no treaty downgrade. Unreachable legacy reward-only replies are harmless stubs.'),
                dict(dimension='regional_replies',status='UNRESOLVED',path=path,actions=[],detail='Shared IDs have no native sender/generation payload: old delivery overlapping a NEW SAME-OUTCOME token remains indistinguishable, even across countries. Existing-save tokens are not migrated. Owned manual withdrawal handles recipient disappearance; native visibility, peace success and sequential conditional-command evaluation need testing; no rollback of previously granted foreign access.')]
        output[path]=replace(text,edits)
    return output,records
