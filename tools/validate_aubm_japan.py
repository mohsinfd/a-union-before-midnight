#!/usr/bin/env python3
"""Static safety checks for the AUBM Delhi-Tokyo partnership module."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_FILE = ROOT / "mod/db/events/aubm_v4/35_japan_partnership.txt"
WARTIME_STATE = ROOT / "mod/db/events/aubm_v4/41_wartime_state.txt"
AI_ROOT = ROOT / "mod/ai"
EVENTS_ROOT = ROOT / "mod/db/events"
EVENT_LIST = ROOT / "mod/db/events.txt"
PICTURE_ROOT = ROOT / "mod/gfx/events_pics"
PROVINCE_NAMES = ROOT / "mod/map/Map_1/province_names.csv"
ID_MIN = 9_281_100
ID_MAX = 9_281_199


def strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def balanced(text: str, label: str, errors: list[str]) -> None:
    clean = strip_comments(text)
    depth = 0
    quoted = False
    escaped = False
    for index, char in enumerate(clean):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                errors.append(f"{label}: closing brace before opening brace at offset {index}")
                return
    if quoted:
        errors.append(f"{label}: unterminated quoted string")
    if depth:
        errors.append(f"{label}: brace depth ends at {depth}, expected 0")


def event_blocks(text: str) -> list[str]:
    clean = strip_comments(text)
    blocks: list[str] = []
    for match in re.finditer(r"(?m)^\s*event\s*=\s*\{", clean):
        start = match.start()
        open_brace = clean.find("{", match.start())
        depth = 0
        quoted = False
        escaped = False
        for pos in range(open_brace, len(clean)):
            char = clean[pos]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(clean[start : pos + 1])
                    break
    return blocks


def province_ids() -> set[int]:
    ids: set[int] = set()
    for line in PROVINCE_NAMES.read_text(encoding="latin-1").splitlines():
        match = re.match(r"PROV(\d+);", line)
        if match:
            ids.add(int(match.group(1)))
    return ids


def all_event_ids() -> dict[int, list[Path]]:
    found: dict[int, list[Path]] = {}
    for path in EVENTS_ROOT.rglob("*.txt"):
        text = path.read_text(encoding="latin-1")
        for value in re.findall(r"(?m)^\s*id\s*=\s*(\d+)\s*$", strip_comments(text)):
            found.setdefault(int(value), []).append(path)
    return found


def used_provinces(text: str) -> set[int]:
    values = {
        int(value)
        for value in re.findall(r"\bprovince\s*=\s*(\d+)", strip_comments(text))
    }
    values.update(
        int(value)
        for value in re.findall(
            r"type\s*=\s*(?:control|secedeprovince)\b[^}\n]*\bvalue\s*=\s*(\d+)",
            strip_comments(text),
        )
    )
    return values


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not EVENT_FILE.exists():
        print(f"ERROR: missing {EVENT_FILE}")
        return 1

    text = EVENT_FILE.read_text(encoding="ascii")
    balanced(text, EVENT_FILE.name, errors)
    blocks = event_blocks(text)
    ids = [int(value) for value in re.findall(r"(?m)^\s*id\s*=\s*(\d+)\s*$", text)]

    if len(blocks) != len(ids):
        errors.append(f"event parser found {len(blocks)} blocks but {len(ids)} id lines")
    if len(ids) != len(set(ids)):
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        errors.append(f"duplicate module event IDs: {duplicates}")
    outside = [value for value in ids if not ID_MIN <= value <= ID_MAX]
    if outside:
        errors.append(f"event IDs outside reserved range: {outside}")

    blocks_by_id: dict[int, str] = {}
    for block in blocks:
        match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
        if match:
            blocks_by_id[int(match.group(1))] = block
    for required_id in (9281100, 9281101, 9281122, 9281191, 9281192):
        if required_id not in blocks_by_id:
            errors.append(f"required Tokyo retry-safety event {required_id} is missing")
    dispatcher = blocks_by_id.get(9281101, "")
    if not re.search(r"(?m)^\s*persistent\s*=\s*yes\s*$", dispatcher):
        errors.append("Tokyo assessment dispatcher 9281101 must remain persistent")
    conference = blocks_by_id.get(9281100, "")
    if "ind_aubm_jp_score_ledger_v2" not in conference:
        errors.append("Tokyo conference does not mark the corrected score ledger")
    for flag in (
        "ind_v3_china_backed_japan",
        "ind_v42_recognized_japanese_china_policy",
        "ind_v3_indian_led_imphal",
    ):
        if flag not in conference:
            errors.append(f"Tokyo score ledger omits earned influence flag {flag}")
    recovery = blocks_by_id.get(9281191, "")
    for token in (
        "event = 9281122",
        "ind_aubm_jp_proposal_pending",
        "ind_aubm_jp_score_ledger_v2",
        "ind_aubm_jp_retry_recovery_dispatched",
        "which = 9281192",
    ):
        if token not in recovery:
            errors.append(f"legacy Tokyo recovery 9281191 is missing {token!r}")

    # Darkest Hour's ordinary flag/setflag pair is global. Clausewitz-style
    # TAG = { flag = ... } scopes are unsupported and crash event parsing;
    # local country state would instead require local_flag/local_setflag.
    callback_contracts = {
        9281113: (
            "ind_aubm_jp_proposal_pending",
            "ind_aubm_jp_partnership",
            "ind_aubm_jp_tier_senior",
            "ind_aubm_jp_india_full_sphere",
        ),
        9281114: (
            "ind_aubm_jp_proposal_pending",
            "ind_aubm_jp_partnership",
            "ind_aubm_jp_tier_peer",
            "ind_aubm_jp_india_core_sphere",
        ),
        9281115: (
            "ind_aubm_jp_proposal_pending",
            "ind_aubm_jp_partnership",
            "ind_aubm_jp_tier_junior",
            "ind_aubm_jp_india_core_sphere",
        ),
    }
    for event_id, tokens in callback_contracts.items():
        block = blocks_by_id.get(event_id, "")
        for token in tokens:
            if token not in block:
                errors.append(f"Tokyo callback {event_id} does not preserve global flag {token}")
    china_policy = blocks_by_id.get(9281130, "")
    for guard in (
        "NOT = { alliance = { country = IND country = JAP } }",
        "NOT = { flag = ind_aubm_jp_formal_alliance }",
    ):
        if guard not in china_policy:
            errors.append(
                f"Tokyo China-policy event 9281130 is not compact-only; missing {guard!r}"
            )
    southern_opening = blocks_by_id.get(9281140, "")
    if "flag = ind_aubm_bespoke_route_contract_alpha23" not in southern_opening:
        errors.append("Tokyo southern theatre 9281140 cannot recognize an Alpha 23 Indian compact war")
    for opponent in ("ENG", "U05", "HOL", "AST"):
        if f"war = {{ country = IND country = {opponent} }}" not in southern_opening:
            errors.append(
                f"Tokyo southern theatre 9281140 omits India's separate {opponent} war"
            )
    if blocks_by_id.get(9281120, "").count("clrflag which = ind_aubm_jp_proposal_pending") < 3:
        errors.append("Tokyo counteroffer 9281120 does not close the Indian pending proposal in every outcome")
    if blocks_by_id.get(9281121, "").count("clrflag which = ind_aubm_jp_proposal_pending") < 3:
        errors.append("Tokyo rejection 9281121 does not close the Indian pending proposal in every outcome")
    unsupported_scope = re.compile(
        r"\b(?!(?:AND|NOT|TAG)\b)[A-Z0-9]{3}\s*=\s*\{\s*flag\s*="
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        if unsupported_scope.search(line):
            errors.append(
                f"line {line_number}: unsupported country-tag flag scope; ordinary flags are global"
            )
    tokyo_transfer = blocks_by_id.get(9281164, "")
    full_sphere_transfers = [
        line
        for line in tokyo_transfer.splitlines()
        if "ind_aubm_jp_india_full_sphere" in line and "secedeprovince" in line
    ]
    if len(full_sphere_transfers) < 50 or any(
        "trigger = { flag = ind_aubm_jp_india_full_sphere }" not in line
        for line in full_sphere_transfers
    ):
        errors.append("Tokyo settlement 9281164 does not guard its full-sphere transfers")
    for province in range(1688, 1718):
        if re.search(rf"secedeprovince\s+which\s*=\s*IND\s+value\s*=\s*{province}\b", tokyo_transfer):
            errors.append(
                f"Tokyo settlement 9281164 illegally transfers sovereign Australian province {province}"
            )
    implementation = blocks_by_id.get(9281165, "")
    for token in (
        "flag = ind_aubm_jp_australia_accept",
        "flag = ind_aubm_jp_britain_base_counter",
        "flag = ind_aubm_jp_dutch_oil_counter",
        "flag = ind_aubm_south_u05_counter",
    ):
        if token not in implementation:
            errors.append(f"Indian Ocean implementation 9281165 omits global reply {token!r}")
    resistance = blocks_by_id.get(9281169, "")
    for token in (
        "flag = ind_aubm_jp_britain_settlement_reject",
        "flag = ind_aubm_jp_dutch_settlement_reject",
        "flag = ind_aubm_south_u05_reject",
        "flag = ind_aubm_jp_australia_reject",
    ):
        if token not in resistance:
            errors.append(f"Indian Ocean resistance 9281169 omits global reply {token!r}")

    southern_settlement = blocks_by_id.get(9281160, "")
    settlement_text = {}
    for field in ("decision_desc", "desc"):
        match = re.search(rf'(?m)^\s*{field}\s*=\s*"([^"]*)"', southern_settlement)
        settlement_text[field] = match.group(1) if match else ""
    warning_tokens = (
        "separate peace",
        "ends formal shared-war membership",
        "separate-command compact",
    )
    for field, value in settlement_text.items():
        for token in warning_tokens:
            if token not in value:
                errors.append(
                    f"Indian Ocean settlement 9281160 {field} omits warning token {token!r}"
                )
    for token in (
        "type = setflag which = ind_aubm_jp_independent_cobelligerent",
        "type = clrflag which = ind_aubm_jp_formal_alliance",
        "type = leave_alliance when = 1",
    ):
        if southern_settlement.count(token) < 3:
            errors.append(
                f"Indian Ocean settlement 9281160 does not preserve its three-action transition {token!r}"
            )

    wartime_text = WARTIME_STATE.read_text(encoding="ascii")
    balanced(wartime_text, WARTIME_STATE.name, errors)
    wartime_blocks_by_id: dict[int, str] = {}
    for block in event_blocks(wartime_text):
        match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
        if match:
            wartime_blocks_by_id[int(match.group(1))] = block
    formal_upgrade = wartime_blocks_by_id.get(9281914, "")
    if not formal_upgrade:
        errors.append("Tokyo formal-entry event 9281914 is missing from wartime state")
    formal_join = formal_upgrade.split("\taction_b = {", 1)[0]
    senior_guard = (
        "trigger = { OR = { flag = ind_aubm_jp_tier_senior "
        "flag = ind_aubm_jp_india_full_sphere } }"
    )
    fresh_guard = (
        "trigger = { NOT = { flag = ind_aubm_jp_tier_senior } "
        "NOT = { flag = ind_aubm_jp_india_full_sphere } }"
    )
    for command in (
        "type = setflag which = ind_aubm_jp_tier_senior",
        "type = setflag which = ind_aubm_jp_india_full_sphere",
        "type = clrflag which = ind_aubm_jp_tier_peer",
        "type = clrflag which = ind_aubm_jp_india_core_sphere",
    ):
        if f"{senior_guard} {command}" not in formal_join:
            errors.append(
                f"Tokyo formal-entry event 9281914 does not preserve senior/full-sphere state via {command!r}"
            )
    for command in (
        "type = setflag which = ind_aubm_jp_tier_peer",
        "type = setflag which = ind_aubm_jp_india_core_sphere",
    ):
        if f"{fresh_guard} {command}" not in formal_join:
            errors.append(
                f"Tokyo formal-entry event 9281914 does not give fresh entry peer/core via {command!r}"
            )
    for flag in ("ind_aubm_jp_tier_senior", "ind_aubm_jp_india_full_sphere"):
        if f"command = {{ type = clrflag which = {flag} }}" in formal_join:
            errors.append(
                f"Tokyo formal-entry event 9281914 unconditionally downgrades existing {flag}"
            )

    global_ids = all_event_ids()
    duplicates = {
        value: paths
        for value, paths in global_ids.items()
        if value in ids and len({path.resolve() for path in paths}) > 1
    }
    for value, paths in sorted(duplicates.items()):
        errors.append(f"event ID {value} also appears in: {', '.join(str(p) for p in paths)}")

    if re.search(r"\btype\s*=\s*trigger\b", strip_comments(text)):
        errors.append("immediate force-trigger command found; use delayed type=event instead")
    if re.search(r"\btype\s*=\s*(?:construct|build_division|add_division|add_corps)\b", strip_comments(text)):
        errors.append("unit or construction command found in diplomacy-only module")
    if re.search(r"\btype\s*=\s*secedeprovince\b[^}\n]*\bwhen\s*=\s*2\b", strip_comments(text)):
        errors.append("unsafe secedeprovince when=2 found")

    for line_number, line in enumerate(text.splitlines(), start=1):
        action_name = re.match(r'^\t\tname\s*=\s*"([^"]+)"', line)
        if action_name:
            byte_length = len(action_name.group(1).encode("cp1252"))
            if byte_length > 58:
                errors.append(
                    f"line {line_number}: action label is {byte_length} CP1252 bytes; maximum is 58"
                )

    for block in blocks:
        id_match = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
        country_match = re.search(r"(?m)^\s*country\s*=\s*([A-Z0-9]{3})", block)
        event_id = int(id_match.group(1)) if id_match else -1
        country = country_match.group(1) if country_match else None
        if country:
            for target in re.findall(
                r"type\s*=\s*secedeprovince\s+which\s*=\s*([A-Z0-9]{3})", block
            ):
                if target == country:
                    errors.append(f"event {event_id}: unsafe self-secession by {country}")

    referenced = {
        int(value)
        for value in re.findall(r"\btype\s*=\s*event\s+which\s*=\s*(\d+)", text)
    }
    missing_refs = sorted(value for value in referenced if value not in global_ids)
    if missing_refs:
        errors.append(f"event commands reference undefined IDs: {missing_refs}")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\btype\s*=\s*event\b", line):
            delay = re.search(r"\bwhen\s*=\s*(\d+)", line)
            if not delay or int(delay.group(1)) < 1:
                errors.append(f"line {line_number}: targeted event command lacks positive delay")

    known_provinces = province_ids()
    invalid_provinces = sorted(used_provinces(text) - known_provinces)
    if invalid_provinces:
        errors.append(f"unknown map province IDs: {invalid_provinces}")

    required_revolt_sets = {
        "TIB": {1278, 1285, 1286, 1287, 1288, 1289, 1290, 1294, 1295},
        "MLY": {1432, 1433, 1434, 1435, 1436, 1437, 1438, 1624, 1625, 1626, 1629},
        "AST": set(range(1688, 1718)),
    }
    for tag, expected in required_revolt_sets.items():
        missing = sorted(expected - used_provinces(text))
        if missing:
            errors.append(f"{tag} verified revolt set is incomplete in module: {missing}")

    ai_refs = set(re.findall(r'type\s*=\s*ai\s+which\s*=\s*"([^"]+)"', text))
    for relative in sorted(ai_refs):
        path = AI_ROOT / relative
        if not path.exists():
            errors.append(f"missing AI switch file: {relative}")

    for path in sorted((AI_ROOT / "aubm/japan").glob("*.ai")):
        ai_text = path.read_text(encoding="ascii")
        balanced(ai_text, str(path.relative_to(ROOT)), errors)
        invalid = sorted(used_provinces(ai_text) - known_provinces)
        if invalid:
            errors.append(f"{path.name}: unknown province IDs {invalid}")

    pictures = set(re.findall(r'(?m)^\s*picture\s*=\s*"([^"]+)"', text))
    for picture in sorted(pictures):
        if not (PICTURE_ROOT / f"{picture}.bmp").exists():
            errors.append(f"missing event picture: {picture}.bmp")

    include_line = 'event = "db/events/aubm_v4/35_japan_partnership.txt"'
    event_list = EVENT_LIST.read_text(encoding="latin-1").replace("\\", "/")
    if include_line not in event_list:
        warnings.append(
            "module is not yet listed in mod/db/events.txt; integration is outside this task's write set"
        )

    print(f"Japan partnership events: {len(ids)} ({min(ids)}-{max(ids)})")
    print(f"AI switch files: {len(ai_refs)}")
    print(f"Verified map provinces referenced: {len(used_provinces(text))}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED with {len(errors)} error(s)")
        return 1
    print("PASS: event IDs, braces, references, pictures, AI files and transfer safety")
    return 0


if __name__ == "__main__":
    sys.exit(main())
