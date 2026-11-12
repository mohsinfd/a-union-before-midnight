"""Compiled eligibility and bounded continental responses; no game/save edits."""
import copy
import unittest
import build
from simulate import World, BY_KEY, BY_ID
import us_campaign_content as usc

build.prepare_catalog()
OLD = {e.key: (e.id, e.gate, e.desc, copy.deepcopy(e.actions)) for e in build.EVENTS if e.module != 'us_campaign_content'}
usc.append_events()
build.IDS.update({e.key: e.id for e in build.EVENTS})
BY_KEY.update({e.key: e for e in build.EVENTS})
BY_ID.update({str(e.id): e for e in build.EVENTS})


class CampaignWorld(World):
    def __init__(self):
        super().__init__()
        self.year = 1942; self.humans = {'JAP'}; self.spawned = []; self.corps_sites = []
        self.wars.clear(); self.addwar('JAP', 'USA')
        self.country_tech['USA'] = {'1110'}
        for p, _ in usc.PORTS:self.owned[p] = self.controlled[p] = 'USA'
        self.controlled[1887] = 'JAP'
    def test(self, node, actor):
        out=[]
        for k,v in node:
            if k == 'ai':out.append((actor not in self.humans) if v == 'yes' else ((actor in self.humans) if v == 'no' else v not in self.humans))
            else:out.append(super().test([(k,v)],actor))
        return all(out)
    def command(self,node,actor):
        gate=build.get(node,'trigger')
        if not gate or self.test(gate,actor):
            if build.get(node,'type')=='add_division':self.spawned.append((actor,build.get(node,'value'),int(build.get(node,'when'))))
            if build.get(node,'type')=='add_corps':self.corps_sites.append((actor,int(build.get(node,'where'))))
        return super().command(node,actor)


def eligible(w,key):
    e=BY_KEY[key];n=build.get(build.parse(build.compiled_event(e)),'event')
    if e.year>w.year or w.year>1950:return False
    return w.test(build.get(n,'decision' if e.decision else 'trigger',[]),e.country) and (not e.decision or w.test(build.get(n,'decision_trigger',[]),e.country))


