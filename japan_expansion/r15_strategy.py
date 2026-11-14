"""Three finite strategic allocations; no diplomacy or permanent modifiers.

Call apply after the released R14.1 catalogue and the other R15 modules. Importing
this module allocates no event IDs and does not read or change an installation.
"""
from catalog import EVENTS, cmd, cond, active, owned, control, war
import r15_common as common

REPORT={}
MODELS={}
PORTS=(1886,1887,1889,1874)
PACIFIC_BASES=((1667,'Truk'),(1685,'Saipan'),(1676,'Kwajalein'))
MIN_YEARS={'infantry':1936,'bergsjaeger':1935,'destroyer':1933,
           'cag':1934,'anti_air':1930,'garrison':1931,'marine':1937,'transport':1936}
ATTACHMENTS={'cag','anti_air'}


def no(gate):return 'NOT = { AND = { '+gate+' } }'
def f(name):return 'flag = JX_'+name
def battle():return 'OR = { '+war('USA')+' '+war('ENG')+' }'
def port(p):return owned(p)+' '+control(p)+f' building = {{ province = {p} type = naval_base value = 1 when = now }}'
def coast():return 'OR = { '+' '.join(control(p) for p in PORTS)+' }'


def model_options(unit):
    """Native researched/date pairs and full manpower, with no future unlocks."""
    if unit in MODELS:return MODELS[unit]
    from build import SOURCE,parse,read,get,getall,num
    folder='brigades' if unit in ATTACHMENTS else 'divisions'
    templates=getall(parse(read(SOURCE/'db/units'/folder/(unit+'.txt'))),'model')
    rows=set()
    for path in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(path)),'technology'):
            for app in getall(tree,'application'):
                year=int(get(app,'year',0))
                if not MIN_YEARS[unit]<=year<=1950:continue
                for c in getall(get(app,'effects',[]),'command'):
                    if get(c,'type')=='new_model' and get(c,'which')==unit and not get(c,'trigger'):
                        model=int(get(c,'value'));rows.add((year,model,int(get(app,'id')),num(templates[model],'manpower')))
    assert rows,unit
    rows=sorted(rows,reverse=True);result=[];higher=[]
    for year,model,tech,mp in rows:
        current=f'year = {year} technology = {tech}'
        gate=current+(' NOT = { OR = { '+' '.join('AND = { '+g+' }' for g in higher)+' } }' if higher else '')
        result.append(dict(year=year,model=model,tech=tech,mp=mp,gate=gate))
        higher.append(current)
    MODELS[unit]=result
    return result


def equipment(unit,count,site,name):
    """A single latest-researched model per unit, same-gated birth and heal."""
    rows=model_options(unit);reserve=max(r['mp'] for r in rows)*count
    # Availability needs one eligible model; mutually exclusive selectors belong
    # only on actual births. This keeps the public option's tooltip compact.
    gate='OR = { '+' '.join(f'AND = {{ year = {r["year"]} technology = {r["tech"]} }}' for r in rows)+' }'
    commands=[]
    if unit not in ATTACHMENTS:
        branch='naval' if unit in ('destroyer','transport') else 'land'
        commands.append(cmd('add_corps',which='"'+name+'"',value=branch,where=site))
    names=[]
    for ordinal in range(1,count+1):
        formation=name+(' '+str(ordinal) if count>1 else '')
        names.append(formation)
        for row in rows:
            if unit in ATTACHMENTS:birth=cmd('add_brigade',value=unit,when=row['model'])
            else:birth=cmd('add_division',which='"'+formation+'"',value=unit,when=row['model'])
            commands.append(cond(row['gate'],birth))
            if unit not in ATTACHMENTS:commands.append(cond(row['gate'],cmd('damage_division',which='"'+formation+'"',value='JAP',where=-100)))
    for row in rows:
        unused=round(reserve-count*row['mp'],4)
        if unused:commands.append(cond(row['gate'],cmd('manpowerpool',value=unused)))
    return dict(commands=commands,mp=reserve,gate=gate,names=names,unit=unit,count=count,site=site)


def bundle(*items):
    return dict(commands=[c for item in items for c in item['commands']],
                mp=round(sum(i['mp'] for i in items),4),
                gate=' '.join(i['gate'] for i in items),items=list(items))


def choice(label,cost,days,valid,units,rewards=(),focus=None,result=''):
    cost=dict(cost);cost['manpower']=round(units['mp']+cost.get('manpower',0),4)
    return dict(label=label,cost=cost,days=days,valid=valid+' '+units['gate'],
                rewards=units['commands']+list(rewards),focus=focus,result=result)


