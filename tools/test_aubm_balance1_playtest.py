"""Regression tests against the installed, registered BALANCE1 input baseline.

Set AUBM_TEST_MOD to use another complete installation. No installation writes.
"""
import os
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, walk
import aubm_balance1_playtest as b

DEFAULT = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1')


def indexed(files):
    return {int(e.get('id')): e for p, t in files.items() if p in b.PATH_IDS for e in parse(t).all('event')}


def passes(n, controls=(), flags=(), war=True):
    """Small test evaluator for only the syntax used in the new hold conditions."""
    results = []
    for f in n.fields:
        k, v = f.key, f.value
        if k == 'AND': value = passes(v, controls, flags, war)
        elif k == 'OR': value = any(passes(Node(fields=[a]), controls, flags, war) for a in v.fields)
        elif k == 'NOT': value = not any(passes(Node(fields=[a]), controls, flags, war) for a in v.fields)
        elif k == 'flag': value = v in flags
        elif k == 'war': value = war
        elif k == 'control': value = int(v.get('province')) in controls
        else: raise AssertionError('Unsupported test condition: ' + str(k))
        results.append(value)
    return all(results)


class Balance1Playtest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(os.environ.get('AUBM_TEST_MOD', str(DEFAULT)))
        if not (cls.base / b.NORTH_PATH).exists(): raise unittest.SkipTest('Installed mod baseline unavailable')
        # Regress the pre-patch events after deployment too. Untouched native
        # model/tech definitions are still checked against the selected game.
        snapshot = Path(__file__).resolve().parents[1] / 'build/balance1/baseline'
        event_base = snapshot if snapshot.exists() and 'AUBM_TEST_MOD' not in os.environ else cls.base
        cls.source = {p: (event_base / p).read_text(encoding='latin1') for p in b.PATH_IDS}
        cls.output, cls.records = b.transform(cls.source)
        cls.events = indexed(cls.output)

    def test_idempotence_and_balanced_syntax(self):
        second, records = b.transform(self.output)
        self.assertEqual(second, self.output)
        self.assertEqual(records, {})
        self.assertTrue(b.NEW_IDS <= self.events.keys())

    def test_non_target_events_unchanged(self):
        for p, old in self.source.items():
            old_events = {int(e.get('id')): old[e.start:e.end] for e in parse(old).all('event')}
            new = self.output[p]
            new_events = {int(e.get('id')): new[e.start:e.end] for e in parse(new).all('event')}
            for eid in old_events.keys() - b.PATH_IDS[p]:
                self.assertEqual(old_events[eid], new_events[eid], f'Unowned event changed: {eid}')

    def test_airfield_complete_packages_and_cost_guards(self):
        e = self.events[9280152]
        for letter, wings in [('a', 1), ('b', 2), ('c', 1)]:
            a = e.get('action_' + letter)
            divisions = [c for c in a.all('command') if c.get('type') == 'add_division']
            self.assertEqual(len(divisions), 2 + wings)
            guards = [c for c in divisions if c.get('value') in ('garrison', 'militia')]
            self.assertEqual(len(guards), 2)
            self.assertEqual(len([c for c in a.all('command') if c.get('type') == 'construct']), 2)
            for kind, trigger_key in [('money', 'money'), ('supplies', 'supplies'), ('manpowerpool', 'manpower')]:
                debit = next(c for c in a.all('command') if c.get('type') == kind)
                self.assertEqual(-float(debit.get('value')), float(a.get('trigger').get(trigger_key)))
            for c in guards:
                allowed = parse((self.base / 'db/units/divisions' / (c.get('value') + '.txt')).read_bytes()).all('allowed_brigades')
                if c.get('where'): self.assertIn(c.get('where'), allowed)
            self.assertTrue(any(c.get('type') == 'setflag' and c.get('which') == 'ind_v4_airfield_security' for c in a.all('command')))
        self.assertIsNone(e.get('persistent'))

    def test_airfield_crew_debits_cover_the_actual_unit_models(self):
        for letter in 'abc':
            a = self.events[9280152].get('action_' + letter)
            needed = 0
            for c in a.all('command'):
                if c.get('type') != 'add_division': continue
                unit = parse((self.base / 'db/units/divisions' / (c.get('value') + '.txt')).read_bytes())
                needed += max(float(m.get('manpower', 0)) for m in unit.all('model'))
                if c.get('where'):
                    brigade = parse((self.base / 'db/units/brigades' / (c.get('where') + '.txt')).read_bytes())
                    needed += max(float(m.get('manpower', 0)) for m in brigade.all('model'))
            self.assertGreaterEqual(float(a.get('trigger').get('manpower')), needed)

    def test_airfield_exact_models_are_available_from_starting_technology(self):
        self.assertEqual(b.AIRFIELD_MODELS, {'interceptor': 7, 'tactical_bomber': 5,
                         'transport_plane': 0, 'garrison': 4, 'militia': 4})
        scenario = parse((self.base / 'scenarios/1933/british raj.inc').read_bytes())
        country = next(n for n in walk(scenario) if n.get('tag') == 'IND')
        starting_tech = set(country.get('techapps').atoms())
        available, scrapped = set(), set()
        for path in ('db/tech/aircraft_tech.txt', 'db/tech/infantry_tech.txt'):
            for app in walk(parse((self.base / path).read_bytes())):
                if app.get('id') not in starting_tech or not isinstance(app.get('effects'), Node): continue
                for command in app.get('effects').all('command'):
                    if command.get('type') == 'new_model':
                        available.add((command.get('which'), int(command.get('value'))))
                    elif command.get('type') == 'scrap_model':
                        scrapped.add((command.get('which'), int(command.get('value'))))
        self.assertTrue(set(b.AIRFIELD_MODELS.items()) <= available)
        self.assertFalse(set(b.AIRFIELD_MODELS.items()) & scrapped)
        for letter in 'abc':
            for command in self.events[9280152].get('action_' + letter).all('command'):
                if command.get('type') != 'add_division': continue
                self.assertEqual(int(command.get('when')), b.AIRFIELD_MODELS[command.get('value')])

    def test_locked_ids_match_scenario_and_only_unlock(self):
        scenario = parse((self.base / 'scenarios/1933/british raj.inc').read_bytes())
        locked = {int(n.get('id').get('id')) for n in walk(scenario) if n.get('locked') == 'yes'}
        self.assertEqual(locked, set(b.LOCKED_IDS))
        event = self.events[9318103]
        self.assertEqual(event.get('trigger').get('atwar'), 'yes')
        for c in event.get('action_a').all('command'):
            self.assertIn(c.get('type'), ('unlock_division', 'setflag'))
            if c.get('type') == 'unlock_division':
                self.assertIsInstance(c.get('trigger').get('division_exists'), Node)
        for letter in 'abc':
            self.assertEqual(sum(c.get('type') == 'unlock_division' for c in self.events[9280111].get('action_' + letter).all('command')), 8)

    def test_tokyo_defer_keeps_existing_late_opening_valid(self):
        e = self.events[9280303]
        deferred = e.get('action_d')
        self.assertIsNotNone(deferred)
        self.assertEqual([c.get('type') for c in deferred.all('command')], ['setflag'])
        self.assertNotIn('ind_v4_early_japan_policy', [c.get('which') for c in deferred.all('command')])
        self.assertIsNone(e.get('persistent'))
        wars = [n.get('war') for n in walk(e.get('trigger')) if isinstance(n.get('war'), Node)]
        self.assertTrue(any('JAP' in w.all('country') for w in wars))

    def test_existing_choice_flags_survive(self):
        originals = indexed(self.source)
        for eid in set().union(*b.PATH_IDS.values()):
            for field in originals[eid].fields:
                if not field.key or not field.key.startswith('action') or not isinstance(field.value, Node): continue
                old = {c.get('which') for c in field.value.all('command') if c.get('type') == 'setflag'}
                revised = self.events[eid].get(field.key)
                new = {c.get('which') for c in revised.all('command') if c.get('type') == 'setflag'}
                self.assertTrue(old <= new, f'Lost established choice flag: {eid}/{field.key}: {old - new}')

    def test_northern_milestone_needs_depth_and_60_day_callback(self):
        e = self.events[9281942]
        flags = {'ind_aubm_wartime_framework', b.READY}
        self.assertFalse(passes(e.get('trigger'), {713, 1103}, flags))
        self.assertFalse(passes(e.get('trigger'), {713, 706}, flags))
        self.assertTrue(passes(e.get('trigger'), {713, 706, 663}, flags))
        self.assertTrue(passes(e.get('trigger'), {1103, 1099, 504, 1151}, flags))
        self.assertFalse(passes(e.get('trigger'), {713, 706, 663}, flags - {b.READY}))
        self.assertFalse(passes(e.get('trigger'), {713, 706, 663}, flags, war=False))
        self.assertFalse(passes(e.get('trigger'), {713, 706, 663}, flags | {'ind_aubm_national_northern_victory'}))
        queued = next(c for c in self.events[9318100].get('action_a').all('command') if c.get('type') == 'event')
        self.assertEqual(queued.get('when'), '60')
        callback = self.events[9318102]
        self.assertIsNone(callback.get('trigger')); self.assertIsNone(callback.get('date'))
        self.assertTrue(any(c.get('type') == 'clrflag' and c.get('which') == b.PENDING for c in callback.get('action_a').all('command')))

    def test_loss_during_or_after_timer_invalidates_hold(self):
        e = self.events[9318101]
        self.assertTrue(passes(e.get('trigger'), {713, 706}, {b.PENDING}))
        self.assertTrue(passes(e.get('trigger'), {713, 706}, {b.READY}))
        self.assertFalse(passes(e.get('trigger'), {713, 706, 663}, {b.PENDING}))
        callback_condition = self.events[9318102].get('action_a').all('command')[0].get('trigger')
        self.assertFalse(passes(callback_condition, {713, 706, 663}, {b.PENDING, b.BROKEN}))
        self.assertTrue(passes(callback_condition, {713, 706, 663}, {b.PENDING}))
        self.assertFalse(passes(callback_condition, {713, 706, 663}, set()))

    def test_partial_overlay_rejected(self):
        source = dict(self.source)
        source[b.NORTH_PATH] += '\nevent = { id = 9318100 country = IND }'
        with self.assertRaises(ValueError): b.transform(source)
        incomplete = dict(self.output)
        incomplete['db/events/india_v3/10_politics.txt'] = self.source['db/events/india_v3/10_politics.txt']
        with self.assertRaises(ValueError): b.transform(incomplete)

    def test_no_peace_puppet_or_economic_multiplier_added(self):
        forbidden = {'peace', 'make_puppet', 'puppet', 'independence', 'alliance', 'secedeprovince', 'industrial_modifier', 'build_time', 'build_cost'}
        for eid in b.NEW_IDS | {9280152}:
            for n in walk(self.events[eid]):
                self.assertNotIn(n.get('type'), forbidden)

    def test_existing_mountain_team_is_not_duplicated(self):
        teams = (self.base / 'db/tech/teams/teams_ind.csv').read_text(encoding='latin1')
        quetta = next(line.split(';') for line in teams.splitlines() if line.startswith('250027;'))
        self.assertLessEqual(int(quetta[4]), 1933)
        self.assertIn('mountain_training', quetta)
        self.assertNotIn('db/tech/teams/teams_ind.csv', self.output)


if __name__ == '__main__': unittest.main()
