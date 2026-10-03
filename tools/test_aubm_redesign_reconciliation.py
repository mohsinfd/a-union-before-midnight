import unittest
from aubm_redesign_reconciliation import COMPONENTS, reconcile, fresh_dispositions


class ReconciliationTests(unittest.TestCase):
    def files(self, ids):
        return {'events.txt': '\n'.join(f'event = {{ id = {eid} country = IND name = "test" action_a = {{ name = "Close" }} }}' for eid in ids)}

    def test_all_forty_have_explicit_component_dispositions(self):
        self.assertEqual(40, len(COMPONENTS))
        report = reconcile(self.files([1]), self.files([1, *COMPONENTS]))
        self.assertEqual(40, report['installed_only_count'])
        self.assertFalse(report['unexpected_installed_only_ids'])
        self.assertFalse(report['expected_ids_missing_from_installed_only'])
        self.assertTrue(all(not row['implemented_in_staged_authored'] for row in report['components']))
        self.assertFalse(report['release_ready'])

    def test_unknown_id_and_changed_menu_effects_are_not_approved(self):
        active = self.files([9297100, 999999])
        active['events.txt'] = active['events.txt'].replace('name = "Close"', 'name = "Close" command = { type = money value = 100 }')
        report = reconcile({}, active)
        self.assertEqual([999999], report['unexpected_installed_only_ids'])
        self.assertTrue(all(row['requires_reassessment'] for row in report['components']))

    def test_preserves_inputs_and_transaction_dependencies(self):
        files = self.files(COMPONENTS)
        original = dict(files)
        report = reconcile({}, files)
        self.assertEqual(original, files)
        rows = {r['id']: r for r in report['components']}
        self.assertIn(9289905, rows[9297200]['dependencies'])
        self.assertIn(9294015, rows[9297201]['dependencies'])
        self.assertIn(9297005, rows[9297202]['dependencies'])
        self.assertFalse(report['auto_merge_performed'])

    def test_unknown_or_mutated_navigation_is_not_silently_excluded(self):
        active = self.files([9297100, 999999])
        active['events.txt'] = active['events.txt'].replace('name = "Close"', 'name = "Close" command = { type = money value = 100 }')
        report = fresh_dispositions(reconcile({}, active), {}, {})
        self.assertEqual([999999, 9297100], report['fresh_campaign_unresolved_ids'])

    def test_ported_callbacks_and_unused_notice_are_distinct(self):
        active = self.files([9297180, 9297190])
        staged = self.files([9297180])
        report = fresh_dispositions(reconcile({}, active), staged, {})
        rows = {row['id']: row for row in report['components']}
        self.assertEqual('ported_with_reviewed_family', rows[9297180]['fresh_campaign_disposition'])
        self.assertEqual('exclude_obsolete_notice_and_unused_done_mirrors', rows[9297190]['fresh_campaign_disposition'])
        self.assertFalse(report['fresh_campaign_unresolved_ids'])

    def test_consumed_legacy_notice_flags_fail_closed(self):
        staged = {'events.txt': 'event = { id = 1 trigger = { flag = ind_cleanup1_loaded } }'}
        with self.assertRaises(ValueError):
            fresh_dispositions(reconcile({}, self.files([9297190])), staged, {})


if __name__ == '__main__':
    unittest.main()
