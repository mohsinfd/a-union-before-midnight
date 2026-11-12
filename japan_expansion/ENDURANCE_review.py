"""State/contract regression checks; no engine launch or installation."""
import unittest
import build
import endurance_economy as economy

build.prepare_catalog()
economy.apply()
build.IDS.update({e.key:e.id for e in build.EVENTS})
import simulate
simulate.BY_KEY.update({e.key:e for e in build.EVENTS})
simulate.BY_ID.update({str(e.id):e for e in build.EVENTS})
from simulate import World, BY_KEY


def select(w, key, index=0):
    e = BY_KEY[key]
    if e.gate and not w.test(build.parse(build.resolve(e.gate)), e.country):
        return False
    return w.action(key, index)


class EnduranceReview(unittest.TestCase):
    def fuel_world(self):
        w = World()
        w.resources['JAP'].update(energy=50000, oil=0)
        w.flags['JX_strategic_storage_DONE'] = 1
        w.flags['JX_home_fuel_DONE'] = 1
        w.flags['JX_war_fuel_DONE'] = 1
        return w

    def test_each_packet_charges_once_delivers_once_and_waits(self):
        for index, amounts in enumerate(((3000,200,25,1500),)+economy.BATCHES):
            with self.subTest(index=index):
                energy, stock, cash, oil = amounts
                w = self.fuel_world(); before = w.resources['JAP'].copy()
                self.assertTrue(select(w,'wartime_fuel_batch',index))
                self.assertEqual(w.resources['JAP']['energy'], before['energy']-energy)
                self.assertEqual(w.resources['JAP']['supplies'], before['supplies']-stock)
                self.assertEqual(w.resources['JAP']['money'], before['money']-cash)
                self.assertFalse(select(w,'wartime_fuel_batch',index))
                w.advance(44); self.assertEqual(w.resources['JAP']['oil'],0)
                w.advance(1); self.assertEqual(w.resources['JAP']['oil'],oil)
                receiver = ('endurance_small_fuel_delivery' if index == 0 else f'fuel_batch_delivery_{index-1}')
                self.assertFalse(w.action(receiver))
                self.assertFalse(select(w,'wartime_fuel_batch',index))
                w.advance(45); w.resources['JAP'].update(oil=0,energy=50000)
                self.assertTrue(select(w,'wartime_fuel_batch',index))

    def test_reserve_storage_and_stock_thresholds_charge_nothing(self):
        for kind in ('reserve','storage','works','oil','peace','supplies','money'):
            w=self.fuel_world()
            if kind=='reserve':w.resources['JAP']['energy']=20999
            elif kind=='storage':w.flags.pop('JX_strategic_storage_DONE')
            elif kind=='works':w.flags.pop('JX_home_fuel_DONE')
            elif kind=='oil':w.resources['JAP']['oil']=6000
            elif kind=='peace':w.wars.clear()
            else:w.resources['JAP'][kind]=0
            before=w.resources['JAP'].copy()
            self.assertFalse(select(w,'wartime_fuel_batch',1),kind)
            self.assertEqual(w.resources['JAP'],before)
            self.assertFalse(w.queue)

    def test_changed_stock_cancels_and_refunds_exactly_once(self):
        w=self.fuel_world(); before=w.resources['JAP'].copy()
        self.assertTrue(select(w,'wartime_fuel_batch',2))
        w.resources['JAP']['oil']=12000
        w.advance(45)
        self.assertEqual(w.resources['JAP']['oil'],12000)
        for resource in ('energy','supplies','money'):
            self.assertEqual(w.resources['JAP'][resource],before[resource])
        self.assertFalse(w.action('fuel_batch_delivery_1',1))
        self.assertTrue(w.flags.get('JX_FUEL_BATCH_WAIT'))

    def test_all_four_work_choices_are_exclusive_and_require_metal(self):
        for key,year,cash,stock,metal,days,mine,alternatives in economy.STAGES:
            for index,values in enumerate(alternatives):
                w=World();w.flags['JX_home_fuel_DONE']=1
                if key=='home_fuel':w.flags.pop('JX_home_fuel_DONE')
                before=w.resources['JAP'].copy()
                self.assertTrue(select(w,key,index))
                self.assertEqual(w.resources['JAP']['metal'],before['metal']-metal)
                self.assertFalse(select(w,key,1-index))
                w.advance(days)
                self.assertEqual(w.properties['JAP','add_prov_resource',str(mine),'energy'],values[0])
                self.assertEqual(w.properties['JAP','add_prov_resource','1552','oil'],values[3])
                self.assertFalse(w.action(f'{key}_finish_{index}'))
                self.assertFalse(select(w,key,index))

    def test_loss_of_mine_returns_complete_investment_without_output(self):
        for index in (0,1):
            w=World();before=w.resources['JAP'].copy()
            self.assertTrue(select(w,'home_fuel',index))
            w.controlled[1544]='USA';w.advance(240)
            self.assertEqual(w.resources['JAP'],before)
            self.assertFalse(any(k[1]=='add_prov_resource' for k in w.properties))

    def test_stage_two_requires_first_stage_and_war(self):
        w=World()
        self.assertFalse(select(w,'war_fuel'))
        w.flags['JX_home_fuel_DONE']=1;w.wars.clear()
        self.assertFalse(select(w,'war_fuel'))

    def test_no_worldwide_or_free_daily_outputs_and_idempotence(self):
        count=len(build.EVENTS);economy.apply();self.assertEqual(len(build.EVENTS),count)
        for key in ('home_fuel','war_fuel','wartime_fuel_batch','endurance_small_fuel_delivery'):
            self.assertEqual(BY_KEY[key].country,'JAP')
        for key in ('home_fuel','war_fuel'):
            self.assertIn('ai = no',BY_KEY[key].gate)
            for i in (0,1):
                self.assertIn('ai = no',BY_KEY[f'{key}_finish_{i}'].actions[0].gate)
                self.assertFalse(any('type = free_' in c for c in BY_KEY[f'{key}_finish_{i}'].actions[0].commands))


if __name__=='__main__':unittest.main(verbosity=2)
