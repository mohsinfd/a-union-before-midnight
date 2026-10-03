"""Staged port of the shared B1 minor-withdrawal safety unit.

Run after campaign access. Only the supplied loaded settlement module changes;
there is no install/save I/O. The existing installed-only 9297200-02 registry is
reused explicitly, not allocated as a new arbitrary range. See DH's local event
commands.txt: leave_alliance when=1 leaves THIS country's old alliance wars.
No Indian peace command or compensating declaration of war is introduced.

The explicit bounded contract requires the current Japan war and preserves
snapshotted Indian wars with SOV, ENG, GER and USA. OTHER WARS ARE NOT VERIFIED.
The prior340-country audit was removed to avoid enormous effect tooltips; no
documented all-war-set comparison was found in the local command reference.
Ordinary action predicates now check those four snapshots directly: there is
no same-click audit-token computation. Government, territory and queued-reply
provenance checks remain. Native war-list mutation, puppet creation, queue
persistence and UI rendering still require engine tests.
"""
import re
from dh_save_spans import Node, parse, replace
from build_aubm_cleanup import peace_gate
from aubm_shared_withdrawal import (
    EXITS, BASE, TAGS, aa, body, prefix, detached, protected,
    gate_edit, transform as shared_transform,
)

MARKER = '# AUBM_STAGED_WITHDRAWAL_V2'
SNAPSHOT_TAGS = ('SOV', 'ENG', 'GER', 'USA')
SOURCE_MODULE = '43_wartime_settlements.txt'
NEW_EVENT_IDS = frozenset(range(BASE, BASE + 3))
WITHDRAWALS = {eid: p for p in EXITS for eid in p.withdrawals}
OUTCOMES = {eid: p for p in EXITS for eid in p.outcomes}
CALLBACKS = {BASE + i: p for i, p in enumerate(EXITS)}
SIDE_EFFECTS = {9297006: EXITS[2], 9297007: EXITS[2]}
EDITED_IDS = frozenset(WITHDRAWALS) | frozenset(OUTCOMES) | frozenset(SIDE_EFFECTS)
SITES = {'U87': (1337, 1317), 'U03': (1395, 1396, 1397, 1399, 1403), 'SIA': (1423, 1425)}
DONE = {'U87': 'ind_lib1_china_protectorate', 'U03': 'ind_lib1_indo_settled', 'SIA': 'ind_lib1_siam_protected'}
GENERIC_MARKER = '# AUBM_STAGED_MINOR_PEACE_V1'
GENERIC_IDS = frozenset((9282212, 9282260, 9282943, 9282958, 9286443, 9286743, 9286458, 9286758))
TARGET_FLAG = re.compile(r'ind_aubm_(?:regional_armistice|armistice|bespoke_armistice)_target_(sia|u87|u03)')
TREATY_DOWNGRADES = frozenset(('ind_v4a_treaty_cobelligerent', 'ind_v4a_treaty_formal_alliance',
    'ind_gc_cobelligerent', 'ind_gc_formal_axis', 'ind_v4_sov_equal_compact',
    'ind_v4_sov_supervised_compact', 'ind_aubm_jp_partnership',
    'ind_aubm_jp_independent_cobelligerent', 'ind_aubm_jp_formal_alliance',
    'ind_v3_joined_allies', 'ind_v3_joined_axis', 'ind_v3_joined_comintern', 'ind_v3_joined_japan'))


