import unittest
from dh_save_spans import Node, parse, walk
from build_aubm_redesign import load, ROOT, index
from aubm_redesign_cooperation import transform as cooperation
from aubm_redesign_crises import ROWS, transform
from aubm_redesign_diplomacy import actions
from test_aubm_redesign_diplomacy import evaluate


class CrisisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, _ = cooperation(load(ROOT / 'mod'))
        cls.output, cls.records = transform(cls.source)
        cls.before, cls.after = index(cls.source), index(cls.output)

    def test_exact_family_no_ids_added(self):
        self.assertEqual(set(ROWS) | {r[3] for r in ROWS.values()}, set(self.records))
        self.assertEqual(set(self.before), set(self.after))
        self.assertEqual(transform(self.output)[0], self.output)

    def test_crises_are_optional_decisions_with_free_exit(self):
        for eid in ROWS:
            ev = self.after[eid][2]
            self.assertIsInstance(ev.get('decision'), Node)
            self.assertTrue(any(not af.value.all('command') for af in actions(ev)))

    def test_reviews_no_longer_write_commitments_or_resolution(self):
        for eid in ROWS:
            for af in actions(self.after[eid][2]):
                commands = af.value.all('command')
                if any(c.get('type') == 'event' for c in commands):
                    self.assertEqual({'event'}, {c.get('type') for c in commands}, eid)

    def test_costs_and_material_support_unchanged(self):
        def canonical(node):
            return [(f.key, canonical(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields]
        for eid in ROWS:
            self.assertEqual([canonical(c) for c in self.before[eid][2].get('action_c').all('command')],
                             [canonical(c) for c in self.after[eid][2].get('action_c').all('command')], eid)

    def test_route_flags_not_required_by_crisis_or_review(self):
        for eid in self.records:
            for n in walk(self.after[eid][2]):
                for flag in n.all('flag'):
                    if isinstance(flag, str):
                        self.assertFalse(flag.startswith('ind_aubm_route_'), (eid, flag))
                        self.assertNotEqual('ind_aubm_bespoke_route_contract_alpha23', flag)

    def test_berlin_current_compact_works_without_route_and_hostility_blocks(self):
        ev = self.after[9289541][2]
        flags = {'ind_aubm_commitment_german': 1}
        wars = {frozenset(('GER', 'SOV'))}
        self.assertTrue(evaluate(ev.get('decision'), flags=flags, wars=wars))
        self.assertFalse(evaluate(ev.get('decision'), flags=flags,
                                 wars=wars | {frozenset(('IND', 'GER'))}))
        self.assertFalse(evaluate(ev.get('decision'), flags=flags,
                                 alliances={frozenset(('IND', 'JAP'))}, wars=wars))
        self.assertFalse(evaluate(ev.get('decision'), flags={**flags, 'ind_aubm_commitment_japan': 1}, wars=wars))

    def test_closing_reviews_does_not_schedule_another_menu(self):
        for row in ROWS.values():
            ev = self.after[row[3]][2]
            close = [a.value for a in actions(ev) if a.value.get('name') == 'Close this review']
            self.assertTrue(close)
            self.assertTrue(all(not a.all('command') for a in close))

    def test_modern_partner_crisis_reaches_matching_enemy_review(self):
        from aubm_redesign_cooperation import PARTNERS
        menu = self.after[9289685][2]
        for tag, (name, enemy) in PARTNERS.items():
            flags = {f'ind_v43_nam_{name}_partner': 1}
            wars = {frozenset((tag, enemy))}
            self.assertTrue(evaluate(self.after[9289661][2].get('decision'), flags=flags, wars=wars))
            for key, target in [('action_a', 'JAP'), ('action_b', 'SOV')]:
                self.assertEqual(enemy == target, evaluate(menu.get(key).get('trigger'), flags=flags, wars=wars), tag)

    def test_no_new_empty_boolean_operators(self):
        for eid in self.records:
            for node in walk(self.after[eid][2]):
                for f in node.fields:
                    if f.key in ('AND', 'OR', 'NOT'):
                        self.assertTrue(f.value.fields, eid)


if __name__ == '__main__':
    unittest.main()
