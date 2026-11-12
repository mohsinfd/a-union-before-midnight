"""Make a separate, offline repair copy of the latest Japan PEARK save."""
from __future__ import annotations
import copy, hashlib, json, re, shutil, subprocess
from datetime import datetime
from pathlib import Path

from build import HERE, TARGET, parse, get, getall, serialise
from repair_completion_save import block_end

SOURCE_NAME = 'pearkEmpire of Japan_1942_January_19.eug'
OUTPUT_NAME = 'JAPAN_PEARK_1942_MARCH_8_REPAIRED.eug'
STAGE = HERE / 'staged_peark_march'
AVOID_SEAS = {2489, 2492}
REROUTES = {
    13: [1544,2491,2420,2415,2414,2424,1675],
    16: [1544,2491,2420,2415,2416,2472,2474,2482,2479,2475,1685],
    17: [1544,2491,2420,2415,2416,2472,2474,2482,2479,2475,1686],
    286541: [1544,2491,2420,2415,2416,1672],
    286828: [1544,2491,2420,2415,2416,2472,2473,1667],
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def value(node, key, default=None):
    return get(node, key, default)


def set_value(node, key, new_value):
    for i, (k, _) in enumerate(node):
        if k == key:
            node[i] = (key, new_value)
            return
    node.append((key, new_value))


def country_map(root):
    return {get(c, 'tag'): c for c in getall(root, 'country')}


def route_id(convoy):
    return int(get(get(convoy, 'id'), 'id'))


def is_garrison(formation):
    divisions = getall(formation, 'division')
    return len(divisions) == 1 and get(get(divisions[0], 'id'), 'type') == '28632'


def edit_country(jap):
    garrisons = [f for f in getall(jap, 'landunit') if is_garrison(f)]
    assert len(garrisons) == 31, f'Expected 31 one-division static garrisons, found {len(garrisons)}'
    names = []
    for formation in garrisons:
        div = getall(formation, 'division')[0]
        division_name = get(div, 'name')
        assert division_name and 'Defence Detachment' in division_name, division_name
        set_value(formation, 'name', division_name)
        formation[:] = [(k, v) for k, v in formation if k != 'leader']
        names.append(division_name)

    convoys = {route_id(c): c for c in getall(jap, 'convoy')}
    assert len(convoys) == len(getall(jap, 'convoy'))
    supply_routes = [c for c in convoys.values() if get(c, 'supplies') == 'yes']
    assert len(supply_routes) == 28, len(supply_routes)
    for convoy in supply_routes:
        set_value(convoy, 'oil', 'yes')

    for rid, path in REROUTES.items():
        convoy = convoys[rid]
        assert not AVOID_SEAS.intersection(path), rid
        set_value(convoy, 'path', [(None, str(p)) for p in path])

    # Put 18 transports on each of the two idle Pacific garrison routes.
    # Preserve the existing pool balance: 57 -> 21 transports and 194 -> 186 escorts.
    for rid in (9, 13):
        convoy = convoys[rid]
        assert int(get(convoy, 'transports', '0')) == 0, rid
        set_value(convoy, 'transports', '18')
    set_value(convoys[9], 'escorts', '8')
    assert int(get(jap, 'transports')) >= 36
    assert int(get(jap, 'escorts')) >= 8
    set_value(jap, 'transports', str(int(get(jap, 'transports')) - 36))
    set_value(jap, 'escorts', str(int(get(jap, 'escorts')) - 8))
    return {'garrisons': names, 'supply_routes': len(supply_routes), 'rerouted_ids': sorted(REROUTES)}


def stage():
    source = TARGET / 'scenarios/save games' / SOURCE_NAME
    raw = source.read_bytes()
    text = raw.decode('latin1')
    root = parse(text)
    before = copy.deepcopy(root)
    countries = country_map(root)
    assert 'JAP' in countries
    edited = edit_country(countries['JAP'])

    # Change only the save label, option filename, and Japan country block.
    save_label = 'Japan - 8 March 1942 - garrisons and convoy repair'
    set_value(root, 'name', save_label)
    optionfile = get(root, 'optionfile')
    if optionfile:
        set_value(root, 'optionfile', optionfile.replace(SOURCE_NAME + '.cfg', OUTPUT_NAME + '.cfg'))
    # Root serialization is intentionally avoided; preserve all original bytes outside JAP block.
    start = next(m for m in re.finditer(r'(?m)^country\s*=\s*\{', text)
                 if re.search(r'(?m)^\s*tag\s*=\s*JAP\s*$', text[m.start():m.start()+500]))
    end = block_end(text, start.start())
    replacement = 'country = {\n' + serialise(countries['JAP'], 1) + '\n}'
    text = text[:start.start()] + replacement + text[end:]
    text = re.sub(r'(?m)^name\s*=\s*"[^"]*"', 'name = "' + save_label + '"', text, count=1)
    text = text.replace(SOURCE_NAME + '.cfg', OUTPUT_NAME + '.cfg', 1)

    warnings = []
    check = parse(text, warnings)
    assert not warnings, warnings[:5]
    after = country_map(check)
    original = country_map(before)
    for tag in original:
        if tag != 'JAP':
            assert original[tag] == after[tag], f'Non-Japan country changed: {tag}'
    assert getall(before, 'province') == getall(check, 'province'), 'Province stocks/control changed'
    assert get(before, 'globaldata') == get(check, 'globaldata'), 'Global flags/timers changed'
    final_jap = after['JAP']
    final_garrisons = [f for f in getall(final_jap, 'landunit') if is_garrison(f)]
    assert len(final_garrisons) == 31
    assert all(get(f, 'name') == get(getall(f, 'division')[0], 'name') for f in final_garrisons)
    assert all(not getall(f, 'leader') for f in final_garrisons)
    final_routes = {route_id(c): c for c in getall(final_jap, 'convoy')}
    assert all(get(c, 'oil') == 'yes' for c in final_routes.values() if get(c, 'supplies') == 'yes')
    assert all(not AVOID_SEAS.intersection(int(v) for _, v in get(final_routes[rid], 'path', [])) for rid in REROUTES)
    assert int(get(final_jap, 'transports')) == int(get(original['JAP'], 'transports')) - 36
    assert int(get(final_jap, 'escorts')) == int(get(original['JAP'], 'escorts')) - 8

    STAGE.mkdir(exist_ok=True)
    output = STAGE / OUTPUT_NAME
    output.write_bytes(text.encode('latin1'))
    shutil.copy2(source.with_suffix('.eug.cfg'), STAGE / (OUTPUT_NAME + '.cfg'))
    report = {
        'state': 'staged', 'source': str(source), 'source_sha256': digest(raw),
        'output': OUTPUT_NAME, 'output_sha256': digest(output.read_bytes()),
        'game_date': '1942-03-08 14:00', 'garrisons_renamed': 31,
        'garrison_leaders_cleared': 31, 'supply_routes_with_oil': 28,
        'rerouted_away_from_inland_sea_and_tokyo_bay': sorted(REROUTES),
        'route_ship_assignments': {'convoy_9_transports': 18, 'convoy_9_escorts': 8,
                                   'convoy_13_transports': 18},
        'transport_pool_after': int(get(final_jap, 'transports')),
        'escort_pool_after': int(get(final_jap, 'escorts')),
        'non_japan_countries_provinces_and_globaldata_preserved': True,
        'game_executed': False,
    }
    (STAGE / 'REPAIR.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def install():
    proc = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq Darkest Hour.exe', '/FO', 'CSV', '/NH'],
                          capture_output=True, text=True)
    assert proc.returncode == 0 and not any(l.lower().startswith('"darkest hour.exe"') for l in proc.stdout.splitlines())
    report_path = STAGE / 'REPAIR.json'
    report = json.loads(report_path.read_text())
    source = Path(report['source'])
    assert digest(source.read_bytes()) == report['source_sha256'], 'Source changed since repair was staged'
    staged = STAGE / OUTPUT_NAME
    assert digest(staged.read_bytes()) == report['output_sha256']
    destination = TARGET / 'scenarios/save games' / OUTPUT_NAME
    assert not destination.exists(), f'Refusing to overwrite {destination}'
    event_source = STAGE / 'campaign_balance.txt'
    event_target = TARGET / 'db/events/japan_rising/campaign_balance.txt'
    expected_event_hash = '25c86e320c20378b00938876afc485328cb17cffc193b18bdbbab550dbc5572d'
    assert digest(event_target.read_bytes()) == expected_event_hash, 'Installed event file changed; re-audit before replacing'
    assert event_source.exists(), 'Generate and review the staged campaign_balance.txt first'
    event_text = event_source.read_text(encoding='latin1')
    new_corps = re.findall(r'type = add_corps which = "[^"]+" value = land where = \d+ when = 0 }', event_text)
    assert len(new_corps) == 31, f'Expected 31 named, leaderless call-up commands, found {len(new_corps)}'
    backup = HERE / 'backups' / ('before-peark-march-repair-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(source, backup / SOURCE_NAME)
    shutil.copy2(source.with_suffix('.eug.cfg'), backup / (SOURCE_NAME + '.cfg'))
    shutil.copy2(event_target, backup / 'campaign_balance.txt')
    shutil.copy2(HERE / 'INSTALLED_FILE_HASHES.json', backup / 'INSTALLED_FILE_HASHES.json')
    shutil.copy2(staged, destination)
    shutil.copy2(STAGE / (OUTPUT_NAME + '.cfg'), destination.with_suffix('.eug.cfg'))
    shutil.copy2(event_source, event_target)
    hashes_path = HERE / 'INSTALLED_FILE_HASHES.json'
    hashes = json.loads(hashes_path.read_text())
    hashes['db\\events\\japan_rising\\campaign_balance.txt'] = digest(event_target.read_bytes())
    hashes_path.write_text(json.dumps(dict(sorted(hashes.items())), indent=2))
    report.update(state='installed', installed_save=str(destination), backup=str(backup))
    report['campaign_balance_sha256'] = digest(event_target.read_bytes())
    report['source_event_change'] = 'Adds a named add_corps command before each island garrison activation; uses leader ID 0 as intended no-commander value.'
    report_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'install'))
    args = parser.parse_args()
    (stage if args.mode == 'stage' else install)()
