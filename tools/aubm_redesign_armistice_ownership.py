"""Country-owned global armistices, applied after full-peace scope.

The existing 90-day retry drains the normal 3+3-day reply path after withdrawal.
This is not generation tracking for arbitrary old saves or native queue proof.
No new events, flags, peace commands, costs or battlefield rewards are added.
"""
from dh_save_spans import Node, parse, replace
from generate_aubm_global_campaigns import COUNTRIES, lifecycle_ids
from aubm_redesign_peace_scope import scope, actions, body

MODULE = '47_global_campaign_matrix.txt'
MARKER = '# AUBM_STAGED_GLOBAL_ARMISTICE_OWNERSHIP_V1'
OUT = 'ind_aubm_universal_armistice_outstanding'
ROLES = ('docket', 'normal_response', 'backed_response', 'accept', 'counter',
         'refuse', 'lapse', 'retry_release')
REGISTRY = {getattr(lifecycle_ids(i), role): (c, role, lifecycle_ids(i))
            for i, c in enumerate(COUNTRIES) for role in ROLES}


def target(c): return 'ind_aubm_armistice_target_' + c.key
def retry(c): return 'ind_aubm_armistice_retry_' + c.key
def owner(c): return f'flag = {target(c)} flag = {OUT}'
def offer_scope(c): return f'exists = IND exists = {c.tag} NOT = {{ ispuppet = IND }}'
def detached(c):
    return (f'NOT = {{ participant = {{ country = {c.tag} value = 4 }} }} '
            f'NOT = {{ ispuppet = {c.tag} }}')
def live(c):
    return (f'{owner(c)} exists = {c.tag} war = {{ country = IND country = {c.tag} }} '
            f'owned = {{ province = {c.capital} data = {c.tag} }} '
            f'control = {{ province = {c.capital} data = IND }} ' + offer_scope(c))


def set_gate(raw, a, rule):
    t = a.get('trigger')
    return ((t.start+1, t.end-1, ' '+rule+' ') if isinstance(t, Node) else
            (a.start+1, a.start+1, '\ntrigger = { '+rule+' }\n'))


def close(rule='', foreign=False):
    return ('\naction = { '+('trigger = { '+rule+' } ' if rule else '')+
            ('ai_chance = 100 ' if foreign else 'ai_chance = 0 ')+
            'name = "Close window" }\n')


def withdraw(c, ids, rule=None):
    return ('\naction = { trigger = { '+(rule or owner(c))+' } ai_chance = 0 '
            'name = "Withdraw offer - retry in 90 days" '
            f'command = {{ type = setflag which = {retry(c)} }} '
            f'command = {{ type = event which = {ids.retry_release} where = IND when = 90 }} '
            f'command = {{ trigger = {{ flag = {target(c)} }} type = clrflag which = {OUT} }} '
            f'command = {{ type = clrflag which = {target(c)} }} '+'}\n')


