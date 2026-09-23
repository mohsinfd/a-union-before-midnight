"""Cold script-state tests only; no native game execution or save changes."""
from pathlib import Path
import unittest
from dh_save_spans import Node, parse
from aubm_redesign_diplomacy import transform as diplomacy, actions
from aubm_redesign_relationships import transform, FAMILIES, token, oldflag, JP_OFFER, JP_ANSWERS, JP_REQUEST
from test_aubm_redesign_replies import State


def evaluate(node, state):
    if not isinstance(node, Node):
        return True
    def child(f):
        k, v = f.key, f.value
        if k == 'AND': return evaluate(v, state)
        if k == 'OR': return any(child(x) for x in v.fields)
        if k == 'NOT': return not any(child(x) for x in v.fields)
        if k == 'flag': return v.get('which') in state.flags if isinstance(v, Node) else v in state.flags
        if k == 'exists': return v in state.countries
        if k == 'ispuppet': return v in state.puppets
        if k in ('war', 'alliance'): return frozenset(v.all('country')) in (state.wars if k == 'war' else state.alliances)
        if k == 'participant': return any(v.get('country') in pair for pair in state.alliances)
        if k == 'control': return state.controls.get(int(v.get('province'))) == v.get('data')
        if k in ('money', 'supplies', 'oil'): return state.resources[k] >= float(v)
        if k in ('ic', 'land_percentage', 'naval_percentage', 'air'): return True
        if k == 'ai': return v == 'no'
        raise AssertionError(k)
    return all(child(f) for f in node.fields)


def apply(a, state):
    effects = []
    for c in a.all('command'):
        if not evaluate(c.get('trigger'), state): continue
        k, w = c.get('type'), c.get('which')
        if k == 'setflag': state.flags.add(w)
        if k == 'clrflag': state.flags.discard(w)
        if k in ('money', 'supplies'): state.resources[k] += float(c.get('value'))
        effects.append((k, w, c.get('value')))
    return effects


class RelationshipsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events/aubm_v4'
        cls.source = {str(root / p): (root / p).read_text(encoding='cp1252') for p in ('35_japan_partnership.txt', '37_german_campaigns.txt')}
        cls.input = diplomacy(cls.source)[0]
        cls.output, cls.records = transform(cls.input)
        cls.events = {int(e.get('id')): e for text in cls.output.values() for e in parse(text).all('event')}

    def a(self, eid, key='action_a'): return self.events[eid].get(key)
    def allowed(self, eid, s, key='action_a'): return evaluate(self.a(eid, key).get('trigger'), s)
    def close(self, eid, s, withdraw=False):
        label = 'Withdraw this offer without agreement' if withdraw else 'Close this obsolete offer without agreement'
        return next(a.value for a in actions(self.events[eid]) if a.value.get('name') == label and evaluate(a.value.get('trigger'), s))
    def state(self, tag='PER'):
        s = State(flags={'ind_gc_campaign_active'}, wars={frozenset(('IND', 'SOV'))})
        s.countries.update(('SIK', 'UPE', 'CHC', 'CXB'))
        s.controls = {1279: tag, 1281: tag}
        return s
    def jp(self):
        s = self.state()
        s.flags = {'ind_aubm_jp_partnership', 'ind_aubm_jp_influence'}
        return s

    def test_pure_idempotent_and_exact_coverage(self):
        self.assertEqual(transform(self.output)[0], self.output)
        expected = {9281135, 9281136, 9281137}
        for request, replies, base, reset in FAMILIES.values(): expected.update((request, *replies.values(), *range(base, base + 3), reset))
        self.assertEqual(set(self.records), expected)
        for eid in expected - {9281135, 9281314, 9281315, 9281316}:
            self.assertEqual(self.events[eid].get('persistent'), 'yes')
            self.assertFalse(self.events[eid].get('date'))
        for eid in (9281135, 9281314, 9281315, 9281316):
            self.assertIsNone(self.events[eid].get('decision').get('trigger'))

    def test_all_seven_hosts_three_outcomes_and_refusal_retry(self):
        for family, (request, responders, base, reset) in FAMILIES.items():
            for tag, reply in responders.items():
                for index, key in enumerate(('action_a', 'action_b', 'action_c')):
                    s = self.state(tag)
                    before = dict(s.resources)
                    self.assertTrue(self.allowed(request, s), (request, tag))
                    apply(self.a(request), s)
                    self.assertLess(s.resources['money'], before['money'])
                    self.assertTrue(self.allowed(reply, s, key))
                    apply(self.a(reply, key), s)
                    self.assertFalse(self.allowed(reply, s, key))
                    self.assertTrue(self.allowed(base + index, s))
                    apply(self.a(base + index), s)
                    self.assertFalse(self.allowed(base + index, s))
                    self.assertFalse(self.allowed(request, s))
                    if index:
                        self.assertTrue(self.allowed(reset, s))
                        apply(self.a(reset), s)
                        self.assertTrue(self.allowed(request, s))
                        apply(self.a(request), s)
                        self.assertTrue(self.allowed(reply, s, key))

    def test_changed_war_host_master_soviet_alignment_and_control_lapse(self):
        for family, (request, responders, base, _) in FAMILIES.items():
            for tag, reply in responders.items():
                for change in ('peace', 'hostwar', 'master', 'sovietalliance', 'disappeared', 'campaignended'):
                    s = self.state(tag)
                    apply(self.a(request), s)
                    apply(self.a(reply), s)
                    s.flags.add('unrelated_pending')
                    if change == 'peace': s.wars.clear()
                    if change == 'hostwar': s.wars.add(frozenset(('IND', tag)))
                    if change == 'master': s.puppets.add(tag)
                    if change == 'sovietalliance': s.alliances.add(frozenset((tag, 'SOV')))
                    if change == 'disappeared': s.countries.remove(tag)
                    if change == 'campaignended': s.flags.discard('ind_gc_campaign_active')
                    self.assertFalse(self.allowed(base, s), (tag, change))
                    apply(self.close(base, s), s)
                    self.assertNotIn(oldflag(family, 'requested'), s.flags)
                    self.assertIn('unrelated_pending', s.flags)
        s = self.state('SIK')
        apply(self.a(9281316), s); apply(self.a(9281322), s)
        s.controls[1281] = 'CHI'
        self.assertFalse(self.allowed(9281336, s))

    def test_withdrawal_does_not_clear_other_offer_and_late_wrong_answers_are_inert(self):
        s = self.state()
        apply(self.a(9281314), s); apply(self.a(9281315), s)
        apply(self.a(9281320, 'action_c'), s)
        self.assertFalse(self.allowed(9281330, s))
        # Already consumed foreign request cannot clear its selected answer.
        unrelated = next(a.value for a in actions(self.events[9281320]) if a.value.get('name') == 'Close an unrelated or completed reply' and evaluate(a.value.get('trigger'), s))
        self.assertFalse(apply(unrelated, s))
        self.assertTrue(self.allowed(9281332, s))
        apply(self.close(9281332, s, True), s)
        self.assertFalse(self.allowed(9281332, s))
        self.assertIn(token('afghan', 'offer_AFG'), s.flags)
        self.assertTrue(self.allowed(9281314, s))

    def test_reset_cannot_clear_new_pending_and_limited_bonus_does_not_stack(self):
        for family, (request, responders, base, reset) in FAMILIES.items():
            tag, reply = next(iter(responders.items()))
            s = self.state(tag)
            for round in range(2):
                apply(self.a(request), s); apply(self.a(reply, 'action_b'), s)
                effects = apply(self.a(base + 1), s)
                bonus = [e for e in effects if e[0] in ('tc_mod', 'intelligence')]
                self.assertEqual(len(bonus), 1 if round == 0 else 0)
                apply(self.a(reset), s)
            apply(self.a(request), s)
            self.assertFalse(self.allowed(reset, s))
            self.assertIn(oldflag(family, 'requested'), s.flags)

    def test_japan_deferred_retry_and_notice_exact_once(self):
        s = self.jp()
        self.assertTrue(self.allowed(9281135, s))
        apply(self.a(9281135), s)
        self.assertTrue(self.allowed(9281136, s, 'action_b'))
        apply(self.a(9281136, 'action_b'), s)
        self.assertFalse(self.allowed(9281135, s))
        self.assertFalse(self.allowed(9281136, s))
        effects = apply(self.a(9281137), s)
        self.assertEqual([e[2] for e in effects if e[0] == 'dissent'], ['1'])
        self.assertFalse(self.allowed(9281137, s))
        self.assertTrue(self.allowed(9281135, s))

    def test_japan_accept_notice_preserves_rank_reject_preserves_source_gate(self):
        for key, index, dissent in (('action_a', 0, '-2'), ('action_c', 2, '2')):
            s = self.jp()
            apply(self.a(9281135), s); apply(self.a(9281136, key), s)
            self.assertIn(JP_ANSWERS[index], s.flags)
            effects = apply(self.a(9281137), s)
            self.assertEqual([e[2] for e in effects if e[0] == 'dissent'], [dissent])
            self.assertFalse(self.allowed(9281135, s))

    def test_japan_changed_relationship_notice_withdrawal_and_stale_reply(self):
        for change in ('war', 'newcompact', 'master'):
            s = self.jp()
            apply(self.a(9281135), s); apply(self.a(9281136), s)
            if change == 'war': s.wars.add(frozenset(('IND', 'JAP')))
            if change == 'newcompact': s.flags.add('ind_aubm_commitment_allied')
            if change == 'master': s.puppets.add('JAP')
            self.assertFalse(self.allowed(9281137, s))
            s.flags.add(JP_REQUEST)  # unrelated later pending must survive notice
            effects = apply(self.close(9281137, s), s)
            self.assertFalse(any(e[0] == 'dissent' for e in effects))
            self.assertIn(JP_REQUEST, s.flags)
            self.assertIn('ind_aubm_jp_tier_senior', s.flags)
        s = self.jp(); apply(self.a(9281135), s); apply(self.a(9281136, 'action_b'), s)
        apply(self.close(9281137, s, True), s)
        self.assertTrue(self.allowed(9281135, s))

    def test_callbacks_never_have_unguarded_free_cancel(self):
        roots = {9281135, 9281314, 9281315, 9281316}
        for eid in self.records.keys() - roots:
            for af in actions(self.events[eid]):
                self.assertIsNotNone(af.value.get('trigger'), eid)

    def test_missing_legacy_pending_releases_owned_japan_offer(self):
        s = self.jp()
        apply(self.a(9281135), s)
        s.flags.discard(JP_REQUEST)
        self.assertFalse(self.allowed(9281136, s))
        apply(self.close(9281136, s), s)
        self.assertNotIn(JP_OFFER, s.flags)
        self.assertTrue(self.allowed(9281135, s))

    def test_japan_foreign_lapse_cannot_clear_selected_notice(self):
        s = self.jp()
        apply(self.a(9281135), s); apply(self.a(9281136, 'action_b'), s)
        old_reply = next(a.value for a in actions(self.events[9281136]) if a.value.get('name') == 'Close an unrelated or completed reply' and evaluate(a.value.get('trigger'), s))
        self.assertFalse(apply(old_reply, s))
        self.assertIn(JP_ANSWERS[1], s.flags)

    def test_root_changed_state_or_insufficient_budget_does_not_dispatch(self):
        for family, (request, responders, base, reset) in FAMILIES.items():
            tag = next(iter(responders))
            s = self.state(tag)
            s.resources['money'] = 0
            self.assertFalse(self.allowed(request, s))
            s.resources['money'] = 10000
            s.puppets.add('IND')
            self.assertFalse(self.allowed(request, s))


if __name__ == '__main__': unittest.main()
