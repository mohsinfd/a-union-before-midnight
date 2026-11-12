"""Whole-Japanese-roster validation and command-derived custom trait copy.

apply() follows force_delivery_audit.apply(), before localisation generation.
apply_personnel() follows all personnel writers. No balance values are changed.
"""
from collections import Counter
import math
import re

import japan_personnel
import specialist_units as sp

POSITIONS = {
    'Head of State': 'HeadOfState', 'Head of Government': 'HeadOfGovernment',
    'Foreign Minister': 'ForeignMinister', 'Minister of Armament': 'ArmamentMinister',
    'Minister of Security': 'MinisterOfSecurity',
    'Head of Military Intelligence': 'MinisterOfIntelligence',
    'Chief of Staff': 'ChiefOfStaff', 'Chief of Army': 'ChiefOfArmy',
    'Chief of Navy': 'ChiefOfNavy', 'Chief of Air Force': 'ChiefOfAir',
}
POLITICS = set('NS FA PA SC ML SL SD LE LWR ST'.split())
REPORT = {}

# Exact enums/defaults from the native minister_personalities.txt header.
SCHEMA = {
    'research': ('all infantry armor naval aircraft industry land_doctrines secret_weapons naval_doctrines air_doctrines', 'time cost', 'all', 'time'),
    'production': ('production consumer supplies reinforcement upgrading', 'national non_national', 'production', 'national'),
    'resource': ('all oil energy metal rare_materials money', '', 'all', None),
    'province': ('all ic coastalfort landfort flak infra air_base naval_base radar_station nuclear_reactor rocket_test', 'all time cost', 'all', 'all'),
    'unit': (None, 'all time cost organisation morale attack defence speed', 'all', 'all'),
    'extra': (None, 'all time cost organisation morale attack defence', 'all', 'all'),
    'diplomacy_chances': ('alliance influence_nation ask_for_military_access assume_military_control demand_territory offer_non_aggression sue_for_peace trade', 'all weak_target same_alignment opposite_alignment democracies dictatorships close_government_type', None, 'all'),
    'diplomacy_cost': ('all declare_war offer_alliance bring_to_alliance join_alliance leave_alliance ban_from_alliance influence_nation ask_for_military_access cancel_military_access revoke_military_access assume_military_control cancel_military_control send_expeditionary_force guarantee_independence annex_nation demand_territory trade offer_non_aggression cancel_non_aggression offer_trade_agreement cancel_trade_agreement cancel_peace_treaty sue_for_peace release_puppet liberate_nation dont_send_forces', 'all weak_target same_alignment opposite_alignment democracies dictatorships close_government_type national', 'all', 'all'),
    'intelligence_chances': ('all steal_blueprint minister_assassination smear_campaign coup sabotage_industry nuclear_sabotage found_partisans massmedia disrupt_techteam', 'non_national national', 'all', 'non_national'),
    'intelligence_cost': ('all steal_blueprint minister_assassination smear_campaign coup sabotage_industry nuclear_sabotage found_partisans massmedia disrupt_techteam', 'non_national national', 'all', 'non_national'),
    'intelligence_report': ('all land navy production', '', 'all', None),
    # The shipped Dismal Enigma definition explicitly uses when=all; all is
    # the combined-scope form alongside the header's national/non_national.
    'intelligence_network': ('all increase_intelligence_founding decrease_intelligence_founding daily_maintenance', 'all national non_national', 'all', 'all'),
    'leader_skill': ('', '', None, None), 'dissent': ('', '', None, None),
    'tc_mod': ('', '', None, None), 'supply_consumption': ('', '', None, None),
    'detection': ('land navy convoy', '', None, None),
    'belligerence': ('peace war declare_war', '', None, None),
    'populationgrowth': ('', 'national non_national', None, 'national'),
    'stockpile': ('industry supplies all', 'war peace all', 'all', 'all'),
}


def command_node(command):
    typ, which, when, value = command
    return [('type', typ)] + ([('which', which)] if which is not None else []) + ([('when', when)] if when is not None else []) + [('value', str(value))]


def describe(command):
    typ, which, when, value = command
    percent = f'{value * 100:+g}%'
    labels = {'destroyer': 'Destroyer', 'transport': 'Troop transport',
              'carrier': 'Fleet carrier', 'battleship': 'Battleship',
              'battlecruiser': 'Battlecruiser', 'interceptor': 'Interceptor',
              'naval_bomber': 'Naval bomber', 'land': 'Land division',
              'air': 'Air division', 'navy': 'Naval division',
              'cag': 'Carrier air group', 'light_cag': 'Light carrier air group'}
    if typ in {'unit', 'extra'}:
        stat = {'all': 'construction IC cost and time', 'cost': 'construction IC cost',
                'time': 'construction time'}.get(when or 'all', when or 'all')
        text = f'{labels[which]} {stat} {percent}'
        if which == 'destroyer' and (when or 'all') in {'all', 'time', 'cost'}:
            text += ' (also convoy escorts)'
        if which == 'transport' and (when or 'all') in {'all', 'time', 'cost'}:
            text += ' (also convoy transports)'
        return text
    if typ == 'province':
        building = {'infra': 'Infrastructure', 'ic': 'Factory'}[which]
        stat = 'IC cost' if when == 'cost' else 'time'
        return f'{building} construction {stat} {percent}'
    if typ == 'research':
        category = {'naval': 'Naval equipment', 'aircraft': 'Aircraft equipment'}[which]
        return f'{category} research {when or "time"} {percent} (doctrines excluded)'
    if typ == 'production':
        label = {'consumer': 'Consumer goods requirement', 'supplies': 'Supply production'}[which]
        return f'{label} {percent}'
    if typ == 'resource':
        return f'All resource output {percent} (including oil and money; trade imports excluded)'
    if typ == 'tc_mod':
        return f'Transport capacity {percent}'
    if typ == 'supply_consumption':
        return f'National unit supply consumption {percent}'
    if typ == 'diplomacy_cost':
        return f'Diplomatic mission cost {percent}'
    if typ == 'diplomacy_chances':
        return f'Alliance acceptance modifier {value:+g} points'
    raise ValueError('Missing custom-description formatter: ' + str(command))


