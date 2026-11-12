"""R9 force value: a usable mixed air force and specialist personnel parity.

Call apply() after human_campaign.apply(). Call apply_personnel() after
japan_personnel.apply_roster(). No new event IDs, unit classes or technologies.
"""
from copy import deepcopy

from catalog import EVENTS, cmd
import specialist_units as sp


AIR_PRIORITY = {
    'interceptor': (3.5, 42), 'multi_role': (4, 42), 'cas': (4, 46),
    'tactical_bomber': (5, 46), 'naval_bomber': (4, 48),
    'transport_plane': (5, 48),
}
AIR_COMMON = (1.5, 18)
AIR_GROUPS = (
    ('interceptor', 'multi_role', 'cas'),
    ('tactical_bomber', 'naval_bomber', 'transport_plane'),
)
REPORT = {}


def _rebates(priority):
    """Totals, not an additional full rebate on top of shared tooling."""
    return {u: AIR_PRIORITY[u] if u in priority else AIR_COMMON for u in AIR_PRIORITY}


def apply():
    if REPORT.get('catalogue_applied'):
        return
    by = {e.key: e for e in EVENTS}
    if 'air_production' not in by:
        raise RuntimeError('force_value.apply must follow human_campaign.apply')
    names = {
        'interceptor': 'Interceptor', 'multi_role': 'Multirole', 'cas': 'CAS',
        'tactical_bomber': 'Tactical bomber', 'naval_bomber': 'Naval bomber',
        'transport_plane': 'Transport aircraft',
    }
    summaries = []
    for i, priority in enumerate(AIR_GROUPS):
        finish = by[f'air_production_finish_{i}']
        action = finish.actions[0]
        # Replace the existing award, preserving its pending/done bookkeeping.
        action.commands = [c for c in action.commands
                           if sp.get(sp.parse(c), 'type') not in {'build_cost', 'build_time'}]
        rebates = _rebates(priority)
        action.commands[:0] = [cmd(kind, which=u, when='on_upgrade', value=-v)
                              for u, values in rebates.items()
                              for kind, v in zip(('build_cost', 'build_time'), values)]
        summary = '; '.join(f'{names[u]} -{rebates[u][0]:g} IC / -{rebates[u][1]:g} days'
                            for u in AIR_PRIORITY)
        summaries.append(('Fighter priority: ' if i == 0 else 'Bomber priority: ') + summary + '.')
        finish.desc = ('The aircraft expansion is ready. ' + summaries[-1] +
                       ' These are total fixed reductions for future normal orders. '
                       'Research, manpower, fuel and supply costs remain necessary.')
    offer = by['air_production']
    offer.desc = (
        'Expand common engine, airframe and repair-parts production, then choose which '
        'aircraft factories receive the larger investment. Both alternatives reduce '
        'construction cost by 1.5 IC and time by 18 days for all six listed classes. '
        'The chosen priority receives the larger TOTAL reductions below, replacing '
        'the common allowance. You can build a mixed air force while keeping a clear '
        'production advantage in your selected role.\n\n' + '\n\n'.join(summaries) +
        '\n\nSetup: 180 money and 1,000 supplies; completion: 180 days. '
        'These are fixed reductions, not percentages of a later model. Technology, '
        'ministers, policy and gearing still affect the final queue price and time. '
        'No aircraft, research, oil or supply consumption is granted for free.')
    # The R8 physical designs already have a strong price/manpower advantage.
    # Explain the actual battlefield decision instead of adding more firepower.
    by['introduce_d_10'].desc = (
        'Naval Base Forces cost 4 base IC for 100 days and 5 manpower, versus '
        '4 IC for 160 days and 10 manpower for a normal garrison. Their smaller '
        'supply and transport demand helps hold ports and airfields while field '
        'divisions advance. They have less firepower, cannot march and cannot '
        'retreat from a lost battle. Transport and defend them accordingly. '
        'Infantry research unlocks later equipment; normal production is required.')
    by['introduce_d_11'].desc = (
        'Jungle Light Infantry cost 4 base IC for 190 days and 8 manpower, versus '
        '5 IC for 290 days and 13 manpower for most ordinary infantry models. '
        'Jungle and swamp attack and movement penalties are smaller; firepower '
        'and defence are lower. They save men, shipping and supply on long tropical '
        'campaigns. They retain infantry landing penalties and offer no special '
        'advantage in Siberian snow, mountains or open plains. Infantry research '
        'unlocks later equipment; use Marines or SNLF against defended beaches.')
    by['snlf_open_recruitment'].desc = (
        'Marine research unlocks Special Naval Landing Divisions. Their base price '
        'is 6 IC for 240 days and 9 manpower, versus 8 IC for 420 days and 15 manpower '
        'for a standard Marine division before postwar mechanisation. They use less '
        'supply and shipping and have a smaller landing and river penalty, but less '
        'firepower and defence. Useful for a broad Pacific assault force; full Marines '
        'retain greater strength in each crowded assault slot. Later models follow '
        'Marine research through 1949. Order them normally; there is no setup payment.')
    REPORT.update(catalogue_applied=True, air={str(i): _rebates(g) for i, g in enumerate(AIR_GROUPS)},
                  specialist_models='Retained R8 prices, stats and research progression')


def mirror_personnel(node, allowed_traits=None):
    """Mirror only concrete base-class minister effects, including their penalties.

    Group effects such as land already cover custom land classes; copying those
    would apply the same policy twice. Native formation effects remain unchanged.
    """
    changed = []
    for minister in sp.getall(node, 'minister'):
        if allowed_traits is not None and sp.get(minister, 'trait') not in allowed_traits:
            continue
        commands = sp.getall(minister, 'command')
        for c in list(commands):
            if sp.get(c, 'type') != 'unit':
                continue
            for unit, info in sp.CLASSES.items():
                if sp.get(c, 'which') != info['base']:
                    continue
                clone = deepcopy(c)
                sp.replace(clone, 'which', unit)
                if clone in commands:
                    continue
                minister.append(('command', clone))
                commands.append(clone)
                changed.append({'personality': sp.get(minister, 'trait'),
                                'base': info['base'], 'unit': unit,
                                'when': sp.get(c, 'when', 'all'),
                                'value': sp.get(c, 'value')})
    return changed


def apply_personnel(target, read, write, parse, serialise):
    path = target / 'db/ministers/minister_personalities.txt'
    node = parse(read(path))
    traits = {r[7] for line in read(target / 'db/ministers/ministers_jap.csv').splitlines()
              if len(r := line.split(';')) > 7 and r[0].isdigit()}
    changed = mirror_personnel(node, traits)
    if changed:
        write(path, serialise(node) + '\n')
    REPORT['personnel_mirrors'] = changed
    return changed
