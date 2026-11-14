"""Finite recovery programmes after actual Japanese naval setbacks.

Only .apply() appends catalogue records. No install, save edit or game launch.
"""
from functools import lru_cache
import re
from catalog import EVENTS, Action, event, cmd, cond, flag, active, control, owned, war
from r14_peace import guarded_action
from r15_common import proposal

REPORT = {}
BASES = ((1667,'Truk'),(1726,'Rabaul'),(1432,'Singapore'),(1734,'Pearl Harbor'))
ASSEMBLY = 1552
MIN_MODELS = {'light_carrier':1,'light_cag':4,'destroyer':6,'naval_bomber':2,'multi_role':6,'marine':4,'transport':2}


def f(name):return 'flag = JX_'+name
def no(gate):return 'NOT = { AND = { '+gate+' } }'


def naval_war():
    return 'OR = { '+war('USA')+' '+war('ENG')+' }'


def fighting():
    return 'flag = JX_PACIFIC '+naval_war()


@lru_cache(maxsize=None)
def equipment(unit):
    """Read genuine B&I models/research, using only service dates through1950."""
    from build import SOURCE,read,parse,get,getall
    folder='brigades' if unit=='light_cag' else 'divisions'
    models=getall(parse(read(SOURCE/'db/units'/folder/(unit+'.txt'))),'model')
    unlocks=[]
    for p in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for app in getall(tree,'application'):
                year=int(get(app,'year',0));tech=int(get(app,'id'))
                if year>1950:continue
                for c in getall(get(app,'effects',[]),'command'):
                    if get(c,'type')=='new_model' and get(c,'which')==unit and not get(c,'trigger'):
                        model=int(get(c,'value'))
                        if model>=MIN_MODELS[unit]:unlocks.append((model,year,tech,float(get(models[model],'manpower'))))
    assert unlocks,unit
    return tuple(sorted(set(unlocks),reverse=True))


def latest(unit):
    prior=[]
    for model,year,tech,mp in equipment(unit):
        present=f'year = {year} technology = {tech}'
        gate=present
        if prior:gate+=' NOT = { OR = { '+' '.join('AND = { '+g+' }' for g in prior)+' } }'
        yield model,gate,mp
        prior.append(present)


def ready(unit):
    # Availability needs any eligible researched model, not the full mutually
    # exclusive delivery selectors. Keeping those separate avoids giant hovers.
    return 'OR = { '+' '.join(f'AND = {{ year = {year} technology = {tech} }}' for _,year,tech,_ in equipment(unit))+' }'


def home(branch):
    kind='naval_base' if branch=='naval' else 'air_base' if branch=='air' else None
    return owned(ASSEMBLY)+' '+control(ASSEMBLY)+(f' building = {{ province = {ASSEMBLY} type = {kind} value = 1 when = now }}' if kind else '')


def formation(unit,name,branch,*,new_corps=True):
    commands=[cmd('add_corps',which='"'+name+'"',value=branch,where=ASSEMBLY)] if new_corps else []
    for model,gate,_ in latest(unit):
        commands += [cond(gate,cmd('add_division',which='"'+name+'"',value=unit,when=model)),
                     cond(gate,cmd('damage_division',which='"'+name+'"',value='JAP',where=-100))]
    return commands


def carrier_crisis():
    return (fighting()+' losses = { country = JAP type = carrier value = 3 } '
            'NOT = { carrier = { country = JAP value = 4 when = now } }')


def lost_anchorage():
    # This is a recorded, verified capture, rather than a stale controller hint.
    return f('R15_ANCHORAGE_LOST')


@lru_cache(maxsize=1)
def country_tags():
    """Every native releasable or1933 country, not a hand-picked opponent list."""
    from build import SOURCE,read,parse,get
    tags={tag for tag,_ in parse(read(SOURCE/'db/revolt.txt')) if re.fullmatch(r'[A-Z0-9]{3}',tag)}
    for p in (SOURCE/'scenarios/1933').glob('*.inc'):
        country=get(parse(read(p)),'country',[]);tag=get(country,'tag','')
        if re.fullmatch(r'[A-Z0-9]{3}',tag):tags.add(tag)
    return tuple(sorted(tags-{'JAP','REB'}))


def hostile_control(province):
    return 'OR = { '+' '.join('AND = { '+control(province,tag)+' '+war(tag)+' }' for tag in country_tags())+' }'


