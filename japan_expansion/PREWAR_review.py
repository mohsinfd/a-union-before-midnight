"""Contract tests for all twelve prewar alternatives; no game execution."""
import unittest
from pathlib import Path
import build
import prewar_content as content

build.prepare_catalog()
BEFORE = {e.key:e.id for e in build.EVENTS}
content.append_events()
build.IDS.update({e.key:e.id for e in build.EVENTS})
import simulate
simulate.BY_KEY.update({e.key:e for e in build.EVENTS})
simulate.BY_ID.update({str(e.id):e for e in build.EVENTS})
from simulate import BY_KEY

MONTHS='january february march april may june july august september october november december'.split()


class World(simulate.World):
    def __init__(self):
        super().__init__()
        self.year=1940;self.month='december';self.wars.clear()
        self.flags.pop('JX_PACIFIC',None)

    def test(self,node,actor):
        tests=[]
        for key,value in node:
            if key=='month':tests.append(MONTHS.index(self.month)>=MONTHS.index(value))
            else:tests.append(super().test([(key,value)],actor))
        return all(tests)

    def command(self,node,actor):
        kind=build.get(node,'type')
        if kind=='max_amphib_mod':
            key=(actor,kind,None,None)
            mode=int(build.get(node,'when',0));value=float(build.get(node,'value'))
            if mode==1:self.properties[key]+=value
            elif mode==0:self.properties[key]=value
            else:self.properties[key]=1  # B&I misc.txt base assault limit
        elif kind in {'surface_detection','shore_attack','trickleback_mod','speed'}:
            self.properties[actor,kind,build.get(node,'which'),build.get(node,'where')]+=float(build.get(node,'value'))
        else:super().command(node,actor)


def select(w,key,index=0):
    event=BY_KEY[key]
    if event.gate and not w.test(build.parse(build.resolve(event.gate)),event.country):return False
    return w.action(key,index)


