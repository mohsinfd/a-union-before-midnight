import unittest
from pathlib import Path
from dh_save_spans import parse
from aubm_redesign_peace_scope import transform,actions,scope,gate
from test_aubm_redesign_withdrawal import State,evaluate


class PeaceScopeTests(unittest.TestCase):
    def test_minor_authority_and_current_master(self):
        p=parse(scope('U03','47_global_campaign_matrix.txt'))
        s=State();self.assertTrue(evaluate(p,s))
        s.masters['U03']='JAP';self.assertFalse(evaluate(p,s))
        s.masters.clear();s.alliances={frozenset(('IND','JAP'))};self.assertFalse(evaluate(p,s))
        s.leaders.add('IND');self.assertTrue(evaluate(p,s))
        s.countries.remove('U03');self.assertFalse(evaluate(p,s))

    def test_major_peace_is_coalition_scope_not_generic_minor(self):
        s=State(alliances={frozenset(('JAP','SIA'))})
        self.assertTrue(evaluate(parse(scope('JAP','45_enemy_campaigns.txt')),s))
        self.assertFalse(evaluate(parse(scope('JAP','47_global_campaign_matrix.txt')),s))

    def test_selector_still_checks_master_after_war_ends(self):
        source={'46_regional_campaigns.txt':'''event = { id = 9282260 country = IND desc = "Old" action_a = {
command = { trigger = { flag = ind_aubm_regional_armistice_target_sia war = { country = IND country = SIA } } type = peace which = SIA value = 1 }
command = { trigger = { flag = ind_aubm_regional_armistice_target_u03 war = { country = IND country = U03 } } type = peace which = U03 value = 1 }
command = { type = clrflag which = ind_v3_joined_japan }
command = { type = dissent value = -2 } } }'''}
        out,_=transform(source);e=parse(next(iter(out.values()))).get('event');a=e.get('action_a')
        s=State(flags={'ind_aubm_regional_armistice_target_sia'})
        self.assertTrue(evaluate(a.get('trigger'),s))
        s.masters['SIA']='JAP';self.assertFalse(evaluate(a.get('trigger'),s))
        s.masters.clear();s.flags.add('ind_aubm_regional_armistice_target_u03');self.assertFalse(evaluate(a.get('trigger'),s))
        self.assertFalse(any(c.get('which')=='ind_v3_joined_japan' for c in a.all('command')))
        self.assertEqual(['0','0'],[c.get('value') for c in a.all('command') if c.get('type')=='peace'])
        self.assertEqual(out,transform(out)[0])

    def test_authored_peace_corpus_complete_and_preserves_rewards(self):
        from build_aubm_redesign import load,ROOT
        source=load(ROOT/'mod');out,records=transform(source)
        self.assertEqual(478,sum(r[0]['peace_commands'] for r in records.values()))
        for t in out.values():
            for e in parse(t).all('event'):
                if int(e.get('id')) not in records:continue
                self.assertTrue(any(not a.all('command') for a in actions(e)))
                for a in actions(e):
                    for c in a.all('command'):
                        if c.get('type')=='peace':
                            self.assertEqual('0',c.get('value'))
                            self.assertIsNotNone(a.get('trigger'))
        self.assertTrue(all(not r[0]['engine_tested'] for r in records.values()))

    def test_absent_restoration_is_not_confused_with_stale_peace_reply(self):
        from build_aubm_redesign import load,ROOT
        source=load(ROOT/'mod');out,_=transform(source)
        evs={int(e.get('id')):e for t in out.values() for e in parse(t).all('event')}
        from aubm_redesign_peace_scope import RESTORATIONS,restore_scope
        for eid,tag in RESTORATIONS.items():
            e=evs[eid];a=e.get('action_a');c=next(c for c in a.all('command') if c.get('type')=='peace')
            s=State(alliances={frozenset(('IND','JAP'))});s.countries.discard(tag)
            self.assertTrue(evaluate(parse(restore_scope(eid,a,c,tag,'43_wartime_settlements.txt')),s))
            s.countries.add(tag);s.masters[tag]='JAP'
            self.assertFalse(evaluate(parse(restore_scope(eid,a,c,tag,'43_wartime_settlements.txt')),s))
        self.assertNotIn('every other Indian war',evs[9286400].get('desc'))
        self.assertNotIn('separate armistice',evs[9281353].get('action_b').get('name'))

    def test_conditional_multi_peace_always_checks_indian_sovereignty(self):
        source={'43_wartime_settlements.txt':'''event = { id = 9282024 country = IND desc = "Restore" action_a = {
command = { trigger = { exists = SAU war = { country = IND country = SAU } } type = peace which = SAU value = 1 }
command = { trigger = { exists = YEM war = { country = IND country = YEM } } type = peace which = YEM value = 1 }
command = { type = independence which = SAU } } }'''}
        out,_=transform(source);a=parse(next(iter(out.values()))).get('event').get('action_a')
        s=State(masters={'IND':'ENG'})
        self.assertFalse(evaluate(a.get('trigger'),s))


if __name__=='__main__':unittest.main()
