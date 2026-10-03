"""Explicit installed-only component dispositions, without silently merging B1.

These are migration requirements, not retirement commands or native signoff.
Unexpected IDs/effects remain visible and require reassessment.
"""
import hashlib
from dh_save_spans import Node, parse, walk

COMPONENTS = {}


def register(ids, disposition, reason, dependencies=()):
    for eid in ids:
        COMPONENTS[eid] = dict(component_disposition=disposition, reason=reason,
                               dependencies=list(dependencies))


register([9297100], 'retain_callable_exit_retire_active_menu',
         'Old Cabinet root is disabled; preserve a safe exit for old references.')
register([9297101], 'rewrite_menu_preserve_capabilities',
         'Current-war campaign access must survive removal of old navigation.',
         [9294031, 9294034, 9294035, 9294032])
register([9297102], 'rewrite_menu_preserve_capabilities',
         'Retain reachable peace choices without nested giant tooltips.',
         [9282212, 9297003, 9289903, 9289905, 9294013, 9294015, 9289870, 9289923])
register([9297103], 'rewrite_menu_preserve_capabilities',
         'Retain economy capabilities; 9270503 is asleep in the reviewed save.',
         [9280310, 9280313, 9280841, 9280203, 9289880, 9270503])
for ids, target in [(range(9297120, 9297122), 9297100), (range(9297122, 9297124), 9297101),
                    (range(9297124, 9297131), 9297102), (range(9297131, 9297149), 9297103)]:
    register(ids, 'retain_callable_compatibility_no_proactive_surface',
             'Moved-menu stub: no reward; old queued/history references need a defined destination.', [target])
register([9297180], 'port_state_initialization',
         'Dockyard readiness is state initialization, not disposable notification.', [9271111, 9271112])
register([9297181, 9297182], 'port_balanced_modifier_pair',
         'Peace adds and war reverses 25 build-time points; port both with migration state.',
         [9271111, 9271112, 9297180])
register([9297190], 'replace_notice_preserve_initialization',
         'Old build notice also sets loaded and historical done flags; replace that payload deliberately.')
register([9297200], 'rebuild_verified_government_transaction',
         'U87 reward verification must travel with its withdrawal/puppetry callers.',
         [9289851, 9289904, 9289852, 9289905])
register([9297201], 'rebuild_verified_government_transaction',
         'Indochina reward verification must travel with its withdrawal/puppetry callers.', [9294014, 9294015])
register([9297202], 'rebuild_verified_government_transaction',
         'Siam verification precedes access and settlement callbacks.',
         [9297004, 9297005, 9297006, 9297007])

SAFETY_UNITS = [
    ('opponent_withdrawal', 'Snapshots, detachment checks, deferred rewards and 9297200–02 must be rebuilt together; checks do not undo a wrong peace.'),
    ('coalition_peace', 'Whole-action peace scope and matching stale replies, treaty preservation and peace value semantics; B1 reports 478 guarded commands.'),
    ('japan_hostility', 'Keep current-war exclusion and usable stale exits for Japanese cooperation.'),
    ('decision_prerequisites', 'Retain date/resource/action eligibility while replacing navigation; reconcile historical single-use flags with legitimate retries.'),
    ('debt_cap', 'Retain lending cap and repayment behavior at 9282080/9282081.'),
    ('dockyard_pair', 'Reconcile 9271111/9271112 with 9297180–82, preserving earned modifiers exactly once.'),
    ('presentation_ai', 'Keep bounded descriptions, usable exits and intentional response odds; do not copy huge combined tooltip predicates.'),
    ('stock_japan', 'Outside custom corpus: 2011028 surrender and 2011018 MAN/MEN mastery safeguards.'),
    ('stock_china', 'Outside custom corpus: 2012004/2012005 inherit/end_mastery/make_puppet safeguards.'),
]


def event_index(files):
    result = {}
    for path, text in files.items():
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            if eid in result:
                raise ValueError(f'Duplicate ID {eid}')
            result[eid] = (path, text[ev.start:ev.end], ev)
    return result


