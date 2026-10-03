"""Bounded prose fixes and whole-corpus layout-risk inventory, not native QA.

Character/word wrapping is a conservative screening proxy. It is not a font
measurement, screenshot, or proof that Darkest Hour will render a popup safely.
Never cut an arbitrary description or silently remove a gameplay warning.
"""
from __future__ import annotations

import re
import textwrap
from dh_save_spans import Node, parse, replace


CATALOG = {
    9270000: (
        "At midnight on 1 January 1933, the Lahore Accord ends British rule.",
        "The Lahore Accord ends British rule. Burma, Ceylon and the princely states join a provisional Union, outside every great-power bloc. Delhi inherits an uneven military, sterling reserves and recruits. Modernisation still needs the normal upgrade budget; ties with Britain, America and China improve."),
    9271307: (
        "Choose a national school system or technical colleges.",
        "India needs classrooms and engineers. Schools cost 450 money and 12 manpower: -3 dissent, +3 research and -2 money production. Technical colleges cost 200 money and 8 manpower: +4 research and two Bangalore factories. Choose once."),
    9270306: (
        "Nepal supplies recruits for India's Gurkha regiments.",
        "Nepal's recruits give Delhi three choices: three mountain divisions at higher cost and +2 dissent; two through a cheaper agreement with -1 dissent; or a school with one division and permanent +2 organisation/+2 morale for ALL Indian mountain units. These are full divisions. Choose once."),
    9271006: (
        "Choose the next aircraft orders.",
        "The air staff wants another production run. A balanced force orders an interceptor, tactical bomber and naval bomber; continental defence orders the first two; maritime operations orders a naval bomber and transport wing. Aircraft enter production, not immediate service. Keep their queues funded."),
    9271204: (
        "The western frontier and the great plains reward speed,",
        "Indian officers want armour that can move beyond the railway. Tanks and motorised formations need fuel, steel and mechanics. Existing cavalry must be fully reinforced before conversion; refits still draw on the normal Upgrades budget."),
    9271206: (
        "Army exercises show weak communications and a shortage of trained staff.",
        "The manoeuvres expose weak signals and too few staff officers. Order two infantry divisions, a tank-motorised-infantry force, or one infantry division with officer training and +1 research. Training also improves two named commanders. All units enter production and need funding. Choose once."),
    9273200: (
        "A year of emergency finance has exposed the real burden of the long war.",
        "A year of war has exhausted the first budget. Imports cost more and every service wants the same machine tools. Tax excess profits, ask households to lend again, or slow military expansion to protect civilian consumption. Who should carry the next year's burden?"),
    9273203: (
        "The armed forces can no longer expand through volunteers and princely contingents alone.",
        "Volunteers can no longer fill every regiment. Universal service brings the largest pool at a political cost; selective service favours technical skills; a professional army grows more slowly. This law changes recruitment, not discounted division orders. Every choice keeps the annual trained-reserve class."),
}

TITLES = {
    9289911: 'The Soviet Frontier: Our Hold Is Broken',
    9289912: 'The Soviet Frontier: Victory Holds',
    9289921: 'Japan: Our Hold Is Broken',
    9289922: 'Japan: Victory Holds',
    9289935: 'The Western Corridor: Our Hold Is Broken',
    9289936: 'The Western Corridor Holds',
    9289937: 'Invest in the Western Corridor',
    9294011: 'Indochina: Our Hold Is Broken',
    9294012: 'Indochina: Victory Holds',
    9289543: 'Berlin: Other Fronts',
    9289563: "Berlin's Counteroffer",
    9289583: 'Moscow: Other Fronts',
    9289602: 'Moscow: Recognition of Indian Victories',
    9289603: "Moscow's Counteroffer",
    9289605: 'Moscow: Separate Indian Wars',
    9289623: 'Tokyo: Other Fronts',
    9289643: "Tokyo's Counteroffer",
    9289663: 'India: Other Fronts',
    9289682: 'India: Recognition of Our Victories',
    9289683: 'India: A Counteroffer',
    9289685: 'India: Separate Wars',
}


