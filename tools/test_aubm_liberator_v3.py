"""State-level LIBERATOR3 contracts; never presented as engine playtests."""
import copy
import unittest

import aubm_liberator_v3 as v3
import generate_aubm_liberator as lib
from test_aubm_liberator import State, pair, parse, get, values, evaluate, execute, is_action


class Liberator3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events={int(get(e,'id')):e for k,e in parse(lib.render()) if k=='event'}

    def gate(self,eid,s):return evaluate(get(self.events[eid],'trigger',[]),s)
    def action(self,eid,letter):return get(self.events[eid],'action_'+letter)
    def choose(self,eid,letter,s):
        result=execute(self.action(eid,letter),s)
        if result and get(self.events[eid],'save_date')=='yes':s.event_dates[eid]=s.day
        return result

    def indo(self):
        s=State();s.exists.add('U03');s.puppets['U03']='JAP'
        s.alliances.add(pair(('U03','JAP')))
        s.wars|={pair(('IND','JAP')),pair(('IND','U03'))}
        for p in v3.INDO_PROVINCES:s.owned[p]='U03';s.control[p]='IND'
        return s

    def witness(self,tag='USA'):
        return 9295000+v3.TAGS.index(tag)*2

    def test_country_watchers_cover_real_tags_not_sentinels(self):
        self.assertNotIn('END',v3.TAGS);self.assertNotIn('REB',v3.TAGS)
        for tag in ('USA','ENG','SOV','CHI','U05','U03','PHI','AST','TIB','AFG'):
            self.assertIn(tag,v3.TAGS)
        self.assertEqual(len(v3.TAGS),len(set(v3.TAGS)))
        self.assertLess(9295000+len(v3.TAGS)*2,9296000)

    def test_existing_war_is_not_new_aggression(self):
        s=State();s.wars.add(pair(('JAP','USA')));s.attacked_by.add('JAP')
        self.assertFalse(self.gate(self.witness(),s))
        self.assertFalse(self.gate(self.witness()+1,s))
        self.assertFalse(self.gate(v3.BASE+4,s))

    def test_peace_then_japanese_attack_unlocks_optional_response(self):
        s=State();base=self.witness()
        self.assertTrue(self.gate(base,s));self.choose(base,'a',s)
        s.wars.add(pair(('JAP','USA')));s.attacked_by.add('JAP')
        self.assertTrue(self.gate(base+1,s));self.choose(base+1,'a',s)
        self.assertTrue(self.gate(v3.BASE+4,s))
        self.assertNotIn(pair(('IND','JAP')),s.wars)

    def test_victim_declaring_on_japan_does_not_unlock_response(self):
        s=State();self.choose(self.witness(),'a',s)
        s.wars.add(pair(('JAP','USA')))
        self.assertFalse(self.gate(self.witness()+1,s))

    def test_witnessed_war_ending_closes_response_and_rearms(self):
        s=State();base=self.witness();self.choose(base,'a',s)
        s.wars.add(pair(('JAP','USA')));s.attacked_by.add('JAP');self.choose(base+1,'a',s)
        s.wars.clear();self.assertFalse(self.gate(v3.BASE+4,s))
        self.assertTrue(self.gate(base,s));self.choose(base,'a',s)
        self.assertNotIn(lib.P+'aggression_live_usa',s.flags)

    def test_intervention_allows_soviet_war_but_not_alliance_switch(self):
        s=State();s.flags.add(lib.P+'aggression_live_usa');s.wars|={pair(('JAP','USA')),pair(('IND','SOV'))}
        self.assertTrue(self.gate(v3.BASE+4,s))
        s.flags.add('ind_aubm_commitment_japan');self.assertFalse(self.gate(v3.BASE+4,s))
        s.flags.discard('ind_aubm_commitment_japan');s.alliances.add(pair(('IND','ENG')))
        self.assertFalse(self.gate(v3.BASE+4,s))

    def test_confirmation_rechecks_aggression_and_cancel_has_no_effect(self):
        s=State();before=copy.deepcopy(s)
        self.choose(v3.BASE+5,'a',s);self.assertEqual(s,before)
        self.assertFalse(evaluate(get(self.action(v3.BASE+5,'b'),'trigger'),s))
        s.flags.add(lib.P+'aggression_live_usa');s.wars.add(pair(('JAP','USA')))
        a=self.action(v3.BASE+5,'b');self.assertTrue(evaluate(get(a,'trigger'),s))
        cmds=values(a,'command')
        self.assertEqual([get(c,'value') for c in cmds if get(c,'type')=='dissent'],['2'])
        self.assertEqual([get(c,'which') for c in cmds if get(c,'type')=='war'],['JAP'])
        self.assertFalse(any(get(c,'type') in ('alliance','peace','leave_alliance') for c in cmds))

    def test_observers_never_declare_war_or_pay_rewards(self):
        for eid,e in self.events.items():
            if not 9295000<=eid<9296000:continue
            for c in values(get(e,'action_a'),'command'):
                self.assertIn(get(c,'type'),('setflag','clrflag'))

    def test_ai_cleanup_is_once_per_rupture_and_not_while_allied(self):
        s=State();s.ai=True;s.flags.add('ind_aubm_jp_rupture')
        self.assertTrue(self.gate(v3.BASE,s))
        s.alliances.add(pair(('IND','JAP')));self.assertFalse(self.gate(v3.BASE,s))
        s.alliances.clear();s.flags.add(lib.P+'japan_ai_released');self.assertFalse(self.gate(v3.BASE,s))
        s.flags.add('ind_aubm_jp_partnership');s.flags.discard('ind_aubm_jp_rupture')
        self.assertTrue(self.gate(v3.BASE+1,s))

    def test_ai_cleanup_also_works_outside_liberator_route(self):
        s=State();s.ai=True;s.flags={'ind_aubm_jp_rupture','ind_aubm_route_german'}
        self.assertTrue(self.gate(v3.BASE,s))

    def test_indochina_requires_all_five_provinces_and_thirty_days(self):
        for p in v3.INDO_PROVINCES:
            s=self.indo();s.control[p]='U03';self.assertFalse(self.gate(v3.BASE+10,s))
        s=self.indo();self.choose(v3.BASE+10,'a',s)
        s.day=29;self.assertFalse(self.gate(v3.BASE+12,s))
        s.day=30;self.assertTrue(self.gate(v3.BASE+12,s));self.choose(v3.BASE+12,'a',s)
        self.assertTrue(self.gate(v3.BASE+13,s))

    def test_friendly_indochina_uses_existing_branch_not_client_defeat(self):
        s=self.indo();s.puppets.clear();s.alliances.clear()
        self.assertFalse(self.gate(v3.BASE+10,s))

    def test_indochina_offer_and_response_reject_lost_leverage(self):
        s=self.indo();s.flags.add(lib.P+'indo_hold_ready')
        self.assertTrue(self.choose(v3.BASE+13,'b',s))
        self.assertEqual(s.resources['money'],4800);self.assertEqual(s.resources['supplies'],9250)
        s.control[1399]='U03'
        self.assertFalse(evaluate(get(self.action(v3.BASE+14,'a'),'trigger'),s))
        self.assertTrue(evaluate(get(self.action(v3.BASE+14,'c'),'trigger'),s))

    def test_generic_peace_pending_blocks_client_offer(self):
        s=self.indo();s.flags|={lib.P+'indo_hold_ready','ind_aubm_universal_armistice_outstanding'}
        self.assertFalse(self.gate(v3.BASE+13,s))

    def test_indochina_consent_uses_withdrawal_only_on_u03(self):
        e=self.events[v3.BASE+14];self.assertEqual(get(e,'country'),'U03')
        cmds=values(get(e,'action_a'),'command')
        self.assertEqual([get(c,'when') for c in cmds if get(c,'type')=='leave_alliance'],['1'])
        self.assertFalse(any(get(c,'type') in ('war','peace','inherit','secedeprovince','make_puppet') for c in cmds))

    def test_ratification_requires_real_indochinese_peace_and_hubs(self):
        s=self.indo();s.flags.add(lib.P+'indo_consent')
        self.assertFalse(self.gate(v3.BASE+15,s))
        s.puppets.clear();s.alliances.clear();s.wars.discard(pair(('IND','U03')))
        for p in v3.INDO_PROVINCES:s.control[p]='U03'
        self.assertTrue(self.gate(v3.BASE+15,s))
        s.wars.add(pair(('U03','USA')));self.assertFalse(self.gate(v3.BASE+15,s))

    def test_southern_partner_excludes_both_a_second_vietnam_slot_and_hostility(self):
        s=State();s.exists.add('U03');s.flags|={lib.P+'indo_settled',lib.P+'indo_sovereign'}
        for p in (1395,1399):s.owned[p]='U03';s.control[p]='U03'
        gate=get(parse('x = { '+v3.INDO_PARTNER+' }'),'x')
        self.assertTrue(evaluate(gate,s));s.wars.add(pair(('IND','U03')));self.assertFalse(evaluate(gate,s))
        # Both U03 and VIE alone cannot meet the two-distinct-regions condition.
        s.wars.clear();s.exists.add('VIE')
        s.flags|={lib.P+'indochina_reward',lib.P+'indochina_partner','ind_aubm_sea_land_indochina_liberated',lib.P+'japan_war','ind_aubm_sea_theatre_achieved'}
        self.assertFalse(self.gate(9289871,s))

    def test_progress_pages_are_effect_free_and_always_cancellable(self):
        for eid in (*range(v3.BASE+40,v3.BASE+48),*range(v3.BASE+49,v3.BASE+56)):
            e=self.events[eid]
            for k,a in e:
                if is_action(k):self.assertFalse(values(a,'command'),(eid,k))
            self.assertEqual(get(get(e,'action_a'),'name'),lib.CANCEL.name)

    def test_progress_navigation_is_immediate_and_has_no_automatic_loop(self):
        edges={}
        for eid,e in self.events.items():
            if not v3.BASE+30<=eid<=v3.BASE+55:continue
            edges[eid]=[]
            for k,a in e:
                if not is_action(k):continue
                for c in values(a,'command'):
                    self.assertEqual(get(c,'type'),'event');self.assertEqual(get(c,'when'),'0')
                    edges[eid].append(int(get(c,'which')))
            self.assertEqual(get(get(e,'action_a'),'name'),lib.CANCEL.name)
            self.assertFalse(values(get(e,'action_a'),'command'))
        def visit(eid,path):
            self.assertNotIn(eid,path)
            for target in edges.get(eid,[]):visit(target,path+[eid])
        visit(v3.BASE+30,[])

    def test_settlement_warnings_are_explicit(self):
        self.assertIn('removes access',get(self.events[9289850],'desc'))
        self.assertIn('forgo',get(get(self.events[9289905],'action_b'),'name'))
        self.assertIn('Limited peace alone',get(self.events[v3.BASE+47],'desc'))

    def test_native_action_grammar_and_complete_button_count(self):
        from validate_v4 import invalid_event_action_keys, event_action_blocks
        source=lib.render()
        self.assertFalse(invalid_event_action_keys(source))
        for eid,e in self.events.items():
            keys=[k for k,_ in e if is_action(k)]
            self.assertTrue(all(k in ('action','action_a','action_b','action_c','action_d') for k in keys),eid)
        # The exact first crashed event had five choices. Keep all five.
        board=self.events[v3.BASE+30]
        self.assertEqual(len([k for k,_ in board if is_action(k)]),5)
        self.assertEqual(len(values(board,'action')),1)
        self.assertEqual(get(values(board,'action')[0],'name'),'Indochina and the southern peace')
        seed=lib.event(1,'Grammar test','Info',[lib.action(str(n)) for n in range(12)])
        self.assertEqual(len(event_action_blocks(seed)),12)
        self.assertFalse(invalid_event_action_keys(seed))

    def test_validator_rejects_reported_crash_syntax(self):
        from validate_v4 import invalid_event_action_keys
        self.assertEqual(invalid_event_action_keys('event = { action_e = { name = "Crash" } }'),['action_e'])
        self.assertEqual(invalid_event_action_keys('event = { action_f = {} action_l = {} }'),['action_f','action_l'])
        self.assertFalse(invalid_event_action_keys('event = { action = {} action = {} action_d = {} }'))
        self.assertFalse(invalid_event_action_keys('# action_e = {}\nevent = { desc = "action_f = { }" action = {} }'))


if __name__=='__main__':unittest.main()
