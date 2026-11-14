"""Adversarial offline checks for finite Allied reactions. No game launch."""
import copy,json,tempfile,unittest
from pathlib import Path
import build as b
from simulate import World,BY_KEY,BY_ID
import r15_enemy as e

e.apply();b.IDS.update({v.key:v.id for v in b.EVENTS})
BY_KEY.update({v.key:v for v in b.EVENTS});BY_ID.update({str(v.id):v for v in b.EVENTS})


class EnemyWorld(World):
    def __init__(self):
        super().__init__();self.year=1944;self.humans={'JAP'};self.ai_loads=[];self.groups_created=[]
        self.wars.clear()
        for row in e.REACTIONS:
            tag=row['enemy'];self.addwar('JAP',tag)
            self.country_tech[tag]={str(t) for unit,_,_ in row['packages'] for _,t,_ in e.model_options(unit)}
            self.resources[tag].update(energy=100000,metal=100000,oil=100000,money=100000,supplies=100000,manpower=10000)
            for p,_ in row['hubs']:
                self.owned[p]=self.controlled[p]=tag
                self.buildings[p,'naval_base']=self.buildings[p,'air_base']=10
        for p in (1734,1726,1432,1511):self.controlled[p]='JAP'
    def test(self,node,actor):
        out=[]
        for k,v in node:
            if k=='ai':out.append(actor not in self.humans if v=='yes' else actor in self.humans if v=='no' else v not in self.humans)
            else:out.append(super().test([(k,v)],actor))
        return all(out)
    def command(self,node,actor):
        gate=b.get(node,'trigger')
        if gate and not self.test(gate,actor):return
        kind=b.get(node,'type')
        if kind=='ai':self.ai_loads.append((actor,b.get(node,'which')))
        if kind=='add_corps':self.groups_created.append((actor,b.get(node,'value'),b.get(node,'which')))
        super().command(node,actor)
        if kind=='add_division':self.deployed_units[-1]['strength']=33
    def cached(self,key,index=0):
        for c in BY_KEY[key].actions[index].commands:self.command(b.parse(b.resolve(c)),BY_KEY[key].country)


def key(row,part):return 'r15_enemy_'+row['key']+'_'+part
def available(w,name):
    event=BY_KEY[name];return w.year>=event.year and w.test(b.parse(b.resolve(event.gate)),event.country)


