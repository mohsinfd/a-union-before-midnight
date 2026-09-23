"""Bhutan's shared lifecycle and simultaneous Himalayan offer regressions.

Only flags/resources are simulated. Inherit and native elapsed time are not.
"""
from pathlib import Path
import unittest
from dh_save_spans import parse, Node
from aubm_redesign_diplomacy import actions
from aubm_redesign_nepal import transform as nepal, BHUTAN
from aubm_redesign_bhutan import transform, NEW_EVENT_IDS
from test_aubm_redesign_nepal import State, evaluate, apply

P = 'ind_stage_bhutan_'
def state(flags=(), merged=False):
    return State(flags=set(flags), countries={'IND','ENG','NEP'} | (set() if merged else {'BHU'}),
        masters={'BHU':'ENG'}, owners={1456:'IND' if merged else 'BHU'},
        controllers={1456:'IND' if merged else 'BHU'})


class BhutanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'mod/db/events/india_v3/40_diplomacy.txt'
        cls.source = {str(path):path.read_bytes().decode('latin1')}
        cls.nepal = nepal(cls.source)[0]
        cls.output,cls.records = transform(cls.nepal)
        cls.ev = {int(e.get('id')):e for t in cls.output.values() for e in parse(t).all('event')}
    def a(self,eid,key='action_a'):return self.ev[eid].get(key)
    def allowed(self,eid,s,key='action_a'):return evaluate(self.a(eid,key).get('trigger'),s)

    def test_initial_odds_and_rewards_preserved(self):
        for eid,chance in ((9270411,60),(9270419,75),(9398211,80),(9270414,45),(9270424,60),(9398201,65)):
            self.assertEqual(str(chance),self.a(eid).get('ai_chance'))
            self.assertEqual(str(100-chance),self.a(eid,'action_b').get('ai_chance'))
        s=state({P+'merge_verifying'},True)
        effects=apply(self.a(9398213),s)
        self.assertIn(('manpowerpool',None,'5',None),effects)
        self.assertIn(('dissent',None,'-1',None),effects)

    def test_grand_offer_dispatches_independent_valid_kingdoms(self):
        s=state();a=self.a(9270410,'action_d');apply(a,s)
        self.assertTrue({P+'offer_pending','ind_stage_nepal_offer_pending'} <= s.flags)
        self.assertTrue(self.allowed(9270419,s));self.assertTrue(self.allowed(9270424,s))
        apply(self.a(9270419,'action_b'),s);apply(self.a(9270413),s)
        self.assertNotIn(P+'offer_pending',s.flags)
        self.assertIn('ind_stage_nepal_offer_pending',s.flags)
        self.assertTrue(self.allowed(9270424,s))

    def test_retry_cooldown_price_and_closure(self):
        s=state({P+'offer_pending'});apply(self.a(9270411,'action_b'),s);apply(self.a(9270413),s)
        self.assertFalse(self.allowed(9398210,s))
        apply(self.a(9398212),s)
        self.assertTrue(self.allowed(9398210,s))
        before=dict(s.resources);effects=apply(self.a(9398210),s)
        self.assertEqual(before['money']-650,s.resources['money'])
        self.assertEqual(before['supplies']-1000,s.resources['supplies'])
        self.assertIn(('dissent',None,'2',None),effects)
        self.assertFalse(self.allowed(9398210,s));self.assertTrue(self.allowed(9398211,s))
        self.assertFalse(self.a(9398210,'action_b').all('command'))

    def test_paid_dual_offer_requires_both_courts_available(self):
        for tag in ('NEP','BHU'):
            s=state();s.countries.remove(tag)
            self.assertFalse(self.allowed(9270410,s,'action_d'))
        for flag in (P+'offer_pending','ind_stage_nepal_offer_pending','ind_v3_bhutan_refused','ind_v3_nepal_refused'):
            self.assertFalse(self.allowed(9270410,state({flag}),'action_d'))
        self.assertTrue(self.allowed(9270410,state(),'action_d'))

    def test_stale_reply_and_hostility_pay_nothing(self):
        for failure in ('no_token','war','new_master'):
            s=state({P+'offer_pending',P+'accepted'})
            if failure=='no_token':s.flags.clear()
            elif failure=='war':s.wars.add(frozenset(('IND','JAP')))
            else:s.masters['BHU']='JAP'
            self.assertFalse(self.allowed(9270412,s),failure)
            available=[f.value for f in actions(self.ev[9270412]) if evaluate(f.value.get('trigger'),s)]
            self.assertEqual(1,len(available));effects=apply(available[0],s)
            self.assertFalse(any(k in ('inherit','manpowerpool','addcore') for k,*_ in effects))

    def test_merger_verified_before_1080_day_core(self):
        s=state({P+'offer_pending',P+'accepted'})
        effects=apply(self.a(9270412),s)
        self.assertIn(('inherit','BHU',None,None),effects)
        self.assertFalse(self.allowed(9398213,s))
        self.assertFalse(s.cores)
        s.countries.remove('BHU');s.owners[1456]=s.controllers[1456]='IND'
        self.assertTrue(self.allowed(9398213,s))
        effects=apply(self.a(9398213),s)
        self.assertIn(('event','9398214',None,'1080'),effects)
        self.assertFalse(s.cores)
        apply(self.a(9398214),s) # only after native delay; not a clock simulation
        self.assertEqual({1456},s.cores);self.assertFalse(self.allowed(9398214,s))

    def test_conquest_is_paid_five_years_not_instant_core(self):
        s=state(merged=True)
        self.assertTrue(self.allowed(9398216,s))
        effects=apply(self.a(9398216),s)
        self.assertIn(('event','9398214',None,'1800'),effects)
        self.assertEqual(8500,s.resources['money']);self.assertEqual(7500,s.resources['supplies'])
        self.assertIn(('dissent',None,'5',None),effects);self.assertFalse(s.cores)
        self.assertFalse(self.allowed(9398216,s))
        for eid in (9270412,9270413):
            self.assertFalse(any(c.get('type')=='addcore' for a in actions(self.ev[eid]) for c in a.value.all('command')))
        self.assertTrue(any(c.get('type')=='addclaim' and c.get('which')=='1456' for c in self.a(9270413,'action_c').all('command')))

    def test_lost_territory_defers_completion_without_repaying(self):
        s=state({P+'core_pending','ind_v3_bhutan_integrated'},True);s.controllers[1456]='JAP'
        apply(self.a(9398214,'action_b'),s);self.assertIn(P+'core_due',s.flags)
        self.assertFalse(self.allowed(9398215,s));s.controllers[1456]='IND'
        self.assertTrue(self.allowed(9398215,s));apply(self.a(9398215),s)
        self.assertEqual({1456},s.cores)

    def test_no_cross_country_generated_state_or_overflow(self):
        for eid in NEW_EVENT_IDS:
            ev=self.ev[eid]
            self.assertLessEqual(len(ev.get('desc')),340,eid)
            for af in actions(ev):self.assertLessEqual(len(af.value.get('name')),58,eid)
        text='\n'.join(t for t in self.output.values())
        for f in parse(text).fields:
            if f.key=='event' and int(f.value.get('id')) in NEW_EVENT_IDS:
                raw=text[f.start:f.end]
                for forbidden in ('NEP','Nepal','Kathmandu','1457','ind_stage_nepal_'):
                    self.assertNotIn(forbidden,raw)

    def test_nepal_events_remain_identical_and_whole_pass_idempotent(self):
        def idx(files):return {int(f.value.get('id')):t[f.start:f.end] for t in files.values() for f in parse(t).fields if f.key=='event'}
        before,after=idx(self.nepal),idx(self.output)
        for eid in (9270414,9270424,9270415,9270416,9270418,*range(9398200,9398207)):
            self.assertEqual(before[eid],after[eid])
        self.assertEqual(self.output,transform(self.output)[0])
        self.assertEqual(self.output,nepal(self.output)[0])
        self.assertEqual(set(NEW_EVENT_IDS),after.keys()-before.keys())

    def test_collisions_and_queue_format(self):
        with self.assertRaises(ValueError):transform(dict(self.nepal,collision='event = { id = 9398210 country = IND }'))
        for eid in (9398211,9398212,9398213,9398214):
            for key in ('trigger','date','offset','deathdate'):self.assertIsNone(self.ev[eid].get(key))


if __name__=='__main__':unittest.main()
