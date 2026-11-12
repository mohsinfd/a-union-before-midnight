"""Native attachment contracts, isolated install and research-order regression."""
from collections import defaultdict
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import unique_attachments as u


def serialise(node):
    def quote(value):
        value=str(value)
        return value if value and all(c.isalnum() or c in '_.:+-' for c in value) else '"'+value.replace('"',"'")+'"'
    return '\n'.join((str(k)+' = ' if k is not None else '')+
                     ('{ '+serialise(v)+' }' if isinstance(v,list) else quote(v)) for k,v in node)


def write(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='latin1')


class NativeState:
    def __init__(self,actor='JAP',year=1935,known=()):
        self.actor=actor;self.year=year;self.known=set(known);self.flags={'JX_ACTIVE'}
        self.allowed=set();self.models={unit:{0} for unit in u.ATTACHMENTS};self.stats=defaultdict(float)

    def test(self,node):
        values=[]
        for key,value in node:
            if key=='AND':values.append(self.test(value))
            elif key=='OR':values.append(any(self.test([(k,v)]) for k,v in value))
            elif key=='NOT':values.append(not any(self.test([(k,v)]) for k,v in value))
            elif key=='country':values.append(self.actor==value)
            elif key=='year':values.append(self.year>=int(value))
            elif key=='technology':values.append(int(value) in self.known)
            elif key=='flag':values.append(value in self.flags)
            elif key=='ai':values.append(value=='no')
            elif key=='ispuppet':values.append(False)
            else:raise AssertionError('Unmodelled native predicate '+str(key))
        return all(values)

    def command(self,text):
        node=u.parse(text) if isinstance(text,str) else text
        if u.get(node,'trigger') and not self.test(u.get(node,'trigger')):return
        kind=u.get(node,'type');unit=u.get(node,'which');value=u.get(node,'value')
        if kind=='activate_unit_type':self.allowed.add(unit)
        elif kind=='deactivate_unit_type':self.allowed.discard(unit)
        elif kind=='new_model':self.models[unit].add(int(value))
        elif kind=='scrap_model':self.models[unit].discard(int(value))
        elif kind=='setflag':self.flags.add(unit)
        else:self.stats[kind,unit]+=float(value or 0)

    def run(self,commands):
        for command in commands:self.command(command)

    def research(self,root,tid):
        self.known.add(tid)
        app=next(a for t in u.getall(root,'technology') for a in u.getall(t,'application') if int(u.get(a,'id'))==tid)
        for command in u.getall(u.get(app,'effects',[]),'command'):
            which=u.get(command,'which','')
            if which in u.ATTACHMENTS or which.startswith('JX_UNIQUE_'):self.command(command)


class AttachmentReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='attachment_review_',dir=u.HERE)
        cls.target=Path(cls.temp.name).resolve()
        assert cls.target.is_relative_to(u.HERE.resolve())
        for directory in ('db/tech','db/units/brigades','db/units/divisions','scenarios/1933'):
            shutil.copytree(u.SOURCE/directory,cls.target/directory)
        for relative in ('db/units/brigade_types.txt','db/units/brigade_modifiers.csv',
                         'db/ministers/minister_personalities.txt','db/ministers/ministers_jap.csv'):
            destination=cls.target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(u.SOURCE/relative,destination)
        # Current target can already contain another module's registered types
        # and tech hooks. This fixture proves our installer preserves them.
        shutil.copy2(u.SOURCE/'db/units/divisions/destroyer.txt',cls.target/'db/units/divisions/d_13.txt')
        shutil.copy2(u.SOURCE/'db/units/divisions/naval_bomber.txt',cls.target/'db/units/divisions/d_14.txt')
        shutil.copy2(u.SOURCE/'db/units/divisions/paratrooper.txt',cls.target/'db/units/divisions/d_15.txt')
        import unique_divisions
        for unit,info in unique_divisions.CLASSES.items():
            shutil.copy2(u.SOURCE/'db/units/divisions'/(info['base']+'.txt'),cls.target/'db/units/divisions'/(unit+'.txt'))
        p=cls.target/'db/tech/naval_tech.txt';root=u.parse(u.read(p))
        app=next(a for t in u.getall(root,'technology') for a in u.getall(t,'application') if u.get(a,'id')=='3060')
        u.get(app,'effects').append(('command',u.parse('trigger = { country = JAP flag = JX_OTHER_MODULE } type = naval_attack which = d_13 value = 9')))
        write(p,serialise(root))
        cls.report=u.install(u.SOURCE,cls.target,u.read,write,u.parse,serialise)
        cls.tech={p.name:u.parse(u.read(p)) for p in (cls.target/'db/tech').glob('*.txt')}

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_registered_indices_model_counts_and_native_schema(self):
        registry=u.parse(u.read(self.target/'db/units/brigade_types.txt'))
        keys=[key for key,value in registry]
        self.assertEqual(keys[41:44],['b_01','b_02','b_03'])
        self.assertEqual(len(keys),44)
        for unit,info in u.ATTACHMENTS.items():
            definition=u.get(registry,unit)
            self.assertEqual(u.get(definition,'type'),info['branch'])
            self.assertIsNone(u.get(definition,'production'))
            self.assertEqual(len(u.getall(u.parse(u.read(self.target/'db/units/brigades'/f'{unit}.txt')),'model')),len(info['years']))

    def test_initially_locked_in_every_country_and_nonjapan_research_cannot_unlock(self):
        count=0
        for path in (self.target/'scenarios/1933').glob('*.inc'):
            for country in u.getall(u.parse(u.read(path)),'country'):
                for unit in u.ATTACHMENTS:self.assertEqual(u.get(u.get(country,'allowed_brigades'),unit),'no')
                count+=1
        self.assertGreater(count,60)
        for actor in ('GER','USA','CHI','U87','INO'):
            w=NativeState(actor,1950)
            # Even if every implicit model exists or Japan has already opened
            # all classes, native initialisation closes non-Japanese production.
            w.allowed.update(u.ATTACHMENTS)
            w.flags.update('JX_'+v['flag'] for v in u.ATTACHMENTS.values())
            w.research(self.tech['infantry_tech.txt'],1010)
            self.assertFalse(w.allowed)
            for root in self.tech.values():
                for tree in u.getall(root,'technology'):
                    for app in u.getall(tree,'application'):
                        tid=int(u.get(app,'id'))
                        if any(u.get(c,'which') in u.ATTACHMENTS for c in u.getall(u.get(app,'effects',[]),'command')):w.research(root,tid)
            for unit in u.ATTACHMENTS:w.run(u.activation_commands(unit))
            self.assertFalse(w.allowed,actor)
            self.assertTrue(all(models=={0} for models in w.models.values()))

    def test_activation_knowledge_date_catchup_and_replay_safety(self):
        for unit,info in u.ATTACHMENTS.items():
            w=NativeState(year=info['year']-1,known=[info['tech']])
            w.run(u.activation_commands(unit));self.assertNotIn(unit,w.allowed)
            w.year=info['year'];w.known.clear();w.run(u.activation_commands(unit));self.assertNotIn(unit,w.allowed)
            w.known.add(info['tech']);w.run(u.activation_commands(unit));self.assertIn(unit,w.allowed)
            snapshot=(deepcopy(w.models),dict(w.stats),set(w.flags))
            w.run(u.activation_commands(unit));self.assertEqual(snapshot,(w.models,dict(w.stats),w.flags))
            self.assertFalse(any(u.get(u.parse(c),'type')=='new_model' and u.get(u.parse(c),'value')=='0' for c in u.activation_commands(unit)))

    def test_early_research_catches_up_at_opening_year_and_sparse_upgrade_never_downgrades(self):
        w=NativeState(year=1942,known=[2050,1630])
        w.run(u.activation_commands('b_03'));self.assertEqual(w.models['b_03'],{0})
        w.year=1949
        resolver=next(r for r in u.upgrade_event_specs() if r['unit']=='b_03' and r['model']==2)
        self.assertTrue(w.test(u.parse(resolver['gate'])))
        w.run(resolver['commands']);self.assertEqual(w.models['b_03'],{2})
        w.research(self.tech['armor_tech.txt'],2060)
        self.assertEqual(w.models['b_03'],{2})
        self.assertFalse(w.test(u.parse(resolver['gate'])))
        torp=NativeState(year=1945,known=[3060,3080])
        torp.run(u.activation_commands('b_01'));self.assertEqual(torp.models['b_01'],{2})
        torp.research(self.tech['naval_tech.txt'],12000)
        self.assertEqual(torp.models['b_01'],{2})

    def test_gift_conditions_choose_one_current_model_even_with_future_research(self):
        for unit,info in u.ATTACHMENTS.items():
            for year in range(info['year'],1951):
                w=NativeState(year=year,known=[tech for tech,model in info['techpairs']])
                choices=[i for i,gate in u.latest_model_conditions(unit) if w.test(u.parse(gate))]
                self.assertEqual(len(choices),1,(unit,year,choices))
                self.assertEqual(choices[0],max(i for i,y in enumerate(info['years']) if y<=year))

    def test_relative_effects_use_native_model_zero_and_tech_receipts_apply_once(self):
        expected={'b_01':-28,'b_02':-14,'b_03':-34}
        techs={'b_01':5150,'b_02':5180,'b_03':5160}
        for unit,info in u.ATTACHMENTS.items():
            tid=techs[unit];w=NativeState(year=1950,known=[info['tech'],tid])
            w.run(u.activation_commands(unit))
            self.assertEqual(w.stats['build_time',unit],expected[unit])
            before=dict(w.stats);w.research(self.tech['industry_tech.txt'],tid)
            self.assertEqual(dict(w.stats),before)
        # Preserve the base amphibious-armor tech's penalties as well as gains.
        w=NativeState(year=1942,known=[2050,7630]);w.run(u.activation_commands('b_03'))
        self.assertEqual(w.stats['build_cost','b_03'],1)
        self.assertEqual(w.stats['manpower','b_03'],-.2)
        self.assertEqual(w.stats['defensiveness','b_03'],-1)

    def test_compatibility_role_boundaries_and_base_models_unchanged(self):
        for path in (self.target/'db/units/divisions').glob('*.txt'):
            allowed=u.getall(u.parse(u.read(path)),'allowed_brigades')
            for unit,info in u.ATTACHMENTS.items():self.assertEqual(unit in allowed,path.stem in info['compatible'],(path.stem,unit))
        for unit in ('naval_torpedoes_s','police','amph_armor'):
            self.assertEqual((self.target/'db/units/brigades'/f'{unit}.txt').read_bytes(),(u.SOURCE/'db/units/brigades'/f'{unit}.txt').read_bytes())
        self.assertIn('d_13',u.ATTACHMENTS['b_01']['compatible'])
        self.assertNotIn('d_15',u.ATTACHMENTS['b_02']['compatible'])
        self.assertNotIn('d_14',u.ATTACHMENTS['b_03']['compatible'])

    def test_balance_roles_and_terrain_columns_eof(self):
        rows=list(csv.reader(u.read(self.target/'db/units/brigade_modifiers.csv').splitlines(),delimiter=';'))
        header=rows[0];values={r[0]:r for r in rows}
        self.assertTrue(all(len(r)==len(header) for r in rows))
        self.assertEqual(values['EOF'][header.index('X')],'X')
        self.assertEqual(values['ATT_SHORE'][header.index('b_03')],'15')
        self.assertEqual(values['ATT_RIVER'][header.index('b_03')],'12')
        self.assertEqual(values['DEF_URBAN'][header.index('b_02')],'5')
        self.assertEqual(values['ATT_SHORE'][header.index('amph_armor')],'10')
        tank=u.models('b_03')[0]
        self.assertEqual((u.num(tank,'cost'),u.num(tank,'buildtime'),u.num(tank,'fuelconsumption')),(4.5,140,1))
        self.assertEqual(u.num(u.models('b_02')[0],'suppression'),8)
        self.assertEqual(u.num(u.models('b_01')[0],'seaattack'),3)

    def test_preserve_other_tech_hooks_and_repeat_install_no_duplicates(self):
        root=self.tech['naval_tech.txt']
        self.assertTrue(any(u.get(c,'which')=='d_13' and u.get(c,'value')=='9' for t in u.getall(root,'technology')
                            for a in u.getall(t,'application') for c in u.getall(u.get(a,'effects',[]),'command')))
        prior={p.relative_to(self.target):p.read_bytes() for p in (self.target/'db/tech').glob('*.txt')}
        u.apply_tech(self.target,u.read,write,u.parse,serialise)
        self.assertEqual(prior,{p.relative_to(self.target):p.read_bytes() for p in (self.target/'db/tech').glob('*.txt')})

    def test_assets_registered_pixels_distinct_symbols_and_24_bit_cards(self):
        from PIL import Image
        for name,tile in (('auxiliary.bmp',16),('auxiliarybig.bmp',20)):
            source=Image.open(u.SOURCE/'gfx/interface'/name).convert('RGB')
            actual=Image.open(self.target/'gfx/interface'/name)
            self.assertEqual(actual.size,(44*tile,tile));self.assertEqual(actual.mode,'RGB')
            self.assertEqual(actual.crop((0,0,41*tile,tile)).tobytes(),source.crop((0,0,41*tile,tile)).tobytes())
            for unit,base in (('b_01',21),('b_02',12),('b_03',32)):
                index=u.ATTACHMENTS[unit]['index']
                self.assertNotEqual(actual.crop((index*tile,0,(index+1)*tile,tile)).tobytes(),source.crop((base*tile,0,(base+1)*tile,tile)).tobytes())
        for unit,info in u.ATTACHMENTS.items():
            for model in range(len(info['years'])):
                path=self.target/'gfx/interface/models'/f'ill_bri_JAP_{info["index"]}_{model}.bmp'
                self.assertEqual(Image.open(path).size,(192,104))
                self.assertEqual(int.from_bytes(path.read_bytes()[28:30],'little'),24)
            self.assertEqual(Image.open(self.target/'gfx/events_pics'/f'jx_{info["artkey"]}.bmp').size,(400,116))
        self.assertEqual(len(u.localisation_rows()),33)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AttachmentReview))
    payload={**u.REPORT,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'engine_launched':False,'active_mod_or_save_edited':False,
             'models':{k:[dict(m) for m in u.models(k)] for k in u.ATTACHMENTS},
             'attachments':u.ATTACHMENTS}
    (u.HERE/'UNIQUE_ATTACHMENTS_REVIEW.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
    raise SystemExit(not result.wasSuccessful())
