#!/usr/bin/env python3
"""Validate that player-facing diplomacy discloses its real response rules."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ensure_decision_visibility import matching_brace, top_blocks, top_string_field


ROOT = Path(__file__).resolve().parents[1]


# Each source is a player-facing choice. Its listed targets contain the actual
# foreign AI rolls that must be disclosed before the player commits.
SOURCE_TARGETS: dict[int, tuple[int, ...]] = {
    9270401: (9280950, 9280953),
    9270402: (9280956, 9280959, 9280962),
    9270403: (9280965,),
    9270410: (9270411, 9270414, 9270419, 9270424),
    9270417: (9270411,),
    9270418: (9270414,),
    9270420: (9270421,),
    9270430: (9270431,),
    9270435: (9270443, 9270436, 9270437),
    9270450: (9280900, 9280902),
    9270452: (9280922,),
    9270453: (9280932,),
    9281100: (9281110, 9281111, 9281112),
    9281130: (9281131,),
    9281135: (9281136,),
    9281160: (9281161, 9281162, 9281163),
    9281169: (9281161, 9281162, 9281163),
    9281180: (9281181,),
    9281200: (9281201, 9281202, 9281203, 9281204),
    9281240: (9281250, 9281251, 9281252, 9281253, 9281254, 9281255, 9281256, 9281257),
    9281242: (9281250, 9281251, 9281252, 9281253, 9281254, 9281255, 9281256, 9281257),
    9281300: (9281301, 9281302, 9281303),
    9281305: (9281313,),
    9281314: (9281320,),
    9281315: (9281321,),
    9281316: (9281322, 9281323, 9281324, 9281325, 9281326),
    9281359: (9281360, 9281361),
    9281372: (9281373, 9281374),
    9281400: (9281401, 9281408),
    9281403: (9281406,),
    9281410: (9281420,),
    9281411: (9281430,),
    9281412: (9281440, 9281441, 9281442),
    9281422: (9281424,),
    9281432: (9281434,),
    9281450: (9281451,),
    9281455: (9281456,),
    9281470: (9281471, 9281472, 9281473),
    9281479: (9281471,),
    9281483: (9281484, 9281485, 9281486),
    9281490: (9281484,),
    9281493: (9281484,),
    9281495: (9281486,),
    9281496: (9281486,),
    9281500: (9281502, 9281506, 9281510, 9281514, 9281520, 9281524, 9281528, 9281532),
    9281544: (9281545, 9281548),
    9282036: (9282037, 9282038, 9282039),
    9282170: (9282171, 9282172, 9282173, 9282174, 9282175),
    9282181: (9282184,),
    9282182: (9282185,),
    9282188: (9282186,),
    9282189: (9282187,),
    9282210: (9282220,),
    9282211: (9282221,),
    9282212: (9282222,),
    9282213: (9282223,),
    9282214: (9282224,),
    9282215: (9282225,),
    9282216: (9282226,),
    9282217: (9282227,),
    9282218: (9282228,),
    9282219: (9282229,),
}


DETERMINISTIC_DECISIONS = {
    9270404,
    9270405,
    9270406,
    9270407,
    9270408,
    9270409,
    9280500,
    9280510,
    9280968,
    9281133,
    9281134,
    9281140,
    9281217,
    9281220,
    9281221,
    9281222,
    9281311,
    9281541,
    9281542,
    9281543,
    9281561,
    9281562,
    9281563,
    9281564,
}


FACTOR_WORDS: dict[int, tuple[str, ...]] = {
    9281100: ("influence", "ic", "army", "navy", "air force", "+1", "+2", "-2"),
    9281135: ("influence 7", "ic 140", "army", "navy", "air"),
    9281240: ("hegemon", "senior", "regional", "participant", "decisive", "projection"),
}


def parse_events() -> dict[int, str]:
    events: dict[int, str] = {}
    for directory in (ROOT / "mod/db/events/india_v3", ROOT / "mod/db/events/aubm_v4"):
        for path in sorted(directory.glob("*.txt")):
            text = path.read_text(encoding="cp1252")
            position = 0
            while True:
                match = re.search(r"(?mi)^event\s*=\s*\{", text[position:])
                if not match:
                    break
                start = position + match.start()
                opening = text.find("{", start)
                closing = matching_brace(text, opening)
                block = text[start : closing + 1]
                position = closing + 1
                event_id = re.search(r"(?m)^\s*id\s*=\s*(\d+)", block)
                if event_id:
                    events[int(event_id.group(1))] = block
    return events


def visible_text(block: str) -> str:
    parts: list[str] = []
    for key in ("decision_desc", "desc"):
        value = top_string_field(block, key)
        if value:
            parts.append(value[2])
    for start, _opening, closing in top_blocks(block, r"action(?:_[a-z]+)?"):
        value = top_string_field(block[start : closing + 1], "name")
        if value:
            parts.append(value[2])
    return " ".join(parts).lower()


def response_odds(block: str) -> tuple[int, ...]:
    odds: list[int] = []
    for start, _opening, closing in top_blocks(block, r"action(?:_[a-z]+)?"):
        action = block[start : closing + 1]
        chance = re.search(r"\bai_chance\s*=\s*(\d+)", action)
        if chance:
            odds.append(int(chance.group(1)))
    return tuple(odds)


def odds_disclosed(text: str, odds: tuple[int, ...]) -> bool:
    slash = r"(?<!\d)" + r"\s*/\s*".join(str(value) for value in odds) + r"(?!\d)"
    if re.search(slash, text):
        return True

    # A binary event can safely state only the acceptance percentage because
    # the other result is its visible complement.
    if len(odds) == 2 and re.search(rf"(?<!\d){odds[0]}\s*%", text):
        return True

    percent_sequence = r".{0,120}?".join(rf"(?<!\d){value}\s*%" for value in odds)
    return re.search(percent_sequence, text) is not None


def main() -> int:
    events = parse_events()
    errors: list[str] = []
    checks = 0

    for source_id, target_ids in SOURCE_TARGETS.items():
        source = events.get(source_id)
        if not source:
            errors.append(f"missing player-facing source event {source_id}")
            continue
        text = visible_text(source)
        unique_vectors: set[tuple[int, ...]] = set()
        for target_id in target_ids:
            target = events.get(target_id)
            if not target:
                errors.append(f"event {source_id} references missing disclosure target {target_id}")
                continue
            odds = response_odds(target)
            checks += 1
            if len(odds) < 2 or sum(odds) != 100:
                errors.append(f"target event {target_id} has invalid response odds {odds}")
                continue
            unique_vectors.add(odds)
        for odds in sorted(unique_vectors):
            checks += 1
            if not odds_disclosed(text, odds):
                errors.append(f"event {source_id} does not disclose actual response odds {'/'.join(map(str, odds))}")

        if source_id not in FACTOR_WORDS:
            checks += 1
            if not re.search(r"\bfix(?:ed|es)\b", text):
                errors.append(f"event {source_id} does not explain that its response roll is fixed")

    deterministic_pattern = re.compile(r"\bno (?:new |immediate )?foreign roll\b|\bimmediate(?:ly)?\b|\bdeterministic\b")
    for event_id in sorted(DETERMINISTIC_DECISIONS):
        block = events.get(event_id)
        if not block:
            errors.append(f"missing deterministic decision {event_id}")
            continue
        checks += 1
        if not top_blocks(block, r"decision"):
            errors.append(f"event {event_id} is no longer a decision")
        if not deterministic_pattern.search(visible_text(block)):
            errors.append(f"decision {event_id} does not state that no foreign probability roll applies")

    for event_id, words in FACTOR_WORDS.items():
        block = events.get(event_id)
        if not block:
            errors.append(f"missing tiered diplomatic event {event_id}")
            continue
        text = visible_text(block)
        for word in words:
            checks += 1
            if word not in text:
                errors.append(f"event {event_id} omits chance factor {word!r}")

    for event_id, block in events.items():
        decision_desc = top_string_field(block, "decision_desc")
        if decision_desc:
            checks += 1
            length = len(decision_desc[2].encode("cp1252"))
            if length > 500:
                errors.append(f"event {event_id} decision_desc is {length} bytes; DH limit is 500")

    if errors:
        print(f"AUBM diplomatic-clarity validation failed ({len(errors)} errors):")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1

    print(f"AUBM diplomatic-clarity validation passed ({checks} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
