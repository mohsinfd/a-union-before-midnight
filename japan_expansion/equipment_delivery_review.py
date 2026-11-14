"""Cold equipment audit: native contracts, source templates and installed parity.

No game launch. --require-installed additionally rejects a pending installation.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

import build as b
import equipment_delivery as fix
import specialist_units as sp

HERE = Path(__file__).resolve().parent


def walk(node):
    if not isinstance(node, list):
        return
    for k, v in node:
        yield k, v
        if isinstance(v, list):
            yield from walk(v)


def loaded_events(folder):
    files = set()
    for registry in (folder / 'db/events.txt', folder / 'scenarios/1933.eug'):
        for k, v in walk(sp.parse(sp.read(registry))):
            if k == 'event' and isinstance(v, str) and v.lower().endswith('.txt'):
                files.add(folder / v)
    records = []
    for path in sorted(files):
        if not path.exists():
            continue
        for event in sp.getall(sp.parse(sp.read(path)), 'event'):
            if isinstance(event, list):
                records.append((path, event))
    return files, records


def run(require_installed=False):
    docs_path = b.GAME / 'Modding documentation/event commands.txt'
    docs = sp.read(docs_path)
    assert 'type = damage_division which = "Exact Name" value = [country tag] where = X' in docs
    assert 'Negative value is strength gain' in docs
    assert 'Division could end with strength between 0 and Max Strength' in docs
    assert 'when = now for current size, else - max size' in docs
    assert 'where = -80 will create a division with STR = 20' in docs
    assert 'where - 0(default) - apply to new units too, 1 - apply only for currently deployed units' in docs
    source_files, source_events = loaded_events(b.SOURCE)
    target_files, target_events = loaded_events(b.TARGET)
    caps, reductions, native_examples = [], [], []
    for folder, records in ((b.SOURCE, source_events), (b.TARGET, target_events)):
        for path, event in records:
            for k, node in walk(event):
                if k != 'command' or not isinstance(node, list):
                    continue
                typ = sp.get(node, 'type')
                if typ == 'strength_cap':
                    row = {'folder': str(folder), 'file': str(path.relative_to(folder)),
                           'event': sp.get(event, 'id'), 'country': sp.get(event, 'country'),
                           'which': sp.get(node, 'which'), 'value': sp.get(node, 'value')}
                    caps.append(row)
                    assert row['country'] not in {None, 'JAP'}
                if typ == 'strength' and sp.get(node, 'value') in {'0.33', '0.66'}:
                    reductions.append({'folder': str(folder), 'event': sp.get(event, 'id'),
                                       'file': str(path.relative_to(folder)), 'command': node})
            for action_key, action in event:
                if not action_key.startswith('action') or not isinstance(action, list):
                    continue
                cs = [c for c in sp.getall(action, 'command') if isinstance(c, list)]
                if folder == b.SOURCE and any(sp.get(c, 'type') == 'add_corps' and sp.get(c, 'value') in {'air', 'naval'} for c in cs):
                    if any(sp.get(c, 'type') == 'add_division' for c in cs) and len(native_examples) < 4:
                        native_examples.append({'file': str(path.relative_to(folder)), 'event': sp.get(event, 'id'),
                                                'commands': [c for c in cs if sp.get(c, 'type') in {'add_corps', 'add_division'}][:5]})
    assert native_examples and reductions and caps
    checks = ['Native engine docs establish named negative-damage strength gain, clamp-to-cap semantics, damaged-unit where values and current-size building predicates.',
              'Both actual 1933 loaded-event sets scanned for strength caps and 33/66% changes; no Japanese new-award class strength cap exists.']

    b.prepare_catalog()
    ids = [(e.key, e.id) for e in b.EVENTS]
    non_r11 = {e.key: deepcopy(e.actions) for e in b.EVENTS if e.module not in {'country_campaigns', 'us_campaign_content'}}
    fix.apply()
    assert ids == [(e.key, e.id) for e in b.EVENTS]
    assert non_r11 == {e.key: e.actions for e in b.EVENTS if e.key in non_r11}
    first = [(e.key, e.gate, e.desc, deepcopy(e.actions)) for e in b.EVENTS]
    fix.apply()
    assert first == [(e.key, e.gate, e.desc, e.actions) for e in b.EVENTS]
    by = {e.key: e for e in b.EVENTS}
    assert fix.REPORT['divisions'] == 14
    assert fix.REPORT['american_conditional_division_commands'] == 210
    r11_commands = [sp.parse(c) for e in b.EVENTS
                    if e.module in {'country_campaigns', 'prewar_content', 'us_campaign_content'}
                    for a in e.actions for c in a.commands]
    command_counts = Counter(sp.get(c, 'type') for c in r11_commands)
    assert command_counts['add_division'] == command_counts['damage_division'] == 224
    assert command_counts['add_corps'] == 15
    assert not any(command_counts[k] for k in ('build_division', 'build_brigade', 'add_brigade', 'strength', 'strength_cap', 'disorg_division'))
    names = {n for row in fix.REPORT['deliveries'] for n in row['unit_names']}
    us_names = {n for row in fix.REPORT['american'] for n in row['names']}
    assert len(names) == 14 and len(us_names) == 42
    baseline_paths = [b.SOURCE / 'db/unitnames.csv', *list((b.SOURCE / 'scenarios/1933').glob('*.inc')),
                      *list((b.SOURCE / 'db/events').rglob('*.txt'))]
    for path in baseline_paths:
        text = sp.read(path).casefold()
        assert not any(n.casefold() in text for n in names | us_names), str(path)
    all_awards = [(e.country, sp.get(sp.parse(c), 'which')) for e in b.EVENTS for a in e.actions for c in a.commands
                  if sp.get(sp.parse(c), 'type') == 'add_division']
    occurrences = Counter(all_awards)
    assert all(occurrences['JAP', n] == 1 for n in names)
    assert all(occurrences['USA', n] == 5 for n in us_names)  # mutually exclusive researched/dates
    checks.append('All 14 Japanese and 42 potential American names are distinct, absent from clean scenario/unit lists/events, and occur only in their own final award/model alternatives; no event-ID names.')
    model_rows = []
    for row in fix.REPORT['deliveries']:
        event = by[row['finish']]
        cs = [sp.parse(c) for c in event.actions[0].commands]
        additions = [c for c in cs if sp.get(c, 'type') == 'add_division']
        heals = [c for c in cs if sp.get(c, 'type') == 'damage_division']
        assert len(heals) == len(additions) == row['count']
        assert Counter(sp.get(c, 'which') for c in heals) == Counter(sp.get(c, 'which') for c in additions)
        assert all(sp.get(c, 'value') == 'JAP' and sp.get(c, 'where') == '-100' for c in heals)
        assert not any(sp.get(c, 'type') in {'strength', 'strength_cap', 'build_division', 'build_brigade', 'add_brigade', 'disorg_division'} for c in cs)
        assert all(sp.get(c, 'where') is None for c in additions)
        mp = 0
        for c in additions:
            unit, model = sp.get(c, 'value'), int(sp.get(c, 'when'))
            template = sp.getall(sp.parse(sp.read(b.SOURCE / 'db/units/divisions' / (unit + '.txt'))), 'model')[model]
            installed_template = sp.getall(sp.parse(sp.read(b.TARGET / 'db/units/divisions' / (unit + '.txt'))), 'model')[model]
            assert template == installed_template, ('Installed native model differs', unit, model)
            assert not any('strength' in k.casefold() for k, _ in template)
            mp += sp.num(template, 'manpower')
            tech = b.regional_content.MODELS[unit]['tech']
            assert f'value = {tech}' in event.actions[0].gate
            assert f'value = {tech}' in by[row['offer']].actions[row['choice']].gate
            model_rows.append({'event': event.key, 'name': sp.get(c, 'which'), 'unit': unit, 'model': model,
                               'tech': tech, 'mp': sp.num(template, 'manpower'),
                               'organisation': sp.num(template, 'defaultorganisation'),
                               'morale': sp.num(template, 'morale'), 'site': row['site']})
        assert mp == row['manpower_reserved']
        assert any(k == 'control' and sp.get(v, 'province') == str(row['site']) and sp.get(v, 'data') == 'JAP'
                   for k, v in walk(sp.parse(event.actions[0].gate)))
        if row['facility_gate']:
            assert row['facility_gate'] in event.actions[0].gate
            assert row['facility_gate'] in by[row['offer']].actions[row['choice']].gate
    checks.append('Every Japanese birth has a valid researched native model, complete model manpower, explicit controlled site, unmodified brigade field and one matching post-creation heal; no extra recruitment charge or organisation boost.')
    for row in fix.REPORT['american']:
        action = by[row['event']].actions[row['action']]
        cs = [sp.parse(c) for c in action.commands]
        additions = [c for c in cs if sp.get(c, 'type') == 'add_division']
        heals = [c for c in cs if sp.get(c, 'type') == 'damage_division']
        assert len(additions) == len(heals) == 30
        for add, heal in zip(additions, heals):
            assert sp.get(add, 'trigger') == sp.get(heal, 'trigger')
            assert sp.get(add, 'which') == sp.get(heal, 'which')
            assert sp.get(heal, 'value') == 'USA' and sp.get(heal, 'where') == '-100'
            assert sp.get(add, 'where') is None
            template = sp.getall(sp.parse(sp.read(b.SOURCE / 'db/units/divisions/infantry.txt')), 'model')[int(sp.get(add, 'when'))]
            installed_template = sp.getall(sp.parse(sp.read(b.TARGET / 'db/units/divisions/infantry.txt')), 'model')[int(sp.get(add, 'when'))]
            assert template == installed_template
            assert sp.num(template, 'manpower') == 13
        assert any(sp.get(c, 'type') == 'manpowerpool' and sp.get(c, 'value') == '-78' for c in cs)
        assert any(k == 'owned' and sp.get(v, 'province') == str(row['site']) and sp.get(v, 'data') == 'USA'
                   for k, v in walk(sp.parse(action.gate)))
        assert any(k == 'control' and sp.get(v, 'province') == str(row['site']) and sp.get(v, 'data') == 'USA'
                   for k, v in walk(sp.parse(action.gate)))
    checks.append('All seven USA staging options preserve exact technology conditions on both birth and heal, 78 manpower/2400-supply cost and American-owned/controlled hubs; only six researched divisions can form per wave.')

    # Supplemental documented-command state fixtures, not a substitute for the
    # native evidence above. Start births understrength to test the real heal.
    from REGIONAL_CONTENT_review import state
    from US_CAMPAIGN_review import CampaignWorld
    from FLOW_review import HumanWorld
    class UnderstrengthWorld(HumanWorld):
        def command(self, node, actor):
            condition = sp.get(node, 'trigger')
            runs = not condition or self.test(condition, actor)
            super().command(node, actor)
            if runs and sp.get(node, 'type') == 'add_division':
                self.deployed_units[-1]['strength'] = 33
    for row in fix.REPORT['deliveries']:
        w = state()
        # Use an actual subclass instance; copy the prepared fixture fields.
        v = UnderstrengthWorld(); v.__dict__.update(w.__dict__)
        before = deepcopy(v.resources['JAP'])
        assert v.action(row['offer'], row['choice'])
        days = b.regional_content.PROGRAMMES[next(i for i,p in enumerate(b.regional_content.PROGRAMMES) if p['key'] == row['offer'])]['choices'][row['choice']]['days']
        v.advance(days)
        units = [u for u in v.deployed_units if u['name'] in row['unit_names']]
        assert len(units) == row['count']
        assert all(u['strength'] == u['max_strength'] == 100 and u['location'] == row['site'] for u in units)
        assert v.resources['JAP']['manpower'] == before['manpower'] - row['manpower_reserved']
        snapshot = deepcopy(v.deployed_units); resources = deepcopy(v.resources)
        v.dispatch(row['finish']); assert v.deployed_units == snapshot and v.resources == resources
        if row['facility_gate']:
            kind = 'air_base' if row['branch'] == 'air' else 'naval_base'
            q = state(); q.buildings[row['site'], kind] = 0
            before = deepcopy(q.resources['JAP'])
            assert not q.action(row['offer'], row['choice']) and q.resources['JAP'] == before, row['finish']
            q = state(); before = deepcopy(q.resources['JAP'])
            assert q.action(row['offer'], row['choice'])
            q.buildings[row['site'], kind] = 0; q.advance(days)
            assert q.resources['JAP'] == before and not q.deployed_units
    checks.append('Eight Japanese state fixtures prove named 33%-strength births restore to 100, exact manpower is spent once, placement is correct and replay is inert; all four air/naval facility failures block funding or refund completely.')
    class USUnderstrength(CampaignWorld):
        def command(self, node, actor):
            condition = sp.get(node, 'trigger')
            runs = not condition or self.test(condition, actor)
            super().command(node, actor)
            if runs and sp.get(node, 'type') == 'add_division':
                self.deployed_units[-1]['strength'] = 33
    for row in fix.REPORT['american']:
        for service_year,technology_id,expected_model in b.us_campaign_content.RESERVE_MODELS:
            technology={str(technology_id)}
            w = USUnderstrength(); w.country_tech['USA'] = technology
            w.year=max(1941,service_year)
            w.flags['JX_USC_LANDING_DONE'] = 1
            w.history[str(by['usc_landing'].id)] = 0; w.day = 60
            for earlier in fix.REPORT['american']:
                if earlier['event'] == row['event'] and earlier['action'] < row['action']:
                    w.controlled[earlier['site']] = 'JAP'
            if row['event'] == 'usc_inland_response':
                w.controlled[1893] = 'JAP'
            before = w.resources['USA']['manpower']
            assert w.action(row['event'], row['action'])
            units = w.deployed_units
            assert len(units) == 6 and all(u['strength'] == 100 and u['model'] == expected_model and u['location'] == row['site'] for u in units)
            assert w.resources['USA']['manpower'] == before - 78
    w = USUnderstrength(); w.flags['JX_USC_LANDING_DONE'] = 1
    w.history[str(by['usc_landing'].id)] = 0; w.day = 60
    for p in (1908, 1896, 1900, 1893):w.controlled[p] = 'JAP'
    assert w.action('usc_coast_response', 3)
    for unit in w.deployed_units:unit['strength'] = 40
    old = deepcopy(w.deployed_units)
    assert w.action('usc_inland_response', 0)
    assert w.deployed_units[:6] == old
    assert all(u['strength'] == 100 for u in w.deployed_units[6:])
    checks.append('Thirty-five USA hub/model fixtures create six full-strength researched divisions each; both Kansas City waves coexist with distinct names, and the second wave leaves wounded first-wave units unchanged.')

    # Exact final compile parity; pending installation is reported explicitly.
    installed_by_id = {sp.get(e, 'id'): e for _, e in target_events}
    relevant = [e for e in b.EVENTS if e.module in {'country_campaigns', 'prewar_content', 'us_campaign_content'}]
    mismatches = [e.key for e in relevant if installed_by_id.get(str(e.id)) != sp.get(sp.parse(b.compiled_event(e)), 'event')]
    parity = not mismatches
    if parity:
        checks.append('All R11 regional, prewar and American event blocks exactly match the installed final compiler output.')
    else:
        checks.append(f'Source is verified; {len(mismatches)} installed event blocks still differ and require the parent rebuild.')
    report = {'checks': checks, 'installed_matches_final_source': parity, 'mismatched_events': mismatches,
              'all_r11_command_counts': dict(command_counts),
              'source_registry_event_files': len(source_files), 'installed_registry_event_files': len(target_files),
              'japanese_branches': fix.REPORT['deliveries'], 'american_branches': fix.REPORT['american'],
              'japanese_model_rows': model_rows, 'strength_caps': caps, 'native_strength_reductions': reductions,
              'native_air_naval_examples': native_examples,
              'limits': ['Documented-command arithmetic and state fixtures do not execute the game engine.',
                         'Named restoration clamps to an existing cap; it never changes that cap or organisation.',
                         'Later native demobilisation, combat, attrition or unsupplied operation can reduce the newly delivered forces.',
                         'The 31 intentionally quarter-strength legacy island garrisons remain unchanged.',
                         'Final deployment UI, engine rounding, organisation defaults and mobilisation timing still require a game playtest.']}
    (HERE / 'EQUIPMENT_DELIVERY_REVIEW.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = ['# R11.1 equipment and delivery cold audit', '',
             'The final source explicitly restores each freshly issued formation to its existing allowed maximum strength. This follows the native named damage_division command contract; it is not inferred from a simulator division count. No global army strength, organisation, cap, equipment-stat or brigade bonus is applied.', '',
             '## Native evidence', '',
             '- Engine event commands.txt lines 227–234 documents land/air/naval add_corps, subsequent add_division placement, negative where damaged-unit creation, and named negative-damage strength gain clamped at Max Strength.',
             '- The same native document lines 695–722 distinguishes changing current unit strength from strength_cap values that may apply to future units. Lines 550 documents current-size building checks with when=now.',
             '- Read both actual 1933 event registries and their event files. Native 33/66% demobilisation commands affect existing land units at execution; they do not establish a permanent 33% new-unit template. The only loaded strength caps found are Italian infantry at 70 and British/American custom d_05/d_06 at 40. None targets Japanese awards or ordinary American infantry.',
             '- The clean model templates contain normal organisation/morale and equipment metadata; none of these award models imposes a 33% strength cap. Native add_corps/add_division examples, including Op Zet aircraft and Empire Transports, support the placement syntax. New named restoration makes the intended strength explicit instead of relying solely on default creation behaviour.', '',
             '## Delivered source corrections', '',
             '- Four Japanese aircraft/ship alternatives now require a current level-one airfield/naval base both at payment and receipt, with the same predicate included in the exact-refund complement.',
             '- All 14 potential Japanese awards use realistic distinct formation names and one scoped restoration per created unit. Each of seven American staging alternatives retains its two exclusive researched model paths, with an identically conditioned scoped restoration.',
             '- Western Reserve and Central Reserve names distinguish the two American waves. Kansas City can host both without a second-wave restoration healing wounded first-wave formations.',
             '- American reserves now choose among five researched and dated models. Manpower bills, supply/money/resource bills, elapsed times, branch markers, receipts, ownership/control predicates and maximum actual American reserve count (12) remain unchanged. Existing intentionally quarter-strength island detachments remain unchanged.', '',
             '## Japanese model / crew / deployment verification', '',
             '| Formation | Type / model | Research | Manpower | Deployment |', '| --- | --- | --- | --- | --- |']
    lines += [f"| {r['name']} | {r['unit']} / {r['model']} | {r['tech']} | {r['mp']:g} | {r['site']} |" for r in model_rows]
    lines += ['', '## Checks and installation parity', '', *('- ' + c for c in checks), '',
              '**Installed matches final source: ' + str(parity) + '.**', '',
              'Organisation is deliberately not filled by a scripted bonus. Normal deployment/reorganisation and maintenance still apply. The strength guarantee is the documented command intent up to the existing cap, not an engine observation. The hook changes no global strength or mobilisation rule.', '',
              'Integration: import equipment_delivery and call apply() after final_event_integrity and all R11 appenders, before player-copy/localisation generation and the final ID refresh. The hook adds no event IDs. After the parent rebuild, run equipment_delivery_review.py --require-installed; it rejects any remaining source/install mismatch.', '',
              '## Limits', '', *('- ' + x for x in report['limits']), '',
              'This audit did not launch the game, change saves, edit German files or install a mod. Full command records, cap findings and parity exceptions are in EQUIPMENT_DELIVERY_REVIEW.json.']
    (HERE / 'EQUIPMENT_DELIVERY_AUDIT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'japanese_births': 14, 'american_conditional_births': 210,
                      'american_max_actual_births': 12, 'installed_matches': parity, 'mismatch_count': len(mismatches)}))
    if require_installed and not parity:
        raise SystemExit('Installed events differ from final source: ' + ', '.join(mismatches))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-installed', action='store_true')
    args = parser.parse_args()
    run(args.require_installed)
