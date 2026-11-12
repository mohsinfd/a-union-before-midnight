"""Local opportunities, with independent completion and dismissal states."""
from catalog import *
from activities import activity
from early import contract


def append_events():
    activity('manchurian_contract','A commercial agreement with Manchukuo',
        'Buy a finite two-year Manchurian contract: 6 energy and 2 metal daily '
        'for 1 supply and 0.1 money daily. Delivery depends on normal trade '
        'efficiency and the agreement remains cancellable. Or spend the same '
        'setup funds on 25 convoy escorts. The puppet relationship must survive '
        'until this project finishes; it does not grant Japan Manchurian manpower.',
        1934,month='september',gate=puppet('MAN'),cash=40,stock=250,days=90,
        reward=[cmd('trade',which='MAN',where='JAP',energy=-6,metal=-2,
                    supplies=1,money=.1,when=720,value=0)],
        alternative=('Fit 25 convoy escorts instead',[cmd('escort_pool',which=-1,value=25)]),
        finish_gate=puppet('MAN'),art='economy',first_label='Arrange the paid Manchurian imports')
    activity('merchant_reserve','Keep civilian hulls ready for a wider war',
        'Reserve merchant hulls before the fleet needs every yard. Commission '
        '60 convoy transports, or 25 transports and 25 escorts. These are convoy '
        'pools, not warships or naval troop transports. The reserve is delivered '
        'once; it does not renew automatically or stop ships being sunk.',
        1935,month='october',gate='NOT = { flag = JX_PACIFIC }',cash=50,stock=300,days=180,
        reward=[cmd('transport_pool',which=-1,value=60)],
        alternative=('Build the smaller escorted reserve',[
            cmd('transport_pool',which=-1,value=25),cmd('escort_pool',which=-1,value=25)]),
        art='naval',first_label='Reserve more merchant hulls')
    activity('berlin_barter','Berlin asks for Asian rubber',
        'Germany offers a one-year barter: Japan receives 6 metal daily and '
        'sends 2 rares and 0.5 supplies daily. This is a cancellable trade with '
        'normal delivery risk, not Axis entry. Germany and Japan must remain '
        'at peace with each other until completion. Alternatively fit 25 convoy '
        'escorts without the continuing rare-material bill.',
        1939,month='october',gate='exists = GER war = { country = GER country = ENG } NOT = { '+war('GER')+' }',
        cash=40,stock=250,days=90,
        reward=[cmd('trade',which='GER',where='JAP',metal=-6,rare_materials=2,
                    supplies=.5,when=360,value=0)],
        alternative=('Protect shipping without a barter deal',[cmd('escort_pool',which=-1,value=25)]),
        finish_gate='exists = GER NOT = { '+war('GER')+' }',art='diplomacy',first_label='Sign the finite metal-for-rubber barter')
    friendly_siam='exists = SIA alliance = { country = JAP country = SIA } '+control(1415)
    activity('thai_connection','Connect the Thai railway to Rangoon',
        'Friendly Thailand opens a connection toward the Burmese coast. Improve '
        'Rangoon infrastructure by 10 points and Japanese transport capacity by '
        '2 percent. Or add two airfield and two AA levels at Rangoon. This adds '
        'no port levels: its starting naval base is already level ten. Thailand '
        'must remain allied and Japan must still hold Rangoon when work finishes.',
        1941,gate=pacific()+' '+friendly_siam,cash=70,stock=450,days=150,
        reward=[cmd('construct',which='infrastructure',where=1415,value=10),cmd('tc_mod',value=2)],
        alternative=('Protect the Burmese air bridge',[
            cmd('construct',which='air_base',where=1415,value=2),cmd('construct',which='flak',where=1415,value=2)]),
        finish_gate=friendly_siam,art='railway',first_label='Fund the railway connection')
    activity('rabaul_workshops','Rabaul needs workers as much as soldiers',
        'Develop the captured forward base: add two airfield levels and ten '
        'infrastructure points at Rabaul. Or commission 40 convoy transports '
        'and 20 escorts for the supply route. Facilities do not supply themselves; '
        'shipping does not defend the airstrip. Japan must hold Rabaul at completion.',
        1942,gate=pacific()+' '+control(1726),cash=60,stock=350,days=150,
        reward=[cmd('construct',which='air_base',where=1726,value=2),cmd('construct',which='infrastructure',where=1726,value=10)],
        alternative=('Fund the escorted supply route',[
            cmd('transport_pool',which=-1,value=40),cmd('escort_pool',which=-1,value=20)]),
        finish_gate=control(1726),art='pacific',first_label='Develop the Rabaul forward airfield')
    activity('colombo_station','Colombo opens the western ocean',
        'A captured Colombo gives the fleet a western base. Its airfield and '
        'port already start at level ten: add two radar and two AA levels '
        'instead. Or train longer maritime searches, '
        'adding 50 kilometres to naval-bomber range. There are no free aircraft. '
        'This one port does not decide the government of India or open the Suez canal.',
        1942,gate=pacific()+' '+control(1511),cash=60,stock=350,days=150,
        reward=[cmd('construct',which='radar_station',where=1511,value=2),cmd('construct',which='flak',where=1511,value=2)],
        alternative=('Prepare longer maritime searches',[
            cmd('range',which='naval_bomber',value=50)]),
        finish_gate=control(1511),art='naval',first_label='Protect the Colombo base')
    activity('northern_station','An Aleutian foothold needs a supply plan',
        'Holding Attu opens a cold and exposed northern approach. Build two '
        'airfield levels and ten infrastructure points there, or commission '
        '40 convoy transports and 20 escorts. Neither changes weather, naval '
        'range or American surrender conditions. Holding Attu through the work '
        'period is checked at completion; this is not an uninterrupted-occupation reward.',
        1942,gate=pacific()+' '+war('USA')+' '+control(2174),cash=60,stock=350,days=180,
        reward=[cmd('construct',which='air_base',where=2174,value=2),cmd('construct',which='infrastructure',where=2174,value=10)],
        alternative=('Provide the escorted northern supply route',[
            cmd('transport_pool',which=-1,value=40),cmd('escort_pool',which=-1,value=20)]),
        finish_gate=control(2174),art='siberia',first_label='Build the Attu staging airfield')
    activity('homefront_breathing_space','A breathing space after two years of war',
        'A long war reaches workshops and households as well as the front. '
        'Pay for one civilian relief effort, reducing dissent by 1.5. Or buy a '
        '1,000-supply reserve for current operations. Both use the stated setup '
        'budget. This is a voluntary, finite choice; declining does not add dissent '
        'or penalise a battlefield victory.',
        1943,month='december',gate=pacific()+' atwar = yes event = { id = @pacific_open days = 720 }',
        cash=60,stock=250,days=90,
        reward=[cmd('dissent',value=-1.5)],alternative=('Buy the operating supply reserve',[supplies(1000)]),
        art='industry',first_label='Fund civilian relief')


append_events()
