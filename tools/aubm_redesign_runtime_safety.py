"""Pure, bounded authored-source dockyard/debt safety port, not B1 compilation.

Only registered installed IDs 9297180-82 are appended to the loaded navy source
module. No file/install/save I/O. Fresh games are primary. Old-standard 9271112
assumes its documented earned -10/-15/-20 hull modifiers; legacy mature state
assumes -50. No generic save migration or inference from arbitrary flag damage.
DH documentation: relative build_time uses model-zero base for EVERY model;
on_upgrade avoids applying modifiers to deployed units. Existing production
orders and engine rounding/limits require native tests, not these script tests.
"""
import json
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate

MARKER = '# AUBM_STAGED_RUNTIME_SAFETY_V1'
NEW_EVENT_IDS = frozenset((9297180, 9297181, 9297182))
EDITED_IDS = frozenset((9271111, 9271112, 9282080, 9282081))
HULLS = tuple('carrier light_carrier escort_carrier battleship battlecruiser heavy_cruiser light_cruiser destroyer submarine transport'.split())
STANDARD = 'ind_aubm_dockyard_efficiency_standard'
MATURE = 'ind_aubm_dockyard_efficiency_50'
READY = 'ind_cleanup1_naval_ready'
PEACE = 'ind_cleanup1_naval_peace'
DEBT_CAP = 'NOT = { flag = ind_aubm_debt_tier_4 flag = ind_aubm_debt_overhang }'
LEGACY = {h: (-10 if i < 5 else -15 if i < 7 else -20) for i, h in enumerate(HULLS)}


def command(kind, which, trigger=''):
    return 'command = { ' + ('trigger = { ' + trigger + ' } ' if trigger else '') + 'type = ' + kind + ' which = ' + which + ' }'


def delta(value, trigger=''):
    return '\n'.join(command('build_time', h + ' when = on_upgrade where = relative value = ' + str(value), trigger) for h in HULLS)


def naval_event(eid, name, desc, valid, commands):
    return ('event = {\n' + MARKER + '\n id = ' + str(eid) + '\n random = no persistent = yes country = IND one_action = yes\n'
        ' trigger = { ' + valid + ' }\n name = ' + json.dumps(name) + '\n desc = ' + json.dumps(desc) + '\n'
        ' style = 2 picture = "india_v3_armed_forces"\n'
        ' date = { day = 0 month = january year = 1933 } offset = 1 deathdate = { day = 29 month = december year = 1964 }\n'
        ' action_a = { trigger = { ' + valid + ' } name = "' + name + '"\n' + commands + '\n }\n'
        ' action = { trigger = { NOT = { AND = { ' + valid + ' } } } name = "The yard schedule has already changed" }\n}\n')


def controllers():
    mature = 'flag = ' + MATURE
    ready = 'flag = ' + READY
    return '\n'.join((
        naval_event(9297180, 'National Dockyard Schedules',
            "The mature yards retain their earned wartime standard. In peace, normal shifts leave a permanent 25% reduction from each hull class's model-zero schedule. Daily IC cost stays unchanged.",
            mature + ' NOT = { flag = ' + READY + ' }',
            delta(25, 'atwar = no') + '\n' + command('setflag', PEACE, 'atwar = no') + '\n' + command('clrflag', PEACE, 'atwar = yes') + '\n' + command('setflag', READY)),
        naval_event(9297181, 'The Yards Return to Normal Shifts',
            'Peace ends emergency shifts. The permanent 25% model-zero construction-time reduction remains. Existing orders may retain their completion dates.',
            mature + ' ' + ready + ' atwar = no NOT = { flag = ' + PEACE + ' }',
            delta(25) + '\n' + command('setflag', PEACE)),
        naval_event(9297182, 'Emergency Dockyard Shifts',
            'War brings priority steel, machinery and extra shifts. The total reduction returns to 50% of the model-zero hull schedule, without changing daily IC cost. Existing orders may retain their dates.',
            mature + ' ' + ready + ' flag = ' + PEACE + ' atwar = yes',
            delta(-25) + '\n' + command('clrflag', PEACE)),
    ))


