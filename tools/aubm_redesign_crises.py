"""Situation-driven partner-war choices; browsing is not a commitment.

Run after cooperation. No event IDs, wars or rewards added. Existing compact
records and actual partner/enemy state replace national-route gates in this
bounded ten-event family. War confirmation/execution remains downstream.
"""
from dh_save_spans import Node, parse, replace, walk
from aubm_redesign_diplomacy import actions, gate

MARKER = '# AUBM_STAGED_CRISIS_V2'
ROWS = {
    9289501: ('allied', ('ENG', 'USA'), ('GER', 'JAP'), 9289525, 'The Allies Ask India to Help'),
    9289541: ('german', ('GER',), ('ENG', 'SOV', 'USA'), 9289565, 'Berlin Asks India to Help'),
    9289581: ('soviet', ('SOV',), ('GER', 'JAP', 'ENG'), 9289605, 'Moscow Asks India to Help'),
    9289621: ('japan', ('JAP',), ('ENG', 'USA', 'SOV'), 9289653, 'Tokyo Asks India to Help'),
    9289661: ('sovereign', (), ('JAP', 'SOV'), 9289685, 'A Partner Calls for Help'),
}


def live(row):
    route, partners, enemies, _, _ = row
    if route == 'sovereign':
        from aubm_redesign_cooperation import CRISIS_VALID
        return CRISIS_VALID
    participants = ' '.join(
        f'AND = {{ exists = {p} NOT = {{ ispuppet = {p} }} '
        f'NOT = {{ war = {{ country = IND country = {p} }} }} '
        f'war = {{ country = {p} country = {e} }} '
        f'NOT = {{ war = {{ country = IND country = {e} }} }} }}'
        for p in partners for e in enemies)
    return ('year = 1937 NOT = { ispuppet = IND } '
            'NOT = { participant = { country = IND value = 4 } } '
            f'flag = ind_aubm_commitment_{route} '
            + ' '.join(f'NOT = {{ flag = ind_aubm_commitment_{other} }} '
                       for other in ('allied', 'german', 'soviet', 'japan') if other != route)
            + ' '.join(f'NOT = {{ war = {{ country = IND country = {p} }} }} ' for p in partners)
            + ('flag = ind_aubm_jp_partnership ' if route == 'japan' else '')
            + 'OR = { ' + participants + ' } '
            + f'NOT = {{ flag = ind_aubm_bespoke_partner_crisis_{route}_resolved }}')


