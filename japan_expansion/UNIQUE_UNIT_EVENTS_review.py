"""Independent R12 free-issue, research-order and installed registry audit."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from functools import lru_cache
from PIL import Image
import build
from simulate import World, BY_KEY
import unique_divisions as divisions
import unique_attachments as attachments
import unique_unit_events as introductions

build.prepare_catalog()
ENTRIES={**divisions.CLASSES,**attachments.ATTACHMENTS}
APPS={}
for path in (build.SOURCE/'db/tech').glob('*.txt'):
    for tree in build.getall(build.parse(build.read(path)),'technology'):
        for app in build.getall(tree,'application'):APPS[int(build.get(app,'id'))]=(path.name,app)
ALL_TECH={str(t) for t in APPS}


class ColdWorld(World):
    def __init__(self,year=1950,techs=None):
        super().__init__();self.year=year;self.humans={'JAP'};self.wars.clear();self.brigades=[]
        self.country_tech['JAP']=set(ALL_TECH if techs is None else map(str,techs))
        for actor in ('JAP','USA'):
            for unit in ENTRIES:self.models[actor,unit].add(0)  # Native implicit model zero; availability is separate.
        for p,_ in introductions.HOME_PORTS+introductions.HOME_AIRFIELDS:
            self.owned[p]=self.controlled[p]='JAP'
            self.buildings[p,'air_base']=self.buildings[p,'naval_base']=1
    def test(self,node,actor):
        results=[]
        for k,v in node:
            if k=='ai':results.append((actor not in self.humans) if v=='yes' else ((actor in self.humans) if v=='no' else v not in self.humans))
            else:results.append(super().test([(k,v)],actor))
        return all(results)
    def command(self,node,actor):
        condition=build.get(node,'trigger')
        if condition and not self.test(condition,actor):return
        kind=build.get(node,'type');unit=build.get(node,'value');which=build.get(node,'which')
        if kind=='add_brigade' and unit in ENTRIES:
            model=int(build.get(node,'when'))
            assert (actor,unit) in self.activated and model in self.models[actor,unit],('Unavailable attachment model',unit,model)
            self.brigades.append((actor,unit,model));return
        if kind=='add_division' and unit in ENTRIES:
            model=int(build.get(node,'when'))
            assert (actor,unit) in self.activated and model in self.models[actor,unit],('Unavailable division model',unit,model)
            self.types[actor,unit]+=1
            # Deliberately start damaged: named native healing must restore only this new formation.
            self.deployed_units.append(dict(country=actor,name=which,type=unit,model=model,strength=1,max_strength=100,location=self.current_corps.get(actor)))
            return
        if kind in divisions.UNIT_EFFECTS:
            amount=float(build.get(node,'value',0));where=build.get(node,'where')
            if kind in {'build_cost','build_time','manpower'} and where=='relative':
                field={'build_cost':'cost','build_time':'buildtime','manpower':'manpower'}[kind]
                base=build.getall(build.parse(build.read(build.SOURCE/'db/units/divisions'/f'{which}.txt')),'model')[0]
                amount*=float(build.get(base,field))/100;where=None
            self.properties[actor,kind,which,where]+=amount;return
        return super().command(node,actor)


def eligible(w,key):
    e=BY_KEY[key];script=build.get(build.parse(build.compiled_event(e)),'event')
    return w.year>=e.year and w.year<=1950 and w.test(build.get(script,'trigger',[]),e.country)


def owner(unit):return divisions if unit in divisions.CLASSES else attachments
def selected(unit,w):return max(i for i,g in introductions.latest_conditions(ENTRIES[unit]) if w.test(build.parse(g),'JAP'))
def snapshot(w):return copy.deepcopy((w.resources,w.flags,w.properties,w.models,w.activated,w.brigades,w.deployed_units))


@lru_cache(None)
def installed_file_commands(filename):
    root=build.parse(build.read(build.TARGET/'db/tech'/filename))
    return {int(build.get(app,'id')):[c for c in build.getall(build.get(app,'effects',[]),'command')
            if build.get(c,'which') in ENTRIES or str(build.get(c,'which','')).startswith('JX_UNIQUE_')]
            for t in build.getall(root,'technology') for app in build.getall(t,'application')}


def installed_commands(tid):return installed_file_commands(APPS[tid][0])[tid]


class DeferredWorld(ColdWorld):
    """Human follow-up actions execute only after the parent action ends."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.human_waiting=[]
    def command(self,node,actor):
        condition=build.get(node,'trigger')
        if condition and not self.test(condition,actor):return
        if build.get(node,'type')=='trigger':
            target=next(e.key for e in build.EVENTS if str(e.id)==str(build.get(node,'which')))
            self.human_waiting.append(target);return
        return super().command(node,actor)
    def acknowledge(self):
        key=self.human_waiting.pop(0)
        return self.dispatch(key)


