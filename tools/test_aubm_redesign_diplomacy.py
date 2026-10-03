"""Script-level staged tests; no engine, installation or save modifications."""
from pathlib import Path
import unittest

from dh_save_spans import Node, parse
from aubm_redesign_diplomacy import transform, actions, ALLIED_PROPOSAL, SAFE_CANCEL_IDS

ROOT = Path(__file__).resolve().parents[1]


def evaluate(node, flags=None, wars=None, alliances=None, resources=None, puppets=None):
    flags, wars, alliances = flags or {}, wars or set(), alliances or set()
    resources, puppets = resources or {}, puppets or set()
    def ev(n):
        result = []
        for f in n.fields:
            k, v = f.key, f.value
            if k == 'NOT':
                # Installed event commands.txt: NONE of the child conditions
                # may be true. Multi-child NOT is NOR, not negated AND.
                r = not any(ev(Node(fields=[x])) for x in v.fields)
            elif k == 'AND':
                r = ev(v)
            elif k == 'OR':
                r = any(ev(Node(fields=[x])) for x in v.fields)
            elif k == 'flag':
                if isinstance(v, Node):
                    val = flags.get(v.get('which'), 0)
                    r = val >= int(v.get('value', '1'))
                else:
                    r = bool(flags.get(v, 0))
            elif k == 'war':
                r = frozenset(v.all('country')) in wars
            elif k == 'alliance':
                r = frozenset(v.all('country')) in alliances
            elif k == 'atwar':
                r = any(('IND' if v in ('yes', 'no') else v) in p for p in wars)
                if v == 'no':
                    r = not r
            elif k == 'participant':
                r = any(v.get('country') in p for p in alliances)
            elif k == 'ispuppet':
                r = v in puppets
            elif k == 'exists':
                r = True
            elif k in ('money', 'supplies', 'oil', 'ic', 'year'):
                r = resources.get(k, 99999) >= float(v)
            elif k in ('land_percentage', 'naval_percentage', 'air'):
                r = True
            elif k == 'ai':
                r = v == 'no'
            else:
                raise AssertionError('Unsupported predicate: ' + k)
            result.append(r)
        return all(result)
    return ev(node) if node else True


class StagedDiplomacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {str(p.relative_to(ROOT)): p.read_text(encoding='cp1252')
                      for p in (ROOT / 'mod/db/events').rglob('*.txt')}
        cls.changed, cls.reviews = transform(cls.source)
        cls.events = {int(e.get('id')): e for t in cls.changed.values()
                      for e in parse(t).all('event')}

    def allowed(self, eid, key, **state):
        return evaluate(self.events[eid].get(key).get('trigger'), **state)

    def test_engine_not_truth_table_is_nor_and_explicit_and_is_distinct(self):
        nor = parse('trigger = { NOT = { flag = first flag = second } }').get('trigger')
        nand = parse('trigger = { NOT = { AND = { flag = first flag = second } } }').get('trigger')
        for first, second, expected_nor, expected_nand in (
                (0, 0, True, True), (1, 0, False, True),
                (0, 1, False, True), (1, 1, False, False)):
            flags = {'first': first, 'second': second}
            self.assertEqual(evaluate(nor, flags=flags), expected_nor)
            self.assertEqual(evaluate(nand, flags=flags), expected_nand)

    def test_pure_and_idempotent(self):
        source = dict(self.source)
        again, _ = transform(self.changed)
        self.assertEqual(again, self.changed)
        self.assertEqual(source, self.source)
        self.assertNotEqual(self.changed, self.source)

    def test_alliance_leaves_lock_wartime_and_existing_alliance(self):
        count = 0
        for eid, e in self.events.items():
            if e.get('country') != 'IND':
                continue
            for a in actions(e):
                if any(c.get('type') == 'alliance' for c in a.value.all('command')):
                    count += 1
                    for state in ({'wars': {frozenset(('IND', 'SIA'))}},
                                  {'alliances': {frozenset(('IND', 'USA'))}}):
                        self.assertFalse(evaluate(a.value.get('trigger'), **state), (eid, a.key))
        self.assertGreaterEqual(count, 17)

    def test_same_compact_upgrade_allowed_competing_compact_blocked(self):
        self.assertTrue(self.allowed(9281934, 'action_a',
            flags={'ind_aubm_commitment_allied': 1, 'ind_v4a_treaty_commonwealth': 1}))
        self.assertFalse(self.allowed(9281934, 'action_a',
            flags={'ind_aubm_jp_partnership': 1}))
        self.assertTrue(self.allowed(9281914, 'action_a',
            flags={'ind_aubm_commitment_japan': 1, 'ind_aubm_jp_partnership': 1}))

    def test_conference_replay_closed_at_each_choice(self):
        for key in ('action_a', 'action_b', 'action_c', 'action_d'):
            self.assertTrue(self.allowed(9281200, key))
            for flag in ('ind_v4a_treaty_commonwealth', 'ind_v4a_treaty_naval_compact',
                         'ind_v4a_allied_framework_settled'):
                self.assertFalse(self.allowed(9281200, key, flags={flag: 1}))

    def test_purchase_exact_thresholds_each_resource(self):
        flags = {'ind_aubm_diplomatic_negotiation_pending': 1, 'ind_aubm_negotiation_japan': 1}
        paid = {'money': 1500, 'supplies': 3000, 'oil': 1500}
        self.assertTrue(self.allowed(9281120, 'action_b', flags=flags, resources=paid))
        for resource in paid:
            insufficient = dict(paid)
            insufficient[resource] -= 1
            self.assertFalse(self.allowed(9281120, 'action_b', flags=flags, resources=insufficient))

    def test_japanese_delayed_reply_changed_facts_and_cleanup(self):
        flags = {'ind_aubm_jp_seniority_review_pending': 1, 'ind_aubm_jp_partnership': 1}
        for key in ('action_a', 'action_b', 'action_c'):
            self.assertTrue(self.allowed(9281136, key, flags=flags))
            self.assertFalse(self.allowed(9281136, key, flags={}))
            self.assertFalse(self.allowed(9281136, key, flags=flags,
                wars={frozenset(('IND', 'JAP'))}))
            self.assertFalse(self.allowed(9281136, key, flags=flags, puppets={'IND'}))
        self.assertIsNone(self.events[9281136].get('trigger'))
        lapse = actions(self.events[9281136])[-1].value
        self.assertTrue(evaluate(lapse.get('trigger'), flags={}))
        self.assertEqual([(c.get('type'), c.get('which')) for c in lapse.all('command')],
                         [('clrflag', 'ind_aubm_jp_seniority_review_pending')])

    def test_request_leaf_cannot_repeat_pending_or_request_after_withdrawal(self):
        flags = {'ind_aubm_jp_partnership': 1, 'ind_aubm_jp_influence': 7}
        self.assertTrue(self.allowed(9281135, 'action_a', flags=flags))
        self.assertFalse(self.allowed(9281135, 'action_a', flags={}))
        flags['ind_aubm_jp_seniority_review_pending'] = 1
        self.assertFalse(self.allowed(9281135, 'action_a', flags=flags))

    def test_allied_reply_and_outcome_recheck_pending_and_treaty(self):
        flags = {'ind_aubm_diplomatic_negotiation_pending': 1,
                 'ind_aubm_negotiation_allied': 1, 'ind_v4a_proposal_commonwealth': 1}
        for eid in (9281201, 9281205):
            self.assertTrue(self.allowed(eid, 'action_a', flags=flags))
            self.assertFalse(self.allowed(eid, 'action_a', flags={}))
            self.assertFalse(self.allowed(eid, 'action_a', flags=flags,
                wars={frozenset(('IND', 'ENG'))}))
            self.assertFalse(self.allowed(eid, 'action_a',
                flags={**flags, 'ind_v4a_treaty_commonwealth': 1}))
            self.assertIsNone(self.events[eid].get('trigger'))
            lapse = next(a.value for a in actions(self.events[eid])
                         if a.value.get('name') == 'Close the obsolete owned Allied proposal')
            self.assertFalse(evaluate(lapse.get('trigger'), flags={'ind_aubm_negotiation_japan': 1}))

    def test_old_commonwealth_reply_cannot_cancel_new_naval_proposal(self):
        flags = {'ind_aubm_negotiation_allied': 1,
                 'ind_aubm_diplomatic_negotiation_pending': 1,
                 'ind_v4a_proposal_naval_compact': 1,
                 'ind_v4a_allied_framework_started': 1}
        for eid in (9281201, 9281205, 9281206, 9281207):
            available = [a.value for a in actions(self.events[eid])
                         if evaluate(a.value.get('trigger'), flags=flags)]
            self.assertTrue(available)
            self.assertTrue(all(not a.all('command') for a in available), eid)

    def test_valid_pending_reply_has_no_effect_free_cancel(self):
        for eid, proposal in ALLIED_PROPOSAL.items():
            flags = {'ind_aubm_negotiation_allied': 1,
                     'ind_aubm_diplomatic_negotiation_pending': 1,
                     'ind_v4a_proposal_' + proposal: 1}
            available = [a.value for a in actions(self.events[eid])
                         if evaluate(a.value.get('trigger'), flags=flags)]
            self.assertTrue(available, eid)
            self.assertTrue(all(a.all('command') for a in available), eid)
        self.assertFalse(any('Cancel' in a.value.get('name', '')
                             for a in actions(self.events[9281120])))

    def test_german_and_soviet_pending_replies_have_no_free_cancel(self):
        for eid, kind in ((9281304, 'german'), (9281453, 'soviet')):
            flags = {'ind_aubm_diplomatic_negotiation_pending': 1,
                     'ind_aubm_negotiation_' + kind: 1}
            available = [a.value for a in actions(self.events[eid])
                         if evaluate(a.value.get('trigger'), flags=flags)]
            self.assertTrue(available, eid)
            self.assertTrue(all(a.all('command') for a in available), eid)
            for state in ({'wars': {frozenset(('IND', 'JAP'))}},
                          {'alliances': {frozenset(('IND', 'USA'))}},
                          {'puppets': {'IND'}}):
                available = [a.value for a in actions(self.events[eid])
                             if evaluate(a.value.get('trigger'), flags=flags, **state)]
                self.assertTrue(available, (eid, state))
                self.assertTrue(all(a.all('command') for a in available), (eid, state))
                # Every available terminal reply releases its own pending state.
                self.assertTrue(all(any(c.get('type') == 'clrflag' and
                    c.get('which') == 'ind_aubm_negotiation_' + kind
                    for c in a.all('command')) for a in available))

    def test_german_wartime_fallback_preserves_wars_and_new_other_negotiation(self):
        flags = {'ind_aubm_diplomatic_negotiation_pending': 1,
                 'ind_aubm_negotiation_german': 1, 'ind_gc_berlin_negotiating': 1}
        wars = {frozenset(('IND', 'JAP'))}
        available = [a.value for a in actions(self.events[9281304])
                     if evaluate(a.value.get('trigger'), flags=flags, wars=wars)]
        self.assertEqual(len(available), 1)
        self.assertTrue(all(c.get('type') == 'clrflag' for c in available[0].all('command')))
        other = {'ind_aubm_diplomatic_negotiation_pending': 1,
                 'ind_aubm_negotiation_japan': 1}
        for eid in (9281304, 9281453):
            available = [a.value for a in actions(self.events[eid])
                         if evaluate(a.value.get('trigger'), flags=other, wars=wars)]
            self.assertTrue(available)
            self.assertTrue(all(not a.all('command') for a in available))

    def test_free_cancel_insertion_is_strictly_allowlisted(self):
        original = {int(e.get('id')): e for t in self.source.values() for e in parse(t).all('event')}
        for eid, event in self.events.items():
            before = {a.value.get('name') for a in actions(original[eid])}
            new_cancels = [a for a in actions(event)
                           if a.value.get('name') == 'Cancel - close without changes'
                           and a.value.get('name') not in before]
            if new_cancels:
                self.assertIn(eid, SAFE_CANCEL_IDS)

    def test_existing_numeric_influence_is_never_reset(self):
        cmd = next(c for c in self.events[9281914].get('action_a').all('command')
                   if c.get('which') == 'ind_aubm_jp_influence')
        for amount in (1, 7, 12, 32767):
            self.assertFalse(evaluate(cmd.get('trigger'), flags={'ind_aubm_jp_influence': amount}))
        self.assertTrue(evaluate(cmd.get('trigger')))

    def test_information_action_no_war_and_preserves_existing_other_commands(self):
        e = self.events[9281140]
        self.assertFalse(any(c.get('type') in ('war', 'peace', 'leave_alliance')
                             for c in e.get('action_a').all('command')))
        self.assertTrue(any(c.get('which') == 'ind_aubm_jp_southern_theatre'
                            for c in e.get('action_a').all('command')))

    def test_every_modified_indian_event_keeps_free_cancel(self):
        for eid, records in self.reviews.items():
            e = self.events[eid]
            if (eid in SAFE_CANCEL_IDS and e.get('country') == 'IND'
                    and any(r['status'] == 'CORRECTED_SCRIPT' for r in records)):
                self.assertTrue(any(not a.value.all('command') for a in actions(e)), eid)

    def test_uncertain_cases_not_claimed_complete(self):
        self.assertEqual(self.reviews[9281165][0]['status'], 'UNRESOLVED')
        self.assertTrue(any(r['status'] == 'UNRESOLVED' for r in self.reviews[9280968]))


if __name__ == '__main__':
    unittest.main()
