"""Replace post-capital armistices with one atomic settlement system.

Every surviving state uses the same three player choices. Protection and
partnership absorb the defeated state and reconstitute it immediately, in the
same India event. There is no one-day gap in which an old alliance can restore
the pre-war map or redeploy Indian formations.
"""
from __future__ import annotations

import json
from dh_save_spans import Node, parse, replace
from generate_aubm_global_campaigns import COUNTRIES, lifecycle_ids
from aubm_redesign_regional_replies import TAGS as REGIONAL_TAGS, CAPITALS as REGIONAL_CAPITALS, ROOTS as REGIONAL_ROOTS, FOREIGN as REGIONAL_FOREIGN
from aubm_redesign_bespoke_replies import TARGETS as BESPOKE_TARGETS, ROOTS as BESPOKE_ROOTS, NAMES as BESPOKE_NAMES, FOREIGN as BESPOKE_FOREIGN

MARKER = "# AUBM_ATOMIC_RESOLUTION_OUTCOMES_V2"
GLOBAL_MODULE = "47_global_campaign_matrix.txt"
REGIONAL_MODULE = "46_regional_campaigns.txt"
BESPOKE_MODULE = "49_bespoke_armistices.txt"


def records():
    out=[]
    for i,c in enumerate(COUNTRIES):
        out.append((GLOBAL_MODULE,lifecycle_ids(i).docket,c.tag,c.name,c.capital,
                    9400000+i*2,9400001+i*2,"global"))
    regional_names=dict(CHI='China',CHC='Communist China',SIA='Siam',ITA='Italy',FRA='France',
                        TUR='Turkey',POR='Portugal',NZL='New Zealand',ETH='Ethiopia',SAF='South Africa')
    for i,tag in enumerate(REGIONAL_TAGS):
        root=next(e for e,t in REGIONAL_ROOTS.items() if t==tag)
        out.append((REGIONAL_MODULE,root,tag,regional_names[tag],REGIONAL_CAPITALS[tag],
                    9401000+i*2,9401001+i*2,"regional"))
    for i,(tag,cap) in enumerate(BESPOKE_TARGETS.items()):
        root=next(e for e,t in BESPOKE_ROOTS.items() if t==tag)
        out.append((BESPOKE_MODULE,root,tag,BESPOKE_NAMES[tag],cap,
                    9401100+i*2,9401101+i*2,"bespoke"))
    return tuple(out)


NEW_EVENT_IDS=frozenset(x for r in records() for x in r[5:7])
LEGACY_RATIFIERS={REGIONAL_MODULE:9282260,BESPOKE_MODULE:9282291}


def actions(e): return [f for f in e.fields if f.key=='action' or (f.key or '').startswith('action_')]
def command(kind,which=None,value=None,when=None,where=None,guard=None):
    bits=[]
    if guard: bits.append('trigger = { '+guard+' }')
    bits.append('type = '+kind)
    if which is not None: bits.append('which = '+str(which))
    if value is not None: bits.append('value = '+str(value))
    if where is not None: bits.append('where = '+str(where))
    if when is not None: bits.append('when = '+str(when))
    return '\t\tcommand = { '+' '.join(bits)+' }'
def action(name,gate,commands=(),chance=None):
    return ('\taction = {\n\t\tname = '+json.dumps(name)+'\n\t\ttrigger = { '+gate+' }\n'+
            ('\t\tai_chance = '+str(chance)+'\n' if chance is not None else '')+
            '\n'.join(commands)+'\n\t}')


def event_title(name, suffix, budget=58):
    """Keep generated event headings inside Darkest Hour's script budget."""
    title=f'{name}: {suffix}'
    if len(title.encode('utf-8')) <= budget:
        return title
    room=budget-len((': '+suffix).encode('utf-8'))
    kept=[]; used=0
    for word in name.split():
        cost=len(word.encode('utf-8'))+(1 if kept else 0)
        if used+cost > room: break
        kept.append(word); used += cost
    return f'{" ".join(kept) or name[:room]}: {suffix}'


def flags(tag,family):
    key=tag.lower(); protect='ind_stage_resolution_protect_'+key; partner='ind_stage_resolution_partner_'+key
    if family=='global':
        target='ind_aubm_armistice_target_'+key; outstanding='ind_aubm_universal_armistice_outstanding'
        settled='ind_aubm_global_settled_'+key
        clear=[f'ind_aubm_global_{x}_{key}' for x in ('pending','active','current','victory','suspended')]
        pflag='ind_aubm_global_protected_'+key; sflag='ind_aubm_global_sovereign_'+key
    elif family=='regional':
        target='ind_aubm_regional_armistice_target_'+key; outstanding='ind_aubm_regional_armistice_outstanding'
        settled='ind_aubm_regional_settled_'+key
        clear=[f'ind_aubm_regional_{x}_{key}' for x in ('pending','current','victory','suspended')]
        pflag='ind_aubm_regional_protected_'+key; sflag='ind_aubm_regional_sovereign_'+key
    else:
        target='ind_aubm_bespoke_target_'+key; outstanding='ind_aubm_bespoke_armistice_outstanding'
        settled='ind_aubm_regional_settled_'+key
        clear=[f'ind_aubm_regional_{x}_{key}' for x in ('pending','current','victory','suspended')]
        pflag='ind_aubm_bespoke_protected_'+key; sflag='ind_aubm_bespoke_sovereign_'+key
    return dict(protect=protect,partner=partner,target=target,outstanding=outstanding,
                settled=settled,clear=clear,pflag=pflag,sflag=sflag)


