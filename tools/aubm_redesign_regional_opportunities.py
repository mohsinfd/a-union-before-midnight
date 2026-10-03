"""Route-free Suez, Himalayan/western investments and replacement training.

Exact legacy-wrapper replacement only. Local wars, governments, provinces,
costs, annual limits, hold timers and reward commands are preserved. This is
not proof of native hold-time or country-government behavior.
"""
from dh_save_spans import Node, parse, replace
from aubm_redesign_campaign_access import canonical, OLD_SOVEREIGN, predicate_roots

SOURCE_MODULE = '43_wartime_settlements.txt'
FAMILIES = {
    'canal_defence': tuple(range(9289860, 9289865)),
    'himalayan_investment': tuple(range(9289930, 9289934)),
    'western_investment': tuple(range(9289934, 9289938)),
    'replacement_training': (9289880,),
}
EVENTS = {eid: family for family, ids in FAMILIES.items() for eid in ids}
GUARD = 'exists = IND NOT = { ispuppet = IND }'
PROSE = {
    9289860: ('Hold the Canal', 'Axis troops threaten Egypt. Keep Suez and Port Said in Indian, British or Egyptian hands, with three Indian land divisions in either canal province for 30 days. India must fight the threatening Axis power and remain at peace with Britain and Egypt. Ownership need not change.'),
    9289861: ('The Canal Defence Is Interrupted', 'The required deployment or friendly control was lost. This attempt cannot earn the reward. After the original 30-day review closes, another attempt can begin if the Axis threat and defensive position return.'),
    9289862: ('Thirty Days on the Canal', 'The observation period has ended. The next review checks whether Indian troops maintained the required position. No reward is granted by this notice alone.'),
    9289863: ('India Keeps the Canal Open', 'Indian troops held their canal positions through the 30-day review. Gain 1500 supplies, 150 money, +1 transport capacity modifier and -2 dissent, once. Britain need not surrender the canal. No alliance, declaration or province transfer occurs.'),
    9289864: ('The Canal Review Closes', 'The required position did not hold. No reward is paid. A future attempt remains possible if the threat and defensive deployment return.'),
    9289930: ('Secure the Himalayan Settlement', 'Tibet must be an actual Indian puppet, at peace with India, owning and controlling Lhasa. Hold that settlement for 90 days to unlock investment. Chinese agreements cannot give India Tibet. Joining another alliance does not by itself end this opportunity.'),
    9289931: ('The Himalayan Settlement Is Shaken', 'The required Tibetan government or control of Lhasa was lost, or India ceased to be sovereign. Readiness is cleared. Restore the position to begin another 90-day attempt; no previous reward is repeated.'),
    9289932: ('The Himalayan Settlement Holds', 'The 90-day requirement has been met. A funded Himalayan network is now available while the required Tibetan government and control of Lhasa remain. This recognition does not force peace, create a puppet or transfer territory.'),
    9289933: ('Invest in the Himalayan Network', 'After the 90-day requirement, spend 200 money and 1000 supplies for +3 transport capacity modifier and +2 supply output, once. Tibet must still be an Indian puppet holding Lhasa. This funds the existing settlement; it does not create one.'),
    9289934: ('Secure the Western Corridor', 'Keep Tehran and Kabul under secure Indian rule or their Indian puppet governments, at peace with both countries, for 90 days. The corridor is its own opportunity: neither a Japanese nor a Soviet victory is required.'),
    9289935: ('The Western Corridor Is Broken', 'The required governments or control of Tehran and Kabul were lost, or India ceased to be sovereign. Readiness is cleared. Restore the corridor to begin another 90-day attempt; no previous reward is repeated.'),
    9289936: ('The Western Corridor Holds', 'The 90-day requirement has been met. India may fund the corridor while Tehran and Kabul remain secure under Indian rule or Indian puppet governments. This does not force peace or create those governments.'),
    9289937: ('Invest in the Western Corridor', 'After the 90-day requirement, spend 300 money and 1000 supplies for +5 transport capacity modifier and +3 supply output, once. Tehran and Kabul must remain secure under Indian rule or Indian puppet governments, at peace with India.'),
    9289880: ('Train Another Replacement Class', 'War with Japan or the USSR strains the regiments. With at least 100 divisions and manpower below 400, spend 100 money and 900 supplies, accepting +1 dissent, for 180 manpower. Available once each calendar year from 1940; fighting both enemies does not grant two classes.'),
}


def transform(files):
    output, records = dict(files), {}
    for path, text in files.items():
        if path.replace('\\', '/').rsplit('/', 1)[-1] != SOURCE_MODULE:
            continue
        edits = []
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            if eid not in EVENTS:
                continue
            changed = []
            def visit(node):
                for f in node.fields:
                    if isinstance(f.value, Node):
                        if f.key == 'AND' and canonical(f.value) == OLD_SOVEREIGN:
                            edits.append((f.start, f.end, 'AND = { ' + GUARD + ' }'))
                            changed.append('global_route_and_unrelated_alliance_exclusions')
                        else:
                            visit(f.value)
                    elif f.key == 'flag' and f.value == 'ind_lib1_enabled':
                        edits.append((f.start, f.end, 'exists = IND'))
                        changed.append('manual_campaign_opt_in')
            for root in predicate_roots(ev):
                visit(root)
            title, description = PROSE[eid]
            assert len(title) <= 58 and len(description) <= 340
            for key, value in [('name', title), ('desc', description)]:
                f = ev.field(key)
                if f.value != value:
                    edits.append((f.value_start, f.end, '"' + value + '"'))
            records[eid] = [dict(dimension='regional_opportunities', status='reviewed',
                path=path, family=EVENTS[eid], changed_predicates=len(changed),
                detail='Replace exact route/opt-in wrapper with Indian existence and sovereignty; preserve local conditions and effects.',
                remaining=['Hold timing and automatic modal behavior remain unverified in the engine.',
                           'No government creation, peace, reward amount or calendar has been changed.'])]
        output[path] = replace(text, edits)
    missing = set(EVENTS) - set(records)
    if missing:
        raise ValueError('Regional opportunity family is incomplete: ' + str(sorted(missing)))
    return output, records
