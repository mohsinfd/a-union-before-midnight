"""Regression checks for clocks which survive loss of persistent save_date data."""
import copy
from pathlib import Path
import unittest
from dh_save_spans import Node, parse, walk
import aubm_redesign_navy as navy
import aubm_naval_clock_fix as fix
from test_aubm_redesign_navy import state, evaluate


class ClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events'
        source = {str(p.relative_to(root)): p.read_text(encoding='latin1')
                  for p in [root/'india_v3/32_navy.txt', root/'aubm_v4/40_special_units_and_capital_ships.txt']}
        cls.staged, _ = navy.transform(source)
        cls.fixed, _ = fix.transform(cls.staged)
        cls.idx = {int(e.get('id')): e for t in cls.fixed.values() for e in parse(t).all('event')}

    def test_callbacks_are_unique_and_idempotent(self):
        second, _ = fix.transform(self.fixed)
        self.assertEqual(second, self.fixed)
        self.assertTrue(fix.NEW_EVENT_IDS <= self.idx.keys())

    def test_legacy_paid_orders_recover_without_a_date(self):
        for target, info in navy.TIMING.items():
            s = state(target)
            s['flags'].add(navy.paid_flag(info['previous']))
            self.assertEqual({}, s['elapsed'])
            self.assertTrue(evaluate(self.idx[target].get('decision_trigger'), s), target)

    def test_new_order_waits_even_after_calendar_floor(self):
        for target, info in navy.TIMING.items():
            s = state(target)
            s['flags'].update([navy.paid_flag(info['previous']), fix.armed(target)])
            self.assertFalse(evaluate(self.idx[target].get('decision_trigger'), s), target)
            # Simulated save/reload retains flags, drops every event timestamp.
            loaded = copy.deepcopy(s); loaded['elapsed'] = {}
            loaded['flags'].add(fix.ready(target))
            self.assertTrue(evaluate(self.idx[target].get('decision_trigger'), loaded), target)

    def test_no_target_depends_on_source_timestamp(self):
        for target, info in navy.TIMING.items():
            for n in walk(self.idx[target]):
                event = n.get('event')
                self.assertFalse(isinstance(event, Node) and event.get('id') == str(info['previous']), target)

    def test_callbacks_obey_engine_queue_format(self):
        for cid in fix.NEW_EVENT_IDS:
            e = self.idx[cid]
            for key in ['trigger', 'date', 'offset', 'deathdate', 'decision', 'save_date']:
                self.assertIsNone(e.get(key), (cid, key))
            self.assertNotEqual(e.get('persistent'), 'yes')
            self.assertTrue(all(c.get('type') == 'setflag' for a in navy.actions(e) for c in a.value.all('command')))

    def test_only_paid_actions_arm_exactly_one_branch_callback(self):
        for target, info in navy.TIMING.items():
            for af in navy.actions(self.idx[info['previous']]):
                cmds = af.value.all('command')
                timers = [c for c in cmds if c.get('type') == 'event' and c.get('which') == str(fix.CALLBACKS[target])]
                paid = any(c.get('type') == 'setflag' and c.get('which') == navy.paid_flag(info['previous']) for c in cmds)
                self.assertEqual(bool(timers), paid)
                if not paid: continue
                expected = list(info['days']) if isinstance(info['days'], tuple) else [info['days']]
                self.assertEqual([int(c.get('when')) for c in timers], expected)
                self.assertTrue(all(c.get('trigger').get('NOT').get('flag') == fix.armed(target) for c in timers))
                arm = next(c for c in cmds if c.get('which') == fix.armed(target))
                self.assertGreater(arm.start, timers[-1].start)

    def test_resource_and_done_guards_survive(self):
        for target, info in navy.TIMING.items():
            s = state(target); s['flags'].update([navy.paid_flag(info['previous']),fix.armed(target),fix.ready(target)])
            s['money'] = 0; s['supplies'] = 0
            self.assertFalse(evaluate(self.idx[target].get('decision_trigger'), s))
            s = state(target); s['flags'].update([navy.paid_flag(info['previous']),fix.armed(target),fix.ready(target)])
            from test_aubm_redesign_navy import DONE
            s['flags'].add(DONE[target])
            self.assertFalse(evaluate(self.idx[target].get('decision_trigger'), s))


if __name__ == '__main__': unittest.main()
