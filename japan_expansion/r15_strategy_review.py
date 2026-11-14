"""Adversarial strategy commitments; file/state checks, never game execution."""
import copy,json,re,unittest
from pathlib import Path
import build as b
import simulate as sim
from FLOW_review import HumanWorld
import r15_strategy as strategy
import r15_common as common

b.prepare_catalog();strategy.apply()
b.IDS.update({e.key:e.id for e in b.EVENTS})
sim.BY_KEY.update({e.key:e for e in b.EVENTS});sim.BY_ID.update({str(e.id):e for e in b.EVENTS})
BY=sim.BY_KEY


class NativeWorld(HumanWorld):
    def __init__(self):super().__init__();self.attachments=[]
    def command(self,node,actor):
        gate=b.get(node,'trigger')
        runs=not gate or self.test(gate,actor)
        if not runs:return
        kind=b.get(node,'type')
        if kind=='add_brigade':self.attachments.append((actor,b.get(node,'value'),int(b.get(node,'when'))));return
        super().command(node,actor)
        if kind=='add_division':self.deployed_units[-1]['strength']=0
    def cached(self,key,index):
        for c in BY[key].actions[index].commands:self.command(b.parse(b.resolve(c)),BY[key].country)


def world(stage='china',year=None):
    w=NativeWorld();w.wars.clear();w.year=year or (1938 if stage=='china' else 1943);w.day=1000
    w.flags['JX_ACTIVE']=1
    w.resources['JAP'].update(money=10000,supplies=100000,manpower=500,oil=100000)
    w.country_tech['JAP']={str(r['tech']) for unit in strategy.MIN_YEARS for r in strategy.model_options(unit)}|{'2800'}
    for p in (1552,1550,1554,1557,1432,1667,1685,1676):
        w.owned[p]=w.controlled[p]='JAP';w.buildings[p,'naval_base']=1;w.buildings[p,'flak']=0
    if stage=='china':
        w.flags.pop('JX_PACIFIC',None);w.addwar('JAP','CHI');w.armies['CHI']=140;w.controlled[1338]='JAP'
    else:
        w.flags['JX_PACIFIC']=1;w.addwar('JAP','USA')
        if stage=='america':
            w.controlled[1887]='JAP';w.history[str(BY['usc_landing'].id)]=w.day-30
    return w