class UniqueUnitReview(unittest.TestCase):
    def test_deferred_human_activation_finishes_before_any_gift_for_all_six(self):
        for unit,info in ENTRIES.items():
            for year in (info['year'],1950):
                with self.subTest(unit=unit,year=year):
                    w=DeferredWorld(year);before=w.resources['JAP'].copy();key='unique_intro_'+unit
                    w.dispatch(key)
                    self.assertTrue(w.flags['JX_'+introductions.progress(unit)])
                    self.assertFalse(w.flags.get('JX_'+introductions.done(unit)))
                    self.assertNotIn(('JAP',unit),w.activated)
                    self.assertFalse(w.brigades or w.deployed_units)
                    self.assertFalse(eligible(w,key))
                    w.acknowledge()
                    self.assertIn(('JAP',unit),w.activated)
                    self.assertTrue(w.flags['JX_'+introductions.done(unit)])
                    self.assertFalse(w.flags.get('JX_'+introductions.progress(unit)))
                    self.assertEqual(w.resources['JAP'],before)
                    self.assertEqual(len(w.deployed_units) if unit in divisions.CLASSES else len(w.brigades),1 if unit in divisions.CLASSES else 2)

    def test_cached_completion_commands_cannot_duplicate_gifts_or_bonuses(self):
        for unit,info in ENTRIES.items():
            w=DeferredWorld(1950);w.dispatch('unique_intro_'+unit)
            helper=BY_KEY['unique_activate_'+unit]
            cached=[build.parse(build.resolve(c)) for c in helper.actions[0].commands]
            w.acknowledge();after=snapshot(w)
            for c in cached:w.command(c,'JAP')
            self.assertEqual(snapshot(w),after,unit)
            w.dispatch('unique_activate_'+unit)
            self.assertEqual(snapshot(w),after,unit)

    def test_base_lost_during_human_wait_resets_request_without_losing_gift(self):
        for unit,info in divisions.CLASSES.items():
            w=DeferredWorld(info['year']);key='unique_intro_'+unit
            w.dispatch(key)
            sites=introductions.HOME_PORTS if info['base']=='destroyer' else introductions.HOME_AIRFIELDS
            kind='naval_base' if info['base']=='destroyer' else 'air_base'
            for p,_ in sites:
                if info['base']=='infantry':w.controlled[p]='ENG'
                else:w.buildings[p,kind]=0
            before=w.resources['JAP'].copy();w.acknowledge()
            self.assertFalse(w.flags.get('JX_'+introductions.done(unit)))
            self.assertFalse(w.flags.get('JX_'+introductions.progress(unit)))
            self.assertFalse(w.deployed_units)
            p,_=sites[-1];w.buildings[p,kind]=1;w.controlled[p]='JAP'
            w.dispatch(key);w.acknowledge()
            self.assertEqual((w.deployed_units[0]['location'],w.deployed_units[0]['strength']),(p,100))
            self.assertEqual(w.resources['JAP'],before)

    def test_original_1773_ids_and_six_compact_automatic_introductions(self):
        self.assertEqual(len(introductions.REPORT['original_ids']),1773)
        for key,value in introductions.REPORT['original_ids'].items():self.assertEqual(BY_KEY[key].id,value)
        self.assertEqual(len(introductions.REPORT['introductions']),10)
        for key in introductions.REPORT['introductions']:
            e=BY_KEY[key];self.assertFalse(e.decision);self.assertLess(len(e.desc),1100)
            for a in e.actions:self.assertLess(len(a.commands),20)
        self.assertEqual(BY_KEY['unique_intro_d_14'].art,'unique_patrol_early')

    def test_all_six_free_issues_work_in_peace_and_never_charge_national_pools(self):
        for unit,info in ENTRIES.items():
            with self.subTest(unit=unit):
                w=ColdWorld(info['year']);before=w.resources['JAP'].copy();model=selected(unit,w)
                key='unique_intro_'+unit;self.assertTrue(eligible(w,key));w.dispatch(key)
                self.assertEqual(w.resources['JAP'],before)
                self.assertTrue(w.flags['JX_'+introductions.done(unit)])
                self.assertIn(('JAP',unit),w.activated)
                if unit in divisions.CLASSES:
                    self.assertEqual([(u['type'],u['model'],u['strength']) for u in w.deployed_units],[(unit,model,100)])
                else:self.assertEqual(w.brigades,[('JAP',unit,model)]*2)
                after=snapshot(w);self.assertFalse(w.action(key));w.dispatch('unique_activate_'+unit)
                self.assertEqual(snapshot(w),after)

    def test_missing_sites_wait_without_consuming_first_issue_and_fallback_is_operational(self):
        for unit,info in divisions.CLASSES.items():
            w=ColdWorld(info['year']);sites=introductions.HOME_PORTS if info['base']=='destroyer' else introductions.HOME_AIRFIELDS
            kind='naval_base' if info['base']=='destroyer' else 'air_base'
            for p,_ in sites:
                if info['base']=='infantry':w.controlled[p]='ENG'
                else:w.buildings[p,kind]=0
            key='unique_intro_'+unit;self.assertFalse(eligible(w,key))
            w.flags['JX_'+introductions.progress(unit)]=1;w.dispatch('unique_activate_'+unit)
            self.assertNotIn(('JAP',unit),w.activated);self.assertFalse(w.flags.get('JX_'+introductions.done(unit)))
            p,_=sites[2];w.buildings[p,kind]=1;w.controlled[p]='JAP';self.assertTrue(eligible(w,key));w.dispatch(key)
            self.assertEqual(w.deployed_units[0]['location'],p);self.assertEqual(w.deployed_units[0]['strength'],100)

    def test_research_year_controller_and_independence_are_real_gates(self):
        for unit,info in ENTRIES.items():
            key='unique_intro_'+unit
            w=ColdWorld(info['year']-1);self.assertFalse(eligible(w,key));self.assertFalse(w.action(key))
            w=ColdWorld(info['year'],techs=[]);self.assertFalse(eligible(w,key))
            w=ColdWorld(info['year']);w.humans=set();self.assertFalse(eligible(w,key))
            w=ColdWorld(info['year']);w.masters['JAP']='USA';self.assertFalse(eligible(w,key))

    def test_early_research_does_not_advance_historical_models_or_block_initial_gift(self):
        for unit,info in ENTRIES.items():
            for tech,index in info['techpairs']:
                year=info['years'][index]
                if year>1950:continue
                w=ColdWorld(year);self.assertEqual(selected(unit,w),index)
                w.dispatch('unique_intro_'+unit)
                self.assertEqual(w.models['JAP',unit],{index})
                if index:
                    previous=ColdWorld(year-1)
                    if previous.year>=info['year']:
                        self.assertLess(selected(unit,previous),index)
                        previous.dispatch('unique_intro_'+unit)
                        previous.year=year
                        for key in introductions.REPORT['upgrade_resolvers']:
                            if eligible(previous,key):previous.dispatch(key)
                        self.assertEqual(previous.models['JAP',unit],{index})

    def test_sparse_cross_tree_research_and_later_lower_tech_do_not_downgrade(self):
        for unit,knowledge,later in [('b_01',{3060,3080},12000),('b_03',{2050,1630},2060)]:
            w=ColdWorld(1950,knowledge);w.dispatch('unique_intro_'+unit)
            expected=selected(unit,w);self.assertEqual(w.models['JAP',unit],{expected})
            commands=installed_commands(later);self.assertTrue(commands)
            for c in commands:w.command(c,'JAP')
            w.country_tech['JAP'].add(str(later))
            self.assertEqual(w.models['JAP',unit],{expected})

    def test_all_installed_research_hooks_before_or_after_unlock_have_same_bonuses(self):
        for unit,info in ENTRIES.items():
            with self.subTest(unit=unit):
                before=ColdWorld();before.dispatch('unique_intro_'+unit)
                after=ColdWorld(1950,{info['tech']});after.dispatch('unique_intro_'+unit)
                for tid in sorted(APPS):
                    if str(tid) in after.country_tech['JAP']:continue
                    # Native effects execute before the just-completed tech is marked known.
                    for c in installed_commands(tid):after.command(c,'JAP')
                    after.country_tech['JAP'].add(str(tid))
                for command in owner(unit).activation_commands(unit):after.command(build.parse(command),'JAP')
                self.assertEqual(after.models['JAP',unit],before.models['JAP',unit])
                def values(w):return {k:v for k,v in w.properties.items() if k[2]==unit and abs(v)>1e-7}
                self.assertEqual(values(after),values(before))
                state=snapshot(after)
                for command in owner(unit).activation_commands(unit):after.command(build.parse(command),'JAP')
                self.assertEqual(snapshot(after),state)

    def test_foreign_research_cannot_use_japanese_global_activation_flags(self):
        w=ColdWorld()
        for unit in ENTRIES:w.dispatch('unique_intro_'+unit)
        w.country_tech['USA']=set(ALL_TECH);before=snapshot(w)
        for tid in APPS:
            for c in installed_commands(tid):w.command(c,'USA')
        for unit in ENTRIES:
            for text in owner(unit).activation_commands(unit):w.command(build.parse(text),'USA')
        self.assertEqual(snapshot(w),before)

    def test_programme_bonuses_survive_unlock_order_without_double_application(self):
        for unit,programme,choice in [('d_13','naval_production',1),('d_14','prewar_navigation_trials',0),('d_15','prewar_landing_trials',0)]:
            finish=BY_KEY[programme+'_finish_'+str(choice)]
            effects=[build.parse(c) for c in finish.actions[0].commands if build.get(build.parse(c),'which')==unit and build.get(build.parse(c),'type') in divisions.UNIT_EFFECTS]
            if unit=='d_15':
                # Teishin follows Paratrooper effects; Marine-only exercises must not leak to it.
                self.assertFalse(effects);continue
            self.assertTrue(effects,programme)
            first=ColdWorld();last=ColdWorld()
            for c in effects:first.command(c,'JAP')
            first.dispatch('unique_intro_'+unit);last.dispatch('unique_intro_'+unit)
            for c in effects:last.command(c,'JAP')
            self.assertEqual(first.properties,last.properties)

    def test_installed_registry_models_ministers_art_and_compatibility(self):
        registries={True:build.parse(build.read(build.TARGET/'db/units/division_types.txt')),False:build.parse(build.read(build.TARGET/'db/units/brigade_types.txt'))}
        traits={r[7].casefold() for l in build.read(build.TARGET/'db/ministers/ministers_jap.csv').splitlines() if len(r:=l.split(';'))>7 and r[0].isdigit()}
        ministers=build.getall(build.parse(build.read(build.TARGET/'db/ministers/minister_personalities.txt')),'minister')
        for unit,info in ENTRIES.items():
            div=unit in divisions.CLASSES;registry=registries[div]
            body=[(k,v) for k,v in registry if isinstance(v,list) and k!='eyr']
            self.assertEqual(body[info['index']][0],unit)
            definition=build.get(registry,unit);self.assertEqual(build.get(definition,'type'),info['base'] if div else info['branch'])
            directory='divisions' if div else 'brigades'
            models=build.getall(build.parse(build.read(build.TARGET/'db/units'/directory/(unit+'.txt'))),'model')
            self.assertEqual(len(models),len(info['years']))
            for i in range(len(models)):
                card=build.TARGET/'gfx/interface/models'/((f'ill_div_JAP_{info["index"]}_{i}.bmp') if div else (f'ill_bri_JAP_{info["index"]}_{i}.bmp'))
                with Image.open(card) as im:self.assertEqual(im.size,(192,104))
            for m in ministers:
                if build.get(m,'trait','').casefold() not in traits:continue
                rows=build.getall(m,'command')
                for row in list(rows):
                    if build.get(row,'type')!=('unit' if div else 'extra') or build.get(row,'which')!=info['base']:continue
                    clone=copy.deepcopy(row);clone=[(k,unit if k=='which' else v) for k,v in clone]
                    self.assertIn(dict(clone),[dict(r) for r in rows],(unit,build.get(m,'trait')))
        for unit,info in attachments.ATTACHMENTS.items():
            for eligible_type in info['compatible']:
                root=build.parse(build.read(build.TARGET/'db/units/divisions'/(eligible_type+'.txt')))
                self.assertIn(unit,build.getall(root,'allowed_brigades'))
        self.assertNotEqual((build.TARGET/'gfx/interface/models/ill_div_JAP_54_0.bmp').read_bytes(),(build.TARGET/'gfx/interface/models/ill_div_JAP_54_1.bmp').read_bytes())
        for key in introductions.REPORT['introductions']:
            path=build.TARGET/'gfx/events_pics'/('jx_'+BY_KEY[key].art+'.bmp')
            with Image.open(path) as im:self.assertEqual(im.size,(400,116))
        index=build.read(build.TARGET/'db/events.txt')
        for module in ('unique_unit_introductions','unique_unit_upgrades'):
            self.assertIn('db\\events\\japan_rising\\'+module+'.txt',index)
            installed={build.get(e,'id'):e for e in build.getall(build.parse(build.read(build.TARGET/'db/events/japan_rising'/(module+'.txt'))),'event')}
            self.assertEqual(set(installed),{str(e.id)for e in build.EVENTS if e.module==module})
            for e in build.EVENTS:
                if e.module==module:self.assertEqual(build.get(installed[str(e.id)],'picture'),'jx_'+e.art)
        with Image.open(build.TARGET/'gfx/map/hoi_counter_strip.bmp') as im:self.assertEqual(im.size,((53+len(divisions.CLASSES))*32,34))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(UniqueUnitReview))
    report=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                introductions=introductions.REPORT['introductions'],resolvers=len(introductions.REPORT['upgrade_resolvers']),
                first_issue_manpower=sum(float(build.get(divisions.models(u)[0],'manpower')) for u in divisions.CLASSES)+2*sum(float(build.get(attachments.models(u)[0],'manpower')) for u in attachments.ATTACHMENTS),game_launched=False)
    Path(__file__).with_name('UNIQUE_UNIT_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
