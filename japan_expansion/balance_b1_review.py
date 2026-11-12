"""Offline B1 regression tests, including the actual staged campaign."""
import copy,json,unittest
from collections import Counter
from pathlib import Path
from build import HERE,SOURCE,TARGET,read,parse,get,getall,serialise,resolve,prepare_catalog,EVENTS
from simulate import World,BY_KEY
import campaign_balance as b
from apply_balance_b1 import STAGE,OUTPUT,SAVE,countries,division_records,identity,unit_type,digest

class BWorld(World):
    def __init__(self):
        super().__init__();self.divisions={};self.vp_losses={}
    def test(self,node,actor):
        for k,v in node:
            if k=='division_exists' and (int(get(v,'type')),int(get(v,'id'))) not in self.divisions:return False
            if k=='lost_VP' and self.vp_losses.get(get(v,'country',actor),0)<float(get(v,'value')):return False
        return super().test([(k,v) for k,v in node if k not in ('division_exists','lost_VP')],actor)
    def command(self,n,actor):
        gate=get(n,'trigger')
        if gate and not self.test(gate,actor):return
        typ=get(n,'type');key=(int(get(n,'which',0)),int(get(n,'value',0))) if typ in ('activate_division','unlock_division') else None
        if typ=='activate_division':
            d=self.divisions[key];assert d['actor']==actor and not d['active'];d['active']=True;self.armies[actor]+=1
        elif typ=='unlock_division':
            if key in self.divisions:self.divisions[key]['locked']=False
        elif typ=='remove_units':
            for d in self.divisions.values():
                if d['actor']==actor and d['active'] and d['continent']==get(n,'value'):
                    d['active']=False;self.armies[actor]-=1
        elif typ=='free_oil':self.properties[actor,'free_oil']+=float(get(n,'value'))
        else:return super().command(n,actor)

