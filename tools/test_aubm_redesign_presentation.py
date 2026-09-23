import unittest
from pathlib import Path
from dh_save_spans import parse, Node
from aubm_redesign_presentation import CATALOG, TITLES, transform, audit
from build_aubm_redesign import load, index, ROOT


def mechanics(node):
    return [(f.key, mechanics(f.value) if isinstance(f.value, Node) else f.value)
            for f in node.fields if f.key not in ('name', 'desc', 'decision_desc')]


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load(ROOT / 'mod')
        cls.output, cls.records = transform(cls.source)

    def test_all_explicit_rewrites_preserve_mechanics(self):
        old, new = index(self.source), index(self.output)
        self.assertTrue((set(CATALOG) | set(TITLES)) <= set(self.records))
        for eid in self.records:
            self.assertEqual(mechanics(old[eid][2]), mechanics(new[eid][2]))
            if eid in CATALOG:
                self.assertLessEqual(len(new[eid][2].get('desc')), 340)
            if eid in TITLES:
                self.assertLessEqual(len(new[eid][2].get('name')), 50)

    def test_idempotent_and_input_untouched(self):
        self.assertEqual(self.source, load(ROOT / 'mod'))
        self.assertEqual(self.output, transform(self.output)[0])

    def test_no_blind_truncation_or_overwrite(self):
        files = {'test': 'event = { id = 9270000 desc = "New upstream meaning" }'}
        out, records = transform(files)
        self.assertEqual(files, out)
        self.assertEqual('pending', records[9270000][0]['status'])

    def test_only_generated_tooltip_override_is_removed(self):
        data = {'test': '''event = { id = 1 desc = "Story" decision_desc = "Cabinet funding estimates: One [money 10]." action = { name = "Buy" command = { type = money value = -10 } } }
event = { id = 2 desc = "Story" decision_desc = "Warning: joins all Allied wars." }
event = { id = 3 desc = "Story" decision_desc = "Funding estimates: manual" # AUBM_DECISION_DESC_MANUAL
}'''}
        out, records = transform(data)
        old, new = parse(data['test']).all('event'), parse(out['test']).all('event')
        self.assertIsNone(new[0].get('decision_desc'))
        self.assertEqual(old[0].get('desc'), new[0].get('desc'))
        self.assertEqual(mechanics(old[0]), mechanics(new[0]))
        for i in (1, 2):
            self.assertEqual(old[i].get('decision_desc'), new[i].get('decision_desc'))
        self.assertEqual({1}, set(records))

    def test_audit_detects_colour_codes_and_overflow(self):
        desc = 'wide ' * 110
        files = {'test': 'event = { id = 1 name = "Title" desc = "' + desc +
                 '\xa7Ywarning" action = { name = "Go" } }'}
        result = audit(files)
        self.assertEqual(2, len(result['hard_errors']))
        self.assertEqual(1, result['events_with_layout_risks'])
        self.assertFalse(result['colour_issue_resolved'])
        self.assertFalse(result['native_layout_verified'])

    def test_all_authored_ids_in_audit_not_just_changed(self):
        result = audit(self.output)
        self.assertEqual(5553, result['events_checked'])
        self.assertEqual([], result['hard_errors'])
        self.assertGreater(result['events_with_layout_risks'], 0)


if __name__ == '__main__':
    unittest.main()