def generic_peace(files):
    """Close only the registered three-minor alternate offers and executions.

    Import the documented scope predicate, NOT the old compiler's broad pass.
    No prose truncation, flag harvesting, treaty rewrites or synthetic cleanup.
    """
    output, records = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event' or ef.value.get('country') != 'IND':
                continue
            ev, changed_actions = ef.value, []
            eid, changes = int(ev.get('id')), []
            marked = GENERIC_MARKER in text[ef.start:ef.end]
            for a in aa(ev):
                tags, rules = set(), []
                for c in a.all('command'):
                    if c.get('type') == 'peace' and (c.get('which') in DONE or eid == 9282260):
                        tag = c.get('which')
                        tags.add(tag)
                        rule = f'exists = IND exists = {tag} ' + peace_gate(tag) + f' NOT = {{ flag = ind_exit_{tag.lower()}_verifying }}'
                        original = body(text, c.get('trigger'))
                        # Shared regional ratification also handles unrelated
                        # countries. Restrict its WHOLE action only when this
                        # minor's conditional peace command would execute.
                        if eid == 9282260:
                            selector = f'ind_aubm_regional_armistice_target_{tag.lower()}'
                            if not isinstance(c.get('trigger'), Node) or selector not in c.get('trigger').all('flag'):
                                raise ValueError('Regional peace selector changed: ' + tag)
                            # Bookkeeping is keyed to this selector even after
                            # war ends. Do not let a stale reply bypass safety.
                            rules.append(f'OR = {{ NOT = {{ flag = {selector} }} AND = {{ {rule} }} }}')
                        else:
                            rules.append(rule)
                        if not marked:
                            f = next((f for f in c.fields if f.key == 'value'), None)
                            changes.append((f.value_start, f.end, '0') if f else (c.end-1, c.end-1, ' value = 0 '))
                    if c.get('type') == 'setflag':
                        match = TARGET_FLAG.fullmatch(c.get('which', ''))
                        if match:
                            tag = match[1].upper()
                            tags.add(tag)
                            rules.append(f'exists = IND exists = {tag} ' + peace_gate(tag) + f' NOT = {{ flag = ind_exit_{tag.lower()}_verifying }}')
                if not tags:
                    continue
                if eid not in GENERIC_IDS:
                    raise ValueError(f'Unregistered alternate minor peace action {eid}')
                changed_actions.append(a.get('name'))
                if not marked:
                    changes.append(gate_edit(text, a, ' '.join(dict.fromkeys(rules))))
                    if any(c.get('type') == 'peace' for c in a.all('command')):
                        # value=0 retains India's actual alliance. These exact
                        # source writes only represented the old value=1 exit;
                        # retain the existing treaty records instead.
                        for f in a.fields:
                            if f.key == 'command' and f.value.get('type') in ('setflag','clrflag') and f.value.get('which') in TREATY_DOWNGRADES:
                                changes.append((f.start,f.end,''))
            if not changed_actions:
                continue
            if not marked:
                if eid == 9282260:
                    changes.append(scalar_edit(ev, 'desc', '"Delhi signs for its side. India must be sovereign and either unallied or alliance leader; the selected respondent must be independent and unallied. Full peace preserves India\'s alliance and treaty records. A Japanese-backed minor must use its withdrawal settlement instead. Closing spends nothing."'))
                if not any(not a.all('command') for a in aa(ev)):
                    changes.append((ev.end-1, ev.end-1,
                        '\n action = { trigger = { ai = no } name = "Close - make no new commitment" }\n'))
                changes.append((ev.end-1, ev.end-1, '\n' + GENERIC_MARKER + '\n'))
                edits.extend(changes)
            records[eid] = [dict(dimension='shared_withdrawal', status='CORRECTED_SCRIPT', path=path,
                actions=changed_actions, engine_tested=False,
                detail='Whole generic peace/offer action requires sovereign Indian unallied-or-leader authority and an independent unallied minor. Full peace value=0 preserves Indian alliance and its treaty records. Shared regional ratifier9282260 covers all ten conditional minors consistently; no arbitrary flags cleared.',
                remaining=['Native coalition-war mutation still needs testing; this is not a separate-peace guarantee.'])]
        if edits:
            output[path] = replace(text, edits)
    return output, records


def snapshot(p):
    return prefix(p) + 'snapshot'


def current(p):
    positions = ' '.join(
        f'owned = {{ province = {site} data = {p.tag} }} ' +
        (f'OR = {{ control = {{ province = {site} data = IND }} control = {{ province = {site} data = {p.tag} }} }}'
         if p.tag == 'SIA' else f'control = {{ province = {site} data = {p.tag} }}')
        for site in SITES[p.tag])
    return (f'flag = {snapshot(p)} exists = IND NOT = {{ ispuppet = IND }} '
            'NOT = { alliance = { country = IND country = JAP } } ' + positions)


def scalar_edit(node, key, value):
    f = node.field(key)
    return f.value_start, f.end, value


def success_actions(ev):
    return [a for a in aa(ev) if any(c.get('type') != 'clrflag' for c in a.all('command'))]


def guard_failures(text, eid):
    """A close/cleanup remains available whenever every actual success is barred."""
    event = parse(text).get('event')
    guards = ['AND = { ' + body(text, a.get('trigger')) + ' }' for a in success_actions(event)]
    if not guards:
        raise ValueError(f'Withdrawal outcome has no guarded success: {eid}')
    failure = '{ NOT = { OR = { ' + ' '.join(guards) + ' } } }'
    edits = []
    for a in aa(event):
        if any(c.get('type') != 'clrflag' for c in a.all('command')):
            continue
        old = a.get('trigger')
        if isinstance(old, Node):
            edits.append((old.start, old.end, failure))
    return replace(text, edits)


