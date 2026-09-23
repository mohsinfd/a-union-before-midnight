"""Executable LIBERATOR2 state contracts, not a Darkest Hour engine emulator."""
import copy
import unittest
from pathlib import Path

import generate_aubm_liberator as lib
import aubm_liberator_v2 as v2
from aubm_menu_safety import event_spans
from test_aubm_liberator import State,pair,parse,get,values,evaluate,execute


class LongWarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events={int(get(e,'id')):e for k,e in parse(lib.render()) if k=='event'}
        cls.legacy={int(get(e,'id')):e for k,e in parse(lib.OUTPUT.read_text(encoding='cp1252')) if k=='event'}

    def gate(self,eid,s): return evaluate(get(self.events[eid],'trigger',[]),s)
    def action_gate(self,eid,letter,s,legacy=False):
        return evaluate(get(get((self.legacy if legacy else self.events)[eid],'action_'+letter),'trigger',[]),s)
    def choose(self,eid,letter,s):
        done=execute(get(self.events[eid],'action_'+letter),s)
        if done and get(self.events[eid],'save_date')=='yes':s.event_dates[eid]=s.day
        return done
    def china(self):
        s=State();s.exists.add('U87');s.flags.add(lib.P+'japan_war')
        s.puppets['U87']='JAP';s.alliances.add(pair(('U87','JAP')))
        s.wars|={pair(('IND','JAP')),pair(('IND','U87'))}
        for p in (1337,1317,1299):s.owned[p]='U87'
        for p in (1337,1338,1317,1299):s.control[p]='IND'
        s.owned[1338]='JAP';return s
    def soviet(self):
        s=State();s.flags|={lib.P+'soviet_war','ind_aubm_soviet_current'}
        s.wars.add(pair(('IND','SOV')))
        for p in (713,1103,706,663,1151):s.control[p]='IND'
        for tag in ('TRK','UZB'):
            for p in v2.CA_MIN[tag]:s.owned[p]='SOV';s.control[p]='IND'
        return s
    def finish_hold(self,base,days,s):
        self.assertTrue(self.gate(base,s));self.choose(base,'a',s)
        s.day+=days-1;self.assertFalse(self.gate(base+2,s))
        s.day+=1;self.assertTrue(self.gate(base+2,s));self.choose(base+2,'a',s)

    def test_four_city_offer_waits_sixty_days(self):
        s=self.china();self.assertFalse(self.gate(9289903,s))
        self.finish_hold(9289900,60,s);self.assertTrue(self.gate(9289903,s))
        self.choose(9289903,'a',s);self.assertFalse(self.gate(9289903,s))
        self.assertFalse(self.action_gate(9289850,'a',s))
        self.assertEqual(s.resources['money'],4650)

    def test_hold_loss_restarts_clock_not_last_day_recovery(self):
        for base,days,s,province in ((9289900,60,self.china(),1299),(9289910,90,self.soviet(),663)):
            self.choose(base,'a',s);s.day=days-1;s.control[province]='JAP'
            self.assertTrue(self.gate(base+1,s));self.choose(base+1,'a',s)
            s.day=days;s.control[province]='IND';self.choose(base,'a',s)
            self.assertFalse(self.gate(base+2,s))
            s.day+=days;self.assertTrue(self.gate(base+2,s))

    def test_soviet_frontier_is_not_republic_victory(self):
        s=self.soviet();s.control.pop(663)
        self.assertFalse(self.gate(9289910,s))
        self.assertFalse(self.action_gate(9282036,'a',s,True))
        self.assertFalse(self.action_gate(9282036,'b',s,True))
        self.assertTrue(self.action_gate(9282036,'c',s,True))

    def test_soviet_needs_every_hub_and_one_interior_city(self):
        for missing in (713,1103,706,663,1151):
            s=self.soviet();s.control.pop(missing)
            self.assertFalse(self.gate(9289910,s),missing)
        for alternative in (1138,572):
            s=self.soviet();s.control.pop(1151);s.control[alternative]='IND'
            self.assertTrue(self.gate(9289910,s),alternative)

    def test_two_complete_republics_not_two_capitals(self):
        for kind in ('owned','control'):
            s=self.soviet();getattr(s,kind)[1097]='GER'
            self.assertFalse(self.gate(9289910,s),kind)
        s=self.soviet();s.exists.add('TRK');self.assertFalse(self.gate(9289910,s))

    def test_soviet_ninety_day_ready_opens_deep_terms(self):
        s=self.soviet();self.finish_hold(9289910,90,s)
        self.assertTrue(self.action_gate(9282036,'b',s,True))
        self.assertTrue(execute(get(self.legacy[9282036],'action_b'),s))
        self.assertIn((9289914,'SOV',3),s.queued)
        self.assertNotIn((9282038,'SOV',3),s.queued)
        self.assertTrue(self.action_gate(9289914,'a',s))
        self.choose(9289914,'a',s)
        self.assertIn((9282046,'SOV',1),s.queued)
        self.assertIn((9282043,'IND',3),s.queued)

    def test_legacy_other_route_preserves_its_original_terms(self):
        s=self.soviet();s.flags.discard(lib.P+'enabled');s.control.pop(663)
        self.assertTrue(self.action_gate(9282036,'b',s,True))
        execute(get(self.legacy[9282036],'action_b'),s)
        self.assertIn((9282038,'SOV',3),s.queued)
        self.assertNotIn((9289914,'SOV',3),s.queued)

    def test_stale_soviet_response_and_transfer_do_not_mutate_ownership(self):
        s=self.soviet();self.finish_hold(9289910,90,s)
        execute(get(self.legacy[9282036],'action_b'),s)
        self.choose(9289914,'a',s);s.control[663]='SOV'
        self.assertFalse(self.action_gate(9289914,'a',s))
        self.assertTrue(self.action_gate(9289914,'c',s))
        self.assertFalse(self.action_gate(9282046,'a',s,True))

    def test_release_callbacks_combine_ownership_and_authority_in_one_gate(self):
        for eid in (9282040,9282043):
            a=get(self.legacy[eid],'action_a')
            self.assertEqual(len(values(a,'trigger')),1)
            s=self.soviet();s.flags|={lib.P+'sov_deep_accepted',lib.P+'sov_deep_transferred',
                'ind_aubm_local_armistice_outstanding','ind_aubm_local_armistice_target_sov'}
            for p in v2.CA_MIN['TRK']:s.owned[p]='IND'
            self.assertTrue(self.action_gate(eid,'a',s,True))
            s.flags.discard(lib.P+'sov_deep_transferred')
            self.assertFalse(self.action_gate(eid,'a',s,True))
            self.assertTrue(self.action_gate(eid,'b',s,True))

    def test_stale_foreign_fallback_is_exact_opposite_of_valid_roll(self):
        s=self.soviet();self.finish_hold(9289910,90,s)
        execute(get(self.legacy[9282036],'action_b'),s)
        for eid in (9282037,9282038):
            for state in (s,State()):
                live=self.action_gate(eid,'a',state,True)
                self.assertEqual(self.action_gate(eid,'b',state,True),live)
                self.assertEqual(self.action_gate(eid,'c',state,True),live)
                self.assertEqual(self.action_gate(eid,'d',state,True),not live)

    def test_chinese_ratification_requires_real_peace_and_consent(self):
        s=State();s.exists.add('U87');s.flags|={lib.P+'china_protection_consent',lib.P+'china_break'}
        for p in lib.CHINA_RETURN:s.owned[p]='U87';s.control[p]='U87'
        self.assertTrue(self.gate(9289905,s))
        s.wars.add(pair(('U87','USA')));self.assertFalse(self.gate(9289905,s))
        s.wars.clear();s.puppets['U87']='JAP';self.assertFalse(self.gate(9289905,s))
        s.puppets.clear();s.flags.discard(lib.P+'china_protection_consent');self.assertFalse(self.gate(9289905,s))

    def test_no_sovereign_reward_in_protectorate_ratification_gap(self):
        s=State();s.exists.add('U87');s.flags|={lib.P+'china_break',lib.P+'china_protection_consent'}
        for p in lib.CHINA_RETURN:s.owned[p]='U87';s.control[p]='U87'
        self.assertFalse(self.gate(9289852,s))
        self.assertTrue(self.choose(9289905,'b',s));self.assertTrue(self.gate(9289852,s))

    def test_stale_china_offer_refuses_without_changing_japan_war(self):
        s=self.china();self.finish_hold(9289900,60,s);self.choose(9289903,'a',s)
        before=copy.deepcopy(s.wars);s.control[1299]='JAP'
        self.assertFalse(self.action_gate(9289904,'a',s));self.choose(9289904,'c',s)
        self.assertEqual(s.wars,before)

    def test_protectorate_review_from_actual_relationship_not_menu_open(self):
        s=State();s.exists.add('U87');s.flags.add(lib.P+'china_protectorate')
        self.assertFalse(self.gate(9289940,s))
        s.puppets['U87']='IND';self.choose(9289940,'a',s)
        self.assertFalse(self.gate(9289941,s));s.day=729;self.assertFalse(self.gate(9289941,s))
        s.day=730;self.assertTrue(self.gate(9289941,s))
        s.wars.add(pair(('IND','JAP')));self.assertFalse(self.gate(9289941,s))
        s.wars.clear();s.wars.add(pair(('U87','SOV')));self.assertFalse(self.gate(9289941,s))

    def test_optional_independence_no_peace_or_old_reward_commands(self):
        for eid in range(9289941,9289952,2):
            a=get(self.events[eid],'action_a')
            self.assertEqual({get(c,'type') for c in values(a,'command')},{'end_mastery','guarantee','setflag'})

    def settled_ca(self):
        s=State();s.flags|={lib.P+'sov_deep_accepted',lib.P+'soviet_war','ind_aubm_settlement_central_asia_protected'}
        for t in ('TRK','UZB'):
            s.exists.add(t);s.puppets[t]='IND'
            for p in v2.CA_MIN[t]:s.owned[p]=t;s.control[p]=t
        return s

    def test_soviet_reward_requires_two_real_complete_client_states(self):
        s=self.settled_ca();self.assertTrue(self.gate(9289915,s))
        s.puppets['TRK']='SOV';self.assertFalse(self.gate(9289915,s))
        s.puppets['TRK']='IND';s.control[1097]='SOV';self.assertFalse(self.gate(9289915,s))

    def test_soviet_programme_waits_for_relevant_peace_not_global_peace(self):
        s=self.settled_ca();s.wars.add(pair(('IND','JAP')))
        self.choose(9289915,'a',s);self.assertTrue(self.gate(9289916,s))
        s.wars.add(pair(('IND','SOV')));self.assertFalse(self.gate(9289916,s))

    def test_protected_branch_qualifies_for_existing_reconstruction(self):
        s=self.settled_ca();self.assertTrue(self.gate(9289870,s))
        s.flags.remove('ind_aubm_settlement_central_asia_protected');self.assertFalse(self.gate(9289870,s))

    def test_major_investments_are_paid_mutually_exclusive_once(self):
        for eid in (9289916,9289923):
            s=self.settled_ca();s.flags|={lib.P+'sov_deep_settled',lib.P+'jap_hold_earned','ind_aubm_armistice_japan'}
            for p in (1459,1517,1447):s.owned[p]='IND';s.control[p]='IND'
            self.assertTrue(self.action_gate(eid,'b',s));self.assertTrue(self.choose(eid,'a',s))
            self.assertFalse(self.action_gate(eid,'b',s));self.assertFalse(self.choose(eid,'a',s))
            self.assertEqual(s.resources['money'],4500);self.assertEqual(s.resources['supplies'],8000)

    def test_industrial_investments_use_correct_guarded_indian_cities(self):
        for eid in (9289916,9289923):
            commands=[c for c in values(get(self.events[eid],'action_b'),'command') if get(c,'type')=='construct']
            self.assertEqual({int(get(c,'where')) for c in commands},{1459,1517,1447})
            self.assertTrue(all(get(c,'trigger') and get(c,'value')=='2' for c in commands))

    def test_japan_is_optional_but_home_island_reward_requires_full_result(self):
        s=State();s.flags.add(lib.P+'jap_hold_earned')
        self.assertFalse(self.gate(9289923,s));s.flags.add('ind_aubm_major_armistice_limited')
        self.assertFalse(self.gate(9289923,s));s.flags.add('ind_aubm_armistice_japan')
        self.assertTrue(self.gate(9289923,s));s.wars.add(pair(('IND','JAP')))
        self.assertFalse(self.gate(9289923,s))

    def test_japanese_hold_survives_actual_peace_without_repaying_conquest(self):
        s=State();s.wars.add(pair(('IND','JAP')))
        for p in (1552,1553,1554):s.control[p]='IND'
        self.finish_hold(9289920,60,s);s.wars.clear();self.choose(9289921,'a',s)
        self.assertIn(lib.P+'jap_hold_earned',s.flags);self.assertFalse(self.gate(9289920,s))

    def test_independent_missions_need_neither_suez_nor_major_wars(self):
        s=State();s.exists.add('TIB');s.puppets['TIB']='IND';s.owned[1289]='TIB';s.control[1289]='TIB'
        self.finish_hold(9289930,90,s);self.assertTrue(self.choose(9289933,'a',s))
        self.assertFalse(self.choose(9289933,'a',s))
        s=State()
        for p in (1085,2171):s.owned[p]='IND';s.control[p]='IND'
        self.finish_hold(9289934,90,s);self.assertTrue(self.choose(9289937,'a',s))

    def test_tibet_is_not_created_or_puppeted_by_chinese_victory(self):
        s=State();s.flags.add(lib.P+'china_protectorate');self.assertFalse(self.gate(9289930,s))
        for eid in (9289904,9289905):
            self.assertNotIn('TIB',str(self.events[eid]))

    def test_counteroffers_have_real_war_preserving_rejection(self):
        major_text=(lib.ROOT/'mod/db/events/aubm_v4/45_enemy_campaigns.txt').read_text(encoding='cp1252')
        major=next(parse(major_text[s:e])[0][1] for s,e,i in event_spans(major_text) if i==9282150)
        for event_node in (self.legacy[9282044],major):
            reject=get(event_node,'action_b');self.assertIsNotNone(reject)
            kinds={get(c,'type') for c in values(reject,'command')}
            self.assertEqual(kinds,{'clrflag','setflag','event'})
            self.assertFalse(any(get(c,'which') in ('9282059','9282160') for c in values(reject,'command')))

    def test_no_duplicate_actions_or_triggers_in_modified_events(self):
        for eid in v2.LEGACY_IDS | set(self.events):
            e=self.legacy[eid]
            for letter in 'abcd':
                self.assertLessEqual(len(values(e,'action_'+letter)),1,eid)
                self.assertLessEqual(len(values(get(e,'action_'+letter,[]),'trigger')),1,eid)

    def test_only_enumerated_legacy_blocks_change_and_rebuild_is_stable(self):
        fixture=(Path(__file__).parent/'fixtures/liberator2_legacy43.txt').read_bytes()
        edited=v2.patch_legacy(fixture)
        self.assertEqual(edited,v2.patch_legacy(edited))
        self.assertEqual({i for _,_,i in event_spans(edited.decode('cp1252'))},v2.LEGACY_IDS)
        seed=b'# keep this text\r\nevent = { id = 7 random = no }\r\n'+fixture
        self.assertTrue(v2.patch_legacy(seed).startswith(seed.split(fixture)[0]))


if __name__=='__main__':unittest.main()
