"""Compile CLEANUP1 over the authored sources into a separate reviewable overlay.

Generated country matrices remain generator-owned. This final, deterministic
pass enforces engine peace scope and human menu rules on their combined output.
Never edits an installed game or a save. Run install_aubm_cleanup.py separately.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re

from dh_save_spans import Node, parse, replace, walk

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build/cleanup1'
MAJORS = {'ENG', 'USA', 'GER', 'SOV', 'JAP'}
PREFIX = 'ind_cleanup1_'
HUBS = {'War Cabinet': 9297100, 'Campaigns': 9297101,
        'Peace Talks': 9297102, 'War Economy': 9297103}
GUIDES = {9289801, 9294030}


def body(text, node):
    if not isinstance(node,Node):return ''
    # Gates are re-embedded inline. Never let a source comment swallow closing
    # braces in their new context.
    return ' '.join(line.split('#',1)[0].strip() for line in text[node.start+1:node.end-1].splitlines()).strip()


def fields(node, key):
    return [f for f in node.fields if f.key == key]


def actions(node):
    return [f for f in node.fields if f.key == 'action' or (f.key or '').startswith('action_')]


def add_gate(text, node, gate):
    f = next((f for f in node.fields if f.key == 'trigger'), None)
    if f:
        return (f.value.start+1, f.value.start+1, '\n\t\t\t'+gate+'\n')
    return (node.start+1, node.start+1, '\n\t\ttrigger = { '+gate+' }\n')


def apply(text, edits):
    # The span parser uses character offsets for text, preserving original bytes
    # through Latin-1. Coalesce insertions so pass order remains deterministic.
    combined = {}
    for start, end, value in edits:
        if (start, end) in combined:
            if start != end:
                raise ValueError('Overlapping replacements')
            combined[start, end] += value
        else:
            combined[start, end] = value
    return replace(text, [(s,e,v) for (s,e),v in combined.items()])


def peace_gate(tag, *, major=False):
    gate = ('NOT = { ispuppet = IND } OR = { NOT = { participant = { country = IND value = 4 } } '
            'alliance_leader = { country = IND value = 0 } }')
    if not major:
        gate += f' NOT = {{ participant = {{ country = {tag} value = 4 }} ispuppet = {tag} }}'
    if tag == 'SIA':
        gate += (' NOT = { flag = ind_lib1_siam_break_pending'
                 ' flag = ind_lib1_siam_detached flag = ind_lib1_siam_protected }')
    return gate


def scoped_peace(text, filename):
    """Gate the WHOLE action, including rewards/cleanup, not just peace command.