class PrewarReview(unittest.TestCase):
    def test_every_choice_cost_delay_exclusive_reward_and_duplicate_safety(self):
        for spec in content.programmes():
            for index,choice in enumerate(spec.choices):
                with self.subTest(programme=spec.key,choice=index):
                    w=World();before=w.resources['JAP'].copy()
                    self.assertTrue(select(w,spec.key,index))
                    for resource,value in choice.costs.items():
                        self.assertEqual(w.resources['JAP'][resource],before[resource]-value)
                    self.assertFalse(select(w,spec.key,1-index))
                    self.assertEqual(len(w.queue),1)
                    w.advance(spec.days-1)
                    self.assertFalse(w.flags.get('JX_'+spec.key+'_DONE'))
                    w.advance(1)
                    self.assertTrue(w.flags.get('JX_'+spec.key+'_DONE'))
                    self.assertFalse(w.flags.get('JX_'+spec.key+'_PENDING'))
                    snapshot=(dict(w.resources['JAP']),{k:v for k,v in w.properties.items() if v},
                              {k:v for k,v in w.buildings.items() if v})
                    w.dispatch(spec.key+f'_finish_{index}')
                    w.dispatch(spec.key+f'_finish_{1-index}')
                    self.assertEqual(snapshot,(dict(w.resources['JAP']),{k:v for k,v in w.properties.items() if v},
                                               {k:v for k,v in w.buildings.items() if v}))
                    self.assertFalse(select(w,spec.key,index))
                    self.assertFalse(w.orders)

    def test_every_missing_input_refuses_without_charge_or_queue(self):
        for spec in content.programmes():
            for index,choice in enumerate(spec.choices):
                for resource,value in choice.costs.items():
                    w=World();w.resources['JAP'][resource]=value-1
                    before=w.resources['JAP'].copy()
                    self.assertFalse(select(w,spec.key,index),(spec.key,index,resource))
                    self.assertEqual(w.resources['JAP'],before)
                    self.assertFalse(w.queue)

    def test_civilian_manpower_is_paid_and_exactly_refunded_if_site_lost(self):
        w=World();before=w.resources['JAP'].copy()
        self.assertTrue(select(w,'prewar_rural_works'))
        self.assertEqual(w.resources['JAP']['manpower'],before['manpower']-25)
        w.controlled[1557]='USA';w.advance(270)
        self.assertEqual(w.resources['JAP'],before)
        self.assertTrue(w.flags.get('JX_prewar_rural_works_CANCELLED'))
        w.dispatch('prewar_rural_works_finish_0')
        self.assertEqual(w.resources['JAP'],before)
        self.assertFalse(select(w,'prewar_rural_works'))

    def test_site_research_and_cap_failure_refund_both_building_branches(self):
        for key,index,mode in (
            ('prewar_navigation_trials',1,'cap'),
            ('prewar_navigation_trials',1,'research'),
            ('prewar_factory_dispersion',0,'site'),
            ('prewar_factory_dispersion',0,'cap'),
            ('prewar_factory_dispersion',1,'infra'),
        ):
            w=World();before=w.resources['JAP'].copy()
            self.assertTrue(select(w,key,index))
            if mode=='cap':w.buildings[1552 if key=='prewar_navigation_trials' else 1549,'flak']=10
            elif mode=='research':w.technologies=set()
            elif mode=='site':w.controlled[1549]='SOV'
            elif mode=='infra':w.buildings[1552,'infrastructure']=30
            w.advance(180 if key=='prewar_navigation_trials' else 270)
            self.assertEqual(w.resources['JAP'],before,(key,index,mode))
            self.assertFalse(w.flags.get('JX_'+key+'_DONE'))

    def test_no_early_or_unselected_receipt_but_funded_work_survives_pacific_war(self):
        w=World();select(w,'prewar_deck_commission',0)
        w.dispatch('prewar_deck_commission_finish_0')
        w.dispatch('prewar_deck_commission_finish_1')
        self.assertEqual(w.properties['JAP','morale','cag',None],0)
        self.assertTrue(w.flags.get('JX_prewar_deck_commission_PENDING'))
        w.flags['JX_PACIFIC']=1;w.addwar('JAP','USA')
        w.advance(240)
        self.assertEqual(w.properties['JAP','morale','cag',None],8)
        self.assertEqual(w.properties['JAP','naval_defense','carrier',None],0)

    def test_initial_1933_resources_can_fund_one_rural_choice(self):
        for index in (0,1):
            w=World();w.year=1933;w.month='april'
            w.resources['JAP'].update(money=100,supplies=500,metal=1000,energy=1000,oil=500,manpower=200)
            self.assertTrue(select(w,'prewar_rural_works',index))
            self.assertEqual(w.resources['JAP']['money'],55)
            self.assertEqual(w.resources['JAP']['supplies'],100)
            self.assertEqual(w.resources['JAP']['metal'],700)

    def test_date_war_dismissal_and_leave_are_non_spamming(self):
        for spec in content.programmes():
            w=World();w.year=spec.year-1
            self.assertFalse(select(w,spec.key))
            for enemy in ('USA','ENG'):
                w=World();w.addwar('JAP',enemy)
                self.assertFalse(select(w,spec.key))
            w=World();before=w.resources['JAP'].copy()
            self.assertTrue(select(w,spec.key,2));self.assertFalse(w.queue)
            self.assertEqual(w.resources['JAP'],before)
            self.assertTrue(select(w,spec.key,3));self.assertFalse(w.queue)
            self.assertFalse(select(w,spec.key))

    def test_vulnerability_direction_native_proof_and_all_models_stay_positive(self):
        native=(build.SOURCE/'db/events/Mods.txt').read_text(encoding='latin1')
        self.assertIn('type = naval_defense which = carrier value = -2 } # bonus',native)
        for unit in ('carrier','light_carrier'):
            models=build.getall(build.parse((build.SOURCE/'db/units/divisions'/f'{unit}.txt').read_text(encoding='latin1')),'model')
            for model in models:
                self.assertGreater(float(build.get(model,'seadefence'))-4,0)
                self.assertGreater(float(build.get(model,'maxspeed'))-1,0)
        rewards=content.programmes()[1].choices[1].rewards
        for text in rewards:
            node=build.parse(text)
            if build.get(node,'type')=='naval_defense':self.assertEqual(build.get(node,'value'),'-4')

    def test_amphibious_training_adds_to_existing_limit_instead_of_resetting(self):
        w=World();w.properties['JAP','max_amphib_mod',None,None]=5
        self.assertTrue(select(w,'prewar_landing_trials',0))
        w.advance(180)
        self.assertEqual(w.properties['JAP','max_amphib_mod',None,None],6)
        command=next(c for c in content.programmes()[3].choices[0].rewards if 'type = max_amphib_mod ' in c)
        self.assertEqual(build.get(build.parse(command),'when'),'1')

    def test_append_only_manual_only_and_no_diplomatic_or_custom_unit_commands(self):
        self.assertEqual(BEFORE,{e.key:e.id for e in build.EVENTS if e.key in BEFORE})
        count=len(build.EVENTS);content.append_events();self.assertEqual(len(build.EVENTS),count)
        new=[e for e in build.EVENTS if e.module==content.MODULE]
        self.assertEqual(len(new),18)
        self.assertEqual(sum(e.decision for e in new),6)
        for event in new:
            self.assertEqual(event.country,'JAP')
            if event.decision:
                self.assertTrue(event.manual_only)
                self.assertEqual(len(event.actions),4)
                self.assertIn('ai = no',event.gate)
            for action in event.actions:
                for text in action.commands:
                    node=build.parse(text)
                    self.assertNotIn(build.get(node,'type'),('war','peace','country','alliance','build_division','activate_unit_type','add_division','free_manpower','free_ic'))
                    self.assertNotIn(build.get(node,'which'),('d_01','d_10','d_11','d_12'))
            build.parse(build.compiled_event(event))


if __name__=='__main__':unittest.main(verbosity=2)