def apply():
    """Derive the 13 custom descriptions from their actual command tuples."""
    changes = []
    for i, entry in enumerate(japan_personnel.PERSONALITIES):
        trait, pid, position, name, old_desc, commands = entry
        desc = '. '.join(describe(c) for c in commands) + '. Active only while appointed. Other national modifiers still apply.'
        japan_personnel.PERSONALITIES[i] = (trait, pid, position, name, desc, commands)
        if desc != old_desc:
            changes.append({'trait': trait, 'id': pid, 'before': old_desc, 'after': desc})
    if changes:
        REPORT['description_changes'] = changes
    return changes


def validate(roster_text, personality_text):
    root = sp.parse(personality_text)
    definitions = sp.getall(root, 'minister')
    traits = Counter(sp.get(m, 'trait').casefold() for m in definitions)
    ids = Counter(sp.get(m, 'id') for m in definitions)
    if any(n != 1 for n in traits.values()) or any(n != 1 for n in ids.values()):
        raise ValueError('Duplicate minister personality name or numeric ID')
    lookup = {sp.get(m, 'trait').casefold(): m for m in definitions}
    unit_types = {k for k, v in sp.parse(sp.read(sp.SOURCE / 'db/units/division_types.txt')) if isinstance(v, list) and sp.get(v, 'type')}
    unit_types |= set(sp.CLASSES) | {'all', 'land', 'navy', 'air'}
    import unique_divisions
    unit_types |= set(unique_divisions.CLASSES)
    brigade_types = {k for k, v in sp.parse(sp.read(sp.SOURCE / 'db/units/brigade_types.txt')) if isinstance(v, list) and sp.get(v, 'type')}
    brigade_types |= {'all', 'land', 'navy', 'air'}
    import unique_attachments
    brigade_types |= set(unique_attachments.ATTACHMENTS)
    rows = [r for line in roster_text.splitlines() if (r := line.split(';'))[0].isdigit()]
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('Duplicate Japanese appointment ID')
    resolved = []
    checked = set()
    normalized = []
    for r in rows:
        if len(r) != 11 or r[-1].upper() != 'X':
            raise ValueError('Malformed Japanese appointment: ' + str(r))
        m = lookup.get(r[7].casefold())
        if m is None:
            raise ValueError('Unresolved trait on minister ' + r[0] + ': ' + r[7])
        expected = POSITIONS.get(r[1])
        actual = sp.get(m, 'position', 'all')
        if expected is None or actual.casefold() not in {'all', expected.casefold()}:
            raise ValueError('Office mismatch on minister ' + r[0])
        if not (int(r[3]) <= int(r[4]) <= int(r[5])) or r[6] not in POLITICS:
            raise ValueError('Invalid dates/ideology on minister ' + r[0])
        resolved.append({'id': int(r[0]), 'name': r[2], 'office': r[1], 'trait': sp.get(m, 'trait'),
                         'personality_id': int(sp.get(m, 'id')), 'start': int(r[3]), 'retirement': int(r[4]), 'end': int(r[5])})
        if r[7].casefold() in checked:
            continue
        checked.add(r[7].casefold())
        for c in sp.getall(m, 'command'):
            typ = sp.get(c, 'type')
            if typ not in SCHEMA or any(k not in {'type', 'which', 'when', 'value'} for k, _ in c):
                raise ValueError('Unsupported minister command: ' + str(c))
            if len({k for k, _ in c}) != len(c):
                raise ValueError('Repeated minister command field: ' + str(c))
            allowed_which, allowed_when, default_which, default_when = SCHEMA[typ]
            allowed_which = unit_types if typ == 'unit' else brigade_types if typ == 'extra' else set(allowed_which.split())
            which, when = sp.get(c, 'which', default_which), sp.get(c, 'when', default_when)
            if allowed_which and default_which is None and which is None:
                raise ValueError('Missing required which field: ' + str(c))
            if which is not None and which not in allowed_which:
                raise ValueError('Unsupported which field: ' + str(c))
            if when is not None and when not in set(allowed_when.split()):
                raise ValueError('Unsupported when field: ' + str(c))
            value = float(sp.get(c, 'value'))
            if not math.isfinite(value) or value == 0:
                raise ValueError('Invalid minister command value: ' + str(c))
            normalized.append({'trait': sp.get(m, 'trait'), 'type': typ, 'which': which, 'when': when, 'value': value})
    return {'roster': resolved, 'traits': len(checked), 'commands': normalized,
            'definitions': len(definitions), 'fallback_to_generic': 0}


def apply_personnel(target, read, write, parse, serialise):
    """Validate all generated Japanese appointments after every writer."""
    result = validate(read(target / 'db/ministers/ministers_jap.csv'),
                      read(target / 'db/ministers/minister_personalities.txt'))
    REPORT['roster_count'] = len(result['roster'])
    REPORT['trait_count'] = result['traits']
    REPORT['command_count'] = len(result['commands'])
    return result
