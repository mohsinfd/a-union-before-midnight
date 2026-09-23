#!/usr/bin/env python3
"""Human-only, effect-free exits for the connected War Cabinet menus.

DH supports additional bare ``action`` blocks beside legacy action_a-d.
Keep every original choice and ID intact. Put the safe exit first so it is
visible without scrolling, including when substantive options are filtered.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from validate_v4 import direct_scalar, extract_blocks, scalar, strip_comments, event_action_blocks, invalid_event_action_keys

ROOT = Path(__file__).resolve().parents[1]
MENU_IDS = {
    "32_national_consolidation.txt": {9281012, 9281013},
    "41_wartime_state.txt": {
        9281910, 9281919, 9281914, 9281934, 9281911, 9281915,
        9281912, 9281916, 9281917, 9281918, 9281913,
        9281926, 9281927, 9281928, 9281929, 9281999,
    },
    "42_wartime_theatres.txt": {9281930, 9281931, 9281932, 9281933, 9281980, 9281981},
    "51_bespoke_route_arcs.txt": {
        9289499, 9289500, 9289540, 9289580, 9289620, 9289660,
        9289525, 9289565, 9289605, 9289653, 9289685,
        9289645, 9289646, 9289647, 9289648,
    },
}
LABEL = "Cancel - close without changes"
CANCEL = (
    '\t# AUBM_MENU_SAFE_EXIT: human-only; no effects or follow-up event.\n'
    '\taction = {\n'
    '\t\ttrigger = { ai = no }\n'
    f'\t\tname = "{LABEL}"\n'
    '\t}\n'
)


def event_spans(text: str):
    """Offsets in original text (unlike comment-stripped validator blocks)."""
    for match in re.finditer(r"(?m)^event\s*=\s*\{", text):
        depth = 1
        for token in re.finditer(r'"[^\"]*"|#[^\n]*|[{}]', text[match.end():]):
            if token[0] == '{': depth += 1
            elif token[0] == '}': depth -= 1
            if depth == 0:
                end = match.end() + token.end()
                yield match.start(), end, int(direct_scalar(text[match.start():end], 'id'))
                break
        else:
            raise ValueError('Unbalanced event block')


def ensure_menu_exits(text: str, event_ids: set[int]) -> str:
    newline = '\r\n' if '\r\n' in text else '\n'
    addition = CANCEL.replace('\n', newline)
    edits, found = [], set()
    for start, end, eid in event_spans(text):
        if eid not in event_ids: continue
        found.add(eid)
        block = text[start:end]
        if addition in block: continue
        if LABEL in block: raise ValueError(f'{eid}: malformed/duplicate safe exit')
        if direct_scalar(block, 'one_action') == 'yes':
            raise ValueError(f'{eid}: do not add cancellation to one-action callbacks')
        first = re.search(r'(?m)^[ \t]*action(?:_[a-z]+)?\s*=\s*\{', block)
        if not first: raise ValueError(f'{eid}: no existing actions')
        edits.append(start + first.start())
    if found != event_ids: raise ValueError(f'Missing menus: {sorted(event_ids - found)}')
    for offset in reversed(edits): text = text[:offset] + addition + text[offset:]
    return text


def validate_text(text: str, event_ids: set[int]) -> int:
    found = set()
    for start, end, eid in event_spans(text):
        if eid not in event_ids: continue
        found.add(eid)
        block = text[start:end]
        all_actions = []
        assert not invalid_event_action_keys(block), f'{eid}: unsupported action label'
        all_actions.extend(event_action_blocks(block))
        exits = [a for a in all_actions if scalar(a.text, 'name') == LABEL]
        assert len(exits) == 1, f'{eid}: exactly one safe exit required'
        exit_text = exits[0].text
        assert not extract_blocks(exit_text, 'command'), f'{eid}: cancel changes state'
        assert re.sub(r'\s+', '', strip_comments(exit_text)) == re.sub(
            r'\s+', '', strip_comments(CANCEL)), f'{eid}: exit must depend only on human control'
        first = re.search(r'(?m)^[ \t]*action(?:_[a-z]+)?\s*=\s*\{', block)
        assert first and block[first.start():].lstrip().startswith('action = {'), f'{eid}: exit must be first'
        assert direct_scalar(block, 'one_action') != 'yes', f'{eid}: exit can be hidden by one_action'
        assert len(LABEL.encode('cp1252')) <= 58
        assert ensure_menu_exits(block, {eid}) == block, f'{eid}: patch not idempotent'
    assert found == event_ids, f'Missing protected menus: {event_ids - found}'
    return len(found)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='mechanically add exits to source event files')
    ap.add_argument('--check', action='store_true', help='validate without writing (default)')
    ap.add_argument('--mod-root', type=Path, default=ROOT / 'mod')
    args = ap.parse_args()
    count = 0
    for filename, ids in MENU_IDS.items():
        path = args.mod_root / 'db/events/aubm_v4' / filename
        raw = path.read_bytes()
        text = raw.decode('cp1252')
        patched = ensure_menu_exits(text, ids)
        if args.write and patched != text:
            path.write_bytes(patched.encode('cp1252'))
            text = patched
        assert patched == text, f'{filename}: safe exits are missing'
        count += validate_text(text, ids)
    print(f'OK: {count} connected Cabinet menus have a first, human-only, effect-free cancel action')
    return 0


if __name__ == '__main__': raise SystemExit(main())
