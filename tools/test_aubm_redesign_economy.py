"""Static/state-model tests, not a Darkest Hour engine or balance simulation."""
import unittest
from pathlib import Path

from dh_save_spans import Node, parse, walk
from aubm_redesign_economy import PLANS, actions, ledger, transform

ROOT = Path(__file__).resolve().parents[1]
PATH = 'db/events/india_v3/20_development.txt'


def index(files):
    return {int(e.get('id')): e for text in files.values() for e in parse(text).all('event')}


def evaluate(node, state):
    values = []
    for field in node.fields:
        key, val = field.key, field.value
        if key == 'AND':
            ok = evaluate(val, state)
        elif key == 'OR':
            ok = any(evaluate(Node(fields=[f]), state) for f in val.fields)
        elif key == 'NOT':
            ok = not evaluate(val, state)
        elif key == 'flag':
            ok = val in state['flags']
        elif key == 'owned':
            ok = int(val.get('province')) not in state.get('lost', set())
        elif key in ('ai', 'atwar'):
            ok = state.get(key, 'no') == val
        elif key in ('year', 'month', 'money', 'supplies', 'manpower'):
            ok = state.get(key, 99999) >= int(val)
        else:
            raise AssertionError('Unmodelled predicate: ' + str(key))
        values.append(ok)
    return all(values)


class EconomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {PATH: (ROOT / 'mod' / PATH).read_bytes().decode('latin1')}
        cls.result, cls.records = transform(cls.source)
        cls.before, cls.after = index(cls.source), index(cls.result)

    def state(self, eid):
        # Include all prerequisites, but not this event's completion token.
        flags = {f.value for n in walk(self.after[eid].get('decision'))
                 for f in n.fields if f.key == 'flag'}
        flags.remove(self.records[eid][0]['completion_flag'])
        return dict(flags=flags, year=1940, month=6, money=10000,
                    supplies=10000, manpower=10000, ai='no', atwar='no')

    def test_six_existing_ids_only_input_unchanged(self):
        self.assertEqual(set(PLANS), set(self.records))
        self.assertEqual(set(self.before), set(self.after))
        self.assertEqual(self.source[PATH], (ROOT / 'mod' / PATH).read_bytes().decode('latin1'))
        self.assertEqual(transform(self.result)[0], self.result)

    def test_factory_totals_and_research_are_distinct(self):
        targets = {9270200: [24, 16, 6], 9270201: [8, 5, 4],
                   9270202: [32, 16, 10], 9270203: [24, 18, 8],
                   9270204: [10, 0, 6], 9270205: [34, 20, 12]}
        for eid, totals in targets.items():
            actual = [ledger(a.value.all('command')).get('construct:ic', 0)
                      for a in actions(self.after[eid])[:3]]
            self.assertEqual(totals, actual)
            for before, after in zip(self.records[eid][0]['before'], self.records[eid][0]['after']):
                self.assertLessEqual(after.get('construct:ic', 0), before.get('construct:ic', 0))
        science = self.records[9270204][0]['after']
        self.assertEqual([2, 4, 2], [a['research_mod'] for a in science])
        self.assertEqual(-350, science[1]['money'])
        self.assertEqual(500, science[2]['supplies'])
        plans = self.records[9270205][0]['after']
        self.assertEqual([5, 0, 1], [a.get('industrial_modifier:ic', 0) for a in plans])
        self.assertEqual(5, plans[1]['tc_mod'])

    def test_explicit_reserves_and_no_free_manpower(self):
        after = lambda eid, option: self.records[eid][0]['after'][option]
        self.assertEqual(600, after(9270200, 2)['supplies'])
        self.assertEqual(40, after(9270201, 1)['transport_pool'])
        self.assertEqual(10, after(9270201, 1)['escort_pool'])
        port_commands = actions(self.after[9270201])[1].value.all('command')
        pool_commands = [c for c in port_commands if c.get('type') in ('transport_pool', 'escort_pool')]
        self.assertEqual(['IND', 'IND'], [c.get('which') for c in pool_commands])
        self.assertEqual(500, after(9270201, 2)['oilpool'])
        self.assertEqual(1000, after(9270202, 1)['metalpool'])
        self.assertEqual(2000, after(9270202, 1)['energypool'])
        self.assertEqual(2500, after(9270203, 1)['energypool'])
        self.assertEqual(-10, after(9270203, 2)['manpowerpool'])

    def test_current_state_and_once_only_for_every_paid_action(self):
        for eid in PLANS:
            event, state = self.after[eid], self.state(eid)
            paid = [a.value for a in actions(event)[:3]]
            self.assertTrue(evaluate(event.get('decision'), state), eid)
            for action in paid:
                self.assertTrue(evaluate(action.get('trigger'), state), (eid, action.get('name')))
                # Model the completion write; every sibling and repeated call closes.
                done = dict(state, flags=state['flags'] | {self.records[eid][0]['completion_flag']})
                self.assertFalse(evaluate(event.get('decision'), done), eid)
                for sibling in paid:
                    self.assertFalse(evaluate(sibling.get('trigger'), done), eid)
                self.assertFalse(evaluate(action.get('trigger'), dict(state, year=1932)), eid)
                self.assertFalse(evaluate(action.get('trigger'), dict(state, year=1965)), eid)
                if eid != 9270204:
                    self.assertFalse(evaluate(action.get('trigger'), dict(state, atwar='yes')), eid)
                missing = dict(state, flags=set())
                self.assertFalse(evaluate(action.get('trigger'), missing), eid)

    def test_every_actual_debit_gated_at_offer_and_action(self):
        for eid in PLANS:
            for action in [a.value for a in actions(self.after[eid])[:3]]:
                for command in action.all('command'):
                    if command.get('type') not in ('money', 'supplies', 'manpowerpool'):
                        continue
                    value = int(command.get('value'))
                    if value >= 0:
                        continue
                    stock = {'manpowerpool': 'manpower'}.get(command.get('type'), command.get('type'))
                    exact = dict(self.state(eid), **{stock: -value})
                    short = dict(exact, **{stock: -value-1})
                    self.assertTrue(evaluate(action.get('trigger'), exact), (eid, stock))
                    self.assertFalse(evaluate(action.get('trigger'), short), (eid, stock))
            broke = dict(self.state(eid), money=0, supplies=0, manpower=0)
            self.assertFalse(evaluate(self.after[eid].get('decision_trigger'), broke), eid)

    def test_lost_province_blocks_full_price_partial_investment(self):
        for eid in PLANS:
            for af in actions(self.after[eid])[:3]:
                sites = [c.get('where') for c in af.value.all('command') if c.get('type') == 'construct']
                if sites:
                    state = dict(self.state(eid), lost={int(sites[0])})
                    self.assertFalse(evaluate(af.value.get('trigger'), state), eid)

    def test_free_defer_no_flags_no_callbacks_and_still_available(self):
        for eid in PLANS:
            ev, state = self.after[eid], self.state(eid)
            close = actions(ev)[3].value
            self.assertEqual('yes', ev.get('persistent'))
            self.assertFalse(close.all('command'))
            self.assertTrue(evaluate(close.get('trigger'), dict(state, money=0, supplies=0, atwar='yes')))
            self.assertFalse(evaluate(close.get('trigger'), dict(state, ai='yes')))
            self.assertTrue(evaluate(ev.get('decision'), state))

    def test_flags_teams_caps_pictures_retained(self):
        def commands(ev, kinds):
            return [c for af in actions(ev) for c in af.value.all('command') if c.get('type') in kinds]
        def canon(n):
            return [(f.key, canon(f.value) if isinstance(f.value, Node) else f.value) for f in n.fields]
        for eid in PLANS:
            a, b = self.before[eid], self.after[eid]
            self.assertEqual(a.get('picture'), b.get('picture'))
            self.assertEqual([canon(c) for c in commands(a, {'setflag', 'waketeam', 'domestic'})],
                             [canon(c) for c in commands(b, {'setflag', 'waketeam', 'domestic'})])
            for ca, cb in zip([c for c in commands(a, {'construct'}) if c.get('which') != 'ic'],
                              [c for c in commands(b, {'construct'}) if c.get('which') != 'ic']):
                self.assertEqual(canon(ca), canon(cb))
            self.assertLessEqual(len(b.get('desc')), 340)
            self.assertTrue(all(len(af.value.get('name')) <= 50 for af in actions(b)))

    def test_empty_boolean_operators_and_engine_claims_absent(self):
        for eid in PLANS:
            for n in walk(self.after[eid]):
                for f in n.fields:
                    if f.key in ('AND', 'OR', 'NOT'):
                        self.assertTrue(f.value.fields, eid)
            self.assertFalse(self.records[eid][0]['engine_tested'])
            self.assertIn('pending', ' '.join(self.records[eid][0]['remaining']))

    def test_duplicate_id_is_not_silently_balanced_twice(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate economy event'):
            transform({**self.source, 'duplicate.txt': self.source[PATH]})


if __name__ == '__main__':
    unittest.main()
