"""R12 division-contract review in a disposable fixture, never the game mod."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

import build as b
import unique_divisions as u
import specialist_units as old

HERE=Path(__file__).resolve().parent


class State:
    """Documented modifier/model contract only; not a combat/engine emulator."""
    def __init__(self,year,known=(),country='JAP'):
        self.year=year;self.known=set(map(str,known));self.country=country
        self.flags={'JX_ACTIVE'};self.allowed=set();self.models=defaultdict(lambda:{0});self.values=defaultdict(float)
    def test(self,node):
        result=[]
        for k,v in node:
            if k=='AND':result.append(self.test(v))
            elif k=='OR':result.append(any(self.test([(a,c)]) for a,c in v))
            elif k=='NOT':result.append(not any(self.test([(a,c)]) for a,c in v))
            elif k=='flag':result.append(v in self.flags)
            elif k=='year':result.append(self.year>=int(v))
            elif k=='technology':result.append(v in self.known)
            elif k=='country':result.append(self.country==v)
            elif k=='ai':result.append((self.country=='JAP')==(v=='no'))
            elif k=='ispuppet':result.append(False)
            else:raise AssertionError('Unmodelled fixture predicate '+k)
        return all(result)
    def run(self,commands):
        for text in commands:
            c=b.parse(text) if isinstance(text,str) else text
            gate=b.get(c,'trigger')
            if gate and not self.test(gate):continue
            typ=b.get(c,'type');which=b.get(c,'which')
            if typ=='setflag':self.flags.add(which)
            elif typ=='clrflag':self.flags.discard(which)
            elif typ=='activate_unit_type':self.allowed.add(which)
            elif typ=='new_model':self.models[which].add(int(b.get(c,'value')))
            elif typ=='scrap_model':self.models[which].discard(int(b.get(c,'value')))
            elif typ in u.UNIT_EFFECTS:self.values[typ,which]+=float(b.get(c,'value'))
            else:raise AssertionError('Unmodelled fixture command '+str(typ))


def _snapshot(state):return (set(state.flags),set(state.allowed),dict(state.values),{k:set(v) for k,v in state.models.items()})


def run():
    b.prepare_catalog();u.apply()
    ids=[(e.key,e.id) for e in b.EVENTS]
    event_snapshot=deepcopy([(e.key,e.actions) for e in b.EVENTS]);u.apply()
    assert event_snapshot==[(e.key,e.actions) for e in b.EVENTS]
    assert ids==[(e.key,e.id) for e in b.EVENTS]
    checks=['Catalogue parity pass is idempotent and allocates no event IDs.']
    comparisons=[]
    for unit,info in u.CLASSES.items():
        original=b.getall(u._root(info['base']),'model')
        models=u.models(unit)
        assert len(models)==len(info['years'])==len(info['techpairs'])==len(info['base_models'])
        for i,m in enumerate(models):
            base=original[info['base_models'][i]]
            assert b.num(m,'manpower')==b.num(base,'manpower')
            assert b.get(m,'equipment')==b.get(base,'equipment')
            expected_cost_factor={'d_13':1.15,'d_14':1.15,'d_15':1.15,'d_16':1.05,'d_17':.95,'d_18':.75,'d_19':1.05}[unit]
            assert abs(b.num(m,'cost')/b.num(base,'cost')-expected_cost_factor)<.001
            if unit=='d_13':
                assert b.num(m,'airattack')==b.num(base,'airattack')*1.5
                assert abs(b.num(m,'seaattack')-b.num(base,'seaattack')*.8)<.001
                assert b.num(m,'subattack')==b.num(base,'subattack')
            elif unit=='d_14':
                assert b.num(m,'range')>=b.num(base,'range')*1.7
                assert b.num(m,'surfacedetectioncapability')==b.num(base,'surfacedetectioncapability')+2
                assert b.num(m,'navalattack')==b.num(base,'navalattack')*.75
                assert b.get(m,'subattack') is None
            elif unit=='d_15':
                for field in ('softattack','hardattack','defensiveness','toughness','maxspeed','transportweight'):
                    assert b.get(m,field)==b.get(base,field)
                assert b.num(m,'defaultorganisation')==b.num(base,'defaultorganisation')+8
                assert b.num(m,'morale')==b.num(base,'morale')+8
            elif unit=='d_16':
                assert b.num(m,'range')>=b.num(base,'range')*2
                assert b.get(m,'airattack')==b.get(base,'airattack')
                assert b.num(m,'airdefence')>b.num(base,'airdefence')
            elif unit=='d_17':
                assert b.num(m,'range')>=b.num(base,'range')*1.5
                assert b.get(m,'navalattack')==b.get(base,'navalattack')
                assert b.num(m,'airdefence')>b.num(base,'airdefence')
            elif unit=='d_18':
                assert b.num(m,'cost')*b.num(m,'buildtime')<b.num(base,'cost')*b.num(base,'buildtime')*.5
                assert b.num(m,'subattack')>=b.num(base,'subattack')*1.2
                assert b.num(m,'maxspeed')<b.num(base,'maxspeed')
            elif unit=='d_19':
                assert b.get(m,'softattack')==b.get(base,'softattack')
                assert b.num(m,'supplyconsumption')<=b.num(base,'supplyconsumption')*.8+1e-6
                assert b.num(m,'defensiveness')<b.num(base,'defensiveness')
                assert b.num(m,'cost')*b.num(m,'buildtime')<=b.num(base,'cost')*b.num(base,'buildtime')*1.01
            fields=('cost','buildtime','manpower','softattack','hardattack','airattack','seaattack','navalattack',
                    'range','surfacedetectioncapability','defaultorganisation','morale','supplyconsumption')
            comparisons.append(dict(unit=unit,year=info['years'][i],model=i,tech=info['techpairs'][i][0],
                                    base_model=info['base_models'][i],stats={k:b.get(m,k) for k in fields},
                                    native={k:b.get(base,k) for k in fields}))
    checks.append('All 29 models retain full native manpower/equipment; the four new classes provide reach, economical ASW or expeditionary terrain/endurance with explicit tradeoffs and IC-day checks.')
    source_apps=list(u._applications());all_known={int(b.get(a,'id')) for _,a in source_apps}
    source_by_id={int(b.get(a,'id')):a for _,a in source_apps}
    for unit,info in u.CLASSES.items():
        for tech,index in info['techpairs']:
            assert any(b.get(c,'type')=='new_model' and b.get(c,'which')==info['base']
                       and int(b.get(c,'value'))==info['base_models'][index]
                       for c in b.getall(b.get(source_by_id[tech],'effects',[]),'command'))

    with tempfile.TemporaryDirectory(prefix='R12_UNIQUE_',dir=HERE) as scratch:
        target=Path(scratch);assert target.resolve().parent==HERE.resolve()
        def write(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='latin1')
        for path in (b.SOURCE/'db/tech').glob('*.txt'):write(target/'db/tech'/path.name,b.read(path))
        for info in u.CLASSES.values():
            write(target/'db/units/divisions'/f'{info["base"]}.txt',b.read(b.SOURCE/'db/units/divisions'/f'{info["base"]}.txt'))
        write(target/'config/models.csv',b.read(b.SOURCE/'config/models.csv'))
        (target/'gfx/map').mkdir(parents=True);(target/'gfx/interface/models').mkdir(parents=True)
        # Populate native event files so preservation of stock Japanese bonuses
        # is exercised, rather than silently skipped by a minimal fixture.
        from equipment_delivery_review import loaded_events
        event_files,_=loaded_events(b.SOURCE)
        for path in event_files:
            if path.exists():write(target/path.relative_to(b.SOURCE),b.read(path))
        old.install(b.SOURCE,target,write,b.serialise)
        old_types=b.parse(b.read(target/'db/units/division_types.txt'))
        preserved={unit:deepcopy(b.get(old_types,unit)) for unit in old.CLASSES}
        from PIL import Image
        with Image.open(target/'gfx/map/hoi_counter_strip.bmp') as opened:
            before=opened.copy();opened.close()
        u.install(b.SOURCE,target,b.read,write,b.parse,b.serialise)
        final_types=b.parse(b.read(target/'db/units/division_types.txt'))
        assert [k for k,v in final_types if k.startswith('d_')][-10:]==['d_10','d_11','d_12']+list(u.CLASSES)
        assert all(b.get(final_types,unit)==node for unit,node in preserved.items())
        for unit,info in u.CLASSES.items():
            definition=b.get(final_types,unit)
            assert b.get(definition,'type')==info['base'] and b.get(definition,'production')=='no'
            assert b.get(definition,info['base']) is None
            new=b.parse(b.read(target/'db/units/divisions'/f'{unit}.txt'))
            original=u._root(info['base'])
            assert b.getall(new,'allowed_brigades')==b.getall(original,'allowed_brigades')
            assert b.getall(new,'model')==u.models(unit)
            assert any(b.get(c,'type')==info['base'] for c in b.getall(new,'upgrade'))
            base=b.parse(b.read(target/'db/units/divisions'/f'{info["base"]}.txt'))
            assert any(b.get(c,'type')==unit and b.get(c,'upgrade_time_factor')=='1.0'
                       and b.get(c,'upgrade_cost_factor')=='1.0' for c in b.getall(base,'upgrade'))
            assert all(c in b.getall(new,'upgrade') for c in b.getall(original,'upgrade'))
        checks.append('Fixture installer appends d_13 through d_19, preserves retired d_10 through d_12, copies native attachment/conversion choices and adds full-factor normal conversion routes.')
        rows=[l.split(';') for l in b.read(target/'db/units/modifiers.csv').splitlines()]
        header=rows[0];assert header[-(len(u.CLASSES)+1):]==list(u.CLASSES)+['X']
        assert all(len(r)==len(header) for r in rows)
        for r in rows[1:]:
            if r[0]=='EOF':continue
            for unit,info in u.CLASSES.items():
                base_value=float(r[header.index(u.PARENT_COLUMNS[info['base']])])
                assert float(r[header.index(unit)])==base_value+u.TERRAIN_BONUSES.get(unit,{}).get(r[0],0)
        model_lines=b.read(target/'config/models.csv').splitlines()
        end=next(i for i,l in enumerate(model_lines) if l.lstrip().upper().startswith('#EOF') or l.split(';')[0].upper()=='EOF')
        for unit,info in u.CLASSES.items():
            for i in range(len(info['years'])):
                for key in (f'MODEL_JAP_{info["index"]}_{i}',f'MODEL_{info["index"]}_{i}'):
                    matches=[j for j,l in enumerate(model_lines) if l.startswith(key+';')]
                    assert len(matches)==1 and matches[0]<end
        with Image.open(target/'gfx/map/hoi_counter_strip.bmp') as opened:
            atlas=opened.copy();opened.close()
        assert atlas.size==((53+len(u.CLASSES))*32,34) and atlas.mode=='P'
        assert atlas.getpalette()==before.getpalette()
        assert atlas.crop((0,0,53*32,34)).tobytes()==before.tobytes()
        cells=[atlas.crop((i*32,0,(i+1)*32,34)) for i in range(53,53+len(u.CLASSES))]
        assert len({c.tobytes() for c in cells})==len(u.CLASSES)
        registry_names=[key for key,node in old_types if isinstance(node,list) and key!='eyr']
        assert {base:registry_names.index(base) for base in ('destroyer','naval_bomber','paratrooper')}=={'destroyer':25,'naval_bomber':16,'paratrooper':6}
        for cell,(unit,label) in zip(cells,u.COUNTER_LABELS.items()):
            native_index=registry_names.index(u.CLASSES[unit]['base'])
            original=before.crop((native_index*32,0,(native_index+1)*32,34))
            assert cell.tobytes()!=original.tobytes()
            left=32-len(label)*4-3
            for y in range(34):
                for x in range(32):
                    if not(1<=y<=6 and left<=x<=30):assert cell.getpixel((x,y))==original.getpixel((x,y))
        preview=Image.new('RGB',(32*8*len(u.CLASSES),34*8),'#ddd')
        for i,cell in enumerate(cells):preview.paste(cell.resize((32*8,34*8),Image.Resampling.NEAREST).convert('RGB'),(i*32*8,0))
        preview.save(HERE/'UNIQUE_DIVISION_COUNTERS.png')
        checks.append('All terrain/weather columns match their native parent except the six intended expeditionary bonuses. Model names precede EOF; the 60-cell counter atlas preserves old pixels and adds distinct AA/P/AB/LR/NA/AS/EX markers.')
        target_apps={int(b.get(a,'id')):a for p in (target/'db/tech').glob('*.txt')
                     for t in b.getall(b.parse(b.read(p)),'technology') for a in b.getall(t,'application')}
        def research_commands(unit,tech):
            return [c for c in b.getall(b.get(target_apps[tech],'effects',[]),'command')
                    if b.get(c,'which')==unit or str(b.get(c,'which','')).startswith('JX_UNIQUE_'+unit.upper()+'_')]
        for unit,info in u.CLASSES.items():
            early=State(1950,all_known);early.run(u.activation_commands(unit))
            initial=_snapshot(early);early.run(u.activation_commands(unit));assert _snapshot(early)==initial
            expected=max(i for tech,i in info['techpairs'] if info['years'][i]<=1950)
            assert early.models[unit]=={expected}
            late=State(info['year'],[info['tech']]);late.run(u.activation_commands(unit))
            for tech in sorted(all_known):
                late.known.add(str(tech));late.run(research_commands(unit,tech))
            late.year=1950
            for spec in reversed(u.upgrade_event_specs()):
                if spec['unit']==unit:late.run(spec['commands'])
            assert dict(late.values)==dict(early.values)
            assert late.models[unit]=={expected}
            assert all(not(b.get(b.parse(c),'type')=='new_model' and b.get(b.parse(c),'value')=='0')
                       for c in u.activation_commands(unit))
            # Early future research must not expose a future-year model.
            for year in sorted(set(info['years'])|{info['year']-1,1950}):
                s=State(year,all_known);s.run(u.activation_commands(unit))
                if year<info['year']:assert unit not in s.allowed
                else:assert s.models[unit]=={max(i for tech,i in info['techpairs'] if info['years'][i]<=year)}
            foreign=State(1950,all_known,'GER');foreign.run(u.activation_commands(unit));assert not foreign.allowed and not foreign.values
            # Sparse/out-of-order research cannot revive an obsolete model.
            last=max(i for tech,i in info['techpairs'] if info['years'][i]<=1950)
            sparse=State(1950,[info['tech'],info['techpairs'][last][0]]);sparse.run(u.activation_commands(unit))
            assert sparse.models[unit]=={last}
            for tech,index in reversed(info['techpairs']):
                sparse.known.add(str(tech));sparse.run(research_commands(unit,tech))
            assert sparse.models[unit]=={last}
            # Some engine effect pipelines publish the just-researched tech
            # after its effects. The native hook must not skip then mark done.
            for tech,index in info['techpairs'][1:]:
                during=State(info['years'][index],[info['tech']]);during.run(u.activation_commands(unit))
                assert str(tech) not in during.known
                during.run(research_commands(unit,tech))
                assert during.models[unit]=={index}
                during.known.add(str(tech));saved=_snapshot(during)
                during.run(u.activation_commands(unit));assert _snapshot(during)==saved
            # Fixed relative adjustments retain native model-zero arithmetic.
            all_values=[c for cs in u._tech_effects(unit).values() for c in cs]
            assert all(b.get(c,'where')!='relative' for c in all_values if b.get(c,'type') in {'build_cost','build_time','manpower'})
        checks.append('Research-before/after activation gives identical modifiers exactly once; year-bound catch-up, reverse resolver order, sparse research, foreign countries and implicit model zero all behave correctly without reviving old models.')
        # Every direct Japanese programme benefit must be present before or
        # after registration unlock with no activation replay of the programme.
        for unit,info in u.CLASSES.items():
            for e in b.EVENTS:
                if e.country!='JAP' or e.key.startswith('unique_'):continue
                for a in e.actions:
                    native_cmds=[b.parse(c) for c in a.commands if b.get(b.parse(c),'which')==info['base'] and b.get(b.parse(c),'type') in u.UNIT_EFFECTS]
                    if not native_cmds:continue
                    aliases=[b.parse(c) for c in a.commands if b.get(b.parse(c),'which')==unit and b.get(b.parse(c),'type') in u.UNIT_EFFECTS]
                    assert all(u._clone(c,info['base'],unit) in aliases for c in native_cmds),(e.key,unit)
                    before=State(1950,[info['tech']]);before.run(aliases);before.run(u.activation_commands(unit))
                    after=State(1950,[info['tech']]);after.run(u.activation_commands(unit));after.run(aliases)
                    assert dict(before.values)==dict(after.values),(e.key,unit)
        checks.append('Every Japanese concrete-class programme award and penalty is mirrored; programme-before-unlock versus after-unlock gives identical cost/time/range/organisation without guessing old-save choices or replaying payments.')
        # Complete generated Japanese roster, not only the new personalities.
        b.japan_personnel.apply_roster(b.SOURCE,target,b.read,write,b.parse,b.serialise)
        b.force_value.apply_personnel(target,b.read,write,b.parse,b.serialise)
        b.force_delivery_audit.apply_personnel(target,b.read,write,b.parse,b.serialise)
        u.install_personnel(target,b.read,write,b.parse,b.serialise)
        personalities=b.parse(b.read(target/'db/ministers/minister_personalities.txt'))
        first=deepcopy(personalities);u.install_personnel(target,b.read,write,b.parse,b.serialise)
        assert b.parse(b.read(target/'db/ministers/minister_personalities.txt'))==first
        mirrored=0
        for m in b.getall(personalities,'minister'):
            commands=b.getall(m,'command')
            for c in list(commands):
                if b.get(c,'type')!='unit':continue
                for unit,info in u.CLASSES.items():
                    if b.get(c,'which')!=info['base']:continue
                    clone=deepcopy(c);old.replace(clone,'which',unit)
                    # Foreign-only personality definitions intentionally stay untouched.
                    roster_traits={r[7].casefold() for l in b.read(target/'db/ministers/ministers_jap.csv').splitlines() if len(r:=l.split(';'))>7 and r[0].isdigit()}
                    if b.get(m,'trait').casefold() in roster_traits:assert clone in commands;mirrored+=1
        assert mirrored>0
        checks.append(f'All applicable Japanese concrete minister effects, including penalties, are mirrored ({mirrored} entries); shared air/navy/land modifiers are not copied and the personnel pass is idempotent.')
    report={'checks':checks,'models':comparisons,'classes':u.CLASSES,'report':u.REPORT,
            'scope':'Disposable source fixture and documented-command contracts only; no game/mod installation or save edits.',
            'limits':['No engine launch: subtype airborne missions, naval conversion queues, animation families and modifier caches still need runtime testing.',
                      'Model dates are hard-gated by year+research; resolvers through 1950 must be appended by unique_unit_events. The 1955 AA data model is retained beyond campaign end.',
                      'Flying boats use native surface detection and naval strike, with no invented independent submarine-attack statistic.',
                      'Full historical programme parity requires a new R12 campaign; old R11 completion flags do not prove which alternative was selected.',
                      'Only the division counter atlas is authored here; parent supplies original model cards and event illustrations.']}
    (HERE/'UNIQUE_DIVISIONS_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# R13 Japanese unique divisions - native contract audit', '',
           'All seven specialist classes and 29 model stages are covered. The table below records the three original families; R13_UNITS.md gives the four additional families, full costs, tradeoffs, research and free issues.', '',
           'Three full-size native-family classes replace neither the regular army nor the retired d_10–d_12. Normal production, crews, research, operating costs and allowed attachments remain necessary. Initial free introductions are owned by unique_unit_events.', '',
           '| Class | First model | Useful advantage | Cost / tradeoff |', '| --- | --- | --- | --- |',
           '| Akizuki AA Escort | 1942, DD research 12000 | AA attack 9 vs 6, full 1.5 manpower crew | Sea attack 5.6 vs 7; IC 1.495 vs 1.3, time 598 vs 570 |',
           '| H6K / H8K Flying Boat | 1938 H6K, then year-gated 1942 H8K | Range 2,125 vs 1,250 km, surface detection 3 vs 1, full 2.2 manpower wing | Naval strike 3 vs 4; IC 17.25 vs 15, time 264 vs 240 |',
           '| Teishin Airborne | 1942, Para research 1680 | Full native firepower and 9 manpower; organisation 43 vs 35, morale 48 vs 40, supply -10% | IC 11.5 vs 10, time 451 vs 410; native transports and airborne rules still apply |', '',
           'Akizuki may use the Type 93 fitting added by the attachment installer, competing for the normal slot. Flying-boat range never regresses at the native 1945 transition; later variants retain native equipment tradeoffs. Postwar aircraft and the 1955 AA model are campaign continuations rather than claims about a historical Japanese production programme. Teishin is a full division-sized game formation, not a cheaper understrength subdivision.', '',
           '## Research, programmes and ministers', '',
           'Each concrete research application has a private per-class receipt. Past research catches up once at activation; research after activation applies once through the same ledger. Native group bonuses already cover the real land/air/naval family and are never duplicated. Native relative production modifiers are converted to fixed amounts from the original base class model zero: modern custom model zero must not increase an old assembly-line discount.', '',
           'New model zero stays implicit. Model unlocks require both their advertised year and native research; automatic once-per-model resolvers catch research completed before the year. Lower out-of-order callbacks cannot revive an older model. The 1955 AA model remains in data/tech hooks but has no post-1950 campaign resolver.', '',
           'Concrete Japanese programme awards are mirrored while classes are registered but still locked for production. Activation does not replay programme awards. This makes completing aircraft factories in 1934 and activating flying boats in 1938 equivalent to activating first and completing the programme later. Fresh R12 campaigns are the supported baseline; no old-save branch is guessed from a generic DONE flag.', '',
           'The installer also preserves the four stock Japanese DD/NAV effects in Mods.txt. Applicable Japanese minister effects, including cost/time penalties, receive concrete aliases; group effects stay single. The attachment module separately handles brigade effects and later Type 93 compatibility.', '',
           '## Registry, artwork and integration', '',
           'Run unique_divisions.apply() after the older catalogue preparation passes. Append unique_unit_events introductions/model resolvers, then run final integrity/copy passes. Run unique_divisions.install(SOURCE,TARGET,read,write,parse,serialise) after specialist_units.install. It reads current target tech files and retains old hooks. Run install_personnel after all old roster/personality writers and before final minister validation; the attachment installer can follow it. Merge localisation_rows() into the normal localisation writer.', '',
           'The installer appends d_13–d_15 and all modifier columns without touching old class slots. It adds explicit full-factor conversion routes to and from the native class and preserves native alternate conversion paths. Counter strip cells 53–55 inherit functional Destroyer/NAV/Para glyphs plus distinct AA/P/AB markers, with the old palette and every old indexed pixel preserved. It does not claim bespoke animated map sprites. Parent art must provide jx_unique_akizuki / jx_unique_patrol / jx_unique_teishin event pictures and the corresponding unit cards; early H6K artwork is separate from later H8K artwork.', '',
           '## Validation', '',*('- '+s for s in checks),'', '## Limits','',*('- '+s for s in report['limits'])]
    (HERE/'UNIQUE_DIVISIONS_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'checks':len(checks),'models':len(comparisons),'programme_mirrors':u.REPORT.get('programme_mirrors'),
                      'minister_mirrors':mirrored,'native_event_mirrors':u.REPORT.get('native_event_mirrors')}))


if __name__=='__main__':run()
