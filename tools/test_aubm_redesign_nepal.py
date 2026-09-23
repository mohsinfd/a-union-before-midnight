"""Script-state tests; native inherit and delayed delivery are not simulated."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest

from dh_save_spans import Node, parse
from aubm_redesign_diplomacy import actions
from aubm_redesign_nepal import (transform, NEW_EVENT_IDS, CORE_PROVINCES, CORE_DAYS, CONQUEST_DAYS,
    PENDING, ACCEPTED, REJECTED, COOLDOWN, VERIFY, FAILED, CORE_PENDING, DUE, CORED, INTEGRATED)


@dataclass
class State:
    flags: set = field(default_factory=set)
    countries: set = field(default_factory=lambda: {'IND', 'NEP', 'ENG', 'BHU'})
    wars: set = field(default_factory=set)
    masters: dict = field(default_factory=lambda: {'NEP': 'ENG'})
    resources: dict = field(default_factory=lambda: {'money': 10000, 'supplies': 10000})
    owners: dict = field(default_factory=lambda: {1457: 'NEP'})
    controllers: dict = field(default_factory=lambda: {1457: 'NEP'})
    cores: set = field(default_factory=set)


def evaluate(n, s):
    if not isinstance(n, Node): return True
    result = []
    for f in n.fields:
        k, v = f.key, f.value
        if k == 'AND': r = evaluate(v, s)
        elif k == 'OR': r = any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'NOT': r = not any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'flag': r = v in s.flags
        elif k == 'exists': r = v in s.countries
        elif k == 'ispuppet': r = v in s.masters
        elif k == 'puppet':
            tags = v.all('country'); r = s.masters.get(tags[0]) == tags[1]
        elif k == 'war': r = frozenset(v.all('country')) in s.wars
        elif k == 'atwar': r = any(v in w for w in s.wars)
        elif k in ('owned', 'control'):
            r = (s.owners if k == 'owned' else s.controllers).get(int(v.get('province'))) == v.get('data')
        elif k in ('money', 'supplies'): r = s.resources[k] >= float(v)
        elif k == 'ai': r = v == 'no'
        else: raise AssertionError('Unsupported predicate ' + k)
        result.append(r)
    return all(result)


def apply(a, s):
    effects = []
    for c in a.all('command'):
        if not evaluate(c.get('trigger'), s): continue
        k, which = c.get('type'), c.get('which')
        if k == 'setflag': s.flags.add(which)
        elif k == 'clrflag': s.flags.discard(which)
        elif k in ('money', 'supplies'): s.resources[k] += float(c.get('value'))
        elif k == 'addcore': s.cores.add(int(which))
        # Do NOT fake an engine inheritance result or execute queued events.
        effects.append((k, which, c.get('value'), c.get('when')))
    return effects


class NepalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'mod/db/events/india_v3/40_diplomacy.txt'
        cls.source = {str(path): path.read_text(encoding='cp1252')}
        cls.changed, cls.records = transform(cls.source)
        cls.events = {int(e.get('id')): e for t in cls.changed.values() for e in parse(t).all('event')}

    def a(self, eid, key='action_a'): return self.events[eid].get(key)
    def allowed(self, eid, s, key='action_a'): return evaluate(self.a(eid, key).get('trigger'), s)

    def test_new_event_prose_and_buttons_fit_script_budgets(self):
        for eid in NEW_EVENT_IDS:
            event = self.events[eid]
            self.assertLessEqual(len(event.get('name')), 58)
            self.assertLessEqual(len(event.get('desc')), 340)
            for af in actions(event):
                self.assertLessEqual(len(af.value.get('name')), 58, (eid, af.value.get('name')))

    def test_initial_nepal_offer_keeps_british_puppet_context_and_sets_token_before_delivery(self):
        s = State()
        self.assertTrue(self.allowed(9270410, s, 'action_c'))
        effects = apply(self.a(9270410, 'action_c'), s)
        self.assertIn(PENDING, s.flags)
        self.assertIn(('event', '9270414', None, '1'), effects)
        self.assertTrue(self.allowed(9270414, s))

    def test_refusal_cooldown_and_repeatable_expensive_retry(self):
        s = State(flags={PENDING})
        apply(self.a(9270414, 'action_b'), s)
        self.assertIn(REJECTED, s.flags)
        apply(self.a(9270416, 'action_a'), s)
        self.assertNotIn(PENDING, s.flags)
        self.assertIn(COOLDOWN, s.flags)
        self.assertFalse(self.allowed(9398200, s))
        self.assertFalse(self.allowed(9270410, s, 'action_c'))
        self.assertFalse(self.allowed(9270418, s))
        apply(self.a(9398202), s)  # callback bookkeeping only, no timing claim
        self.assertTrue(self.allowed(9398200, s))
        self.assertFalse(self.allowed(9270418, s))
        before = dict(s.resources)
        effects = apply(self.a(9398200), s)
        self.assertEqual(s.resources['money'], before['money'] - 650)
        self.assertEqual(s.resources['supplies'], before['supplies'] - 1000)
        self.assertIn(('dissent', None, '2', None), effects)
        self.assertFalse(self.allowed(9398200, s))
        apply(self.a(9398201, 'action_b'), s)
        apply(self.a(9270416, 'action_b'), s)
        apply(self.a(9398202), s)
        self.assertTrue(self.allowed(9398200, s))

    def test_retry_affordability_and_free_cancel(self):
        for money, supplies, expected in ((650, 1000, True), (649, 1000, False), (650, 999, False)):
            s = State(flags={'ind_v3_nepal_refused'}, resources={'money': money, 'supplies': supplies})
            self.assertEqual(self.allowed(9398200, s), expected)
        cancel = self.a(9398200, 'action_b')
        self.assertFalse(cancel.all('command'))

    def test_current_war_or_new_master_blocks_offer_and_replies(self):
        for change in ('ind_war', 'nepal_war', 'rival_master'):
            s = State(flags={PENDING, ACCEPTED, 'ind_v3_nepal_refused'})
            if change == 'ind_war': s.wars.add(frozenset(('IND', 'JAP')))
            elif change == 'nepal_war': s.wars.add(frozenset(('NEP', 'JAP')))
            else: s.masters['NEP'] = 'JAP'
            self.assertFalse(self.allowed(9398201, s))
            self.assertFalse(self.allowed(9270415, s))
            available = [a.value for a in actions(self.events[9270415]) if evaluate(a.value.get('trigger'), s)]
            self.assertEqual(len(available), 1)
            apply(available[0], s)
            self.assertNotIn(PENDING, s.flags)
            self.assertNotIn(INTEGRATED, s.flags)

    def test_inherit_command_does_not_itself_award_core_or_integrated_state(self):
        s = State(flags={PENDING, ACCEPTED})
        effects = apply(self.a(9270415), s)
        self.assertIn(('inherit', 'NEP', None, None), effects)
        self.assertIn(VERIFY, s.flags)
        self.assertNotIn(INTEGRATED, s.flags)
        self.assertEqual(s.cores, set())
        self.assertFalse(any(k in ('manpowerpool', 'dissent', 'addcore') for k, *_ in effects))
        self.assertFalse(self.allowed(9398203, s))
        self.assertTrue(self.allowed(9398203, s, 'action_b'))
        apply(self.a(9398203, 'action_b'), s)
        self.assertIn(FAILED, s.flags)
        self.assertNotIn(VERIFY, s.flags)

    def test_verified_merger_starts_1080_day_queue_then_adds_kathmandu_core(self):
        s = State(flags={VERIFY}, countries={'IND', 'ENG', 'BHU'}, owners={1457: 'IND'}, controllers={1457: 'IND'})
        self.assertTrue(self.allowed(9398203, s))
        effects = apply(self.a(9398203), s)
        self.assertIn(INTEGRATED, s.flags)
        self.assertIn(('event', '9398204', None, str(CORE_DAYS)), effects)
        self.assertIn(('manpowerpool', None, '20', None), effects)
        self.assertEqual(s.cores, set())
        self.assertTrue(self.allowed(9398204, s))
        apply(self.a(9398204), s)  # action after native due-time, not clock simulation
        self.assertEqual(s.cores, set(CORE_PROVINCES))
        self.assertIn(CORED, s.flags)
        self.assertFalse(self.allowed(9398204, s))

    def test_matured_but_lost_territory_can_complete_when_recovered(self):
        s = State(flags={CORE_PENDING, INTEGRATED}, countries={'IND', 'ENG'}, owners={1457: 'IND'}, controllers={1457: 'JAP'})
        self.assertFalse(self.allowed(9398204, s))
        apply(self.a(9398204, 'action_b'), s)
        self.assertIn(DUE, s.flags)
        self.assertEqual(s.cores, set())
        self.assertFalse(self.allowed(9398205, s))
        s.controllers[1457] = 'IND'
        self.assertTrue(self.allowed(9398205, s))
        apply(self.a(9398205), s)
        self.assertEqual(s.cores, {1457})

    def test_no_nepal_core_before_verified_delayed_integration(self):
        for eid in (9270415, 9270416):
            self.assertFalse(any(c.get('type') == 'addcore' for a in actions(self.events[eid]) for c in a.value.all('command')))
        self.assertTrue(any(c.get('type') == 'addclaim' for c in self.a(9270416, 'action_c').all('command')))

    def test_post_annexation_integration_is_expensive_and_takes_five_years(self):
        s = State(countries={'IND', 'ENG', 'BHU'}, owners={1457: 'IND'}, controllers={1457: 'IND'})
        before = dict(s.resources)
        self.assertTrue(self.allowed(9398206, s))
        effects = apply(self.a(9398206), s)
        self.assertEqual(s.resources['money'], before['money'] - 1500)
        self.assertEqual(s.resources['supplies'], before['supplies'] - 2500)
        self.assertIn(('dissent', None, '5', None), effects)
        self.assertIn(('event', '9398204', None, str(CONQUEST_DAYS)), effects)
        self.assertNotIn(('manpowerpool', None, '20', None), effects)
        self.assertEqual(s.cores, set())
        self.assertFalse(self.allowed(9398206, s))
        apply(self.a(9398204), s)  # only after native queue matures
        self.assertEqual(s.cores, {1457})

    def test_occupation_project_rejects_live_nepal_lost_ownership_and_insufficient_funds(self):
        s = State(owners={1457: 'IND'}, controllers={1457: 'IND'})
        self.assertFalse(self.allowed(9398206, s))
        s.countries.remove('NEP')
        s.resources['money'] = 1499
        self.assertFalse(self.allowed(9398206, s))
        s.resources['money'] = 1500
        s.resources['supplies'] = 2499
        self.assertFalse(self.allowed(9398206, s))
        s.resources['supplies'] = 2500
        s.owners[1457] = 'ENG'
        self.assertFalse(self.allowed(9398206, s))
        self.assertFalse(self.a(9398206, 'action_b').all('command'))

    def test_generated_narrative_is_short_and_no_mutation_timer_can_repeat(self):
        for eid in NEW_EVENT_IDS:
            self.assertLessEqual(len(self.events[eid].get('desc')), 340, eid)
        s = State(flags={VERIFY}, countries={'IND'}, owners={1457: 'IND'}, controllers={1457: 'IND'})
        apply(self.a(9398203), s)
        self.assertFalse(self.allowed(9398203, s))
        self.assertFalse(self.allowed(9398206, s))

    def test_bhutan_standalone_events_and_grand_offer_bhutan_commands_preserved(self):
        def raw_events(files):
            return {int(f.value.get('id')): text[f.start:f.end] for text in files.values()
                    for f in parse(text).fields if f.key == 'event'}
        before, after = raw_events(self.source), raw_events(self.changed)
        for eid in (9270411, 9270412, 9270413, 9270417, 9270419):
            self.assertEqual(before[eid], after[eid])
        self.assertIn('type = trigger which = 9270419', after[9270410])
        self.assertTrue(any(c.get('type') == 'addcore' and c.get('which') == '1456' for c in self.a(9270412).all('command')))

    def test_new_ids_collision_checks_idempotence_and_queued_format(self):
        self.assertEqual(transform(self.changed)[0], self.changed)
        self.assertEqual(NEW_EVENT_IDS, set(self.events) - {int(e.get('id')) for t in self.source.values() for e in parse(t).all('event')})
        for eid in (9398201, 9398202, 9398203, 9398204):
            for key in ('trigger', 'date', 'offset', 'deathdate'):
                self.assertIsNone(self.events[eid].get(key))
        collision = dict(self.source)
        collision['collision'] = 'event = { id = 9398200 country = IND }'
        with self.assertRaises(ValueError): transform(collision)


if __name__ == '__main__': unittest.main()
