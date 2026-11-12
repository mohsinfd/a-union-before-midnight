"""R7: fewer programmes, useful forces and a sustained human fuel economy.

Applied after the legacy catalogue is complete. Retired entries keep their IDs
and receivers for recovery; new campaigns cannot start their old offers.
"""
from catalog import *
import early

RETIRED = {
    'naval_school','pilot_school','army_school','war_standard','fleet_order',
    'escort_order','naval_air_rebuild','guards','mobile_army','base_guard',
    'maritime_patrol','fuel_discipline','synthetic','australian_prep',
    'med_expedition','late_fleet','late_air','ocean_patrol','island_defence',
    'long_range','cold_training','fleet_1944','reserve_1948','science_1949',
    'winter_school','landing_rehearsal','airborne_study','field_medicine',
    'airborne_force','mobile_columns','home_air_defence',
    'base_force_orders','jungle_force_orders','snlf','emergency_rebuild',
}
REPORT = {}


def discount(units, cost, time):
    air={'interceptor':(3.5,42),'multi_role':(4,42),'cas':(4,46),
         'tactical_bomber':(5,46),'naval_bomber':(4,48),'transport_plane':(5,48)}
    if all(u in air for u in units):
        return [cmd(kind,which=u,when='on_upgrade',value=-value)
                for u in units for kind,value in [('build_cost',air[u][0]),('build_time',air[u][1])]]
    import specialist_units as s
    commands=[]
    for u in units:
        if u in s.CLASSES:m=s.models(u)[0]
        else:
            p=s.SOURCE/'db/units/divisions'/f'{u}.txt'
            if not p.exists():p=s.SOURCE/'db/units/brigades'/f'{u}.txt'
            m=s.getall(s.parse(s.read(p)),'model')[0]
        commands += [cmd('build_cost',which=u,when='on_upgrade',value=-round(s.num(m,'cost')*cost/100,2)),
                     cmd('build_time',which=u,when='on_upgrade',value=-round(s.num(m,'buildtime')*time/100,2))]
    return commands


