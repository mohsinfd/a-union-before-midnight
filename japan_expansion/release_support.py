"""One bounded starter-support policy for every releasable Japanese partner.

Generated per tag because DH events require a concrete recipient country. These
are hidden technical handlers, not country routes or decision cards.
"""
from pathlib import Path
import csv,re,sys
from catalog import *
from runtime_paths import SOURCE
from runtime_paths import GAME
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from audit_japan_baseline import parse,get,getall,num

META={}


def rel(tag,keys=()):
    neutral=' '.join(f'AND = {{ flag = JX_{k}_NEUTRAL flag = JX_{k}_SETTLED access = {{ country = {tag} country = JAP }} access = {{ country = JAP country = {tag} }} NOT = {{ ispuppet = {tag} }} }}' for k in keys)
    choices=puppet(tag)+' '+neutral
    return f'flag = JX_ACTIVE exists = {tag} NOT = {{ {war(tag)} }} OR = {{ {choices} }}'


def short(flag_name):return 'flag = JX_'+flag_name


def receipt_guard(tag,part):return f'NOT = {{ flag = JX_AID_{tag}_{part}_DONE flag = JX_AID_{tag}_{part}_CLOSED }}'


def retry_actions(tag,part,good,success):
    prefix=f'AID_{tag}_{part}';again='relief_'+tag+'_'+part.lower()
    available=receipt_guard(tag,part)
    failed=available+' '+good+' NOT = { AND = { '+success+' } }'
    return [
        Action('',[flag(prefix+'_TRY1'),later(again,30,tag)],gate=failed+' NOT = { '+short(prefix+'_TRY1')+' }',chance=100),
        Action('',[flag(prefix+'_TRY2'),later(again,30,tag)],gate=failed+' '+short(prefix+'_TRY1')+' NOT = { '+short(prefix+'_TRY2')+' }',chance=100),
        Action('',[flag(prefix+'_CLOSED')],gate=failed+' '+short(prefix+'_TRY2'),chance=100),
        Action('',[flag(prefix+'_CLOSED')],gate=available+' NOT = { AND = { '+good+' } }',chance=100),
        Action('',[],gate='OR = { '+short(prefix+'_DONE')+' '+short(prefix+'_CLOSED')+' }')]


