#!/usr/bin/env python3
"""Make priced DH decisions discoverable, affordable and self-documenting.

Darkest Hour hides an action when its action-level trigger is false. A decision
therefore needs three separate affordability layers: it unlocks when at least
one programme can be funded, every priced action has its own reserve trigger,
and decision_desc lists every programme including currently blocked ones.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


GATE_BEGIN = "# AUBM_FULL_OPTION_GATE_BEGIN"
GATE_END = "# AUBM_FULL_OPTION_GATE_END"
ACTION_GATE_BEGIN = "# AUBM_ACTION_RESERVE_BEGIN"
ACTION_GATE_END = "# AUBM_ACTION_RESERVE_END"
MANUAL_DESC_MARKER = "# AUBM_DECISION_DESC_MANUAL"
RESOURCE_KEYS = ("money", "supplies", "manpower", "oil")


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    comment = False
    index = opening
    while index < len(text):
        char = text[index]
        if comment:
            if char in "\r\n":
                comment = False
        elif quoted:
            if char == '"' and (index == 0 or text[index - 1] != "\\"):
                quoted = False
        elif char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError(f"Unclosed block beginning at character {opening}")


def depth_map(text: str) -> list[int]:
    result = [0] * (len(text) + 1)
    depth = 0
    quoted = False
    comment = False
    for index, char in enumerate(text):
        result[index] = depth
        if comment:
            if char in "\r\n":
                comment = False
        elif quoted:
            if char == '"' and (index == 0 or text[index - 1] != "\\"):
                quoted = False
        elif char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    result[len(text)] = depth
    return result


def top_blocks(text: str, key_pattern: str, target_depth: int = 1) -> list[tuple[int, int, int]]:
    depths = depth_map(text)
    matches: list[tuple[int, int, int]] = []
    pattern = re.compile(rf"(?mi)^([ \t]*)({key_pattern})\s*=\s*\{{")
    for match in pattern.finditer(text):
        if depths[match.start()] != target_depth:
            continue
        opening = text.find("{", match.start(), match.end())
        closing = matching_brace(text, opening)
        matches.append((match.start(), opening, closing))
    return matches


def top_string_field(text: str, key: str) -> tuple[int, int, str] | None:
    depths = depth_map(text)
    pattern = re.compile(rf'(?mi)^([ \t]*){re.escape(key)}\s*=\s*"([^"\r\n]*)"[ \t]*')
    for match in pattern.finditer(text):
        if depths[match.start()] == 1:
            return match.start(), match.end(), match.group(2)
    return None


def marker_pattern(begin: str, end: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?ms)^[ \t]*{re.escape(begin)}.*?^[ \t]*{re.escape(end)}[ \t]*(?:\r?\n)?"
    )


def command_costs(action_text: str) -> dict[str, int]:
    costs = {key: 0 for key in RESOURCE_KEYS}
    command_pattern = re.compile(r"(?mi)^\s*command\s*=\s*\{")
    for match in command_pattern.finditer(action_text):
        opening = action_text.find("{", match.start(), match.end())
        closing = matching_brace(action_text, opening)
        body = action_text[opening + 1 : closing]
        type_match = re.search(
            r"\btype\s*=\s*(money|supplies|manpowerpool|oilpool)\b",
            body,
            re.I,
        )
        value_match = re.search(r"\bvalue\s*=\s*(-\d+)\b", body, re.I)
        if not type_match or not value_match:
            continue
        command_type = type_match.group(1).lower()
        key = {
            "manpowerpool": "manpower",
            "oilpool": "oil",
        }.get(command_type, command_type)
        costs[key] += abs(int(value_match.group(1)))
    if (
        "AUBM_APPROVED_SHBB_HALF_COMPLETE_BEGIN" in action_text
        and re.search(r"\btype\s*=\s*build_division\s+which\s*=\s*battleship\b", action_text)
    ):
        costs["manpower"] = max(costs["manpower"], 3)
    return costs


def trigger_requirements(action_text: str) -> dict[str, int]:
    requirements = {key: 0 for key in RESOURCE_KEYS}
    triggers = top_blocks(action_text, r"trigger")
    if not triggers:
        return requirements
    _start, opening, closing = triggers[0]
    body = action_text[opening + 1 : closing]
    body = marker_pattern(ACTION_GATE_BEGIN, ACTION_GATE_END).sub("", body)
    for key in RESOURCE_KEYS:
        values = [int(value) for value in re.findall(rf"\b{key}\s*=\s*(\d+)", body, re.I)]
        if values:
            requirements[key] = max(values)
    return requirements


def action_requirements(action_text: str) -> dict[str, int]:
    costs = command_costs(action_text)
    requirements = trigger_requirements(action_text)
    return {key: max(costs[key], requirements[key]) for key in RESOURCE_KEYS}


def requirement_lines(requirements: dict[str, int]) -> str:
    return " ".join(
        f"{key} = {requirements[key]}"
        for key in RESOURCE_KEYS
        if requirements[key] > 0
    )


def gate_lines(alternatives: list[dict[str, int]], indent: str) -> str:
    lines = [f"{indent}{GATE_BEGIN}"]
    if any(not any(requirement.values()) for requirement in alternatives):
        lines.append(f"{indent}# A programme without a resource threshold is available.")
    elif len(alternatives) == 1:
        for key in RESOURCE_KEYS:
            if alternatives[0][key] > 0:
                lines.append(f"{indent}{key} = {alternatives[0][key]}")
    else:
        lines.append(f"{indent}OR = {{")
        for requirement in alternatives:
            lines.append(f"{indent}\tAND = {{ {requirement_lines(requirement)} }}")
        lines.append(f"{indent}}}")
    lines.append(f"{indent}{GATE_END}")
    return "\n".join(lines)


def action_gate_lines(requirements: dict[str, int], indent: str) -> str:
    lines = [f"{indent}{ACTION_GATE_BEGIN}"]
    for key in RESOURCE_KEYS:
        if requirements[key] > 0:
            lines.append(f"{indent}{key} = {requirements[key]}")
    lines.append(f"{indent}{ACTION_GATE_END}")
    return "\n".join(lines)


def resource_only_logic(block: str) -> bool:
    without_comments = re.sub(r"(?m)#.*$", "", block)
    words = {word.lower() for word in re.findall(r"[A-Za-z_]+", without_comments)}
    return bool(words) and words <= {"and", "or", *RESOURCE_KEYS}


def strip_legacy_resource_gates(body: str) -> str:
    """Remove old maximum-price gates while preserving strategic conditions."""
    body = marker_pattern(GATE_BEGIN, GATE_END).sub("", body)
    wrapped = "root = {\n" + body + "\n}"
    removals: list[tuple[int, int]] = []

    for start, _opening, closing in top_blocks(wrapped, r"AND|OR"):
        line_end = closing + 1
        while line_end < len(wrapped) and wrapped[line_end] in " \t":
            line_end += 1
        if line_end < len(wrapped) and wrapped[line_end] == "\r":
            line_end += 1
        if line_end < len(wrapped) and wrapped[line_end] == "\n":
            line_end += 1
        if resource_only_logic(wrapped[start : closing + 1]):
            removals.append((start, line_end))

    depths = depth_map(wrapped)
    scalar = re.compile(
        r"(?mi)^([ \t]*)(money|supplies|manpower|oil)\s*=\s*\d+[ \t]*(?:#.*)?(?:\r?\n|$)"
    )
    for match in scalar.finditer(wrapped):
        if depths[match.start()] == 1:
            removals.append((match.start(), match.end()))

    for start, end in sorted(removals, reverse=True):
        wrapped = wrapped[:start] + wrapped[end:]
    return wrapped[wrapped.find("{") + 1 : wrapped.rfind("}")].strip("\r\n")


def update_action(action_text: str, requirements: dict[str, int]) -> tuple[str, bool]:
    if not any(requirements.values()):
        return action_text, False
    triggers = top_blocks(action_text, r"trigger")
    if triggers:
        _start, opening, closing = triggers[0]
        body = action_text[opening + 1 : closing]
        marker = marker_pattern(ACTION_GATE_BEGIN, ACTION_GATE_END)
        indent_match = re.search(r"(?m)^([ \t]*)\S", body)
        indent = indent_match.group(1) if indent_match else "\t\t\t"
        rendered = action_gate_lines(requirements, indent)
        if marker.search(body):
            new_body = marker.sub(rendered + "\n", body, count=1)
        else:
            new_body = "\n" + rendered + "\n" + body.lstrip("\r\n")
        updated = action_text[: opening + 1] + new_body + action_text[closing:]
        return updated, updated != action_text

    opening = action_text.find("{")
    insertion = "\n\t\ttrigger = {\n" + action_gate_lines(requirements, "\t\t\t") + "\n\t\t}\n"
    updated = action_text[: opening + 1] + insertion + action_text[opening + 1 :].lstrip("\r\n")
    return updated, updated != action_text


def compact_action_name(action_text: str, index: int) -> str:
    field = top_string_field(action_text, "name")
    label = field[2].strip() if field else f"Plan {chr(65 + index)}"
    label = re.split(r"\s*:\s*-?\d", label, maxsplit=1)[0]
    label = re.sub(r"\s+", " ", label).strip(" .")
    if len(label) > 56:
        label = label[:53].rstrip() + "..."
    return label or f"Plan {chr(65 + index)}"


def format_requirements(requirements: dict[str, int]) -> str:
    parts = [f"{key} {requirements[key]:,}" for key in RESOURCE_KEYS if requirements[key] > 0]
    return ", ".join(parts) if parts else "no minimum reserve"


def decision_ledger(actions: list[str], alternatives: list[dict[str, int]]) -> str:
    entries = [
        f"{compact_action_name(action, index)} [{format_requirements(requirements)}]"
        for index, (action, requirements) in enumerate(zip(actions, alternatives))
    ]
    result = "Cabinet funding estimates: " + "; ".join(entries) + "."
    if len(result.encode("cp1252")) <= 500:
        return result

    entries = [
        f"Plan {chr(65 + index)} [{format_requirements(requirements)}]"
        for index, requirements in enumerate(alternatives)
    ]
    result = "Funding estimates: " + "; ".join(entries) + "."
    if len(result.encode("cp1252")) > 500:
        raise ValueError("Generated decision_desc exceeds Darkest Hour's 511-byte limit")
    return result


def set_decision_desc(event_text: str, ledger: str) -> tuple[str, bool]:
    rendered = f'\tdecision_desc = "{ledger.replace(chr(34), chr(39))}"'
    existing = top_string_field(event_text, "decision_desc")
    if existing:
        start, end, _value = existing
        updated = event_text[:start] + rendered + event_text[end:]
        return updated, updated != event_text

    name_field = top_string_field(event_text, "name")
    if not name_field:
        raise ValueError("Decision event has no top-level name field")
    _start, end, _value = name_field
    updated = event_text[:end] + "\n" + rendered + event_text[end:]
    return updated, True


def update_event(event_text: str) -> tuple[str, bool]:
    decisions = top_blocks(event_text, r"decision")
    action_blocks = top_blocks(event_text, r"action(?:_[a-z]+)?")
    if not decisions or not action_blocks:
        return event_text, False

    actions = [event_text[start : closing + 1] for start, _opening, closing in action_blocks]
    alternatives = [action_requirements(action) for action in actions]
    if not any(any(requirement.values()) for requirement in alternatives):
        return event_text, False

    changed = False
    for (start, _opening, closing), requirements in reversed(list(zip(action_blocks, alternatives))):
        updated_action, action_changed = update_action(event_text[start : closing + 1], requirements)
        if action_changed:
            event_text = event_text[:start] + updated_action + event_text[closing + 1 :]
            changed = True

    decision_triggers = top_blocks(event_text, r"decision_trigger")
    if decision_triggers:
        _start, opening, closing = decision_triggers[0]
        body = event_text[opening + 1 : closing]
        cleaned = strip_legacy_resource_gates(body).rstrip()
        indent_match = re.search(r"(?m)^([ \t]*)\S", cleaned)
        indent = indent_match.group(1) if indent_match else "\t\t"
        new_body = "\n" + gate_lines(alternatives, indent)
        if cleaned.strip():
            new_body += "\n" + cleaned.strip()
        new_body += "\n\t"
        updated = event_text[: opening + 1] + new_body + event_text[closing:]
        changed = changed or updated != event_text
        event_text = updated
    else:
        decisions = top_blocks(event_text, r"decision")
        _decision_start, _decision_opening, decision_closing = decisions[0]
        insertion = "\n\tdecision_trigger = {\n" + gate_lines(alternatives, "\t\t") + "\n\t}\n"
        event_text = event_text[: decision_closing + 1] + insertion + event_text[decision_closing + 1 :]
        changed = True

    if MANUAL_DESC_MARKER in event_text:
        desc_changed = False
    else:
        event_text, desc_changed = set_decision_desc(event_text, decision_ledger(actions, alternatives))
    return event_text, changed or desc_changed


def update_file(path: Path) -> int:
    raw = path.read_text(encoding="cp1252")
    event_pattern = re.compile(r"(?mi)^event\s*=\s*\{")
    events: list[tuple[int, int]] = []
    for match in event_pattern.finditer(raw):
        opening = raw.find("{", match.start(), match.end())
        closing = matching_brace(raw, opening)
        events.append((match.start(), closing + 1))

    changed = 0
    updated = raw
    for start, end in reversed(events):
        new_event, did_change = update_event(updated[start:end])
        if did_change:
            updated = updated[:start] + new_event + updated[end:]
            changed += 1
    if updated != raw:
        path.write_text(updated, encoding="cp1252", newline="")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    event_root = args.root / "mod" / "db" / "events"
    files = sorted((event_root / "india_v3").glob("*.txt"))
    files += sorted((event_root / "aubm_v4").glob("*.txt"))
    changed = sum(update_file(path) for path in files)
    print(f"Transparent decision ledgers updated in {changed} event block(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
