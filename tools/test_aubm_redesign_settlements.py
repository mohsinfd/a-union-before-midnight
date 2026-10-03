import unittest
from build_aubm_cleanup import load_sources
from dh_save_spans import Node, parse, walk
from aubm_redesign_settlements import transform, actions, closed_gate, DIRECT


class SettlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load_sources()
        cls.output, cls.records = transform(cls.source)
        cls.before = {int(e.get('id')): e for t in cls.source.values() for e in parse(t).all('event')}
        cls.after = {int(e.get('id')): e for t in cls.output.values() for e in parse(t).all('event')}

    def test_every_family_member_covered(self):
        expected = {eid for eid, e in self.before.items() if e.get('country') == 'IND' and any(
            DIRECT.fullmatch(c.get('which', '')) for a in actions(e) for c in a.value.all('command') if c.get('type') == 'setflag')}
        self.assertEqual(expected, set(self.records))
        self.assertEqual(220, len(expected))

    def test_all_effectful_leaves_check_both_ledgers(self):
        for eid, records in self.records.items():
            target = records[0]['target'].lower()
            for a in actions(self.after[eid]):
                if a.value.all('command'):
                    trigger = a.value.get('trigger')
                    self.assertIsNotNone(trigger, eid)
                    guards = [n for n in trigger.all('NOT') if n.all('OR')]
                    self.assertTrue(guards, eid)
                    flags = [f for n in walk(guards[-1]) for f in n.all('flag')]
                    self.assertIn(f'ind_aubm_global_direct_{target}', flags)
                    self.assertIn(f'ind_aubm_regional_protected_{target}', flags)

    def test_direct_costs_preserved_and_closed(self):
        for eid in self.records:
            for old in actions(self.before[eid]):
                if not any(DIRECT.fullmatch(c.get('which', '')) for c in old.value.all('command')):
                    continue
                new = next(a for a in actions(self.after[eid]) if a.value.get('name') == old.value.get('name'))
                for kind in ('dissent', 'belligerence', 'peace', 'independence', 'make_puppet'):
                    self.assertEqual([(c.get('which'), c.get('value')) for c in old.value.all('command') if c.get('type') == kind],
                                     [(c.get('which'), c.get('value')) for c in new.value.all('command') if c.get('type') == kind], (eid, kind))
                self.assertTrue(any('_settled_' in c.get('which', '') for c in new.value.all('command')))

    def test_free_exit_and_no_event_additions(self):
        self.assertEqual(set(self.before), set(self.after))
        for eid in self.records:
            self.assertTrue(any(not a.value.all('command') for a in actions(self.after[eid])), eid)

    def test_repeat_transform_is_identical(self):
        output, records = transform(self.output)
        self.assertEqual(self.output, output)
        self.assertEqual(self.records, records)

    def test_small_gate(self):
        self.assertLess(len(closed_gate('sia')), 550)

    def test_failed_release_or_wrong_master_does_not_lock_recovery(self):
        from test_aubm_liberator import State, evaluate
        def pairs(node):
            return [(f.key, pairs(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields]
        gate = pairs(parse(closed_gate('sia')))
        for kind in ('sovereign', 'protected'):
            state = State(flags={f'ind_aubm_regional_{kind}_sia'}, exists={'IND'})
            self.assertTrue(evaluate(gate, state))
            state.exists.add('SIA')
            state.puppets['SIA'] = 'JAP'
            self.assertTrue(evaluate(gate, state))

    def test_real_outcome_closes_choice_in_either_family(self):
        from test_aubm_liberator import State, evaluate
        def pairs(node):
            return [(f.key, pairs(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields]
        gate = pairs(parse(closed_gate('sia')))
        for family in ('regional', 'global'):
            for kind in ('direct', 'sovereign', 'protected'):
                state = State(flags={f'ind_aubm_{family}_{kind}_sia'}, exists={'IND', 'SIA'})
                if kind == 'protected':
                    state.puppets['SIA'] = 'IND'
                self.assertFalse(evaluate(gate, state), (family, kind))


if __name__ == '__main__':
    unittest.main()
