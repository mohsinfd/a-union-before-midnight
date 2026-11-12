"""Native-engine integrity corrections; apply last without allocating event IDs.

In particular, DH does NOT interpret an empty decision_trigger as true: it
falls back to trigger. Manual human offers disable their automatic trigger,
so every such card needs an explicit, nonempty readiness predicate.
"""
import re
from catalog import EVENTS, cmd

REPORT = {}


def negate(gate): return 'NOT = { AND = { ' + gate + ' } }'


def _current_infrastructure(text):
    """Patch only the four-predicate IC infrastructure FLOOR expression.

    Infrastructure expansion's separate capacity tests deliberately use maximum
    size, so replacing every infrastructure predicate would be incorrect.
    """
    def building(value):
        return (r'building\s*=\s*\{\s*province\s*=\s*\d+\s+type\s*=\s*infrastructure\s+value\s*=\s*'
                +value+r'(?:\s+when\s*=\s*\w+)?\s*\}')
    pattern=(r'OR\s*=\s*\{\s*AND\s*=\s*\{\s*NOT\s*=\s*\{\s*'+building('2')+r'\s*\}\s*'+building(r'0?\.31')+
             r'\s*\}\s*AND\s*=\s*\{\s*'+building('2')+r'\s*'+building('31')+r'\s*\}\s*\}')
    def floor(match):
        def now(b):
            body=b.group()
            if re.search(r'\bwhen\s*=',body):return re.sub(r'\bwhen\s*=\s*\w+','when = now',body)
            return body[:-1]+' when = now }'
        return re.sub(r'building\s*=\s*\{[^{}]*\}',now,match.group())
    return re.subn(pattern,floor,text)


def _guard_real_actions(e, extra):
    """Keep early direct/queued callbacks inert rather than refunding early."""
    for a in e.actions:
        if a.commands:
            a.gate = (a.gate + ' ' + extra).strip()
        else:
            a.gate = 'OR = { AND = { ' + a.gate + ' } ' + negate(extra) + ' }'


def apply():
    if REPORT:
        return REPORT
    from build import parse, get
    import regional_content
    before = {e.key:e.id for e in EVENTS}
    by = {e.key:e for e in EVENTS}
    ready=[];dated=[];infrastructure=[]
    for e in EVENTS:
        if e.decision and e.country=='JAP' and not e.ready.strip():
            # Visibility and option eligibility remain the material guards.
            # This merely prevents fallback to the deliberately disabled
            # AI-only automatic trigger. It is never an unconditional bypass.
            e.ready = f'year = {e.year}'
            ready.append(e.key)

    amphib=[]
    for e in EVENTS:
        if e.module!='prewar_content':continue
        for a in e.actions:
            for i,text in enumerate(a.commands):
                node=parse(text)
                if get(node,'type')=='max_amphib_mod' and get(node,'when')!='1':
                    a.commands[i]=cmd('max_amphib_mod',value=get(node,'value'),when=1)
                    amphib.append(e.key)

    for spec in regional_content.PROGRAMMES:
        parent=by[spec['key']]
        opening=f'year = {parent.year}'
        parent.gate+=' '+opening
        for a in parent.actions:a.gate+=' '+opening
        for i,option in enumerate(spec['choices']):
            child=by[spec['key']+'_finish_'+str(i)]
            elapsed=f'event = {{ id = @{spec["key"]} days = {option["days"]} }}'
            _guard_real_actions(child,elapsed)
            dated.append(child.key)

    # Revised Chinese aid crosses into a recipient country synchronously.
    # Its recipient must independently check elapsed time and the Japanese
    # controller; event-level dates/triggers cannot secure a forced receiver.
    aid_due='event = { id = @china_mission days = 60 }'
    for i in (0,1):
        _guard_real_actions(by['china_mission_finish_'+str(i)],aid_due)
        dated.append('china_mission_finish_'+str(i))
    jp='flag = JX_ACTIVE exists = JAP NOT = { ai = JAP ispuppet = JAP }'
    for key in ('china_mission_aid','china_mission_unit'):
        _guard_real_actions(by[key],aid_due+' '+jp)
        dated.append(key)

    for e in EVENTS:
        for field in ('gate','ready'):
            text,n=_current_infrastructure(getattr(e,field))
            if n:setattr(e,field,text);infrastructure.append((e.key,field,n))
        for i,a in enumerate(e.actions):
            a.gate,n=_current_infrastructure(a.gate)
            if n:infrastructure.append((e.key,'action_'+str(i),n))
            for j,text in enumerate(a.commands):
                a.commands[j],n=_current_infrastructure(text)
                if n:infrastructure.append((e.key,'command_'+str(i)+'_'+str(j),n))

    assert before=={e.key:e.id for e in EVENTS}
    REPORT.update(ready_filled=ready, elapsed_guarded=dated, amphib_fixed=amphib,
                  infrastructure_current_floors=infrastructure,
                  event_count=len(EVENTS),preserved_ids=len(before))
    return REPORT
