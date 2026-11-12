"""Verify delivered recruitment retirement and civil-works commands in memory."""
from copy import deepcopy
import json
from pathlib import Path
import re

import build as b
import force_delivery_audit as fix
import specialist_units as s
from FORCE_review import applications, latest_model

HERE = Path(__file__).resolve().parent


def run():
    b.prepare_catalog()
    ids = [(e.key, e.id) for e in b.EVENTS]
    fix.apply()
    by = {e.key: e for e in b.EVENTS}
    assert ids == [(e.key, e.id) for e in b.EVENTS]
    before = deepcopy([(e.key, e.gate, e.actions) for e in b.EVENTS])
    fix.apply()
    assert before == [(e.key, e.gate, e.actions) for e in b.EVENTS]
    checks = ['Final pass preserves every event ID and is idempotent.']
    for key in fix.RECRUITMENT:
        assert by[key].gate == by[key].ready == fix.IMPOSSIBLE
        assert all(not a.commands for a in by[key].actions)
    for u in fix.RETIRED:
        for a in by['activate_' + u].actions:
            assert a.commands == [b.cmd('deactivate_unit_type', which=u)]
    for e in b.EVENTS:
        for a in e.actions:
            for text in a.commands:
                n = s.parse(text)
                assert not (s.get(n, 'type') == 'activate_unit_type' and s.get(n, 'which') in fix.RETIRED)
                assert not (s.get(n, 'type') == 'trigger' and s.get(n, 'which') in {'@activate_' + u for u in fix.RETIRED})
    checks.append('All six recruitment offers are unreachable; all direct and indirect custom activation paths are closed.')
    welcome = [s.parse(c) for c in by['welcome'].actions[0].commands]
    assert {s.get(n, 'which') for n in welcome if s.get(n, 'type') == 'deactivate_unit_type'} == set(fix.RETIRED)
    assert not any(s.get(s.parse(c), 'type') == 'deactivate_unit_type' and s.get(s.parse(c), 'which') == 'garrison'
                   for e in b.EVENTS for a in e.actions for c in a.commands)
    checks.append('Opening disables only the three custom classes; ordinary garrison production and island defenders remain intact.')
    rebates = {}
    for c in by['army_production_finish_0'].actions[0].commands:
        n = s.parse(c)
        if s.get(n, 'type') in {'build_cost', 'build_time'}:
            k = (s.get(n, 'which'), s.get(n, 'type'))
            assert k not in rebates
            rebates[k] = s.num(n, 'value')
    assert set(u for u, kind in rebates) == {'infantry', 'bergsjaeger', 'marine'}
    assert rebates['marine', 'build_cost'] == -1.6
    assert rebates['marine', 'build_time'] == -63
    checks.append('Army infantry priority now supports exactly Infantry, Mountain Infantry and full Marines, with each correctly priced from its own model-zero baseline.')

    # Full personnel writing uses memory-backed files only.
    virtual = Path('FORCE_DELIVERY_virtual')
    generated = {}
    def write(path, text):
        generated[str(path)] = text
    def read(path):
        return generated[str(path)]
    b.japan_personnel.apply_roster(s.SOURCE, virtual, s.read, write, s.parse, b.serialise)
    b.force_value.apply_personnel(virtual, read, write, s.parse, b.serialise)
    fix.apply_personnel(virtual, read, write, s.parse, b.serialise)
    first = deepcopy(generated)
    fix.apply_personnel(virtual, read, write, s.parse, b.serialise)
    assert first == generated
    ministers = s.parse(read(virtual / 'db/ministers/minister_personalities.txt'))
    civil = next(m for m in s.getall(ministers, 'minister') if s.get(m, 'trait') == fix.CIVIL_TRAIT)
    commands = s.getall(civil, 'command')
    assert len(commands) == 5
    assert {(s.get(c, 'type'), s.get(c, 'which'), s.get(c, 'when'), s.num(c, 'value')) for c in commands} == set(fix.CIVIL_COMMANDS)
    roster = {r[0]: r for l in read(virtual / 'db/ministers/ministers_jap.csv').splitlines() if (r := l.split(';'))[0].isdigit()}
    source_rows = {r[0]: r for l in s.read(s.SOURCE / 'db/ministers/ministers_jap.csv').splitlines() if (r := l.split(';'))[0].isdigit()}
    assert roster['50066'] == source_rows['50066']
    assert roster['286122'][2] == 'Fujiwara Ginjiro (Civil Works)'
    assert roster['286122'][3:8] == ['1937', '1951', '1961', 'PA', fix.CIVIL_TRAIT]
    checks.append('Fujiwara final roster/personality output round-trips and is idempotent; original 50066 unchanged, alternate 286122 identifiable and available 1937–1951.')

    # Primary local engine metadata: valid group, scope and parameter names.
    primary = s.read(s.SOURCE / 'db/ministers/minister_personalities.txt')
    assert 'province - modifiers to province buildings production time and cost' in primary
    assert 'when = all (default - means both cost and time bonus) / time / cost' in primary
    assert '/ land / navy / air / infantry' in primary
    assert '/ d_09 / d_10 / d_11 / d_12' in primary
    engine = s.read(b.GAME / 'Modding documentation/event commands.txt')
    assert 'type = deactivate_unit_type which = [division or brigade type]' in engine
    assert 'max_amphib_mod' in engine
    germany_path = b.GAME / 'Mods/Germany Overhaul Campaign/db/ministers/minister_personalities.txt'
    germany = s.read(germany_path)
    assert 'type = province which = ic when = cost value = -0.15' in germany
    assert 'type = province which = infra when = time value = -0.20' in germany
    checks.append('Exact building cost/time, navy group and custom-unit/deactivation syntax confirmed by local engine metadata and actual installed German definitions.')

    apps = applications()
    rows = []
    for u, info in s.CLASSES.items():
        for i, m in enumerate(s.models(u)):
            year = s.model_years(u)[i]
            idx = latest_model(apps, info['base'], year)
            base = s.getall(s.parse(s.read(s.SOURCE / 'db/units/divisions' / (info['base'] + '.txt'))), 'model')[idx]
            fields = ('softattack', 'hardattack', 'defensiveness', 'toughness', 'defaultorganisation', 'morale', 'maxspeed', 'transportweight', 'supplyconsumption')
            installed_path = b.TARGET / 'db/units/divisions' / (u + '.txt')
            installed = s.getall(s.parse(s.read(installed_path)), 'model')[i] if installed_path.exists() else None
            rows.append(dict(unit=u, year=year, model=i, base=info['base'], base_model=idx,
                             stats={k: s.num(m, k) for k in fields},
                             native={k: s.num(base, k) for k in fields},
                             installed={k: s.num(installed, k) for k in fields} if installed else None))
    output = dict(checks=checks, retired=fix.REPORT['retired'], civil_commands=fix.CIVIL_COMMANDS,
                  specialists=rows, original_fujiwara=roster['50066'], alternate_fujiwara=roster['286122'])
    (HERE / 'FORCE_DELIVERY_TESTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    lines = ['# Force delivery audit: retire the three classes; make Fujiwara explicit', '',
             '## Delivered changes', '',
             '- New campaigns cannot recruit Naval Base Force, Jungle Light Infantry or SNLF. All six related offers are retired, their activation receivers only deactivate the corresponding custom class, and the opening action explicitly disables all three. Existing type registrations and model slots remain for compatibility. Existing deployed units are not deleted or converted.',
             '- Infantry priority now improves standard Infantry, Mountain Infantry and full Marines. Marine tooling grants -1.6 IC and -63 baseline days. Normal Marine research is required. Ordinary garrisons and the local island defence packages are preserved.',
             '- Fujiwara\'s alternate appointment now has the distinct menu name **Fujiwara Ginjiro (Civil Works)** and changes both construction price and construction time. It retains its 1937 opening year and 1951 retirement cutoff.', '',
             '## Why the earlier classes could feel detrimental', '',
             'Cheap construction did not compensate for every practical disadvantage. Models have the same baseline organisation and morale as their native parent; there is no elite endurance bonus. Every formation still counts as one division for command and amphibious limits. The actual source land command limits are 12/9/6/3 divisions by rank and the base amphibious allowance is 1, expanded by doctrine. A smaller custom formation does not consume a fraction of that allowance.', '',
             '| Class / year | Soft attack custom/native | Hard attack | Defence | Toughness | Org/morale | Transport weight | Supply |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        a, n = r['stats'], r['native']
        def pair(k):
            return f'{a[k]:g}/{n[k]:g}'
        lines.append(f"| {r['unit']} {r['year']} | {pair('softattack')} | {pair('hardattack')} | {pair('defensiveness')} | {pair('toughness')} | {pair('defaultorganisation')}, {pair('morale')} | {pair('transportweight')} | {pair('supplyconsumption')} |")
    lines += ['',
              'Naval Base Force: 1937 soft attack 6 vs garrison 8 and toughness 20 vs 40. Defence is only 38 vs 35; organisation/morale stay 30/30. Speed remains zero. Transport weight is **5 for both**, so the earlier claim of a shipping advantage over normal garrisons was incorrect. It cannot replace a mobile follow-up formation.', '',
              'Jungle Light Infantry: 1937 attack 8 vs infantry 10 and defence 30 vs 35, without an organisation or morale advantage (both 30/30). Jungle attack penalty -50% vs -70% and swamp -45% vs -60% do produce a local advantage: terrain-only jungle attack 4 vs 3, and swamp 4.4 vs 4. Outside that niche, lower firepower hurts. Jungle movement -20% vs -35% and swamp -15% vs -25% help only those terrains. Snow/frozen/mountain penalties remain normal infantry values; native Mountain Infantry has smaller penalties in those environments. The custom class permits only artillery, AA and engineer attachments; native infantry permits 13 attachment types, including armour and tank destroyers. It was a poor general-purpose replacement for continental conquest.', '',
              'SNLF: 1937 soft attack 9 vs Marine 10 and defence/toughness 30/36 vs 35/40. Both have organisation/morale 35/40. SNLF landing penalty -15% vs Marine -20% gives terrain-only soft attack **7.65 vs 8**: the five-point landing bonus does not recover the lost firepower in each division counted toward the assault limit. River penalty -5% vs -10% similarly gives 8.55 vs 9. Transport weight 8 vs 10 may fit more troops aboard some ships, but does not enlarge the amphibious combat allowance. SNLF also omits native Marine cavalry, self-propelled artillery/AA and tank-destroyer attachment options.', '',
              'These terrain products isolate the listed model and terrain values. They are not simulated battle results; technology, leaders, experience, ESE, weather, stacking and enemy fire also matter. The full JSON records current installed model values alongside source-derived designs for comparison.', '',
              '## Personnel inheritance and command metadata', '',
              'The division-type metadata assigns real types garrison/infantry/marine, sprites and statistics groups; its value=0.8 is explicitly a military-power calculation value, not a direct combat-strength bonus. Model equipment blocks are diagnostic display metadata and do not restore the missing combat stats. Specialist research mirrors explicitly target each custom ID. The minister file header explicitly supports d_10/d_11/d_12 as concrete targets; five Japanese concrete infantry personality effects were mirrored to Jungle Light in R9, while generic land effects remain a single copy. This does not add elite organisation or morale. Full normal classes remove that extra custom-target dependency.', '',
              'Primary references: Blood and Iron db/units/division_types.txt format notes; db/ministers/minister_personalities.txt header; db/units/modifiers.csv; db/misc.txt land-command, amphibious and garrison settings; installed Modding documentation/event commands.txt activate/deactivate and max_amphib_mod entries. Reviewed Germany Overhaul Campaign db/ministers/minister_personalities.txt, which actually uses separate province/ic/infra cost and time commands. German files were read only.', '',
              '## What Fujiwara previously did, and why the price could look unchanged', '',
              'There are two distinct profiles of the same historical person. Original appointment **50066** is Administrative Genius, available from 1904, with +5% national production and +5% energy/metal/rare-material output. It has no factory or infrastructure construction discount. Alternate **286122** is the PA civil-works appointment, available from **1937** through the 1951 retirement cutoff. Listing it in the minister roster does not appoint it automatically.', '',
              'The earlier alternate used exactly province/infra/time=-0.12, province/ic/time=-0.05, and unit/navy/time=+0.04. Those are valid supported commands. They intentionally changed time only: the daily IC price could remain unchanged. They applied only while that alternate was actually the appointed Armament Minister. Therefore unchanged daily IC alone did not establish an engine failure.', '',
              'The delivered alternate uses:', '',
              '```text',
              'type = province which = infra when = time value = -0.12',
              'type = province which = infra when = cost value = -0.12',
              'type = province which = ic when = time value = -0.05',
              'type = province which = ic when = cost value = -0.05',
              'type = unit which = navy when = time value = 0.04',
              '```', '',
              'With every other modifier neutral, the source building bases illustrate the change: infrastructure 1 IC × 360 days becomes **0.88 IC × 316.8 days**; a factory 5 IC × 360 days becomes **4.75 IC × 342 days**. These imply 22.56% and 9.75% fewer IC-days respectively before rounding and other national/provincial modifiers. Naval division time grows by four percentage points; ship IC cost and CAG attachments receive no new modifier. Actual queue values depend on the other ministers, policies, technology and location. Compare a newly quoted order for the same province/model after appointing the Civil Works profile; do not compare its price with a different province or the original Fujiwara profile.', '',
              '## Integration and verification', '',
              'Import force_delivery_audit. Call apply() as the final catalogue pass after force_value and all flow/accessibility passes, before IDS update and localisation generation. Call apply_personnel(TARGET, read, write, parse, serialise) after japan_personnel.apply_roster and force_value.apply_personnel. No specialist_units.py edit or additional model hook is needed.', '',
              *('- ' + c for c in checks), '',
              'All writes during verification were in-memory fixtures plus these FORCE_DELIVERY reports. No game installation or save was changed, and the game was not launched. Runtime queue refresh, cabinet appointment UI and campaign difficulty still need an engine playtest.']
    (HERE / 'FORCE_DELIVERY_AUDIT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'specialist_model_comparisons': len(rows), 'retired_offers': len(fix.RECRUITMENT)}))


if __name__ == '__main__':
    run()
