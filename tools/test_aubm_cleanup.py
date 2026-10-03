"""Executable script contracts for the compiled overlay, not DH engine emulation."""
from collections import Counter
import unittest

import build_aubm_cleanup as cleanup
from dh_save_spans import Node, parse, walk
from test_aubm_liberator import State, pair, evaluate


def tuple_node(node):
    return [(f.key, tuple_node(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields]


def permits(node, state):
    """Extend the existing strict predicate checker for alliance participation."""
    if node is None:
        return True
    def clause(key, value):
        if key == 'AND': return all(clause(f.key, f.value) for f in value.fields)
        if key == 'OR': return any(clause(f.key, f.value) for f in value.fields)
        if key == 'NOT': return not any(clause(f.key, f.value) for f in value.fields)
        if key == 'participant':
            assert value.get('value') == '4', 'Only any-alliance test is modeled'
            return any(value.get('country', 'IND') in p for p in state.alliances)
        if key == 'alliance_leader':
            assert value.get('value') == '0'
            return value.get('country', 'IND') in getattr(state, 'alliance_leaders', set())
        if key == 'month': return state.month >= int(value)
        if key == 'day': return state.day >= int(value)
        return evaluate([(key, tuple_node(value) if isinstance(value, Node) else value)], state)
    return all(clause(f.key, f.value) for f in node.fields)


def available_action(ev, index, state):
    return permits(cleanup.actions(ev)[index].value.get('trigger'), state)


class CleanupOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = cleanup.load_sources()
        cls.files, cls.details = cleanup.compile_files(cls.sources)
        cls.events = {}
        cls.event_list = []
        for text in cls.files.values():
            for ev in parse(text).all('event'):
                cls.event_list.append(ev)
                cls.events[int(ev.get('id'))] = ev

    def siam(self):
        s = State(); s.exists.add('SIA'); s.puppets['SIA'] = 'JAP'
        s.alliances.add(pair(('SIA', 'JAP')))
        s.wars |= {pair(('IND', 'SIA')), pair(('IND', 'JAP')), pair(('IND', 'SOV'))}
        s.flags |= {'ind_aubm_regional_current_sia', 'ind_aubm_regional_armistice_target_sia',
                    'ind_aubm_regional_armistice_outstanding'}
        for p in (1423, 1425): s.owned[p] = 'SIA'; s.control[p] = 'IND'
        return s

    def test_root_decision_tooltips_do_not_expand_all_child_conditions(self):
        for eid in cleanup.HUBS.values():
            ev=self.events[eid]
            for key in ('trigger','decision'):
                gate=ev.get(key)
                self.assertLess(gate.end-gate.start,512,(eid,key))
            for af in cleanup.actions(ev):
                commands=af.value.all('command')
                if len(commands)==1 and commands[0].get('type')=='event' and 9297120<=int(commands[0].get('which','0'))<9297190:
                    gate=af.value.get('trigger')
                    self.assertLess(gate.end-gate.start,64,(eid,af.value.get('name')))

    def test_political_programme_cannot_change_during_war(self):
        checked=0
        for eid in (9281910,9281911,9281912,9281914):
            for af in cleanup.actions(self.events[eid]):
                if any(c.get('type') not in ('event','trigger') for c in af.value.all('command')):
                    checked+=1
                    gate=af.value.get('trigger')
                    self.assertTrue(any(f.key=='atwar' and f.value=='no' for f in gate.fields),(eid,af.value.get('name')))
        self.assertGreater(checked,3)

    def test_wartime_roots_have_no_route_maze(self):
        for eid in (9297101,9297102,9297103):
            for af in cleanup.actions(self.events[eid]):
                for c in af.value.all('command'):
                    if c.get('type')=='event':
                        self.assertFalse(9297120<=int(c.get('which'))<9297190)
                        self.assertNotIn(c.get('which'),('9281910','9281912','9281914','9289499','9281913'))

    def test_annexed_siam_has_direct_government_branch(self):
        s=State();s.owned[1423]='IND'
        a=next(a.value for a in cleanup.actions(self.events[9297102]) if 'post-conquest' in a.value.get('name',''))
        self.assertTrue(permits(a.get('trigger'),s))
        s.exists.add('SIA');self.assertFalse(permits(a.get('trigger'),s))

    def test_generated_ids_unique_and_supported_action_keys(self):
        counts = Counter(int(e.get('id')) for e in self.event_list)
        self.assertFalse({eid: n for eid, n in counts.items() if n > 1})
        for ev in self.event_list:
            for af in cleanup.actions(ev):
                self.assertIn(af.key, ('action', 'action_a', 'action_b', 'action_c', 'action_d'), ev.get('id'))

    def test_siam_generic_offer_blocked_for_japanese_puppet_and_ally(self):
        s = self.siam(); s.flags.discard('ind_aubm_regional_armistice_outstanding')
        self.assertFalse(available_action(self.events[9282212], 0, s))
        s.puppets.clear(); self.assertFalse(available_action(self.events[9282212], 0, s))
        s.alliances.clear(); self.assertTrue(available_action(self.events[9282212], 0, s))

    def test_queued_siam_foreign_acceptance_cannot_grant_access_or_start_old_peace(self):
        s = self.siam()
        ev = self.events[9282222]
        for af in cleanup.actions(ev):
            if any(c.get('type') in ('access', 'relation') or
                   (c.get('type') == 'event' and c.get('which') in ('9282261', '9282262'))
                   for c in af.value.all('command')):
                self.assertFalse(permits(af.value.get('trigger'), s), af.value.get('name'))

    def test_foreign_reply_odds_and_expiry_are_mutually_exclusive(self):
        for eid, odds in ((9282800, [60, 25, 15]), (9283000, [75, 20, 5])):
            ev = self.events[eid]
            def state():
                s = State(); s.exists.add('ALB'); s.wars.add(pair(('IND', 'ALB')))
                s.flags |= {'ind_aubm_armistice_target_alb', 'ind_aubm_universal_armistice_outstanding'}
                s.owned[359] = 'ALB'; s.control[359] = 'IND'
                return s
            s = state()
            active = [a.value for a in cleanup.actions(ev) if permits(a.value.get('trigger'), s)]
            self.assertEqual([int(a.get('ai_chance')) for a in active], odds, eid)
            for change in ('coalition', 'control', 'pending', 'war'):
                s = state()
                if change == 'coalition': s.alliances.add(pair(('ALB', 'GER')))
                if change == 'control': s.control[359] = 'ALB'
                if change == 'pending': s.flags.discard('ind_aubm_armistice_target_alb')
                if change == 'war': s.wars.clear()
                active = [a.value for a in cleanup.actions(ev) if permits(a.value.get('trigger'), s)]
                self.assertEqual(len(active), 1, (eid, change))
                self.assertEqual(active[0].get('ai_chance'), '100')
                self.assertTrue(all(c.get('type') == 'clrflag' for c in active[0].all('command')))
        ev = self.events[9282222]; s = self.siam()
        active = [a.value for a in cleanup.actions(ev) if permits(a.value.get('trigger'), s)]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].get('ai_chance'), '100')
        self.assertTrue(all(c.get('type') == 'clrflag' for c in active[0].all('command')))

    def test_queued_siam_indian_acceptance_cannot_award_settlement_or_dissent(self):
        s = self.siam()
        for eid in (9282232, 9282242, 9282261, 9282262):
            for af in cleanup.actions(self.events[eid]):
                if any(c.get('type') == 'dissent' or
                       (c.get('type') == 'setflag' and 'armistice' in c.get('which', ''))
                       for c in af.value.all('command')):
                    self.assertFalse(permits(af.value.get('trigger'), s), (eid, af.value.get('name')))

    def test_queued_siam_ratification_blocked_and_has_effect_free_exit(self):
        s = self.siam(); ev = self.events[9282260]
        for af in cleanup.actions(ev):
            if any(c.get('type') == 'peace' for c in af.value.all('command')):
                self.assertFalse(permits(af.value.get('trigger'), s))
        self.assertTrue(any(permits(a.value.get('trigger'), s) and
                            all(c.get('type') == 'clrflag' for c in a.value.all('command'))
                            for a in cleanup.actions(ev)))

    def test_unaffiliated_minor_peace_allows_only_unaffiliated_signatories(self):
        gate = parse(cleanup.peace_gate('TUR'))
        s = State(); self.assertTrue(permits(gate, s))
        for a, b in (('IND', 'ENG'), ('TUR', 'GER')):
            s = State(); s.alliances.add(pair((a, b))); self.assertFalse(permits(gate, s))
        for tag in ('IND', 'TUR'):
            s = State(); s.puppets[tag] = 'ENG'; self.assertFalse(permits(gate, s))
        s = State(); s.alliances.add(pair(('IND', 'SIA'))); s.alliance_leaders = {'IND'}
        self.assertTrue(permits(gate, s))

    def test_siam_new_sequence_contains_no_indian_war_mutation_commands(self):
        for eid in range(9297000, 9297009):
            ev = self.events[eid]
            if ev.get('country') != 'IND': continue
            for af in cleanup.actions(ev):
                for c in af.value.all('command'):
                    self.assertNotIn(c.get('type'), ('peace', 'war', 'leave_alliance', 'alliance'))

    def test_siam_protection_still_requires_active_japan_war_and_detached_siam(self):
        s = self.siam(); s.flags.add('ind_lib1_siam_break_pending')
        s.puppets.clear(); s.alliances.clear(); s.wars.discard(pair(('IND', 'SIA')))
        ev = self.events[9297005]
        self.assertTrue(available_action(ev, 0, s))
        s.wars.discard(pair(('IND', 'JAP')))
        self.assertFalse(available_action(ev, 0, s))
        self.assertIn(pair(('IND', 'SOV')), s.wars)

    def test_siam_action_is_under_peace_talks(self):
        decisions = cleanup.collect_decisions(self.sources)
        self.assertEqual(next(d for d in decisions if d['id'] == 9297003)['group'], 'Peace Talks')

    def test_naval_modifiers_are_reversible_and_do_not_stack(self):
        s = State(); s.flags.add('ind_aubm_dockyard_efficiency_50')
        def run(eid):
            ev = self.events[eid]
            if not permits(ev.get('trigger'), s): return None
            amounts = {}
            for c in cleanup.actions(ev)[0].value.all('command'):
                if not permits(c.get('trigger'), s): continue
                if c.get('type') == 'setflag': s.flags.add(c.get('which'))
                if c.get('type') == 'clrflag': s.flags.discard(c.get('which'))
                if c.get('type') == 'build_time':
                    self.assertEqual(c.get('when'), 'on_upgrade')
                    self.assertEqual(c.get('where'), 'relative')
                    amounts[c.get('which')] = int(c.get('value'))
            return amounts
        self.assertEqual(run(9297180), {})
        peace = run(9297181); self.assertEqual(len(peace), 10)
        self.assertEqual(set(peace.values()), {25}); self.assertIsNone(run(9297181))
        s.wars.add(pair(('IND', 'SIA'))); war = run(9297182)
        self.assertEqual(war, {h: -25 for h in peace}); self.assertIsNone(run(9297182))
        s.wars.clear(); self.assertEqual(run(9297181), peace)

    def test_four_wartime_roots_available_before_1940(self):
        for eid in cleanup.HUBS.values():
            self.assertEqual(self.events[eid].get('date').get('year'), '1933')

    def test_full_local_peace_does_not_downgrade_indian_alliance_records(self):
        commands=cleanup.actions(self.events[9286400])[0].value.all('command')
        self.assertTrue(any(c.get('type')=='peace' and c.get('value')=='0' for c in commands))
        forbidden={'ind_v3_joined_allies','ind_v3_joined_axis','ind_v3_joined_comintern',
                   'ind_v3_joined_japan','ind_gc_cobelligerent','ind_gc_formal_axis',
                   'ind_v4a_treaty_cobelligerent','ind_v4a_treaty_formal_alliance',
                   'ind_aubm_jp_independent_cobelligerent','ind_aubm_jp_formal_alliance'}
        self.assertFalse(any(c.get('which') in forbidden for c in commands))

    def test_source_decision_trigger_is_not_lost_when_called_as_page(self):
        text = '''event = { id = 1 country = IND persistent = yes
decision = { flag = visible } decision_trigger = { flag = unlocked }
trigger = { flag = essential }
date = { day = 15 month = july year = 1937 }
deathdate = { day = 5 month = november year = 1941 }
name = "Test" action_a = { name = "Buy" command = { type = money value = -100 } }
}'''
        decisions = cleanup.collect_decisions({'fixture.txt': text})
        converted = parse(cleanup.navigation(text, decisions)).all('event')[0]
        gate = cleanup.actions(converted)[0].value.get('trigger')
        flag_names = {f.value for n in walk(gate) for f in n.fields if f.key == 'flag'}
        self.assertTrue({'visible', 'unlocked'} <= flag_names)
        self.assertNotIn('essential', flag_names)
        text = text.replace('decision_trigger = { flag = unlocked }', '')
        decisions = cleanup.collect_decisions({'fixture.txt': text})
        converted = parse(cleanup.navigation(text, decisions)).all('event')[0]
        gate = cleanup.actions(converted)[0].value.get('trigger')
        flag_names = {f.value for n in walk(gate) for f in n.fields if f.key == 'flag'}
        self.assertTrue({'visible', 'essential'} <= flag_names)

    def test_menu_gate_respects_exact_calendar_boundaries(self):
        event = parse('event = { date = { year = 1937 month = july day = 15 } deathdate = { year = 1941 month = november day = 5 } }').all('event')[0]
        gate = parse(cleanup.date_gate(event))
        for y, m, d, expected in ((1937, 6, 14, False), (1937, 6, 15, True),
                                  (1938, 0, 0, True), (1941, 10, 5, True),
                                  (1941, 10, 6, False), (1942, 0, 0, False)):
            s = State(); s.year = y; s.month = m; s.day = d
            self.assertEqual(permits(gate, s), expected, (y,m,d))

    def test_cancel_does_not_consume_single_use_decision(self):
        text = '''event = { id = 123 country = IND decision = { flag = visible }
name = "Single choice" action_a = { name = "Buy" command = { type = money value = -100 } } }'''
        decisions = cleanup.collect_decisions({'fixture.txt': text})
        converted = parse(cleanup.navigation(text, decisions)).all('event')[0]
        self.assertEqual(converted.get('persistent'), 'yes')
        cancel = next(a for a in cleanup.actions(converted) if 'Cancel' in a.value.get('name', ''))
        self.assertFalse(cancel.value.all('command'))
        success = cleanup.actions(converted)[0].value
        done = [c.get('which') for c in success.all('command') if c.get('type') == 'setflag']
        self.assertEqual(done, ['ind_cleanup1_done_123'])
        s = State(); s.flags.add('visible')
        self.assertTrue(permits(success.get('trigger'), s))
        s.flags.add(done[0]); self.assertFalse(permits(success.get('trigger'), s))
        self.assertTrue(permits(cancel.value.get('trigger'), s))


if __name__ == '__main__': unittest.main()
