"""Offline recovery choices: actual losses, commitments and equipped deliveries."""
import copy,json,unittest
from pathlib import Path
import build as b
import simulate as sim
import r15_recovery as rec

rec.apply()
b.IDS.update({e.key:e.id for e in b.EVENTS})
sim.BY_KEY.update({e.key:e for e in b.EVENTS})
sim.BY_ID.update({str(e.id):e for e in b.EVENTS})
BY=sim.BY_KEY


class RecoveryWorld(sim.World):
    def __init__(self):
        super().__init__();self.year=1944;self.brigades=[];self.created_corps=[]
        self.types['JAP','carrier']=3;self.types['JAP','lost_carrier']=3
        self.country_tech['JAP']={str(t) for u in rec.MIN_MODELS for _,_,t,_ in rec.equipment(u)}
        self.owned[1552]=self.controlled[1552]='JAP'
        self.buildings[1552,'air_base']=10;self.buildings[1552,'naval_base']=10
        for tag in self.countries:self.resources[tag]
    def test(self,node,actor):
        out=[]
        for k,v in node:
            if k=='carrier':out.append(self.types[b.get(v,'country',actor),'carrier']>=float(b.get(v,'value')))
            elif k=='losses':out.append(self.types[b.get(v,'country',actor),'lost_'+b.get(v,'type')]>=float(b.get(v,'value')))
            elif k=='ai':out.append((actor=='JAP') if v=='no' else (actor!='JAP') if v=='yes' else v!='JAP')
            else:out.append(super().test([(k,v)],actor))
        return all(out)
    def command(self,node,actor):
        gate=b.get(node,'trigger');runs=not gate or self.test(gate,actor)
        super().command(node,actor)
        if runs and b.get(node,'type')=='add_division':self.deployed_units[-1]['strength']=0
        if runs and b.get(node,'type')=='add_brigade':self.brigades.append((actor,b.get(node,'value'),int(b.get(node,'when'))))
        if runs and b.get(node,'type')=='add_corps':self.created_corps.append((b.get(node,'which'),b.get(node,'value'),int(b.get(node,'where'))))
    def cached(self,key,index=0):
        for command in BY[key].actions[index].commands:self.command(b.parse(b.resolve(command)),BY[key].country)


def available(w,key):
    e=BY[key];return w.year>=e.year and w.test(b.parse(b.resolve(e.gate+' '+e.ready)),e.country)