def owner(f): return f'flag = {f["target"]} flag = {f["outstanding"]}'
def objective(tag,cap,f):
    return (f'exists = IND exists = {tag} NOT = {{ ispuppet = IND }} '
            f'war = {{ country = IND country = {tag} }} '
            f'control = {{ province = {cap} data = IND }} NOT = {{ flag = {f["settled"]} }} '
            f'NOT = {{ flag = {f["outstanding"]} }}')


def rewrite_docket(raw,tag,name,cap,foreign_id,family):
    e=parse(raw).get('event'); f=flags(tag,family); keep=[]
    for af in actions(e):
        a=af.value
        # Preserve post-annex constitutional choices; the new surviving-state
        # choices replace only the random armistice and navigation clutter.
        if any(c.get('type')=='independence' and c.get('which')==tag for c in a.all('command')):
            keep.append(raw[af.start:af.end])
        elif any(c.get('type') in ('province_revoltrisk','belligerence') for c in a.all('command')) and 'Direct administration' in (a.get('name') or ''):
            keep.append(raw[af.start:af.end])
    base=objective(tag,cap,f)
    cleanup=[command('setflag',f['settled']),command('setflag','ind_aubm_global_campaign_victory')]
    if family=='bespoke': cleanup.append(command('setflag','ind_aubm_bespoke_negotiated_'+tag.lower()))
    cleanup += [command('clrflag',x) for x in f['clear']+[f['target'],f['outstanding'],f['protect'],f['partner']]]
    protect=[command('inherit',tag),command('independence',tag,value=1,when=0),
             command('make_puppet',tag),command('dissent',value=2),
             command('setflag',f['pflag']),*cleanup]
    partner=[command('inherit',tag),command('independence',tag,value=1,when=0),
             command('make_puppet',tag),command('end_mastery',tag),
             command('trigger',foreign_id),command('dissent',value=-1),
             command('setflag',f['sflag']),*cleanup]
    aa=[action('Indian protectorate: +2 dissent',base+' NOT = { flag = '+f['protect']+' flag = '+f['partner']+' }',protect),
        action('Independent partner: access, -1 dissent',base+' NOT = { flag = '+f['protect']+' flag = '+f['partner']+' }',partner),
        action('Continue the war toward annexation','ai = no '+base,())]+keep+[action('Close - change nothing','ai = no',())]
    edits=[(af.start,af.end,'') for af in actions(e)]
    for key,value in [('name',event_title(name,'Victory Settlement')),
                      ('desc',f'India controls {name}\'s capital. A full surrender absorbs and immediately rebuilds the defeated state as either an Indian protectorate or an independent partner with Indian access. This ends only that state\'s war; no old-alliance status quo and no delayed peace step are used.')]:
        field=e.field(key);edits.append((field.value_start,field.end,json.dumps(value)))
    edits.append((e.end-1,e.end-1,'\n'+'\n'.join(aa)+'\n'+MARKER+'\n'))
    return replace(raw,edits)


def foreign_event(eid,final_id,tag,name,cap,family):
    cmds=[command('access','IND'),
          command('leave_alliance',when=0,guard=f'participant = {{ country = {tag} value = 4 }}')]
    return f'''event = {{
\tid = {eid}
\trandom = no
\tpersistent = yes
\tone_action = yes
\tcountry = {tag}
\tname = "{event_title(name,'Independent Partner')}"
\tdesc = "The reconstituted government grants India military access before leaving any inherited alliance. No delayed peace or territorial reset is used."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
{action('Confirm independence and Indian access','OR = { ai = yes ai = no }',cmds,100)}
{MARKER}
}}
'''


def final_event(eid,tag,name,cap,family):
    f=flags(tag,family)
    invalid=[command('clrflag',x) for x in (f['protect'],f['partner'],f['target'],f['outstanding'])]
    return f'''event = {{
\tid = {eid}
\trandom = no
\tpersistent = yes
\tone_action = yes
\tcountry = IND
\tname = "{event_title(name,'Old Settlement Closed')}"
\tdesc = "This delayed settlement step has been retired. The atomic settlement is completed in the victory event itself."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
{action('Close the retired delayed file','OR = { ai = yes ai = no }',invalid,100)}
{MARKER}
}}
'''


