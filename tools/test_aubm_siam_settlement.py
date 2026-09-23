"""Siam script contracts. Foreign-government/war transitions are not emulated."""
import copy
import unittest

import aubm_siam_settlement as siam
import generate_aubm_liberator as lib
from test_aubm_liberator import State, pair, parse, get, values, evaluate, execute, is_action


class SiamSettlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {int(get(e, 'id')): e for k, e in parse('\n'.join(siam.render_events())) if k == 'event'}

    def state(self):
        s = State()
        s.exists.add('SIA')
        s.puppets['SIA'] = 'JAP'
        s.alliances.add(pair(('SIA', 'JAP')))
        s.wars |= {pair(('IND', 'JAP')), pair(('IND', 'SIA')), pair(('IND', 'SOV'))}
        for p in siam.HUBS:
            s.owned[p] = 'SIA'
            s.control[p] = 'IND'
        return s

    def gate(self, offset, state):
        return evaluate(get(self.events[siam.BASE+offset], 'trigger', []), state)

    def action(self, offset, letter='a'):
        return get(self.events[siam.BASE+offset], 'action_'+letter)

    def available(self, offset, state, letter='a'):
        return evaluate(get(self.action(offset, letter), 'trigger', []), state)

    def ready(self):
        s = self.state()
        execute(self.action(0), s)
        s.event_dates[siam.BASE] = 0
        s.day = siam.HOLD_DAYS
        execute(self.action(2), s)
        return s

    def detached(self):
        # Supply the expected engine result explicitly; do not model the commands.
        s = self.ready()
        execute(self.action(3), s)
        s.puppets.pop('SIA')
        s.alliances.clear()
        s.wars.discard(pair(('IND', 'SIA')))
        for p in siam.HUBS: s.control[p] = 'SIA'
        return s

    def test_all_non_japanese_routes_and_parallel_soviet_war(self):
        for route in ('sovereign', 'allied', 'german', 'soviet'):
            s = self.state(); s.flags = {'ind_aubm_route_'+route}
            self.assertTrue(self.gate(0, s), route)
        s.alliances.add(pair(('IND', 'JAP')))
        self.assertFalse(self.gate(0, s))

    def test_both_current_owned_hubs_and_both_wars_required(self):
        for p in siam.HUBS:
            s = self.state(); s.control[p] = 'SIA'; self.assertFalse(self.gate(0, s))
            s = self.state(); s.owned[p] = 'IND'; self.assertFalse(self.gate(0, s))
        for tag in ('SIA', 'JAP'):
            s = self.state(); s.wars.discard(pair(('IND', tag))); self.assertFalse(self.gate(0, s))

    def test_japan_puppet_or_ally_qualifies_but_free_siam_does_not(self):
        s = self.state(); s.alliances.clear(); self.assertTrue(self.gate(0, s))
        s = self.state(); s.puppets.clear(); self.assertTrue(self.gate(0, s))
        s.alliances.clear(); self.assertFalse(self.gate(0, s))

    def test_hold_matures_at_21_days_and_loss_resets(self):
        s = self.state(); execute(self.action(0), s); s.event_dates[siam.BASE] = 0
        s.day = siam.HOLD_DAYS-1; self.assertFalse(self.gate(2, s))
        s.day += 1; self.assertTrue(self.gate(2, s)); execute(self.action(2), s)
        s.control[1425] = 'JAP'; self.assertTrue(self.gate(1, s)); execute(self.action(1), s)
        s.control[1425] = 'IND'; self.assertFalse(self.available(3, s))
        self.assertTrue(self.gate(0, s))

    def test_offer_cancel_is_effect_free(self):
        s = self.ready(); before = copy.deepcopy(s)
        self.assertTrue(execute(self.action(3, 'b'), s)); self.assertEqual(s, before)

    def test_offer_is_once_pending_and_response_rechecks_front(self):
        s = self.ready(); self.assertTrue(execute(self.action(3), s))
        self.assertFalse(self.available(3, s)); self.assertTrue(self.available(4, s))
        s.control[1423] = 'JAP'; self.assertFalse(self.available(4, s))
        self.assertTrue(self.available(4, s, 'b'))

    def test_government_exit_is_siam_side_and_precedes_delayed_check(self):
        e = self.events[siam.BASE+4]; self.assertEqual(get(e, 'country'), 'SIA')
        commands = values(self.action(4), 'command')
        self.assertEqual([get(c, 'type') for c in commands], ['end_puppet', 'leave_alliance', 'event'])
        self.assertEqual(get(commands[1], 'when'), '1')
        self.assertEqual(get(commands[2], 'when'), '1')
        self.assertEqual(get(commands[2], 'where'), 'IND')

    def test_verified_exit_allows_protection(self):
        s = self.detached(); self.assertTrue(self.available(5, s))
        self.assertIn(pair(('IND', 'SOV')), s.wars)

    def test_failed_exit_or_lost_japan_war_blocks_protection(self):
        for change in ('puppet', 'alliance', 'war', 'japan_peace', 'third_party_control'):
            s = self.detached()
            if change == 'puppet': s.puppets['SIA'] = 'JAP'
            if change == 'alliance': s.alliances.add(pair(('SIA', 'AFG')))
            if change == 'war': s.wars.add(pair(('SIA', 'ENG')))
            if change == 'japan_peace': s.wars.discard(pair(('IND', 'JAP')))
            if change == 'third_party_control': s.control[1423] = 'JAP'
            self.assertFalse(self.available(5, s), change)
            self.assertTrue(self.available(5, s, 'b'), change)

    def test_protection_check_requires_actual_puppet_and_active_japanese_war(self):
        s = self.detached(); s.flags.add(lib.P+'siam_detached')
        self.assertFalse(self.available(7, s))
        s.puppets['SIA'] = 'IND'; self.assertTrue(self.available(7, s))
        s.wars.discard(pair(('IND', 'JAP'))); self.assertFalse(self.available(7, s))

    def test_completed_outcome_cannot_replay(self):
        s = self.detached(); s.flags.add(lib.P+'siam_detached'); s.puppets['SIA'] = 'IND'
        execute(self.action(7), s)
        self.assertFalse(self.available(7, s)); self.assertFalse(self.gate(0, s))
        self.assertIn('ind_aubm_regional_protected_sia', s.flags)

    def test_no_peace_war_alliance_or_free_modifier_commands_anywhere(self):
        for e in self.events.values():
            for k, a in e:
                if not is_action(k): continue
                for c in values(a, 'command'):
                    self.assertNotIn(get(c, 'type'), ('peace', 'war', 'alliance', 'tc_mod', 'industrial_modifier', 'research_mod'))

    def test_abandoned_country_cleans_pending_state(self):
        s = self.ready(); execute(self.action(3), s); s.exists.discard('SIA')
        self.assertTrue(self.gate(8, s)); execute(self.action(8), s)
        self.assertNotIn(lib.P+'siam_break_pending', s.flags)

    def test_id_range_unique_and_callbacks_target_correct_country(self):
        self.assertEqual(len(self.events), 9)
        for eid, e in self.events.items():
            self.assertTrue(9297000 <= eid < 9297100)
            for k, a in e:
                if not is_action(k): continue
                for c in values(a, 'command'):
                    if get(c, 'type') == 'event':
                        target = self.events[int(get(c, 'which'))]
                        self.assertEqual(get(c, 'where'), get(target, 'country'))


if __name__ == '__main__': unittest.main()