def apply():
    if REPORT:return REPORT
    before={e.key:e.id for e in EVENTS};packages={}
    army=bundle(equipment('infantry',2,1552,'China Offensive Infantry'),
                equipment('bergsjaeger',1,1552,'China Offensive Mountain Division'))
    navy=bundle(equipment('destroyer',2,1552,'Carrier Reserve Escorts'),
                equipment('cag',2,1552,'Carrier Reserve Air Groups'))
    packages['china']=[army,navy]
    context=(war('CHI')+' NOT = { flag = JX_PACIFIC } '
             'OR = { '+control(1338)+' '+control(1337)+' } '
             'army = { country = CHI size = 61 type = 0 when = 0 where = 1 which = 1 }')
    common.proposal('r15_china_or_fleet','Finish China or prepare the fleet?',
        'Shanghai gives the Army a base for a decisive advance. The Navy wants the same training and supply budget for the next war. '
        'Choose two Infantry and one Mountain division, or two Destroyers, two CAG attachments and 60 convoy escorts. Twelve naval training staff return at delivery.',
        context,[
            choice('Reinforce the Chinese offensive',dict(money=300,supplies=7000,oil=500),180,
                   owned(1552)+' '+control(1552),army,focus='CHINA',
                   result='Two Infantry and one Mountain division enter service at Tokyo with current researched equipment. Training can finish after peace in China. Their manpower was paid at commissioning; normal organisation and supply are required.'),
            choice('Prepare the carrier and escort reserve',dict(money=350,supplies=7000,oil=1800,manpower=12),240,
                   port(1552),navy,[cmd('manpowerpool',value=12),cmd('escort_pool',which=-1,value=60)],focus='FLEET',
                   result='Two Destroyer flotillas enter service at Tokyo. Two current CAG attachments enter the deployment pool for your carriers; no carrier hulls are created. Twelve training staff return and 60 convoy escorts join the pool. New ships need normal organisation, fuel and supplies.')],
        year=1937,art='army',retry_on_failure=True)

    garrisons=[equipment('garrison',1,p,name+' Port Defence') for p,name in PACIFIC_BASES]
    defence=bundle(*garrisons,equipment('anti_air',3,1552,'Pacific Base AA Brigades'))
    expedition=bundle(equipment('marine',1,1432,'Indian Ocean Marine Division'),
                      equipment('bergsjaeger',1,1432,'Indian Ocean Mountain Division'),
                      equipment('transport',2,1432,'Indian Ocean Troop Transports'))
    packages['ocean']=[defence,expedition]
    aa=' '.join(port(p) for p,_ in PACIFIC_BASES)
    aa_rewards=[cmd('escort_pool',which=-1,value=100)]
    context='flag = JX_PACIFIC '+battle()+' '+control(1432)
    common.proposal('r15_pacific_or_ocean','Hold the Pacific or sail west?',
        'Singapore opens the Indian Ocean, while the Pacific bases need permanent defenders. '
        'Choose full Garrisons at Truk, Saipan and Kwajalein, three AA brigades to assign and 100 escorts, '
        'or a Marine division, a Mountain division and two troop transports at Japanese-owned Singapore with 2,000 oil.',
        context,[
            choice('Defend the Pacific bases',dict(money=350,supplies=7500,oil=1000),210,
                   battle()+' '+aa,defence,aa_rewards,focus='PACIFIC',
                   result='Truk, Saipan and Kwajalein each receive one full Garrison division. Three researched AA brigades enter the deployment pool; assign them manually to eligible formations. The older quarter-strength detachments are unchanged. One hundred convoy escorts join the pool; normal supply routes are still required.'),
            choice('Form the Indian Ocean expedition',dict(money=450,supplies=9000,oil=5000),240,
                   battle()+' '+port(1432),expedition,[cmd('oilpool',value=2000)],focus='OCEAN',
                   result='One Marine and one Mountain division, plus two troop-transport flotillas, enter service at Singapore with current researched equipment. Japan receives 2,000 oil for operations. These are map transport flotillas, not convoy points. No war is declared and no territory changes hands.')],
        year=1941,art='pacific',retry_on_failure=True)

    america=bundle(equipment('infantry',6,1552,'American Expedition Infantry'),
                   equipment('bergsjaeger',2,1552,'American Expedition Mountain Troops'))
    bases=((1552,'Tokyo'),(1550,'Yokohama'),(1554,'Hiroshima'),(1557,'Nagoya'))
    consolidate=bundle(*(equipment('garrison',1,p,name+' Home Defence') for p,name in bases))
    packages['america']=[america,consolidate]
    context=('flag = JX_PACIFIC '+war('USA')+' '+coast()+
             ' event = { id = @usc_landing days = 30 }')
    common.proposal('r15_american_army','Raise the next expeditionary army?',
        'The American foothold has survived a month. A new field army needs 104 recruits and nine months of the shared preparation budget. '
        'The alternative gives four home-base Garrisons, 180 convoy transports, 100 escorts and 4,000 supplies in five months. '
        'The field army assembles at Tokyo; you must carry it across the Pacific.',
        context,[
            choice('Raise the next army for America',dict(money=800,supplies=22000,oil=6000),270,
                   war('USA')+' '+coast()+' '+owned(1552)+' '+control(1552),america,focus='AMERICA',
                   result='Six Infantry and two Mountain divisions enter service at Tokyo with current researched equipment. Their full manpower was reserved when commissioned. They do not appear in America: provide transports, escorts, supplies and time to recover organisation before sending them overseas.'),
            choice('Strengthen home bases and shipping',dict(money=450,supplies=11000,oil=2500),150,
                   war('USA')+' '+' '.join(owned(p)+' '+control(p) for p,_ in bases),consolidate,
                   [cmd('transport_pool',which=-1,value=180),cmd('escort_pool',which=-1,value=100),cmd('supplies',value=4000)],focus='HOME',
                   result='Tokyo, Yokohama, Hiroshima and Nagoya each receive one full Garrison division. The national pool receives 180 convoy transports, 100 convoy escorts and 4,000 supplies. This protects the home and shipping system; it creates no additional American field army.')],
        year=1942,art='pacific',retry_on_failure=True)
    assert all(next(e.id for e in EVENTS if e.key==k)==v for k,v in before.items())
    REPORT.update(applied=True,roots=['r15_china_or_fleet','r15_pacific_or_ocean','r15_american_army'],
                  original_ids_preserved=True,packages=packages,added=[e.key for e in EVENTS if e.key not in before])
    return REPORT
