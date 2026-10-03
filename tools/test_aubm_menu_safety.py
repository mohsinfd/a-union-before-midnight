"""Regression tests for non-destructive Cabinet dismissal."""
import unittest

from aubm_menu_safety import CANCEL, MENU_IDS, ROOT, ensure_menu_exits, validate_text


class MenuSafetyTests(unittest.TestCase):
    def test_original_options_are_byte_preserved(self):
        for filename, ids in MENU_IDS.items():
            text = (ROOT / 'mod/db/events/aubm_v4' / filename).read_bytes().decode('cp1252')
            addition = CANCEL.replace('\n', '\r\n') if '\r\n' in text else CANCEL
            before = text.replace(addition, '')
            after = ensure_menu_exits(before, ids)
            self.assertEqual(after.replace(addition, ''), before)
            self.assertEqual(ensure_menu_exits(after, ids), after)
            self.assertEqual(validate_text(after, ids), len(ids))

    def test_cancel_is_independent_of_peace_alignment_and_resources(self):
        # The complete cancel predicate is ai=no. Every human state is allowed;
        # no war, resource, charter, commitment or cooldown requirement exists.
        for state in ('peace-compact', 'war-compact', 'war-alliance', 'peace-cooldown', 'no-resources'):
            with self.subTest(state=state):
                self.assertIn('trigger = { ai = no }', CANCEL)
                self.assertNotIn('command =', CANCEL)
                self.assertNotIn('event which', CANCEL)

    def test_rejects_state_changing_or_gated_cancel(self):
        seed = 'event = {\n id = 1\n persistent = yes\n country = IND\n action_a = { name = "Join" }\n}\n'
        safe = ensure_menu_exits(seed, {1})
        for bad in (
            safe.replace('ai = no', 'ai = no atwar = no'),
            safe.replace('ai = no', 'ai = no supplies = 500'),
            safe.replace('name = "Cancel - close without changes"', 'name = "Cancel - close without changes" command = { type = event which = 1 when = 1 }'),
        ):
            with self.assertRaises(AssertionError): validate_text(bad, {1})

    def test_refuses_missing_ids_and_one_action_callbacks(self):
        with self.assertRaises(ValueError): ensure_menu_exits('', {1})
        with self.assertRaises(ValueError):
            ensure_menu_exits('event = { id = 1 one_action = yes\n action_a = { name = "Award" }\n}', {1})


if __name__ == '__main__': unittest.main()
