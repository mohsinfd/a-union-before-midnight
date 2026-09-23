"""Dockyard modifier bookkeeping and debt predicates; no native game emulation."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest
from dh_save_spans import Node, parse
from aubm_redesign_diplomacy import actions
from aubm_redesign_runtime_safety import (transform, NEW_EVENT_IDS, EDITED_IDS,
    HULLS, LEGACY, STANDARD, MATURE, READY, PEACE)


@dataclass
class State:
    flags: set = field(default_factory=set)
    wars: set = field(default_factory=set)
    modifiers: dict = field(default_factory=lambda: {h: 0 for h in HULLS})


def permits(node, state):
    if not isinstance(node, Node): return True
    def ev(f):
        k, v = f.key, f.value
        if k == 'AND': return permits(v, state)
        if k == 'OR': return any(ev(x) for x in v.fields)
        if k == 'NOT': return not any(ev(x) for x in v.fields)
        if k == 'flag': return v in state.flags
        if k == 'atwar': return bool(state.wars) == (v == 'yes')
        if k == 'exists': return True
        if k == 'ai': return v == 'no'
        raise AssertionError(k)
    return all(ev(f) for f in node.fields)


def apply(a, state):
    if not permits(a.get('trigger'), state): return None
    effects = []
    for c in a.all('command'):
        if not permits(c.get('trigger'), state): continue
        kind, which = c.get('type'), c.get('which')
        if kind == 'setflag': state.flags.add(which)
        if kind == 'clrflag': state.flags.discard(which)
        if kind == 'build_time': state.modifiers[which] += int(c.get('value'))
        effects.append((kind, which, c.get('value')))
    return effects


def canon(node):
    return [(f.key, canon(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields]


class RuntimeSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events'
        cls.source = {p: (root / p).read_text(encoding='cp1252') for p in ('india_v3/32_navy.txt', 'aubm_v4/44_wartime_economy.txt')}
        cls.output, cls.records = transform(cls.source)
        cls.before = {int(e.get('id')): e for t in cls.source.values() for e in parse(t).all('event')}
        cls.events = {int(e.get('id')): e for t in cls.output.values() for e in parse(t).all('event')}

    def a(self, eid): return self.events[eid].get('action_a')
    def total(self, s, expected): self.assertEqual(set(s.modifiers.values()), {expected})
    def fire(self, eid, s):
        if not permits(self.events[eid].get('trigger'), s): return None
        return apply(self.a(eid), s)

    def test_exact_registered_ids_idempotence_and_input_preserved(self):
        source = dict(self.source)
        self.assertEqual(set(self.events) - set(self.before), NEW_EVENT_IDS)
        self.assertEqual(set(self.records), NEW_EVENT_IDS | EDITED_IDS)
        self.assertEqual(transform(self.output)[0], self.output)
        self.assertEqual(source, self.source)
        for eid in self.before.keys() - EDITED_IDS:
            self.assertEqual(canon(self.before[eid]), canon(self.events[eid]), eid)

    def test_fresh_peace_standard_then_repeated_war_peace_cycles(self):
        s = State(flags={'ind_v3_dockyard_act'})
        self.assertIsNotNone(self.fire(9271111, s)); self.total(s, -25)
        self.assertTrue({STANDARD, MATURE, READY, PEACE} <= s.flags)
        for eid in (9271111, 9271112, 9297180, 9297181, 9297182): self.assertIsNone(self.fire(eid, s))
        for _ in range(3):
            s.wars.add('JAP')
            self.assertIsNotNone(self.fire(9297182, s)); self.total(s, -50)
            self.assertIsNone(self.fire(9297182, s))
            s.wars.clear()
            self.assertIsNotNone(self.fire(9297181, s)); self.total(s, -25)
            self.assertIsNone(self.fire(9297181, s))

    def test_fresh_wartime_standard_is_immediately_full_bonus(self):
        s = State(flags={'ind_v3_dockyard_act'}, wars={'JAP'})
        self.fire(9271111, s); self.total(s, -50)
        self.assertNotIn(PEACE, s.flags)
        self.assertIsNone(self.fire(9297180, s))
        self.assertIsNone(self.fire(9297182, s))
        s.wars.clear(); self.fire(9297181, s); self.total(s, -25)

    def test_legacy_differential_retains_old_earned_hull_modifiers(self):
        for wartime in (False, True):
            s = State(flags={STANDARD, 'ind_v3_dockyard_act'}, wars={'JAP'} if wartime else set(), modifiers=dict(LEGACY))
            self.assertIsNone(self.fire(9271111, s))
            self.assertIsNotNone(self.fire(9271112, s))
            self.total(s, -50 if wartime else -25)
            self.assertIsNone(self.fire(9271112, s))

    def test_legacy_mature_initializer_preserves_earned_war_delta_once(self):
        for wartime in (False, True):
            s = State(flags={MATURE}, wars={'JAP'} if wartime else set(), modifiers={h: -50 for h in HULLS})
            self.assertIsNotNone(self.fire(9297180, s)); self.total(s, -50 if wartime else -25)
            self.assertIsNone(self.fire(9297180, s))
            self.assertIsNone(self.fire(9297181, s))
            self.assertIsNone(self.fire(9297182, s))

    def test_stale_transition_action_has_no_delta_and_no_earned_flag_cleanup(self):
        s = State(flags={MATURE, READY, PEACE}, wars={'JAP'}, modifiers={h: -25 for h in HULLS})
        self.assertTrue(permits(self.a(9297182).get('trigger'), s))
        s.wars.clear()
        self.assertIsNone(apply(self.a(9297182), s)); self.total(s, -25)
        close = actions(self.events[9297182])[1].value
        self.assertEqual(apply(close, s), [])
        self.assertEqual(s.flags, {MATURE, READY, PEACE})

    def test_peace_means_no_remaining_indian_war(self):
        s = State(flags={'ind_v3_dockyard_act'}, wars={'JAP', 'SOV'})
        self.fire(9271111, s)
        s.wars.remove('JAP')
        self.assertIsNone(self.fire(9297181, s)); self.total(s, -50)
        s.wars.clear(); self.fire(9297181, s); self.total(s, -25)

    def test_unearned_controller_has_no_bonus(self):
        s = State()
        for eid in NEW_EVENT_IDS:
            self.assertIsNone(self.fire(eid, s))
            self.assertIsNone(apply(self.a(eid), s))
        self.total(s, 0)

    def test_other_earned_modifiers_costs_technology_are_not_reset(self):
        s = State(flags={'ind_v3_dockyard_act'}, modifiers={h: -7 for h in HULLS})
        self.fire(9271111, s); self.total(s, -32)
        s.wars.add('JAP'); self.fire(9297182, s); self.total(s, -57)
        s.wars.clear(); self.fire(9297181, s); self.total(s, -32)
        for eid in (9271111, 9271112):
            old = [canon(c) for c in self.before[eid].get('action_a').all('command') if c.get('type') != 'build_time']
            new = [canon(c) for c in self.a(eid).all('command') if c.get('type') != 'build_time' and c.get('which') not in (READY, PEACE)]
            self.assertEqual(old, new)
        for eid in NEW_EVENT_IDS | {9271111, 9271112}:
            for c in self.a(eid).all('command'):
                if c.get('type') == 'build_time':
                    self.assertEqual((c.get('when'), c.get('where')), ('on_upgrade', 'relative'))

    def test_debt_cap_nor_truth_table_repayment_and_nonborrowing_alternatives(self):
        for eid in (9282080, 9282081):
            for tier4, overhang in ((False, False), (True, False), (False, True), (True, True)):
                s = State(wars={'JAP'})
                if tier4: s.flags.add('ind_aubm_debt_tier_4')
                if overhang: s.flags.add('ind_aubm_debt_overhang')
                for key in ('action_a', 'action_c'):
                    self.assertEqual(permits(self.events[eid].get(key).get('trigger'), s), not (tier4 or overhang))
                for key in ('action_b', 'action_d'):
                    self.assertTrue(permits(self.events[eid].get(key).get('trigger'), s))
                s.flags.clear()  # Repayment's original flag cleanup reopens lending.
                self.assertTrue(permits(self.a(eid).get('trigger'), s))

    def test_finance_commands_and_original_narrative_untouched(self):
        for eid in (9282080, 9282081):
            self.assertEqual(self.events[eid].get('desc'), self.before[eid].get('desc'))
            for old, new in zip(actions(self.before[eid]), actions(self.events[eid])):
                self.assertEqual([canon(c) for c in old.value.all('command')], [canon(c) for c in new.value.all('command')])
        peace = State()
        self.assertFalse(permits(self.a(9282081).get('trigger'), peace))
        self.assertTrue(permits(self.events[9282081].get('action_d').get('trigger'), peace))

    def test_collisions_partial_port_and_already_compiled_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'collision'):
            transform(dict(self.source, bad='event = { id = 9297180 country = IND }'))
        altered = dict(self.source)
        altered['india_v3/32_navy.txt'] = altered['india_v3/32_navy.txt'].replace('relative value = -50', 'relative value = -25')
        with self.assertRaisesRegex(ValueError, 'authored'):
            transform(altered)


if __name__ == '__main__': unittest.main()