Major opponent settlements explicitly end that opponent's coalition war.
Generic regional offers are unavailable when either signatory is affiliated.
The new Siam/China/Indochina opponent-withdrawal chains use no Indian peace.
"""
    edits, count = [], 0
    for ev in parse(text).all('event'):
        if ev.get('country') != 'IND':
            continue
        event_rules = []
        for af in actions(ev):
            a = af.value
            rules = []
            # These generic tables used to downgrade treaty flags to match
            # value=1 ejecting India. Full peace now preserves the alliance;
            # keep its recorded diplomatic status as well.
            if filename in ('46_regional_campaigns.txt','47_global_campaign_matrix.txt','49_bespoke_armistices.txt') and any(c.get('type')=='peace' for c in a.all('command')):
                treaty_flags={'ind_v4a_treaty_cobelligerent','ind_v4a_treaty_formal_alliance',
                    'ind_gc_cobelligerent','ind_gc_formal_axis','ind_v4_sov_equal_compact',
                    'ind_v4_sov_supervised_compact','ind_aubm_jp_partnership',
                    'ind_aubm_jp_independent_cobelligerent','ind_aubm_jp_formal_alliance',
                    'ind_v3_joined_allies','ind_v3_joined_axis','ind_v3_joined_comintern','ind_v3_joined_japan'}
                for cf in fields(a,'command'):
                    if cf.value.get('type') in ('setflag','clrflag') and cf.value.get('which') in treaty_flags:
                        edits.append((cf.start,cf.end,''))
            for command in a.all('command'):
                if command.get('type') == 'peace':
                    tag = command.get('which')
                    major = tag in MAJORS and filename != '47_global_campaign_matrix.txt'
                    gate = peace_gate(tag, major=major)
                    original = body(text, command.get('trigger'))
                    rules.append(f'OR = {{ NOT = {{ AND = {{ {original} }} }} AND = {{ {gate} }} }}' if original else gate)
                    count += 1
                    # The issuer is independent or leads its coalition. Full
                    # peace preserves that alliance; value=1 could eject India.
                    f=next((f for f in command.fields if f.key=='value'),None)
                    if f:edits.append((f.value_start,f.end,'0'))
                    else:edits.append((command.end-1,command.end-1,' value = 0 '))
                if command.get('type') == 'setflag':
                    m = re.fullmatch(r'ind_aubm_(?:regional_armistice|armistice|bespoke_armistice)_target_([a-z0-9]+)', command.get('which',''))
                    if m:
                        tag = m[1].upper()
                        rules.append(peace_gate(tag))
            if rules:
                rule = ' '.join(dict.fromkeys(rules))
                edits.append(add_gate(text, a, rule))
                event_rules.append(rule)
        if event_rules:
            desc = next((f for f in ev.fields if f.key == 'desc'), None)
            major_tags=sorted({c.get('which') for af in actions(ev) for c in af.value.all('command')
                               if c.get('type')=='peace' and c.get('which') in MAJORS})
            scope = (('Signing ends the war between India\'s side and '+', '.join(major_tags)+' and its coalition. India must be independent and either unallied or alliance leader. This is not a local peace.')
                     if major_tags and filename!='47_global_campaign_matrix.txt' else
                     'India signs for its side and must be independent and either unallied or alliance leader. The opponent must be independent and unallied. Japanese Siam uses End Japanese Rule. Cancel changes nothing.')
            if desc:
                old = desc.value
                # Remove assertions contradicted by the engine, retain objectives.
                old = re.sub(r'[^.]*\b(?:separate peace|pairwise|every other Indian war|all other wars|without affecting any other campaign|only this war|only the selected regional campaign)[^.]*\.', '', old, flags=re.I).strip()
                room=498-len(scope)-1
                if len(old)>room:old=old[:room].rsplit(' ',1)[0].rstrip('.,;:')+'.'
                edits.append((desc.value_start,desc.end,json.dumps((old+' '+scope).strip(),ensure_ascii=False)))
            fallback = ('\n\taction = {\n\t\ttrigger = { ai = no }\n'
                        '\t\tname = "Keep fighting - close these peace talks"\n')
            # Cancel an outstanding request only when the player chooses to close.
            flags = set()
            for n in walk(ev):
                for f in n.fields:
                    if f.key == 'flag' and isinstance(f.value,str) and ('armistice_target_' in f.value or f.value.endswith('armistice_outstanding')):
                        flags.add(f.value)
            for flag in sorted(flags):
                fallback += f'\t\tcommand = {{ type = clrflag which = {flag} }}\n'
            fallback += '\t}\n'
            edits.append((ev.end-1,ev.end-1,fallback))
            oa = next((f for f in ev.fields if f.key == 'one_action'),None)
            if oa:
                edits.append((oa.value_start,oa.end,'no'))
    return apply(text, edits), count


def date_gate(ev):
    months='january february march april may june july august september october november december'.split()
    def parts(node):
        year=int(node.get('year')); month=node.get('month','0')
        month=int(month) if month.isdigit() else months.index(month.lower())
        return year,month,int(node.get('day','0'))
    def since(y,m,d):
        # DH day/month/year comparisons mean "at least", not exact equality.
        return f'OR = {{ year = {y+1} AND = {{ year = {y} OR = {{ month = {m+1} AND = {{ month = {m} day = {d} }} }} }} }}' if m<11 else f'OR = {{ year = {y+1} AND = {{ year = {y} month = {m} day = {d} }} }}'
    result=[]
    if isinstance(ev.get('date'),Node):result.append(since(*parts(ev.get('date'))))
    if isinstance(ev.get('deathdate'),Node):
        y,m,d=parts(ev.get('deathdate'));d+=1
        if d>=30:m+=1;d=0
        if m>=12:y+=1;m=0
        result.append('NOT = { '+since(y,m,d)+' }')
    return ' '.join(result)


def category(eid, name, filename):
    if eid == 9297003:return 'Peace Talks'
    if eid in GUIDES:return 'Campaigns'
    if eid == 9281001:
        return 'War Cabinet'
    if re.search(r'peace|petition|treaty|ratif|independence|protector|settlement|congress|ending|Japanese Rule in Siam',name,re.I):
        return 'Peace Talks'
    if re.search(r'guide|progress|objective|campaign|mission|interven|war on|aggression',name,re.I):
        return 'Campaigns'
    if re.search(r'alli|diploma|strategy|mandate|pact|commitment|liberation programme',name,re.I):
        return 'War Cabinet'
    return 'War Economy'


def clean_name(name):
    name = re.sub(r'LIBERATOR\d\s*(?:[-:]\s*)?', '', name).strip()
    name = re.sub(r'\s*:\s*LIBERATOR\d', '', name).strip()
    return name.replace('Dockets','Plans').replace('dockets','plans').replace('docket','plan').replace('Authored ','')


def collect_decisions(files):
    result=[]
    for rel,text in sorted(files.items()):
        for ev in parse(text).all('event'):
            decision=ev.get('decision')
            if ev.get('country') != 'IND' or not isinstance(decision,Node):
                continue
            eid=int(ev.get('id')); name=clean_name(ev.get('name','Decision'))
            name={9289820:'Indonesia: ask the East Indies government',
                  9289822:'Indonesia: ask the Netherlands',
                  9289830:'Vietnam: ask the Indochina government',
                  9289832:'Vietnam: ask France'}.get(eid,name)
            selectable=body(text,ev.get('decision_trigger')) or body(text,ev.get('trigger'))
            gate=' '.join(x for x in (body(text,decision),selectable,date_gate(ev)) if x)
            single=ev.get('persistent')!='yes'
            if single:
                gate += f' NOT = {{ flag = {PREFIX}done_{eid} }}'
            # At least one substantive action must remain available. Do not
            # advertise an empty settlement when its engine-scope guard fails.
            actionable=[]
            for af in actions(ev):
                if af.value.all('command'):
                    actionable.append(body(text,af.value.get('trigger')))
            if actionable and all(actionable):
                gate+=' OR = { '+' '.join('AND = { '+g+' }' for g in actionable)+' }'
            result.append(dict(id=eid,name=name,gate=gate,group=category(eid,name,Path(rel).name),file=rel,single=single))
    return result


def navigation(text, decisions):
    by_id={d['id']:d for d in decisions}
    edits=[]
    for ev in parse(text).all('event'):
        if ev.get('country') != 'IND':continue
        eid=int(ev.get('id'))
        if eid in by_id:
            d=by_id[eid]; decision=ev.get('decision')
            edits.append((decision.start+1,decision.start+1,'\n\t\tflag = ind_cleanup1_loaded OR = { ai = yes atwar = no }\n'))
            if d['single']:
                done=f'NOT = {{ flag = {PREFIX}done_{eid} }}'
                edits.append((decision.start+1,decision.start+1,done+'\n'))
                edits.append(add_gate(text,ev,done))
                pf=next((f for f in ev.fields if f.key=='persistent'),None)
                if pf:edits.append((pf.value_start,pf.end,'yes'))
                else:edits.append((ev.start+1,ev.start+1,'\n persistent = yes\n'))
            # Calling a decision through an event bypasses its decision gate;
            # repeat original conditions at each state-changing action.
            for af in actions(ev):
                if af.value.all('command'):
                    edits.append(add_gate(text,af.value,'OR = { ai = yes AND = { '+d['gate']+' } }'))
                    if d['single']:
                        edits.append(add_gate(text,af.value,f'NOT = {{ flag = {PREFIX}done_{eid} }}'))
                        edits.append((af.value.end-1,af.value.end-1,f'\n command = {{ type = setflag which = {PREFIX}done_{eid} }}\n'))
        # Every navigable page has a human exit, even if source conditions
        # became false between opening and selecting it.
        if eid in by_id or eid in MENU_IDS:
            if not any(not af.value.all('command') and re.search(r'cancel|close',af.value.get('name',''),re.I) for af in actions(ev)):
                edits.append((ev.end-1,ev.end-1,'\n\taction = { trigger = { ai = no } ai_chance = 0 name = "Cancel - close without changes" }\n'))
            oa=next((f for f in ev.fields if f.key=='one_action'),None)
            if oa:edits.append((oa.value_start,oa.end,'no'))
        for af in actions(ev):
            if af.value.get('name')=='Cancel - close without changes':
                t=af.value.get('trigger')
                if not isinstance(t,Node) or t.get('ai')!='no':
                    edits.append(add_gate(text,af.value,'ai = no'))
            commands=af.value.all('command')
            # Pure page navigation only. No diplomatic replies, holds, rewards,
            # maintenance timers, or actions that change a flag are accelerated.
            if len(commands)==1 and commands[0].get('type')=='event' and commands[0].get('where')=='IND':
                c=commands[0]; target=int(c.get('which'))
                if c.get('when')=='1' and target in MENU_IDS:
                    f=c.field('when');edits.append((f.value_start,f.end,'0'))
        for f in ev.fields:
            if f.key in ('name','desc','decision_desc') and isinstance(f.value,str):
                value=clean_name(f.value)
                if value!=f.value:edits.append((f.value_start,f.end,json.dumps(value,ensure_ascii=False)))
    return apply(text,edits)


MENU_IDS=set()


def make_hubs(decisions):
    return compact_hubs(decisions)


def compact_hubs(decisions):
    """Direct task branches; compatibility pages only return to their parent."""
    from generate_aubm_liberator import event,action,later
    cancel=action('Cancel - close without changes',gate='ai = no',chance=0)
    result=[];next_id=9297120;by_id={d['id']:d for d in decisions}
    common='ai = no atwar = yes flag = ind_v3_started flag = ind_cleanup1_loaded'
    for name,eid in HUBS.items():
        # Preserve old IDs for queued/history references, but remove the maze.
        entries=[d for d in decisions if d['group']==name and d['id']!=9297003]
        for i in range(0,len(entries),5):
            result.append(event(next_id,'This menu has moved','Use the direct campaign, settlement or war economy menu.',[cancel,action('Open the main menu',later(eid,days=0))]));next_id+=1
    def link(eid,label,gate):return action(label,later(eid,days=0),gate=gate)
    war=lambda tag:f'war = {{ country = IND country = {tag} }}'
    campaigns=[cancel,
        link(9294031,'China: objectives and settlement',war('U87')),
        link(9294034,'Japan: home-island objectives',war('JAP')),
        link(9294035,'Indochina: objectives and settlement',war('U03')),
        link(9294032,'Soviet Union: objectives and settlement',war('SOV'))]
    talks=[cancel,
        link(9282212,'Thailand: choose its post-conquest government','NOT = { exists = SIA flag = ind_aubm_regional_settled_sia } owned = { province = 1423 data = IND }'),
        link(9297003,'Siam: demand an Indian puppet government','exists = SIA flag = ind_lib1_siam_hold_ready '+war('JAP')),
        link(9289903,'China: demand a protectorate','flag = ind_lib1_china_hold_ready NOT = { flag = ind_lib1_china_protectorate } '+war('JAP')),
        link(9289905,'China: confirm the agreed government','flag = ind_lib1_china_protection_consent NOT = { flag = ind_lib1_china_protectorate } '+war('JAP')),
        link(9294013,'Indochina: demand withdrawal from Japan','flag = ind_lib1_indo_hold_ready NOT = { flag = ind_lib1_indo_settled } '+war('JAP')),
        link(9294015,'Indochina: confirm the agreed government','flag = ind_lib1_indo_consent NOT = { flag = ind_lib1_indo_settled } '+war('JAP')),
        link(9289870,'Central Asia: reconstruct liberated republics','flag = ind_lib1_sov_hold_ready'),
        link(9289923,'Japan: choose the postwar investment','flag = ind_lib1_jap_hold_earned NOT = { '+war('JAP')+' }')]
    economy=[cancel]
    for i in (9280310,9280313,9280841,9280203,9289880,9270503):
        if i in by_id:economy.append(link(i,by_id[i]['name'].rstrip(':'),by_id[i]['gate']))
    # The old Cabinet ID remains callable but cannot offer new political routes
    # during an existing war. No resources or earned programmes are reversed.
    result.append(event(HUBS['War Cabinet'],'War Cabinet','During war, use Campaigns, Peace Talks and War Economy. Political realignment is closed.',[cancel],gate=common+' atwar = no',decision=True))
    for name,aa in (('Campaigns',campaigns),('Peace Talks',talks),('War Economy',economy)):
        result.append(event(HUBS[name],name,'Choose an available task. Completed settlements close their branch. Cancel changes nothing.',aa,gate=common,decision=True))
    return ('\n\n'+'\n\n'.join(result)+'\n').replace('year = 1940 }','year = 1933 }')


def legacy_hubs_reference(decisions):
    """Retained only as a reference for the compatibility ID allocation."""
    from generate_aubm_liberator import event,action,CANCEL,later
    CANCEL=action('Cancel - close without changes',gate='ai = no',chance=0)
    result=[];next_id=9297120
    for name,eid in HUBS.items():
        entries=[d for d in decisions if d['group']==name and d['id']!=9297003]
        siam=next((d for d in decisions if d['id']==9297003),None)
        # Source decisions retain their original conditions and one-shot state.
        pages=[]
        for i in range(0,len(entries),5):
            chunk=entries[i:i+5];pid=next_id;next_id+=1
            gate='OR = { '+' '.join('AND = { '+d['gate']+' }' for d in chunk)+' }'
            aa=[CANCEL]+[action(d['name'][:58],later(d['id'],days=0),gate=d['gate']) for d in chunk]
            aa.append(action('Back',later(eid,days=0)))
            result.append(event(pid,name+' - '+str(len(pages)+1),'Only available choices are shown. Reading a page takes no game time.',aa))
            pages.append((pid,gate,chunk))
        aa=[CANCEL]
        if name=='Peace Talks' and siam:
            aa.append(action('Siam: End Japanese Rule',later(siam['id'],days=0),gate=siam['gate']))
        if name=='Campaigns':
            aa += [action('Current objectives',later(9281913,days=0),gate='flag = ind_aubm_wartime_framework'),
                   action('Liberation progress',later(9294030,days=0),gate='flag = ind_lib1_enabled'),
                   action('Strategic route and partner requests',later(9289499,days=0),gate='flag = ind_aubm_wartime_framework')]
        for pid,gate,chunk in pages:
            source=Path(chunk[0]['file']).stem
            labels={'32_navy':'Navy','30_military':'Army','31_air_force':'Air force',
                    '40_special_units_and_capital_ships':'Special units and ships',
                    '43_wartime_settlements':'Liberation and settlements',
                    '44_wartime_economy':'Finance and wartime production',
                    '35_japan_partnership':'Relations with Japan',
                    '41_wartime_state':'War policy','18_manpower_reserves':'Manpower',
                    '20_procurement':'Procurement','26_grand_strategy':'Foreign policy'}
            title=chunk[0]['name'] if len(chunk)==1 else labels.get(source,' '.join(source.split('_')[1:]).capitalize())+' - '+str(pages.index((pid,gate,chunk))+1)
            # Routing has no gameplay effect. Do not concatenate every child
            # predicate into this tooltip: the 2026-09-08 dump shows rendered
            # condition text overwriting the engine's live game pointer.
            # Individual choices retain their original eligibility checks.
            aa.append(action(title,later(pid,days=0),gate='ai = no'))
        gate='ai = no atwar = yes flag = ind_v3_started flag = ind_cleanup1_loaded'
        # Four small navigation decisions remain visible during war. An empty
        # topic is safe to close; a 299 KB aggregate decision trigger is not.
        result.append(event(eid,name,'Choose a subject. Cancel closes the page without spending resources or changing policy.',aa,gate=gate,decision=True))
    return ('\n\n# CLEANUP1: four wartime decision groups\n'+'\n\n'.join(result)+'\n').replace('year = 1940 }','year = 1933 }')


def naval_events():
    from generate_aubm_liberator import event,action
    hulls='carrier light_carrier escort_carrier battleship battlecruiser heavy_cruiser light_cruiser destroyer submarine transport'.split()
    def delta(n):return [f'build_time which = {h} when = on_upgrade where = relative value = {n}' for h in hulls]
    # Existing construction-standard flags establish that exactly the old -50
    # has already been applied. Never reset technology or unrelated modifiers.
    mature='flag = ind_aubm_dockyard_efficiency_50'
    major='atwar = yes'
    return '\n\n'.join([
        event(9297180,'National dockyard schedules','Standard yards cut new-hull schedules by 25% of each class\'s first-model schedule. During war, emergency shifts add another 25%. Daily IC cost stays the same. Existing orders may keep their completion dates.',
            [action('Record the dockyard standard',f'setflag which = {PREFIX}naval_ready')],gate=f'{mature} NOT = {{ flag = {PREFIX}naval_ready }}',automatic=True,offset=1),
        event(9297181,'Return yards to normal shifts','The emergency schedule ends. The permanent 25% construction reduction remains.',
            [action('Return to normal shifts',*delta(25),f'setflag which = {PREFIX}naval_peace')],gate=f'{mature} flag = {PREFIX}naval_ready NOT = {{ {major} }} NOT = {{ flag = {PREFIX}naval_peace }}',automatic=True,offset=1),
        event(9297182,'Emergency dockyard shifts','India is at war. Priority steel, machinery and extra shifts restore the full 50% schedule reduction. Existing orders may keep their completion dates.',
            [action('Begin emergency shifts',*delta(-25),f'clrflag which = {PREFIX}naval_peace')],gate=f'{mature} flag = {PREFIX}naval_peace {major}',automatic=True,offset=1)
    ]).replace('year = 1940 }','year = 1933 }')


def fresh_naval(text):
    edits=[]
    for ev in parse(text).all('event'):
        if ev.get('id') not in ('9271111','9271112'):continue
        for af in actions(ev):
            for c in af.value.all('command'):
                if c.get('type')=='build_time':
                    f=c.field('value');edits.append((f.value_start,f.end,str(int(f.value)+25)))
            edits.append((af.value.end-1,af.value.end-1,
                '\n\t\tcommand = { type = setflag which = '+PREFIX+'naval_ready }'
                '\n\t\tcommand = { type = setflag which = '+PREFIX+'naval_peace }\n'))
        f=ev.field('desc');edits.append((f.value_start,f.end,json.dumps(
            'Standard yards reduce new-hull schedules by 25% of each class\'s first-model schedule. War unlocks another 25% through emergency shifts. Daily IC cost stays the same. Existing orders may retain their completion dates.')))
    return apply(text,edits)


def debt_cap(text):
    edits=[]
    for ev in parse(text).all('event'):
        if ev.get('id') not in ('9282080','9282081'):continue
        for af in actions(ev):
            if any(c.get('type')=='event' and c.get('which')=='9282090' for c in af.value.all('command')):
                edits.append(add_gate(text,af.value,'NOT = { flag = ind_aubm_debt_tier_4 flag = ind_aubm_debt_overhang }'))
        f=ev.field('desc');edits.append((f.value_start,f.end,json.dumps('Lenders refuse new loans at four outstanding debt levels or during a debt overhang. Repayment reopens borrowing. Taxation and ordinary revenue remain available. '+f.value[:325].rsplit(' ',1)[0].rstrip('.,;:')+'.')))
    return apply(text,edits)


def compile_files(files):
    global MENU_IDS
    files=dict(files)
    # Explicit menus plus events with no calendar trigger, whose commands only
    # navigate to Indian pages. Avoid treating timed callbacks as menus.
    from aubm_menu_safety import MENU_IDS as protected
    MENU_IDS=set().union(*protected.values())|{9281001,9289801,9289802,9289803,9289806,9289807,9289808,9294030}
    for text in files.values():
        for ev in parse(text).all('event'):
            if ev.get('country')=='IND' and not ev.get('date') and all(c.get('type')=='event' and c.get('where')=='IND' for a in actions(ev) for c in a.value.all('command')):
                MENU_IDS.add(int(ev.get('id')))
    count=0
    from aubm_shared_withdrawal import transform as shared_withdrawal
    settlement='db/events/aubm_v4/43_wartime_settlements.txt'
    files[settlement]=shared_withdrawal(files[settlement])
    from aubm_armistice_guards import guarded_callbacks
    from aubm_japan_war_guards import transform as japan_guards
    for rel,text in files.items():
        text=japan_guards(text)
        text=guarded_callbacks(text,Path(rel).name)
        text,n=scoped_peace(text,Path(rel).name);count+=n
        files[rel]=text
    decisions=collect_decisions(files)
    for rel,text in files.items():
        # Navigation extracts original gate before human wartime root hiding.
        text=navigation(text,decisions)
        # A navigation click must never let the player change political
        # programmes mid-war. These are the legacy coalition-choice pages.
        branch_edits=[]
        for ev in parse(text).all('event'):
            if ev.get('country')!='IND':continue
            if int(ev.get('id')) in (9281910,9281911,9281912,9281914):
                for af in actions(ev):
                    if any(c.get('type') not in ('event','trigger') for c in af.value.all('command')):
                        branch_edits.append(add_gate(text,af.value,'atwar = no'))
        text=apply(text,branch_edits)
        if rel.endswith('44_wartime_economy.txt'):text=debt_cap(text)
        if rel.endswith('india_v3/32_navy.txt'):text=fresh_naval(text)
        files[rel]=text
    rel='db/events/aubm_v4/32_national_consolidation.txt'
    files[rel]+=make_hubs(decisions)+naval_events()+release_notice(decisions)
    from aubm_cleanup_presentation import normalize
    files={rel:normalize(text) for rel,text in files.items()}
    return files,dict(decisions=len(decisions),peace_commands_guarded=count,roots=HUBS)


def load_sources():
    result={}
    for folder in ('india_v3','aubm_v4'):
        for p in sorted((ROOT/'mod/db/events'/folder).glob('*.txt')):
            result[p.relative_to(ROOT/'mod').as_posix()]=p.read_bytes().decode('latin1')
    return result


def release_notice(decisions):
    from generate_aubm_liberator import event,action
    return '\n\n'+event(9297190,'CLEANUP1 is loaded - playtest build',
        'This build adds the Siam breakaway settlement, four wartime decision groups, current-war checks and 25% peacetime / 50% wartime dockyard schedules. Existing units and earned rewards are kept. The new peace transition still needs an engine playtest. Your original save has not been overwritten.',
        [action('Continue the campaign',
            *(f'trigger = {{ event = {d["id"]} }} type = setflag which = {PREFIX}done_{d["id"]}' for d in decisions if d['single']),
            'setflag which = ind_cleanup1_loaded')],
        gate='ai = no flag = ind_v3_started NOT = { flag = ind_cleanup1_loaded }',automatic=True,offset=1).replace('year = 1940 }','year = 1933 }')+'\n'


def main():
    from install_aubm_liberator import TARGET
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=OUTPUT)
    ap.add_argument('--target',type=Path,default=TARGET);args=ap.parse_args()
    sources=load_sources();files,details=compile_files(sources)
    from aubm_stock_settlement_guard import apply_guard,apply_china_client_guard,apply_japan_client_guard
    stock={}
    for rel in ('db/events/japan.txt','db/events/china.txt'):
        raw=(args.target/rel).read_bytes();stock[rel]=raw.decode('latin1');sources[rel]=stock[rel]
        raw=apply_japan_client_guard(apply_guard(raw)) if rel.endswith('japan.txt') else apply_china_client_guard(raw)
        files[rel]=raw.decode('latin1')
    args.output.mkdir(parents=True,exist_ok=True)
    manifest={}
    for rel,text in files.items():
        p=args.output/'mod'/rel;p.parent.mkdir(parents=True,exist_ok=True)
        raw=text.encode('latin1');p.write_bytes(raw)
        manifest[rel]=dict(source=hashlib.sha256(sources[rel].encode('latin1')).hexdigest(),compiled=hashlib.sha256(raw).hexdigest(),origin='installed' if rel in stock else 'repository')
    details['files']=manifest;details['build']='CLEANUP1';details['engine_playtested']=False
    (args.output/'manifest.json').write_text(json.dumps(details,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in details.items() if k!='files'},indent=2))


if __name__=='__main__':main()