def transform(files):
    result, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            if eid in TITLES and '# AUBM_STAGED_NAVIGATION_V1' not in text[ev.start:ev.end]:
                f = ev.field('name')
                if f.value != TITLES[eid]:
                    edits.append((f.value_start, f.end, '"' + TITLES[eid] + '"'))
                reviews[eid] = [dict(dimension='presentation', status='reviewed', path=path,
                    detail='Explicit short title; behavior and remaining prose are not certified.',
                    native_layout_verified=False)]
            if eid not in CATALOG:
                continue
            prefix, prose = CATALOG[eid]
            current = ev.get('desc', '')
            if current != prose and not current.startswith(prefix):
                reviews[eid] = [dict(dimension='presentation', status='pending',
                    detail='Description changed upstream; no unreviewed overwrite.', path=path)]
                continue
            assert len(prose) <= 340
            if current != prose:
                f = ev.field('desc')
                edits.append((f.value_start, f.end, '"' + prose + '"'))
            reviews[eid] = [dict(dimension='presentation', status='reviewed', path=path,
                detail='Authored shorter description; no commands, conditions or buttons changed.',
                native_layout_verified=False)]
        result[path] = replace(text, edits)
    # These generated resource lists are a separate tooltip override, not the
    # event story. Removing only their known prefix restores the native fallback
    # to desc. Preserve all manual/bespoke decision warnings and game effects.
    for path, text in result.items():
        edits = []
        for ev in parse(text).all('event'):
            value = ev.get('decision_desc', '')
            if not value.startswith(('Cabinet funding estimates:', 'Funding estimates:')):
                continue
            if '# AUBM_DECISION_DESC_MANUAL' in text[ev.start:ev.end]:
                continue
            f = ev.field('decision_desc')
            edits.append((f.start, f.end, ''))
            reviews.setdefault(int(ev.get('id')), []).append(dict(
                dimension='helper_cleanup', status='reviewed', path=path,
                detail='Removed generated funding tooltip override; native desc fallback and effect tooltips remain.',
                native_layout_verified=False))
        result[path] = replace(text, edits)
    return result, reviews


def audit(files):
    entries, hard_errors = [], []
    for path, text in files.items():
        for ev in parse(text).all('event'):
            eid = int(ev.get('id'))
            actions = [f.value for f in ev.fields
                       if f.key == 'action' or (f.key or '').startswith('action_')]
            fields = [(k, ev.get(k, '')) for k in ('name', 'desc', 'decision_desc')]
            fields += [('action_name', a.get('name', '')) for a in actions]
            risks = []
            for key, value in fields:
                if not isinstance(value, str):
                    hard_errors.append(dict(id=eid, field=key, problem='non-text UI field'))
                    continue
                if '\xa7' in value or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
                    hard_errors.append(dict(id=eid, field=key, problem='colour/control code requires review'))
                limit = 58 if key in ('name', 'action_name') else 500
                if len(value.encode('latin1')) > limit:
                    hard_errors.append(dict(id=eid, field=key, problem=f'exceeds {limit}-byte script budget'))
                # Preserve explicit line breaks, including the engine's literal \n.
                lines = sum(max(1, len(textwrap.wrap(line, width=55)))
                            for line in value.replace('\\n', '\n').splitlines())
                if key == 'desc' and lines > 6:
                    risks.append('description_exceeds_six_proxy_lines')
                if key == 'action_name' and len(value) > 50:
                    risks.append('long_button_label')
            if len(actions) > 4:
                risks.append('more_than_four_authored_buttons_visibility_unverified')
            generated_helper = ev.get('decision_desc', '').startswith(
                ('Cabinet funding estimates:', 'Funding estimates:'))
            if generated_helper:
                risks.append('legacy_generated_funding_helper')
            trigger_sizes = []
            for owner in [ev] + actions:
                for key in ('trigger', 'decision', 'decision_trigger'):
                    node = owner.get(key)
                    if isinstance(node, Node):
                        trigger_sizes.append(node.end - node.start)
            if max(trigger_sizes, default=0) >= 10000:
                risks.append('large_condition_tooltip')
            entries.append(dict(id=eid, path=path, name=ev.get('name'),
                description_bytes=len(ev.get('desc', '').encode('latin1')),
                legacy_generated_funding_helper=generated_helper,
                authored_action_count=len(actions), max_condition_bytes=max(trigger_sizes, default=0),
                risks=sorted(set(risks)), native_layout_verified=False))
    return dict(events_checked=len(entries), hard_errors=hard_errors,
        legacy_generated_funding_helpers=sum(e['legacy_generated_funding_helper'] for e in entries),
        events_with_layout_risks=sum(bool(e['risks']) for e in entries),
        method='55-character word-wrap screening, not measured native glyph layout. Conditional buttons may be hidden.',
        colour_issue_resolved=False, native_layout_verified=False, events=entries)
