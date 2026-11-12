"""Small, situational activities; append-only IDs, no global campaign routes.

These use existing B&I unit types. An airborne formation is not advertised as
a new class, nor does a production order award an already completed division.
"""
from catalog import *


def activity(key, title, desc, year, *, gate='', month='january', cash=60,
             stock=300, days=120, reward=None, alternative=None,
             finish_gate='', art='army', first_label='Fund the first proposal'):
    paid_project(key, title, desc, year=year, gate=gate, money_cost=cash,
                 supply_cost=stock, days=days, reward=reward,
                 alternative=alternative, finish_gate=finish_gate,
                 art=art, module='activities')
    main=next(e for e in EVENTS if e.key==key)
    # These appear once as story windows, not eight extra permanent cards.
    main.decision=False
    main.start_month=month
    main.actions[0].name=first_label
    for e in EVENTS:
        if e.key.startswith(key+'_finish_'):
            e.desc += ' This is an optional Japanese programme, not a compulsory historical outcome.'


def append_events():
    if any(e.key=='winter_school' for e in EVENTS):return
    activity('winter_school','A winter in Hokkaido',
        'A quiet winter gives the Army time to practise away from the parade ground. '
        'Give mountain troops cold-weather movement and defensive training: 5 points '
        'better frozen movement and defence, plus the 1935 mountain-infantry blueprint. '
        'Or teach ordinary infantry to hold in the cold: 3 points better frozen defence. '
        'These are training modifiers, not new divisions or protection against every winter penalty.',
        1935,month='february',gate='atwar = no '+control(1545),cash=40,stock=250,
        reward=[blueprint(1250),cmd('frozen_move',which='bergsjaeger',value=5),
                cmd('frozen_defense',which='bergsjaeger',value=5)],
        alternative=('Train the ordinary infantry for winter',[
            cmd('frozen_defense',which='infantry',value=3)]),
        finish_gate=control(1545),art='siberia',first_label='Train the mountain formations')

    activity('landing_rehearsal','The landing must survive its first night',
        'Boats reaching the beach are only the beginning. Train naval infantry to '
        'cross defended waterways: gain the 1937 marine blueprint and 3 points better '
        'marine river attack. Or use the same funds to improve the merchant support '
        'behind the landing, adding 30 convoy transports and 10 convoy escorts. '
        'Convoy ships cannot carry divisions as naval transports.',
        1936,month='june',gate='NOT = { flag = JX_PACIFIC }',cash=50,stock=300,
        reward=[blueprint(1590),cmd('river_attack',which='marine',value=3)],
        alternative=('Provide the merchant support instead',[
            cmd('transport_pool',which=-1,value=30),cmd('escort_pool',which=-1,value=10)]),
        art='naval',first_label='Rehearse the naval-infantry assault')

    activity('airborne_study','Can troops arrive ahead of the landing fleet?',
        'A small airborne study gives the paratrooper and transport-aircraft '
        'blueprints, plus an eight-day improvement to future transport-aircraft '
        'construction. Research, aircraft and parachute divisions must still be '
        'funded normally. Or put the study budget into two additional airfield '
        'levels at Saipan. Its starting airfield is level four; Truk already has '
        'a level-ten airfield and is not offered a pointless expansion.',
        1938,month='march',gate='NOT = { flag = JX_PACIFIC } '+control(1685),cash=60,stock=300,days=180,
        reward=[blueprint(1670),blueprint(4290),cmd('build_time',which='transport_plane',when='on_upgrade',value=-8)],
        alternative=('Expand Saipan for conventional air operations',[
            cmd('construct',which='air_base',where=1685,value=2)]),
        finish_gate=control(1685),art='air',first_label='Fund the airborne study')

    activity('field_medicine','Bring the wounded back',
        'Long marches and scattered aid posts take men out of the China campaign. '
        'Improve evacuation and field medicine for one point less attrition. '
        'Or finance a single return of recovered personnel, adding 18 manpower '
        'to the pool. This is a finite reserve, not extra manpower every month. '
        'Neither choice awards combat divisions.',
        1938,month='august',gate=war('CHI'),cash=50,stock=350,
        reward=[cmd('attrition_mod',value=1)],
        alternative=('Return recovered personnel to the pool',[
            cmd('manpowerpool',value=18)]),art='army',first_label='Improve evacuation and field medicine')

    activity('airborne_force','An airborne force for the southern war',
        'Research has made an airborne operation possible. Order one parachute '
        'division and one transport-aircraft wing, or two interceptor wings. '
        'These enter ordinary production and require IC, manpower and time; '
        'the first force is not delivered ready for an immediate air assault. '
        'Airborne missions still require the appropriate doctrine, organisation, '
        'range and transport capacity.',
        1942,gate=pacific()+' atwar = yes technology = 1670 technology = 4290',cash=80,stock=450,days=60,
        reward=[cmd('build_division',which='paratrooper',when=1),
                cmd('build_division',which='transport_plane',when=1)],
        alternative=('Build two interceptor wings instead',[
            cmd('build_division',which='interceptor',when=2)]),
        first_label='Prepare the parachute and transport orders',art='air')

    activity('mobile_columns','A formation that can exploit the breakthrough',
        'The Pacific war has also opened long land campaigns. Order two motorised '
        'divisions for exploitation, or two cavalry divisions for a force with '
        'less dependence on trucks at early models. Both use existing Blood and '
        'Iron models, normal production and manpower. Check the model you will '
        'actually build: later cavalry can consume fuel too. Neither force gains '
        'an invented jungle or mountain movement advantage.',
        1942,month='april',gate=pacific()+' atwar = yes technology = 1396',cash=70,stock=450,days=90,
        reward=[cmd('build_division',which='motorized',when=2)],
        alternative=('Prepare two cavalry divisions instead',[
            cmd('build_division',which='cavalry',when=2)]),
        art='army',first_label='Prepare the motorised formations')

    activity('island_depth','Make the enemy fight for the island bases',
        'Truk and Saipan are valuable bases, not self-defending symbols. Add two '
        'coastal-fort levels to each island, or add two airfield levels and two '
        'AA levels at Saipan. Coastal forts help against a landing; aircraft and '
        'ships still need to be assigned by you. Truk already has a level-ten '
        'airfield. Losing either island before completion returns the payment.',
        1942,month='july',gate=pacific()+' '+war('USA')+' '+control(1667)+' '+control(1685),cash=80,stock=400,days=180,
        reward=[cmd('construct',which='coastal_fort',where=p,value=2) for p in (1667,1685)],
        alternative=('Expand Saipan air operations and AA',[
            cmd('construct',which='air_base',where=1685,value=2),
            cmd('construct',which='flak',where=1685,value=2)]),
        finish_gate=control(1667)+' '+control(1685),art='pacific',first_label='Build the coastal defences')

    activity('home_air_defence','Who will meet the bombers over Japan?',
        'Fighters over distant fronts cannot also guard the industrial cities. '
        'Order two interceptor wings, or add two AA levels in both Tokyo and '
        'Hiroshima. Aircraft use ordinary production, manpower and operating '
        'supplies. AA stays at the named sites and cannot escort a fleet. '
        'This preparation does not conjure a defence force or predict when the '
        'American bombers will come.',
        1943,month='march',gate=pacific()+' '+war('USA')+' '+control(1552)+' '+control(1554),cash=60,stock=350,days=120,
        reward=[cmd('build_division',which='interceptor',when=2)],
        alternative=('Build AA around the two industrial centres',[
            cmd('construct',which='flak',where=p,value=2) for p in (1552,1554)]),
        finish_gate=control(1552)+' '+control(1554),art='air',first_label='Prepare the interceptor orders')


append_events()
