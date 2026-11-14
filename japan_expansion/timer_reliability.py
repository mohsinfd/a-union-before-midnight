"""Replace persistent-event history clocks with the engine's saved event queue.

The February 1934 R15 save proves that persistent funding events are absent
from both history and save_date. A delayed callback still arrives, but a
subsequent event={id=... days=...} test rejects its own receipt. Use finite
queued maturity flags instead. No rewards, bills or original IDs change.
"""
import re
from catalog import EVENTS, Action, event, cmd, cond, flag, clear, later, fire

REPORT = {}
PATTERN = re.compile(r'event\s*=\s*\{\s*id\s*=\s*"?(@?[\w]+)"?\s+days\s*=\s*(\d+)\s*\}')


def apply():
    if REPORT:return REPORT
    from build import parse, get, serialise
    original=list(EVENTS); by={e.key:e for e in original}
    by_id={str(e.id):e.key for e in original}
    def source_key(ref):return by_id.get(ref,ref.lstrip('@'))
    pairs={}; references={}
    for e in original:
        refs=set()
        for text in [e.gate,e.ready]+[a.gate for a in e.actions]+[c for a in e.actions for c in a.commands]:
            refs.update((source_key(m[1]),int(m[2])) for m in PATTERN.finditer(text))
        references[e.key]=refs
        for key,days in sorted(refs):
            if key not in by:raise ValueError('Unknown funding clock: '+key)
            pairs[(key,days)]='TIME_'+str(by[key].id)+'_'+str(days)

    def replace(text):
        return PATTERN.sub(lambda m:'flag = JX_'+pairs[(source_key(m[1]),int(m[2]))],text)

    # Receipts use an ordered handoff, not a redundant second queued event.
    # Separate timers are needed only for offers polled after an elapsed time,
    # or a reference with no matching delayed delivery to carry its maturity.
    covered=set()
    for e in original:
        for a in e.actions:
            issued={e.key}
            for text in a.commands:
                node=parse(text)
                if get(node,'type')=='trigger':issued.add(str(get(node,'which','')).lstrip('@'))
            for text in a.commands:
                node=parse(text)
                target=str(get(node,'which','')).lstrip('@')
                if get(node,'type')=='event' and target in references:
                    delay=int(get(node,'when','0'))
                    covered.update(pair for pair in references[target] if pair[0] in issued and pair[1]<=delay)
    autonomous=set().union(*(references[e.key] for e in original if not e.triggered))
    needed=autonomous | (set(pairs)-covered)
    timers={}
    for (key,days),name in sorted(pairs.items()):
        if (key,days) not in needed:continue
        timer='time_'+str(by[key].id)+'_'+str(days)
        timers[(key,days)]=timer
        # Keep elapsed clocks alive if a Chinese/Indian recipient disappears;
        # Japan's existing government-loss watcher must still refund the bill.
        e=event(timer,'Military preparations','',country='JAP',
                triggered=True,module='timer_reliability',
                actions=[Action('',[flag(name)],chance=100)],
                purpose='Saved native queue matures a finite elapsed-time flag.')
        e.engine_hidden=True

    armed=[]; deliveries=[]; changed=[]
    for e in original:
        own=[(pair,name) for pair,name in sorted(pairs.items()) if pair[0]==e.key and pair in timers]
        for index,a in enumerate(e.actions):
            before=list(a.commands)
            # Existing private clocks have an intentionally empty valid action.
            material=bool(before) or ('_clock_' in e.key and index==0)
            if own and material:
                gate=a.gate
                if not gate and before:
                    node=parse(before[0]); check=get(node,'trigger')
                    if isinstance(check,list):gate=serialise(check)
                start=[]
                for pair,name in own:
                    for command in (clear(name),later(timers[pair],pair[1],'JAP')):
                        start.append(cond(gate,command) if gate else command)
                a.commands=start+before
                armed.append((e.key,index))

            # A receipt and its maturity timer can share the same hour. Route
            # paid delayed receipts through a tiny ordered handoff so queue
            # ordering cannot select the empty action again.
            issued={e.key}
            for text in before:
                node=parse(text)
                if get(node,'type')=='trigger':issued.add(str(get(node,'which','')).lstrip('@'))
            for j,text in enumerate(a.commands):
                node=parse(text)
                if get(node,'type')!='event':continue
                target=str(get(node,'which','')).lstrip('@')
                if target not in references:continue
                delay=int(get(node,'when','0'))
                mature=sorted(pair for pair in references[target] if pair[0] in issued and pair[1]<=delay)
                if not mature:continue
                wrapper='time_delivery_'+str(e.id)+'_'+str(index)+'_'+str(j)
                receiver=event(wrapper,'Military preparations','',country=by[target].country,
                    triggered=True,module='timer_reliability',
                    actions=[Action('',[flag(pairs[pair]) for pair in mature]+[fire(target)],chance=100)],
                    purpose='Mature paid receipt before evaluating its original action guards.')
                receiver.engine_hidden=True
                node=[(k,'@'+wrapper if k=='which' else v) for k,v in node]
                a.commands[j]=serialise(node)
                deliveries.append(dict(source=e.key,choice=index,target=target,days=delay,
                                       flags=[pairs[pair] for pair in mature],wrapper=wrapper))
        old=(e.gate,e.ready,[(a.gate,list(a.commands)) for a in e.actions])
        e.gate=replace(e.gate);e.ready=replace(e.ready)
        for a in e.actions:
            a.gate=replace(a.gate);a.commands=[replace(c) for c in a.commands]
        if old!=(e.gate,e.ready,[(a.gate,list(a.commands)) for a in e.actions]):changed.append(e.key)
    assert all(not PATTERN.search(t) for e in EVENTS for t in
               [e.gate,e.ready]+[a.gate for a in e.actions]+[c for a in e.actions for c in a.commands])
    REPORT.update(pairs=[dict(source=k,days=d,flag=n,timer=timers.get((k,d))) for (k,d),n in sorted(pairs.items())],
                  original_ids={e.key:e.id for e in original},armed=armed,deliveries=deliveries,
                  changed=changed,events=len(EVENTS),game_launched=False)
    return REPORT
