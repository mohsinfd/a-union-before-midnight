"""Native-contract cold checks, independent of the older permissive model."""
import copy
import re
import unittest
import build
import final_event_integrity as integrity

build.prepare_catalog()
BASE_IDS={e.key:e.id for e in build.EVENTS}
integrity.apply()

from EVENT_ACCESSIBILITY_matrix import AuditWorld, PROFILES, fixture
from EVENT_ACCESSIBILITY_review import available
from simulate import BY_KEY
import prewar_content
import regional_content


class NativeWorld(AuditWorld):
    def __init__(self):
        super().__init__();self.current=dict(self.buildings);self.year=1933;self.month=3
        self.wars.clear();self.flags.pop('JX_PACIFIC',None)
    def test(self,node,actor):
        result=[]
        for k,v in node:
            if k=='building':
                sizes=self.current if build.get(v,'when')=='now' else self.buildings
                result.append(sizes.get((int(build.get(v,'province')),build.get(v,'type')),0)>=float(build.get(v,'value')))
            else:result.append(super().test([(k,v)],actor))
        return all(result)
    def command(self,node,actor):
        gate=build.get(node,'trigger')
        if build.get(node,'type')=='max_amphib_mod' and (not gate or self.test(gate,actor)):
            slot=(actor,'max_amphib_mod',build.get(node,'which'),build.get(node,'where'))
            value=float(build.get(node,'value'));mode=int(build.get(node,'when',0))
            self.properties[slot]=self.properties[slot]+value if mode==1 else value
            return
        return super().command(node,actor)


def fingerprint(w):
    return copy.deepcopy((dict(w.resources),dict(w.flags),dict(w.properties),dict(w.types),
                          list(w.orders),dict(w.armies),dict(w.navies),dict(w.buildings),
                          list(getattr(w,'deployed_units',[]))))


class FinalIntegrityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.worlds={(p,y):fixture(p,y) for p,y in PROFILES}

    def witness(self,key,index):
        for w in self.worlds.values():
            if available(w,key) and w.test(build.parse(build.resolve(BY_KEY[key].actions[index].gate)),'JAP'):
                return copy.deepcopy(w)
        self.fail('No compiled-eligible funded witness: '+key+' choice '+str(index))

    def test_ids_preserved_and_hook_is_idempotent(self):
        legacy=[e for e in build.EVENTS if e.id<=28601822 and not e.module.startswith('unique_unit_')]
        self.assertEqual(len(legacy),1773)
        self.assertGreaterEqual(len(build.EVENTS),1822)
        self.assertEqual(BASE_IDS,{e.key:e.id for e in build.EVENTS})
        before=copy.deepcopy(build.EVENTS);integrity.apply();self.assertEqual(build.EVENTS,before)

    def test_native_manual_readiness_fallback_is_exercised_not_assumed_true(self):
        w=self.witness('first_industry',0)
        self.assertTrue(available(w,'first_industry'))
        clone=copy.deepcopy(BY_KEY['first_industry']);clone.ready=''
        script=build.get(build.parse(build.compiled_event(clone)),'event')
        self.assertTrue(w.test(build.get(script,'decision'),'JAP'))
        ready=build.get(script,'decision_trigger',[]) or build.get(script,'trigger',[])
        self.assertFalse(w.test(ready,'JAP'),'An empty ready section falls back to the disabled automatic trigger')
        for e in build.EVENTS:
            if e.country=='JAP' and e.decision:
                script=build.get(build.parse(build.compiled_event(e)),'event')
                self.assertTrue(build.get(script,'decision_trigger'),e.key)

    def test_prewar_month_year_and_poor_player_close_are_real(self):
        w=NativeWorld();w.month=2
        self.assertFalse(available(w,'prewar_rural_works'));w.month=3
        self.assertTrue(available(w,'prewar_rural_works'))
        w.year=1934;w.month=0;self.assertTrue(available(w,'prewar_rural_works'))
        w.resources['JAP'].update(money=0,supplies=0,metal=0,manpower=0)
        self.assertTrue(available(w,'prewar_rural_works'))
        self.assertFalse(w.action('prewar_rural_works',0));self.assertFalse(w.action('prewar_rural_works',1))
        self.assertTrue(w.action('prewar_rural_works',2))

    def test_amphibious_award_adds_one_to_nonzero_limit_in_native_when_mode(self):
        w=NativeWorld();w.year=1936;w.month=4
        slot=('JAP','max_amphib_mod',None,None);w.properties[slot]=5
        self.assertTrue(available(w,'prewar_landing_trials'));self.assertTrue(w.action('prewar_landing_trials',0))
        w.advance(180);self.assertEqual(w.properties[slot],6)
        commands=BY_KEY['prewar_landing_trials_finish_0'].actions[0].commands
        award=next(build.parse(c) for c in commands if build.get(build.parse(c),'type')=='max_amphib_mod')
        self.assertEqual(build.get(award,'when'),'1')

    def test_current_infrastructure_floor_and_maximum_capacity_are_distinct(self):
        for maximum,damaged,repaired in ((60,20,31),(.6,.2,.31)):
            w=NativeWorld();w.buildings[1557,'infrastructure']=maximum;w.current[1557,'infrastructure']=damaged
            before=w.resources['JAP'].copy()
            self.assertFalse(w.action('prewar_rural_works',0));self.assertEqual(w.resources['JAP'],before)
            w.current[1557,'infrastructure']=repaired;self.assertTrue(w.action('prewar_rural_works',0))
        v=NativeWorld();v.buildings[1557,'ic']=199;v.current[1557,'ic']=20
        self.assertFalse(v.action('prewar_rural_works',0),'Damaged IC does not create room above maximum capacity')
        r=NativeWorld();r.year=1942;r.flags['JX_PACIFIC']=1
        r.owned[1726]=r.controlled[1726]='JAP'
        r.buildings[1726,'infrastructure']=100;r.current[1726,'infrastructure']=60
        self.assertFalse(r.action('rabaul_workshops',0),'Infrastructure expansion still tests maximum room')

    def test_all_16_new_programmes_both_branches_early_wrong_and_duplicate_callbacks(self):
        specs=[(p['key'],[c['days'] for c in p['choices']]) for p in regional_content.PROGRAMMES]
        specs += [(p.key,[p.days,p.days]) for p in prewar_content.programmes()]
        specs += [('usc_replacements',[60,60]),('usc_commitment',[60,60])]
        self.assertEqual(len(specs),16)
        for key,days in specs:
            for i in (0,1):
                with self.subTest(programme=key,choice=i):
                    w=self.witness(key,i);self.assertTrue(w.action(key,i))
                    expected=fingerprint(w)
                    w.dispatch(key+'_finish_'+str(1-i));self.assertEqual(fingerprint(w),expected)
                    w.dispatch(key+'_finish_'+str(i));self.assertEqual(fingerprint(w),expected)
                    w.advance(days[i]-1);self.assertFalse(w.flags.get('JX_'+key+'_DONE'))
                    w.advance(1);self.assertTrue(w.flags.get('JX_'+key+'_DONE'))
                    finished=fingerprint(w)
                    w.dispatch(key+'_finish_'+str(i));w.dispatch(key+'_finish_'+str(1-i))
                    self.assertEqual(fingerprint(w),finished)

    def test_new_chinese_aid_receivers_cannot_deliver_early_or_cross_branches(self):
        for i,receiver in enumerate(('china_mission_aid','china_mission_unit')):
            w=self.witness('china_mission',i);self.assertTrue(w.action('china_mission',i));before=fingerprint(w)
            w.dispatch(receiver);w.dispatch(('china_mission_unit','china_mission_aid')[i])
            self.assertEqual(fingerprint(w),before)
            w.dispatch('china_mission_finish_'+str(1-i));self.assertEqual(fingerprint(w),before)
            w.advance(60);self.assertTrue(w.flags.get('JX_china_mission_DONE'))
            delivered=fingerprint(w);w.dispatch(receiver);self.assertEqual(fingerprint(w),delivered)

    def test_us_superseded_unselected_jobs_refund_once_only_when_due(self):
        for key,cash,stock in (('usc_replacements',200,2500),('usc_commitment',250,4000)):
            w=self.witness(key,0)
            w.flags['JX_'+key+'_PENDING']=1
            w.history[str(BY_KEY[key].id)]=w.day
            before=w.resources['JAP'].copy();w.dispatch(key+'_finish_0')
            self.assertEqual(w.resources['JAP'],before)
            w.day+=60;w.dispatch(key+'_finish_0')
            self.assertEqual(w.resources['JAP']['money'],before['money']+cash)
            self.assertEqual(w.resources['JAP']['supplies'],before['supplies']+stock)
            refunded=w.resources['JAP'].copy();w.dispatch(key+'_finish_1');w.dispatch(key+'_finish_0')
            self.assertEqual(w.resources['JAP'],refunded)

    def test_new_due_guards_have_saved_source_dates_and_triggered_receivers_no_dates(self):
        ids={str(e.id):e for e in build.EVENTS}
        def visit(node):
            for k,v in node:
                if k=='event' and isinstance(v,list) and build.get(v,'days') is not None:
                    parent=ids[build.get(v,'id')]
                    compiled=build.get(build.parse(build.compiled_event(parent)),'event')
                    self.assertEqual(build.get(compiled,'save_date'),'yes',parent.key)
                if isinstance(v,list):visit(v)
        for e in build.EVENTS:
            if e.module not in {'prewar_content','country_campaigns','us_campaign_content'}:continue
            script=build.get(build.parse(build.compiled_event(e)),'event');visit(script)
            if e.triggered:
                self.assertIsNone(build.get(script,'date'),e.key)
                self.assertIsNone(build.get(script,'offset'),e.key)

    def test_native_documentation_supports_country_ai_global_flags_and_readiness(self):
        text=build.read(build.GAME/'Modding documentation/event commands.txt')
        for phrase in ('ai = [yes/no/country tag]','Sets Global flag, visible for all countries',
                       'If decision_trigger = { } section doesn\'t exist or is empty, it will use trigger = { } instead.',
                       'when = now for current size, else - max size','save_date = yes',
                       'max_amphib_mod to value / 1 - add value'):
            self.assertIn(phrase,text)

    def test_registered_source_modules_and_engine_loaded_localisation_have_all_keys(self):
        # Structural source proof. Installed byte equivalence is checked by
        # the parent after rebuilding these corrections into the mod.
        payload=build.localisation();keys={line.split(';')[0] for line in payload.splitlines()}
        for e in build.EVENTS:
            if e.module not in {'prewar_content','country_campaigns','us_campaign_content'}:continue
            script=build.get(build.parse(build.compiled_event(e)),'event')
            for field in ('name','desc'):
                value=build.get(script,field)
                if value!='AI_EVENT':self.assertIn(value,keys)
            for a in build.getall(script,'action'):
                name=build.get(a,'name')
                if name!='ACTION_NAME_OK':self.assertIn(name,keys)
        import localisation_support
        self.assertIn('mods.csv',localisation_support.ENGINE_CSV_NAMES)
        self.assertIn(b'config\\mods.csv',(build.GAME/'Darkest Hour.exe').read_bytes())

    def test_actual_installed_registration_and_loaded_key_resolution(self):
        scene=build.read(build.TARGET/'scenarios/1933.eug')
        self.assertRegex(scene,r'include\s*=\s*"db\\events\.txt"')
        index=build.read(build.TARGET/'db/events.txt')
        import localisation_support
        names=localisation_support.loaded_names(build.TARGET,build.GAME,build.read)
        for module in ('prewar_content','country_campaigns','us_campaign_content'):
            self.assertIn('db\\events\\japan_rising\\'+module+'.txt',index)
            entries=build.getall(build.parse(build.read(build.TARGET/'db/events/japan_rising'/(module+'.txt'))),'event')
            ids=[build.get(e,'id') for e in entries]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(set(ids),{str(e.id) for e in build.EVENTS if e.module==module})
            for e in entries:
                for key in ('name','desc'):
                    value=build.get(e,key)
                    if value!='AI_EVENT':self.assertTrue(names.get(value),value)
                for a in build.getall(e,'action'):
                    value=build.get(a,'name')
                    if value!='ACTION_NAME_OK':self.assertTrue(names.get(value),value)


if __name__=='__main__':unittest.main(verbosity=2)
