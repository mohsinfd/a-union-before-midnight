"""Regression scenarios for the R14 economic and opponent corrections."""
import json, unittest
import build as b
import endurance_economy as fuel
import unique_divisions as units
from US_CAMPAIGN_review import CampaignWorld
from simulate import BY_KEY

b.prepare_catalog()


class BalanceReview(unittest.TestCase):
    def test_existing_ids_and_unique_definitions(self):
        previous=json.loads((b.HERE/'R14_BASELINE_IDS.json').read_text(encoding='utf-8'))
        actual={e.key:e.id for e in b.EVENTS}
        self.assertEqual(len(actual),len(b.EVENTS))
        self.assertTrue(all(actual[k]==v for k,v in previous.items()))
        self.assertTrue(all(v>max(previous.values()) for k,v in actual.items() if k not in previous))

    def test_india_receives_the_land_ai_at_any_industrial_size(self):
        receiver=BY_KEY['relief_IND']
        commands=[b.parse(b.resolve(c)) for c in receiver.actions[0].commands]
        ai=[c for c in commands if b.get(c,'type')=='ai']
        self.assertEqual(len(ai),1)
        self.assertEqual(b.get(ai[0],'which'),'jx/partner_land.ai')
        self.assertIsNone(b.get(ai[0],'trigger'))
        self.assertTrue((b.TARGET/'ai/jx/partner_land.ai').exists())

    def test_matsu_retains_a_useful_bounded_discount_and_full_manpower(self):
        info=units.CLASSES['d_18'];native=b.getall(units._root('destroyer'),'model')
        for model,index in zip(units.models('d_18'),info['base_models']):
            parent=native[index]
            ratio=b.num(model,'cost')*b.num(model,'buildtime')/(b.num(parent,'cost')*b.num(parent,'buildtime'))
            self.assertTrue(.63<=ratio<=.65,ratio)
            self.assertEqual(b.num(model,'manpower'),b.num(parent,'manpower'))
            self.assertLess(b.num(model,'fuelconsumption'),b.num(parent,'fuelconsumption'))
            self.assertLess(b.num(model,'range'),b.num(parent,'range'))

    def test_large_fuel_order_has_real_recovery_and_exact_cancel_terms(self):
        event=BY_KEY['fuel_batch_delivery_1']
        for action in event.actions[:2]:
            commands=[b.parse(b.resolve(c)) for c in action.commands]
            cooldown=[c for c in commands if b.get(c,'type')=='event' and b.get(c,'which')==str(BY_KEY['fuel_batch_reset'].id)]
            self.assertEqual(len(cooldown),1)
            self.assertEqual(b.get(cooldown[0],'when'),'90')
        self.assertEqual(fuel.batch_cooldown(6000),45)
        self.assertEqual(fuel.batch_cooldown(1500),45)
        self.assertIn('90 days',BY_KEY['wartime_fuel_batch'].desc)
        self.assertIn('90 days',event.desc)

    def test_us_equipment_and_healing_are_exclusive_even_with_future_tech(self):
        from us_campaign_content import RESERVE_MODELS
        for year in (1941,1942,1945,1948,1950):
            model=max(m for y,t,m in RESERVE_MODELS if y<=year)
            w=CampaignWorld();w.year=year;w.flags['JX_USC_LANDING_DONE']=1
            w.country_tech['USA']={str(t) for _,t,_ in RESERVE_MODELS}
            w.dispatch('usc_coast_response')
            self.assertEqual(w.spawned,[('USA','infantry',model)]*6)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(BalanceReview)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    from endurance_economy import STAGES,BATCHES,batch_cooldown
    summary=dict(passed=result.wasSuccessful(),tests=result.testsRun,game_executed=False,
        large_batch_oil_per_day=BATCHES[1][3]/(45+batch_cooldown(BATCHES[1][3])),
        balanced_works_raw_oil_per_day=sum(stage[-1][0][3] for stage in STAGES),
        fuel_priority_works_raw_oil_per_day=sum(stage[-1][1][3] for stage in STAGES),
        note='Provincial works outputs are raw, before actual research/territorial/resource modifiers. Batch output is paid, repeatable only at low stocks, and consumes industrial coal. At the review benchmark of 165 oil/day, balanced domestic works plus the large emergency batch supply about134 raw/day, or about131 at 94% works efficiency. Fuel priority sacrifices minerals. Southern fields, imports, native conversion and captured stock remain material; these are illustrative flows, not a forecast of a particular fleet.')
    (b.HERE/'R14_BALANCE_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
