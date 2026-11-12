"""Adversarial country-project state checks; no game launch."""
import copy
import json
import unittest
from pathlib import Path
from FLOW_review import HumanWorld
from simulate import BY_KEY
from build import EVENTS, parse, get, getall, resolve, compiled_event
import regional_content as rc


def state():
    w=HumanWorld();w.year=1942;w.addwar('JAP','CHI')
    for p in (1338,1317,1565,1647,1653,1636,1432,1438,1552):w.controlled[p]='JAP'
    w.groups['PHI']='Japan';w.masters['PHI']='JAP';w.wars.discard(frozenset(('JAP','PHI')))
    return w


def available(w,key):
    script=get(parse(compiled_event(BY_KEY[key])),'event')
    return w.year>=BY_KEY[key].year and w.test(get(script,'decision',[]),'JAP')


class RegionalTests(unittest.TestCase):
    def test_all_sixteen_choices_pay_deliver_once_and_create_no_orders(self):
        for p in rc.PROGRAMMES:
            for i,opt in enumerate(p['choices']):
                with self.subTest(key=p['key'],choice=i):
                    w=state();w.resources['JAP']['oil']=5000
                    before=copy.deepcopy(w.resources['JAP'])
                    self.assertTrue(available(w,p['key']))
                    self.assertTrue(w.action(p['key'],i));self.assertFalse(w.action(p['key'],i))
                    for typ,col in [('money','cash'),('supplies','stock'),('manpower','mp'),('metal','metal'),('energy','energy'),('oil','oil')]:
                        self.assertAlmostEqual(w.resources['JAP'][typ],before[typ]-opt[col])
                    w.advance(opt['days'])
                    self.assertTrue(w.flags.get('JX_'+p['key']+'_DONE'))
                    snapshot=(copy.deepcopy(w.resources),dict(w.types),dict(w.properties))
                    w.dispatch(p['key']+'_finish_'+str(i))
                    self.assertEqual(snapshot,(w.resources,dict(w.types),dict(w.properties)))
                    self.assertFalse(w.orders)
                    self.assertFalse(any('d_1' in str(k) for k in w.types))

    def test_no_money_or_manpower_starts_without_complete_bill(self):
        for p in rc.PROGRAMMES:
            for i,opt in enumerate(p['choices']):
                w=state();w.resources['JAP']['money']=0;before=copy.deepcopy(w.resources['JAP'])
                self.assertFalse(w.action(p['key'],i));self.assertEqual(w.resources['JAP'],before)
                if opt['mp']:
                    w=state();w.resources['JAP']['manpower']=opt['mp']-.01
                    self.assertFalse(w.action(p['key'],i))

    def test_loss_of_map_or_relationship_returns_all_inputs_once(self):
        for p in rc.PROGRAMMES:
            for i,opt in enumerate(p['choices']):
                with self.subTest(key=p['key'],choice=i):
                    w=state();before=copy.deepcopy(w.resources['JAP']);w.action(p['key'],i)
                    for site in (1338,1317,1565,1647,1653,1636,1432,1438,1552):w.controlled[site]='USA'
                    w.masters.pop('PHI',None);w.groups.pop('PHI',None)
                    w.advance(opt['days']);self.assertEqual(w.resources['JAP'],before)
                    self.assertFalse(w.flags.get('JX_'+p['key']+'_DONE'))
                    w.dispatch(p['key']+'_finish_'+str(i));self.assertEqual(w.resources['JAP'],before)

    def test_forged_other_branch_cannot_claim_or_refund_selected_branch(self):
        for p in rc.PROGRAMMES:
            w=state();w.action(p['key'],0);before=copy.deepcopy(w.resources['JAP'])
            w.dispatch(p['key']+'_finish_1');self.assertEqual(w.resources['JAP'],before)
            self.assertTrue(w.flags.get('JX_'+p['key']+'_PENDING'))
            w.dispatch(p['key']+'_finish_0');self.assertEqual(w.resources['JAP'],before)
            self.assertTrue(w.flags.get('JX_'+p['key']+'_PENDING'))

    def test_neutral_philippines_can_buy_shipping_without_inheriting_war(self):
        w=state();w.masters.pop('PHI');w.groups.pop('PHI');w.flags['JX_philippines_NEUTRAL']=1
        w.flags['JX_philippines_SETTLED']=1;w.access.add(('PHI','JAP'))
        wars=copy.deepcopy(w.wars)
        self.assertFalse(w.action('ph_island_agreement',0));self.assertTrue(w.action('ph_island_agreement',1))
        w.advance(120);self.assertEqual(w.wars,wars);self.assertNotIn('PHI',w.masters)
        self.assertEqual(w.properties['JAP','transport_pool','-1',None],160)

    def test_indonesia_and_malaya_exports_work_after_release_or_neutral_treaty(self):
        for tag,key,sites,offer in [('INO','indonesia',(1647,1636),'in_indonesian_exports'),('MLY','malaya',(1438,),'my_malayan_exports')]:
            for neutral in (False,True):
                w=state();w.countries.add(tag);w.wars.discard(frozenset(('JAP',tag)))
                if neutral:
                    w.masters.pop(tag,None);w.flags['JX_'+key+'_NEUTRAL']=1;w.flags['JX_'+key+'_SETTLED']=1
                    w.access.add((tag,'JAP'))
                else:w.masters[tag]='JAP'
                for p in sites:w.controlled[p]=tag;w.owned[p]=tag
                self.assertTrue(w.action(offer,1));w.advance(150)
                self.assertTrue(w.flags.get('JX_'+offer+'_DONE'))

    def test_research_is_required_and_models_mp_match_native_templates(self):
        for p in rc.PROGRAMMES:
            for i,opt in enumerate(p['choices']):
                units=[get(parse(c),'value') for c in opt['awards'] if get(parse(c),'type')=='add_division']
                if not units:continue
                w=state();w.technologies=set();self.assertFalse(w.action(p['key'],i))
                self.assertAlmostEqual(opt['mp'],sum(rc.MODELS[u]['mp'] for u in units))

    def test_oil_overstock_cancels_refunds_and_repair_service_expires_once(self):
        w=state();w.resources['JAP']['oil']=5000;w.action('in_indonesian_exports',0)
        paid=copy.deepcopy(w.resources['JAP']);w.resources['JAP']['oil']=12000;w.advance(150)
        self.assertFalse(w.flags.get('JX_in_indonesian_exports_DONE'))
        self.assertEqual(w.resources['JAP']['money'],paid['money']+260)
        self.assertEqual(w.resources['JAP']['oil'],12000)
        w=state();w.action('my_singapore_yards',0);w.advance(90)
        self.assertEqual(w.properties['JAP','repair_mod',None,None],20)
        w.advance(360);self.assertEqual(w.properties['JAP','repair_mod',None,None],0)
        w.dispatch('my_singapore_repair_end');self.assertEqual(w.properties['JAP','repair_mod',None,None],0)

    def test_close_and_dismiss_do_not_pay_or_loop_or_change_political_state(self):
        for p in rc.PROGRAMMES:
            w=state();before=copy.deepcopy(w.resources);wars=copy.deepcopy(w.wars)
            self.assertTrue(w.action(p['key'],2));self.assertFalse(w.queue)
            self.assertTrue(w.action(p['key'],3));self.assertEqual(w.resources,before);self.assertEqual(w.wars,wars)
            self.assertFalse(w.action(p['key'],0))

    def test_chinese_aid_has_material_reward_and_no_unfunded_queue(self):
        w=state();w.countries.add('U87');w.masters['U87']='JAP';w.controlled[1337]='U87'
        old=w.resources['U87'].copy();self.assertTrue(w.action('china_mission',1));w.advance(60)
        self.assertEqual(w.resources['U87']['manpower'],old['manpower']+35)
        self.assertEqual(w.resources['U87']['supplies'],old['supplies']+3000)
        self.assertFalse(w.orders);w.dispatch('china_mission_unit')
        self.assertEqual(w.resources['U87']['manpower'],old['manpower']+35)
        self.assertEqual(BY_KEY['china_mission'].year,1938)

    def test_chinese_aid_both_recipients_and_wrong_branch_are_guarded(self):
        for i,recipient in enumerate(('china_mission_aid','china_mission_unit')):
            w=state();w.countries.add('U87');w.masters['U87']='JAP'
            before=w.resources['U87'].copy();w.action('china_mission',i)
            w.dispatch('china_mission_finish_'+str(1-i));self.assertEqual(w.resources['U87'],before)
            w.dispatch('china_mission_unit' if i==0 else 'china_mission_aid');self.assertEqual(w.resources['U87'],before)
            w.advance(60);after=w.resources['U87'].copy();self.assertNotEqual(after,before)
            w.dispatch(recipient);self.assertEqual(w.resources['U87'],after)
        w=state();w.flags['JX_china_mission_PENDING']=1;before=w.resources['JAP'].copy()
        w.history[str(BY_KEY['china_mission'].id)]=w.day
        w.dispatch('china_mission_finish_0');self.assertEqual(w.resources['JAP'],before)
        w.advance(60)
        w.dispatch('china_mission_finish_0');self.assertEqual(w.resources['JAP']['money'],before['money']+120)
        w.dispatch('china_mission_finish_1');self.assertEqual(w.resources['JAP']['money'],before['money']+120)

    def test_absent_philippines_can_be_settled_during_usa_only_war(self):
        from build import source_country
        _,provinces=source_country('PHI')
        for choice in (0,2):
            w=state();w.countries.discard('PHI');w.masters.pop('PHI',None);w.groups.pop('PHI',None)
            w.wars={frozenset(('JAP','USA'))}
            for p in provinces:w.owned[p]='USA';w.controlled[p]='JAP'
            self.assertTrue(available(w,'philippines'));self.assertTrue(w.action('philippines',choice));w.advance(12)
            self.assertIn('PHI',w.countries);self.assertTrue(w.flags.get('JX_philippines_SETTLED'))
            self.assertTrue(w.atwar('JAP','USA'))
            self.assertEqual(w.masters.get('PHI'),'JAP' if choice==0 else None)
            w.owned[1565]='USA';w.controlled[1565]='USA';w.dispatch('philippines_land_USA')
            self.assertEqual(w.owned[1565],'USA')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RegionalTests))
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'programmes':len(rc.PROGRAMMES),'choices':sum(len(p['choices']) for p in rc.PROGRAMMES),
            'models':rc.MODELS,'game_launched':False}
    Path(__file__).with_name('REGIONAL_CONTENT_TESTS.json').write_text(json.dumps(report,indent=2)+'\n')
    rc.documentation(Path(__file__).with_name('COUNTRY_CAMPAIGNS.md'))
    raise SystemExit(not result.wasSuccessful())