class RecoveryReview(unittest.TestCase):
    def lost_base(self,p=1667,enemy='USA'):
        w=RecoveryWorld();w.controlled[p]='JAP';w.dispatch('r15_remember_base_'+str(p));w.controlled[p]=enemy
        w.countries.add(enemy);w.addwar('JAP',enemy);w.dispatch('r15_lost_base_'+str(p));return w

    def test_crisis_needs_both_real_losses_and_current_weakness(self):
        w=RecoveryWorld();self.assertTrue(available(w,'r15_carrier_recovery'))
        for change in ('losses','carriers','peace','prewar','year'):
            w=RecoveryWorld()
            if change=='losses':w.types['JAP','lost_carrier']=2
            if change=='carriers':w.types['JAP','carrier']=4
            if change=='peace':w.wars.clear()
            if change=='prewar':w.flags.pop('JX_PACIFIC')
            if change=='year':w.year=1941
            self.assertFalse(available(w,'r15_carrier_recovery'),change)
            if change!='year':
                before=copy.deepcopy(w.resources);w.cached('r15_carrier_recovery');self.assertEqual(w.resources,before)

    def test_fleet_rebuild_has_paid_hull_correct_air_group_and_crews(self):
        for year in (1942,1945,1950):
            w=RecoveryWorld();w.year=year;before=w.resources['JAP'].copy()
            self.assertTrue(w.action('r15_carrier_recovery',0));self.assertTrue(w.flags['JX_R15_MAJOR_PENDING'])
            self.assertFalse(w.action('r15_carrier_recovery',1))
            self.assertFalse(w.action('r15_carrier_recovery_finish_0'))
            w.advance(329);self.assertFalse(w.deployed_units);w.advance(1)
            self.assertEqual(sorted(u['type'] for u in w.deployed_units),['destroyer']*4+['light_carrier']*2)
            self.assertTrue(all(u['strength']==100 and u['location']==1552 for u in w.deployed_units))
            self.assertEqual(len(w.brigades),2);self.assertTrue(all(brigade[1]=='light_cag' for brigade in w.brigades))
            self.assertEqual(w.created_corps,[('Rebuilt Carrier Force','naval',1552)])
            self.assertEqual(w.resources['JAP']['oil'],before['oil'])
            actual_mp=.14
            for u in w.deployed_units:
                models=b.getall(b.parse(b.read(b.SOURCE/'db/units/divisions'/(u['type']+'.txt'))),'model')
                actual_mp+=b.num(models[u['model']],'manpower')
            self.assertAlmostEqual(before['manpower']-w.resources['JAP']['manpower'],actual_mp)
            self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
            snapshot=copy.deepcopy((w.resources,w.deployed_units,w.brigades));w.cached('r15_carrier_recovery_finish_0')
            self.assertEqual((w.resources,w.deployed_units,w.brigades),snapshot)

    def test_shore_air_is_faster_and_uses_researched_dated_equipment(self):
        w=RecoveryWorld();w.year=1942;before=w.resources['JAP'].copy()
        self.assertTrue(w.action('r15_carrier_recovery',1));w.advance(179);self.assertFalse(w.deployed_units);w.advance(1)
        self.assertEqual(sorted(u['type'] for u in w.deployed_units),['multi_role','naval_bomber','naval_bomber'])
        self.assertTrue(all(u['strength']==100 for u in w.deployed_units))
        self.assertEqual([u['model'] for u in w.deployed_units],[3,3,6])
        self.assertEqual(w.resources['JAP']['manpower'],before['manpower']-5.4)
        self.assertFalse(w.brigades)

    def test_future_research_does_not_unlock_future_models(self):
        for unit in rec.MIN_MODELS:
            w=RecoveryWorld();w.year=1942
            actual=[(model,mp) for model,g,mp in rec.latest(unit) if w.test(b.parse(g),'JAP')]
            self.assertEqual(len(actual),1,unit)
            expected=max(model for model,year,_,_ in rec.equipment(unit) if year<=1942)
            self.assertEqual(actual[0][0],expected)

    def test_no_research_no_home_facility_or_budget_cannot_pay(self):
        for defect in ('tech','port','airfield','money','manpower','lock','puppet'):
            w=RecoveryWorld()
            if defect=='tech':w.country_tech['JAP']=set()
            elif defect=='port':w.buildings[1552,'naval_base']=0
            elif defect=='airfield':w.buildings[1552,'air_base']=0
            elif defect=='lock':w.flags['JX_R15_MAJOR_PENDING']=1
            elif defect=='puppet':w.masters['JAP']='USA'
            else:w.resources['JAP'][defect]=0
            index=1 if defect=='airfield' else 0;before=copy.deepcopy(w.resources)
            self.assertFalse(w.action('r15_carrier_recovery',index),defect);w.cached('r15_carrier_recovery',index)
            self.assertEqual(w.resources,before,defect);self.assertFalse(w.queue)

    def test_delivery_failure_refunds_every_input_and_closes_once(self):
        for key,index,days in [('r15_carrier_recovery',0,330),('r15_carrier_recovery',1,180),('r15_anchorage_recovery',0,90),('r15_anchorage_recovery',1,180)]:
            for defect in ('peace','occupation'):
                if key=='r15_anchorage_recovery' and index==0 and defect=='occupation':continue
                w=self.lost_base();before=copy.deepcopy(w.resources)
                self.assertTrue(w.action(key,index));paid=copy.deepcopy(w.resources)
                if defect=='peace':w.wars.clear()
                else:w.controlled[1552]='USA'
                finish=f'{key}_finish_{index}';self.assertFalse(w.action(finish,1));self.assertEqual(w.resources,paid)
                w.advance(days);self.assertEqual(w.resources,before,(key,index,defect));self.assertFalse(w.deployed_units)
                self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'));w.cached(finish,1);self.assertEqual(w.resources,before)

    def test_previous_control_and_enemy_war_are_required(self):
        w=RecoveryWorld();w.controlled[1667]='USA'
        w.dispatch('r15_lost_base_1667')
        self.assertFalse(available(w,'r15_anchorage_recovery'))
        for p,_ in rec.BASES:
            w=self.lost_base(p);self.assertTrue(available(w,'r15_anchorage_recovery'))
            w=RecoveryWorld();w.controlled[p]='JAP';w.dispatch('r15_remember_base_'+str(p));w.controlled[p]='USA'
            w.wars={pair for pair in w.wars if not('JAP' in pair and 'USA' in pair)}
            w.dispatch('r15_lost_base_'+str(p))
            # Britain is still an enemy; a peaceful American handover still cannot qualify.
            self.assertTrue(w.atwar('JAP','ENG'));self.assertFalse(available(w,'r15_anchorage_recovery'))

    def test_all_native_hostile_controllers_and_recovered_base_history(self):
        for enemy in ('HOL','U02','PHI','SOV'):
            self.assertIn(enemy,rec.country_tags())
            w=self.lost_base(enemy=enemy);self.assertTrue(w.flags.get('JX_R15_ANCHORAGE_LOST'),enemy)
            w.controlled[1667]='JAP';self.assertTrue(available(w,'r15_anchorage_recovery'))
            before=copy.deepcopy(w.flags);w.cached('r15_lost_base_1667');self.assertEqual(w.flags,before)
        for neutral in ('MAN','GER'):
            w=RecoveryWorld();w.controlled[1667]='JAP';w.dispatch('r15_remember_base_1667');w.controlled[1667]=neutral
            w.dispatch('r15_lost_base_1667');self.assertFalse(w.flags.get('JX_R15_ANCHORAGE_LOST'),neutral)

    def test_shipping_recovery_is_a_finite_pool_not_a_spawn(self):
        w=self.lost_base();self.assertTrue(w.action('r15_anchorage_recovery',0));w.advance(90)
        self.assertEqual(w.properties['JAP','transport_pool','-1',None],160)
        self.assertEqual(w.properties['JAP','escort_pool','-1',None],100)
        self.assertFalse(w.deployed_units);self.assertFalse(w.action('r15_anchorage_recovery',1))

    def test_return_force_can_finish_after_successful_recapture(self):
        w=self.lost_base();self.assertTrue(w.action('r15_anchorage_recovery',1));w.controlled[1667]='JAP';w.advance(180)
        self.assertEqual([u['type'] for u in w.deployed_units],['marine','transport'])
        self.assertTrue(all(u['strength']==100 and u['location']==1552 for u in w.deployed_units))
        self.assertEqual(w.controlled[1667],'JAP')

    def test_shared_lock_blocks_second_recovery_and_unauthorised_cleanup(self):
        w=self.lost_base();w.action('r15_carrier_recovery',0)
        before=copy.deepcopy(w.resources);self.assertFalse(w.action('r15_anchorage_recovery',0));w.cached('r15_anchorage_recovery')
        w.cached('r15_anchorage_recovery_finish_0',1);self.assertEqual(w.resources,before)
        self.assertTrue(w.flags['JX_R15_MAJOR_PENDING']);w.advance(330);self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
        self.assertTrue(w.action('r15_anchorage_recovery',0))

    def test_cached_start_cannot_spend_twice_or_change_choice(self):
        w=RecoveryWorld();w.action('r15_carrier_recovery',0);before=copy.deepcopy(w.resources)
        w.cached('r15_carrier_recovery',0);w.cached('r15_carrier_recovery',1)
        self.assertEqual(w.resources,before);self.assertEqual(len(w.queue),1)

    def test_stop_work_releases_commitment_with_visible_sunk_cost(self):
        for key,index,days in [('r15_carrier_recovery',0,330),('r15_carrier_recovery',1,180),('r15_anchorage_recovery',0,90),('r15_anchorage_recovery',1,180)]:
            w=self.lost_base();before=w.resources['JAP'].copy();self.assertTrue(w.action(key,index))
            selected=[i for i,a in enumerate(BY[key].actions) if i>=4 and w.test(b.parse(b.resolve(a.gate)),'JAP')]
            self.assertEqual(len(selected),1,(key,index));stop=selected[0]
            self.assertTrue(w.action(key,stop));self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
            row=__import__('r15_common').REPORT[key]['choices'][index]
            self.assertEqual(w.resources['JAP']['money'],before['money']-row['cost']['money'])
            self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-row['cost']['supplies']*.25)
            for resource in ('manpower','metal','oil'):self.assertEqual(w.resources['JAP'][resource],before[resource])
            closed=copy.deepcopy(w.resources);w.cached(key,stop);self.assertEqual(w.resources,closed)
            w.advance(days);self.assertEqual(w.resources,closed);self.assertFalse(w.deployed_units);self.assertFalse(w.brigades)

    def test_leave_and_dismiss_are_free_and_permanent(self):
        w=RecoveryWorld();before=copy.deepcopy(w.resources);self.assertTrue(w.action('r15_carrier_recovery',2))
        self.assertEqual(w.resources,before);self.assertFalse(w.queue)
        self.assertTrue(w.action('r15_carrier_recovery',3));self.assertFalse(w.action('r15_carrier_recovery',0))
        self.assertEqual(w.resources,before)

    def test_old_ids_idempotence_and_readable_compact_choices(self):
        old={e.key:e.id for e in b.EVENTS};rec.apply();self.assertEqual({e.key:e.id for e in b.EVENTS},old)
        baseline=json.loads((b.HERE/'events.json').read_text(encoding='utf-8'))
        self.assertTrue(all(old[e['key']]==e['id'] for e in baseline))
        for e in b.EVENTS:
            if e.module!='r15_recovery':continue
            self.assertLess(len(e.desc),1101)
            for a in e.actions:
                if a.name:self.assertLess(len(a.gate),3000,(e.key,len(a.gate)))
                for c in a.commands:self.assertNotIn(b.get(b.parse(c),'type'),('war','peace','secedeprovince','make_puppet','free_manpower','build_cost','build_time'))


if __name__=='__main__':unittest.main(verbosity=2)
