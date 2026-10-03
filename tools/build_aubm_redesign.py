"""Build a NON-INSTALLABLE event redesign workspace and complete coverage ledger.

Reads authored modules and optionally the installed custom modules. Never calls
the old B1 compiler, installer, executable, or a save migration. The staged tree
is an intermediate review artifact, not a playable mod or replacement overlay.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from dh_save_spans import Node, parse
from aubm_redesign_inventory import inventory

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build' / 'redesign'
MODULE_DIRS = ('india_v3', 'aubm_v4')


def registered_new_ids():
    from aubm_redesign_indian_stories import NEW_EVENT_IDS as stories
    from aubm_redesign_nepal import NEW_EVENT_IDS as nepal
    from aubm_redesign_bhutan import NEW_EVENT_IDS as bhutan
    from aubm_redesign_campaign_stories import NEW_EVENT_IDS as campaigns
    from aubm_redesign_decolonisation import NEW_EVENT_IDS as decolonisation
    from aubm_redesign_final_treaties import NEW_EVENT_IDS as treaties
    from aubm_naval_clock_fix import NEW_EVENT_IDS as naval_clocks
    from aubm_campaign_clock_fix import NEW_EVENT_IDS as campaign_clocks
    from aubm_release_ownership import NEW_EVENT_IDS as release_ownership
    from aubm_resolution_outcomes import NEW_EVENT_IDS as resolution_outcomes
    groups = [set(stories), set(nepal), set(bhutan), set(campaigns), set(decolonisation), set(treaties), set(naval_clocks), set(campaign_clocks), set(release_ownership), set(resolution_outcomes), registered_ported_ids()]
    if sum(map(len, groups)) != len(set.union(*groups)):
        raise ValueError('Added-content registries collide')
    return set.union(*groups)


def registered_ported_ids():
    # Explicit installed safety callbacks being brought into the authored stage.
    # They are not advertised as newly invented player-facing content.
    from aubm_redesign_withdrawal import NEW_EVENT_IDS as withdrawals
    from aubm_redesign_runtime_safety import NEW_EVENT_IDS as runtime
    return set(withdrawals) | set(runtime)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(root):
    files = {p.relative_to(root).as_posix(): p.read_bytes().decode('latin1')
             for folder in MODULE_DIRS
             for p in sorted((root / 'db/events' / folder).glob('*.txt'))}
    if not files:
        raise ValueError('No custom event modules found under ' + str(root))
    return files


def index(files):
    result = {}
    for path, text in files.items():
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            if eid in result:
                raise ValueError('Duplicate event ' + str(eid))
            result[eid] = (path, text[ev.start:ev.end], ev)
    return result


def compile_files(files):
    from aubm_redesign_prose import transform as prose
    from aubm_redesign_diplomacy import transform as diplomacy
    from aubm_redesign_settlements import transform as settlements
    from aubm_redesign_cooperation import transform as cooperation
    from aubm_redesign_replies import transform as replies
    from aubm_redesign_campaign_access import transform as campaign_access
    from aubm_redesign_crises import transform as crises
    from aubm_redesign_great_power_replies import transform as great_power_replies
    from aubm_redesign_indian_stories import transform as indian_stories
    from aubm_redesign_navy import transform as navy
    from aubm_redesign_nepal import transform as nepal
    from aubm_redesign_bhutan import transform as bhutan
    from aubm_redesign_economy import transform as economy
    from aubm_redesign_presentation import transform as presentation
    from aubm_redesign_regional_opportunities import transform as regional_opportunities
    from aubm_redesign_relationships import transform as relationships
    from aubm_redesign_navigation import transform as navigation
    from aubm_redesign_withdrawal import transform as withdrawal
    from aubm_redesign_runtime_safety import transform as runtime_safety
    from aubm_redesign_peace_scope import transform as peace_scope
    from aubm_redesign_armistice_ownership import transform as armistice_ownership
    from aubm_redesign_regional_replies import transform as regional_replies
    from aubm_redesign_bespoke_replies import transform as bespoke_replies
    from aubm_redesign_route_finish import transform as route_finish
    from aubm_redesign_aggression import transform as aggression
    from aubm_redesign_version import transform as version
    from aubm_redesign_focus_outcomes import transform as focus_outcomes
    from aubm_redesign_campaign_stories import transform as campaign_stories
    from aubm_redesign_decolonisation import transform as decolonisation
    from aubm_redesign_final_treaties import transform as final_treaties
    from aubm_redesign_western import transform as western
    from aubm_naval_clock_fix import transform as naval_clocks
    from aubm_campaign_clock_fix import transform as campaign_clocks
    from aubm_diplomacy_consistency import transform as diplomacy_consistency
    from aubm_release_ownership import transform_all as release_ownership
    from aubm_resolution_outcomes import transform as resolution_outcomes
    from aubm_victory_clarity import transform as victory_clarity
    stages = [('prose', prose), ('diplomacy', diplomacy),
              ('settlement_closure', settlements), ('cooperation', cooperation),
              ('foreign_replies', replies), ('campaign_access', campaign_access),
              ('crisis_choices', crises), ('great_power_replies', great_power_replies),
              ('indian_stories', indian_stories), ('navy', navy),
              ('nepal_merger', nepal), ('bhutan_merger', bhutan), ('economy_choices', economy),
              ('regional_opportunities', regional_opportunities),
              ('relationships', relationships), ('withdrawal', withdrawal),
              ('runtime_safety', runtime_safety), ('peace_scope', peace_scope),
              ('armistice_ownership', armistice_ownership), ('regional_replies', regional_replies),
              ('bespoke_replies', bespoke_replies),
              ('navigation', navigation),
              ('route_finish', route_finish),
              ('focus_outcomes', focus_outcomes), ('western_campaign', western),
              ('campaign_stories', campaign_stories),
              ('decolonisation', decolonisation),
              ('final_treaties', final_treaties),
              ('aggression', aggression),
              ('presentation', presentation), ('candidate_identification', version),
              ('naval_clocks', naval_clocks), ('campaign_clocks', campaign_clocks),
              ('diplomacy_consistency', diplomacy_consistency),
              ('release_ownership', release_ownership),
              ('clear_resolution_outcomes', resolution_outcomes),
              ('victory_clarity', victory_clarity)]
    output = dict(files)
    records = defaultdict(list)
    for dimension, transform in stages:
        output, reviewed = transform(output)
        for eid, entries in reviewed.items():
            records[eid].extend(dict(entry, dimension=entry.get('dimension', dimension)) for entry in entries)
    before, after = index(files), index(output)
    expected_new = registered_new_ids() - before.keys()
    if before.keys() - after.keys() or after.keys() - before.keys() != expected_new:
        raise ValueError('Existing IDs must survive; only explicitly registered new IDs may be added')
    for eid, entries in records.items():
        for record in entries:
            record['engine_tested'] = False
            record['full_lifecycle_review_complete'] = False
            if eid in after:
                record['staged_event_sha256'] = sha(after[eid][1].encode('latin1'))
    return output, dict(records)


def risk_register(files):
    """Per-event mechanical observations: candidates, NOT confirmed defects."""
    observations = {}
    for eid, (path, block, ev) in index(files).items():
        reasons = []
        if 'ind_aubm_route_' in block:
            reasons.append('global_route_dependency_requires_disposition')
        if any(term in (ev.get('name', '') + ' ' + ev.get('desc', '')).lower()
               for term in ('ledger', 'cumulative', 'route contract', 'framework', 'charter')):
            reasons.append('bureaucratic_language_candidate')
        if ev.get('persistent') == 'yes' and ev.get('save_date') == 'yes':
            reasons.append('persistent_dated_event_engine_test_needed')
        if any(ev.get(key) == 'yes' for key in ('one_action',)):
            reasons.append('one_action_is_not_a_silent_internal_event')
        kinds = []
        for af in ev.fields:
            if af.key == 'action' or (af.key or '').startswith('action_'):
                kinds.extend(c.get('type') for c in af.value.all('command'))
                tr = af.value.get('trigger')
                if isinstance(tr, Node) and tr.end - tr.start >= 10000:
                    reasons.append('large_existing_action_gate_requires_tooltip_review')
        if set(kinds) & {'peace', 'leave_alliance', 'end_puppet', 'make_puppet', 'independence', 'alliance'}:
            reasons.append('native_diplomatic_transaction_test_needed')
        observations[eid] = reasons
    return observations


def coverage_report(files, records, slept):
    report = inventory(files, slept_1933_ids=slept)
    risks = risk_register(files)
    for ev in report['events']:
        # A reviewed prose span or template invariant is not a complete event
        # review. Leave the full-lifecycle disposition pending in this first stage.
        ev['dimension_reviews'] = records.get(ev['id'], [])
        ev['mechanical_followup_candidates'] = risks[ev['id']]
    report['coverage']['events_with_dimension_work'] = sum(bool(records.get(e['id'])) for e in report['events'])
    report['coverage']['full_lifecycle_review_complete'] = 0
    return report


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def story_preview(files, story_ids, records):
    """Exact staged prose/buttons, not an imagined or installed-game preview."""
    events = index(files)
    lines = ['# New Indian stories: staged text preview', '',
             'These optional decisions are not installed or engine-playtested.',
             'The text and choices below are read from the generated event scripts.',
             'Completing one story does not select an alliance or unlock a national route.', '']
    for eid in sorted(story_ids):
        _, _, ev = events[eid]
        lines += ['## ' + ev.get('name'), '', ev.get('desc'), '']
        decision_desc = ev.get('decision_desc')
        if decision_desc and decision_desc != ev.get('desc'):
            lines += [decision_desc, '']
        for af in ev.fields:
            if af.key == 'action' or (af.key or '').startswith('action_'):
                lines.append('- ' + af.value.get('name', '(unnamed choice)'))
        lines += ['', f'Event ID: {eid}.', '']
    return '\n'.join(lines)


def safe_output(path):
    # No caller-controlled output can overlap an installed game, sources, or saves.
    resolved = path.resolve()
    allowed = (ROOT / 'build' / 'redesign').resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError('Output must be build/redesign or one of its children')
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--installed-root', type=Path, help='Read-only comparison; never patched')
    parser.add_argument('--save', type=Path, help='Read-only fingerprint only; never parsed or migrated')
    args = parser.parse_args()
    destination = safe_output(args.output)
    toolchain_paths = sorted((ROOT / 'tools').glob('*aubm_redesign*.py'))
    toolchain_hashes = {p.name: sha(p.read_bytes()) for p in toolchain_paths}
    source_root = ROOT / 'mod'
    sources = load(source_root)
    installed = load(args.installed_root) if args.installed_root else None
    if installed is not None:
        conflicts = (registered_new_ids() - registered_ported_ids()) & index(installed).keys()
        if conflicts:
            raise ValueError(f'Proposed story IDs already exist in installed input: {sorted(conflicts)}')
    stock_sources = ({p: (args.installed_root / p).read_bytes() for p in ('db/events/japan.txt','db/events/china.txt')}
                     if args.installed_root else {})
    stock_outputs, stock_reviews = {}, {}
    if stock_sources:
        from aubm_redesign_stock import transform_files as stock_bridge
        stock_outputs, stock_reviews = stock_bridge(stock_sources)
    save_hash = sha(args.save.read_bytes()) if args.save else None
    scenario = source_root / 'scenarios/1933.eug'
    scenario_source = scenario.read_bytes()
    from aubm_redesign_version import scenario as identify_scenario
    scenario_output = identify_scenario(scenario_source)
    slept = [int(n) for node in parse(scenario_source).all('sleepevent') for n in node.atoms()]
    output, records = compile_files(sources)
    from aubm_redesign_presentation import audit as presentation_audit
    presentation_report = presentation_audit(output)
    if presentation_report['hard_errors']:
        raise ValueError('Staged presentation budget/control-code errors: ' + str(presentation_report['hard_errors']))
    report = coverage_report(output, records, slept)
    if report['duplicate_ids'] or report['coverage']['events_without_numeric_id'] or report['callback_missing']:
        raise ValueError('Staged custom-module structural reference validation failed')
    before, after = index(sources), index(output)
    changed = sorted(eid for eid in before if before[eid][1] != after[eid][1])
    added = sorted(after.keys() - before.keys())
    blockers = [
        'Full event-by-event lifecycle and narrative review is unfinished; all full-lifecycle dispositions remain pending.',
        'Old global route/charter/focus machinery has not yet been replaced across the full event corpus.',
        'This authored-source stage does not yet incorporate every installed B1 safety/compiler change.',
        'Foreign withdrawal, coalition peace, government release/puppetry and hold timers need native engine tests.',
        'Added helper-text colour/overflow is not visually verified; presentation-audit.json lists remaining legacy funding helpers and layout risks.',
        'Fresh-1933 native playtesting has not been performed. Old-save migration/continuation is outside the current new-campaign release target.',
        'Opening event and scenario title identify the current unverified candidate; no main-menu artwork, installer or GitHub release is produced by this staging artifact.',
    ]
    from aubm_redesign_version import BUILD
    manifest = dict(build=BUILD, installable=False, engine_playtested=False,
                    scope='58 authored custom modules; foreign replies and explicit Japanese/Chinese stock safety adapters included',
                    scenario={'path': 'scenarios/1933.eug', 'source': sha(scenario_source), 'staged': sha(scenario_output)},
                    source_events=len(before), staged_events=len(after), changed_events=changed, added_events=added,
                    ported_safety_callback_ids=sorted(registered_ported_ids()),
                    coverage=report['coverage'], blockers=blockers,
                    presentation={k: v for k, v in presentation_report.items() if k != 'events'},
                    dimension_record_counts=dict(Counter(r['dimension'] for rr in records.values() for r in rr)),
                    toolchain_sha256=toolchain_hashes,
                    stock_bridge={p: {'source': sha(stock_sources[p]), 'staged': sha(raw),
                                      'engine_tested': False, 'output_root': 'staged-stock'}
                                  for p, raw in stock_outputs.items()},
                    files={p: {'source': sha(sources[p].encode('latin1')),
                               'staged': sha(t.encode('latin1'))} for p, t in output.items()},
                    save_fingerprint={'path': str(args.save), 'sha256': save_hash} if args.save else None)
    destination.mkdir(parents=True, exist_ok=True)
    for path, text in output.items():
        p = destination / 'staged-authored' / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode('latin1'))
    scenario_target = destination / 'staged-authored/scenarios/1933.eug'
    scenario_target.parent.mkdir(parents=True, exist_ok=True)
    scenario_target.write_bytes(scenario_output)
    write_json(destination / 'coverage.json', report)
    write_json(destination / 'reviews.json', records)
    write_json(destination / 'presentation-audit.json', presentation_report)
    if added:
        from aubm_redesign_indian_stories import NEW_EVENT_IDS as story_ids
        (destination / 'INDIAN_STORIES.md').write_text(story_preview(output, story_ids, records), encoding='utf-8')
    if stock_outputs:
        for path, raw in stock_outputs.items():
            p = destination / 'staged-stock' / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        write_json(destination / 'stock-bridge-reviews.json', stock_reviews)
    if installed is not None:
        from aubm_redesign_reconciliation import reconcile, fresh_dispositions
        reconciliation = fresh_dispositions(reconcile(sources, installed), output, records)
        for component in reconciliation['components']:
            eid = component['id']
            if eid in registered_ported_ids() and eid in after:
                component['implemented_in_staged_authored'] = True
                component['staged_sha256'] = sha(after[eid][1].encode('latin1'))
                component['implementation_scope'] = 'Registered withdrawal or dockyard family port; native execution unverified.'
        for unit in reconciliation['required_safety_units']:
            if unit['key'] == 'opponent_withdrawal':
                unit['status'] = 'staged_shared_family_port_native_verification_pending'
            if stock_reviews and unit['key'] in ('stock_japan', 'stock_china'):
                unit['status'] = 'explicit_stock_adapter_staged_native_validation_pending'
        write_json(destination / 'reconciliation.json', reconciliation)
        manifest['installed_reconciliation'] = {
            'count': reconciliation['installed_only_count'],
            'unexpected_ids': reconciliation['unexpected_installed_only_ids'],
            'missing_expected_ids': reconciliation['expected_ids_missing_from_installed_only'],
            'fresh_campaign_unresolved_ids': reconciliation['fresh_campaign_unresolved_ids'],
            'required_safety_units': reconciliation['required_safety_units'],
            'auto_merge_performed': False, 'report': 'reconciliation.json'}
        installed_report = inventory(installed)
        write_json(destination / 'installed-inventory.json', installed_report)
        active = index(installed)
        manifest['installed_comparison'] = {
            'root': str(args.installed_root), 'events': len(active),
            'installed_only_ids': sorted(active.keys() - before.keys()),
            'authored_only_ids': sorted(before.keys() - active.keys()),
            'same_id_different_body_count': sum(active[e][1] != before[e][1] for e in active.keys() & before.keys()),
            'hashes': {p: sha(t.encode('latin1')) for p, t in installed.items()},
        }
    # Re-read all protected inputs after artifact generation: fail if an external
    # edit/race changed our evidence, rather than certifying a mixed snapshot.
    if sources != load(source_root):
        raise RuntimeError('Authored source changed during staging; rebuild')
    if scenario.read_bytes() != scenario_source:
        raise RuntimeError('Authored scenario changed during staging; rebuild')
    if installed is not None and installed != load(args.installed_root):
        raise RuntimeError('Installed input changed during staging; rebuild')
    if any(raw != (args.installed_root / path).read_bytes() for path, raw in stock_sources.items()):
        raise RuntimeError('Installed stock input changed during staging; rebuild')
    if args.save and save_hash != sha(args.save.read_bytes()):
        raise RuntimeError('Save changed during staging; rebuild')
    if toolchain_hashes != {p.name: sha(p.read_bytes()) for p in toolchain_paths}:
        raise RuntimeError('Redesign tools changed during staging; rebuild')
    manifest['protected_inputs_unchanged'] = True
    write_json(destination / 'manifest.json', manifest)
    lines = ['# Event redesign: staged work, not a release', '',
             f"{len(before):,} original authored events preserved; {len(changed):,} existing event blocks changed; {len(added)} new events (stories and follow-ups).",
             'No event is signed off as fully redesigned or engine-tested.', '',
             '## Release blockers', ''] + ['- ' + b for b in blockers]
    lines += ['', '## Module coverage', '', '| Module | Events | Changed | Added |', '| --- | ---: | ---: | ---: |']
    for module in report['modules']:
        path = module['path']
        lines.append(f"| {path.rsplit('/', 1)[-1]} | {module['event_count']} | {sum(before[e][0] == path for e in changed)} | {sum(after[e][0] == path for e in added)} |")
    lines += ['', 'Full records: coverage.json, reviews.json, reconciliation.json and installed-inventory.json.',
              'Do not copy staged-authored into the active game. See manifest.json for exact hashes.', '']
    (destination / 'STATUS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('build', 'installable', 'source_events', 'staged_events',
                                             'coverage', 'protected_inputs_unchanged')}, indent=2))
    print('Changed event blocks:', len(changed))
    print('New story/follow-up events:', len(added))
    print('Review artifacts:', destination)


if __name__ == '__main__':
    main()
