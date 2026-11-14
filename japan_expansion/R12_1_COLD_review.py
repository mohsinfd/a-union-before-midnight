"""Independent installed-file and shipping checks; no engine or save changes."""
import copy,json,unittest
from pathlib import Path
import build
import island_shipping as shipping
import campaign_balance
from UNIQUE_UNIT_EVENTS_review import ColdWorld,DeferredWorld,ENTRIES,snapshot


class RevisionReview(unittest.TestCase):
    def test_actual_installed_events_match_every_final_source_command(self):
        modules={e.module for e in build.EVENTS}
        installed={}
        for module in modules:
            p=build.TARGET/'db/events/japan_rising'/(module+'.txt')
            for e in build.getall(build.parse(build.read(p)),'event'):
                key=build.get(e,'id');self.assertNotIn(key,installed);installed[key]=e
        self.assertEqual(len(installed),len(build.EVENTS))
        for e in build.EVENTS:
            self.assertEqual(installed[str(e.id)],build.get(build.parse(build.compiled_event(e)),'event'),e.key)

    def test_all_previous_R12_ids_preserved(self):
        previous=json.loads((build.HERE/'backups/before_R12_1_activation/events.json').read_text())
        current={e.key:e.id for e in build.EVENTS}
        self.assertTrue(all(current[e['key']]==e['id'] for e in previous))

    def award(self,key):
        event=next(e for e in build.EVENTS if e.key==key)
        return [build.parse(build.resolve(c)) for c in event.actions[0].commands
                if build.get(build.parse(c),'type') in {'transport_pool','escort_pool'} or
                build.get(build.parse(c),'which')=='JX_'+shipping.DONE]

    def test_shipping_first_callup_any_order_pays_exactly_once(self):
        for first in shipping.RECIPIENTS:
            w=ColdWorld(1939);before=w.resources['JAP'].copy()
            order=[first]+list(shipping.RECIPIENTS)*2
            for key in order:
                commands=self.award(key);self.assertEqual(len(commands),3)
                for node in commands:w.command(node,'JAP')
            self.assertEqual(w.properties['JAP','transport_pool','-1',None],180)
            self.assertEqual(w.properties['JAP','escort_pool','-1',None],90)
            self.assertEqual(w.resources['JAP'],before)
            self.assertTrue(w.flags['JX_'+shipping.DONE])

    def test_shipping_does_not_pay_foreign_AI_or_puppet_countries(self):
        for mode in ('foreign','AI','puppet'):
            w=ColdWorld(1939)
            if mode=='AI':w.humans=set()
            if mode=='puppet':w.masters['JAP']='USA'
            for node in self.award(shipping.RECIPIENTS[0]):w.command(node,'USA' if mode=='foreign' else 'JAP')
            self.assertFalse(w.properties)
            self.assertFalse(w.flags.get('JX_'+shipping.DONE))

    def test_paid_merchant_choices_keep_cost_and_delay_with_larger_real_awards(self):
        by={e.key:e for e in build.EVENTS}
        for index,transports,escorts in ((0,160,40),(1,100,80)):
            w=ColdWorld(1933);before=w.resources['JAP'].copy()
            self.assertTrue(w.action('merchant_prewar',index));w.advance(151)
            self.assertEqual(w.resources['JAP']['money'],before['money']-120)
            self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-600)
            self.assertEqual(w.properties['JAP','transport_pool','-1',None],transports)
            self.assertEqual(w.properties['JAP','escort_pool','-1',None],escorts)
            self.assertTrue(w.flags['JX_merchant_prewar_DONE'])
        self.assertIn('160 convoy transports and 40 convoy escorts',by['merchant_prewar'].desc)

    def test_all_31_local_garrison_templates_remain_at_quarter_strength(self):
        country=build.get(build.parse(build.read(build.TARGET/'scenarios/1933/japan.inc')),'country')
        templates=[d for d in build.getall(country,'landdivision')
                   if build.get(build.get(d,'id',[]),'type')==str(campaign_balance.ISLAND_TYPE)]
        self.assertEqual(len(templates),31)
        for d in templates:
            self.assertEqual(build.get(d,'max_strength'),'25')
            self.assertEqual(build.get(d,'strength'),'25')
            self.assertEqual(build.get(d,'dormant'),'yes')

    def test_actual_installed_deferred_helpers_are_transactional(self):
        root=build.parse(build.read(build.TARGET/'db/events/japan_rising/unique_unit_introductions.txt'))
        installed={build.get(e,'id'):e for e in build.getall(root,'event')}
        by={e.key:e for e in build.EVENTS}
        for unit,info in ENTRIES.items():
            w=DeferredWorld(info['year']);parent=installed[str(by['unique_intro_'+unit].id)]
            choices=[a for a in build.getall(parent,'action') if w.test(build.get(a,'trigger',[]),'JAP')]
            self.assertEqual(len(choices),1)
            for c in build.getall(choices[0],'command'):w.command(c,'JAP')
            self.assertFalse(w.brigades or w.deployed_units)
            key=w.human_waiting.pop(0);helper=installed[str(by[key].id)]
            choices=[a for a in build.getall(helper,'action') if w.test(build.get(a,'trigger',[]),'JAP')]
            self.assertEqual(len(choices),1)
            commands=build.getall(choices[0],'command')
            for c in commands:w.command(c,'JAP')
            self.assertIn(('JAP',unit),w.activated)
            after=snapshot(w)
            for c in commands:w.command(c,'JAP')
            self.assertEqual(snapshot(w),after)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RevisionReview))
    report=dict(version=build.VERSION,passed=result.wasSuccessful(),tests=result.testsRun,
                failures=len(result.failures),errors=len(result.errors),game_launched=False,
                scope='Actual installed events and retained garrisons; deferred human acknowledgements, cached action replay and finite shipping; no engine playtest.')
    (build.HERE/'R12_1_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
