"""Bounded, funded industrial feedstocks for the human Japan campaign.

Call apply() after human_campaign.apply(). Existing IDs are never reassigned;
only additional completion/receiver events are appended. No installed files
or saves are read or changed by this module.
"""
from catalog import *

REPORT = {}
# Provincial increments, before territorial efficiency and country modifiers.
# Balanced capacity supports industry; fuel priority needs imported/captured metal.
STAGES = (
    ('home_fuel', 1935, 350, 2400, 1000, 240, 1544,
     ((160, 40, 10, 20), (200, 20, 0, 35))),
    ('war_fuel', 1940, 500, 3600, 2000, 270, 1545,
     ((320, 90, 30, 25), (400, 40, 10, 50))),
)
BATCHES = ((12000, 800, 100, 6000), (24000, 1600, 200, 12000))
ENERGY_RESERVE = 9000
METAL_RESERVE = 500


def _terminal_commands(energy, stock, cash, oil, refund=False):
    payment = ([cmd('energypool', value=energy), supplies(stock), money(cash)]
               if refund else [cmd('oilpool', value=oil)])
    return payment + [clear('FUEL_BATCH_PENDING'), flag('FUEL_BATCH_WAIT'),
                      later('fuel_batch_reset', 45)]


def _delivery(e, amounts):
    energy, stock, cash, oil = amounts
    pending = 'flag = JX_FUEL_BATCH_PENDING'
    e.desc = (f'The paid batch is ready: {oil:,} oil. Check the displayed oil storage '
              'limit before accepting; this event cannot measure that dynamic limit. '
              'If there is too little room, cancel for an exact return of the energy, '
              'supplies and money. Above the stated oil threshold only cancellation '
              'is available. Either choice starts the 45-day cooldown.')
    e.actions = [
        Action(f'Receive {oil:,} oil', _terminal_commands(*amounts),
               gate=human()+' '+pending+f' NOT = {{ oil = {oil} }}', chance=100),
        Action('Cancel and recover the paid inputs',
               _terminal_commands(*amounts, refund=True), gate=pending),
    ]