class USCampaignReview(unittest.TestCase):
    def landed(self):
        w=CampaignWorld();self.assertTrue(eligible(w,'usc_landing'));self.assertTrue(w.action('usc_landing'));return w

    def test_append_only_and_eight_substantive_entries(self):
        self.assertEqual(len(usc.REPORT['substantive']),8)
        for key,old in OLD.items():
            e=BY_KEY[key];self.assertEqual((e.id,e.gate,e.desc,e.actions),old,key)
        ids=[BY_KEY[k].id for k in usc.REPORT['added']]
        self.assertEqual(len(ids),len(set(ids)))
        earlier_ids=[v[0] for key,v in OLD.items() if not BY_KEY[key].module.startswith('unique_unit_')]
        later_ids=[e.id for e in build.EVENTS if e.module.startswith('unique_unit_')]
        self.assertGreater(min(ids),max(earlier_ids))
        self.assertLess(max(ids),min(later_ids))
        count=len(build.EVENTS);usc.append_events();self.assertEqual(len(build.EVENTS),count)

    def test_prewar_and_wrong_controllers_cannot_start_new_content(self):
        for year in (1933,1937,1940):
            w=CampaignWorld();w.year=year
            for key in usc.REPORT['substantive']:self.assertFalse(eligible(w,key),(year,key))
        for humans in ({'USA'}, {'JAP','USA'}, set()):
            w=CampaignWorld();w.humans=humans;w.flags['JX_USC_LANDING_DONE']=1
            self.assertFalse(eligible(w,'usc_landing'));self.assertFalse(eligible(w,'usc_coast_response'))
        w=CampaignWorld();w.masters['JAP']='USA';w.flags['JX_USC_LANDING_DONE']=1
        self.assertFalse(eligible(w,'usc_landing'));self.assertFalse(eligible(w,'usc_coast_response'))

    def test_all_major_ports_allow_once_only_landing_reward_without_ownership_change(self):
        for port,_ in usc.PORTS:
            w=CampaignWorld()
            for p,_ in usc.PORTS:w.controlled[p]='USA'
            w.controlled[port]='JAP';before=w.resources['JAP']['supplies']
            self.assertTrue(eligible(w,'usc_landing'));self.assertTrue(w.action('usc_landing'))
            self.assertEqual(w.resources['JAP']['supplies'],before+3500)
            self.assertEqual(w.owned[port],'USA');self.assertFalse(w.action('usc_landing'))
            self.assertFalse(w.action('usc_landing',1))

    def test_coastal_response_spends_actual_budget_and_spawns_six_researched_infantry(self):
        w=self.landed();before=w.resources['USA'].copy();army=w.armies['USA']
        self.assertTrue(eligible(w,'usc_coast_response'));w.dispatch('usc_coast_response')
        self.assertEqual(w.resources['USA']['manpower'],before['manpower']-78)
        self.assertEqual(w.resources['USA']['supplies'],before['supplies']-2400)
        self.assertEqual(w.armies['USA'],army+6);self.assertEqual(w.spawned,[('USA','infantry',10)]*6)
        self.assertEqual(w.corps_sites,[('USA',1908)])
        self.assertFalse(eligible(w,'usc_coast_response'));w.advance(1)
        self.assertIn('usc_coast_response_notice',w.received);self.assertTrue(w.flags['JX_USC_COAST_RESPONSE_TOLD'])

    def test_1936_fallback_and_low_research_or_stock_budget_are_real(self):
        w=self.landed();w.country_tech['USA']={'1100'};w.dispatch('usc_coast_response')
        self.assertEqual(w.spawned,[('USA','infantry',9)]*6)
        for failure in ('research','manpower','supplies','sites'):
            v=self.landed()
            if failure=='research':v.country_tech['USA']=set()
            elif failure=='sites':
                for p,_ in usc.COAST_HUBS:v.controlled[p]='JAP'
            else:v.resources['USA'][failure]=0
            before=v.resources['USA'].copy();v.dispatch('usc_coast_response')
            self.assertFalse(v.spawned);self.assertFalse(v.corps_sites)
            self.assertEqual(v.resources['USA']['manpower'],before['manpower']+40)
            self.assertEqual(v.resources['USA']['supplies'],before['supplies']+2000)
            v.advance(1);self.assertTrue(v.flags['JX_USC_COAST_RESPONSE_TOLD'])

    def test_no_response_can_spawn_on_enemy_controlled_or_foreign_owned_city(self):
        w=self.landed();w.controlled[1908]='JAP';w.owned[1896]='ENG'
        w.dispatch('usc_coast_response');self.assertEqual(w.corps_sites,[('USA',1900)])
        for actor,site in w.corps_sites:
            self.assertEqual(w.owned[site],actor);self.assertEqual(w.controlled[site],actor)

    def test_second_wave_needs_time_and_interior_and_total_is_bounded_at_twelve(self):
        w=self.landed();w.dispatch('usc_coast_response');w.controlled[1893]='JAP'
        self.assertFalse(eligible(w,'usc_inland_response'));w.advance(59)
        self.assertFalse(eligible(w,'usc_inland_response'));w.advance(1)
        self.assertTrue(eligible(w,'usc_inland_response'));w.dispatch('usc_inland_response')
        self.assertEqual(len(w.spawned),12);self.assertEqual(w.corps_sites[-1],('USA',1914))
        self.assertFalse(eligible(w,'usc_inland_response'));self.assertFalse(w.action('usc_inland_response'))

    def test_replacement_choices_charge_deliver_once_and_refund_if_foothold_lost(self):
        for option in (0,1):
            w=self.landed();before=w.resources['JAP'].copy()
            self.assertTrue(eligible(w,'usc_replacements'));self.assertTrue(w.action('usc_replacements',option))
            self.assertFalse(w.action('usc_replacements',option));w.advance(60)
            self.assertEqual(w.resources['JAP']['money'],before['money']-200)
            self.assertEqual(w.resources['JAP']['manpower'],before['manpower']+(50 if option==0 else 0))
            self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-2500+(6000 if option==1 else 0))
            self.assertFalse(w.action('usc_replacements_finish_'+str(option)))
        w=self.landed();before=w.resources['JAP'].copy();w.action('usc_replacements')
        w.controlled[1887]='USA';w.advance(60);self.assertEqual(w.resources['JAP'],before)
        w.dispatch('usc_replacements_finish_0');self.assertEqual(w.resources['JAP'],before)

    def test_california_and_plains_milestones_require_named_cities_and_time(self):
        w=self.landed()
        for p in (1886,1887,1888,1889):w.controlled[p]='JAP'
        self.assertFalse(eligible(w,'usc_california'));w.advance(90)
        self.assertTrue(eligible(w,'usc_california'));before=w.resources['JAP'].copy();w.action('usc_california')
        self.assertEqual(w.resources['JAP']['metal'],before['metal']+8000);self.assertFalse(w.action('usc_california'))
        w.controlled[1908]='JAP';w.advance(90);self.assertFalse(eligible(w,'usc_plains'))
        w.controlled[1914]='JAP';self.assertTrue(eligible(w,'usc_plains'));before=w.resources['JAP']['supplies']
        w.action('usc_plains',1);self.assertEqual(w.resources['JAP']['supplies'],before+9000)
        self.assertEqual(w.owned[1908],'USA');self.assertEqual(w.owned[1914],'USA')

    def test_180_day_commitment_and_endurance_keep_all_existing_peace_choices(self):
        w=self.landed();self.assertFalse(eligible(w,'usc_commitment'));self.assertFalse(eligible(w,'usc_endurance'))
        w.advance(180);self.assertTrue(eligible(w,'usc_commitment'));self.assertTrue(eligible(w,'usc_endurance'))
        before=w.resources['USA'].copy();w.action('usc_endurance')
        self.assertEqual(w.resources['USA']['manpower'],before['manpower']+60)
        self.assertEqual(w.resources['USA']['supplies'],before['supplies']+9000)
        self.assertEqual(w.resources['USA']['oil'],before['oil']+5000)
        self.assertFalse(eligible(w,'usc_endurance'));w.action('usc_commitment',1);w.advance(60)
        self.assertTrue(w.atwar('JAP','USA'))
        self.assertFalse(any('DISMISSED' in k and ('US_INV' in k or k=='JX_US_DISMISSED') for k in w.flags))
        self.assertNotIn('JX_US_PEACE',w.flags)
        self.assertNotIn('JX_usc_replacements_DISMISSED',w.flags)

    def test_source_templates_tech_mapping_province_names_and_copy_are_verified(self):
        models=build.getall(build.parse(build.read(build.SOURCE/'db/units/divisions/infantry.txt')),'model')
        self.assertEqual(float(build.get(models[9],'manpower')),13);self.assertEqual(float(build.get(models[10],'manpower')),13)
        tech=build.parse(build.read(build.SOURCE/'db/tech/infantry_tech.txt'))
        apps=[a for t in build.getall(tech,'technology') for a in build.getall(t,'application')]
        for appid,model in [('1110','10'),('1100','9')]:
            app=next(a for a in apps if build.get(a,'id')==appid)
            self.assertTrue(any(build.get(c,'type')=='new_model' and build.get(c,'which')=='infantry' and build.get(c,'value')==model for c in build.getall(build.get(app,'effects'),'command')))
        names=build.province_names()
        for p,name in usc.PORTS+usc.COAST_HUBS+usc.INLAND_HUBS:self.assertEqual(names[p],name)
        usa=build.get(build.parse(build.read(build.SOURCE/'scenarios/1933/usa.inc')),'country')
        homeland={int(p) for _,p in build.get(usa,'ownedprovinces',[])}
        self.assertTrue({p for p,_ in usc.PORTS+usc.COAST_HUBS+usc.INLAND_HUBS}|{1888,1893} <= homeland)
        self.assertEqual(names[1888],'Sacramento');self.assertEqual(names[1893],'Las Vegas')
        for key in usc.REPORT['added']:
            e=BY_KEY[key];self.assertLess(len(e.desc),1100)
            for a in e.actions:
                for c in a.commands:self.assertNotIn(build.get(build.parse(c),'type'),{'war','peace','country','independence','make_puppet','secedeprovince','addcore','free_ic','free_oil'})


if __name__=='__main__':unittest.main(verbosity=2)
