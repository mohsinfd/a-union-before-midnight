"""Map opportunities must buy useful, deliverable support in occupied territory.

Apply after campaign_flow.apply(). No new event IDs or territorial shortcuts.
"""
from catalog import EVENTS, Action, active, no_state, human, war, control, flag, clear, later, cmd, money, supplies

REPORT = {}
US_PORTS = (1886, 1887, 1889, 1874)


def _not(gate):
    return 'NOT = { AND = { ' + gate + ' } }'


def _stock_project(by, key, year, title, description, context, finish_context, choices, days):
    """Reuse a two-option project's existing transaction/receiver IDs."""
    main = by[key]
    main.year = year; main.title = title; main.desc = description
    main.decision = True; main.manual_only = True; main.ready = ''
    main.gate = active() + ' ' + no_state(key) + ' ' + context
    main.actions = []
    for i, (label, cash, stock, fuel, rewards, requirements) in enumerate(choices):
        live = f'flag = JX_{key}_PENDING NOT = {{ flag = JX_{key}_DONE }}'
        valid = human() + ' ' + finish_context
        payment = [money(-cash), supplies(-stock)] + ([cmd('oilpool', value=-fuel)] if fuel else [])
        main.actions.append(Action(label, payment + [flag(key + '_PENDING'), later(f'{key}_finish_{i}', days)],
                                   gate=main.gate + f' money = {cash} supplies = {stock} ' + requirements,
                                   chance=100 if i == 0 else 0))
        finish = by[f'{key}_finish_{i}']
        finish.title = title + ' - support ready'
        finish.desc = description + ' The inputs were paid at the start; this delivery takes no second payment.'
        refunds = [money(cash), supplies(stock)] + ([cmd('oilpool', value=fuel)] if fuel else [])
        finish.actions = [
            Action('Receive the selected support', rewards + [flag(key + '_DONE'), clear(key + '_PENDING')],
                   gate=live + ' ' + valid, chance=100),
            Action('The operation cannot finish; recover all paid inputs', refunds + [clear(key + '_PENDING'), flag(key + '_WAIT'), later(key + '_return', 90)],
                   gate=live + ' ' + _not(valid)),
            Action('', [], gate=_not(live)),
        ]
    main.actions += [Action('Leave this proposal available', [], gate=main.gate),
                     Action('Dismiss this proposal permanently', [flag(key + '_DISMISSED')], gate=main.gate)]


def _replace_discount(finish, rewards, description):
    finish.actions[0].commands = [c for c in finish.actions[0].commands if 'type = build_time ' not in c] + rewards
    finish.desc = description + ' The setup payment was taken when work began; delivery charges nothing further.'


