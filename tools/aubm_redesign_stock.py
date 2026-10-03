"""Staged stock-surrender bridge for route-free Indian home-island campaigns.

Build from supplied stock bytes, retain every existing engine command. No file
I/O or install. This is a guard correction, not a surrender engine playtest.
"""
from dh_save_spans import Node, parse, replace, walk
from aubm_stock_settlement_guard import apply_guard, PROTECTED, MARKER as OLD_MARKER
from aubm_stock_settlement_guard import apply_china_client_guard, apply_japan_client_guard

MARKER = '# AUBM_STAGED_STOCK_SURRENDER_V2'


def canonical(node):
    return tuple((f.key, canonical(f.value) if isinstance(f.value, Node) else f.value) for f in node.fields)


def transform(raw):
    text = raw.decode('latin1')
    events = [e for e in parse(text).all('event') if e.get('id') == '2011028']
    if len(events) != 1:
        raise ValueError('Expected exactly one stock Japanese surrender event')
    record = {2011028: [{'dimension': 'stock_surrender_guard', 'status': 'reviewed',
        'detail': 'Existing Indian-war/home-island-control guard no longer requires manual campaign opt-in.',
        'remaining': ['Native surrender/coalition behavior remains untested.',
                      'Other stock safety components require separate reconciliation.'],
        'engine_tested': False}]}
    if MARKER in text[events[0].start:events[0].end]:
        return raw, record
    # Reuse the authored adapter only to establish/validate the exact existing
    # guard contract; then replace its exact protection expression everywhere.
    guarded = apply_guard(raw)
    text = guarded.decode('latin1')
    ev = next(e for e in parse(text).all('event') if e.get('id') == '2011028')
    expected = canonical(parse(PROTECTED))
    edits = []
    matches = 0
    for node in walk(ev):
        for f in node.fields:
            if f.key == 'AND' and isinstance(f.value, Node) and canonical(f.value) == expected:
                opt_in = next(x for x in f.value.fields if x.key == 'flag' and x.value == 'ind_lib1_enabled')
                edits.append((opt_in.start, opt_in.end, ''))
                matches += 1
    action_count = sum(f.key == 'action' or (f.key or '').startswith('action_') for f in ev.fields)
    if matches != action_count + 1:
        raise ValueError('Stock guard coverage drift: header and every action must be reconciled')
    edits.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n'))
    output = replace(text, edits).encode('latin1')
    parse(output)
    return output, record


def transform_files(files):
    """Compose the complete registered Japan/China stock safety bridge."""
    required = {'db/events/japan.txt', 'db/events/china.txt'}
    if set(files) != required:
        raise ValueError('Both registered stock modules are required')
    japan, records = transform(files['db/events/japan.txt'])
    japan = apply_japan_client_guard(japan)
    china = apply_china_client_guard(files['db/events/china.txt'])
    for eid in (2011018, 2012004, 2012005):
        records[eid] = [dict(dimension='stock_client_guard', status='reviewed',
            detail='Explicit targeted transfer/mastery commands cannot consume an actual Indian puppet; other outcomes preserved.',
            engine_tested=False, remaining=['Native country transfer and coalition war behavior require engine tests.'])]
    return {'db/events/japan.txt':japan,'db/events/china.txt':china},records
