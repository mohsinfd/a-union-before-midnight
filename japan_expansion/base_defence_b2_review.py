"""Read-only stage/save and documented-command tests; no game execution."""
import copy,json,unittest
from build import HERE,TARGET,read,parse,get,getall,resolve
from balance_b1_review import BWorld,BY_KEY
from apply_base_defence_b2 import STAGE,OUTPUT,SOURCE_SAVE
from apply_balance_b1 import countries,digest,identity
import campaign_balance as b

class B2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=parse(read(TARGET/'scenarios/save games'/SOURCE_SAVE));cls.new=parse(read(STAGE/OUTPUT))
        cls.report=json.loads((STAGE/'REVIEW.json').read_text())
    def world(self):
        w=BWorld();w.countries.add('CGX');w.masters['CGX']='JAP'
        for i,(p,name) in enumerate(b.BASE_GAPS,22):
            w.controlled[p]='CGX' if p==1365 else 'JAP'
            w.divisions[b.ISLAND_TYPE,i]={'actor':'JAP','active':False,'locked':True,'continent':'Asia'}
        return w
    def test_save_adds_only_ten_dormant_templates(self):
        oc=countries(self.old);nc=countries(self.new)
        for tag in oc:
            if tag!='JAP':self.assertEqual(nc[tag],oc[tag],tag)
        for k,v in oc['JAP']:
            if k!='landdivision':self.assertEqual(getall(nc['JAP'],k),getall(oc['JAP'],k),k)
        old=getall(oc['JAP'],'landdivision');new=getall(nc['JAP'],'landdivision')
        self.assertEqual(new[:len(old)],old);self.assertEqual(len(new)-len(old),10)
        for d in new[len(old):]:
            self.assertEqual(get(d,'max_strength'),'25');self.assertEqual(get(d,'strength'),'25')
            self.assertEqual(get(d,'locked'),'yes');self.assertIsNone(get(d,'extra'))
        self.assertEqual(len({identity(d) for d in new}),len(new))
    def test_save_migration_builder_emits_complete_profiles(self):
        # Scenario templates can omit derived values because the engine builds
        # them at scenario start. A migration must pack the values explicitly.
        from garrison_profiles import complete,vals
        from build import TARGET,serialise
        source=countries(self.old)['JAP'];_,templates=b.scenario_templates(serialise)
        completed=[complete(source,d,TARGET) for _,d in templates]
        self.assertEqual(len(completed),31)
        for d in completed:
            all_stats=[float(x) for x in vals(d,'all')]
            land=[float(x) for x in vals(d,'land')]
            self.assertEqual(len(all_stats),17);self.assertEqual(len(land),13)
            self.assertEqual(all_stats[0],25);self.assertEqual(all_stats[1],25)
            self.assertGreater(all_stats[3],0,'maximum organization')
            self.assertGreater(all_stats[7],0,'supply consumption')
            self.assertGreater(land[0],0,'defence')
            self.assertGreater(land[4],0,'soft attack')

    def test_december_b3_copy_has_all_repaired_profiles(self):
        from garrison_profiles import vals
        b3=STAGE.parent/'staged_garrison_b3'/'JAPAN_B3_1941_December_23.eug'
        c=countries(parse(b3.read_text(encoding='latin1')))['JAP'];units=[]
        for key,value in c:
            if key=='landdivision':units.append(value)
            elif key=='landunit':units.extend(getall(value,'division'))
        units=[d for d in units if get(get(d,'id'),'type')==str(b.ISLAND_TYPE)]
        self.assertEqual(len(units),31)
        for d in units:
            all_stats=[float(x) for x in vals(d,'all')]
            land=[float(x) for x in vals(d,'land')]
            self.assertEqual(all_stats[0],25);self.assertEqual(all_stats[1],25)
            self.assertGreater(all_stats[3],0);self.assertGreater(all_stats[7],0)
            self.assertGreater(land[0],0);self.assertGreater(land[4],0)
        port_arthur=next(r for r in getall(c,'convoy')
                         if get(get(r,'id'),'type')=='4712' and get(get(r,'id'),'id')=='4300')
        self.assertEqual(get(port_arthur,'transports'),'12')
        self.assertEqual(get(port_arthur,'supplies'),'yes')
        self.assertNotEqual(get(port_arthur,'oil'),'yes')
        added=[r for r in getall(c,'convoy') if get(get(r,'id'),'type')=='28634']
        self.assertEqual(len(added),17)
        self.assertTrue(all(get(r,'supplies')=='yes' and get(r,'oil')=='no' for r in added))
        self.assertEqual(sum(int(get(r,'transports')) for r in added)+12,436)
        self.assertEqual(get(c,'transports'),'296')
    def test_original_queues_preserved_plus_two_first_hour_completions(self):
        oq=get(get(self.old,'globaldata'),'queued_events');nq=get(get(self.new,'globaldata'),'queued_events')
        self.assertEqual(nq[:-2],oq)
        for q,key in zip(getall(nq,'event')[-2:],('base_gaps_b2_apply','haikou_b2_apply')):
            self.assertEqual(get(q,'id'),str(BY_KEY[key].id));self.assertEqual(get(q,'hour'),'1')
    def test_exact_combined_payment_and_no_repeated_rewards(self):
        w=self.world();old=w.resources['JAP'].copy()
        for key in ('base_gaps_b2_apply','haikou_b2_apply'):self.assertTrue(w.action(key))
        self.assertEqual(sum(d['active'] for d in w.divisions.values()),10)
        self.assertEqual(old['manpower']-w.resources['JAP']['manpower'],25)
        self.assertEqual(old['supplies']-w.resources['JAP']['supplies'],400)
        self.assertEqual(old['money']-w.resources['JAP']['money'],30)
        after=w.resources['JAP'].copy()
        for key in ('base_gaps_b2_apply','haikou_b2_apply'):self.assertFalse(w.action(key))
        self.assertEqual(w.resources['JAP'],after)
    def test_hostile_haikou_does_not_block_nine_other_bases(self):
        w=self.world();w.controlled[1365]='ENG';before=w.resources['JAP'].copy()
        self.assertTrue(w.action('base_gaps_b2_apply'));self.assertFalse(w.action('haikou_b2_apply'))
        self.assertEqual(sum(d['active'] for d in w.divisions.values()),9)
        self.assertEqual(before['manpower']-w.resources['JAP']['manpower'],22.5)
    def test_missing_template_or_budget_never_charges(self):
        for condition in ('missing','poor','lost'):
            w=self.world()
            if condition=='missing':del w.divisions[b.ISLAND_TYPE,22]
            elif condition=='poor':w.resources['JAP']['manpower']=22.49
            else:w.controlled[1338]='ENG'
            before=w.resources['JAP'].copy();self.assertFalse(w.action('base_gaps_b2_apply'))
            self.assertEqual(w.resources['JAP'],before);self.assertFalse(any(d['active'] for d in w.divisions.values()))
    def test_haikou_can_be_japanese_or_chinese_puppet_controlled(self):
        for owner in ('JAP','CGX','U87'):
            w=self.world();w.controlled[1365]=owner
            if owner!='JAP':w.masters[owner]='JAP'
            self.assertTrue(w.action('haikou_b2_apply'),owner)
        w=self.world();del w.masters['CGX'];self.assertFalse(w.action('haikou_b2_apply'))
    def test_future_scenario_adds_only_same_ten_templates(self):
        report=self.report
        from pathlib import Path
        prior=(Path(report['backup']) if report['state']=='installed' else TARGET)/'scenarios/1933/japan.inc'
        old=parse(read(prior));new=parse(read(STAGE/'scenarios/1933/japan.inc'))
        c=get(new,'country');ds=[d for d in getall(c,'landdivision') if get(get(d,'id'),'type')==str(b.ISLAND_TYPE)]
        self.assertEqual(len(ds),31)
        c[:]=[(k,v) for k,v in c if not(k=='landdivision' and get(get(v,'id'),'type')==str(b.ISLAND_TYPE) and int(get(get(v,'id'),'id'))>21)]
        self.assertEqual(new,old)
    def test_b1_input_unchanged(self):
        from pathlib import Path
        self.assertEqual(digest(Path(self.report['source'])),self.report['source_sha256'])
    def test_every_queued_jx_event_resolves_from_saved_registry(self):
        from save_event_registry import queued_jx_missing,ensure_modules
        text=read(STAGE/OUTPUT)
        self.assertEqual(queued_jx_missing(text,TARGET),[])
        self.assertEqual(ensure_modules(text,read(TARGET/'db/events.txt')),(text,[]))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(B2Tests))
    (HERE/'BASE_DEFENCE_B2_TESTS.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,
      'errors':len(result.errors),'failures':len(result.failures),'game_executed':False,
      'scope':'Staged save/scenario preservation and documented-command tests; not engine playtesting'},indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