def rewrite(raw, c, role, ids):
    e = parse(raw).get('event')
    if MARKER in raw: return raw
    aa = actions(e); edits = []; extra = ''
    own = owner(c); valid = live(c)
    lapse_rule = own+' NOT = { AND = { '+valid+' } }'
    for a in aa:
        cs = a.all('command')
        if not cs:
            f = a.field('name'); edits.append((f.value_start, f.end, '"Close window"'))
            continue
        queued = {int(x.get('which')) for x in cs if x.get('type') == 'event'}
        old = body(raw, a.get('trigger'))
        if role == 'docket':
            if ids.normal_response in queued or ids.backed_response in queued:
                rule = old+' '+offer_scope(c)+' NOT = { flag = '+target(c)+' }'
            elif ids.retry_release in queued:
                rule = old+f' NOT = {{ flag = {target(c)} }} NOT = {{ flag = {retry(c)} }}'
            else:
                # Docket navigation closes, never queues another menu.
                for f in a.fields:
                    if f.key == 'command': edits.append((f.start, f.end, ''))
                f = a.field('name'); edits.append((f.value_start, f.end, '"Close window"'))
                continue
        elif role in ('normal_response', 'backed_response', 'accept', 'counter', 'refuse'):
            if ids.lapse in queued:
                rule = lapse_rule
            elif role in ('accept','counter'):
                # Replace the earlier generic full-peace gate completely.  It
                # still contains the obsolete "India is alliance leader" rule.
                rule = valid+' '+detached(c)
            else:
                rule = old+' '+valid
            if role in ('normal_response','backed_response') and queued & {ids.accept,ids.counter}:
                edits.append((a.start+1,a.start+1,
                    f'\ncommand = {{ trigger = {{ ispuppet = {c.tag} }} type = end_puppet }}\n'
                    f'command = {{ trigger = {{ participant = {{ country = {c.tag} value = 4 }} }} type = leave_alliance when = 1 }}\n'))
        elif role == 'lapse':
            rule = own
            for cmd in cs:
                if cmd.get('type') == 'clrflag' and cmd.get('which') == retry(c):
                    f = cmd.field('type'); edits.append((f.value_start,f.end,'setflag'))
            edits.append((a.start+1,a.start+1,
                          f'\ncommand = {{ type = event which = {ids.retry_release} where = IND when = 90 }}\n'))
        else:
            rule = f'flag = {retry(c)} NOT = {{ flag = {target(c)} }}'
            for cmd in cs:
                if cmd.get('type') == 'event':
                    t = cmd.get('trigger')
                    edits.append((t.start+1,t.start+1,f' NOT = {{ flag = {OUT} }} '))
        edits.append(set_gate(raw, a, rule))
        # The shared clear explicitly belongs to this target. Keep its local
        # selector alive until all conditional commands have been evaluated.
        shared = [x for x in cs if x.get('type') == 'clrflag' and x.get('which') == OUT]
        if shared:
            for cmd in shared:
                t = cmd.get('trigger')
                if not isinstance(t, Node):
                    edits.append((cmd.start+1, cmd.start+1, f' trigger = {{ flag = {target(c)} }} '))
            for f in a.fields:
                if f.key == 'command' and f.value.get('type') == 'clrflag' and f.value.get('which') == target(c):
                    edits.append((f.start, f.end, ''))
                    edits.append((a.end-1, a.end-1, '\n'+raw[f.start:f.end]+'\n'))
    if role in ('docket','accept','counter'):
        extra += withdraw(c, ids)
    elif role == 'refuse':
        # A valid refusal keeps its authored relation/dissent consequences.
        extra += withdraw(c, ids, lapse_rule)
    if role in ('normal_response','backed_response','lapse'):
        extra += close('NOT = { AND = { '+own+' } }', role != 'lapse')
    elif role == 'retry_release':
        extra += close(f'NOT = {{ AND = {{ flag = {retry(c)} NOT = {{ flag = {target(c)} }} }} }}')
    elif not any(not a.all('command') for a in aa) and role != 'docket':
        extra += close()
    if role in ('docket','refuse'):
        note = ('Withdrawing this owned offer costs no resources, keeps its battlefield record, '
                'and blocks another offer to this country for 90 days. Closing the window leaves the offer pending.')
        d = e.get('decision_desc'); text = ((d+' ') if isinstance(d,str) else '')+note
        f = next((f for f in e.fields if f.key=='decision_desc'),None)
        edits.append((f.value_start,f.end,'"'+text+'"') if f else
                     (e.start+1,e.start+1,'\ndecision_desc = "'+text+'"\n'))
    if role in ('accept','counter'):
        f=e.field('desc')
        desc=(f'{c.name} has accepted country-specific terms. It has left any former master and alliance. '
              'Delhi can now ratify peace without India leaving its own coalition or ending unrelated wars.')
        edits.append((f.value_start,f.end,'"'+desc+'"'))
        d=next((x for x in e.fields if x.key=='decision_desc'),None)
        decision=('Ratify only this country file. India remains in its current alliance and every unrelated war continues. '
                  'Closing leaves the accepted terms pending; withdrawal reopens this country after ninety days.')
        edits.append((d.value_start,d.end,'"'+decision+'"') if d else
                     (e.start+1,e.start+1,'\ndecision_desc = "'+decision+'"\n'))
    if role == 'docket':
        if e.get('decision') is not None or e.get('decision_trigger') is not None:
            raise ValueError('Unexpected global docket decision; review existing access')
        # This same docket is also queued before an offer exists. Do not add
        # event-level trigger/date/offset filters to that original delivery.
        # Only its manual recovery entry requires the outstanding local owner.
        recovery = 'ai = no '+own
        edits.append((e.start+1,e.start+1,
                      '\ndecision = { '+recovery+' }\ndecision_trigger = { '+recovery+' }\n'))
        f = e.field('desc')
        desc = (f'India holds {c.seat}. Submit terms for a 60/25/15 response, improved to 75/20/5 '
                'by recognized standing. India may negotiate while serving in a coalition. An affiliated '
                'respondent that accepts first leaves its master and alliance; Delhi then makes peace without leaving its own coalition.')
        edits.append((f.value_start,f.end,'"'+desc+'"'))
    if role == 'lapse':
        f = e.field('desc')
        desc = ('Changed conditions suspend a surviving opponent\'s claim. An Indian-held annexed capital '
                'opens constitutional review; another annexing power resets this interrupted campaign. '
                'Earned rewards stay recorded. An owned offer waits 90 days before retry; an unowned reply changes nothing.')
        edits.append((f.value_start,f.end,'"'+desc+'"'))
    edits.append((e.end-1,e.end-1,extra+'\n'+MARKER+'\n'))
    return replace(raw, edits)


def transform(files):
    output, records = dict(files), {}
    for path, text in files.items():
        if path.replace('\\','/').rsplit('/',1)[-1] != MODULE: continue
        edits = []
        for f in parse(text).fields:
            if f.key != 'event': continue
            eid = int(f.value.get('id'))
            if eid not in REGISTRY: continue
            c, role, ids = REGISTRY[eid]
            edits.append((f.start,f.end,rewrite(text[f.start:f.end],c,role,ids)))
            records[eid] = [dict(dimension='armistice_ownership',status='CORRECTED_SCRIPT',
                target=c.tag,role=role,engine_tested=False,
                detail='Country-owned callbacks and explicit 90-day withdrawal; costs and response odds retained.',
                remaining=['Native queued delivery and UI pending; no arbitrary old-save generation proof.'])]
        output[path] = replace(text, edits)
    return output, records
