"""Read-only force audit; writes only FORCE_ reports beside this script."""
from copy import deepcopy
import json
from pathlib import Path

import build as b
import force_value as fv
import specialist_units as s

HERE = Path(__file__).resolve().parent
GERMANY = b.GAME / 'Mods/Germany Overhaul Campaign'


def applications():
    return [(p.name, app) for p in sorted((s.SOURCE / 'db/tech').glob('*.txt'))
            for tree in s.getall(s.parse(s.read(p)), 'technology')
            for app in s.getall(tree, 'application')]


def latest_model(apps, unit, year):
    candidates = [(s.num(a, 'year'), int(s.get(c, 'value')))
                  for _, a in apps if s.num(a, 'year') <= year
                  for c in s.getall(s.get(a, 'effects', []), 'command')
                  if s.get(c, 'type') == 'new_model' and s.get(c, 'which') == unit
                  and not s.get(c, 'trigger')]
    return max(candidates)[1] if candidates else None


def run():
    b.prepare_catalog()
    fv.apply()
    by = {e.key: e for e in b.EVENTS}
    snapshot = deepcopy([(e.key, e.id, e.actions) for e in b.EVENTS])
    fv.apply()
    assert snapshot == [(e.key, e.id, e.actions) for e in b.EVENTS]
    checks = ['Catalogue application is idempotent; no event IDs or ordering change.']
    for i, priority in enumerate(fv.AIR_GROUPS):
        f = by[f'air_production_finish_{i}']
        assert 'flag = JX_air_production_PENDING' in f.actions[0].gate
        assert 'ai = no' in by['air_production'].gate
        parsed = [s.parse(c) for c in f.actions[0].commands]
        rebates = {}
        for n in parsed:
            if s.get(n, 'type') in {'build_cost', 'build_time'}:
                pair = (s.get(n, 'which'), s.get(n, 'type'))
                assert pair not in rebates, pair
                rebates[pair] = -s.num(n, 'value')
                assert s.get(n, 'when') == 'on_upgrade'
                assert s.get(n, 'where') is None
        assert len(rebates) == 12
        assert all(rebates[u, 'build_cost'] > 0 and rebates[u, 'build_time'] > 0
                   for u in fv.AIR_PRIORITY)
        assert all(rebates[u, 'build_cost'] > fv.AIR_COMMON[0] for u in priority)
        assert not any(s.get(n, 'type') in {'build_division', 'add_division', 'gain_tech'} for n in parsed)
    checks.append('Both funded choices cover six aircraft classes exactly once, with stronger chosen roles; no units or research awarded.')

    # Structural personnel checks include adverse values and shared-group effects.
    personnel = s.parse(s.read(s.SOURCE / 'db/ministers/minister_personalities.txt'))
    native = deepcopy(personnel)
    traits = {r[7] for line in s.read(s.SOURCE / 'db/ministers/ministers_jap.csv').splitlines()
              if len(r := line.split(';')) > 7 and r[0].isdigit()}
    mirrors = fv.mirror_personnel(personnel, traits)
    assert mirrors
    assert fv.mirror_personnel(personnel, traits) == []
    for old, new in zip(s.getall(native, 'minister'), s.getall(personnel, 'minister')):
        old_commands = s.getall(old, 'command')
        assert all(c in s.getall(new, 'command') for c in old_commands)
        assert [(k, v) for k, v in new if k != 'command'] == [(k, v) for k, v in old if k != 'command']
        assert len([c for c in s.getall(new, 'command') if s.get(c, 'which') == 'land']) == len([c for c in old_commands if s.get(c, 'which') == 'land'])
    checks.append(f'{len(mirrors)} concrete minister effects mirrored; native effects retained, shared land effects not duplicated, second pass adds nothing.')
    # Exercise the actual personnel writer and final expanded Japanese roster
    # entirely in memory, so neither installed mod nor source files are touched.
    virtual = Path('FORCE_virtual')
    generated = {}
    def capture(path, content):
        generated[str(path)] = content
    b.japan_personnel.apply_roster(s.SOURCE, virtual, s.read, capture, s.parse, b.serialise)
    installed_mirrors = fv.apply_personnel(virtual, lambda p: generated[str(p)], capture, s.parse, b.serialise)
    assert len(installed_mirrors) == len(mirrors)
    final_node = s.parse(generated[str(virtual / 'db/ministers/minister_personalities.txt')])
    assert fv.mirror_personnel(final_node, traits) == []
    checks.append('Expanded personnel roster + specialist mirroring serialise and parse successfully using an in-memory build, with no installed-file writes.')

    apps = applications()
    air_rows = []
    unavailable = []
    for year in (1933, 1937, 1941, 1945, 1950):
        for u in fv.AIR_PRIORITY:
            ms = s.getall(s.parse(s.read(s.SOURCE / 'db/units/divisions' / f'{u}.txt')), 'model')
            idx = latest_model(apps, u, year)
            if idx is None:
                unavailable.append({'year': year, 'unit': u})
                continue
            model = ms[idx]
            # Aircraft Assembly Line 5140 applies its relative time adjustment
            # to MODEL ZERO. Keep this separate from unmodelled queue modifiers.
            assembly = sum(s.num(c, 'value') * s.num(ms[0], 'buildtime') / 100
                           for _, a in apps if s.get(a, 'id') == '5140'
                           for c in s.getall(s.get(a, 'effects', []), 'command')
                           if s.get(c, 'type') == 'build_time' and s.get(c, 'which') == u)
            cost, days = fv.AIR_PRIORITY[u]
            assert assembly < 0, (u, assembly)
            after_cost = s.num(model, 'cost') - cost
            after_days = s.num(model, 'buildtime') - days
            assert after_cost > 0 and after_days + assembly > 0
            air_rows.append(dict(year=year, unit=u, model=idx,
                                 base_ic=s.num(model, 'cost'), base_days=s.num(model, 'buildtime'),
                                 priority_ic=after_cost, priority_days=after_days,
                                 priority_with_assembly_days=round(after_days + assembly, 2),
                                 common_ic=s.num(model, 'cost') - fv.AIR_COMMON[0],
                                 common_days=s.num(model, 'buildtime') - fv.AIR_COMMON[1],
                                 assembly_raw_days=round(assembly, 2)))
    checks.append('Every sampled 1933/1937/1941/1945/1950 air model retains positive raw cost/time under the stronger priority plus native assembly line.')
    unit_rows = []
    for u, info in s.CLASSES.items():
        techs = s.model_techs(u)
        assert len(s.models(u)) == len(techs) == 5
        assert all(any(s.get(a, 'id') == str(t) for _, a in apps) for t in techs)
        for i, m in enumerate(s.models(u)):
            # Research year determines a source-derived model, rather than a
            # parallel invented tech line or model-zero-only unit definition.
            idx = latest_model(apps, info['base'], s.model_years(u)[i])
            native_models = s.getall(s.parse(s.read(s.SOURCE / 'db/units/divisions' / (info['base'] + '.txt'))), 'model')
            base = native_models[idx]
            assert s.num(m, 'manpower') < s.num(base, 'manpower')
            assert s.num(m, 'cost') * s.num(m, 'buildtime') < s.num(base, 'cost') * s.num(base, 'buildtime')
            unit_rows.append(dict(unit=u, year=s.model_years(u)[i], model=i, research=techs[i],
                                  baseclass=info['base'], native_model=idx,
                                  ic_days=s.num(m, 'cost') * s.num(m, 'buildtime'),
                                  native_ic_days=s.num(base, 'cost') * s.num(base, 'buildtime'),
                                  manpower=s.num(m, 'manpower'), native_manpower=s.num(base, 'manpower'),
                                  softattack=s.num(m, 'softattack'), native_softattack=s.num(base, 'softattack')))
    checks.append('All 15 specialist models have real prerequisite tech IDs, lower manpower and lower IC-days than their contemporary native class.')
    germany = GERMANY / 'db/events/GMO/g02_force_preparation_breadth.txt'
    assert germany.exists()
    evidence = s.read(germany)
    assert 'GMO_FC_PREP_AIR_COMMITTED' in evidence
    assert 'Air-force and naval priorities remain independent' in evidence
    output = dict(checks=checks, air=air_rows, unavailable_air=unavailable, specialists=unit_rows,
                  personnel_mirrors=mirrors,
                  germany_read_only=str(germany),
                  limits=['Static source/data inspection only; no engine or campaign was launched.',
                          'Raw air arithmetic excludes doctrine surcharges, sliders, minister multipliers, conversion ratios, upgrades, gearing and rounding; these are not displayed queue prices.',
                          'Latest nominal-year research is a comparison, not a claim that Japan can or should research every branch by then.',
                          'Some obsolete pre-1930 aircraft can reach the engine time floor after stacking native assembly with priority; modern sampled models remain positive.',
                          'Custom-class minister targeting requires engine validation; source structure permits explicit unit commands but this audit cannot prove runtime inheritance behavior.'])
    (HERE / 'FORCE_TESTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    lines = ['# R9 force-value audit', '',
             'Historical R9 manufacturing and model-value analysis. The final recruitment policy is documented in FORCE_DELIVERY_AUDIT.md: the three custom classes are retired in new campaigns, and full Marines replace the Jungle Light production subsidy. Model comparisons below describe retained compatibility data, not a recommendation to recruit those classes.', '',
             *('- ' + c for c in checks), '',
             '## Aircraft manufacturing', '',
             'The existing selected-role rebates are retained. The other three aircraft classes now receive 1.5 IC / 18 days of common tooling from the same funded choice. Selected totals replace the common rebate. This supports a mixed air force without a second decision or a second setup bill.', '',
             '| Year | Unit | Base IC / days | Priority IC / days | Priority + native assembly days |',
             '| --- | --- | --- | --- | --- |']
    lines += [f"| {r['year']} | {r['unit']} | {r['base_ic']:g} / {r['base_days']:g} | {r['priority_ic']:g} / {r['priority_days']:g} | {r['priority_with_assembly_days']:g} |" for r in air_rows]
    lines += ['', 'These are raw model and national-adjustment comparisons, not final production queue quotes. Native aircraft assembly removes 41.76 INT/FTR, 42 CAS, 46.08 TAC, 47.52 NAV and 80 transport days. It stacks with the service programme. Domestic policy, minister effects, gearing and conversion/upgrade factors remain active; cheaper factories do not reduce fuel, manpower or operating supply.', '',
              '## Specialists and personnel', '',
              'The R8 specialist economy is already substantial: base forces cost 400 vs 640 IC-days with half the manpower; jungle infantry cost 760 vs 1,450 with 8 vs 13 manpower; SNLF cost 1,440 vs 3,360 with 9 vs 15 manpower before the native postwar Marine mechanisation model. Jungle terrain and SNLF landing/river advantages already exist. Added combat strength would obscure those distinct roles and create cheap replacements for full divisions. Their five-model progression and existing technology catch-up are retained.', '',
              'The change mirrors concrete garrison/infantry/marine minister effects onto their corresponding Japanese specialist class, including adverse values. Shared land effects are left as one copy. This keeps personnel choices useful across the selected force structure. Native formations, personalities and appointment dates retain their original entries.', '',
              'The current Japanese roster has five applicable concrete infantry effects across Static Defence, Decisive Battle and Razor personalities. Those now cover Jungle Light Infantry. Base Force/SNLF retain existing generic land benefits; there are no applicable concrete garrison/marine effects in that roster to duplicate. Foreign-only personalities are untouched.', '',
              '## Germany comparison and integration', '',
              'Read the installed Germany Overhaul Campaign GMO force-preparation and manufacturing-retooling events plus their secret-weapons tech entries. Reused the principle of independent service priorities, fixed production improvements and actual research/IC requirements. Did not copy Germany\'s very large research-unlock/retooling event graph into Japan or edit any German file.', '',
              'In build.prepare_catalog(), import force_value and call force_value.apply() immediately after human_campaign.apply(). In compile_mod(), call force_value.apply_personnel(TARGET, read, write, parse, serialise) immediately after japan_personnel.apply_roster(). No model/configure hook is needed; specialist_units.py remains untouched.', '',
              '## Validation limits', '', *('- ' + x for x in output['limits'])]
    (HERE / 'FORCE_AUDIT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'air_samples': len(air_rows), 'specialist_samples': len(unit_rows), 'personnel_mirrors': len(mirrors)}))


if __name__ == '__main__':
    run()
