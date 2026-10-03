#!/usr/bin/env python3
"""Reversible eligibility adapter for stock Japanese surrender event 2011028.

The public API accepts bytes and returns bytes. It does not read or write an
installation, save or repository file. The release builder owns input/output.
"""
import re

from dh_save_spans import Node, parse, replace

EVENT_ID = "2011028"
MARKER = "# AUBM_STOCK_JAPAN_SETTLEMENT_GUARD_V1"
FALLBACK_NAME = "Indian forces hold the home islands; await their terms"
PROTECTED = """exists = IND
war = { country = IND country = JAP }
flag = ind_lib1_enabled
OR = {
    control = { province = 1552 data = IND }
    control = { province = 1553 data = IND }
    control = { province = 1554 data = IND }
}"""
PERMITTED = "NOT = { AND = { " + " ".join(PROTECTED.split()) + " } }"


def apply_guard(raw: bytes) -> bytes:
    """Defer this surrender only during an active Indian home-island campaign.

    Event eligibility protects ordinary polling. Every pre-existing action is
    also guarded because a direct trigger can bypass the event trigger. A
    complementary action has no effects, preventing an empty direct-call UI.
    All original command bytes and all unrelated events are preserved.
    """
    source = raw.decode("latin1")
    matches = [e for e in parse(source).all("event") if e.get("id") == EVENT_ID]
    if len(matches) != 1:
        raise ValueError("Expected exactly one stock Japanese surrender event 2011028")
    event = matches[0]
    if MARKER in source[event.start:event.end]:
        validate_guard(raw)
        return raw
    newline = "\r\n" if b"\r\n" in raw else "\n"
    edits = []

    def guarded(node):
        trigger = node.get("trigger")
        if isinstance(trigger, Node):
            edits.append((trigger.start + 1, trigger.start + 1, (" " + PERMITTED + " ").encode("ascii")))
        else:
            value = newline + "\t\ttrigger = { " + PERMITTED + " }"
            edits.append((node.start + 1, node.start + 1, value.encode("ascii")))

    guarded(event)
    original_actions = [f.value for f in event.fields if f.key in ("action", "action_a", "action_b", "action_c", "action_d")]
    if not original_actions:
        raise ValueError("Japanese surrender has no actions")
    for action in original_actions:
        guarded(action)
    addition = (
        f"\n\t{MARKER}\n"
        "\taction = {\n"
        "\t\ttrigger = { AND = { " + " ".join(PROTECTED.split()) + " } }\n"
        "\t\tai_chance = 100\n"
        f'\t\tname = "{FALLBACK_NAME}"\n'
        "\t}\n"
    ).replace("\n", newline).encode("ascii")
    edits.append((event.end - 1, event.end - 1, addition))
    result = replace(raw, edits)
    validate_guard(result)
    return result


def validate_guard(raw: bytes) -> None:
    source = raw.decode("latin1")
    event = next(e for e in parse(source).all("event") if e.get("id") == EVENT_ID)
    assert MARKER in source[event.start:event.end]
    trigger = event.get("trigger")
    assert isinstance(trigger, Node) and PERMITTED in source[trigger.start:trigger.end]
    fallback = []
    for f in event.fields:
        if f.key not in ("action", "action_a", "action_b", "action_c", "action_d"):
            continue
        action = f.value
        if action.get("name") == FALLBACK_NAME:
            fallback.append(action)
            assert not action.all("command")
            assert " ".join(PROTECTED.split()) in " ".join(source[action.get("trigger").start:action.get("trigger").end].split())
        else:
            trigger = action.get("trigger")
            assert isinstance(trigger, Node) and PERMITTED in source[trigger.start:trigger.end]
    assert len(fallback) == 1


# Descriptive alias for release builders.
guard_japan_surrender = apply_guard


CHINA_EVENT_IDS = ("2012004", "2012005")
CHINA_MARKER = "# AUBM_STOCK_CHINA_CLIENT_GUARD_V1"
CLIENT_TRANSFER_TYPES = frozenset(("inherit", "end_mastery", "make_puppet"))
ACTION_KEYS = frozenset(("action", "action_a", "action_b", "action_c", "action_d"))


def _china_events(source):
    events = parse(source).all("event")
    selected = []
    for event_id in CHINA_EVENT_IDS:
        matches = [e for e in events if e.get("id") == event_id]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one stock China event {event_id}")
        selected.extend(matches)
    return selected


