"""Pure source-state reply scenarios; never execute the game or change saves."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest

from dh_save_spans import Node, parse
from aubm_redesign_diplomacy import transform as diplomacy, actions
from aubm_redesign_cooperation import transform as cooperation
from aubm_redesign_replies import transform, REGIONAL, REQUEST, ACTIVE, DEFERRED, pending, protocol_pending


@dataclass
class State:
    flags: set = field(default_factory=set)
    wars: set = field(default_factory=set)
    alliances: set = field(default_factory=set)
    puppets: set = field(default_factory=set)
    countries: set = field(default_factory=lambda: set('IND SOV CHI SIA PER AFG ENG USA GER ITA JAP'.split()))
    resources: dict = field(default_factory=lambda: dict(money=10000, supplies=10000, oil=10000))


def evaluate(node, s):
    if not isinstance(node, Node):
        return True
    results = []
    for f in node.fields:
        k, v = f.key, f.value
        if k == 'AND':
            r = evaluate(v, s)
        elif k == 'OR':
            r = any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'NOT':
            r = not any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'flag':
            r = v in s.flags
        elif k == 'exists':
            r = v in s.countries
        elif k == 'ispuppet':
            r = v in s.puppets
        elif k in ('war', 'alliance'):
            r = frozenset(v.all('country')) in (s.wars if k == 'war' else s.alliances)
        elif k in ('money', 'supplies', 'oil'):
            r = s.resources[k] >= float(v)
        elif k == 'ai':
            r = v == 'no'
        else:
            raise AssertionError('Unsupported predicate: ' + k)
        results.append(r)
    return all(results)


def apply(action, state):
    """Apply bookkeeping/debits only; returned effects expose native commands."""
    effects = []
    for c in action.all('command'):
        if not evaluate(c.get('trigger'), state):
            continue
        kind, which = c.get('type'), c.get('which')
        if kind == 'setflag':
            state.flags.add(which)
        elif kind == 'clrflag':
            state.flags.discard(which)
        elif kind in ('money', 'supplies', 'oilpool'):
            state.resources['oil' if kind == 'oilpool' else kind] += float(c.get('value'))
        effects.append((kind, which))
    return effects


class ReplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events/aubm_v4'
        raw = {str(root / n): (root / n).read_text(encoding='cp1252') for n in
               ('38_soviet_campaigns.txt', '39_non_aligned_campaigns.txt')}
        cls.input = cooperation(diplomacy(raw)[0])[0]
        cls.changed, cls.records = transform(cls.input)
        cls.events = {int(e.get('id')): e for t in cls.changed.values() for e in parse(t).all('event')}

    def action(self, eid, key='action_a'):
        return self.events[eid].get(key)

    def allowed(self, eid, state, key='action_a'):
        return evaluate(self.action(eid, key).get('trigger'), state)

    def choice(self, eid, state, label):
        return next(a.value for a in actions(self.events[eid])
                    if a.value.get('name') == label and evaluate(a.value.get('trigger'), state))

    def nam(self, name):
        return State(flags={pending(name), 'ind_v43_nam_doctrine_set', 'ind_v43_nam_outreach_started'})

    def test_dispatch_assigns_exact_four_tokens_and_cannot_repeat(self):
        s = State(flags={'ind_v43_nam_doctrine_set'})
        self.assertTrue(self.allowed(9281501, s))
        apply(self.action(9281501), s)
        for _, name, _ in REGIONAL.values():
            self.assertIn(pending(name), s.flags)
        self.assertFalse(self.allowed(9281501, s))

    def test_each_regional_chain_accepts_once_and_preserves_reward(self):
        for base, (tag, name, _) in REGIONAL.items():
            s = self.nam(name)
            self.assertTrue(self.allowed(base, s))
            apply(self.action(base), s)
            self.assertIn(pending(name), s.flags)
            self.assertTrue(self.allowed(base + 1, s))
            effects = apply(self.action(base + 1), s)
            self.assertIn(('guarantee', 'IND'), effects)
            self.assertIn('ind_v43_nam_' + name + '_partner', s.flags)
            self.assertNotIn(pending(name), s.flags)
            self.assertFalse(self.allowed(base + 1, s))

    def test_regional_war_master_and_defunct_partner_close_only_owned_offer(self):
        for base, (tag, name, _) in REGIONAL.items():
            for change in ('war', 'puppet', 'absent', 'new_commitment'):
                s = self.nam(name)
                s.flags.add(pending('other'))
                if change == 'war':
                    s.wars.add(frozenset(('IND', tag)))
                elif change == 'puppet':
                    s.puppets.add(tag)
                elif change == 'absent':
                    s.countries.remove(tag)
                else:
                    s.flags.add('ind_aubm_commitment_japan')
                for eid in (base, base + 1, base + 2, base + 3):
                    self.assertFalse(self.allowed(eid, s), (eid, change))
                lapse = self.choice(base + 1, s, 'Close this obsolete offer without agreement')
                apply(lapse, s)
                self.assertNotIn(pending(name), s.flags)
                self.assertIn(pending('other'), s.flags)
                self.assertNotIn('ind_v43_nam_' + name + '_partner', s.flags)

    def test_valid_human_withdrawal_resolves_offer_and_preserves_other_negotiation(self):
        s = self.nam('persia')
        s.flags.update({pending('siam'), 'ind_aubm_diplomatic_negotiation_pending', 'ind_aubm_negotiation_german'})
        withdraw = self.choice(9281512, s, 'Withdraw this offer without agreement')
        effects = apply(withdraw, s)
        self.assertEqual({kind for kind, _ in effects}, {'setflag', 'clrflag'})
        self.assertNotIn(pending('persia'), s.flags)
        self.assertIn('ind_v43_nam_persia_resolved', s.flags)
        self.assertIn(pending('siam'), s.flags)
        self.assertIn('ind_aubm_diplomatic_negotiation_pending', s.flags)
        self.assertFalse(self.allowed(9281512, s))

    def test_counteroffer_protocol_has_separate_consumed_token_and_live_guard(self):
        for base, (tag, name, protocol) in REGIONAL.items():
            s = self.nam(name)
            before = dict(s.resources)
            apply(self.action(base + 2), s)
            self.assertLess(s.resources['money'], before['money'])
            self.assertNotIn(pending(name), s.flags)
            self.assertIn(protocol_pending(name), s.flags)
            self.assertTrue(self.allowed(protocol, s))
            s.wars.add(frozenset(('IND', tag)))
            self.assertFalse(self.allowed(protocol, s))
            lapse = self.choice(protocol, s, 'Close this obsolete offer without agreement')
            apply(lapse, s)
            self.assertNotIn(protocol_pending(name), s.flags)
            self.assertIn('ind_v43_nam_' + name + '_partner', s.flags)

    def test_all_unaffordable_options_still_allow_owned_cleanup(self):
        s = self.nam('afghan')
        s.resources = dict(money=0, supplies=0, oil=0)
        for key in ('action_a', 'action_b', 'action_c'):
            self.assertFalse(self.allowed(9281517, s, key))
        self.choice(9281517, s, 'Close this obsolete offer without agreement')

    def test_soviet_refusal_defer_reset_then_retry_accepts_once(self):
        s = State(flags={REQUEST, 'ind_v4_sov_technical_only'})
        s.wars.add(frozenset(('IND', 'JAP')))
        self.assertTrue(self.allowed(9281456, s))
        apply(self.action(9281456, 'action_c'), s)
        self.assertTrue(self.allowed(9281459, s, 'action_c'))
        apply(self.action(9281459, 'action_c'), s)
        self.assertIn(DEFERRED, s.flags)
        self.assertNotIn(REQUEST, s.flags)
        # Execute the actual reset/request bookkeeping, without claiming native
        # elapsed-time or queued-event delivery has been simulated.
        self.assertTrue(self.allowed(9281446, s))
        apply(self.action(9281446), s)
        self.assertTrue(self.allowed(9281455, s))
        apply(self.action(9281455), s)
        self.assertTrue(self.allowed(9281457, s))
        effects = apply(self.action(9281457), s)
        self.assertIn(('max_organization', 'land'), effects)
        self.assertIn(ACTIVE, s.flags)
        self.assertFalse(self.allowed(9281457, s))

    def test_soviet_war_or_japanese_alignment_cleans_only_eastern_pending(self):
        for change in ('war', 'ally', 'puppet'):
            s = State(flags={REQUEST, 'ind_aubm_negotiation_german', 'ind_aubm_diplomatic_negotiation_pending'})
            s.wars.add(frozenset(('CHI', 'JAP')))
            if change == 'war':
                s.wars.add(frozenset(('IND', 'SOV')))
            elif change == 'ally':
                s.alliances.add(frozenset(('IND', 'JAP')))
            else:
                s.puppets.add('SOV')
            self.assertFalse(self.allowed(9281457, s))
            apply(self.choice(9281457, s, 'Close this obsolete offer without agreement'), s)
            self.assertNotIn(REQUEST, s.flags)
            self.assertIn('ind_aubm_negotiation_german', s.flags)

    def test_soviet_explicit_withdrawal_unblocks_without_award(self):
        s = State(flags={REQUEST})
        s.wars.add(frozenset(('CHI', 'JAP')))
        withdrawal = self.choice(9281458, s, 'Withdraw this offer without agreement')
        effects = apply(withdrawal, s)
        self.assertEqual(effects, [('clrflag', REQUEST)])
        self.assertNotIn(ACTIVE, s.flags)

    def test_no_free_cancel_on_valid_pending_callbacks(self):
        for eid in range(9281456, 9281460):
            s = State(flags={REQUEST})
            s.wars.add(frozenset(('CHI', 'JAP')))
            available = [a.value for a in actions(self.events[eid]) if evaluate(a.value.get('trigger'), s)]
            self.assertTrue(available)
            self.assertTrue(all(a.all('command') for a in available))
        for base, (_, name, _) in REGIONAL.items():
            s = self.nam(name)
            for eid in range(base, base + 4):
                available = [a.value for a in actions(self.events[eid]) if evaluate(a.value.get('trigger'), s)]
                self.assertTrue(available)
                self.assertTrue(all(a.all('command') for a in available))

    def test_ended_japanese_war_blocks_awards_and_releases_own_pending(self):
        for eid in range(9281456, 9281460):
            s = State(flags={REQUEST, 'ind_aubm_negotiation_german'})
            for key in ('action_a', 'action_b', 'action_c'):
                if self.events[eid].get(key):
                    self.assertFalse(self.allowed(eid, s, key), (eid, key))
            before = dict(s.resources)
            effects = apply(self.choice(eid, s, 'Close this obsolete offer without agreement'), s)
            self.assertEqual(effects, [('clrflag', REQUEST)])
            self.assertEqual(s.resources, before)
            self.assertNotIn(ACTIVE, s.flags)
            self.assertIn('ind_aubm_negotiation_german', s.flags)

    def test_china_bilateral_choices_recheck_partner_without_blocking_other_options(self):
        for change in ('absent', 'hostile', 'puppet'):
            s = State(flags={REQUEST}, wars={frozenset(('IND', 'JAP'))})
            if change == 'absent':
                s.countries.remove('CHI')
            elif change == 'hostile':
                s.wars.add(frozenset(('IND', 'CHI')))
            else:
                s.puppets.add('CHI')
            self.assertFalse(self.allowed(9281458, s, 'action_c'))
            self.assertFalse(self.allowed(9281459, s, 'action_a'))
            self.assertTrue(self.allowed(9281458, s, 'action_b'))
            self.assertTrue(self.allowed(9281459, s, 'action_b'))

    def test_unowned_stale_reply_cannot_clear_new_other_offer(self):
        s = self.nam('siam')
        reply = self.choice(9281511, s, 'Close an unrelated or completed reply')
        self.assertEqual(apply(reply, s), [])
        self.assertIn(pending('siam'), s.flags)

    def test_no_calendar_or_event_ids_added_idempotent_limitations_reported(self):
        self.assertEqual(transform(self.changed)[0], self.changed)
        original_ids = {int(e.get('id')) for t in self.input.values() for e in parse(t).all('event')}
        self.assertEqual(original_ids, set(self.events))
        for eid, records in self.records.items():
            if any(r['status'] == 'CORRECTED_SCRIPT' for r in records):
                self.assertIsNone(self.events[eid].get('trigger'))
                self.assertIsNone(self.events[eid].get('date'))
                self.assertTrue(any(r['status'] == 'UNRESOLVED' for r in records))
        self.assertEqual(self.records[9281520][0]['status'], 'UNRESOLVED')


if __name__ == '__main__':
    unittest.main()