class B1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((STAGE/'REVIEW.json').read_text())
        cls.original=parse(read(TARGET/'scenarios/save games'/SAVE))
        cls.new=parse(read(STAGE/OUTPUT));cls.cs=countries(cls.new)
    def test_original_and_unrelated_countries(self):
        self.assertEqual(digest(Path(self.report['source'])),self.report['source_sha256'])
        old=countries(self.original)
        for tag in old:
            if tag not in ('JAP','U87'):self.assertEqual(self.cs[tag],old[tag],tag)
    def test_actual_china_count_locks_and_separated_corps(self):
        rs=division_records(self.cs['U87']);self.assertEqual(len(rs),96)
        self.assertEqual(Counter(unit_type(d) for f,d in rs),{0:72,11:18,10:4,1:2})
        self.assertEqual(sum(bool(int(get(d,'flag'))&2) for f,d in rs),64)
        for f in getall(self.cs['U87'],'landunit'):
            self.assertEqual(len({bool(int(get(d,'flag'))&2) for d in getall(f,'division')}),1)
    def test_save_release_waves_target_exactly_locked_survivors(self):
        rs=division_records(self.cs['U87']);locked={identity(d) for f,d in rs if int(get(d,'flag'))&2}
        waves=json.loads((HERE/'china_legacy_b1.json').read_text())['stages']
        self.assertEqual([len(w) for w in waves],[32,32]);self.assertEqual({tuple(i) for w in waves for i in w},locked)
        q=get(get(self.new,'globaldata'),'queued_events')
        timers={int(get(e,'id')):int(get(e,'hour')) for e in getall(q,'event')}
        for stage in (1,2):self.assertEqual(timers[BY_KEY['cn_legacy_release_'+str(stage)].id],stage*360*24)
    def test_island_templates_are_capped_small_and_unbrigaded(self):
        ds=[d for d in getall(self.cs['JAP'],'landdivision') if get(get(d,'id'),'type')==str(b.ISLAND_TYPE)]
        self.assertEqual(len(ds),21)
        for d in ds:
            self.assertEqual(get(d,'strength'),'25');self.assertEqual(get(d,'max_strength'),'25')
            self.assertEqual(get(d,'locked'),'yes');self.assertIsNone(get(d,'extra'))
    def test_root_templates_do_not_replace_starting_armies(self):
        for rel,typ,count in [('scenarios/1933/china nationalist.inc',b.CHINA_TYPE,96),('scenarios/1933/japan.inc',b.ISLAND_TYPE,21)]:
            before=Path(self.report['backup'])/rel if self.report['state']=='installed' else TARGET/rel
            old=parse(read(before));new=parse(read(STAGE/rel));country=get(new,'country')
            added=[d for d in getall(country,'landdivision') if get(get(d,'id'),'type')==str(typ)]
            self.assertEqual(len(added),count);self.assertTrue(all(get(d,'dormant')=='yes' for d in added))
            country[:]=[(k,v) for k,v in country if not(k=='landdivision' and get(get(v,'id'),'type')==str(typ))]
            self.assertEqual(new,old)
    def root_world(self):
        w=BWorld();w.countries.add('U87');w.masters['U87']='JAP';w.flags['JX_china_SETTLED']=1
        w.groups['U87']='Japan';w.wars={x for x in w.wars if 'U87' not in x};w.controlled[1337]='U87';w.armies['U87']=169
        for i,(typ,model) in enumerate(b.CHINA_ROSTER,1):
            w.divisions[b.CHINA_TYPE,i]={'actor':'U87','active':False,'locked':True,'continent':None}
        for i in range(169):w.divisions[1,i]={'actor':'U87','active':True,'locked':False,'continent':'Asia'}
        return w
    def test_root_consolidation_and_timed_unlock(self):
        w=self.root_world();self.assertTrue(w.test(parse(resolve(BY_KEY['cn_reorganise'].gate)),'U87'))
        w.action('cn_reorganise');self.assertEqual(w.armies['U87'],96)
        self.assertEqual(sum(d['active'] and d['locked'] for d in w.divisions.values()),64)
        w.advance(360);self.assertEqual(sum(d['active'] and d['locked'] for d in w.divisions.values()),32)
        w.advance(360);self.assertEqual(sum(d['active'] and d['locked'] for d in w.divisions.values()),0)
    def test_small_army_or_missing_template_never_enters_destructive_reorganisation(self):
        w=self.root_world();w.armies['U87']=60
        self.assertFalse(w.test(parse(resolve(BY_KEY['cn_reorganise'].gate)),'U87'))
        w=self.root_world();del w.divisions[b.CHINA_TYPE,96]
        self.assertFalse(w.test(parse(resolve(BY_KEY['cn_reorganise'].gate)),'U87'))
    def test_independence_clears_locks_and_timers_do_not_regrant(self):
        w=self.root_world();w.action('cn_reorganise');del w.masters['U87']
        w.action('cn_independent_b1');self.assertFalse(any(d['active'] and d['locked'] for d in w.divisions.values()))
        w.advance(720);self.assertEqual(w.armies['U87'],96)
    def test_italian_help_is_once_only_independent_of_germany(self):
        w=BWorld();w.addwar('ITA','ENG');w.armies['ITA']=16;w.controlled[419]='ITA'
        german=copy.deepcopy(w.resources['GER']);japanese=copy.deepcopy(w.resources['JAP'])
        old=copy.deepcopy(w.resources['ITA']);self.assertTrue(w.action('ita_apply_b1'))
        self.assertEqual(w.armies['ITA'],28);self.assertEqual(w.resources['ITA']['oil']-old['oil'],4000)
        self.assertFalse(w.action('ita_apply_b1'));self.assertEqual(w.resources['GER'],german);self.assertEqual(w.resources['JAP'],japanese)
        self.assertEqual(w.properties['ITA','free_oil'],8);w.advance(360);self.assertEqual(w.properties['ITA','free_oil'],0)
    def test_island_payment_and_activation_cannot_repeat(self):
        w=BWorld()
        for i,(p,name) in enumerate(b.ISLANDS,1):
            w.controlled[p]='JAP';w.divisions[b.ISLAND_TYPE,i]={'actor':'JAP','active':False,'locked':True,'continent':'Oceania'}
        before=w.resources['JAP'].copy();self.assertTrue(w.action('island_muster_b1'))
        self.assertEqual(sum(d['active'] for d in w.divisions.values()),21)
        self.assertEqual(before['manpower']-w.resources['JAP']['manpower'],53)
        self.assertFalse(w.action('island_muster_b1'))
    def test_italian_ai_weights_and_priorities(self):
        root=parse(read(STAGE/'ai/jx/ita_recovery_b1.ai'))
        self.assertEqual(sum(float(v) for k,v in get(root,'military') if k!='relative_build_scheme'),100)
        self.assertEqual(get(root,'exp_force_ratio'),'0.0')
        for p in (STAGE/'ai').rglob('ITA*.ai'):
            g=get(parse(read(p)),'garrison')
            if g:
                keys=[k for k,v in get(g,'province_priorities',[])];self.assertEqual(len(keys),len(set(keys)))
    def test_future_roster_does_not_mix_locked_and_mobile_corps(self):
        commands=[parse(resolve(c)) for c in BY_KEY['cn_reorganise'].actions[0].commands]
        corps=[]
        for c in commands:
            if get(c,'type')=='add_corps':corps.append([])
            if get(c,'type')=='activate_division':corps[-1].append(int(get(c,'value')))
        self.assertEqual(len(corps),12)
        for group in corps:self.assertEqual(len({(i-1)//32 for i in group}),1)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(B1Tests))
    (HERE/'BALANCE_B1_TESTS.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'game_executed':False,'scope':'Staged source/save checks and documented-command model, not engine playtesting'},indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