def reconcile(authored, installed):
    before, active = event_index(authored), event_index(installed)
    rows = []
    for eid in sorted(active.keys() - before.keys()):
        path, block, ev = active[eid]
        record = dict(COMPONENTS.get(eid, dict(component_disposition='unreviewed',
                           reason='Unexpected installed-only ID; do not drop or automatically port.', dependencies=[])))
        effects, calls = [], []
        for af in ev.fields:
            if af.key == 'action' or (af.key or '').startswith('action_'):
                for c in af.value.all('command'):
                    if c.get('type') == 'event':
                        calls.append(int(c.get('which')))
                    elif c.get('type'):
                        effects.append(c.get('type'))
        menu = eid <= 9297148 and eid in COMPONENTS
        reassess = eid not in COMPONENTS or ev.get('country') != 'IND' or (menu and bool(effects))
        record.update(id=eid, name=ev.get('name'), module=path,
                      installed_sha256=hashlib.sha256(block.encode('latin1')).hexdigest(),
                      commands=sorted(set(effects)), callbacks=sorted(set(calls)),
                      full_lifecycle_review_complete=False, engine_tested=False,
                      implemented_in_staged_authored=False, requires_reassessment=reassess)
        rows.append(record)
    actual = {row['id'] for row in rows}
    return dict(installed_only_count=len(rows), components=rows,
                expected_ids_missing_from_installed_only=sorted(COMPONENTS.keys() - actual),
                unexpected_installed_only_ids=sorted(actual - COMPONENTS.keys()),
                required_safety_units=[dict(key=k, requirement=v, status='pending_reconciliation') for k, v in SAFETY_UNITS],
                auto_merge_performed=False, release_ready=False,
                limitations=['Component disposition is not an implementation or native-engine signoff.',
                             'Stock safeguards are named requirements, not inspected by this custom-module function.'])


def fresh_dispositions(report, staged, records):
    """Resolve obsolete B1-only IDs for NEW campaigns, not save migration."""
    index=event_index(staged)
    references=set()
    flags=set()
    for text in staged.values():
        for n in walk(parse(text)):
            for f in n.fields:
                if f.key=='flag' and isinstance(f.value,str):flags.add(f.value)
                if f.key in ('event','sleepevent') and isinstance(f.value,str) and f.value.isdigit():references.add(int(f.value))
            if n.get('type') in ('event','trigger','sleepevent') and str(n.get('which','')).isdigit():references.add(int(n.get('which')))
    for row in report['components']:
        eid=row['id']
        if row['requires_reassessment']:
            row['fresh_campaign_disposition']='unresolved'
            continue
        if eid in index:
            row['implemented_in_staged_authored']=True
            row['fresh_campaign_disposition']='ported_with_reviewed_family'
            row['staged_sha256']=hashlib.sha256(index[eid][1].encode('latin1')).hexdigest()
        elif eid<9297180 and eid in COMPONENTS:
            if eid in references:raise ValueError('Legacy menu still called by fresh stage '+str(eid))
            if any(dep not in index for dep in row['dependencies'] if dep>=9270000 and dep not in COMPONENTS):
                raise ValueError('Legacy menu capability lost '+str(eid))
            row['fresh_campaign_disposition']='exclude_unreferenced_old_navigation'
            row['implementation_scope']='Old B1 hub/stub not required by fresh authored entry points. This is not old-save compatibility approval.'
        elif eid==9297190:
            if any(f=='ind_cleanup1_loaded' or f.startswith('ind_cleanup1_done_') for f in flags):
                raise ValueError('Legacy B1 notice initialization still consumed')
            row['fresh_campaign_disposition']='exclude_obsolete_notice_and_unused_done_mirrors'
            row['implementation_scope']='No staged condition consumes its old loaded/done flags; do not port an old build announcement.'
        else:row['fresh_campaign_disposition']='unresolved'
    implemented={'opponent_withdrawal':'shared_withdrawal','coalition_peace':'peace_scope',
                 'debt_cap':'runtime_safety','dockyard_pair':'runtime_safety'}
    dimensions={r['dimension'] for rr in records.values() for r in rr}
    for unit in report['required_safety_units']:
        if implemented.get(unit['key']) in dimensions:
            unit['status']='staged_script_port_native_validation_pending'
    report['fresh_campaign_unresolved_ids']=[r['id'] for r in report['components'] if r['fresh_campaign_disposition']=='unresolved']
    return report