def apply():
    if REPORT:
        return REPORT
    by = {e.key: e for e in EVENTS}
    ids = {e.key: e.id for e in EVENTS}
    ports = 'OR = { ' + ' '.join(control(p) for p in US_PORTS) + ' }'
    _stock_project(by, 'american_base', 1941, 'Sustain the American bridgehead',
        'From 1941, holding San Diego, Los Angeles, San Francisco or Seattle during war with America opens this one-time support programme. '
        'Pay 180 money and 1,000 supplies. After 90 days choose the funded result: 120 convoy transports, 40 convoy escorts and 2,000 supplies; '
        'or a 4,000-supply reinforcement reserve and 5 percent more transport capacity. Select the result before paying. '
        'Both alternatives work in American-owned territory and at capped ports. Supplies enter Japan\'s national reserve; normal convoys must move them to the front. '
        'No buildings, land, cores or completed divisions are granted. Keep at least one listed port through completion or receive the exact payment back. '
        'This is a manual decision, not an automatic victory award.',
        war('USA') + ' ' + ports, ports,
        [('Fund the escorted bridgehead supply route', 180, 1000, 0,
          [cmd('transport_pool', which=-1, value=120), cmd('escort_pool', which=-1, value=40), supplies(2000)], ''),
         ('Fund the reinforcement reserve and transport service', 180, 1000, 0,
          [supplies(4000), cmd('tc_mod', value=5)], '')], 90)

    # Superseded building bookkeeping describes a stock/shipping award now.
    # Keep its old snapshot/helper events and IDs registered for compatibility.
    import construction_safety
    for row in construction_safety.REPORT:
        if row['event'] == 'american_base_finish_0':
            row['previous_buildings'] = row['buildings']
            row['buildings'] = []
            row['delivery_policy'] = 'Superseded by occupation-safe national supplies and convoy pools; no construction.'

    # Supply-only German aid must not require Japan to have spare oil, either
    # when selecting the offer or when its delivery becomes due.
    _stock_project(by, 'axis_fuel', 1942, 'Choose a finite shipment to Germany',
        'Send a one-time German aid mission while Japan and Germany are at peace with each other. '
        'Either alternative costs 100 money and 1,000 supplies and takes 120 days. '
        'The fuel alternative additionally pays 1,000 Japanese oil now, keeping a 2,000-oil reserve, and delivers 800 oil to Germany. '
        'The supply alternative needs no oil and delivers 1,500 German supplies. No alliance or continuing trade is created. '
        'If Germany disappears or becomes an enemy before delivery, all paid inputs are returned.',
        'flag = JX_PACIFIC exists = GER NOT = { ' + war('GER') + ' }',
        'exists = GER NOT = { ' + war('GER') + ' }',
        [('Pay for the limited fuel shipment', 100, 1000, 1000,
          [cmd('trigger', which='@axis_fuel_arrives')], 'oil = 3000'),
         ('Send supply support without an oil payment', 100, 1000, 0,
          [cmd('trigger', which='@axis_supplies_arrive')], '')], 120)
    by['axis_supplies_arrive'].actions[0].commands = [supplies(1500)]

    by['siberian_rail'].desc = ('Support the occupied Siberian railway belt without pretending to own or rebuild Soviet infrastructure. '
        'Keep Vladivostok, Khabarovsk and Chita through the 180-day work period. Pay 200 money and 1,500 supplies. '
        'Choose railway crews and field depots for 5 percent more transport capacity plus 1,500 supplies, '
        'or a 4,500-supply operating reserve. Supplies enter Japan\'s national stock; transport to the front remains necessary. '
        'There are no new divisions, production discounts or provincial buildings. Losing a required centre returns the payment.')
    by['siberian_rail'].actions[1].name = 'Build the larger Siberian operating reserve'
    for i in (0, 1):
        by[f'siberian_rail_finish_{i}'].desc = by['siberian_rail'].desc + ' The payment was already taken.'
    _replace_discount(by['siberian_rail_finish_1'], [supplies(4500)], by['siberian_rail'].desc)

    by['naval_treaty'].desc = ('At peace from 1947, choose a civilian shipyard conversion or merchant-fleet reconstruction. '
        'Both cost 200 money and 700 supplies and take 60 days. Conversion adds 3 IC at Tokyo and removes 2 dissent, '
        'but adds 40 construction days to naval orders for 1,080 days; it requires legal Japanese ownership, research and room for the factories. '
        'Merchant reconstruction instead delivers 200 convoy transports, 60 convoy escorts and 2,000 supplies, with no naval construction penalty. '
        'These are convoy pools, not troop transports or warships. Renewed war before completion refunds the payment.')
    by['naval_treaty'].actions[0].name = 'Convert shipyards to civilian factories; accept the naval delay'
    by['naval_treaty'].actions[1].name = 'Reconstruct merchant shipping and operating stocks'
    _replace_discount(by['naval_treaty_finish_1'],
                      [cmd('transport_pool', which=-1, value=200), cmd('escort_pool', which=-1, value=60), supplies(2000)],
                      by['naval_treaty'].desc)

    by['colombo_station'].actions[1].name = 'Fund the escorted Indian Ocean supply route'
    by['colombo_station'].desc = ('While holding Colombo from 1942, pay 60 money and 350 supplies for a 150-day support programme. '
        'If Japan legally owns the site, has the research and room, the first option adds 2 radar and 2 AA levels. '
        'Its port and airfield already start at level ten and are not expanded. '
        'The alternative works during occupation: 60 convoy transports, 20 escorts and 1,500 supplies for Japan\'s national reserve. '
        'Hold Colombo until completion or the payment returns. This does not change India\'s government or canal access.')
    _replace_discount(by['colombo_station_finish_1'],
                      [cmd('transport_pool', which=-1, value=60), cmd('escort_pool', which=-1, value=20), supplies(1500)],
                      by['colombo_station'].desc)
    # The old alternative was range, not construction time.
    by['colombo_station_finish_1'].actions[0].commands = [c for c in by['colombo_station_finish_1'].actions[0].commands if 'type = range ' not in c]

    manual = []
    for e in EVENTS:
        if e.country == 'JAP' and not e.triggered and e.module == 'activities' and e.gate != 'ai = yes ai = no':
            e.decision = True; e.manual_only = True; manual.append(e.key)
            e.desc += '\n\nOpen this optional programme in Decisions when its map requirements are met. It does not open automatically.'
            for a in e.actions:
                if any('type = setflag which = JX_' + e.key + '_WAIT' in c for c in a.commands):
                    a.name = 'Leave this proposal available'; a.commands = []
    assert ids == {e.key: e.id for e in EVENTS}
    REPORT.update(rebuilt=['american_base', 'axis_fuel'], reward_replaced=['siberian_rail', 'naval_treaty', 'colombo_station'],
                  manual_activities=manual, american_ports=list(US_PORTS))
    return REPORT
