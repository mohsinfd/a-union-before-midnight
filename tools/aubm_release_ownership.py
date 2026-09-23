"""Preserve foreign occupation while assigning release territory to its new state.

One queued, effect-free-unless-needed callback per released tag. No polling,
new decisions, peace, alliance, military access, or forced control commands.
Territory catalogue is the installed DH map's revolt minimum+extra lists.
"""
import json
from pathlib import Path
from dh_save_spans import Node, parse, replace

ROOT = Path(__file__).resolve().parents[1]
TERRITORIES = json.loads((ROOT/'tools/data/release_territories.json').read_text())
CALLBACKS = {tag: 9297400+i for i, tag in enumerate(sorted(TERRITORIES))}
NEW_EVENT_IDS = set(CALLBACKS.values())
MODULE = 'db/events/aubm_v4/43_wartime_settlements.txt'
MARKER = '# SETTLEMENT1_RELEASE_OWNERSHIP'
UNRELEASABLE = {'U03', 'U04'}  # No revolt definition in the installed map.


def common(tag):
    return (f'exists = IND exists = {tag} NOT = {{ ispuppet = IND }} '
            f'NOT = {{ war = {{ country = IND country = {tag} }} }} '
            f'OR = {{ NOT = {{ ispuppet = {tag} }} '
            f'puppet = {{ country = {tag} country = IND }} }}')


def province_guard(tag, province):
    return (f'owned = {{ province = {province} data = IND }} '
            f'core = {{ province = {province} data = {tag} }} '
            f'NOT = {{ core = {{ province = {province} data = IND }} }} '
            f'NOT = {{ control = {{ province = {province} data = IND }} }} '
            f'NOT = {{ control = {{ province = {province} data = REB }} }}')


def callback(tag):
    rule = common(tag)
    commands = '\n'.join(
        'command = { trigger = { '+province_guard(tag, p)+' } '
        f'type = secedeprovince which = {tag} value = {p} when = 1 }}'
        for p in TERRITORIES[tag])
    return (f'\n# Release title reconciliation: {tag}\nevent = {{\n'
            f'id = {CALLBACKS[tag]}\nrandom = no\npersistent = yes\none_action = yes\n'
            'country = IND\nname = "AI_EVENT"\n'
            'desc = "Assign remaining claims to the released country. Foreign occupation remains unchanged."\n'
            'style = 2\npicture = "aubm_v4_indian_ocean_war"\n'
            f'action_a = {{ trigger = {{ {rule} }} name = "OK"\n{commands}\n}}\n'
            f'action_b = {{ trigger = {{ NOT = {{ AND = {{ {rule} }} }} }} name = "OK" }}\n}}\n')


def actions(e):
    return [f.value for f in e.fields if (f.key or '').startswith('action')]


def transform(files):
    result, records, existing = dict(files), {}, set()
    for path, text in files.items():
        edits = []
        for e in parse(text).all('event'):
            eid = int(e.get('id')); existing.add(eid)
            if eid in NEW_EVENT_IDS or e.get('country') != 'IND':
                continue
            releases = [(a, f) for a in actions(e) for f in a.fields
                        if f.key == 'command' and f.value.get('type') == 'independence']
            if not releases:
                continue
            records[eid] = [dict(dimension='release_ownership', status='CORRECTED_SCRIPT',
                                 engine_tested=False, releases=len(releases))]
            if MARKER in text[e.start:e.end]:
                continue
            edits.append((e.start+1, e.start+1, '\n'+MARKER+'\n'))
            for a, f in releases:
                cmd = f.value; tag = cmd.get('which')
                if tag in UNRELEASABLE:
                    continue
                if tag not in CALLBACKS:
                    raise ValueError('Missing release catalogue: '+tag)
                gate = cmd.get('trigger')
                gate_text = text[gate.start+1:gate.end-1] if isinstance(gate, Node) else ''
                # Queue BEFORE release so NOT exists conditions are evaluated
                # while still valid. It runs tomorrow, after government creation.
                gate_text += f' NOT = {{ exists = {tag} }}'
                queue = ('command = { trigger = { '+gate_text+' } '
                         f'type = event which = {CALLBACKS[tag]} where = IND when = 1 }}\n')
                edits.append((f.start, f.start, queue))
            desc = e.get('desc')
            note = ' Foreign-held land stays occupied; independence does not force foreign armies out.'
            if isinstance(desc, str) and len(desc+note) <= 500:
                f = e.field('desc'); edits.append((f.value_start, f.end, '"'+desc+note+'"'))
        result[path] = replace(text, edits)
    if MODULE not in result:
        raise ValueError('Missing loaded settlement module')
    result[MODULE] += ''.join(callback(tag) for tag in sorted(CALLBACKS)
                             if CALLBACKS[tag] not in existing)
    for tag, eid in CALLBACKS.items():
        records[eid] = [dict(dimension='release_ownership', status='CORRECTED_SCRIPT',
                            target=tag, engine_tested=False)]
    return result, records


