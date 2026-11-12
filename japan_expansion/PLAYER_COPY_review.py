"""Text-only editorial regression checks for the fully prepared catalogue."""
import json
from pathlib import Path
import unittest
import build
import player_copy

build.prepare_catalog()
player_copy.apply()
BY={e.key:e for e in build.EVENTS}


class PlayerCopyReview(unittest.TestCase):
    def test_no_development_terms_in_any_event_english(self):
        self.assertFalse(player_copy.REPORT['remaining'])
        for e in build.EVENTS:
            for value in (e.title,e.desc,*(a.name for a in e.actions)):
                self.assertIsNone(player_copy.BANNED.search(value),(e.key,value))

    def test_all_generated_english_and_ministers_are_clean(self):
        for line in build.localisation().splitlines():
            cells=line.split(';')
            if len(cells)>1:
                self.assertIsNone(player_copy.BANNED.search(cells[1]),cells[:2])
        import japan_personnel
        self.assertEqual(len(japan_personnel.PERSONALITIES),13)
        for trait,pid,office,name,desc,commands in japan_personnel.PERSONALITIES:
            self.assertIsNone(player_copy.BANNED.search(name+' '+desc))
            self.assertTrue(commands)

    def test_mechanics_fingerprint_and_idempotence(self):
        self.assertTrue(player_copy.REPORT['mechanics_unchanged'])
        before=player_copy._mechanics()
        copy_before=[(e.title,e.desc,[a.name for a in e.actions]) for e in build.EVENTS]
        player_copy.apply()
        self.assertEqual(before,player_copy._mechanics())
        self.assertEqual(copy_before,[(e.title,e.desc,[a.name for a in e.actions]) for e in build.EVENTS])

    def test_prewar_choice_bills_and_paid_worker_finish(self):
        import prewar_content
        for spec in prewar_content.programmes():
            text=BY[spec.key].desc
            self.assertIn(f'{spec.days} days',text)
            for choice in spec.choices:
                for kind,value in choice.costs.items():self.assertIn(f'{value:,} {kind}',text)
            for i in (0,1):
                text=BY[f'{spec.key}_finish_{i}'].desc
                self.assertNotIn('pay ',text.lower())
                self.assertNotIn('now;',text.lower())
        text=BY['prewar_rural_works_finish_0'].desc
        self.assertIn('25-manpower workforce was assigned when construction began',text)

    def test_selected_fuel_deliveries_do_not_request_payment_again(self):
        import endurance_economy
        for key,year,cash,stock,metal,days,mine,choices in endurance_economy.STAGES:
            for i,values in enumerate(choices):
                text=BY[f'{key}_finish_{i}'].desc
                self.assertIn(f'Tokyo: oil +{values[3]} daily',text)
                self.assertNotIn(f'Tokyo: oil +{choices[1-i][3]} daily',text)
                self.assertNotIn('money',text)
                self.assertNotIn('Pay ',text)
        self.assertIn('24,000 energy, 1,600 supplies and 200 money for 12,000 oil',BY['wartime_fuel_batch'].desc)

    def test_army_mobile_and_naval_effects_are_explicit(self):
        text=BY['army_production'].desc
        for expected in ('Motorised Infantry: -3 IC, -47.25 days','Cavalry: -1.2 IC, -49.5 days',
                         'Armour: -4.2 IC, -51.75 days','Transport capacity +10%',
                         'Marines: -1.6 IC, -63 days','150 money and 900 supplies'):
            self.assertIn(expected,text)
        self.assertIn('Fleet carriers: -0.38 IC, -153 days',BY['naval_production'].desc)

    def test_selected_regional_delivery_and_plain_equipment_conditions(self):
        self.assertIn('Two Destroyers',BY['in_java_shipyards_finish_0'].desc)
        self.assertNotIn('Light Cruiser',BY['in_java_shipyards_finish_0'].desc)
        self.assertIn('One Light Cruiser',BY['in_java_shipyards_finish_1'].desc)
        self.assertIn('operational airfield level in Manila',BY['ph_manila_air'].desc)
        self.assertIn('full strength',BY['ph_manila_air'].desc)
        self.assertNotIn('allowed maximum strength',BY['ph_manila_air'].desc)
        self.assertNotIn('Pearl Harbor',BY['welcome'].desc)
        self.assertNotIn('historical',BY['welcome'].desc)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PlayerCopyReview))
    report={**player_copy.REPORT,'catalogue_events':len(build.EVENTS),'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),
            'justified_game_terms':['IC, AA and transport capacity are displayed game statistics.',
                                   'Technical mission describes an equipment-research delegation.',
                                   'Airfields and air groups are ordinary military terms; the AI test uses whole words.'],
            'source_max_amphib_correction':'prewar_landing_trials uses value=1 when=1; native default mode sets the absolute limit.'}
    (Path(__file__).parent/'PLAYER_COPY_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    raise SystemExit(not result.wasSuccessful())
