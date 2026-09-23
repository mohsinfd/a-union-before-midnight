"""Close queued generic peace replies when either country joins a coalition.

Only generic armistice dialogue is transformed. Annexation/restoration choices,
campaign record maintenance and the bespoke Siam withdrawal are not touched.
"""
import re

from dh_save_spans import Node, parse, walk, replace

TARGET = re.compile(r'ind_aubm_(?:regional_armistice|armistice|bespoke_armistice)_target_([a-z0-9]+)$')
REGIONAL_TAGS = ('CHI', 'CHC', 'SIA', 'ITA', 'FRA', 'TUR', 'POR', 'NZL', 'ETH', 'SAF')


def target_flags(node):
    return sorted({f.value for n in walk(node) for f in n.fields
                   if f.key in ('flag', 'which') and isinstance(f.value, str) and TARGET.fullmatch(f.value)})


def scope(tag):
    gate = (f'exists = IND exists = {tag} war = {{ country = IND country = {tag} }} '
            'NOT = { ispuppet = IND } OR = { NOT = { participant = { country = IND value = 4 } } '
            'alliance_leader = { country = IND value = 0 } } '
            f'NOT = {{ participant = {{ country = {tag} value = 4 }} ispuppet = {tag} }}')
    if tag == 'SIA':
        gate += (' NOT = { flag = ind_lib1_siam_break_pending '
                 'flag = ind_lib1_siam_detached flag = ind_lib1_siam_protected }')
    return gate


def actions(event):
    return [f.value for f in event.fields if f.key == 'action' or (f.key or '').startswith('action_')]


def add_gate(text, node, gate):
    trigger = node.get('trigger')
    if isinstance(trigger, Node): return trigger.start+1, trigger.start+1, '\n '+gate+'\n'
    return node.start+1, node.start+1, '\n trigger = { '+gate+' }\n'


def guarded_callbacks(text, filename=''):
    edits = []
    for ev in parse(text).all('event'):
        eid = int(ev.get('id'))
        if 9297000 <= eid < 9297100: continue
        flags = target_flags(ev)
        name = ev.get('name', '')
        regional = False
        if 9282220 <= eid <= 9282229 or 9282230 <= eid <= 9282249:
            tag = REGIONAL_TAGS[(eid-9282220) % 10]
            flags = ['ind_aubm_regional_armistice_target_'+tag.lower()]
            regional = True
        elif eid in (9282260, 9282261, 9282262, 9282263):
            flags = ['ind_aubm_regional_armistice_target_'+t.lower() for t in REGIONAL_TAGS]
            regional = True
        is_reply = regional or bool(re.search(r'Offers.*Armistice|Accepts.*Armistice|Counters.*Armistice|Refuses.*Armistice', name, re.I))
        offers = [a for a in actions(ev) if any(c.get('type') == 'setflag' and
                  TARGET.fullmatch(c.get('which', '')) for c in a.all('command'))]
        if not flags or (not is_reply and not offers): continue
        rules = []
        stale_actions = []
        for a in actions(ev):
            commands = a.all('command')
            if not commands: continue
            # Refusal is part of the fixed response odds and must expire with
            # acceptance. Reuse the old lapse slot to avoid two 100% fallbacks.
            harmless = all(c.get('type') in ('event', 'clrflag', 'setflag') for c in commands)
            if a not in offers and harmless and re.search(r'lapse|no longer appl', a.get('name', ''), re.I):
                stale_actions.append(a)
                continue
            if a not in offers and harmless and re.search(r'cancel|close|return', a.get('name', ''), re.I):
                continue
            if a not in offers and not is_reply: continue
            active_flags = target_flags(a) or flags
            if a in offers:
                active_flags = [c.get('which') for c in commands if c.get('type') == 'setflag' and TARGET.fullmatch(c.get('which', ''))]
                rule = ' '.join(scope(TARGET.fullmatch(f)[1].upper()) for f in active_flags)
            else:
                # Exactly one selected target; a stale mixed request may not
                # execute several country settlements through one generic page.
                choices = []
                for f in active_flags:
                    choices.append('AND = { flag = '+f+' '+scope(TARGET.fullmatch(f)[1].upper())+
                        ''.join(' NOT = { flag = '+other+' }' for other in flags if other != f)+' }')
                rule = 'OR = { '+' '.join(choices)+' }'
            old_trigger = a.get('trigger')
            original = text[old_trigger.start+1:old_trigger.end-1] if isinstance(old_trigger, Node) else ''
            original = re.sub(r'#[^\n]*', '', original).strip()
            edits.append(add_gate(text, a, rule))
            rules.append((original+' '+rule).strip())
        if not rules: continue
        # The new fallback is valid for human or AI, without bonuses, foreign
        # relations changes, government mutation, navigation or new war orders.
        invalid = 'NOT = { OR = { '+' '.join('AND = { '+r+' }' for r in rules)+' } }'
        # An Indian offer MENU already has return/defer actions. Its additional
        # close button is human-only, not a competing 100-point AI reply.
        fallback = '\n action = { trigger = { '+('ai = no ' if not is_reply else '')+invalid+' } ai_chance = '+('0' if not is_reply else '100')+' name = "These peace terms no longer apply"\n'
        regional_flags = any('_regional_' in f for f in flags)
        common = (('ind_aubm_regional_armistice_outstanding', 'ind_aubm_regional_armistice_full', 'ind_aubm_regional_armistice_limited')
                  if regional_flags else ('ind_aubm_universal_armistice_outstanding',))
        selected = 'OR = { '+' '.join('flag = '+f for f in flags)+' }'
        for f in common:
            fallback += ' command = { trigger = { '+selected+' } type = clrflag which = '+f+' }\n'
        for f in flags:
            fallback += ' command = { type = clrflag which = '+f+' }\n'
        fallback += '}\n'
        if stale_actions:
            # Keep the existing action key and replace its guarded contents.
            content = fallback[fallback.index('{'):].strip()
            edits.append((stale_actions[0].start, stale_actions[0].end, content))
            for redundant in stale_actions[1:]:
                # Defensive: extra historical lapse slots become unavailable,
                # so a foreign AI never sees duplicate 100% expiry choices.
                edits.append(add_gate(text, redundant, 'AND = { exists = IND NOT = { exists = IND } }'))
        else:
            edits.append((ev.end-1, ev.end-1, fallback))
        oa = ev.get('one_action')
        if oa == 'yes':
            field = ev.field('one_action'); edits.append((field.value_start, field.end, 'no'))
    return replace(text, edits)