class StrategyReview(unittest.TestCase):
    def eligible(self,w,key):return w.test(b.parse(b.resolve(BY[key].gate)),BY[key].country)

    def test_original_ids_and_only_three_manual_offers(self):
        baseline=json.loads((b.HERE/'R14_PRESTART_BASELINE_IDS.json').read_text(encoding='utf-8'))
        for k,v in baseline.items():self.assertEqual(BY[k].id,v,k)
        self.assertEqual(BY['r14_china_limited_interrupted'].id,28602941)
        self.assertEqual(len(strategy.REPORT['roots']),3)
        self.assertTrue(all(BY[k].decision and BY[k].id>28602941 for k in strategy.REPORT['roots']))
        before=len(b.EVENTS);strategy.apply();self.assertEqual(len(b.EVENTS),before)

    def test_dates_context_and_manual_only(self):
        for key,stage in zip(strategy.REPORT['roots'],('china','ocean','america')):
            w=world(stage);self.assertTrue(self.eligible(w,key),key)
            compiled=b.get(b.parse(b.compiled_event(BY[key])),'event')
            self.assertFalse(w.test(b.get(compiled,'trigger'),'JAP'),key)
            w.year=BY[key].year-1;self.assertFalse(self.eligible(w,key))
        w=world();w.armies['CHI']=60;self.assertFalse(self.eligible(w,'r15_china_or_fleet'))
        w=world('america');w.history[str(BY['usc_landing'].id)]=w.day-29
        self.assertFalse(self.eligible(w,'r15_american_army'))
        w=world('ocean');w.controlled[1432]='ENG';self.assertFalse(self.eligible(w,'r15_pacific_or_ocean'))

    def test_all_six_branches_fund_deliver_once_equipped(self):
        cases=[('r15_china_or_fleet','china'),('r15_pacific_or_ocean','ocean'),('r15_american_army','america')]
        for key,stage in cases:
            for index in (0,1):
                with self.subTest(key=key,index=index):
                    w=world(stage);row=common.REPORT[key]['choices'][index];start=copy.deepcopy(w.resources['JAP'])
                    self.assertTrue(w.action(key,index))
                    for resource,amount in row['cost'].items():self.assertAlmostEqual(w.resources['JAP'][resource],start[resource]-amount)
                    paid=copy.deepcopy(w.resources);w.cached(key,index);self.assertEqual(w.resources,paid)
                    self.assertFalse(w.action(key,1-index));w.advance(row['days']-1)
                    self.assertFalse(w.deployed_units);w.advance(1)
                    self.assertTrue(w.deployed_units)
                    self.assertTrue(all(u['strength']==u['max_strength']==100 for u in w.deployed_units))
                    self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
                    self.assertTrue(w.flags[common.f(common.REPORT[key]['closed']).split()[-1]])
                    before=copy.deepcopy((w.resources,w.flags,w.deployed_units,w.attachments,w.properties))
                    w.cached(row['finish'],0);w.dispatch(row['finish'])
                    self.assertEqual((w.resources,w.flags,w.deployed_units,w.attachments,w.properties),before)

    def test_china_front_and_carrier_reserve_are_different(self):
        a=world();a.action('r15_china_or_fleet',0);a.advance(180)
        self.assertEqual(sorted(u['type'] for u in a.deployed_units),['bergsjaeger','infantry','infantry'])
        n=world();start=n.resources['JAP']['manpower'];n.action('r15_china_or_fleet',1);n.advance(240)
        self.assertEqual([u['type'] for u in n.deployed_units],['destroyer','destroyer'])
        self.assertEqual(n.attachments,[('JAP','cag',3)]*2)
        destroyer=next(r['mp'] for r in strategy.MODELS['destroyer'] if r['model']==6)
        cag=next(r['mp'] for r in strategy.MODELS['cag'] if r['model']==3)
        self.assertAlmostEqual(start-n.resources['JAP']['manpower'],2*destroyer+2*cag)
        self.assertEqual(n.properties['JAP','escort_pool','-1',None],60)

    def test_geographic_outcomes_and_researched_aa_attachments(self):
        w=world('ocean');w.action('r15_pacific_or_ocean',0);w.advance(210)
        self.assertEqual({u['location'] for u in w.deployed_units},{1667,1685,1676})
        self.assertEqual(w.attachments,[('JAP','anti_air',4)]*3)
        self.assertTrue(all(w.buildings[p,'flak']==0 for p,_ in strategy.PACIFIC_BASES))
        w=world('ocean');w.country_tech['JAP']-={str(r['tech']) for r in strategy.model_options('anti_air')};before=copy.deepcopy(w.resources)
        self.assertFalse(w.action('r15_pacific_or_ocean',0));self.assertEqual(w.resources,before)
        w=world('ocean');w.owned[1432]='ENG'
        self.assertFalse(w.action('r15_pacific_or_ocean',1))
        w=world('ocean');w.action('r15_pacific_or_ocean',1);w.advance(240)
        self.assertEqual([u['type'] for u in w.deployed_units],['marine','bergsjaeger','transport','transport'])
        self.assertTrue(all(u['location']==1432 for u in w.deployed_units))

    def test_american_army_does_not_teleport_or_create_manpower(self):
        w=world('america');start=w.resources['JAP']['manpower'];w.action('r15_american_army',0);w.advance(270)
        self.assertEqual(len(w.deployed_units),8);self.assertTrue(all(u['location']==1552 for u in w.deployed_units))
        self.assertEqual(start-w.resources['JAP']['manpower'],104)
        w=world('america');w.action('r15_american_army',1);w.advance(150)
        self.assertEqual(len(w.deployed_units),4)
        self.assertEqual({u['location'] for u in w.deployed_units},{1552,1550,1554,1557})
        self.assertEqual(w.properties['JAP','transport_pool','-1',None],180)
        self.assertEqual(w.properties['JAP','escort_pool','-1',None],100)

    def test_inadequate_recruits_or_research_cannot_pay(self):
        for resource in ('money','supplies','manpower','oil'):
            w=world('america');w.resources['JAP'][resource]=0;before=copy.deepcopy(w.resources)
            self.assertFalse(w.action('r15_american_army',0));self.assertEqual(w.resources,before)
        w=world();w.country_tech['JAP']={'1140','1290'};before=copy.deepcopy(w.resources)
        self.assertFalse(w.action('r15_china_or_fleet',0));self.assertEqual(w.resources,before)

    def test_real_models_match_research_year_and_full_manpower(self):
        w=world('america',1945);w.action('r15_american_army',0);w.advance(270)
        self.assertEqual([u['model'] for u in w.deployed_units[:6]],[12]*6)
        self.assertEqual([u['model'] for u in w.deployed_units[6:]],[12]*2)
        for unit,rows in strategy.MODELS.items():
            self.assertTrue(all(r['year']<=1950 and r['mp']>0 for r in rows),unit)
        # Birth/heal share exact model selector; no accidental brigade field.
        for pack in strategy.REPORT['packages'].values():
            for bundle in pack:
                for item in bundle['items']:
                    nodes=[b.parse(b.resolve(c)) for c in item['commands']]
                    if item['unit'] in strategy.ATTACHMENTS:self.assertFalse(any(b.get(c,'type')=='add_division' for c in nodes));continue
                    births=[c for c in nodes if b.get(c,'type')=='add_division'];heals=[c for c in nodes if b.get(c,'type')=='damage_division']
                    self.assertEqual(len(births),len(heals))
                    for birth,heal in zip(births,heals):
                        self.assertEqual(b.get(birth,'trigger'),b.get(heal,'trigger'))
                        self.assertEqual(b.get(birth,'which'),b.get(heal,'which'));self.assertIsNone(b.get(birth,'where'))

    def test_lost_position_or_peace_refunds_every_input_and_reopens(self):
        for kind in ('site','war','research','port'):
            w=world('ocean');before=copy.deepcopy(w.resources['JAP']);w.action('r15_pacific_or_ocean',0)
            if kind=='site':w.controlled[1667]='USA'
            elif kind=='war':w.wars.clear()
            elif kind=='research':w.country_tech['JAP']=set()
            else:w.buildings[1667,'naval_base']=0
            w.advance(210);self.assertEqual(w.resources['JAP'],before,kind)
            self.assertFalse(w.deployed_units);self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
            self.assertTrue(w.flags.get('JX_R15_PACIFIC_OR_OCEAN_WAIT'))
            self.assertFalse(w.action('r15_pacific_or_ocean',0));w.advance(90)
            self.assertFalse(w.flags.get('JX_R15_PACIFIC_OR_OCEAN_WAIT'))

    def test_winning_china_does_not_cancel_training_already_paid(self):
        w=world();self.assertTrue(w.action('r15_china_or_fleet',0));w.wars.clear();w.advance(180)
        self.assertEqual(len(w.deployed_units),3)
        self.assertTrue(w.flags['JX_R15_CHINA_OR_FLEET_CLOSED'])

    def test_shared_lock_cancel_and_old_callback_cannot_unlock_new_work(self):
        w=world();before=copy.deepcopy(w.resources['JAP']);w.action('r15_china_or_fleet',1)
        w.flags['JX_PACIFIC']=1;w.year=1943;w.addwar('JAP','USA')
        self.assertFalse(w.action('r15_pacific_or_ocean',1))
        self.assertTrue(w.action('r15_china_or_fleet',5))
        self.assertAlmostEqual(w.resources['JAP']['manpower'],before['manpower'])
        self.assertEqual(w.resources['JAP']['money'],before['money']-350)
        self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-1750)
        self.assertTrue(w.action('r15_pacific_or_ocean',1));self.assertTrue(w.flags['JX_R15_MAJOR_PENDING'])
        w.cached('r15_china_or_fleet_finish_1',0)
        self.assertTrue(w.flags['JX_R15_MAJOR_PENDING']);self.assertFalse(w.deployed_units)

    def test_leave_dismiss_and_no_diplomatic_or_modifier_changes(self):
        w=world();before=copy.deepcopy((w.resources,w.flags,w.wars,w.owned,w.masters))
        self.assertTrue(w.action('r15_china_or_fleet',2));self.assertEqual((w.resources,w.flags,w.wars,w.owned,w.masters),before)
        self.assertTrue(w.action('r15_china_or_fleet',3));self.assertFalse(w.action('r15_china_or_fleet',0))
        forbidden={'war','peace','alliance','country','independence','make_puppet','secedeprovince','free_manpower','build_cost','build_time','strength_cap','remove_units'}
        for k in strategy.REPORT['added']:
            for a in BY[k].actions:
                self.assertLess(len(a.gate),3000,k)
                for c in a.commands:self.assertNotIn(b.get(b.parse(b.resolve(c)),'type'),forbidden,k)
        for k in strategy.REPORT['roots']:self.assertLessEqual(len(BY[k].desc),1100)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StrategyReview))
    (b.HERE/'R15_STRATEGY_AUDIT.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,game_executed=False,roots=strategy.REPORT['roots']),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
