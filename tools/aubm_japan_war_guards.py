"""Guard Japanese cooperation against a current India--Japan war.

Pure, idempotent compiler transform. Does not edit files or settlements.
Historical orientation flags can outlive a partnership. Action-level guards
also protect queued replies, which may bypass an event's normal trigger.
"""
from __future__ import annotations

import re

from aubm_menu_safety import event_spans
from ensure_decision_visibility import top_blocks

WAR = 'war = { country = IND country = JAP }'
GUARD = f'NOT = {{ {WAR} }}'
MARKER = '# AUBM_JAPAN_WAR_GUARD'

# These events exclusively conduct or reward cooperation. Guard their normal
# entry as well as each substantive action. Keep IDs and all original commands.
FULL_IDS = {
    9272202, 9272211,
    9281100, 9281101, 9281110, 9281111, 9281112, 9281123,
    9281131, 9281132, 9281133, 9281134, 9281135, 9281136, 9281137,
    9281140, 9281141, 9281142, 9281143, 9281144, 9281145, 9281146,
    9281150, 9281151, 9281152, 9281153, 9281164,
    9281180, 9281182, 9281183, 9281184, 9281190, 9281191, 9281192,
    9281193,
}
# Mixed events retain refusal, China aid, sovereignty and condemnation choices.
PARTIAL_IDS = {
    9272203: {'action_a', 'action_b'},
    9272210: {'action_a', 'action_b'},
    9272212: {'action_a', 'action_b'},
    9281130: {'action_a', 'action_b'},
    9281181: {'action_a', 'action_b', 'action_c'},
}
TARGET_IDS = FULL_IDS | set(PARTIAL_IDS)


def _add_trigger(block: str, guard: str = GUARD) -> str:
    triggers = top_blocks(block, 'trigger')
    if triggers:
        opening = triggers[0][1]
        return block[:opening + 1] + '\n\t\t\t' + guard + block[opening + 1:]
    opening = block.index('{')
    return block[:opening + 1] + '\n\t\ttrigger = { ' + guard + ' }' + block[opening + 1:]


def transform(text: str) -> str:
    """Apply only the explicitly reviewed Japanese cooperation event IDs."""
    for start, end, eid in reversed(list(event_spans(text))):
        if eid not in TARGET_IDS:
            continue
        event = text[start:end]
        if MARKER in event:
            continue
        actions = top_blocks(event, r'action(?:_[a-z]+)?')
        for astart, opening, closing in reversed(actions):
            action = event[astart:closing + 1]
            key = re.search(r'action(?:_[a-z]+)?', action).group()
            # Existing effect-free exits remain available in every state.
            if not top_blocks(action, 'command'):
                continue
            if eid in FULL_IDS or key in PARTIAL_IDS.get(eid, set()):
                event = event[:astart] + _add_trigger(action) + event[closing + 1:]
        if eid in FULL_IDS:
            # Decision visibility and event trigger are independent surfaces.
            decisions = top_blocks(event, 'decision')
            if decisions:
                opening = decisions[0][1]
                event = event[:opening + 1] + '\n\t\t' + GUARD + event[opening + 1:]
            event = _add_trigger(event)
        # A delayed offer can arrive after war starts. Never leave its modal
        # with no available action; this exit changes no state or history flags.
        human_exit=eid in PARTIAL_IDS or bool(top_blocks(event,'decision'))
        fallback = (
            '\n\t' + MARKER + '\n'
            '\taction = {\n'
            '\t\ttrigger = { ' + ('ai = no ' if human_exit else '') + WAR + ' }\n'
            '\t\tai_chance = ' + ('0' if human_exit else '100') + '\n'
            '\t\tname = "Close the old proposal - India and Japan are at war"\n'
            '\t}\n'
        )
        event = event[:-1] + fallback + '}'
        text = text[:start] + event + text[end:]
    return text