def append_events():
    if any(e.key.startswith('relief_') for e in EVENTS):return
    rev=parse((SOURCE/'db/revolt.txt').read_text(encoding='latin1'))
    rows={int(r['Id']):r for r in csv.DictReader((GAME/'map/Map_1/Province.csv').read_text(encoding='latin1').splitlines(),delimiter=';') if r.get('Id','').isdigit()}
    settlements={}
    for e in list(EVENTS):
        if e.module=='settlements' and e.key.endswith('_local'):settlements.setdefault(e.country,[]).append(e.key[:-6])
    archipelago={'INO','PHI','AST','NZL','CEY','HAW','MAD','CUB','ICL'}
    for tag,node in rev:
        if not re.fullmatch('[A-Z0-9]{3}',tag) or tag in {'JAP','MAN'}:continue
        provinces=list(dict.fromkeys(int(p) for f in ('minimum','extra') for _,p in get(node,f,[]) if str(p).isdigit() and int(p) in rows))
        if not provinces:continue
        cap=int(get(node,'capital',provinces[0]));ports=[p for p in provinces if rows[p].get('Port Allowed')=='1']
        keys=settlements.get(tag,[]);reserved=[]
        for key in keys:
            local=next(e for e in EVENTS if e.key==key+'_local')
            for command in local.actions[0].commands:
                if 'type = secedeprovince' in command:
                    n=parse(command);p=get(n,'value')
                    if str(p).isdigit() and rows[int(p)].get('Port Allowed')=='1':reserved.append((int(p),key))
        if tag=='U87':
            provinces=list(dict.fromkeys([1337]+[int(v) for _,v in get(node,'claims',[]) if str(v).isdigit()]))
            ports=[p for p in provinces if p in rows and rows[p].get('Port Allowed')=='1']
        small=len(provinces)<=8 and tag not in {'IND','U87'}
        tier='archipelago' if tag in archipelago else ('small_coastal' if small and ports else 'continental')
        maritime=bool(ports or reserved)
        transports,escorts=(120,25) if tier=='archipelago' else ((40,10) if maritime else (0,0))
        count,unit,model,cost,limit=(1,'garrison',4,8,2) if small else (2,'infantry',9,20,6)
        minimum={'supplies':1200 if tier=='archipelago' else 800,'money':75 if maritime else 50,
                 'manpower':30 if not small else 20,'oil':200 if maritime else 50}
        good=rel(tag,keys);key='relief_'+tag
        commands=[flag('AID_'+tag+'_STARTED')]
        for resource,amount in minimum.items():
            typ={'manpower':'manpowerpool','oil':'oilpool'}.get(resource,resource)
            commands.append(cond(f'NOT = {{ {resource} = {amount} }}',cmd(typ,value=amount)))
        for typ,amount in [('energypool',500),('metalpool',250),('rarematerialspool',100)]:commands.append(cmd(typ,value=amount))
        commands += [cond('NOT = { ic = 2 }',cmd('free_ic',value=1))]
        if maritime:
            commands += [cond(f'NOT = {{ convoypool = {transports} }}',cmd('transport_pool',which=-1,value=transports)),
                         cond(f'NOT = {{ escortpool = {escorts} }}',cmd('escort_pool',which=-1,value=escorts))]
        profile='partner_islands.ai' if tier=='archipelago' else ('partner_small.ai' if small else 'partner_land.ai')
        commands += [cond('NOT = { ic = 20 }',cmd('ai',which='"jx/'+profile+'"')),
                     fire(key+'_army')]
        if maritime:commands.append(fire(key+'_navy'))
        commands.append(flag('AID_'+tag+'_MAIN_DONE'))
        main_gate=good+' NOT = { '+short('AID_'+tag+'_MAIN_DONE')+' }'
        event(key,'Initial support for '+tag,'',country=tag,gate=main_gate,offset=3,
              actions=[Action('',commands,gate=main_gate,chance=100),Action('',[],gate='NOT = { AND = { '+main_gate+' } }')],module='release_support',
              purpose='One finite startup package after Japanese puppeting or a verified neutral agreement; also covers manual releases. MAN is excluded because it is a starting puppet.')
        sites=list(dict.fromkeys([cap]+provinces))
        valid_site='OR = { '+' '.join('AND = { '+owned(p,tag)+' '+control(p,tag)+' }' for p in sites)+' }'
        army_success=f'{valid_site} manpower = {cost} NOT = {{ army = {{ country = {tag} size = {limit} }} }}'
        site_flag='AID_'+tag+'_ARMY_SITE'
        army_commands=[cmd('manpowerpool',value=-cost),clear(site_flag)]
        for p in sites:
            army_commands.append(cond('NOT = { '+short(site_flag)+' } '+owned(p,tag)+' '+control(p,tag),cmd('setflag',which='JX_'+site_flag,value=p+1)))
        for p in sites:
            selected=f'flag = {{ which = JX_{site_flag} when = 0 value = {p+1} }}'
            army_commands.append(cond(selected,cmd('add_corps',which='"Local Defence Command"',value='land',where=p)))
            army_commands += [cond(selected,cmd('add_division',which=f'"Local Defence Formation {i+1}"',value=unit,when=model,where=-25)) for i in range(count)]
        army_commands += [flag('AID_'+tag+'_ARMY_DONE')]
        a=[Action('',army_commands,gate=receipt_guard(tag,'ARMY')+' '+good+' '+army_success,chance=100),
           Action('',[flag('AID_'+tag+'_ARMY_DONE')],gate=receipt_guard(tag,'ARMY')+' '+good+f' army = {{ country = {tag} size = {limit} }}',chance=100)]
        # Existing large armies close this branch, not trigger retries.
        a+=retry_actions(tag,'ARMY',good,f'OR = {{ AND = {{ {army_success} }} army = {{ country = {tag} size = {limit} }} }}')
        event(key+'_army','Local defence support','',country=tag,triggered=True,actions=a,module='release_support')
        if maritime:
            pick='AID_'+tag+'_PORT';need_tr='AID_'+tag+'_NEED_TRANSPORT';need_dd='AID_'+tag+'_NEED_ESCORT'
            commands=[clear(pick),clear(need_tr),clear(need_dd)]
            choices=[]
            for p in sorted(set(ports),key=lambda p:(p!=cap,p)):
                choices.append((p,owned(p,tag)+' '+control(p,tag)))
            for p,k in reserved:
                choices.append((p,short(k+'_BASES')+' '+owned(p)+' '+control(p)))
            # A tiny released island can have coast but no built port. Treaty
            # access/alliance permits a fleet to start at an operational Japanese
            # hub without stealing or fabricating local ownership.
            friendly=f'OR = {{ alliance = {{ country = {tag} country = JAP }} AND = {{ access = {{ country = {tag} country = JAP }} access = {{ country = JAP country = {tag} }} }} }}'
            for p in (1432,1653,1565,1511,1517,1399,1371,1667,1685,1554,1552):
                choices.append((p,friendly+' '+owned(p)+' '+control(p)))
            # Select exactly one operational port before any fleet command.
            for i,(p,condition) in enumerate(choices):
                selected=pick+'_'+str(i);commands.append(clear(selected))
                g=f'NOT = {{ {short(pick)} }} {condition} building = {{ province = {p} type = naval_base value = 1 when = now }}'
                commands += [cond(g,flag(selected)),cond(short(selected),flag(pick))]
            commands += [cond('NOT = { transport = { value = 1 when = now } } manpower = 2',flag(need_tr)),
                         cond('NOT = { destroyer = { value = 1 when = now } } OR = { AND = { transport = { value = 1 when = now } manpower = 1 } manpower = 3 }',flag(need_dd))]
            for i,(p,_) in enumerate(choices):
                selected=short(pick+'_'+str(i))
                commands += [cond(selected,cmd('add_corps',which='"Coastal Support Flotilla"',value='naval',where=p)),
                             cond(selected+' '+short(need_tr),cmd('add_division',which='"Coastal Transport Group"',value='transport',when=1,where=-25)),
                             cond(selected+' '+short(need_tr),cmd('manpowerpool',value=-2)),
                             cond(selected+' '+short(need_dd),cmd('add_division',which='"Coastal Escort Group"',value='destroyer',when=2,where=-25)),
                             cond(selected+' '+short(need_dd),cmd('manpowerpool',value=-1))]
            commands.append(later(key+'_navy_check',1,tag))
            event(key+'_navy','Deliver coastal support','',country=tag,triggered=True,
                  actions=[Action('',commands,gate=receipt_guard(tag,'NAVY')+' '+good,chance=100),
                           Action('',[],gate='NOT = { AND = { '+receipt_guard(tag,'NAVY')+' '+good+' } }')],module='release_support')
            success='transport = { value = 1 when = now } destroyer = { value = 1 when = now }'
            check=[Action('',[flag('AID_'+tag+'_NAVY_DONE')],gate=receipt_guard(tag,'NAVY')+' '+good+' '+success,chance=100)]
            check+=retry_actions(tag,'NAVY',good,success)
            event(key+'_navy_check','Check coastal support','',country=tag,triggered=True,actions=check,module='release_support')
        META[tag]={'tier':tier,'capital':cap,'ports':len(ports),'reserved_ports':reserved,'convoy_batch':transports,'escort_batch':escorts,
                   'army_units':count,'army_type':unit,'army_threshold':limit,'army_manpower':cost,'minimum':minimum}


