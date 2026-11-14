"""R13 installed-native audit, independent arithmetic and preservation checks."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
import build as b
import unique_divisions as u
import unique_attachments as attachments
from R12_1_COLD_review import RevisionReview

b.prepare_catalog()
NEW=('d_16','d_17','d_18','d_19')


class NewSpecialistReview(unittest.TestCase):
    def test_all_1802_previous_ids_survive_with_only_twenty_appended(self):
        prior=json.loads((b.HERE/'backups/before_R13_specialists/events.json').read_text())
        now={e.key:e.id for e in b.EVENTS}
        self.assertEqual(len(prior),1802);self.assertEqual(len({k:v for k,v in now.items() if v<=28601822}),1822)
        self.assertTrue(all(now[e['key']]==e['id'] for e in prior))
        self.assertEqual(sum(e.decision for e in b.EVENTS if e.id<=28601822),121)
        self.assertTrue(all(now[e.key]>max(x['id'] for x in prior) for e in b.EVENTS if e.key not in {x['key'] for x in prior}))

    def test_existing_heavy_submarines_and_starting_boats_are_preserved(self):
        old=b.HERE/'backups/before_R13_specialists/installed'
        relative=Path('db/units/divisions/nuclear_submarine.txt')
        self.assertEqual((old/relative).read_bytes(),(b.TARGET/relative).read_bytes())
        before=b.parse(b.read(old/'db/units/division_types.txt'))
        after=b.parse(b.read(b.TARGET/'db/units/division_types.txt'))
        self.assertEqual(b.get(before,'nuclear_submarine'),b.get(after,'nuclear_submarine'))
        def boats(root):
            country=b.get(b.parse(b.read(root/'scenarios/1933/japan.inc')),'country')
            return [d for fleet in b.getall(country,'navalunit') for d in b.getall(fleet,'division') if b.get(d,'type')=='nuclear_submarine']
        self.assertGreater(len(boats(old)),0);self.assertEqual(boats(old),boats(b.TARGET))
        self.assertFalse(any('submarine' in info['base'] for unit,info in u.CLASSES.items() if unit in NEW))

    def test_installed_new_models_retain_full_crews_and_equipment(self):
        for unit in NEW:
            info=u.CLASSES[unit]
            actual=b.getall(b.parse(b.read(b.TARGET/'db/units/divisions'/(unit+'.txt'))),'model')
            self.assertEqual(actual,u.models(unit))
            native=b.getall(u._root(info['base']),'model')
            for i,model in enumerate(actual):
                base=native[info['base_models'][i]]
                self.assertEqual(b.get(model,'manpower'),b.get(base,'manpower'))
                self.assertEqual(b.get(model,'equipment'),b.get(base,'equipment'))

    def test_cost_benefits_hold_for_every_new_model_without_tiny_formations(self):
        for unit in NEW:
            info=u.CLASSES[unit];native=b.getall(u._root(info['base']),'model')
            last_range=0
            for i,model in enumerate(u.models(unit)):
                base=native[info['base_models'][i]]
                ratio=b.num(model,'cost')*b.num(model,'buildtime')/(b.num(base,'cost')*b.num(base,'buildtime'))
                self.assertGreater(b.num(model,'manpower'),0)
                if unit in ('d_16','d_19'):self.assertLessEqual(ratio,1.01)
                elif unit=='d_17':self.assertLessEqual(ratio,.91)
                else:self.assertLessEqual(ratio,.65)
                if unit in ('d_16','d_17'):
                    self.assertGreaterEqual(b.num(model,'range'),last_range);last_range=b.num(model,'range')
                    self.assertGreater(b.num(model,'airdefence'),b.num(base,'airdefence'))
                if unit=='d_16':self.assertEqual(b.get(model,'airattack'),b.get(base,'airattack'))
                elif unit=='d_17':self.assertEqual(b.get(model,'navalattack'),b.get(base,'navalattack'))
                elif unit=='d_18':self.assertLess(b.num(model,'maxspeed'),b.num(base,'maxspeed'))
                elif unit=='d_19':
                    self.assertEqual(b.get(model,'softattack'),b.get(base,'softattack'))
                    self.assertLess(b.num(model,'defensiveness'),b.num(base,'defensiveness'))

    def test_land_terrain_advantage_is_real_and_standard_families_unchanged(self):
        rows=[line.split(';') for line in b.read(b.TARGET/'db/units/modifiers.csv').splitlines()]
        old=[line.split(';') for line in b.read(b.HERE/'backups/before_R13_specialists/installed/db/units/modifiers.csv').splitlines()]
        self.assertTrue(all(len(r)==len(rows[0]) for r in rows))
        columns=rows[0];prior=old[0]
        values={r[0]:r for r in rows}
        for row in old[1:]:
            if row[0]=='EOF':continue
            for col in prior[1:-1]:self.assertEqual(values[row[0]][columns.index(col)],row[prior.index(col)],(row[0],col))
        for row,bonus in {'ATT_JUNGLE':15,'MOV_JUNGLE':15,'ATT_FOREST':10,'MOV_FOREST':10,'ATT_RIVER':15,'ATT_URBAN':10}.items():
            self.assertEqual(float(values[row][columns.index('d_19')])-float(values[row][columns.index('INF')]),bonus)
        for row in ('ATT_SHORE','ATT_MOUNTAIN','ATT_FROZEN'):
            self.assertEqual(values[row][columns.index('d_19')],values[row][columns.index('INF')])

    def test_all_native_models_unchanged_and_no_self_conversion(self):
        for base in {i['base'] for i in u.CLASSES.values()}:
            actual=b.parse(b.read(b.TARGET/'db/units/divisions'/(base+'.txt')))
            native=u._root(base)
            self.assertEqual(b.getall(actual,'model'),b.getall(native,'model'),base)
        for unit in u.CLASSES:
            actual=b.parse(b.read(b.TARGET/'db/units/divisions'/(unit+'.txt')))
            self.assertFalse(any(b.get(c,'type')==unit for c in b.getall(actual,'upgrade')),unit)

    def test_new_attachment_compatibility_does_not_insert_extra_equipment(self):
        for unit in NEW:
            actual=b.parse(b.read(b.TARGET/'db/units/divisions'/(unit+'.txt')))
            allowed=b.getall(actual,'allowed_brigades')
            self.assertEqual(len(allowed),len(set(allowed)))
            for brigade,info in attachments.ATTACHMENTS.items():self.assertEqual(brigade in allowed,unit in info['compatible'])
        for e in b.EVENTS:
            if e.key not in {'unique_activate_'+unit for unit in NEW}:continue
            for a in e.actions:
                for text in a.commands:
                    c=b.parse(text)
                    if b.get(c,'type')=='add_division':self.assertIsNone(b.get(c,'extra'))

    def test_new_art_is_distinct_and_aircraft_upgrades_use_new_cards(self):
        model_hashes=[]
        for unit in NEW:
            info=u.CLASSES[unit]
            for i in range(len(info['years'])):
                for name,size in ((f'ill_div_JAP_{info["index"]}_{i}.bmp',(192,104)),(f'JAP_model_{info["index"]}_{i}.bmp',(67,44))):
                    path=b.TARGET/'gfx/interface/models'/name
                    with Image.open(path) as image:self.assertEqual(image.size,size)
            model_hashes.append(hashlib.sha256((b.TARGET/'gfx/interface/models'/f'ill_div_JAP_{info["index"]}_0.bmp').read_bytes()).hexdigest())
        self.assertEqual(len(set(model_hashes)),4)
        for unit,later in (('d_16',2),('d_17',1)):
            index=u.CLASSES[unit]['index'];root=b.TARGET/'gfx/interface/models'
            self.assertNotEqual((root/f'ill_div_JAP_{index}_0.bmp').read_bytes(),(root/f'ill_div_JAP_{index}_{later}.bmp').read_bytes())
        with Image.open(b.TARGET/'gfx/map/hoi_counter_strip.bmp') as atlas:
            self.assertEqual(atlas.size,(60*32,34))
            with Image.open(b.HERE/'backups/before_R13_specialists/installed/gfx/map/hoi_counter_strip.bmp') as old:
                self.assertEqual(atlas.crop((0,0,56*32,34)).tobytes(),old.tobytes())


if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(RevisionReview),unittest.defaultTestLoader.loadTestsFromTestCase(NewSpecialistReview)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(version=b.VERSION,passed=result.wasSuccessful(),tests=result.testsRun,
                failures=len(result.failures),errors=len(result.errors),game_launched=False,
                scope='Installed event commands, deferred delivery, shipping, existing heavy submarines, native stats, full equipment, IC-days, terrain, conversions, attachment compatibility and artwork.')
    (b.HERE/'R13_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