def transform(files: dict[str, str]):
    output, records, seen = dict(files), {}, {}
    for path, text in files.items():
        for ef in parse(text).fields:
            if ef.key == 'event' and int(ef.value.get('id')) in EDITED_IDS | NEW_EVENT_IDS:
                eid = int(ef.value.get('id'))
                if eid in seen: raise ValueError('Duplicate runtime safety ID ' + str(eid))
                seen[eid] = (path, text[ef.start:ef.end])
    existing = NEW_EVENT_IDS & seen.keys()
    if existing and (existing != NEW_EVENT_IDS or any(MARKER not in seen[eid][1] for eid in existing)):
        raise ValueError('Runtime safety registered ID collision or partial port')
    if not {9271111, 9271112} <= seen.keys() or seen[9271111][0] != seen[9271112][0]:
        raise ValueError('Both dockyard standards must share the loaded navy module')
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event': continue
            eid = int(ef.value.get('id'))
            if eid not in EDITED_IDS: continue
            raw = text[ef.start:ef.end]
            if MARKER in raw:
                records[eid] = [dict(dimension='runtime_safety', status='ALREADY_APPLIED', path=path, actions=[])]
                continue
            ev, changes, keys = parse(raw).get('event'), [], []
            if eid in (9271111, 9271112):
                prerequisite = ('flag = ind_v3_dockyard_act NOT = { flag = ' + STANDARD + ' }' if eid == 9271111 else 'flag = ' + STANDARD)
                valid = prerequisite + ' NOT = { flag = ' + MATURE + ' } NOT = { flag = ' + READY + ' }'
                tr = ev.get('trigger')
                changes.append((tr.start + 1, tr.start + 1, '\n' + valid + '\n'))
                for af in actions(ev):
                    a = af.value
                    build = [c for c in a.all('command') if c.get('type') == 'build_time']
                    if not build: continue
                    if len(build) != len(HULLS) or {c.get('which') for c in build} != set(HULLS):
                        raise ValueError('Unexpected dockyard hull registry')
                    changes.append(gate(a, valid))
                    for c in build:
                        expected = -50 if eid == 9271111 else -50 - LEGACY[c.get('which')]
                        if int(c.get('value')) != expected or c.get('where') != 'relative' or c.get('when') != 'on_upgrade':
                            raise ValueError('Expected uncompiled authored dockyard modifiers')
                        f = c.field('value')
                        changes.append((f.value_start, f.end, str(expected + 25)))
                    tail = ('\n' + delta(-25, 'atwar = yes') + '\n' + command('setflag', READY) + '\n' +
                        command('setflag', PEACE, 'atwar = no') + '\n' + command('clrflag', PEACE, 'atwar = yes') + '\n')
                    changes.append((a.end - 1, a.end - 1, tail))
                    keys.append(af.key)
                f = ev.field('desc')
                changes.append((f.value_start, f.end, json.dumps("Standardized yards cut new-hull schedules by 25% of each class's model-zero construction time. Emergency wartime shifts add another 25%. Daily IC cost and research stay unchanged; existing orders may retain their completion dates.")))
                changes.append((ev.end - 1, ev.end - 1, '\n action = { trigger = { NOT = { AND = { ' + valid + ' } } } name = "The construction standard is already recorded" }\n'))
                detail = 'Permanent -25 points plus wartime -25 points; original earned legacy hull differences preserved. Paired event/action gates and existing ready/peace flags prevent duplicate standards and reversed transitions. Original costs, technology and non-build-time effects unchanged.'
            else:
                for af in actions(ev):
                    if any(c.get('type') == 'event' and c.get('which') == '9282090' for c in af.value.all('command')):
                        changes.append(gate(af.value, DEBT_CAP))
                        keys.append(af.key)
                detail = 'Only borrowing choices are barred at debt tier4 OR debt overhang (NOR predicate). Original rewards, annual scheduling, taxation, ordinary revenue, repayment and research commands remain byte-identical.'
            changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n'))
            updated = replace(raw, changes)
            parse(updated)
            edits.append((ef.start, ef.end, updated))
            records[eid] = [dict(dimension='runtime_safety', status='CORRECTED_SCRIPT', path=path, actions=keys, detail=detail),
                dict(dimension='runtime_safety', status='UNRESOLVED', path=path, actions=[], detail='Fresh-game primary. Dockyard legacy flags must truthfully represent documented earned modifiers; arbitrary save damage is not migrated. Engine modifier rounding, existing production completion dates and notification timing need native validation. Debt callback generations and the broader borrowing lifecycle are not redesigned.')]
        output[path] = replace(text, edits)
    path = seen[9271111][0]
    if not existing: output[path] += '\n\n' + controllers()
    for eid in NEW_EVENT_IDS:
        records[eid] = [dict(dimension='runtime_safety', status='CORRECTED_SCRIPT', path=path, actions=['action_a'], registry_reused=True,
            detail='Ported registered B1 state controller with event/action guards. Mature legacy -50 initializes once; peace adds25 and war subtracts25 exactly once per state change. No absolute modifier reset or new event ID allocation.',
            engine_tested=False)]
    return output, records
