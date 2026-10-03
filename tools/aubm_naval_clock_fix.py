"""Pure NAVAL1 overlay: saved callback clocks instead of persistent-event dates.

Apply after the staged navy transform. No installation or save writes here.
Old paid contracts lacking a clock retain their calendar fallback. New paid
actions arm exactly one callback; opening/cancelling a decision cannot arm it.
"""
import json
from dh_save_spans import Node, parse, replace, walk
from aubm_redesign_navy import TIMING, paid_flag, calendar_gate, exact_programme

MARKER = '# AUBM_NAVAL1_CALLBACK_CLOCK'
CALLBACKS = dict(zip(TIMING, range(9297190, 9297195)))
NOTICES = (9297195, 9297196)
NEW_EVENT_IDS = set(CALLBACKS.values()) | set(NOTICES)
CATCHUP = 'ind_aubm_naval1_catchup'


def armed(eid): return 'ind_aubm_naval1_clock_' + str(eid)
def ready(eid): return 'ind_aubm_naval1_ready_' + str(eid)


def callback(eid):
    return f'''event = {{
 {MARKER}
 id = {CALLBACKS[eid]} country = IND random = no
 name = "Naval construction review available"
 desc = "The funded construction interval has elapsed. The next appropriation remains a separate choice."
 style = 2 picture = "india_v3_armed_forces"
 action_a = {{ name = "Record the completed interval"
  command = {{ type = setflag which = {ready(eid)} }}
 }}
}}
'''


def notice(eid, title, detail):
    return f'''event = {{
 {MARKER}
 id = {eid} country = IND random = no
 name = {json.dumps(title)}
 desc = {json.dumps(detail + ' These orders are already present in this recovery save at 90 percent completion. Their appropriation and crews have been accounted for once. Fund the remaining production IC to finish them; acknowledging this notice creates no duplicate orders.')}
 style = 2 picture = "india_v3_armed_forces"
 action_a = {{ name = "Continue the final fitting-out"
  command = {{ type = setflag which = ind_aubm_naval1_notice_{eid} }}
 }}
}}
'''


def transform(files):
    output = dict(files)
    index = {}
    for path, text in files.items():
        for e in parse(text).all('event'):
            eid = int(e.get('id'))
            if eid in index: raise ValueError(f'Duplicate event {eid}')
            index[eid] = (path, e)
    if NEW_EVENT_IDS & index.keys():
        if not NEW_EVENT_IDS <= index.keys(): raise ValueError('Partial NAVAL1 overlay')
        if not all(MARKER in files[index[i][0]][index[i][1].start:index[i][1].end] for i in NEW_EVENT_IDS):
            raise ValueError('NAVAL1 ID collision')
        return output, {}
    if not set(TIMING) <= index.keys(): raise ValueError('Staged naval events missing')
    edits = {p: [] for p in files}
    records = {}
    for target, info in TIMING.items():
        path, e = index[target]
        text = files[path]
        replacements = 0
        # Match the complete two-branch timing gate, including the programme-
        # dependent commissioning delay. Preserve every resource/context gate.
        for n in walk(e):
            if len(n.fields) != 2 or any(f.key != 'AND' for f in n.fields): continue
            first, second = [f.value for f in n.fields]
            if first.get('flag') != paid_flag(info['previous']): continue
            neg = second.get('NOT')
            if not isinstance(neg, Node) or neg.get('flag') != paid_flag(info['previous']): continue
            if not any(isinstance(x.get('event'), Node) and x.get('event').get('id') == str(info['previous']) for x in walk(first)): continue
            gate = ('{ AND = { flag = ' + paid_flag(info['previous']) + ' flag = ' + ready(target)
                    + ' } AND = { NOT = { flag = ' + armed(target) + ' } '
                    + calendar_gate(*info['legacy']) + ' } }')
            edits[path].append((n.start, n.end, gate)); replacements += 1
        if replacements < 3: raise ValueError(f'Timer gate drift for {target}: {replacements}')
        tooltip = e.field('decision_desc')
        days = '/'.join(map(str, info['days'])) if isinstance(info['days'], tuple) else str(info['days'])
        description = str(tooltip.value).replace('elapsed time, not queue progress. Legacy contracts retain their original calendar gate.',
            'a saved construction callback unlocks the next review. Existing contracts without that callback retain the calendar fallback.')
        edits[path].append((tooltip.value_start, tooltip.end, json.dumps(description)))
        source_path, source = index[info['previous']]
        count = 0
        for f in source.fields:
            if not f.key or not f.key.startswith('action') or not isinstance(f.value, Node): continue
            a = f.value
            if not any(c.get('type') == 'setflag' and c.get('which') == paid_flag(info['previous']) for c in a.all('command')): continue
            fresh = 'NOT = { flag = ' + armed(target) + ' }'
            delays = enumerate(info['days']) if isinstance(info['days'], tuple) else [(None, info['days'])]
            cmds = []
            for branch, delay in delays:
                condition = fresh + (' ' + exact_programme(branch) if branch is not None else '')
                cmds.append(f' command = {{ trigger = {{ {condition} }} type = event which = {CALLBACKS[target]} where = IND when = {delay} }}')
            cmds.append(f' command = {{ type = setflag which = {armed(target)} }}')
            edits[source_path].append((a.end - 1, a.end - 1, '\n' + '\n'.join(cmds) + '\n'))
            count += 1
        if count == 0: raise ValueError(f'No paid action for clock {target}')
        records[target] = [dict(dimension='naval_clock', status='reviewed',
                               changes=f'Saved {days}-day callback; cancel does not start a clock; legacy fallback retained')]
    for path, changes in edits.items():
        if changes: output[path] = replace(files[path], changes)
    navy_path = index[9271105][0]
    output[navy_path] += '\n' + '\n'.join(callback(eid) for eid in TIMING)
    output[navy_path] += '\n' + notice(NOTICES[0], 'The Bay of Bengal Fleet: Overdue Orders Restored',
        'INS Purvasagar, INS Chilika, INS Coromandel and the two Bengal escort flotillas are in final fitting-out. Appropriation: 500 money and 1100 supplies.')
    output[navy_path] += '\n' + notice(NOTICES[1], 'The Oceanic Fleet: Overdue Carrier Restored',
        'INS Samudra with its carrier air group, INS Makran, INS Malacca and two ocean escort flotillas are in final fitting-out. Appropriation: 900 money and 2100 supplies.')
    # Authorization is design expenditure, not an invisible ship order.
    t = output[navy_path]; e = next(e for e in parse(t).all('event') if e.get('id') == '9271103')
    f = e.field('desc')
    t = replace(t, [(f.value_start, f.end, json.dumps(
        'Choose a fleet carrier, two light carriers or an ocean-denial submarine arm. Carrier authorization pays for design and training only; no aviation ship enters production yet. Fund the Arabian Sea Fleet, then the Bay of Bengal Fleet, then the Oceanic Fleet keels to order the carrier hulls. The submarine choice orders one submarine immediately.'))])
    output[navy_path] = t
    return output, records
