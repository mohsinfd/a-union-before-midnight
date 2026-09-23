import copy
from pathlib import Path
import unittest
from dh_save_spans import Node, parse, walk
from aubm_redesign_campaign_access import canonical, predicate_roots
from aubm_redesign_regional_opportunities import transform, EVENTS, SOURCE_MODULE
from test_aubm_liberator import State, evaluate, pair

ROOT = Path(__file__).resolve().parents[1]
PATH = 'db/events/aubm_v4/' + SOURCE_MODULE


class RegionalOpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {PATH: (ROOT / 'mod' / PATH).read_bytes().decode('latin1')}
        cls.output, cls.records = transform(cls.source)
        cls.before = {int(e.get('id')): e for e in parse(cls.source[PATH]).all('event')}
        cls.after = {int(e.get('id')): e for e in parse(cls.output[PATH]).all('event')}

    def allowed(self, eid, state, action=False):
        e = self.after[eid].get('action_a') if action else self.after[eid]
        return evaluate(canonical(e.get('trigger', Node())), state)

    def suez(self):
        s = State(flags=set(), wars={pair(('IND', 'GER'))}, alliances={pair(('IND', 'ENG'))})
        s.control = {900: 'ENG', 791: 'EGY', 783: 'GER'}
        s.garrisons = {('IND', 900): 3}
        return s

    def test_allied_india_can_defend_suez_without_route_or_optin(self):
        s = self.suez()
        for route in (None, 'allied', 'german', 'soviet', 'japan', 'sovereign'):
            t = copy.deepcopy(s)
            if route:
                t.flags.add('ind_aubm_route_' + route)
            self.assertTrue(self.allowed(9289860, t))
            self.assertTrue(self.allowed(9289860, t, True))

    def test_canal_war_garrison_and_friendly_control_still_required(self):
        for change in ('peace', 'enemy_canal', 'small_garrison', 'hostile_britain', 'puppet_india'):
            s = self.suez()
            if change == 'peace': s.wars.clear()
            if change == 'enemy_canal': s.control[791] = 'GER'
            if change == 'small_garrison': s.garrisons[('IND', 900)] = 2
            if change == 'hostile_britain': s.wars.add(pair(('IND', 'ENG')))
            if change == 'puppet_india': s.puppets['IND'] = 'ENG'
            self.assertFalse(self.allowed(9289860, s), change)

    def test_suez_reward_needs_due_valid_unpaid_record(self):
        s = self.suez(); s.flags |= {'ind_lib1_suez_watch', 'ind_lib1_suez_due'}
        self.assertTrue(self.allowed(9289863, s, True))
        for flag in ('ind_lib1_suez_invalid', 'ind_lib1_suez_reward'):
            bad = copy.deepcopy(s); bad.flags.add(flag)
            self.assertFalse(self.allowed(9289863, bad, True))
        s.flags.remove('ind_lib1_suez_due')
        self.assertFalse(self.allowed(9289863, s, True))

    def test_tibet_investment_uses_actual_puppet_and_paid_closure(self):
        s = State(flags={'ind_lib1_tib_mission_ready'}, alliances={pair(('IND', 'JAP'))})
        s.exists.add('TIB'); s.puppets['TIB'] = 'IND'
        s.owned[1289] = s.control[1289] = 'TIB'
        self.assertTrue(self.allowed(9289933, s, True))
        s.resources['money'] = 199
        self.assertFalse(self.allowed(9289933, s, True))
        s.resources['money'] = 200; s.flags.add('ind_lib1_tib_mission_paid')
        self.assertFalse(self.allowed(9289933, s, True))
        s.flags.clear(); s.puppets['TIB'] = 'JAP'
        self.assertFalse(self.allowed(9289930, s))

    def test_western_corridor_can_mix_direct_rule_and_puppet(self):
        s = State(flags={'ind_lib1_west_mission_ready'}, alliances={pair(('IND', 'SOV'))})
        s.exists.add('PER'); s.puppets['PER'] = 'IND'
        s.owned = {1085: 'PER', 2171: 'IND'}; s.control = dict(s.owned)
        self.assertTrue(self.allowed(9289937, s, True))
        s.wars.add(pair(('IND', 'PER')))
        self.assertFalse(self.allowed(9289937, s, True))

    def test_training_remains_annual_and_enemy_specific(self):
        s = State(flags=set(), wars={pair(('IND', 'JAP'))}, alliances={pair(('IND', 'ENG'))})
        self.assertTrue(self.allowed(9289880, s, True))
        s.flags.add('ind_lib1_replacement_1940')
        self.assertFalse(self.allowed(9289880, s, True))
        s.year = 1941
        self.assertTrue(self.allowed(9289880, s, True))
        s.resources['manpower'] = 400
        self.assertFalse(self.allowed(9289880, s, True))
        s.resources['manpower'] = 80; s.wars = {pair(('IND', 'ITA'))}
        self.assertFalse(self.allowed(9289880, s, True))

    def test_effects_costs_and_hold_timers_preserved(self):
        protected = {'war', 'owned', 'control', 'puppet', 'event', 'money', 'supplies', 'garrison', 'year', 'manpower', 'army'}
        def observations(e):
            return [(f.key, canonical(f.value) if isinstance(f.value, Node) else f.value)
                    for root in predicate_roots(e) for n in walk(root) for f in n.fields
                    if f.key in protected or (f.key == 'flag' and str(f.value).startswith('ind_lib1_') and f.value != 'ind_lib1_enabled')]
        for eid in EVENTS:
            self.assertEqual(observations(self.before[eid]), observations(self.after[eid]))
            old = [canonical(c) for n in walk(self.before[eid]) for c in n.all('command')]
            new = [canonical(c) for n in walk(self.after[eid]) for c in n.all('command')]
            self.assertEqual(old, new, eid)

    def test_exact_scope_idempotent_no_unnamed_family(self):
        self.assertEqual(14, len(self.records))
        self.assertEqual(set(self.before), set(self.after))
        for eid in set(self.before) - set(EVENTS):
            a, b = self.before[eid], self.after[eid]
            self.assertEqual(self.source[PATH][a.start:a.end], self.output[PATH][b.start:b.end])
        self.assertEqual(self.output, transform(self.output)[0])


if __name__ == '__main__': unittest.main()
