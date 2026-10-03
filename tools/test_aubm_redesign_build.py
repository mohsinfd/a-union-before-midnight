"""Integration evidence only. These tests do not execute Darkest Hour."""
from pathlib import Path
import unittest

from dh_save_spans import Node
from build_aubm_redesign import ROOT, compile_files, coverage_report, index, load, safe_output, registered_new_ids


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load(ROOT / 'mod')
        cls.snapshot = dict(cls.sources)
        cls.output, cls.records = compile_files(cls.sources)
        cls.before, cls.after = index(cls.sources), index(cls.output)

    def test_no_source_mutation_and_only_explicit_story_additions(self):
        NEW_EVENT_IDS = registered_new_ids()
        self.assertEqual(self.snapshot, self.sources)
        self.assertEqual(set(), set(self.before) - set(self.after))
        self.assertEqual(set(NEW_EVENT_IDS), set(self.after) - set(self.before))
        self.assertEqual(5553 + len(NEW_EVENT_IDS), len(self.after))

    def test_full_coverage_does_not_claim_full_review(self):
        report = coverage_report(self.output, self.records, [])
        self.assertEqual(len(self.after), report['coverage']['event_occurrences'])
        self.assertEqual(len(self.after), report['coverage']['dispositions']['pending'])
        self.assertEqual(0, report['coverage']['engine_tested'])
        self.assertEqual(0, report['coverage']['full_lifecycle_review_complete'])
        self.assertFalse(report['duplicate_ids'])
        self.assertFalse(report['callback_missing'])

    def test_prose_precedes_behavior_and_both_are_recorded(self):
        siam = self.after[9282212][2]
        self.assertEqual('Bangkok After the Fighting', siam.get('name'))
        self.assertTrue(siam.get('action_d').get('trigger'))
        dimensions = {r['dimension'] for r in self.records[9282212]}
        self.assertTrue({'prose', 'settlement_closure'} <= dimensions)

    def test_navigation_does_not_declare_war(self):
        event = self.after[9281140][2]
        self.assertFalse(any(c.get('type') == 'war' for c in event.get('action_a').all('command')))

    def test_candidate_and_all_three_armistice_passes_are_composed(self):
        from aubm_redesign_version import TITLE
        self.assertEqual(TITLE, self.after[9270000][2].get('name'))
        dimensions = {r['dimension'] for records in self.records.values() for r in records}
        self.assertTrue({'armistice_ownership', 'regional_replies', 'bespoke_replies'} <= dimensions)
        for eid in (9282260, 9282291):
            commands = [c for f in self.after[eid][2].fields
                        if f.key == 'action' or (f.key or '').startswith('action_')
                        for c in f.value.all('command') if c.get('type') == 'peace']
            self.assertTrue(commands, eid)
            self.assertTrue(all(c.get('value') == '0' for c in commands), eid)

    def test_final_presentation_respects_revised_purpose(self):
        from aubm_redesign_navigation import RETIRED_IDS
        for eid in RETIRED_IDS:
            self.assertEqual('This Review Is Closed', self.after[eid][2].get('name'))
        self.assertEqual('The Western Corridor Holds', self.after[9289936][2].get('name'))

    def test_changed_presentation_limits_and_action_keys(self):
        for eid, (_, _, event) in self.after.items():
            old = self.before[eid][2] if eid in self.before else Node()
            for key in ('name', 'desc', 'decision_desc'):
                if event.get(key) != old.get(key):
                    if event.get(key) is None:
                        self.assertEqual('decision_desc', key)
                        self.assertTrue(old.get(key).startswith(('Cabinet funding estimates:', 'Funding estimates:')))
                        continue
                    self.assertLessEqual(len(event.get(key).encode('latin1')), 58 if key == 'name' else 500, (eid, key))
            for af in event.fields:
                if (af.key or '').startswith('action_'):
                    self.assertIn(af.key, ('action_a', 'action_b', 'action_c', 'action_d'), eid)

    def test_added_action_gates_are_bounded(self):
        def canonical(node):
            return [(f.key, canonical(f.value) if isinstance(f.value, Node) else f.value)
                    for f in node.fields] if isinstance(node, Node) else node
        for eid, (_, block, event) in self.after.items():
            if eid in self.before and self.before[eid][1] == block:
                continue
            for af in event.fields:
                if af.key == 'action' or (af.key or '').startswith('action_'):
                    trigger = af.value.get('trigger')
                    if isinstance(trigger, Node):
                        old_action = self.before[eid][2].get(af.key) if eid in self.before else None
                        old_trigger = old_action.get('trigger') if isinstance(old_action, Node) else None
                        if canonical(trigger) != canonical(old_trigger):
                            # Route removal may shrink a pre-existing oversized
                            # gate. Do not confuse a smaller inherited condition
                            # with introducing a new oversized tooltip.
                            prior_size = old_trigger.end - old_trigger.start if isinstance(old_trigger, Node) else 0
                            self.assertLessEqual(trigger.end - trigger.start, max(9999, prior_size), eid)

    def test_records_never_claim_native_engine_execution(self):
        self.assertTrue(self.records)
        for eid, records in self.records.items():
            for record in records:
                self.assertFalse(record['engine_tested'], eid)
                self.assertFalse(record['full_lifecycle_review_complete'], eid)

    def test_output_cannot_target_source_install_or_save(self):
        self.assertEqual(ROOT / 'build/redesign', safe_output(ROOT / 'build/redesign'))
        for path in (ROOT, ROOT / 'mod', ROOT / 'build/cleanup1', ROOT / 'build/redesign/../cleanup1',
                     Path('C:/Program Files (x86)/Steam')):
            with self.assertRaises(ValueError):
                safe_output(path)


if __name__ == '__main__':
    unittest.main()
