"""Source-state tests only; authored callback effects do not prove delivery."""
from pathlib import Path
import unittest

from dh_save_spans import parse
from aubm_redesign_cooperation import transform, DONE, PARTNERS, partner
from aubm_redesign_diplomacy import actions
from test_aubm_redesign_diplomacy import evaluate

ROOT = Path(__file__).resolve().parents[1]


class CooperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {str(p): p.read_text(encoding='cp1252') for p in
                     [ROOT / 'mod/db/events/aubm_v4' / n for n in
                      ('38_soviet_campaigns.txt', '39_non_aligned_campaigns.txt', '51_bespoke_route_arcs.txt')]}
        cls.changed, cls.records = transform(cls.files)
        cls.events = {int(e.get('id')): e for t in cls.changed.values() for e in parse(t).all('event')}

    def allowed(self, eid, key='action_a', **state):
        return evaluate(self.events[eid].get(key).get('trigger'), **state)

    def apply_flags(self, eid, key, flags):
        for c in self.events[eid].get(key).all('command'):
            if c.get('type') == 'setflag':
                flags[c.get('which')] = int(c.get('value', '1'))
            elif c.get('type') == 'clrflag':
                flags.pop(c.get('which'), None)

    def test_first_refusal_defer_reset_retry_acceptance_closes_request(self):
        flags = {'ind_v4_sov_autonomous_socialism': 1}
        wars = {frozenset(('IND', 'JAP'))}
        self.assertTrue(self.allowed(9281455, flags=flags, wars=wars))
        self.apply_flags(9281455, 'action_a', flags)
        self.assertFalse(self.allowed(9281455, flags=flags, wars=wars))
        self.apply_flags(9281459, 'action_c', flags)
        flags[DONE] = 1
        self.assertTrue(self.allowed(9281446, flags=flags))
        self.apply_flags(9281446, 'action_a', flags)
        self.assertNotIn(DONE, flags)
        self.assertTrue(self.allowed(9281455, flags=flags, wars=wars))
        self.apply_flags(9281455, 'action_a', flags)
        self.apply_flags(9281457, 'action_a', flags)
        self.assertFalse(self.allowed(9281455, flags=flags, wars=wars))
        self.assertEqual(flags['ind_v4_sov_east_equal_command'], 1)

    def test_repeated_refusal_can_reopen_and_stale_reset_cannot_clear_request(self):
        flags = {'ind_v4_sov_technical_only': 1}
        wars = {frozenset(('CHI', 'JAP'))}
        for attempt in range(2):
            self.assertTrue(self.allowed(9281455, flags=flags, wars=wars))
            self.apply_flags(9281455, 'action_a', flags)
            self.assertFalse(self.allowed(9281446, flags=flags))
            self.apply_flags(9281459, 'action_c', flags)
            self.apply_flags(9281446, 'action_a', flags)

    def test_changed_relations_and_historical_orientation(self):
        flags = {'ind_v4_sov_autonomous_socialism': 1, 'ind_v3_japanese_orientation': 1}
        wars = {frozenset(('CHI', 'JAP'))}
        self.assertTrue(self.allowed(9281455, flags=flags, wars=wars))
        self.assertFalse(self.allowed(9281455, flags=flags,
            wars=wars | {frozenset(('IND', 'SOV'))}))
        self.assertFalse(self.allowed(9281455, flags={**flags, 'ind_aubm_jp_partnership': 1}, wars=wars))
        self.assertFalse(self.allowed(9281455, flags=flags, wars=wars,
            alliances={frozenset(('IND', 'JAP'))}))

    def test_persistent_request_compiler_will_not_make_single_completion(self):
        self.assertEqual(self.events[9281455].get('persistent'), 'yes')
        from build_aubm_cleanup import collect_decisions
        row = next(r for r in collect_decisions(self.changed) if r['id'] == 9281455)
        self.assertFalse(row['single'])

    def test_country_specific_partners_work_without_route_flags(self):
        for tag, (name, enemy) in PARTNERS.items():
            flags = {'ind_v43_nam_' + name + '_partner': 1}
            wars = {frozenset((tag, enemy))}
            self.assertTrue(self.allowed(9289661, flags=flags, wars=wars), tag)
            self.assertFalse(self.allowed(9289661, flags={}, wars=wars), tag)
            self.assertFalse(self.allowed(9289661, flags={'ind_v3_delhi_pact': 1}, wars=wars), tag)
            self.assertFalse(self.allowed(9289661, flags=flags,
                wars=wars | {frozenset(('IND', tag))}), tag)

    def test_legacy_acceptance_and_actual_alliance_preserved(self):
        for tag, name in [('CHI', 'china'), ('SIA', 'siam')]:
            wars = {frozenset((tag, 'JAP'))}
            flags = {'ind_v42_delhi_pact_consultative': 1,
                     'ind_v42_' + name + '_accepts_delhi_pact': 1}
            self.assertTrue(self.allowed(9289661, flags=flags, wars=wars))
            self.assertTrue(self.allowed(9289661, wars=wars,
                alliances={frozenset(('IND', tag))}))

    def test_support_relations_match_each_current_accepted_belligerent(self):
        commands = [c for c in self.events[9289661].get('action_c').all('command') if c.get('type') == 'relation']
        for tag, (name, enemy) in PARTNERS.items():
            flags = {'ind_v43_nam_' + name + '_partner': 1,
                     'ind_aubm_bespoke_partner_crisis_sovereign_limited_support': 1}
            wars = {frozenset((tag, enemy))}
            for c in commands:
                self.assertEqual(evaluate(c.get('trigger'), flags=flags, wars=wars), c.get('which') == tag)

    def test_current_commitment_closes_opportunity_autonomous_politics_does_not(self):
        flags = {'ind_v43_nam_persia_partner': 1, 'ind_aubm_socialist_autonomous': 1}
        wars = {frozenset(('PER', 'SOV'))}
        self.assertTrue(self.allowed(9289661, flags=flags, wars=wars))
        self.assertFalse(self.allowed(9289661, flags={**flags, 'ind_v4a_treaty_commonwealth': 1}, wars=wars))
        self.assertFalse(self.allowed(9289661, flags=flags, wars=wars,
            alliances={frozenset(('IND', 'USA'))}))

    def test_unresolved_callbacks_are_unchanged_and_cancel_has_no_effects(self):
        original = {int(e.get('id')): t[e.start:e.end] for t in self.files.values() for e in parse(t).all('event')}
        updated = {int(e.get('id')): t[e.start:e.end] for t in self.changed.values() for e in parse(t).all('event')}
        for eid in (9281456, 9281457, 9281458, 9281459, 9281511):
            self.assertEqual(original[eid], updated[eid])
            self.assertEqual(self.records[eid][0]['status'], 'UNRESOLVED')
        self.assertTrue(any(not a.value.all('command') for a in actions(self.events[9281455])))
        self.assertEqual(transform(self.changed)[0], self.changed)

    def test_calendar_crisis_does_not_gain_a_daily_no_effect_cancel_loop(self):
        self.assertFalse(any(not a.value.all('command') for a in actions(self.events[9289661])))


if __name__ == '__main__':
    unittest.main()
