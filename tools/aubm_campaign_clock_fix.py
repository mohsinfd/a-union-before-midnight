"""CONTINUE1: resettable campaign clocks stored as integer flags.

One saved daily callback per running clock. Count=1 means zero elapsed days.
A restart while an old callback is pending discards that partial day, so an
old callback can never complete the new hold early. No timestamp dependency.
"""
from dh_save_spans import Node,parse,replace,walk

SOURCES=(9289900,9289910,9289920,9289930,9289934,9294010,9297000,
         9289940,9289942,9289944,9289946,9289948,9289950,9294018)
CALLBACKS=dict(zip(SOURCES,range(9398400,9398414)))
BOOT=9398414
NEW_EVENT_IDS=set(CALLBACKS.values())|{BOOT}
MARKER='# AUBM_CONTINUE1_SAVED_COUNTERS'
def count(i):return 'ind_c1_days_'+str(i)
def pending(i):return 'ind_c1_tick_'+str(i)
def skip(i):return 'ind_c1_partial_'+str(i)
def flag(k):return 'flag = '+k
def no(k):return 'NOT = { flag = '+k+' }'
def ge(i,d):return f'flag = {{ which = {count(i)} when = 1 value = {d+1} }}'
def cmd(typ,which,guard='',extra=''):
    return 'command = { '+('trigger = { '+guard+' } ' if guard else '')+'type = '+typ+' which = '+which+' '+extra+' }'
def acts(e):return [f.value for f in e.fields if (f.key or '').startswith('action')]
def token(t,n):return t[n.start:n.end]

