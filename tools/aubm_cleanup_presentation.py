"""Explicit weights for cleanup's added exits; never rewrite outcome odds.

Pure compiler helper. Trigger/eligibility errors remain validation errors.
Complementary automatic expiry branches keep their own 100-point weight;
human-only cancellation has zero AI weight. Previously implicit ordinary
choices receive an equal distribution only when none had explicit weights.
"""
from __future__ import annotations

import re

from dh_save_spans import Node, parse

HUMAN_EXITS = {
    'Cancel - close without changes',
    'Keep fighting - close these peace talks',
}
EXPIRY_EXITS = {
    'Close the old proposal - India and Japan are at war',
    'These peace terms no longer apply',
}


def normalize(text: str) -> str:
    """Add missing explicit weights only around reviewed added exit labels."""
    edits = []
    for event in parse(text).all('event'):
        fields = [f for f in event.fields if f.key == 'action' or re.fullmatch(r'action_[a-d]', f.key or '')]
        added = []
        for f in fields:
            trigger = f.value.get('trigger')
            human = isinstance(trigger, Node) and trigger.get('ai') == 'no'
            if f.value.get('name') in EXPIRY_EXITS or (f.value.get('name') in HUMAN_EXITS and human):
                added.append(f)
        if not added:
            continue
        originals = [f for f in fields if f not in added]
        for field in added:
            action = field.value
            trigger = action.get('trigger')
            is_human = isinstance(trigger, Node) and trigger.get('ai') == 'no'
            # Human labels alone do not establish that the action is AI-hidden.
            if action.get('name') in HUMAN_EXITS and not is_human:
                continue
            desired = 0 if is_human else 100
            if action.get('ai_chance') is None:
                edits.append((action.start + 1, action.start + 1, f' ai_chance = {desired} '))
        if originals and all(f.value.get('ai_chance') is None for f in originals):
            groups = {}
            # Conditional callback outcomes were implicitly equal within their
            # own eligible set, not across valid and expired circumstances.
            # Group exact predicates only; do not infer logical equivalence.
            conditional = all(isinstance(f.value.get('trigger'), Node) for f in originals)
            for field in originals:
                trigger = field.value.get('trigger')
                key = re.sub(r'\s+', ' ', text[trigger.start:trigger.end]).strip().lower() if conditional else ''
                groups.setdefault(key, []).append(field)
            for group in groups.values():
                quotient, remainder = divmod(100, len(group))
                for i, field in enumerate(group):
                    weight = quotient + (i < remainder)
                    edits.append((field.value.start + 1, field.value.start + 1, f' ai_chance = {weight} '))
    # The global campaign file contains thousands of actions. One linear join
    # avoids copying its complete contents once for every inserted weight.
    parts, cursor = [], 0
    for start, end, value in sorted(edits):
        if start < cursor:
            raise ValueError('Overlapping presentation edits')
        parts.extend((text[cursor:start], value))
        cursor = end
    parts.append(text[cursor:])
    return ''.join(parts)


def audit(text: str) -> list[str]:
    """Strict staged UI/AI checks; reports overlap/trigger issues unchanged."""
    issues = []
    for event in parse(text).all('event'):
        eid = event.get('id', '?')
        description = event.get('desc', '')
        if len(description.encode('cp1252')) > 500:
            issues.append(f'{eid}: description exceeds 500 bytes')
        actions = [f.value for f in event.fields if f.key == 'action' or re.fullmatch(r'action_[a-d]', f.key or '')]
        names = []
        for action in actions:
            name = action.get('name', '')
            names.append(name)
            if len(name.encode('cp1252')) > 58:
                issues.append(f'{eid}: action label exceeds 58 bytes: {name}')
        if len(names) != len(set(names)):
            issues.append(f'{eid}: duplicate action labels')
        chances = [a.get('ai_chance') for a in actions]
        if len(actions) < 2 or not any(c is not None for c in chances):
            continue
        if any(c is None for c in chances):
            issues.append(f'{eid}: explicit/implicit AI chance mix')
            continue
        if any(not re.fullmatch(r'\d+', c) or not 0 <= int(c) <= 100 for c in chances):
            issues.append(f'{eid}: invalid AI weight')
            continue
        if sum(map(int, chances)) == 100:
            continue
        groups = {}
        for action, chance in zip(actions, chances):
            trigger = action.get('trigger')
            if isinstance(trigger, Node) and trigger.get('ai') == 'no' and int(chance) == 0:
                continue
            if not isinstance(trigger, Node):
                groups = {}
                break
            key = re.sub(r'\s+', ' ', text[trigger.start:trigger.end]).strip().lower()
            groups.setdefault(key, []).append(int(chance))
        if len(groups) < 2 or any(sum(group) != 100 for group in groups.values()):
            issues.append(f'{eid}: AI chances do not form complete 100-point trigger groups')
    return issues