def apply():
    if REPORT:return
    by={e.key:e for e in EVENTS}
    first=by['national_callup_1941']
    first.gate+=' OR = { flag = JX_PACIFIC war = { country = JAP country = SOV } }'
    for current,previous in [('national_callup_1942','national_callup_1941'),('national_callup_1943','national_callup_1942')]:
        by[current].gate+=f' event = {{ id = {by[previous].id} days = 300 }}'
    by['national_mobilization_end'].actions[0].gate='flag = JX_NATIONAL_CALLUP_1941_DONE NOT = { flag = JX_NATIONAL_MOBILIZATION_ENDED }'
    retired=[]
    for key in sorted(RETIRED):
        if key not in by:raise ValueError('Unknown retired offer '+key)
        e=by[key]
        retired.append({'key':key,'id':e.id,'title':e.title})
        e.gate='ai = yes ai = no'
        e.ready='ai = yes ai = no'
        e.purpose='Retired in R7; replaced by service production choices, normal orders or fuel programmes.'

    # R6 land-air range survives. Production discounts now come from a visible
    # funded service priority, so they cannot stack with an automatic award.
    for key in ('land_air_reorganisation','land_air_forward_network'):
        e=by[key]
        e.actions[0].commands=[c for c in e.actions[0].commands if 'type = build_cost ' not in c and 'type = build_time ' not in c]
        amount=200 if key=='land_air_reorganisation' else 250
        e.desc=f'Forward basing, navigation and ground control add {amount} km of range to Japanese Interceptors, Multirole Fighters, Tactical Bombers and CAS. Aircraft production discounts come from the separate air production programme. Airfields still need oil and supplies.'

    e=by['army_supply']
    e.desc='Choose a lasting supply network or four additional IC at Tokyo. The supply network improves supply production by 15% and transport capacity by 15%, helping a larger army overseas. Costs: 150 money and 700 supplies; completion in 180 days. Each alternative is awarded once.'
    f=by['army_supply_finish_0']
    f.actions[0].commands=[c.replace('value = 5','value = 15') if 'type = industrial_modifier ' in c or 'type = tc_mod ' in c else c for c in f.actions[0].commands]
    f.desc='The army supply network is ready: supply production and transport capacity each rise by 15%.'
    for key in ('sumatra_oil','borneo_oil','java_oil'):
        e=by[key]
        e.desc=e.desc.replace('five daily','twenty daily').replace('three oil','fifteen oil')
        for i,amount in ((0,20),(1,15)):
            f=by[f'{key}_finish_{i}']
            f.actions[0].commands=[c.rsplit('value = ',1)[0]+f'value = {amount}' if 'type = add_prov_resource ' in c and 'where = oil' in c else c for c in f.actions[0].commands]
            f.desc=f'The selected oilfield work is ready. It adds {amount} provincial oil output at the named site, together with the selected shipping or airfield work. Oil remains subject to territorial resource efficiency and transport.'

    # Scale paid prewar imports to the intended fleet, air and mobile-army war.
    e=by['fx1933']
    e.title='Buy oil for a larger fleet'
    e.desc='Choose a two-year American fuel contract. The mixed contract buys 12 metal and 24 oil daily for 4 supplies and 1 money daily. The oil-first contract buys 48 oil daily for 6 supplies and 1.5 money daily. Either costs 80 money now. Delivery follows trade efficiency; embargo, war or expiry can end it. These agreements do not renew themselves.'
    for i,(label,metal,oil,sp,mn) in enumerate([('Buy 24 oil and 12 metal daily',12,24,4,1),('Buy 48 oil daily',0,48,6,1.5)]):
        e.actions[i].name=label
        e.actions[i].gate='NOT = { flag = JX_EARLY_fx1933_DONE } '+early.budget(80)+' '+early.us_trade()
        e.actions[i].commands=early.purchase(80)+[early.contract('USA',720,metal=metal,oil=oil,pay_supplies=sp,pay_money=mn),early.done('fx1933')]
    e=by['oil1934']
    e.desc='Buy 24 oil daily for three years, paying 4 supplies and 1 money daily plus 80 money now. This is an additional contract. Storage expansion is a separate programme. Embargo, war or expiry can end this trade. The alternative keeps the existing fuel-conservation work.'
    e.actions[0].name='Buy a further 24 oil daily'
    e.actions[0].gate='NOT = { flag = JX_EARLY_oil1934_DONE } '+early.budget(80)+' '+early.us_trade()
    e.actions[0].commands=early.purchase(80)+[early.contract('USA',1080,oil=24,pay_supplies=4,pay_money=1),early.done('oil1934')]
    # Identify the renewal by its actual contract rather than assuming its key.
    renew=[x for x in EVENTS if x.module=='early' and x.year==1936 and any('type = trade ' in c for a in x.actions for c in a.commands)]
    for e in renew:
        e.desc='Buy a three-year American contract for 12 metal and 24 oil daily. Pay 80 money now, then 4 supplies and 1 money daily. Embargo, war or expiry can end it. Or retain the existing escort alternative.'
        e.actions[0].name='Buy 24 oil and 12 metal daily'
        e.actions[0].gate=f'NOT = {{ flag = JX_EARLY_{e.key}_DONE }} '+early.budget(80)+' '+early.us_trade()
        e.actions[0].commands=early.purchase(80)+[early.contract('USA',1080,metal=12,oil=24,pay_supplies=4,pay_money=1),early.done(e.key)]

    # Larger imports must not lock the player into payments after storage fills.
    # The engine cannot selectively pause one named trade from an event; use
    # cancellable ordinary agreements rather than ending every US-Japan trade.
    imports=[by['fx1933'],by['oil1934']]+renew
    for e in imports:
        for a in e.actions:
            a.commands=[c.replace('value = 1','value = 0') if 'type = trade ' in c else c for c in a.commands]
        e.desc+=' This is an ordinary cancellable trade: cancel it in Diplomacy when imports exceed use or storage is full. The handling fee is spent; daily payments stop when the trade is cancelled. Oil over the engine limit still decays.'
    by['fx1933'].actions.insert(2,Action('Buy only 8 oil daily',
        early.purchase(30)+[cmd('trade',which='USA',where='JAP',oil=-8,supplies=1,money=.4,when=720,value=0),early.done('fx1933')],
        gate='NOT = { flag = JX_EARLY_fx1933_DONE } '+early.budget(30)+' '+early.us_trade()))
    by['fx1933'].desc+=' A smaller 8-oil daily contract costs 30 money now, then one supply and 0.4 money daily.'

    # Three independent service choices. They do not choose wars or allies.
    for key,title,year,cash,stock,days,desc,first,second,art in [
        ('army_production','Equip a larger army',1933,150,900,180,
         'Choose an army production priority. Both choices cut IC cost by 20% and construction time by 15% for their listed formations. The infantry programme covers Infantry, Mountain Infantry and Jungle Light Infantry. The mobile programme covers Motorised Infantry, Cavalry and Armour and adds 10% transport capacity. Normal research, manpower and operating costs apply. Your diplomatic choices remain open.',
         ('Equip infantry and mountain formations',discount(('infantry','bergsjaeger','d_11'),20,15)),
         ('Equip motorised formations and armour',discount(('motorized','cavalry','armor'),20,15)+[cmd('tc_mod',value=10)]),'army'),
        ('air_production','Build an air force Japan can afford',1934,180,1000,180,
         'Choose which aircraft factories expand first. Fighters: Interceptor IC -3.5 and time -42 days; Multirole IC -4 and time -42 days; CAS IC -4 and time -46 days. Bombers: Tactical IC -5 and time -46 days; Naval IC -4 and time -48 days; Transport IC -5 and time -48 days. These fixed reductions apply to future normal orders. Other technology, policy and gearing modifiers still apply.',
         ('Expand fighters and close air support',discount(('interceptor','multi_role','cas'),25,20)),
         ('Expand tactical and maritime aviation',discount(('tactical_bomber','naval_bomber','transport_plane'),25,20)),'air'),
        ('naval_production','Choose the next shipyard expansion',1935,220,1200,240,
         'Choose a shipbuilding priority. Carrier warfare cuts IC cost and construction time by 15% for Fleet Carriers, Light Carriers, CAG and Light CAG. Escort warfare cuts both by 20% for Destroyers, Light Cruisers and Submarines. Existing technology and conversion bonuses still apply. Fuel, screens and normal production remain necessary.',
         ('Expand carrier and air-group production',discount(('carrier','light_carrier','cag','light_cag'),15,15)),
         ('Expand escorts and submarines',discount(('destroyer','light_cruiser','submarine'),20,20)),'naval'),
    ]:
        paid_project(key,title,desc,year=year,money_cost=cash,supply_cost=stock,days=days,
                     reward=first[1],alternative=second,art=art,module='human_preparation')
        next(x for x in EVENTS if x.key==key).actions[0].name=first[0]
        from production_programmes import NAMES
        import specialist_units as sp
        summaries=[]
        for label,commands in (first,second):
            values={}
            for c in commands:
                n=sp.parse(c);kind=sp.get(n,'type');u=sp.get(n,'which')
                if kind in ('build_cost','build_time'):
                    values.setdefault(u,{})[kind]=-sp.num(n,'value')
            summaries.append(label+': '+ '; '.join(f"{NAMES.get(u,u)} -{v.get('build_cost',0):g} IC and -{v.get('build_time',0):g} days" for u,v in values.items()))
        main=next(x for x in EVENTS if x.key==key)
        main.desc='Choose one production priority. These fixed reductions apply to future normal orders; other national modifiers still apply.\n\n'+'\n\n'.join(summaries)+f'\n\nSetup: {cash} money and {stock} supplies. Completion: {days} days. Normal research, manpower and operating resources are still needed.'
        if key=='army_production':main.desc+=' The mobile alternative also adds 10% transport capacity.'
        for i in (0,1):
            f=next(x for x in EVENTS if x.key==f'{key}_finish_{i}')
            f.desc=f'{title}: the selected production expansion is ready. Its listed cost and time reductions now apply to future orders. Order the forces through normal production; no empty queue orders are inserted.'

    # Physical fuel output remains tied to home territory. Forty energy is
    # deducted from Yokohama's verified starting 47 across the two stages.
    for key,title,year,cash,stock,days,oil,prior in [
        ('home_fuel','Build home fuel works',1935,350,2400,240,20,''),
        ('war_fuel','Expand wartime fuel production',1940,500,3600,270,25,'flag = JX_home_fuel_DONE atwar = yes'),
    ]:
        sites=owned(1552)+' '+control(1552)+' '+owned(1550)+' '+control(1550)
        paid_project(key,title,
            f'Fund an ahistorical fuel expansion at Tokyo. After {days} days it adds {oil} daily provincial oil output and redirects 20 daily energy output from Yokohama. Output follows normal resource efficiency. It stays with the provinces if they are lost. This programme can be completed once.',
            year=year,gate=prior+' '+sites,money_cost=cash,supply_cost=stock,days=days,
            reward=[cmd('add_prov_resource',which=1552,where='oil',value=oil),cmd('add_prov_resource',which=1550,where='energy',value=-20)],
            finish_gate=sites,module='human_fuel',art='industry')
        next(x for x in EVENTS if x.key==key).actions[0].name=f'Build capacity for {oil} daily oil'

    # A repeatable wartime fallback converts paid stocks into a specified batch.
    # Only a pending batch can deliver. The 45+45 day cycle prevents spam.
    key='wartime_fuel_batch'
    fuel_available=active()+' atwar = yes NOT = { flag = JX_FUEL_BATCH_PENDING flag = JX_FUEL_BATCH_WAIT flag = JX_FUEL_BATCH_DISMISSED }'
    actions=[]
    for i,(energy,stock,cash,oil) in enumerate([(12000,800,100,6000),(24000,1600,200,12000)]):
        actions.append(Action(f'Convert {energy:,} energy into {oil:,} oil',
            [cmd('energypool',value=-energy),supplies(-stock),money(-cash),flag('FUEL_BATCH_PENDING'),later(f'fuel_batch_delivery_{i}',45)],
            gate=fuel_available+f' energy = {energy} supplies = {stock} money = {cash}'))
        event(f'fuel_batch_delivery_{i}','The wartime fuel batch is ready',
              f'The paid conversion programme delivers {oil:,} oil to Japan. Its energy, money and supply costs were charged when work began. Another order can be placed in 45 days.',triggered=True,
              actions=[Action('Receive the fuel',[cmd('oilpool',value=oil),clear('FUEL_BATCH_PENDING'),flag('FUEL_BATCH_WAIT'),later('fuel_batch_reset',45)],gate='flag = JX_FUEL_BATCH_PENDING',chance=100)],module='human_fuel',art='industry')
    actions+=[Action('Keep the present fuel policy',[]),Action('Hide this fuel order permanently',[flag('FUEL_BATCH_DISMISSED')])]
    event(key,'Order another wartime fuel batch',
          'Use stocked energy for an emergency fuel programme while at war. A normal batch costs 12,000 energy, 800 supplies and 100 money for 6,000 oil. A large batch costs double and delivers 12,000 oil. Delivery takes 45 days; another order becomes available 45 days later. This is an explicit ahistorical stock conversion, not an unbreakable foreign trade. One batch can be pending at a time.',
          decision=True,persistent=True,year=1937,gate=fuel_available,
          actions=actions,module='human_fuel',art='industry')
    event('fuel_batch_reset','A new fuel batch can be ordered','',triggered=True,
          actions=[Action('',[clear('FUEL_BATCH_WAIT')])],module='human_fuel')

    paid_project('repair_service','Keep damaged forces in the war',
          'Build a permanent repair and replacement service. Reinforcement efficiency rises by 25% for all services, helping damaged ships, aircraft and land formations return to strength through normal reinforcement spending. Sunk ships and destroyed units are not recreated. Costs: 220 money and 1,400 supplies; work takes 120 days.',
          year=1939,gate='atwar = yes',money_cost=220,supply_cost=1400,days=120,
          reward=[cmd('repair_mod',value=25)],module='human_preparation',art='naval')

    # The dedicated assault class replaces Japan's borrowed German SS class.
    event('snlf_open_recruitment','Naval landing formations are available',
          'Marine research now unlocks Special Naval Landing Divisions. They are smaller and cheaper than full Marine divisions, with better landing modifiers and less firepower. Order them normally; there is no separate setup payment.',
          year=1937,gate=active()+' technology = 1590 NOT = { flag = JX_SNLF_FORCE }',
          actions=[Action('Open naval landing recruitment',[fire('activate_d_12')],chance=100)],module='human_preparation',art='snlf')
    by['introduce_d_10'].desc='Naval Base Forces are small static defenders: 5 manpower, 4 base IC and 100 base construction days. They use little supply and cannot march. Use them to hold ports and airfields while field divisions advance.'
    by['introduce_d_11'].desc='Jungle Light Infantry use 8 manpower, 4 base IC and 190 base construction days. They carry less firepower than ordinary infantry and move better through jungle and swamp. They keep ordinary opposed-landing penalties; use naval landing formations for defended beaches.'
    paid_project('strategic_storage','Expand fuel and supply reserves',
        'Expand Japan\'s strategic storage allowance before importing a large surplus. This adds 200 percentage points to Japan\'s oil-and-supply stockpile modifier in peace and war. The engine groups oil and supplies together. The resulting limit depends on national needs; this does not promise a fixed number of oil barrels. Check the displayed limit and cancel imports when full. Overflow loss remains in force. Costs: 100 money, 800 supplies; work takes 90 days.',
        year=1933,money_cost=100,supply_cost=800,days=90,
        reward=[cmd('stockpile',which='supplies',when='all',value=200)],module='human_fuel',art='industry')


    REPORT.update(retired=retired,added=[e.key for e in EVENTS if e.module in ('human_preparation','human_fuel')])