def replace_old_support():
    """Keep settlement diplomacy intact; use one policy for actual aid."""
    for e in EVENTS:
        if e.module=='settlements' and e.key.endswith('_local'):
            kept=[]
            for c in e.actions[0].commands:
                n=parse(c);typ=get(n,'type')
                if typ in {'supplies','manpowerpool','ai'} or '_AID_GIVEN' in c or '_NAVAL_AID' in c or '_army' in str(get(n,'which')):continue
                kept.append(c)
            if e.country in META:kept.append(fire('relief_'+e.country))
            e.actions[0].commands=kept
            e.desc='The agreed government takes charge and grants access. Reserved bases transfer only under the agreed ownership checks. A separate one-time national support package supplies local defenders, stocks and, where appropriate, convoy ships and naval support. Existing forces and shipping are checked first.'
            confirmed=next(x for x in EVENTS if x.key==e.key[:-6]+'_confirmed')
            info=META[e.country]
            confirmed.desc='The agreed government, reciprocal access and reserved Japanese bases have been checked. A separate one-time support package checks existing forces and shipping. Small states can receive one garrison; larger states two infantry, at 75 percent strength, with recruitment and supply reserves. '+(f'This coastal state can receive a {info["convoy_batch"]}-transport and {info["escort_batch"]}-escort convoy batch when below its starter threshold. A troop transport and destroyer are checked separately and need an operational local or agreed Japanese base. ' if info['convoy_batch'] else '')+'Undelivered units retry at most twice after the first attempt. Japan\'s other wars continue.'
        elif e.module=='settlements' and e.key.endswith('_army'):
            # Old scheduled IDs are preserved and safely forward to the common
            # guarded policy, rather than maintaining a second grant system.
            if e.country in META:e.actions=[Action('',[fire('relief_'+e.country+'_army')],chance=100)]
        elif e.key in {'guangxi_local','yunnan_local'}:
            # Keep the paid development grant, but do not stack another partial
            # 20-MP/two-order army system on the common starter force.
            e.actions[0].commands=[c for c in e.actions[0].commands if get(parse(c),'type') not in {'manpowerpool','build_division','ai'}]+[fire('relief_'+e.country)]
            e.desc='The regional state receives the paid development grant and grants Japanese access. The common one-time starter policy checks its defenders, stocks and shipping; it does not add a second overlapping recruitment programme.'
    # Old delayed military reconstruction must not aid a state that has since
    # left Japan's protection or gone to war against Japan.
    for key,tag,marker in [('china_recovery','U87','CHINA_ARMY_RECOVERY'),('india_air_recovery','IND','INDIA_AIR_RECOVERY')]:
        e=next(x for x in EVENTS if x.key==key)
        valid=puppet(tag)+' NOT = { '+war(tag)+' '+short(marker)+' }'
        for a in e.actions:
            a.gate=(a.gate+' '+valid).strip();a.commands.insert(0,flag(marker))
            if key=='china_recovery':a.commands=[c.replace('type = manpowerpool value = 50','type = manpowerpool value = 80') for c in a.commands]
        e.actions.append(Action('',[],gate='NOT = { AND = { '+valid+' } }'))
    # International project awards execute immediately in their recipient's
    # context after the parent completion checks, avoiding a one-day gap.
    keys={e.key:e for e in EVENTS}
    for e in EVENTS:
        if not re.fullmatch(r'.+_finish_\d+',e.key):continue
        for a in e.actions:
            changed=[]
            for c in a.commands:
                n=parse(c);target=str(get(n,'which','')).removeprefix('@')
                child=keys.get(target)
                if get(n,'type')=='event' and child and child.country!=e.country:c=fire(target)
                changed.append(c)
            a.commands=changed


append_events()
