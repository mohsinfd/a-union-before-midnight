"""Offline R14 aftermath transaction, chronology and adverse-state checks."""
import unittest

import simulate as sim
import build
import r14_afterwar as content

content.apply()
build.IDS.update({e.key:e.id for e in build.EVENTS})
sim.BY_KEY.update({e.key:e for e in build.EVENTS})
sim.BY_ID.update({str(e.id):e for e in build.EVENTS})


class NativeWorld(sim.World):
    def test(self,node,actor):
        checks=[]
        for key,value in node:
            if key=='atwar' and value not in ('yes','no'):
                checks.append(any(value in pair for pair in self.wars))
            else:checks.append(super().test([(key,value)],actor))
        return all(checks)


class Afterwar(unittest.TestCase):
    def world(self):
        w=NativeWorld()
        w.wars=set()
        w.year=1947
        w.owned[1552]=w.controlled[1552]='JAP'
        w.buildings[1552,'infrastructure']=100
        return w

    def gate(self,w,key):
        e=sim.BY_KEY[key]
        return w.test(build.parse(build.resolve(e.gate+' '+e.ready)),e.country)

    def test_civilian_work_and_replays(self):
        w=self.world()
        start=dict(w.resources['JAP']); before=w.buildings[1552,'ic']
        self.assertTrue(self.gate(w,'civil_recovery'))
        self.assertTrue(w.action('civil_recovery',0))
        self.assertEqual(w.resources['JAP']['manpower'],start['manpower']-60)
        paid=dict(w.resources['JAP'])
        self.assertFalse(w.action('civil_recovery',0))
        self.assertEqual(dict(w.resources['JAP']),paid)
        # A cached window may retain its option after its eligibility changes.
        for command in sim.BY_KEY['civil_recovery'].actions[0].commands:
            w.command(build.parse(build.resolve(command)),'JAP')
        self.assertEqual(dict(w.resources['JAP']),paid)
        self.assertFalse(w.action('r14_civil_recovery_civilian',0))
        w.advance(360)
        self.assertEqual(w.buildings[1552,'ic'],before+6)
        self.assertEqual(w.resources['JAP']['manpower'],start['manpower'])
        self.assertFalse(w.action('r14_civil_recovery_civilian',0))

    def test_civilian_war_refund_and_no_negative_manpower(self):
        w=self.world();start=dict(w.resources['JAP'])
        w.action('civil_recovery',0);w.wars.add(frozenset(('JAP','USA')))
        w.advance(360)
        self.assertEqual(dict(w.resources['JAP']),start)
        self.assertFalse(w.action('r14_civil_recovery_civilian',1))
        w=self.world();w.resources['JAP']['manpower']=59
        self.assertFalse(w.action('civil_recovery',0))

    def test_readiness_has_finite_concrete_cost(self):
        w=self.world();start=dict(w.resources['JAP'])
        w.action('civil_recovery',1);w.wars.add(frozenset(('JAP','USA')))
        w.advance(180)
        self.assertEqual(w.resources['JAP']['manpower'],start['manpower']+80)
        self.assertEqual(w.resources['JAP']['money'],start['money']-400)
        self.assertEqual(w.resources['JAP']['supplies'],start['supplies']-2000)
        self.assertEqual(w.resources['JAP']['oil'],start['oil']-1000)
        self.assertFalse(w.action('r14_civil_recovery_reserves',0))

    def partner(self,tag,capital):
        w=self.world();w.countries.add(tag);w.masters[tag]='JAP';w.groups[tag]=w.groups['JAP']
        w.owned[capital]=w.controlled[capital]=tag;w.buildings[capital,'infrastructure']=100
        return w

    def test_both_partners_all_three_policies(self):
        for key,tag,capital in [('china_autonomy','U87',1337),('india_autonomy','IND',1459)]:
            for choice in range(3):
                with self.subTest(key=key,choice=choice):
                    w=self.partner(tag,capital);start=dict(w.resources['JAP']);before=w.buildings[capital,'ic'];mp=w.resources[tag]['manpower']
                    self.assertTrue(w.action(key,choice))
                    self.assertFalse(w.action(key,choice))
                    w.advance(2)
                    self.assertIn((tag,'JAP'),w.access)
                    if choice==0:self.assertNotIn(tag,w.masters)
                    else:self.assertEqual(w.masters[tag],'JAP')
                    w.advance(360)
                    self.assertEqual(w.resources['JAP']['money'],start['money']-250)
                    if choice==2:
                        self.assertEqual(w.resources[tag]['manpower'],mp+80)
                        self.assertEqual(w.resources['JAP']['supplies'],start['supplies']-5000)
                    else:self.assertEqual(w.buildings[capital,'ic'],before+4)

    def test_partner_disappears_or_loses_capital_refunds_once(self):
        for vanished in (False,True):
            w=self.partner('IND',1459);start=dict(w.resources['JAP'])
            w.action('india_autonomy',1)
            if vanished:w.countries.remove('IND')
            else:w.controlled[1459]='ENG'
            w.advance(362)
            self.assertEqual(dict(w.resources['JAP']),start)
            w.dispatch('r14_india_autonomy_civilian_refund')
            self.assertEqual(dict(w.resources['JAP']),start)

    def test_partner_civilian_aid_rejects_known_war_and_bad_factory_site(self):
        w=self.partner('IND',1459);w.wars.add(frozenset(('IND','SOV')))
        self.assertFalse(w.action('india_autonomy',1))
        w=self.partner('IND',1459);w.controlled[1459]='ENG'
        self.assertFalse(w.action('india_autonomy',1))
        w=self.world();w.controlled[1552]='USA'
        self.assertFalse(w.action('civil_recovery',0))

    def test_annexed_partner_after_acceptance_refunds_once_and_closes_recreated_receiver(self):
        for key,tag,capital in [('china_autonomy','U87',1337),('india_autonomy','IND',1459)]:
            for choice,mode,delay in [(0,'sovereign',360),(1,'civilian',360),(2,'military',180)]:
                with self.subTest(country=tag,mode=mode):
                    w=self.partner(tag,capital);start=dict(w.resources['JAP'])
                    w.action(key,choice);w.advance(2);w.countries.remove(tag)
                    watcher='r14_'+key+'_'+mode+'_government_lost'
                    self.assertFalse(w.action(watcher))
                    w.advance(delay)
                    self.assertTrue(w.action(watcher))
                    self.assertEqual(dict(w.resources['JAP']),start)
                    self.assertFalse(w.action(watcher))
                    w.countries.add(tag)
                    self.assertFalse(w.action('r14_'+key+'_'+mode+'_finish',0))

    def test_native_infrastructure_scales_and_factory_cap(self):
        for infra in (.31,.6,31,100):
            w=self.world();w.buildings[1552,'infrastructure']=infra
            self.assertTrue(w.action('civil_recovery',0))
        for infra in (.30,30):
            w=self.world();w.buildings[1552,'infrastructure']=infra
            self.assertFalse(w.action('civil_recovery',0))
        w=self.world();w.buildings[1552,'ic']=195
        self.assertFalse(w.action('civil_recovery',0))

    def america(self,returned=True):
        w=self.world();w.flags.update(JX_US_PEACE=1)
        w.flags['JX_US_RETURN_HAWAII' if returned else 'JX_US_KEEP_HAWAII']=1
        w.history[str(sim.BY_KEY['us_signed'].id)]=-360
        if not returned:w.owned[1734]=w.controlled[1734]='JAP'
        return w

    def test_us_waits_for_verified_peace_and_treaty_choice(self):
        w=self.america();self.assertTrue(self.gate(w,'r14_american_future'))
        w.history[str(sim.BY_KEY['us_signed'].id)]=0
        self.assertFalse(self.gate(w,'r14_american_future'))
        w=self.america();self.assertFalse(w.action('r14_american_future',1))
        w=self.america(False);self.assertFalse(w.action('r14_american_future',0))

    def test_us_commerce_and_refund(self):
        w=self.america();start=dict(w.resources['JAP']);us=dict(w.resources['USA'])
        w.action('r14_american_future',0);self.assertFalse(w.action('r14_american_future',0));w.advance(181)
        self.assertEqual(w.resources['JAP']['oil'],start['oil']+12000)
        self.assertEqual(w.resources['USA']['money'],us['money']+600)
        self.assertFalse(w.action('r14_us_export_receipt',0))
        w=self.america();start=dict(w.resources['JAP']);w.action('r14_american_future',0)
        w.wars.add(frozenset(('JAP','USA')));w.advance(181)
        self.assertEqual(dict(w.resources['JAP']),start)

    def test_brief_renewed_wars_cannot_be_erased_before_completion(self):
        w=self.america();start=dict(w.resources['JAP']);w.action('r14_american_future',0)
        w.wars.add(frozenset(('JAP','USA')));w.dispatch('r14_armistice_broken');w.wars.clear();w.advance(181)
        self.assertEqual(dict(w.resources['JAP']),start)
        self.assertFalse(self.gate(w,'r14_american_future'))
        w=self.world();start=dict(w.resources['JAP']);w.action('civil_recovery',0)
        w.wars.add(frozenset(('JAP','USA')));w.dispatch('r14_home_work_interrupted');w.wars.clear();w.advance(360)
        self.assertEqual(dict(w.resources['JAP']),start)

    def test_retained_hawaii_and_american_budget(self):
        w=self.america(False);before=w.buildings[1734,'coastal_fort'];us=dict(w.resources['USA'])
        w.action('r14_american_future',1);w.advance(181)
        self.assertEqual(w.buildings[1734,'coastal_fort'],before+3)
        self.assertEqual(w.resources['USA']['money'],us['money']-400)
        self.assertEqual(w.properties['USA','escort_pool',None,None],80)
        self.assertFalse(w.action('r14_us_pacific_rebuild',0))

    def test_declines_do_not_reward_or_repeat(self):
        w=self.world();start=dict(w.resources['JAP']);w.action('civil_recovery',2)
        self.assertEqual(dict(w.resources['JAP']),start);self.assertFalse(w.action('civil_recovery',0))
        w=self.america();start=dict(w.resources['JAP']);w.action('r14_american_future',2)
        self.assertEqual(dict(w.resources['JAP']),start);self.assertFalse(w.action('r14_american_future',0))

    def test_replaced_awards_have_no_stale_construction_metadata(self):
        import construction_safety
        self.assertFalse(any(row['event'].startswith(('civil_recovery','china_autonomy','india_autonomy'))
                             for row in construction_safety.REPORT))
        for key in ('civil_recovery','china_autonomy','india_autonomy','china_autonomy_grant','india_autonomy_grant'):
            self.assertEqual(construction_safety.effective_award(key),sim.BY_KEY[key].actions[0].commands)


if __name__=='__main__':unittest.main(verbosity=2)
