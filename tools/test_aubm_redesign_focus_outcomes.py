import unittest
from pathlib import Path
from dh_save_spans import Node, parse
from aubm_redesign_campaign_access import canonical
import aubm_redesign_focus_outcomes as subject
from test_aubm_redesign_route_finish import state, evaluate as basic, index
from aubm_redesign_navigation import transform as navigation
from aubm_redesign_route_finish import transform as finish


def evaluate(node, s):
    def one(key, value):
        if key in ('AND', 'OR', 'NOT'):
            results = [one(f.key, f.value) for f in value.fields]
            return all(results) if key == 'AND' else any(results) if key == 'OR' else not any(results)
        if key == 'garrison':
            return s.get('garrison', {}).get(int(value.get('province')), 0) >= int(value.get('size'))
        return basic(parse(serialize(key, value)), s)
    return all(one(f.key, f.value) for f in node.fields)


def serialize(key, value):
    if isinstance(value, Node):
        return key + ' = { ' + ' '.join(serialize(f.key, f.value) for f in value.fields) + ' }'
    return key + ' = ' + value


class FocusOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events/aubm_v4'
        source = {p.name: p.read_bytes().decode('latin1') for p in root.glob('*.txt')}
        cls.before, _ = finish(navigation(source)[0])
        cls.output, cls.records = subject.transform(cls.before)
        cls.events = index(cls.output)

    def test_no_ids_added_and_idempotent(self):
        self.assertEqual(index(self.before).keys(), self.events.keys())
        self.assertEqual(subject.transform(self.output)[0], self.output)
        self.assertEqual(len(self.records), 10)

    def test_coalition_presence_not_free_ally_capture(self):
        s = state(); s['wars'] = {frozenset(('IND', 'GER'))}
        s['control'] = {163: 'ENG', 195: 'ENG'}
        s['alliances'] = {frozenset(('IND', 'ENG'))}
        self.assertFalse(evaluate(parse(subject.EXPEDITION), s))
        s['garrison'] = {163: 6, 195: 6}
        self.assertTrue(evaluate(parse(subject.EXPEDITION), s))
        for province in (163, 195):
            s['garrison'][province] = 5
            self.assertFalse(evaluate(parse(subject.EXPEDITION), s))
            s['garrison'][province] = 6
        s['alliances'].clear()
        self.assertFalse(evaluate(parse(subject.EXPEDITION), s))
        s['control'] = {163: 'IND', 195: 'IND'}
        self.assertTrue(evaluate(parse(subject.EXPEDITION), s))
        s['wars'].clear()
        self.assertFalse(evaluate(parse(subject.EXPEDITION), s))

    def test_twelve_choice_rewards_and_no_diplomatic_effects(self):
        for eid in (9289518, 9289557, 9289597, 9289678):
            before = index(self.before)[eid]
            after = self.events[eid]
            old = subject.actions(before)[0].value.all('command')
            new = subject.actions(after)[0].value.all('command')
            self.assertEqual([canonical(c) for c in old], [canonical(c) for c in new[:len(old)]])
            self.assertEqual(len(new) - len(old), 3)
            for c in new[len(old):]:
                self.assertIsNotNone(c.get('trigger'))
                self.assertIn(c.get('type'), ('supplies', 'oilpool', 'research_mod', 'tc_mod', 'dissent'))
            self.assertIn('ind_aubm_route_war_achievement', serialize('trigger', after.get('trigger')))

    def test_choice_gates_exclusive_and_axis_targets_distinct(self):
        r = next(r for r in subject.ROUTES if r.key == 'german')
        f = r.focuses[0]
        goals = ['AND = { ' + subject.control(713) + ' ' + subject.control(706) + ' }',
                 'AND = { ' + subject.control(1103) + ' ' + subject.control(1138) + ' }',
                 f.culmination_condition]
        gate = parse(subject.guarded_choices(f, goals))
        s = state(); s['flags'] = {f.choices[0].flag}; s['control'] = {713: 'IND', 706: 'IND'}
        self.assertTrue(evaluate(gate, s))
        s['flags'] = {f.choices[1].flag}
        self.assertFalse(evaluate(gate, s))
        s['control'] = {1103: 'IND', 1138: 'IND'}
        self.assertTrue(evaluate(gate, s))
        s['flags'].add(f.choices[0].flag)
        self.assertFalse(evaluate(gate, s))

    def test_choice_text_budget(self):
        for eid in self.records:
            self.assertLessEqual(len(self.events[eid].get('desc').encode('latin1')), 500)


if __name__ == '__main__':
    unittest.main()