def transform(files):
    out=dict(files);idx={}
    for p,t in files.items():
        for e in parse(t).all('event'):
            i=int(e.get('id'))
            if i in idx:raise ValueError('Duplicate ID '+str(i))
            idx[i]=(p,e)
    if NEW_EVENT_IDS&idx.keys():
        if not NEW_EVENT_IDS<=idx.keys() or not all(MARKER in token(files[idx[i][0]],idx[i][1]) for i in NEW_EVENT_IDS):
            raise ValueError('Partial/colliding CONTINUE1 clocks')
        return out,{}
    if not set(SOURCES)<=idx.keys():raise ValueError('Campaign clock source missing')
    watches={};guards={};limits={i:0 for i in SOURCES};edits={p:[] for p in files}
    for i in SOURCES:
        p,e=idx[i];t=files[p]
        setters=[c.get('which') for a in acts(e) for c in a.all('command') if c.get('type')=='setflag']
        if len(setters)!=1:raise ValueError('Unexpected clock start payload '+str(i))
        watches[i]=setters[0]
        if i in SOURCES[:7]:
            # Keep the original continuous-hold context, replacing only its
            # "not yet watching" predicate with the running-watch predicate.
            tr=e.get('trigger');raw=token(t,tr);changes=[]
            for n in walk(tr):
                notn=n.get('NOT')
                if isinstance(notn,Node) and len(notn.fields)==1 and notn.get('flag')==watches[i]:
                    f=n.field('NOT');changes.append((f.start-tr.start,f.end-tr.start,flag(watches[i])))
            if len(changes)!=1:raise ValueError('Cannot isolate hold watch '+str(i))
            guards[i]='AND = '+replace(raw,changes)
        else:
            # Protectorate reviews measure age, not uninterrupted peace.
            # Their existing final decision still checks current sovereignty.
            guards[i]=flag(watches[i])
        for a in acts(e):
            if not any(c.get('type')=='setflag' and c.get('which')==watches[i] for c in a.all('command')):continue
            commands=[cmd('setflag',count(i),extra='value = 1'),
                      cmd('setflag',skip(i),flag(pending(i))),
                      cmd('event',str(CALLBACKS[i]),no(pending(i)),'where = IND when = 1'),
                      cmd('setflag',pending(i))]
            edits[p].append((a.end-1,a.end-1,'\n'+'\n'.join(commands)+'\n'))
    # Replace all references, including progress-report buckets at 0/30/60d.
    for p,t in files.items():
        for e in parse(t).all('event'):
            for n in walk(e):
                for f in n.fields:
                    if f.key=='event' and isinstance(f.value,Node) and f.value.get('days') is not None:
                        i=int(f.value.get('id'))
                        if i in SOURCES:
                            days=int(f.value.get('days'));limits[i]=max(limits[i],days)
                            edits[p].append((f.start,f.end,ge(i,days)))
                if n.get('type')=='clrflag' and n.get('which') in watches.values():
                    i=next(i for i,w in watches.items() if w==n.get('which'))
                    guard=token(t,n.get('trigger'))[1:-1] if isinstance(n.get('trigger'),Node) else ''
                    edits[p].append((n.end,n.end,'\n'+cmd('clrflag',count(i),guard)))
    if any(v<=0 for v in limits.values()):raise ValueError('Missing clock duration')
    helpers=[];bootcmds=[];bootgates=[]
    for i in SOURCES:
        active=guards[i]+' NOT = { '+ge(i,limits[i])+' }'
        # A pending tick can see a new watch; skip its partial interval once.
        # Choose the entire transition before changing the counter. This works
        # whether command guards are evaluated before or during execution.
        again=cmd('event',str(CALLBACKS[i]),extra='where = IND when = 1')
        increment=cmd('setflag',count(i),extra='when = 1 value = 1')
        helpers.append(f'''event = {{
 {MARKER}
 id = {CALLBACKS[i]} country = IND random = no persistent = yes one_action = yes
 name = "AI_EVENT" style = 2
 action_a = {{ trigger = {{ {active} {flag(skip(i))} }} name = "AI_EVENT"
 {cmd('clrflag',skip(i))}
 {again}
 }}
 action_b = {{ trigger = {{ {active} {no(skip(i))} NOT = {{ {ge(i,limits[i]-1)} }} }} name = "AI_EVENT"
 {increment}
 {again}
 }}
 action_c = {{ trigger = {{ {active} {no(skip(i))} {ge(i,limits[i]-1)} }} name = "AI_EVENT"
 {increment}
 {cmd('clrflag',pending(i))}
 }}
 action_d = {{ trigger = {{ NOT = {{ AND = {{ {active} }} }} }} name = "AI_EVENT"
 {cmd('clrflag',pending(i))}
 {cmd('clrflag',skip(i))}
 {cmd('clrflag',count(i),'NOT = { '+ge(i,limits[i])+' }')}
 }}
}}
''')
        bg=guards[i]+' '+no(pending(i))+' NOT = { '+ge(i,limits[i])+' }'
        bootgates.append('AND = { '+bg+' }')
        # Preserve valid counters when recovering a lost callback. Unknown
        # legacy ages start at zero; never fabricate a completed campaign.
        bootcmds.extend([cmd('setflag',count(i),bg+' '+no(count(i)),'value = 1'),
                        cmd('event',str(CALLBACKS[i]),bg,'where = IND when = 1'),
                        cmd('setflag',pending(i),bg)])
    helpers.append(f'''event = {{
 {MARKER}
 id = {BOOT} country = IND random = no persistent = yes one_action = yes
 name = "AI_EVENT" style = 2
 trigger = {{ OR = {{ {' '.join(bootgates)} }} }}
 date = {{ day = 0 month = january year = 1933 }} offset = 1
 deathdate = {{ day = 29 month = december year = 1964 }}
 action_a = {{ name = "AI_EVENT"
 {chr(10).join(bootcmds)}
 }}
}}
''')
    for p,es in edits.items():
        if es:out[p]=replace(files[p],es)
    out[idx[SOURCES[0]][0]]+='\n'+'\n'.join(helpers)
    return out,{i:[dict(dimension='campaign_clock',status='reviewed',days=limits[i],watch=watches[i],
                       changes='Saved counter; guarded daily tick; loss/reset invalidates partial time')] for i in SOURCES}
