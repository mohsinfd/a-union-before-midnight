"""Staged source-state tests. No native delivery or save migration simulation."""
from pathlib import Path
import unittest

from dh_save_spans import parse
from aubm_redesign_diplomacy import actions, transform as diplomacy
from aubm_redesign_cooperation import transform as cooperation
from aubm_redesign_replies import transform as regional, pending
from aubm_redesign_great_power_replies import transform, FAMILIES, answer
from test_aubm_redesign_replies import State, evaluate, apply


class GreatPowerReplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'mod/db/events/aubm_v4/39_non_aligned_campaigns.txt'
        cls.raw = {str(path): path.read_text(encoding='cp1252')}
        cls.input = regional(cooperation(diplomacy(cls.raw)[0])[0])[0]
        cls.changed, cls.records = transform(cls.input)
        cls.events = {int(e.get('id')): e for t in cls.changed.values() for e in parse(t).all('event')}

    def action(self, eid, key='action_a'):
        return self.events[eid].get(key)

    def allowed(self, eid, state, key='action_a'):
        return evaluate(self.action(eid, key).get('trigger'), state)

    def choice(self, eid, state, label):
        return next(a.value for a in actions(self.events[eid])
                    if a.value.get('name') == label and evaluate(a.value.get('trigger'), state))

    def offer(self, name):
        return State(flags={pending(name), 'ind_v43_nam_doctrine_set', 'ind_v43_nam_outreach_started'})

    def selected(self, base, offset=1):
        _, name = FAMILIES[base]
        s = self.offer(name)
        s.flags.add(answer(name, base + offset))
        return s

    def test_dispatch_keeps_regional_tokens_and_adds_four_great_powers_once(self):
        s = State(flags={'ind_v43_nam_doctrine_set'})
        self.assertTrue(self.allowed(9281501, s))
        apply(self.action(9281501), s)
        for name in ('china', 'siam', 'persia', 'afghan', 'britain', 'america', 'soviet', 'japan'):
            self.assertIn(pending(name), s.flags)
        self.assertFalse(self.allowed(9281501, s))
        self.assertEqual(transform(self.changed)[0], self.changed)

    def test_dispatch_current_war_skips_only_affected_offer_and_closes_its_record(self):
        s = State(flags={'ind_v43_nam_doctrine_set'}, wars={frozenset(('IND', 'JAP'))})
        effects = apply(self.action(9281501), s)
        self.assertNotIn(pending('japan'), s.flags)
        self.assertIn('ind_v43_nam_japan_resolved', s.flags)
        self.assertNotIn(('event', '9281532'), effects)
        self.assertIn(('event', '9281520'), effects)

    def test_all_foreign_choices_dispatch_exact_selected_answer_and_disable_replays(self):
        for base, (_, name) in FAMILIES.items():
            for offset, key in enumerate(('action_a', 'action_b', 'action_c'), 1):
                s = self.offer(name)
                self.assertTrue(self.allowed(base, s, key))
                apply(self.action(base, key), s)
                self.assertIn(answer(name, base + offset), s.flags)
                self.assertFalse(self.allowed(base, s, key))
                # Re-delivery of the now-obsolete foreign event cannot cancel
                # the Indian answer that it has already selected.
                close = self.choice(base, s, 'Close an unrelated or completed reply')
                self.assertEqual(apply(close, s), [])
                self.assertIn(pending(name), s.flags)

    def test_all_twelve_indian_answers_resolve_once_without_joining_or_war(self):
        for base, (_, name) in FAMILIES.items():
            for offset in (1, 2, 3):
                eid = base + offset
                for key in ('action_a', 'action_b', 'action_c'):
                    if not self.action(eid, key):
                        continue
                    s = self.selected(base, offset)
                    self.assertTrue(self.allowed(eid, s, key), (eid, key))
                    effects = apply(self.action(eid, key), s)
                    self.assertNotIn(pending(name), s.flags)
                    self.assertNotIn(answer(name, eid), s.flags)
                    self.assertIn('ind_v43_nam_' + name + '_resolved', s.flags)
                    self.assertFalse(self.allowed(eid, s, key))
                    self.assertFalse(any(kind in ('alliance', 'war', 'peace', 'leave_alliance') for kind, _ in effects))

    def test_wrong_sibling_cannot_award_or_clear_selected_counteroffer(self):
        for base, (_, name) in FAMILIES.items():
            s = self.selected(base, 2)
            self.assertFalse(self.allowed(base + 1, s))
            close = self.choice(base + 1, s, 'Close an unrelated or completed reply')
            self.assertEqual(apply(close, s), [])
            self.assertIn(answer(name, base + 2), s.flags)
            self.assertIn(pending(name), s.flags)
            self.assertTrue(self.allowed(base + 2, s))

    def test_changed_war_master_country_or_indian_alignment_invalidates_selected_promise(self):
        for base, (tag, name) in FAMILIES.items():
            for change in ('war', 'master', 'absent', 'alliance', 'compact', 'doctrine'):
                s = self.selected(base)
                s.flags.add(pending('other'))
                if change == 'war':
                    s.wars.add(frozenset(('IND', tag)))
                elif change == 'master':
                    s.puppets.add(tag)
                elif change == 'absent':
                    s.countries.remove(tag)
                elif change == 'alliance':
                    s.alliances.add(frozenset(('IND', 'GER')))
                elif change == 'compact':
                    s.flags.add('ind_v4a_treaty_commonwealth')
                else:
                    s.flags.remove('ind_v43_nam_doctrine_set')
                self.assertFalse(self.allowed(base + 1, s), (base, change))
                before = dict(s.resources)
                effects = apply(self.choice(base + 1, s, 'Close this obsolete offer without agreement'), s)
                self.assertEqual(s.resources, before)
                self.assertTrue(all(kind in ('setflag', 'clrflag') for kind, _ in effects))
                self.assertIn(pending('other'), s.flags)
                self.assertNotIn(pending(name), s.flags)

    def test_explicit_withdrawal_releases_only_this_answer_without_reversing_earned_modifiers(self):
        s = self.selected(9281524, 2)
        s.flags.update({'ind_aubm_diplomatic_negotiation_pending', 'ind_aubm_negotiation_german',
                        pending('britain'), 'ind_v43_nam_base_autonomy'})
        effects = apply(self.choice(9281526, s, 'Withdraw this offer without agreement'), s)
        self.assertTrue(all(kind in ('setflag', 'clrflag') for kind, _ in effects))
        for keep in ('ind_aubm_diplomatic_negotiation_pending', 'ind_aubm_negotiation_german',
                     pending('britain'), 'ind_v43_nam_base_autonomy'):
            self.assertIn(keep, s.flags)
        self.assertNotIn(pending('america'), s.flags)

    def test_affordability_foreign_and_indian_amounts(self):
        for base, (_, name) in FAMILIES.items():
            s = self.offer(name)
            s.resources['supplies'] = 0
            self.assertFalse(self.allowed(base, s))
            self.assertTrue(self.allowed(base, s, 'action_b'))
        s = self.selected(9281520, 2)
        s.resources.update(money=299, supplies=700)
        self.assertFalse(self.allowed(9281522, s, 'action_b'))
        s.resources['money'] = 300
        self.assertTrue(self.allowed(9281522, s, 'action_b'))

    def test_named_third_country_promises_recheck_current_facts(self):
        s = self.selected(9281520, 3)
        s.countries.remove('USA')
        self.assertFalse(self.allowed(9281523, s, 'action_b'))
        s = self.selected(9281532, 2)
        s.flags.add('ind_v43_nam_china_partner')
        self.assertFalse(self.allowed(9281534, s, 'action_a'))
        self.assertTrue(self.allowed(9281534, s, 'action_b'))
        s.wars.add(frozenset(('IND', 'CHI')))
        self.assertFalse(self.allowed(9281534, s, 'action_c'))
        s = self.selected(9281532, 3)
        s.puppets.add('SIA')
        self.assertFalse(self.allowed(9281535, s, 'action_c'))

    def test_existing_command_amounts_are_preserved(self):
        originals = {int(e.get('id')): e for t in self.input.values() for e in parse(t).all('event')}
        def signature(c):
            return [(f.key, f.value) for f in c.fields if not isinstance(f.value, type(c))]
        for eid in range(9281520, 9281536):
            for af in actions(originals[eid]):
                original = [signature(c) for c in af.value.all('command')]
                updated = [signature(c) for c in self.action(eid, af.key).all('command')
                           if not (c.get('which', '').startswith('ind_stage_nam_') and c.get('type') in ('setflag', 'clrflag'))]
                self.assertEqual(original, updated, (eid, af.key))

    def test_valid_pending_callbacks_have_no_effect_free_cancel_and_no_calendar(self):
        for base, (_, name) in FAMILIES.items():
            for offset in range(4):
                eid = base + offset
                s = self.offer(name) if offset == 0 else self.selected(base, offset)
                available = [a.value for a in actions(self.events[eid]) if evaluate(a.value.get('trigger'), s)]
                self.assertTrue(available)
                self.assertTrue(all(a.all('command') for a in available), eid)
                self.assertIsNone(self.events[eid].get('date'))
                self.assertIsNone(self.events[eid].get('trigger'))

    def test_no_new_ids_partial_input_rejected_and_limits_reported(self):
        original_ids = {int(e.get('id')) for t in self.input.values() for e in parse(t).all('event')}
        self.assertEqual(original_ids, set(self.events))
        with self.assertRaises(ValueError):
            transform(self.raw)
        self.assertTrue(all(any(r['status'] == 'UNRESOLVED' for r in records) for records in self.records.values()))


if __name__ == '__main__':
    unittest.main()