def clarify(files):
    """Keep outcomes/costs unchanged; make common constitutional buttons explicit."""
    result, records = dict(files), {}
    for path, text in files.items():
        edits = []
        for e in parse(text).all('event'):
            eid = int(e.get('id'))
            if e.get('country') != 'IND' or eid in NEW_EVENT_IDS:
                continue
            for a in actions(e):
                flags = [c.get('which', '') for c in a.all('command') if c.get('type') == 'setflag']
                kind = None
                if any(x.startswith(('ind_aubm_global_sovereign_', 'ind_aubm_regional_sovereign_')) for x in flags):
                    kind = 'Independent country (not an Indian puppet)'
                elif any(x.startswith(('ind_aubm_global_protected_', 'ind_aubm_regional_protected_')) for x in flags):
                    kind = 'Indian puppet government'
                elif eid == 9287601:
                    if 'ind_aubm_local_dei_sovereign' in flags: kind = 'Independent Indonesia (not an Indian puppet)'
                    if 'ind_aubm_local_dei_protected' in flags: kind = 'Indian puppet | -500 supplies | +4 dissent'
                    if 'ind_aubm_local_dei_direct' in flags: kind = 'Direct Indian rule | +8 dissent'
                if kind:
                    f = a.field('name')
                    if f.value != kind: edits.append((f.value_start, f.end, '"'+kind+'"'))
                    records[eid] = [dict(dimension='settlement_wording',status='CORRECTED_SCRIPT',engine_tested=False)]
            if eid == 9287601:
                description = ("Batavia has fallen. Choose an independent Indonesia, an Indian puppet, or direct Indian rule. "
                    "Independence gives India's guarantee, not obedience or automatic alliance membership. "
                    "A puppet costs 500 supplies and 4 dissent. Direct rule needs a second centre and adds 8 dissent and 8 belligerence. "
                    "The Dutch government must still accept. Foreign-held islands remain occupied; this agreement cannot order Japan out.")
                f=e.field('desc');edits.append((f.value_start,f.end,'"'+description+'"'))
            if eid == 9281316:
                description = ("Ask the government holding Kashgar and Urumqi for passage. It must be independent, outside the Soviet alliance, "
                    "and at peace with India. A Soviet puppet or enemy is a fighting front, not a transit partner. "
                    "If this road is closed, review the Afghan-Central Asian corridor. An access treaty itself grants no territory.")
                f=e.field('desc');edits.append((f.value_start,f.end,'"'+description+'"'))
                records[eid]=[dict(dimension='corridor_wording',status='CORRECTED_SCRIPT',engine_tested=False)]
        result[path]=replace(text,edits)
    return result,records


def transform_all(files):
    output,records=transform(files)
    output,words=clarify(output)
    for eid,entries in words.items():records.setdefault(eid,[]).extend(entries)
    return output,records