def transform(files):
    result, records = dict(files), {}
    menus = {row[3]: row for row in ROWS.values()}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            if eid not in ROWS and eid not in menus:
                continue
            row = ROWS.get(eid, menus.get(eid))
            route, _, _, _, title = row
            raw = text[ef.start:ef.end]
            ev = parse(raw).get('event')
            records[eid] = [{'dimension': 'crisis_choices', 'status': 'reviewed',
                'detail': 'Current partner-war opportunity; review is navigation only; costs and real choices retained.',
                'remaining': ['Downstream confirmation and war execution require their own lifecycle/native tests.',
                              'Legacy generic operations-board entry points are not retired by this pass.'],
                'engine_tested': False}]
            if MARKER in raw:
                continue
            changes = []
            valid = live(row)
            if eid in ROWS:
                tr = ev.get('trigger')
                changes.append((tr.start, tr.end, '{ ' + valid + ' }'))
                if ev.get('decision') is not None:
                    raise ValueError(f'{eid}: unexpected authored decision; review conversion')
                changes.append((ev.start + 1, ev.start + 1,
                                '\n decision = { ' + valid + ' }\n'))
                description = (
                    "A partner is fighting a war India has not joined. Review your options without committing troops, "
                    "send supplies and money for goodwill and a say in the settlement, or keep out. "
                    "Opening a review changes no policy; formal alliance entry later would bring its wars with it.")
                for key, value in [('name', title), ('desc', description)]:
                    f = ev.field(key)
                    changes.append((f.value_start, f.end, '"' + value + '"'))
                for af in actions(ev):
                    a = af.value
                    commands = a.all('command')
                    if not commands:
                        continue
                    # Source cooperation already guards its actions; an extra
                    # identical eligibility layer is harmless but unnecessary.
                    if eid != 9289661:
                        changes.append(gate(a, valid))
                    navigation = any(c.get('type') == 'event' for c in commands) and all(
                        c.get('type') in ('event', 'setflag') for c in commands)
                    if navigation:
                        for cf in a.fields:
                            if cf.key == 'command' and cf.value.get('type') == 'setflag':
                                flag = cf.value.get('which', '')
                                if not flag.startswith(f'ind_aubm_bespoke_partner_crisis_{route}_'):
                                    raise ValueError(f'{eid}: unexpected effect in reviewed navigation')
                                changes.append((cf.start, cf.end, ''))
                        if af.key == 'action_a':
                            label = 'Review full alliance entry; no commitment yet'
                            changes.append(gate(a, 'atwar = no'))
                        elif af.key == 'action_d':
                            label = 'Review ending the treaty; no commitment yet'
                            changes.append(gate(a, 'atwar = no'))
                        else:
                            label = 'Review possible wars; do not declare one yet'
                        f = a.field('name')
                        changes.append((f.value_start, f.end, '"' + label + '"'))
                if not any(not a.value.all('command') for a in actions(ev)):
                    changes.append((ev.end - 1, ev.end - 1,
                                    '\n action = { trigger = { ai = no } name = "Not now - keep current orders" }\n'))
            else:
                # The only readers of separate_campaign are these five review
                # pages. Real current war/compact conditions replace that click.
                obsolete = {f'ind_aubm_route_{route}', 'ind_aubm_bespoke_route_contract_alpha23',
                            f'ind_aubm_bespoke_partner_crisis_{route}_separate_campaign'}
                obsolete.update({'ind_aubm_route_soviet', 'ind_aubm_route_sovereign',
                                 'ind_aubm_socialist_autonomous'} if route in ('soviet', 'sovereign') else set())
                def policy_only(field):
                    if field.key == 'flag':
                        return isinstance(field.value, str) and field.value in obsolete
                    return (field.key in ('AND', 'OR', 'NOT') and isinstance(field.value, Node)
                            and bool(field.value.fields) and all(policy_only(f) for f in field.value.fields))
                def prune(node):
                    for field in node.fields:
                        if policy_only(field):
                            changes.append((field.start, field.end, ''))
                        elif isinstance(field.value, Node):
                            prune(field.value)
                for af in actions(ev):
                    a = af.value
                    if not a.all('command'):
                        continue
                    is_return = 'return' in a.get('name', '').lower()
                    if is_return:
                        # Do not force another operations-board popup on exit.
                        if not all(c.get('type') == 'event' for c in a.all('command')):
                            raise ValueError(f'{eid}: return action has effects')
                        for cf in a.fields:
                            if cf.key == 'command':
                                changes.append((cf.start, cf.end, ''))
                        f = a.field('name')
                        changes.append((f.value_start, f.end, '"Close this review"'))
                        continue
                    if eid == 9289685:
                        from aubm_redesign_cooperation import PARTNERS, crisis_partner
                        enemy = 'JAP' if af.key == 'action_a' else 'SOV'
                        current_partners = ' OR = { ' + ' '.join(
                            'AND = { ' + crisis_partner(p) + ' }'
                            for p, (_, opponent) in PARTNERS.items() if opponent == enemy) + ' }'
                        replacement = (valid + current_partners + f' exists = {enemy} '
                                       f'NOT = {{ war = {{ country = IND country = {enemy} }} }} '
                                       f'NOT = {{ alliance = {{ country = IND country = {enemy} }} }}')
                        tr = a.get('trigger')
                        changes.append((tr.start, tr.end, '{ ' + replacement + ' }'))
                    else:
                        changes.append(gate(a, valid))
                        prune(a.get('trigger') or Node())
                f = ev.field('name')
                changes.append((f.value_start, f.end, '"Review India\'s War Options"'))
                f = ev.field('desc')
                changes.append((f.value_start, f.end,
                    '"These are wars your current partner is already fighting. Review an eligible opponent to reach the existing war confirmation; this page itself declares no war. Close the review to keep your present orders."'))
            changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n'))
            # Coalesce same-position gate insertions, preserving order.
            merged = {}
            for start, end, value in changes:
                if (start, end) in merged and start != end:
                    raise ValueError('Overlapping crisis edits')
                merged[start, end] = merged.get((start, end), '') + value
            rewritten = replace(raw, [(s, e, v) for (s, e), v in merged.items()])
            parse(rewritten)
            edits.append((ef.start, ef.end, rewritten))
        result[path] = replace(text, edits)
    return result, records