def apply():
    if REPORT:return REPORT
    old={e.key:e.id for e in EVENTS}
    for p,name in BASES:
        gate=active()+' flag = JX_PACIFIC '+control(p)+' NOT = { '+f('R15_HELD_'+str(p))+' }'
        event('r15_remember_base_'+str(p),'Japanese control of '+name,'',gate=gate,
              persistent=True,offset=1,year=1941,module='r15_recovery',
              actions=[guarded_action('',[flag('R15_HELD_'+str(p))],gate)])

    fleet=[cmd('add_corps',which='"Rebuilt Carrier Force"',value='naval',where=ASSEMBLY)]
    for model,g,_ in latest('light_cag'):
        fleet += [cond(g,cmd('add_brigade',value='light_cag',when=model)) for _ in range(2)]
    for name in ('Rebuilt Light Carrier One','Rebuilt Light Carrier Two'):
        fleet += formation('light_carrier',name,'naval',new_corps=False)
    for _,g,mp in latest('light_carrier'):
        refund=round(3.6-2*mp,6)
        if refund:fleet.append(cond(g,cmd('manpowerpool',value=refund)))
    for name in ('Rebuilt Carrier Force Escort One','Rebuilt Carrier Force Escort Two',
                 'Rebuilt Carrier Force Escort Three','Rebuilt Carrier Force Escort Four'):
        fleet += formation('destroyer',name,'naval',new_corps=False)
    for _,g,mp in latest('destroyer'):
        refund=round(6.4-4*mp,6)
        if refund:fleet.append(cond(g,cmd('manpowerpool',value=refund)))
    fleet += [cmd('oilpool',value=4000)]
    shore=[]
    for name in ('Naval Recovery Air Group One','Naval Recovery Air Group Two'):
        shore += formation('naval_bomber',name,'air')
    shore += formation('multi_role','Naval Recovery Fighter Group','air')
    proposal('r15_carrier_recovery','After the carrier losses',
        'Three fleet carriers have been lost and fewer than four remain. Commission two Light Carriers, their air groups and escorts through a costly emergency programme, or form land-based strike wings sooner. Both choices occupy the major investment until delivery.',
        carrier_crisis(),[
            dict(label='Commission two Light Carriers and escorts',cost=dict(money=500,supplies=14000,oil=4000,metal=3500,manpower=10.14),days=330,
                 valid=fighting()+' '+home('naval')+' '+ready('light_carrier')+' '+ready('light_cag')+' '+ready('destroyer'),rewards=fleet,focus='FLEET_RECOVERY',
                 result='Two Light Carriers and four Destroyer flotillas form at Tokyo. Two Light CAGs enter the deployment pool: fit them before combat. Japan receives the reserved 4,000 oil. Newest researched, dated models are used. Unused crew reserves return; organisation recovers normally.'),
            dict(label='Fight from the land airfields',cost=dict(money=250,supplies=6500,oil=1500,metal=1500,manpower=5.4),days=180,
                 valid=fighting()+' '+home('air')+' '+ready('naval_bomber')+' '+ready('multi_role'),rewards=shore,focus='SHORE_RECOVERY',
                 result='Two Naval Bomber wings and one Multirole Fighter wing form at Tokyo with the newest researched, dated equipment. They are land-based. Full crews were paid when training began. Units arrive at their allowed maximum strength and need normal organisation, oil and supplies.'),
        ],year=1942,art='naval',module='r15_recovery')

    shipping=[cmd('transport_pool',which=-1,value=160),cmd('escort_pool',which=-1,value=100),
              cmd('supplies',value=5000),cmd('oilpool',value=2000)]
    returnforce=formation('marine','Anchorage Return Marine Division','land')
    returnforce+=formation('transport','Anchorage Return Transport Flotilla','naval')
    returnforce+=[cmd('supplies',value=2000)]
    proposal('r15_anchorage_recovery','After an important anchorage falls',
        'Losing an anchorage at Truk, Rabaul, Singapore or Pearl Harbor exposed the remaining routes. Protect shipping quickly, or prepare Marines and troop shipping for a return. You plan the counterattack. Retaking the base does not erase this one-time recovery choice.',
        fighting()+' '+lost_anchorage(),[
            dict(label='Protect the remaining sea routes',cost=dict(money=150,supplies=3500,oil=1000),days=90,
                 valid=fighting(),rewards=shipping,focus='CONVOY_RECOVERY',
                 result='The remaining routes receive 160 convoy transports and 100 convoy escorts. Japan receives 5,000 supplies and 2,000 oil. These are shipping pools, not troop-transport flotillas. Convoy management still assigns the actual routes and escorts.'),
            dict(label='Prepare a force to return',cost=dict(money=300,supplies=6000,oil=2000,metal=1000,manpower=15.5),days=180,
                 valid=fighting()+' '+home('land')+' '+home('naval')+' '+ready('marine')+' '+ready('transport'),rewards=returnforce,focus='RETURN_FORCE',
                 result='One Marine division and one naval Transport flotilla form at Tokyo with the newest researched, dated equipment. Japan receives 2,000 supplies. Full crews were paid at funding. Recover organisation, assemble escorts, and plan the landing; this event moves no force to the lost base.'),
        ],year=1941,art='naval',module='r15_recovery')
    # Long controller tests stay in four silent actions, never on public cards.
    # A recorded hostile capture remains a real past setback if the base is
    # later recovered; it cannot be manufactured by a peaceful treaty handover.
    for p,name in BASES:
        unseen=active()+' flag = JX_PACIFIC '+f('R15_HELD_'+str(p))+' NOT = { '+f('R15_ANCHORAGE_LOST')+' '+control(p)+' }'
        actual=unseen+' '+hostile_control(p)
        event('r15_lost_base_'+str(p),'The loss of '+name,'',gate=unseen,
              persistent=True,offset=1,year=1941,module='r15_recovery',actions=[
                  guarded_action('',[flag('R15_ANCHORAGE_LOST'),flag('R15_LOST_'+str(p))],actual),
                  Action('',[],gate=no(actual),chance=100)])
    assert all(next(e.id for e in EVENTS if e.key==k)==v for k,v in old.items())
    REPORT.update(applied=True,original_ids_preserved=len(old),added=[e.key for e in EVENTS if e.key not in old],
                  proposals=('r15_carrier_recovery','r15_anchorage_recovery'),remembered_bases=dict(BASES))
    return REPORT