class EnemyReview(unittest.TestCase):
    def paid(self,row):
        w=EnemyWorld();self.assertTrue(available(w,key(row,'threat')))
        self.assertTrue(w.action(key(row,'threat')));w.advance(30)
        self.assertTrue(available(w,key(row,'pay')));before=copy.deepcopy(w.resources[row['enemy']])
        self.assertTrue(w.action(key(row,'pay')))
        for resource,amount in row['bill'].items():self.assertEqual(w.resources[row['enemy']][resource],before[resource]-amount)
        return w
    def test_war_human_date_and_geography_gate_every_family(self):
        for row in e.REACTIONS:
            for issue in ('war','human','date','pacific','map'):
                w=EnemyWorld()
                if issue=='war':w.wars={p for p in w.wars if row['enemy'] not in p}
                elif issue=='human':w.humans.add(row['enemy'])
                elif issue=='date':w.year=1940
                elif issue=='pacific':w.flags.pop('JX_PACIFIC')
                else:
                    for p in (1734,1726,1607,1697,1432,1511):w.controlled[p]='ENG'
                self.assertFalse(available(w,key(row,'threat')),(row['key'],issue))
                before=copy.deepcopy(w.flags);w.cached(key(row,'threat'));self.assertEqual(w.flags,before)
    def test_thirty_day_assessment_cannot_be_bypassed(self):
        for row in e.REACTIONS:
            w=EnemyWorld();w.action(key(row,'threat'));before=copy.deepcopy(w.resources)
            w.cached(key(row,'assess'));w.cached(key(row,'pay'))
            self.assertEqual(w.resources,before);self.assertFalse(w.ai_loads)
            w.advance(29);self.assertFalse(available(w,key(row,'pay')))
            w.advance(1);self.assertTrue(available(w,key(row,'pay')));self.assertEqual(len(w.ai_loads),1)
    def test_poor_enemy_can_wait_and_later_pay_without_a_free_budget(self):
        for row in e.REACTIONS:
            w=EnemyWorld();w.resources[row['enemy']]['money']=0;w.action(key(row,'threat'));w.advance(30)
            before=copy.deepcopy(w.resources);w.dispatch(key(row,'pay'))
            self.assertEqual(w.resources,before);self.assertFalse(w.flags.get('JX_R15_E_'+row['key'].upper()+'_CLOSED'))
            w.resources[row['enemy']]['money']=row['bill']['money']
            self.assertTrue(available(w,key(row,'pay')));w.dispatch(key(row,'pay'))
            self.assertTrue(w.flags['JX_R15_E_'+row['key'].upper()+'_ORDERED'])
    def test_full_cost_once_and_no_early_or_duplicate_delivery(self):
        for row in e.REACTIONS:
            w=self.paid(row);before=copy.deepcopy(w.resources);w.cached(key(row,'pay'))
            self.assertEqual(w.resources,before);w.cached(key(row,'finish'));self.assertFalse(w.deployed_units)
            w.advance(row['days']-1);self.assertFalse(w.deployed_units)
            w.advance(1);expected=sum(count for _,count,_ in row['packages'])
            self.assertEqual(len(w.deployed_units),expected)
            self.assertTrue(all(u['strength']==100 and u['country']==row['enemy'] for u in w.deployed_units))
            snapshot=copy.deepcopy((w.deployed_units,w.resources));w.cached(key(row,'finish'))
            self.assertEqual((w.deployed_units,w.resources),snapshot)
    def test_all_missing_inputs_and_research_or_facilities_block_payment(self):
        for row in e.REACTIONS:
            for failure in tuple(row['bill'])+('research','facilities','ownership'):
                w=EnemyWorld();w.action(key(row,'threat'));w.advance(30)
                if failure in row['bill']:w.resources[row['enemy']][failure]=row['bill'][failure]-1
                elif failure=='research':w.country_tech[row['enemy']]=set()
                else:
                    for p,_ in row['hubs']:
                        if failure=='ownership':w.owned[p]='GER'
                        else:w.buildings[p,'naval_base']=w.buildings[p,'air_base']=0
                before=copy.deepcopy(w.resources);w.cached(key(row,'pay'))
                self.assertEqual(w.resources,before,(row['key'],failure));self.assertFalse(available(w,key(row,'pay')))
    def test_peace_or_lost_hubs_or_research_refund_exactly(self):
        for row in e.REACTIONS:
            for issue in ('peace','hubs','research','human'):
                w=self.paid(row);after=copy.deepcopy(w.resources[row['enemy']])
                if issue=='peace':w.wars.clear()
                elif issue=='research':w.country_tech[row['enemy']]=set()
                elif issue=='human':w.humans.add(row['enemy'])
                else:
                    for p,_ in row['hubs']:w.controlled[p]='JAP'
                w.advance(row['days']);self.assertFalse(w.deployed_units)
                for resource,amount in row['bill'].items():self.assertEqual(w.resources[row['enemy']][resource],after[resource]+amount)
                before=copy.deepcopy(w.resources);w.cached(key(row,'finish'));self.assertEqual(w.resources,before)
    def test_late_equipment_is_researched_and_dated_with_full_manpower_budget(self):
        for row in e.REACTIONS:
            w=self.paid(row);w.advance(row['days']);total=0
            for unit in w.deployed_units:
                choices=[(year,tech,model) for year,tech,model in e.model_options(unit['type']) if year<=w.year]
                expected=max(choices)[2];self.assertEqual(unit['model'],expected)
                model=b.getall(b.parse(b.read(b.SOURCE/'db/units/divisions'/(unit['type']+'.txt'))),'model')[expected]
                total+=b.num(model,'manpower')
            self.assertLessEqual(total,row['bill']['manpower'])
    def test_naval_transports_and_screens_are_born_in_one_group(self):
        for row in (e.REACTIONS[0],e.REACTIONS[2]):
            w=self.paid(row);w.advance(row['days'])
            naval=[g for g in w.groups_created if g[1]=='naval'];self.assertEqual(len(naval),1)
            self.assertTrue(any(u['type']=='transport' for u in w.deployed_units));self.assertTrue(any(u['type']=='destroyer' for u in w.deployed_units))
    def test_disappeared_recipient_closes_without_resurrection_gift(self):
        for row in e.REACTIONS:
            w=self.paid(row);w.countries.discard(row['enemy']);w.advance(row['days']+1)
            self.assertTrue(w.flags.get('JX_R15_E_'+row['key'].upper()+'_CLOSED'))
            w.countries.add(row['enemy']);w.cached(key(row,'finish'));self.assertFalse(w.deployed_units)
    def test_threat_reversal_abandons_unpaid_order_but_not_paid_training(self):
        for row in e.REACTIONS:
            w=EnemyWorld();w.action(key(row,'threat'));w.advance(30)
            for p in (1734,1726,1607,1697,1432,1511):w.controlled[p]='ENG'
            self.assertTrue(available(w,key(row,'abandoned')));w.dispatch(key(row,'abandoned'))
            self.assertFalse(available(w,key(row,'pay')))
            w=self.paid(row)
            for p in (1734,1726,1607,1697,1432,1511):w.controlled[p]='ENG'
            w.advance(row['days']);self.assertTrue(w.deployed_units)
    def test_safe_us_fallback_and_same_family_cannot_repeat(self):
        row=e.REACTIONS[0];w=self.paid(row);w.controlled[1886]='JAP';w.advance(row['days'])
        self.assertTrue(all(u['location']==1887 for u in w.deployed_units));self.assertFalse(available(w,key(row,'threat')))
    def test_released_clients_count_but_neutrals_and_independent_allies_do_not(self):
        for row in (e.REACTIONS[1],e.REACTIONS[2]):
            province=1607 if row['key']=='australia' else 1511
            tag='INO' if province==1607 else 'U83'
            self.assertIn(tag,e.client_controllers(province))
            w=EnemyWorld()
            if row['key']=='australia':w.controlled[1726]=w.controlled[1697]='AST'
            w.countries.add(tag);w.masters[tag]='JAP';w.groups[tag]='Japan';w.controlled[province]=tag
            self.assertTrue(available(w,key(row,'threat')))
            w.action(key(row,'threat'));w.advance(30);self.assertTrue(available(w,key(row,'pay')))
            w.dispatch(key(row,'pay'));w.advance(row['days']);self.assertTrue(w.deployed_units)
            for relationship in ('neutral','independent_ally','enemy'):
                z=EnemyWorld()
                if row['key']=='australia':z.controlled[1726]=z.controlled[1697]='AST'
                z.countries.add(tag);z.masters.pop(tag,None);z.groups.pop(tag,None);z.controlled[province]=tag
                if relationship=='independent_ally':z.groups[tag]='Japan'
                elif relationship=='enemy':z.masters[tag]='JAP';z.wars.add(frozenset(('JAP',tag)))
                self.assertFalse(available(z,key(row,'threat')),(row['key'],relationship))
    def test_client_release_during_assessment_or_after_funding_preserves_response(self):
        row=e.REACTIONS[2]
        for after_payment in (False,True):
            w=EnemyWorld();w.action(key(row,'threat'))
            if after_payment:w.advance(30);w.dispatch(key(row,'pay'))
            w.countries.add('U83');w.masters['U83']='JAP';w.groups['U83']='Japan';w.controlled[1511]='U83'
            if not after_payment:w.advance(30);self.assertTrue(available(w,key(row,'pay')));w.dispatch(key(row,'pay'))
            self.assertFalse(available(w,key(row,'abandoned')))
            w.advance(row['days']);self.assertEqual(len(w.deployed_units),9)
    def test_ai_plans_are_minimal_native_partials_and_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)
            first=e.install(b.SOURCE,target,b.read,b.write,b.parse,b.serialise)
            bytes_first={r['path']:(target/r['path']).read_bytes() for r in first}
            e.install(b.SOURCE,target,b.read,b.write,b.parse,b.serialise)
            for row,result in zip(e.REACTIONS,first):
                data=b.parse(b.read(target/result['path']));self.assertEqual([k for k,_ in data],[row['block']])
                block=b.get(data,row['block']);field='target' if row['block']=='invasion' else 'province_priorities'
                self.assertEqual([k for k,_ in block],[field]);values=dict(b.get(block,field))
                for p,v in row['priorities'].items():self.assertEqual(values[str(p)],str(v))
                self.assertEqual((target/result['path']).read_bytes(),bytes_first[result['path']])
    def test_idempotent_and_no_diplomatic_or_global_reward_commands(self):
        snapshot=copy.deepcopy(b.EVENTS);e.apply();self.assertEqual(b.EVENTS,snapshot)
        for event in b.EVENTS:
            if event.module!='r15_enemy':continue
            for a in event.actions:
                self.assertLess(len(a.gate),3000 if a.name else 20000)
                for c in a.commands:
                    self.assertNotIn(b.get(b.parse(b.resolve(c)),'type'),{'war','peace','country','secedeprovince','make_puppet','alliance','free_ic','free_manpower'})


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EnemyReview))
    report=dict(passed=result.wasSuccessful(),tests=result.testsRun,game_executed=False,reactive_families=3,ai_plans=[e.ai_path(r['key']) for r in e.REACTIONS])
    (b.HERE/'R15_ENEMY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