def _client_transfers(event):
    for field in event.fields:
        if field.key not in ACTION_KEYS:
            continue
        for command in field.value.all("command"):
            target = command.get("which")
            if command.get("type") in CLIENT_TRANSFER_TYPES and isinstance(target, str) and re.fullmatch(r"[A-Z][A-Z0-9]{2}", target):
                yield command, target


def _client_permitted(target):
    return f"NOT = {{ puppet = {{ country = {target} country = IND }} }}"


def apply_china_client_guard(raw: bytes) -> bytes:
    """Preserve actual Indian clients without disabling Chinese victory events.

    Only explicitly targeted inherit/end_mastery/make_puppet commands in stock
    events 2012004 and 2012005 are guarded. Existing command conditions remain
    inside an AND, with a live Indian-puppet check. Occupation, old flags and
    disputed mainland claims are deliberately outside this adapter's scope.
    Resource amounts, other commands and event/action eligibility stay intact.
    """
    source = raw.decode("latin1")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    edits = []
    for event in _china_events(source):
        if CHINA_MARKER in source[event.start:event.end]:
            continue
        for command, target in _client_transfers(event):
            condition = _client_permitted(target)
            trigger = command.get("trigger")
            if isinstance(trigger, Node):
                edits.append((trigger.start + 1, trigger.start + 1, b" AND = { "))
                edits.append((trigger.end - 1, trigger.end - 1, (" " + condition + " } ").encode("ascii")))
            else:
                value = " trigger = { " + condition + " } "
                edits.append((command.start + 1, command.start + 1, value.encode("ascii")))
        marker = newline + "\t" + CHINA_MARKER + newline
        edits.append((event.end - 1, event.end - 1, marker.encode("ascii")))
    result = replace(raw, edits)
    validate_china_client_guard(result)
    return result


def validate_china_client_guard(raw: bytes) -> None:
    source = raw.decode("latin1")
    for event in _china_events(source):
        assert CHINA_MARKER in source[event.start:event.end]
        for command, target in _client_transfers(event):
            trigger = command.get("trigger")
            assert isinstance(trigger, Node)
            assert _client_permitted(target) in source[trigger.start:trigger.end]


JAPAN_CLIENT_MARKER = "# AUBM_STOCK_JAPAN_CLIENT_GUARD_V1"


def _japan_client_event(source):
    matches = [e for e in parse(source).all("event") if e.get("id") == "2011018"]
    if len(matches) != 1:
        raise ValueError("Expected exactly one stock Japanese callback 2011018")
    return matches[0]


def _japan_client_commands(event):
    return [(command, target) for command, target in _client_transfers(event)
            if command.get("type") == "end_mastery" and target in ("MAN", "MEN")]


def apply_japan_client_guard(raw: bytes) -> bytes:
    """Do not strip Indian MAN/MEN clients before China's guarded callback.

    This touches only the two explicit end_mastery commands in 2011018. It is
    separate from apply_guard so builders can compose both Japan adapters.
    """
    source = raw.decode("latin1")
    event = _japan_client_event(source)
    if JAPAN_CLIENT_MARKER in source[event.start:event.end]:
        validate_japan_client_guard(raw)
        return raw
    commands = _japan_client_commands(event)
    if sorted(target for _, target in commands) != ["MAN", "MEN"]:
        raise ValueError("Expected exactly the MAN and MEN mastery commands in 2011018")
    edits = []
    for command, target in commands:
        condition = _client_permitted(target)
        trigger = command.get("trigger")
        if isinstance(trigger, Node):
            edits.append((trigger.start + 1, trigger.start + 1, b" AND = { "))
            edits.append((trigger.end - 1, trigger.end - 1, (" " + condition + " } ").encode("ascii")))
        else:
            value = " trigger = { " + condition + " } "
            edits.append((command.start + 1, command.start + 1, value.encode("ascii")))
    newline = "\r\n" if b"\r\n" in raw else "\n"
    marker = newline + "\t" + JAPAN_CLIENT_MARKER + newline
    edits.append((event.end - 1, event.end - 1, marker.encode("ascii")))
    result = replace(raw, edits)
    validate_japan_client_guard(result)
    return result


def validate_japan_client_guard(raw: bytes) -> None:
    source = raw.decode("latin1")
    event = _japan_client_event(source)
    assert JAPAN_CLIENT_MARKER in source[event.start:event.end]
    commands = _japan_client_commands(event)
    assert sorted(target for _, target in commands) == ["MAN", "MEN"]
    for command, target in commands:
        trigger = command.get("trigger")
        assert isinstance(trigger, Node)
        assert _client_permitted(target) in source[trigger.start:trigger.end]
