"""Map/flag regression checks, not native campaign simulation."""
from pathlib import Path
import unittest
from dh_save_spans import parse
from aubm_redesign_western import transform,EDITED_IDS,MODULE,LIMITED,MAJOR,aa,CURRENT,SUSPENDED
from test_aubm_redesign_withdrawal import State,evaluate,bookkeeping


class WesternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[1]/'mod/db/events/aubm_v4'/MODULE
        cls.source={MODULE:p.read_bytes().decode('latin1')}
        cls.output,cls.records=transform(cls.source)
        cls.before={int(e.get('id')):e for e in parse(cls.source[MODULE]).all('event')}
        cls.events={int(e.get('id')):e for e in parse(cls.output[MODULE]).all('event')}

    def state(self,provinces,flags=()):
        return State(flags=set(flags),wars={frozenset(('IND','ENG'))},controllers={p:'IND' for p in provinces})

    def test_exact_ids_idempotent_and_no_peace_added(self):
        self.assertEqual(EDITED_IDS,set(self.records))
        self.assertEqual(set(self.before),set(self.events))
        self.assertEqual(self.output,transform(self.output)[0])
        for eid in EDITED_IDS:
            old=[(c.get('type'),c.get('which'),c.get('value')) for a in aa(self.before[eid]) for c in a.all('command')]
            new=[(c.get('type'),c.get('which'),c.get('value')) for a in aa(self.events[eid]) for c in a.all('command')]
            self.assertEqual(old,new)

    def test_western_limited_needs_all_three_and_major_adds_cape(self):
        for absent in (1053,900,842):
            self.assertFalse(evaluate(parse(LIMITED),self.state({1053,900,842}-{absent})))
        s=self.state({1053,900,842})
        self.assertTrue(evaluate(parse(LIMITED),s));self.assertFalse(evaluate(parse(MAJOR),s))
        s.controllers[880]='IND';self.assertTrue(evaluate(parse(MAJOR),s))
        s.controllers.pop(880);s.controllers[29]='IND'
        self.assertFalse(evaluate(parse(MAJOR),s))

    def test_old_eastern_path_and_major_pairs_retained(self):
        for hinge in (1053,900,842):
            self.assertTrue(evaluate(parse(LIMITED),self.state({1432,1438,hinge})))
        for pair in ((1053,900),(1053,880),(1053,29),(900,880),(900,29),(880,29)):
            self.assertTrue(evaluate(parse(MAJOR),self.state({1432,1438,842,*pair})))
        self.assertFalse(evaluate(parse(MAJOR),self.state({1432,1438,842,880})))

    def test_current_limited_map_required_for_major_not_only_historical_flag(self):
        s=self.state({900,880,1053},{'ind_aubm_britain_limited_victory'})
        self.assertFalse(evaluate(self.events[9282131].get('trigger'),s))
        s.controllers[842]='IND';self.assertTrue(evaluate(self.events[9282131].get('trigger'),s))

    def test_reward_one_time_gates_and_war_retained(self):
        s=self.state({1053,900,842},{'ind_aubm_campaign_britain_active'})
        self.assertTrue(evaluate(self.events[9282130].get('trigger'),s))
        bookkeeping(aa(self.events[9282130])[0],s)
        self.assertFalse(evaluate(self.events[9282130].get('trigger'),s))
        s.controllers[880]='IND';self.assertTrue(evaluate(self.events[9282131].get('trigger'),s))
        bookkeeping(aa(self.events[9282131])[0],s)
        self.assertFalse(evaluate(self.events[9282131].get('trigger'),s))
        s.flags.discard('ind_aubm_britain_major_victory');s.wars.clear()
        self.assertFalse(evaluate(self.events[9282131].get('trigger'),s))

    def test_western_loss_and_recovery_no_eastern_dependency_or_reward_reset(self):
        history={'ind_aubm_britain_limited_victory','ind_aubm_britain_major_victory'}
        s=self.state({1053,900,842},history|{CURRENT})
        self.assertFalse(evaluate(self.events[9282141].get('trigger'),s))
        s.controllers.pop(842)
        self.assertTrue(evaluate(self.events[9282141].get('trigger'),s))
        bookkeeping(aa(self.events[9282141])[0],s)
        self.assertNotIn(CURRENT,s.flags);self.assertIn(SUSPENDED,s.flags)
        self.assertTrue(history<=s.flags)
        self.assertFalse(evaluate(self.events[9282142].get('trigger'),s))
        s.controllers[842]='IND';self.assertTrue(evaluate(self.events[9282142].get('trigger'),s))
        bookkeeping(aa(self.events[9282142])[0],s)
        self.assertIn(CURRENT,s.flags);self.assertNotIn(SUSPENDED,s.flags)
        self.assertTrue(history<=s.flags)

    def test_other_opponent_recovery_cannot_restore_britain_without_its_map(self):
        s=self.state({377,338},{'ind_aubm_germany_suspended','ind_aubm_britain_limited_victory'})
        self.assertTrue(evaluate(self.events[9282142].get('trigger'),s))
        bookkeeping(aa(self.events[9282142])[0],s)
        self.assertNotIn(CURRENT,s.flags)

    def test_switching_between_qualifying_routes_keeps_leverage(self):
        s=self.state({1432,1438,900},{CURRENT,'ind_aubm_britain_limited_victory'})
        self.assertFalse(evaluate(self.events[9282141].get('trigger'),s))
        s.controllers={p:'IND' for p in (1053,900,842)}
        self.assertFalse(evaluate(self.events[9282141].get('trigger'),s))

    def test_staged_build_action_guards_admit_western_only(self):
        p=Path(__file__).resolve().parents[1]/'build/redesign/staged-authored/db/events/aubm_v4'/MODULE
        if not p.exists():self.skipTest('No staged build artifact available')
        output,_=transform({MODULE:p.read_bytes().decode('latin1')})
        events={int(e.get('id')):e for e in parse(output[MODULE]).all('event')}
        s=self.state({1053,900,842},{'ind_aubm_campaign_britain_active'})
        limited=events[9282130]
        self.assertTrue(evaluate(limited.get('trigger'),s))
        self.assertTrue(evaluate(aa(limited)[0].get('trigger'),s))
        bookkeeping(aa(limited)[0],s)
        s.controllers[880]='IND'
        major=events[9282131]
        self.assertTrue(evaluate(major.get('trigger'),s))
        self.assertTrue(evaluate(aa(major)[0].get('trigger'),s))


if __name__=='__main__':unittest.main()