def apply():
    if REPORT:
        return
    by = {e.key: e for e in EVENTS}
    if 'wartime_fuel_batch' not in by:
        raise RuntimeError('endurance_economy.apply() requires human_campaign.apply() first')
    old_ids = {e.key: e.id for e in EVENTS}
    for key, year, cash, stock, metal, days, mine, alternatives in STAGES:
        offer = by[key]
        sites = ' '.join(owned(p)+' '+control(p) for p in (1552, 1550, mine))
        prior = '' if key == 'home_fuel' else 'flag = JX_home_fuel_DONE atwar = yes'
        offer.title = ('Build the home fuel and minerals complex' if key == 'home_fuel'
                       else 'Expand wartime fuel and minerals capacity')
        descriptions = []
        for label, (energy, steel, rare, oil) in zip(('Balanced industry', 'Fuel priority'), alternatives):
            descriptions.append(f'{label}: +{energy} energy, +{steel} metal, +{rare} rare materials '
                                f'at the northern works, +{oil} oil at Tokyo and -20 energy at Yokohama, daily provincial output.')
        offer.desc = ('Choose one substantial ahistorical expansion. '+ ' '.join(descriptions)+
                      ' Coal extraction, mineral processing and recycling are included; this replaces '
                      'the previous oil-only award. Output follows territorial efficiency, country '
                      'modifiers and convoy delivery. The works stay with their provinces if lost. '
                      'Fuel priority sacrifices metal and rare-material self-sufficiency: factories '
                      'may still need imports or conquest. Native energy-to-oil conversion competes '
                      'for the same coal. Neither option removes operating costs. '
                      f'Pay {cash} money, {stock:,} supplies and {metal:,} metal now; keep at least 500 metal unspent. Work takes {days} days. '
                      'Only one option per stage. Losing a required site before completion returns the exact payment.')
        offer.gate = active()+' '+no_state(key)+' '+prior+' '+sites
        offer.ready = ''
        offer.actions = []
        for i, (energy, steel, rare, oil) in enumerate(alternatives):
            finish_key = f'{key}_finish_{i}'
            rewards = [cmd('add_prov_resource', which=mine, where=kind, value=value)
                       for kind, value in (('energy', energy), ('metal', steel), ('rare_materials', rare)) if value]
            rewards += [cmd('add_prov_resource', which=1552, where='oil', value=oil),
                        cmd('add_prov_resource', which=1550, where='energy', value=-20)]
            valid = human()+' flag = JX_'+key+'_PENDING '+sites
            invalid = 'flag = JX_'+key+'_PENDING NOT = { AND = { '+human()+' '+sites+' } }'
            actions = [Action('Put the selected works into service', rewards+[flag(key+'_DONE'), clear(key+'_PENDING')], gate=valid, chance=100),
                       Action('Return the investment; the works cannot finish',
                              [money(cash), supplies(stock), cmd('metalpool', value=metal), clear(key+'_PENDING'),
                               flag(key+'_WAIT'), later(key+'_return', 90)], gate=invalid)]
            if i == 0:
                finish = by[finish_key]
                finish.actions = actions
                finish.desc = offer.desc+' The investment has already been paid.'
                finish.title = offer.title+' - completed'
            else:
                event(finish_key, offer.title+' - completed', offer.desc+' The investment has already been paid.',
                      triggered=True, actions=actions, module='endurance_economy', art='industry')
            offer.actions.append(Action(('Fund balanced industry', 'Prioritise fuel and coal')[i],
                         [money(-cash), supplies(-stock), cmd('metalpool', value=-metal),
                          flag(key+'_PENDING'), later(finish_key, days)],
                         gate=f'money = {cash} supplies = {stock} metal = {metal+METAL_RESERVE}', chance=100 if i == 0 else 0))
        offer.actions += [Action('Ask again in three months', [flag(key+'_WAIT'), later(key+'_return', 90)]),
                          Action('Drop this proposal permanently', [flag(key+'_DISMISSED')])]

    offer = by['wartime_fuel_batch']
    available = active()+' atwar = yes NOT = { flag = JX_FUEL_BATCH_PENDING flag = JX_FUEL_BATCH_WAIT flag = JX_FUEL_BATCH_DISMISSED }'
    offer.gate = available+' NOT = { oil = 12000 }'
    offer.actions = []
    for i, amounts in enumerate(BATCHES):
        energy, stock, cash, oil = amounts
        offer.actions.append(Action(f'Convert {energy:,} energy into {oil:,} oil',
                    [cmd('energypool', value=-energy), supplies(-stock), money(-cash),
                     flag('FUEL_BATCH_PENDING'), later(f'fuel_batch_delivery_{i}', 45)],
                    gate=available+f' energy = {energy+ENERGY_RESERVE} supplies = {stock} money = {cash} '
                         f'flag = JX_strategic_storage_DONE flag = JX_{("home_fuel", "war_fuel")[i]}_DONE '
                         f'NOT = {{ oil = {oil} }}'))
        _delivery(by[f'fuel_batch_delivery_{i}'], amounts)
    small = (3000, 200, 25, 1500)
    offer.actions.insert(0, Action('Order a small 1,500-oil batch',
                [cmd('energypool', value=-3000), supplies(-200), money(-25), flag('FUEL_BATCH_PENDING'),
                 later('endurance_small_fuel_delivery', 45)],
                gate=available+' energy = 12000 supplies = 200 money = 25 NOT = { oil = 1500 }'))
    offer.actions.append(Action('Hide this fuel order permanently', [flag('FUEL_BATCH_DISMISSED')]))
    receiver = event('endurance_small_fuel_delivery', 'The small fuel batch is ready', '',
                     triggered=True, module='endurance_economy', art='industry')
    _delivery(receiver, small)
    offer.desc = ('Convert paid coal stocks into oil while at war. Small: 3,000 energy, 200 supplies and '
                  '25 money for 1,500 oil. Standard: 12,000 energy, 800 supplies and 100 money for 6,000 oil. '
                  'Large: double the standard costs for 12,000 oil. Delivery takes 45 days, followed by '
                  '45 days before another order. One batch at a time. Every option leaves at least '
                  '9,000 energy unspent when ordered; daily industry and native conversion still consume it. '
                  'Standard and large orders require the completed strategic-storage programme; standard '
                  'also needs the home works and large needs the wartime expansion. Orders '
                  'and acceptance require oil below the size of that batch. This is a fixed low-stock '
                  'safeguard, not a measurement of storage room. Check the actual displayed cap. At '
                  'delivery you may cancel for the exact inputs, with the same cooldown. The small '
                  'batch helps a low-capacity economy. You can leave the decision unused or hide it.')
    assert all(by[key].id == value for key, value in old_ids.items())
    REPORT.update(stages=STAGES, batches=BATCHES, small_batch=small,
                  energy_reserve=ENERGY_RESERVE, stable_old_ids=len(old_ids))