def compact_war_guards(text):
    # Reuse only the approved, named major-war part of the shared generator.
    # Explicitly discard every other war predicate AND its snapshot writes.
    for p in EXITS:
        for tag in TAGS:
            if tag in ('IND', p.tag) or tag in SNAPSHOT_TAGS:
                continue
            text = text.replace(f'OR = {{ NOT = {{ flag = {prefix(p)}war_{tag.lower()} }} war = {{ country = IND country = {tag} }} }}', '')
    edits = []
    for ef in parse(text).fields:
        if ef.key != 'event' or int(ef.value.get('id')) not in WITHDRAWALS:continue
        p = WITHDRAWALS[int(ef.value.get('id'))]
        for a in aa(ef.value):
            for f in a.fields:
                if f.key != 'command':continue
                c = f.value
                which = c.get('which','')
                if c.get('type') in ('setflag','clrflag') and which.startswith(prefix(p)+'war_'):
                    tag = which[len(prefix(p)+'war_'):].upper()
                    if tag not in SNAPSHOT_TAGS:edits.append((f.start,f.end,''))
    # Siam's original UNATTACHED expands every possible alliance pair. The
    # documented participant value4 checks any alliance without that expansion.
    def visit(n):
        negatives = []
        for f in n.fields:
            if isinstance(f.value, Node):
                child = f.value
                alliance = child.get('alliance') if f.key == 'NOT' and len(child.fields) == 1 else None
                if isinstance(alliance, Node) and alliance.all('country')[:1] == ['SIA']:
                    negatives.append(f)
        partners = {f.value.get('alliance').all('country')[1] for f in negatives}
        if partners == set(TAGS)-{'SIA'}:
            for i, f in enumerate(negatives):
                edits.append((f.start, f.end, 'NOT = { participant = { country = SIA value = 4 } }' if i == 0 else ''))
        for f in n.fields:
            if isinstance(f.value, Node): visit(f.value)
    visit(parse(text))
    return replace(text, edits)


def harden(text):
    edits = []
    for ef in parse(text).fields:
        if ef.key != 'event':
            continue
        eid, ev = int(ef.value.get('id')), ef.value
        if eid not in EDITED_IDS | NEW_EVENT_IDS:
            continue
        changes = []
        if eid in WITHDRAWALS:
            p = WITHDRAWALS[eid]
            for a in aa(ev):
                if not any(c.get('type') == 'end_puppet' for c in a.all('command')):
                    continue
                first = next(f for f in a.fields if f.key == 'command')
                changes.append((first.start, first.start,
                    f'\ncommand = {{ type = setflag which = {snapshot(p)} }}\n'))
                # Existing foreign access/relation concessions are not paid on
                # an unverified engine exit. They remain in the minor's context.
                for c in a.all('command'):
                    if c.get('type') in ('access', 'relation'):
                        changes.append(gate_edit(text, c, detached(p) + ' ' + current(p)))
        elif eid in OUTCOMES:
            p = OUTCOMES[eid]
            for a in success_actions(ev):
                changes.append(gate_edit(text, a, current(p)))
            for key in ('decision', 'trigger'):
                n = ev.get(key)
                if isinstance(n, Node):
                    changes.append((n.start+1, n.start+1, '\n' + current(p) + f' NOT = {{ flag = {prefix(p)}verifying }}\n'))
            if eid == 9297005:
                # This is a queued target, not a calendar watcher. Its action
                # guards provide both safe success and a usable failure exit.
                for f in ev.fields:
                    if f.key in ('trigger', 'date', 'offset', 'deathdate'):
                        # Remove the insertion above that falls within this span.
                        changes = [x for x in changes if not f.start <= x[0] <= f.end]
                        changes.append((f.start, f.end, ''))
        elif eid in CALLBACKS:
            p = CALLBACKS[eid]
            for a in success_actions(ev):
                changes.append(gate_edit(text, a, current(p) + f' NOT = {{ flag = {DONE[p.tag]} }}'))
            changes.append(scalar_edit(ev, 'name', '"' + {'U87': 'Nanjing', 'U03': 'Indochina', 'SIA': 'Siam'}[p.tag] + ': Verify the New Government"'))
            changes.append(scalar_edit(ev, 'desc', '"The government and agreed territory must be secure. India must still fight Japan. Any Indian war with Britain, Germany, the Soviet Union or the USA recorded at withdrawal must remain active before settlement effects are released. Other wars are not checked. Failed checks pay nothing."'))
        else:
            p = SIDE_EFFECTS[eid]
            for a in success_actions(ev):
                changes.append(gate_edit(text, a, current(p) + ' ' + protected(p)))
        if eid == 9289905:
            f = ev.field('desc')
            updated = f.value.replace('India remains in its current wars.',
                'No Indian peace order is issued; the named major wars are checked, not every war.')
            changes.append((f.value_start,f.end,'"'+updated+'"'))
        changes.append((ev.end-1, ev.end-1, '\n' + MARKER + '\n'))
        raw = replace(text[ef.start:ef.end], [(a-ef.start, b-ef.start, s) for a, b, s in changes])
        if eid in OUTCOMES or eid in CALLBACKS or eid in SIDE_EFFECTS:
            raw = guard_failures(raw, eid)
        edits.append((ef.start, ef.end, raw))
    return compact_war_guards(replace(text, edits))


