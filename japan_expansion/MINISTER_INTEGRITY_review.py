"""Read installed Japan and exercise final minister hooks without installation."""
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import re

import build as b
import minister_integrity as check
import specialist_units as sp

HERE = Path(__file__).resolve().parent
FIELDS = ('id', 'office', 'name', 'start', 'retirement', 'end', 'ideology', 'trait', 'loyalty', 'portrait', 'sentinel')


def roster(text):
    return {r[0]: r for l in text.splitlines() if (r := l.split(';'))[0].isdigit()}


def localisation(folder):
    found = defaultdict(list)
    for path in sorted(folder.glob('*.csv')):
        for line in sp.read(path).splitlines():
            cells = line.split(';')
            if len(cells) > 1 and cells[0]:
                found[cells[0]].append({'file': path.name, 'english': cells[1]})
    return found


def effective(command):
    typ = sp.get(command, 'type')
    _, _, which, when = check.SCHEMA[typ]
    return (typ, sp.get(command, 'which', which), sp.get(command, 'when', when), float(sp.get(command, 'value')))


def run():
    # Evidence is read before preparing any in-memory source catalogue.
    paths = {name: b.TARGET / 'db/ministers' / name for name in ('ministers_jap.csv', 'minister_personalities.txt')}
    installed_text = {name: sp.read(p) for name, p in paths.items()}
    hashes = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in paths.items()}
    installed = check.validate(installed_text['ministers_jap.csv'], installed_text['minister_personalities.txt'])
    rows = roster(installed_text['ministers_jap.csv'])
    source_rows = roster(sp.read(sp.SOURCE / 'db/ministers/ministers_jap.csv'))
    assert set(source_rows) <= set(rows), 'Original Japanese appointment removed'
    changes = []
    for mid, r in rows.items():
        old = source_rows.get(mid)
        if old is None:
            changes.append({'id': int(mid), 'kind': 'added', 'row': dict(zip(FIELDS, r))})
        elif old != r:
            changes.append({'id': int(mid), 'kind': 'modified', 'name': r[2],
                            'fields': {FIELDS[i]: {'before': a, 'after': v} for i, (a, v) in enumerate(zip(old, r)) if a != v}})
    assert {x['id'] for x in changes if x['kind'] == 'modified'} == {50010, 50131, 50164, 50167, 50369, 50370}
    assert sum(x['kind'] == 'added' for x in changes) == 11
    checks = ['Every installed Japanese appointment resolves uniquely, matches its office and has valid dates/ideology; no Generic fallback.',
              'All original appointment IDs survive; exactly six original rows differ and eleven appointments were added.']
    global_ids = defaultdict(list)
    for p in (b.TARGET / 'db/ministers').glob('ministers_*.csv'):
        for mid in roster(sp.read(p)):
            if mid in rows:
                global_ids[mid].append(p.name)
    assert all(v == ['ministers_jap.csv'] for v in global_ids.values()), global_ids
    assert len(global_ids) == len(rows)
    checks.append('All Japanese appointment IDs are unique across the installed country minister rosters.')

    local = localisation(b.TARGET / 'config')
    definitions = sp.getall(sp.parse(installed_text['minister_personalities.txt']), 'minister')
    used = {x['trait'].casefold() for x in installed['roster']}
    used_definitions = [m for m in definitions if sp.get(m, 'trait').casefold() in used]
    local_rows = []
    for m in used_definitions:
        for field in ('name', 'desc'):
            key = sp.get(m, field)
            matches = local.get(key, [])
            assert matches and all(r['english'].strip() for r in matches), (sp.get(m, 'trait'), field, key)
            assert len({r['english'] for r in matches}) == 1, ('Conflicting localisation', key, matches)
            local_rows.append({'trait': sp.get(m, 'trait'), 'field': field, 'key': key, 'matches': matches})
    checks.append('All 180 used trait name/description keys resolve to nonempty English; duplicated keys have identical text.')

    # Numeric prose audit across every custom personality, including the prior
    # installed descriptions; shared native prose mostly has no numeric claims.
    custom = [m for m in used_definitions if sp.get(m, 'trait').startswith('jx ')]
    assert len(custom) == 13
    numeric = []
    for m in custom:
        description = local[sp.get(m, 'desc')][0]['english']
        prose_numbers = {abs(float(n)) for n in re.findall(r'(?<!\w)[+-]?\d+(?:\.\d+)?', description) if abs(float(n)) < 100}
        command_numbers = {abs(sp.num(c, 'value')) * (1 if sp.get(c, 'type') == 'diplomacy_chances' else 100)
                           for c in sp.getall(m, 'command')}
        assert prose_numbers == command_numbers, (sp.get(m, 'trait'), prose_numbers, command_numbers)
        numeric.append({'trait': sp.get(m, 'trait'), 'numbers': sorted(command_numbers),
                        'commands': [effective(c) for c in sp.getall(m, 'command')], 'installed_description': description})
    checks.append('All 13 custom descriptions contain exactly their command magnitudes; alliance chance uses points, percentage commands use fractions.')

    # Rebuild all personnel passes into memory and compare command effects,
    # proving the new source hook improves copy without quietly rebalancing.
    b.prepare_catalog()
    before_personalities = deepcopy(b.japan_personnel.PERSONALITIES)
    check.apply()
    assert [e[:4] + (e[5],) for e in before_personalities] == [e[:4] + (e[5],) for e in b.japan_personnel.PERSONALITIES]
    fixed = deepcopy(b.japan_personnel.PERSONALITIES)
    check.apply()
    assert fixed == b.japan_personnel.PERSONALITIES
    virtual = Path('MINISTER_INTEGRITY_virtual')
    generated = {}
    def write(path, value):
        generated[str(path)] = value
    def read(path):
        return generated[str(path)]
    b.japan_personnel.apply_roster(sp.SOURCE, virtual, sp.read, write, sp.parse, b.serialise)
    b.force_value.apply_personnel(virtual, read, write, sp.parse, b.serialise)
    b.force_delivery_audit.apply_personnel(virtual, read, write, sp.parse, b.serialise)
    b.unique_divisions.install_personnel(virtual, read, write, sp.parse, b.serialise)
    b.unique_attachments.install_personnel(virtual, read, write, sp.parse, b.serialise)
    candidate = check.apply_personnel(virtual, read, write, sp.parse, b.serialise)
    assert candidate['roster'] == installed['roster']
    assert candidate['commands'] == installed['commands']
    assert candidate['fallback_to_generic'] == 0
    checks.append(f'Final source hooks round-trip all 383 appointments and {len(installed["commands"])} used-trait commands; new subtype effects preserve their native parent magnitudes and penalties.')

    # Negative fixtures demonstrate detection, rather than merely a happy path.
    failures = []
    source_roster = generated[str(virtual / 'db/ministers/ministers_jap.csv')]
    source_traits = generated[str(virtual / 'db/ministers/minister_personalities.txt')]
    invalid_category = sp.parse(source_traits)
    civil = next(m for m in sp.getall(invalid_category, 'minister') if sp.get(m, 'id') == '1211')
    sp.replace(sp.getall(civil, 'command')[0], 'which', 'railway_factory')
    invalid_timing = sp.parse(source_traits)
    pilots = next(m for m in sp.getall(invalid_timing, 'minister') if sp.get(m, 'id') == '1202')
    sp.replace(sp.getall(pilots, 'command')[0], 'when', 'unsupported_scope')
    fixtures = {
        'unresolved trait': (source_roster.replace(';jx joint logistics;', ';unresolved minister trait;', 1), source_traits),
        'wrong office': (source_roster.replace(';jx joint logistics;', ';jx pilot continuity;', 1), source_traits),
        'duplicate appointment ID': (source_roster + '\n' + next(l for l in source_roster.splitlines() if l.startswith('50131;')), source_traits),
        'invalid ideology': (source_roster.replace(';PA;jx joint logistics;', ';XX;jx joint logistics;', 1), source_traits),
        'invalid command category': (source_roster, b.serialise(invalid_category)),
        'invalid command timing': (source_roster, b.serialise(invalid_timing)),
    }
    for label, (rtext, ptext) in fixtures.items():
        try:
            check.validate(rtext, ptext)
        except ValueError:
            failures.append(label)
        else:
            raise AssertionError('Bad fixture accepted: ' + label)
    checks.append(f'All {len(failures)} negative fixtures are rejected: missing trait, office mismatch, duplicate appointment, bad ideology, bad category and bad timing.')
    assert hashes == {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in paths.items()}
    checks.append('Installed roster/personality hashes are unchanged by this audit; no installation or game launch.')

    source_defs = {sp.get(m, 'trait').casefold(): m for m in sp.getall(sp.parse(sp.read(sp.SOURCE / 'db/ministers/minister_personalities.txt')), 'minister')}
    legacy_changes = []
    for m in used_definitions:
        old = source_defs.get(sp.get(m, 'trait').casefold())
        if old is not None and m != old:
            old_commands = sp.getall(old, 'command')
            new_commands = sp.getall(m, 'command')
            assert all(c in new_commands for c in old_commands)
            legacy_changes.append({'trait': sp.get(m, 'trait'), 'added_commands': [c for c in new_commands if c not in old_commands]})
    # Every added command must be an exact native-parent alias, not an
    # unreviewed buff merely using an allowed custom target name.
    parents={'d_11':'infantry',**{u:i['base'] for u,i in b.unique_divisions.CLASSES.items()},
             **{u:i['base'] for u,i in b.unique_attachments.ATTACHMENTS.items()}}
    for row in legacy_changes:
        original=sp.getall(source_defs[row['trait'].casefold()],'command')
        for command in row['added_commands']:
            clone=deepcopy(command);which=sp.get(clone,'which')
            assert which in parents,which
            sp.replace(clone,'which',parents[which])
            assert effective(clone) in [effective(c) for c in original],(row['trait'],command)
    summary = {'installed_appointments': len(rows), 'original_appointments': len(source_rows),
               'unchanged_original_rows': len(source_rows) - sum(x['kind'] == 'modified' for x in changes),
               'modified_original_rows': sum(x['kind'] == 'modified' for x in changes),
               'added_appointments': sum(x['kind'] == 'added' for x in changes),
               'used_personalities': installed['traits'], 'custom_personalities': len(custom),
               'used_trait_commands': len(installed['commands']), 'generic_fallbacks': 0,
               'localisation_keys': len(local_rows), 'negative_fixtures_rejected': len(failures),
               'future_placeholder_rows': sum(r[3] == '1999' for r in rows.values())}
    result = {'summary': summary, 'checks': checks, 'roster': installed['roster'], 'commands': installed['commands'],
              'roster_changes': changes, 'legacy_trait_changes': legacy_changes,
              'custom_numeric_audit': numeric, 'localisation': local_rows,
              'command_derived_descriptions': [{'id': e[1], 'trait': e[0], 'description': e[4]} for e in fixed],
              'installed_hashes': hashes}
    (HERE / 'MINISTER_INTEGRITY_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(installed['roster'][0]))
    writer.writeheader(); writer.writerows(installed['roster'])
    (HERE / 'MINISTER_INTEGRITY_ROSTER.csv').write_text(stream.getvalue(), encoding='utf-8')
    lines = ['# Complete Japanese minister integrity audit', '',
             f"Checked all **{summary['installed_appointments']} installed Japanese appointments**, using **{summary['used_personalities']} distinct personalities** and **{summary['used_trait_commands']} command entries**. All resolve uniquely, match their office, and avoid Generic fallback. This is a full-roster check, not a Fujiwara-only spot check.", '',
             '## What changed in the source', '',
             'No minister balance values required correction. The new final hook generates all 13 added personality descriptions directly from the commands, closing a quiet wording gap: naval equipment research excludes naval doctrines; aircraft equipment research excludes air doctrines; Fleet Carrier means the carrier class, not Light Carrier or CAG; resource/all includes oil and money as well as materials. Cost, time, organisation, morale and chance-point effects are labelled separately. It also validates the complete generated roster after all personnel writers.', '',
             'The 13 existing descriptions already had matching numeric magnitudes. Their duplicate entries in japan_rising.csv and mods.csv were identical. The new source wording improves scope and prevents later numerical copy drift; it does not claim an engine bug or silently buff every historical minister.', '',
             '## Full roster and trait coverage', '',
             f"- Original rows: {summary['original_appointments']}; unchanged original rows: {summary['unchanged_original_rows']}; modified originals: {summary['modified_original_rows']}; added appointments: {summary['added_appointments']}.",
             '- Trait names and office tokens resolve case-insensitively, as the native file itself uses mixed case. Head of State, all nine other offices, and default/all position semantics are handled. No used personality relies on the all-office default.',
             '- Every used command type, which category and when scope is checked against the native minister metadata, including concrete custom unit targets. Numeric values must be finite and nonzero. Shared group effects and per-class effects are distinguished.',
             '- Omitted when on unit/extra means both construction cost and time; omitted when on research means time; omitted which on unit/research/resource means all; production defaults to national production. Native Dismal Enigma uses the shipped combined-scope intelligence_network when=all form.',
             f"- All {summary['localisation_keys']} used name/description keys resolve to nonempty English. Duplicate keys must agree. No missing or conflicting key was found.",
             '- Dates, ideology codes, roster structure, unique appointment IDs and unique personality IDs/names were checked. Japanese IDs also have no collisions with other installed country minister rosters.',
             f"- {summary['future_placeholder_rows']} native rows start in 1999; these deliberate unavailable placeholders were reported and preserved. Validation is not a claim that all 383 appointments should be selectable in 1933.", '',
             '## Every original-row modification', '',
             '| ID | Name | Field changes |', '| --- | --- | --- |']
    for row in changes:
        if row['kind'] == 'modified':
            fields = '; '.join(f"{k}: {v['before']} → {v['after']}" for k, v in row['fields'].items())
            lines.append(f"| {row['id']} | {row['name']} | {fields} |")
    lines += ['', 'All other original appointments retain their source fields. Original traits retain every native command. Three inherited personalities (Static Defence, Decisive Battle and Razor) also contain the five R9 concrete Jungle Light parity commands; that class is retired from new recruitment. No native formation effect was replaced or removed.', '',
              '## All eleven added appointments', '',
              '| ID | Person / office | Trait | Availability |', '| --- | --- | --- | --- |']
    for row in changes:
        if row['kind'] == 'added':
            r = row['row']
            lines.append(f"| {r['id']} | {r['name']} / {r['office']} | {r['trait']} | {r['start']}–{r['retirement']} |")
    lines += ['', 'The other two custom traits are Joint Logistics for Abe Nobuyuki as Chief of Staff (50131) and Pilot Continuity for Sugawara Michio as Chief of Air (50164), giving 13 custom personalities across 11 additions and two reassigned original appointments.', '',
              '## Exact custom effects generated from commands', '',
              '| Personality | Effects |', '| --- | --- |']
    lines += [f'| {e[0]} ({e[1]}) | {e[4]} |' for e in fixed]
    lines += ['', '## Evidence and validation', '', *('- ' + c for c in checks), '',
              'Primary evidence: installed and baseline db/ministers/ministers_jap.csv; native minister_personalities.txt header and definitions; db/units/division_types.txt and brigade_types.txt; all installed config CSV files. Full 383-row mapping is in MINISTER_INTEGRITY_ROSTER.csv; the JSON includes every normalized command, localisation source, original diff and installed-file hash.', '',
              'Integration: call minister_integrity.apply() after force_delivery_audit.apply(), before localisation generation. Call minister_integrity.apply_personnel(TARGET, read, write, parse, serialise) after all other personnel writers. No additional installation files or new personality IDs are required.', '',
              'Limits: this validates source and installed data against shipped command contracts. It does not launch the engine, appoint every minister, measure save-game cached effects, or claim every political event/ideology makes every person available. No saves or German mod files were edited.']
    (HERE / 'MINISTER_INTEGRITY_AUDIT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(checks), **summary}))


if __name__ == '__main__':
    run()
