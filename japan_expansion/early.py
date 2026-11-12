"""Historical anchors and operational choices for the 1933–1940 campaign.

Appended after the original catalogue: existing IDs remain stable. These are
one-off story windows, not another permanent strategic decision menu.
"""
from catalog import *


def done(key):return flag('EARLY_'+key+'_DONE')


def budget(cash=0,stock=0,fuel=0):
    return f'money = {cash} supplies = {stock} oil = {fuel}'


def purchase(cash=0,stock=0,fuel=0):
    return [money(-cash),supplies(-stock),cmd('oilpool',value=-fuel)]


def prewar():return active()+' NOT = { flag = JX_PACIFIC }'


def us_trade():
    return 'exists = USA NOT = { '+war('USA')+' event = 2049026 }'


def contract(supplier,days,metal=0,oil=0,pay_supplies=0,pay_money=0):
    # In B&I's German-Yugoslav barter example, positive resources flow from
    # where to which. Negative metal/oil therefore enter Japan; payment leaves.
    return cmd('trade',which=supplier,where='JAP',metal=-metal,oil=-oil,
               supplies=pay_supplies,money=pay_money,when=days,value=1 if supplier=='USA' else 0)


def story(key,title,description,year,options,*,month='january',day=0,gate='',art='college'):
    marker='EARLY_'+key
    available=prewar()+f' NOT = {{ flag = JX_{marker}_DONE flag = JX_{marker}_WAIT }} '+gate
    acts=[]
    for label,commands,requirements in options:
        acts.append(Action(label,commands+[done(key)],gate=f'NOT = {{ flag = JX_{marker}_DONE }} '+requirements,chance=100 if not acts else 0))
    acts += [Action('Reconsider in three months',[flag(marker+'_WAIT'),later(key+'_reconsider',90)],gate=f'NOT = {{ flag = JX_{marker}_DONE flag = JX_{marker}_WAIT }}'),Action('Pass on this proposal permanently',[done(key)],gate=f'NOT = {{ flag = JX_{marker}_DONE }}')]
    event(key,title,description,year=year,start_month=month,start_day=day,gate=available,persistent=True,offset=7,actions=acts,art=art,module='early')
    event(key+'_reconsider',title+' - reconsideration','',triggered=True,actions=[Action('',[clear(marker+'_WAIT')])],module='early')


def expiry(key,commands,days):
    active_flag='EARLY_'+key+'_ACTIVE'
    event(key+'_expiry','The temporary allocation ends','',triggered=True,actions=[Action('',commands+[clear(active_flag)],gate='flag = JX_'+active_flag,chance=100),Action('',[],gate='NOT = { flag = JX_'+active_flag+' }')],module='early')
    return [flag(active_flag),later(key+'_expiry',days)]


def project_story(key,title,description,year,*,month='january',gate='',cash=60,stock=300,days=180,reward=None,alternative=None,finish_gate='',art='railway'):
    paid_project(key,title,description,year=year,gate='NOT = { flag = JX_PACIFIC } '+gate,money_cost=cash,supply_cost=stock,days=days,reward=reward,alternative=alternative,finish_gate=finish_gate,art=art,module='early')
    main=next(e for e in EVENTS if e.key==key)
    main.decision=False;main.start_month=month