def validate(text):
    events = {int(e.get('id')): e for e in parse(text).all('event')}
    required = EDITED_IDS | NEW_EVENT_IDS
    if not required <= events.keys():
        raise ValueError('Incomplete shared withdrawal unit')
    for eid in required:
        ev = events[eid]
        for a in aa(ev):
            if a.all('command') and not isinstance(a.get('trigger'), Node):
                raise ValueError(f'Unguarded withdrawal action {eid}')
            for c in a.all('command'):
                if c.get('type') in ('peace', 'war'):
                    raise ValueError(f'Unexpected peace/war command in withdrawal unit {eid}')
                if c.get('type') in ('end_puppet', 'leave_alliance'):
                    if eid not in WITHDRAWALS or ev.get('country') != WITHDRAWALS[eid].tag:
                        raise ValueError('Withdrawal executed outside minor country')
                    if c.get('type') == 'leave_alliance' and c.get('when') != '1':
                        raise ValueError('Withdrawal must leave inherited alliance wars')
        if eid in NEW_EVENT_IDS or eid == 9297005:
            if any(ev.get(k) is not None for k in ('trigger', 'date', 'offset', 'deathdate')):
                raise ValueError('Queued withdrawal verification has a calendar gate')
        if eid in NEW_EVENT_IDS:
            if ev.get('country') != 'IND':
                raise ValueError('Reward verification is not Indian')
            a = aa(ev)[0]
            guard = body(text, a.get('trigger'))
            p = CALLBACKS[eid]
            if f'flag = {snapshot(p)}' not in guard or f'flag = {prefix(p)}verifying' not in guard:
                raise ValueError('Reward verification provenance missing')


def transform(files):
    output, target, seen = dict(files), None, {}
    for path, text in files.items():
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            if eid not in EDITED_IDS | NEW_EVENT_IDS:
                continue
            if eid in seen:
                raise ValueError(f'Duplicate withdrawal ID {eid}')
            seen[eid] = path
            if eid == 9297005:
                target = path
            if eid in NEW_EVENT_IDS and MARKER not in text[ef.start:ef.end]:
                raise ValueError(f'Withdrawal callback registry collision {eid}')
    if target is None or any(seen.get(eid) != target for eid in EDITED_IDS):
        raise ValueError('The complete three-family withdrawal unit must share its loaded module')
    text = files[target]
    existing = NEW_EVENT_IDS & seen.keys()
    if existing:
        if existing != NEW_EVENT_IDS:
            raise ValueError('Partial withdrawal verification registry')
        validate(text)
    else:
        text = harden(shared_transform(text))
        validate(text)
        output[target] = text
    records = {}
    for eid in EDITED_IDS | NEW_EVENT_IDS:
        records[eid] = [dict(dimension='shared_withdrawal', status='CORRECTED_SCRIPT', path=target,
            detail='Minor-side withdrawal, current Japan war plus snapshotted SOV/ENG/GER/USA wars checked, verified government/territory before rewards; queued callbacks stay trigger-less.',
            engine_tested=False, registry_reused=(eid in NEW_EVENT_IDS),
            remaining=['Native separate-peace war-list mutation and make_puppet success require engine testing.',
                       'Other simultaneous wars are not verified; this is explicitly not an all-war preservation guarantee.',
                       'No rollback or compensating war is attempted if engine outcomes differ.',
                       'Fresh-game primary; old saves without snapshot provenance are not migrated.'])]
    output, alternate_records = generic_peace(output)
    records.update(alternate_records)
    return output, records