def compatibility_event(raw, root_id, tag, name, family):
    """Turn an already queued legacy random reply into the new player docket."""
    e=parse(raw).get('event'); f=flags(tag,family)
    cmds=[command('clrflag',f['target']),command('clrflag',f['outstanding']),
          command('event',root_id,when=1,where='IND')]
    replacement=action('Return this file to Delhi for an explicit choice','OR = { ai = yes ai = no }',cmds,100)
    edits=[(af.start,af.end,'') for af in actions(e)]
    for key,value in [('name',event_title(name,'Old Reply Reopened')),
                      ('desc','The former random reply has been retired. No peace is imposed here. Delhi will choose protection, independent partnership with access, or continued war.')]:
        field=e.field(key); edits.append((field.value_start,field.end,json.dumps(value)))
    edits.append((e.end-1,e.end-1,'\n'+replacement+'\n'+MARKER+'\n'))
    return replace(raw,edits)


def retire_legacy_ratifier(raw,module):
    """Disable the old shared peace controllers retained by earlier builds."""
    e=parse(raw).get('event')
    families=('regional',) if module==REGIONAL_MODULE else ('bespoke',)
    stale=[]
    for rec in records():
        if rec[7] in families:
            f=flags(rec[2],rec[7])
            stale += [f['protect'],f['partner'],f['target'],*f['clear']]
    stale += (['ind_aubm_regional_armistice_outstanding'] if module==REGIONAL_MODULE
              else ['ind_aubm_bespoke_armistice_outstanding'])
    cmds=[command('clrflag',x) for x in dict.fromkeys(stale)]
    replacement=action('Close the retired armistice file','OR = { ai = yes ai = no }',cmds,100)
    edits=[(af.start,af.end,'') for af in actions(e)]
    for key,value in [('name','Retired Armistice Controller'),
                      ('desc','This old delayed peace system is disabled. Use the named country victory settlement; it resolves the target atomically and cannot restore an old alliance map.')]:
        field=e.field(key); edits.append((field.value_start,field.end,json.dumps(value)))
    edits.append((e.end-1,e.end-1,'\n'+replacement+'\n'+MARKER+'\n'))
    return replace(raw,edits)


def transform(files):
    output=dict(files); reviewed={}; by_module={}
    for rec in records(): by_module.setdefault(rec[0],[]).append(rec)
    for path,text in files.items():
        module=path.replace('\\','/').rsplit('/',1)[-1]
        if module not in by_module: continue
        if MARKER in text:
            continue
        index={int(f.value.get('id')):f for f in parse(text).fields if f.key=='event'}
        edits=[]; appended=[]
        for _,root,tag,name,cap,foreign_id,final_id,family in by_module[module]:
            field=index[root]
            edits.append((field.start,field.end,rewrite_docket(text[field.start:field.end],tag,name,cap,foreign_id,family)))
            appended += [foreign_event(foreign_id,final_id,tag,name,cap,family),final_event(final_id,tag,name,cap,family)]
            if family=='global':
                i=next(i for i,c in enumerate(COUNTRIES) if c.tag==tag)
                legacy=(lifecycle_ids(i).normal_response,lifecycle_ids(i).backed_response)
            elif family=='regional': legacy=tuple(eid for eid,t in REGIONAL_FOREIGN.items() if t==tag)
            else: legacy=tuple(eid for eid,t in BESPOKE_FOREIGN.items() if t==tag)
            for eid in legacy:
                if eid in index:
                    field=index[eid]
                    edits.append((field.start,field.end,compatibility_event(text[field.start:field.end],root,tag,name,family)))
            reviewed[root]=[dict(dimension='clear_resolution_outcomes',status='CORRECTED_SCRIPT',target=tag,
                detail='Explicit protected/partner/continue-war choice; immediate access; no random post-victory answer.',engine_tested=False)]
        ratifier_id=LEGACY_RATIFIERS.get(module)
        if ratifier_id in index:
            field=index[ratifier_id]
            edits.append((field.start,field.end,retire_legacy_ratifier(text[field.start:field.end],module)))
        updated=replace(text,edits)+'\n\n'+'\n'.join(appended)
        if module==REGIONAL_MODULE:
            board_desc={
                9282201:'Each action names its country. A surviving state appears only after India controls its listed capital. The country docket then offers protection, an independent partner with access, or continued war. Annexed states retain their constitutional choices.',
                9282202:'China and Siam use separate named country dockets. Protection creates an Indian puppet at +2 dissent; partnership preserves independence, grants Indian access and reduces dissent by 1; continued war leaves annexation open.',
                9282203:'Italy, France, Turkey and Portugal use separate named country dockets. No random reply is rolled and no unrelated Indian war ends.',
                9282204:'New Zealand, Ethiopia and South Africa use separate named country dockets. Australia and the colonial ocean states retain their dedicated Southern settlement.'}
            rootnode=parse(updated); desc_edits=[]
            for ef in rootnode.fields:
                if ef.key=='event' and int(ef.value.get('id')) in board_desc:
                    df=ef.value.field('desc'); desc_edits.append((df.value_start,df.end,json.dumps(board_desc[int(ef.value.get('id'))])))
            updated=replace(updated,desc_edits)
        output[path]=updated
    return output,reviewed