def append_events():
    if any(e.key=='fx1933' for e in EVENTS):return
    story('fx1933','Import licences: ore or oil?',
        'Reserve shipping and payment for essential imports. A mixed American contract brings 8 metal and 4 oil daily for 2 supplies and 0.3 money daily. An oil-first contract brings 8 oil for 1 supply and 0.4 money daily. Either runs for 720 days and costs 40 money to arrange. America cannot cancel it through ordinary AI trade decisions; war, embargo or expiry can end it. Delivery still depends on trade efficiency.',
        1933,[('Buy a mixed ore and oil contract',purchase(40)+[contract('USA',720,metal=8,oil=4,pay_supplies=2,pay_money=.3)],budget(40)+' '+us_trade()),('Put the import allowance into oil',purchase(40)+[contract('USA',720,oil=8,pay_supplies=1,pay_money=.4)],budget(40)+' '+us_trade())],month='may',gate=us_trade(),art='economy')

    navy_expire=expiry('alloc_navy',[cmd('build_cost',which='naval',where='relative',when='on_upgrade',value=4),cmd('build_cost',which='land',where='relative',when='on_upgrade',value=-4)],720)
    army_expire=expiry('alloc_army',[cmd('build_cost',which='land',where='relative',when='on_upgrade',value=4),cmd('build_cost',which='naval',where='relative',when='on_upgrade',value=-4)],720)
    story('allocations1933','One steel budget, two services',
        'The Army and Navy both want first claim on skilled labour and scarce steel. Give one service priority for two years: its new-unit IC cost falls by 4 percent of each class\'s basic cost, while the other service pays 4 percent more. Air production is unchanged. You can also keep equal allocations. After 720 days the temporary priority ends. This is a production choice, with no commitment to a northern or southern war.',
        1933,[('Give the naval yards temporary priority',[cmd('build_cost',which='naval',where='relative',when='on_upgrade',value=-4),cmd('build_cost',which='land',where='relative',when='on_upgrade',value=4)]+navy_expire,''),('Give the Army temporary priority',[cmd('build_cost',which='land',where='relative',when='on_upgrade',value=-4),cmd('build_cost',which='naval',where='relative',when='on_upgrade',value=4)]+army_expire,''),('Keep equal allocations',[], '')],month='october',art='college')

    stability_end=expiry('stability',[cmd('build_time',which=u,when='on_upgrade',value=-12) for u in ('destroyer','light_cruiser')],180)
    story('tomozuru1934','Tomozuru: too much weight above the waterline',
        'The torpedo-boat disaster exposes the danger of packing heavy armament onto small hulls. A stability review costs 60 money and 250 supplies. It reduces destroyer and light-cruiser naval vulnerability by 0.5, but redesign delays their new construction by 12 days for six months. Alternatively spend 30 money, 150 supplies and 100 oil on seamanship drills for 1 naval morale. Earlier design work reduces the cost of the later structural review.',
        1934,[('Redesign the small-ship hulls',purchase(60,250)+[flag('STABILITY_STUDIES')]+[cmd('naval_defense',which=u,value=-.5) for u in ('destroyer','light_cruiser')]+[cmd('build_time',which=u,when='on_upgrade',value=12) for u in ('destroyer','light_cruiser')]+stability_end,budget(60,250)),('Improve seamanship and operating limits',purchase(30,150,100)+[cmd('morale',which='naval',value=1)],budget(30,150,100))],month='march',day=11,art='storm')

    story('oil1934','The oil law needs an actual reserve',
        'Storage obligations mean little unless the tanks are filled. A three-year American purchase brings 6 oil daily and costs 1.5 supplies and 0.3 money daily, plus 50 money in handling costs now. America cannot cancel it through ordinary AI trade decisions. War, embargo or expiry can end it. Alternatively spend 50 money and 250 supplies on fuel discipline, reducing carrier fuel consumption by 0.02 and destroyer consumption by 0.01 per ship. Japan will still need imports.',
        1934,[('Fill the tanks through a paid oil contract',purchase(50)+[contract('USA',1080,oil=6,pay_supplies=1.5,pay_money=.3)],budget(50)+' '+us_trade()),('Make the existing fuel go further',purchase(50,250)+[cmd('fuel_consumption',which='carrier',value=-.02),cmd('fuel_consumption',which='destroyer',value=-.01)],budget(50,250))],month='july',art='economy')

    structure_end=expiry('structure',[cmd('build_time',which='destroyer',when='on_upgrade',value=-8)],180)
    structural_reward=[cmd('naval_defense',which='destroyer',value=-.5),cmd('naval_defense',which='light_cruiser',value=-.5),cmd('build_time',which='destroyer',when='on_upgrade',value=8)]+structure_end
    story('typhoon1935','The typhoon exposes the fleet\'s weak seams',
        'Heavy-weather damage makes hull strength an urgent yard problem. Pay 70 money and 300 supplies for stronger destroyer and cruiser structures: naval vulnerability falls by 0.5 for each class, with an 8-day destroyer construction delay for six months. The fee falls to 40 money if the Tomozuru design study was funded. Or spend 60 money to stock 800 supplies for repairs and reinforcement.',
        1935,[('Apply the earlier study: 40 money, 300 supplies',purchase(40,300)+structural_reward,budget(40,300)+' flag = JX_STABILITY_STUDIES'),('Fund a fresh structural review: 70 money',purchase(70,300)+structural_reward,budget(70,300)+' NOT = { flag = JX_STABILITY_STUDIES }'),('Buy the repair reserve: 60 money',purchase(60)+[supplies(800)],budget(60))],month='september',day=25,art='storm')

    story('deck1935','The flight deck or the battle line?',
        'Exercises consume fuel that could stay in reserve. Spend 40 money, 250 supplies and 250 oil on repeated carrier landings: CAG and light-CAG morale rise by 2. Or spend the same money and supplies with 350 oil on battle-line gunnery, adding 0.5 battleship naval attack. Your existing fleet makes the answer different from another player\'s.',
        1935,[('Practise carrier landing cycles',purchase(40,250,250)+[cmd('morale',which='cag',value=2),cmd('morale',which='light_cag',value=2)],budget(40,250,250)),('Exercise the battleship gunners',purchase(40,250,350)+[cmd('naval_attack',which='battleship',value=.5)],budget(40,250,350))],month='november',gate='carrier = { value = 2 when = now }',art='air')

    story('colleges1936','Experienced officers: classrooms or formations?',
        'After the February crisis, the services must rebuild professional training without reopening the political struggle. Keep experienced officers teaching for 40 money and 250 supplies: land morale rises by 1. Or spend the same funds to return a small, finite cadre to formation work, adding 15 manpower to the recruitment pool. The political settlement after the coup stands; the question now is where experienced officers can do the most good.',
        1936,[('Keep the instructors in the colleges',purchase(40,250)+[cmd('morale',which='land',value=1)],budget(40,250)),('Return the cadre to formation work',purchase(40,250)+[cmd('manpowerpool',value=15)],budget(40,250))],month='april',gate='OR = { event = 2011006 event = 9300220 }',art='college')

    story('fx1936','Renew the commercial breathing space',
        'The first import arrangement is nearing its end or has already expired. A fresh three-year mixed contract buys 8 metal and 4 oil daily from America for 2 supplies and 0.3 money daily, with a 40-money handling payment now. America cannot cancel it through ordinary AI trade decisions; war, embargo or expiry can end it. Alternatively pay 40 money and 150 supplies to fit 20 convoy escorts. This volume cannot feed the whole Japanese economy.',
        1936,[('Renew the paid mixed imports',purchase(40)+[contract('USA',1080,metal=8,oil=4,pay_supplies=2,pay_money=.3)],budget(40)+' '+us_trade()),('Protect the merchant ships already sailing',purchase(40,150)+[cmd('escort_pool',which=-1,value=20)],budget(40,150))],month='september',gate=us_trade(),art='economy')

    story('rail1937','The offensive has outrun the railheads',
        'Advancing divisions can move farther than their depots and engineers can support. Spend 40 money and 400 supplies on loading discipline, field workshops and rail coordination for 3 percent more transport capacity. Or put the same funds into assault-group training for 3 points better infantry urban attack. The first supports a long, dispersed campaign; the second helps break defended cities.',
        1937,[('Bring the depots forward',purchase(40,400)+[cmd('tc_mod',value=3)],budget(40,400)),('Train infantry assault groups',purchase(40,400)+[cmd('urban_attack',which='infantry',value=3)],budget(40,400))],month='september',gate=war('CHI'),art='railway')

    project_story('procurement1937','The captured railway must keep working',
        'Holding Shanghai and Nanjing leaves a choice about the supply corridor. Rebuild track and loading facilities for 10 infrastructure in each city and 2 percent more transport capacity. Or fund local contractors for a 1,200-supply operating reserve. Both options cost 70 money and 500 supplies and take 120 days. Losing either required centre before completion returns the payment.',
        1937,month='october',gate=war('CHI')+' '+control(1337)+' '+control(1338),cash=70,stock=500,days=120,reward=[cmd('construct',which='infrastructure',where=p,value=10) for p in (1337,1338)]+[cmd('tc_mod',value=2)],alternative=('Buy a local supply reserve instead',[supplies(1200)]),finish_gate=control(1337)+' '+control(1338),art='railway')

    project_story('materials1938','Steel for the mobilisation orders',
        'Mobilisation has raised orders faster than the supply of raw materials. Improve processing at Pyeongyang: add 2 provincial metal output while consuming 4 provincial energy output. Or reorganise existing workshops for 3 percent better supply production without new resource output. The funding is additional to the earlier mobilisation bill. The site must remain Japanese-owned and controlled.',
        1938,month='may',gate='OR = { event = 1000247 flag = JX_china_SETTLED '+war('CHI')+' } '+control(1221)+' '+owned(1221),cash=60,stock=350,days=270,reward=[cmd('add_prov_resource',which=1221,where='metal',value=2),cmd('add_prov_resource',which=1221,where='energy',value=-4)],alternative=('Improve supply workshops instead',[cmd('industrial_modifier',which='supplies',value=3)]),finish_gate=control(1221)+' '+owned(1221),art='economy')

    story('nomonhan1939','Nomonhan: learn before the next war',
        'The border fighting has exposed weaknesses in anti-tank drill, signals and recovery. For 50 money and 300 supplies, improve infantry hard attack by 0.5 through gun drills and ammunition work. Or spend the same funds on signals and recovery for 2 percent more transport capacity. These are limited lessons from the clash, not a cure for poor equipment. Neither option starts a Soviet war or commits Japan to a northern strategy.',
        1939,[('Improve infantry anti-tank drill',purchase(50,300)+[cmd('hard_attack',which='infantry',value=.5)],budget(50,300)),('Improve signals and recovery',purchase(50,300)+[cmd('tc_mod',value=2)],budget(50,300))],month='september',gate='OR = { event = 2011023 event = 2007009 }',art='army')

    story('neutral1939','A commercial opening while Europe fights',
        'War in Europe makes alternative suppliers worth considering. If Japan and the USSR remain at peace, pay 40 money for a one-year cancellable Soviet contract: 4 metal and 4 oil daily in exchange for 1 supply and 0.2 money daily. This is trade, not an alliance or a neutrality guarantee. Or spend 40 money and 150 supplies on 20 convoy escorts. Either choice leaves later Soviet-war decisions available.',
        1939,[('Buy the northern commercial contract',purchase(40)+[contract('SOV',360,metal=4,oil=4,pay_supplies=1,pay_money=.2)],budget(40)+' exists = SOV NOT = { '+war('SOV')+' }'),('Escort the existing imports instead',purchase(40,150)+[cmd('escort_pool',which=-1,value=20)],budget(40,150))],month='october',gate='war = { country = GER country = ENG }',art='economy')

    story('instructors1940','Bring veteran naval aviators home to teach?',
        'Experience from China is concentrated in a small number of crews. For 50 money and 300 supplies, rotate instructors into the training schools: CAG and light-CAG morale rise by 2. Or pay 50 money for an immediate 700-supply readiness reserve and keep the veterans with their units. Training gives a lasting recovery benefit; the reserve helps the forces you already have.',
        1940,[('Rotate veteran instructors',purchase(50,300)+[cmd('morale',which='cag',value=2),cmd('morale',which='light_cag',value=2)],budget(50,300)),('Keep the crews forward; buy the reserve',purchase(50)+[supplies(700)],budget(50))],month='march',gate='OR = { '+war('CHI')+' flag = JX_china_SETTLED }',art='college')


append_events()
