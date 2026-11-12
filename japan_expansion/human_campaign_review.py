"""Focused state checks for the R7 economy and retired offers; no game launch."""
import json
import unittest
from pathlib import Path
from simulate import World, BY_KEY
from build import EVENTS,parse,resolve
from human_campaign import RETIRED
from specialist_units import models


class HumanCampaignReview(unittest.TestCase):
    def test_small_and_large_fuel_orders_charge_and_deliver_once(self):
        for i,energy,stock,cash,oil in [(1,12000,800,100,6000),(2,24000,1600,200,12000)]:
            w=World();w.resources['JAP'].update(energy=50000,oil=0);w.flags.update(JX_strategic_storage_DONE=1,JX_home_fuel_DONE=1,JX_war_fuel_DONE=1)
            before=w.resources['JAP'].copy()
            self.assertTrue(w.action('wartime_fuel_batch',i))
            self.assertEqual(w.resources['JAP']['energy'],before['energy']-energy)
            self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-stock)
            self.assertEqual(w.resources['JAP']['money'],before['money']-cash)
            self.assertFalse(w.action('wartime_fuel_batch',i))
            w.advance(44);self.assertEqual(w.resources['JAP']['oil'],before['oil'])
            w.advance(1);self.assertEqual(w.resources['JAP']['oil'],before['oil']+oil)
            self.assertFalse(w.action(f'fuel_batch_delivery_{i-1}',0))
            self.assertFalse(w.action('wartime_fuel_batch',i))
            w.advance(45);w.resources['JAP'].update(oil=0,energy=50000);self.assertTrue(w.action('wartime_fuel_batch',i))

    def test_unfunded_and_peacetime_fuel_orders_take_nothing(self):
        for mode in ('energy','supplies','money','peace'):
            w=World();w.resources['JAP'].update(energy=50000,oil=0);w.flags.update(JX_strategic_storage_DONE=1,JX_home_fuel_DONE=1,JX_war_fuel_DONE=1)
            if mode=='peace':w.wars.clear()
            else:w.resources['JAP'][mode]=0
            before=w.resources['JAP'].copy()
            self.assertFalse(w.action('wartime_fuel_batch',0))
            self.assertEqual(w.resources['JAP'],before)
            self.assertFalse(w.queue)

    def test_losing_fuelworks_site_refunds_and_awards_no_output(self):
        w=World();before=w.resources['JAP'].copy()
        self.assertTrue(w.action('home_fuel',0))
        w.controlled[1552]='USA';w.advance(240)
        self.assertEqual(w.resources['JAP'],before)
        self.assertFalse(any(k[1]=='add_prov_resource' for k in w.properties))

    def test_fuelworks_can_award_only_once(self):
        w=World();w.action('home_fuel',0);w.advance(240)
        before=dict(w.properties)
        self.assertFalse(w.action('home_fuel_finish_0',0))
        self.assertEqual(dict(w.properties),before)

    def test_old_ids_are_preserved_and_retired_offers_are_blocked(self):
        old=json.loads((Path(__file__).parent/'backups/before_R7_20261111/events.json').read_text())
        for e in old:self.assertEqual(BY_KEY[e['key']].id,e['id'],e['key'])
        for key in RETIRED:self.assertEqual(BY_KEY[key].gate,'ai = yes ai = no')
        self.assertIn('guards',RETIRED)
        self.assertFalse(any('which = d_01' in c for e in EVENTS if e.module in ('human_preparation','human_fuel') for a in e.actions for c in a.commands))

    def test_small_formations_have_meaningful_production_roles(self):
        for unit,max_days,max_mp in [('d_10',400,5),('d_11',760,8),('d_12',1440,9)]:
            for m in models(unit):
                n=dict(m)
                self.assertLessEqual(float(n['cost'])*float(n['buildtime']),max_days)
                self.assertEqual(float(n['manpower']),max_mp)

    def test_imports_have_an_exit_and_a_small_volume_choice(self):
        from build import get
        imports=[e for e in EVENTS if e.module=='early' and e.key in ('fx1933','oil1934','fx1936')]
        for e in imports:
            for a in e.actions:
                for c in a.commands:
                    n=parse(resolve(c))
                    if get(n,'type')=='trade':self.assertEqual(get(n,'value'),'0')
        self.assertIn('8 oil',BY_KEY['fx1933'].actions[2].name)

    def test_storage_applies_to_japan_once_without_free_fuel(self):
        w=World();before=w.resources['JAP']['oil']
        w.action('strategic_storage');w.advance(90)
        self.assertEqual(w.properties['JAP','stockpile','supplies',None],200)
        self.assertEqual(w.resources['JAP']['oil'],before)
        self.assertFalse(w.action('strategic_storage_finish_0'))

    def test_r7_ids_and_explicit_air_costs_are_preserved(self):
        from build import get
        old=json.loads((Path(__file__).parent/'backups/R7_before_R8_events.json').read_text())
        for e in old:self.assertEqual(BY_KEY[e['key']].id,e['id'],e['key'])
        costs={}
        for c in BY_KEY['air_production_finish_0'].actions[0].commands:
            n=parse(resolve(c))
            if get(n,'type')=='build_cost':
                self.assertIsNone(get(n,'where'))
                costs[get(n,'which')]=float(get(n,'value'))
        self.assertEqual(costs,{'interceptor':-3.5,'multi_role':-4,'cas':-4,'tactical_bomber':-1.5,'naval_bomber':-1.5,'transport_plane':-1.5})


if __name__=='__main__':unittest.main(verbosity=2)
