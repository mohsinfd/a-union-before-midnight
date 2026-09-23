#!/usr/bin/env python3
"""Audit and mechanically apply the scoped India reaction context correction.

No install/save writes. --patch emits an apply_patch patch; --check is read-only.
Existing event IDs, effect amounts and once-only outcome flags are preserved.
"""
from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import re

from dh_save_spans import Node, parse

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "aubm_v4/25_global_war.txt", "aubm_v4/28_foreign_responses.txt",
    "aubm_v4/29_world_pressure.txt", "aubm_v4/31_campaign_continuity.txt",
    "india_v3/46_world_reactions.txt", "india_v3/47_revisionist_aftermath.txt",
)
MARKER = "# AUBM_CONTEXT_GUARDS_V1"
KEEP = "Keep current orders; no new spending"
LAPSE = "The offer has lapsed; close the file"
FAMILIES = {
    "allied": ("ENG", "USA"), "german": ("GER", "ITA"),
    "soviet": ("SOV",), "japan": ("JAP",),
}


def peaceful(*tags: str) -> str:
    return " ".join(f"exists = {t} NOT = {{ war = {{ country = IND country = {t} }} }}" for t in tags)


def outside(*families: str) -> str:
    # Only live commitments and engine alliances count. Historical orientations
    # and route credit deliberately do not decide today's available choices.
    return " ".join(
        f"NOT = {{ flag = ind_aubm_commitment_{family} }} "
        + " ".join(f"NOT = {{ alliance = {{ country = IND country = {t} }} }}" for t in FAMILIES[family])
        for family in families
    )


def support(*tags: str, against: tuple[str, ...] = ()) -> str:
    return peaceful(*tags) + " " + outside(*against)


UNCOMMITTED = "NOT = { participant = { country = IND value = 4 } } " + outside(*FAMILIES)
NEUTRAL = "NOT = { atwar = IND } " + UNCOMMITTED
CHINA = support("CHI", against=("japan",))
JAPAN = support("JAP", against=("allied", "soviet"))
BRITAIN = support("ENG", against=("german", "japan"))
SOVIET = support("SOV", against=("german", "japan"))
GERMAN = support("GER", against=("allied", "soviet"))
PACIFIC = support("ENG", "USA", against=("japan", "german"))

# Existing action keys remain stable: no semantic guessing from prose labels.
ACTION_GUARDS: dict[int, dict[str, str]] = {
    9280350: {"action_a": CHINA, "action_b": NEUTRAL + " " + peaceful("JAP", "CHI"), "action_c": JAPAN},
    9280352: {"action_a": outside("japan"), "action_b": peaceful("SIA", "JAP"), "action_c": peaceful("SIA", "JAP") + " OR = { alliance = { country = JAP country = SIA } puppet = { country = SIA country = JAP } }"},
    9280353: {"action_a": CHINA, "action_b": NEUTRAL + " " + peaceful("JAP", "CHI"), "action_c": JAPAN},
    9280354: {"action_a": BRITAIN, "action_b": NEUTRAL + " " + peaceful("ENG", "GER", "ITA")},
    9280355: {"action_a": SOVIET, "action_b": NEUTRAL + " " + peaceful("GER", "SOV"), "action_c": GERMAN},
    9280356: {"action_b": NEUTRAL + " " + peaceful("JAP", "ENG"), "action_c": UNCOMMITTED + " " + peaceful("CHI", "SIA")},
    9280357: {"action_a": BRITAIN},
    9280700: {"action_a": BRITAIN + " " + peaceful("USA"), "action_b": GERMAN},
    9280701: {"action_a": BRITAIN, "action_b": NEUTRAL},
    9280702: {"action_a": BRITAIN, "action_b": peaceful("IRQ", "ENG")},
    9280703: {"action_a": SOVIET + " " + peaceful("PER"), "action_b": SOVIET + " " + peaceful("ENG"), "action_c": peaceful("PER")},
    9280704: {"action_a": PACIFIC, "action_b": NEUTRAL + " " + peaceful("JAP", "USA"), "action_c": UNCOMMITTED + " " + peaceful("CHI", "JAP")},
    9280705: {"action_a": BRITAIN, "action_b": peaceful("ENG")},
    9280706: {"action_b": "war = { country = IND country = JAP }"},
    9280709: {"action_a": PACIFIC, "action_b": CHINA, "action_c": UNCOMMITTED + " " + peaceful("CHI", "SIA")},
    9280710: {"action_a": peaceful("USA", "SOV"), "action_b": peaceful("CHI")},
    9280711: {"action_b": peaceful("USA") + " " + outside("japan"), "action_c": peaceful("CHI")},
    9280712: {"action_a": peaceful("CHI", "USA"), "action_b": peaceful("ENG", "USA"), "action_c": peaceful("CHI")},
    9280801: {"action_a": BRITAIN, "action_c": JAPAN},
    9280802: {"action_a": outside("japan"), "action_b": peaceful("SIA", "JAP"), "action_c": peaceful("SIA", "JAP")},
    9270450: {"action_a": "exists = ITA " + outside("german"), "action_b": NEUTRAL + " " + peaceful("ITA", "ETH"), "action_c": support("ITA", against=("allied", "soviet"))},
    9270451: {"action_a": support("SPR", against=("german",)), "action_b": peaceful("SPR", "SPA"), "action_c": support("SPA", "GER", "ITA", against=("allied", "soviet"))},
    9270452: {"action_a": CHINA, "action_b": NEUTRAL + " " + peaceful("CHI", "JAP"), "action_c": JAPAN},
    9270453: {"action_a": "exists = GER " + outside("german"), "action_b": GERMAN, "action_c": support("CZE", against=("german",))},
    9270454: {"action_a": support("CZE", against=("german",)), "action_c": peaceful("ENG", "FRA")},
    9270455: {"action_a": BRITAIN + " " + peaceful("FRA"), "action_b": NEUTRAL + " " + peaceful("ENG", "GER", "SOV"), "action_c": support("GER", "ITA", against=("allied", "soviet"))},
    9270456: {"action_b": NEUTRAL, "action_c": NEUTRAL + " " + peaceful("ENG", "GER", "SOV")},
    9272207: {"action_c": peaceful("USA", "SOV")},
    9280610: {"action_a": CHINA, "action_b": peaceful("JAP"), "action_c": peaceful("JAP")},
    9280611: {"action_a": JAPAN, "action_b": peaceful("CHI")},
}

# Recheck on receipt, including the Indian return leg. A scheduled foreign
# callback does not inherit the sender's old trigger state.
CALLBACK_GUARDS = {
    9280600: CHINA, 9280601: "exists = IND exists = JAP exists = CHI",
    9280602: JAPAN, 9280603: SOVIET, 9280604: GERMAN, 9280605: BRITAIN,
    9280606: BRITAIN, 9280607: GERMAN, 9280608: SOVIET, 9280609: JAPAN,
    9280612: BRITAIN, 9280613: GERMAN, 9280614: SOVIET, 9280615: JAPAN,
    9280616: CHINA + " " + UNCOMMITTED, 9280617: CHINA + " " + UNCOMMITTED,
    9280618: peaceful("SIA") + " " + UNCOMMITTED, 9280619: peaceful("SIA") + " " + UNCOMMITTED,
    9280620: BRITAIN, 9280621: peaceful("IRQ", "ENG"),
    9280622: SOVIET + " " + peaceful("PER"), 9280623: PACIFIC,
    9280624: BRITAIN, 9280625: peaceful("IRQ", "ENG"),
    9280626: SOVIET + " " + peaceful("PER"), 9280627: PACIFIC,
    9280640: peaceful("USA"), 9280641: CHINA, 9280642: peaceful("USA"),
    9280643: peaceful("USA"), 9280644: CHINA, 9280645: peaceful("USA"),
}
for _base, _tag in ((9280630, "ENG"), (9280631, "GER"), (9280632, "SOV"), (9280633, "JAP")):
    CALLBACK_GUARDS[_base] = CALLBACK_GUARDS[_base + 4] = peaceful(_tag) + f" alliance = {{ country = IND country = {_tag} }}"

EVENT_GUARDS = {
    9280358: UNCOMMITTED,
    9280707: "owned = { province = 1415 data = IND } control = { province = 1415 data = -2 }",
    9280712: "NOT = { war = { country = IND country = JAP } }",
    9280801: "NOT = { flag = ind_aubm_wartime_framework }",
    9280802: "NOT = { flag = ind_aubm_wartime_framework }",
    9272207: "NOT = { flag = ind_aubm_wartime_framework }",
}

TEXT = {
    9280352: ("Japan and the Siamese Frontier", "Japan and Siam now shape the security of India's eastern frontier, whether through partnership or open war. Delhi can strengthen its defences or seek talks with governments it is not fighting."),
    9280353: (None, "China has lost much of its territory but continues the war with Japan. Delhi can fund Chinese supply routes, trade with Japan, or stay out of their conflict if India remains at peace. Existing Indian wars and alliances continue."),
    9280354: ("War Disrupts Indian Ocean Shipping", "The European war has raised shipping costs and stretched the patrols protecting Indian Ocean trade. Delhi can help a friendly Britain, trade across the divide while neutral, or reserve its shipping for Indian needs."),
    9280355: ("Germany and the Soviet Union Are at War", "The war between Germany and the Soviet Union changes India's trade and supply routes. Delhi can support a government it is not fighting, offer neutral mediation while at peace, or keep its present policy."),
    9280356: ("Japan and India's Eastern Defence", "Japan's wars and its ties with Siam put India's eastern ports and borders at risk. Delhi can strengthen the armed forces or pursue talks where relations allow. These choices do not declare war, end a war or change India's alliance."),
    9280357: ("Defending Burma and Malaya", "The Japanese war puts Burma and Malaya under pressure. India can share warnings with a friendly Britain, keep its own mobile reserve, or support the people behind the frontier. Indian forces remain under Delhi's command."),
    9280704: (None, "Japan and the United States are now at war. India must review the danger to its shipping and eastern approaches. Cooperation is available with governments India is not fighting. Armed neutrality is available only while India is at peace and uncommitted; an existing Indian war continues."),
    9280705: ("Japan Holds Singapore", "Japan controls Singapore. Indian Burma faces greater pressure, and people displaced from Malaya may seek refuge. Delhi can prepare to receive help from a friendly Britain or concentrate on its own border."),
    9280706: ("Prepare for Japanese Naval Raids", "The war between Japan and Britain puts Indian Ocean shipping at risk. The naval staff recommends dispersal, repairs and convoy protection. This is a defence plan, not a report that a raid has occurred. India may prepare for battle with Japan only if the two countries are at war."),
    9280707: (None, "An enemy occupies Indian-owned Rangoon. Delhi can strengthen the Imphal line, prepare a return to Burma, or conserve the army. These are Indian preparations; the player still commands every move on the map."),
    9280708: ("Plan the Imphal Front", "India holds Imphal while fighting Japan. The army can prepare a return to Burma, strengthen the position or preserve its reserve. These choices fund preparations; they do not mean a battle has taken place or move troops automatically."),
    9280709: (None, "Germany has lost ground while fighting the United States. Delhi can support friendly maritime powers, prepare its forces for Asia or discuss a future settlement with countries it is not fighting."),
    9280710: ("Berlin Falls", "Berlin is occupied or the German government has collapsed. This is a major change in the war, but fighting elsewhere may continue. Delhi must decide which diplomatic claims to press; this discussion ends no war."),
    9280711: ("The Cost of the War in Japan", "Japan has suffered heavy territorial losses or an atomic attack. India must consider limits on attacks against cities, its own research and the need for a negotiated end. These positions do not impose surrender or end an existing war."),
    9280712: ("India Reviews Japan's Defeat", "Tokyo has fallen or Japan has ceased to exist, and India is no longer fighting Japan. Other Indian wars may continue. Delhi must decide what to seek for Asia; this discussion changes no borders or alliances."),
    9272206: ("Review the Emergency Government", "Earlier German or Japanese war plans strengthened India's emergency government. Delhi can place those powers under constitutional limits, maintain them, or restore the Gandhi-Nehru cabinet. This domestic review does not renew an old alliance or change India's current wars."),
    9272207: (None, "India is at peace and still allied with Germany. Delhi can press for Asian independence, fund Indian Ocean logistics or improve relations with other powers. These policies do not transfer territory or end the alliance."),
}
ACTION_TEXT = {
    (9280354, "action_a"): "Escort friendly commerce: -500 supplies, +300 money",
    (9280356, "action_b"): "Discuss neutrality: -250 money; no treaty or war change",
    (9280356, "action_c"): "Invite Asian governments to talks: -300 money",
    (9280703, "action_c"): "Support Persian neutrality; no guarantee treaty",
    (9280704, "action_b"): "Keep armed neutrality: -500 supplies",
    (9280704, "action_c"): "Invite China to peace talks: -200 money; no armistice",
    (9280706, "action_b"): "Fight under air cover: -250 money, -700 supplies",
    (9280706, "action_c"): "Protect convoy routes: -350 supplies",
    (9280708, "action_a"): "Prepare a return to Burma: -400 money, -1400 supplies",
    (9280708, "action_b"): "Strengthen the defence: -800 supplies",
    (9280709, "action_a"): "Support the Allies: -350 money, -1000 supplies",
    (9280709, "action_b"): "Prepare for Asian operations: -600 supplies",
    (9280711, "action_a"): "Call for limits on attacks against cities",
    (9280711, "action_b"): "Press for surrender and fund research: -400 money",
    (9280711, "action_c"): "Fund Asian relief: -500 supplies",
    (9280610, "action_a"): "Continue Chinese aid: +1 dissent",
    (9280610, "action_b"): "Restrict military cargo: +250 money, China -20",
    (9280611, "action_a"): "Continue permitted trade: +250 money, +2 dissent",
    (9270454, "action_b"): "Fund Indian rearmament: -800 supplies",
    (9272206, "action_a"): "Limit emergency powers: -375 money, -3 dissent",
    (9272206, "action_b"): "Keep emergency production: -900 supplies, +4 dissent",
    (9272207, "action_a"): "Press for Asian independence: -4 dissent",
    (9272207, "action_b"): "Fund ocean logistics: -800 money, -1200 supplies",
    (9272207, "action_c"): "Improve foreign relations: -2 dissent",
}
REACTIONS = set(range(9280350, 9280360)) | set(range(9280700, 9280713)) | {9280801, 9280802, 9272206, 9272207} | set(range(9270450, 9270457)) | {9280610, 9280611}

CALLBACK_TEXT = {}
for _ids, _title, _description in (
    ((9280600,), "The Indian Shipment for China", "India has promised lorries, medical stores and machine tools for the Burma Road. China can receive the shipment while the two governments remain at peace and India has no Japanese commitment."),
    ((9280601,), "Japan Objects to Indian Aid", "Tokyo condemns India's support for China. Japan's warning does not decide Indian policy or change the wars already being fought. Delhi will consider its response."),
    ((9280602,), "Japan's Indian Supply Contracts", "Japanese buyers are ready to receive Indian goods. The contracts can proceed only while India and Japan are at peace and India's commitments allow this trade."),
    ((9280603,), "The Indian Shipment for Moscow", "India has promised machinery and medicine for the Soviet war. Moscow can receive them while it remains at peace with India and Delhi has no opposing German or Japanese commitment."),
    ((9280604,), "Germany's Indian Trade Channel", "German buyers seek delivery through intermediaries. The trade can continue only while Germany and India are at peace and India's current commitments permit it."),
    ((9280605,), "Indian Ocean Patrol Cooperation", "Britain has asked to use Indian patrol reports and convoy information. Cooperation requires peace with India and leaves Indian ships under Indian command."),
    ((9280606, 9280612), "London's Reply on Indian Command", "London offers equipment and liaison officers on terms that leave Indian forces under Delhi's command. The offer can proceed while Britain and India remain at peace and India's present commitments allow cooperation."),
    ((9280607, 9280613), "Berlin's Technical Mission", "Berlin offers doctrine manuals, optical equipment and industrial samples. A mission can proceed while Germany and India remain at peace and India's present commitments allow it. No alliance is created."),
    ((9280608, 9280614), "Moscow's Technical Mission", "Moscow offers engineers and staff instructors under Indian authority. A mission can proceed while the Soviet Union and India remain at peace and India's present commitments allow it. No alliance is created."),
    ((9280609, 9280615), "Tokyo's Reply on Naval Cooperation", "Tokyo offers naval instructors under Indian command. Delivery requires peace between the two countries and compatible Indian commitments. The offer settles neither China nor India's future wars."),
    ((9280616, 9280617), "China and the Delhi Conference", "China is willing to discuss supply routes and Asian security with an uncommitted India. Talks require peace between the two governments and create no alliance."),
    ((9280618, 9280619), "Siam and the Delhi Conference", "Siam is willing to discuss frontier communication with an uncommitted India. Talks require peace between the two governments and do not change Siam's existing alliances."),
    ((9280620, 9280624), "Britain's Reply to Indian Aid", "Britain is ready to acknowledge the supplies India offered after France's defeat. The aid can proceed while Britain and India remain at peace and India's commitments allow cooperation."),
    ((9280621, 9280625), "Iraq's Reply to Indian Mediation", "Baghdad is willing to discuss sovereignty and transport with India. Mediation requires India to remain at peace with both Iraq and Britain. These talks do not themselves end the Iraqi war."),
    ((9280622, 9280626), "Persia's Reply on the Supply Corridor", "Tehran offers to keep Persian officials in charge of a supply route toward the Soviet Union. India can proceed while at peace with Persia and Moscow and free of an opposing German or Japanese commitment."),
    ((9280623, 9280627), "Washington's Reply on Pacific Cooperation", "Washington offers equipment and shared convoy information while leaving Indian forces under Delhi's command. The offer requires peace with both America and Britain and compatible Indian commitments."),
    ((9280630, 9280634), "The British Alliance Shipment", "Britain has offered equipment for India's entry into the Allied coalition. The shipment is available only if India still shares Britain's alliance when the reply is received."),
    ((9280631, 9280635), "The German Alliance Shipment", "Germany has offered equipment for joint war plans. The shipment is available only if India still shares Germany's alliance when the reply is received."),
    ((9280632, 9280636), "The Soviet Alliance Shipment", "Moscow has offered equipment and liaison officers for the coalition. The shipment is available only if India still shares the Soviet alliance when the reply is received."),
    ((9280633, 9280637), "The Japanese Alliance Shipment", "Tokyo has offered equipment for the alliance with India. The shipment is available only if the two countries still share an alliance when the reply is received. Their alliance joins wars under the game's normal rules."),
    ((9280640, 9280643), "Washington and India's Place at the Peace", "Washington is willing to discuss India's claim to a leading place in the postwar settlement. Recognition requires peaceful relations between the two governments and creates no alliance."),
    ((9280641, 9280644), "China and the Independence Charter", "China is willing to support fixed timetables for Asian independence if the charter also opposes Japanese conquest. Endorsement requires peace with India and no Indian commitment to Japan."),
    ((9280642, 9280645), "Washington and the Indian Ocean Conference", "Washington is willing to discuss rescue services, convoy standards and agreed access to Indian Ocean bases. Talks require peace with India and give no foreign power command over Indian forces."),
):
    for _eid in _ids:
        CALLBACK_TEXT[_eid] = (_title, _description)


def actions(event: Node):
    return [(f.key, f.value) for f in event.fields if f.key and re.fullmatch(r"action(?:_[a-d])?", f.key)]


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def cost_guard(action: Node) -> str:
    costs: dict[str, float] = {}
    for command in action.all("command"):
        kind = command.get("type")
        if kind in ("money", "supplies", "manpowerpool") and command.get("trigger") is None:
            value = float(command.get("value", 0))
            if value < 0:
                key = "manpower" if kind == "manpowerpool" else kind
                costs[key] = costs.get(key, 0) - value
    return " ".join(f"{k} = {v:g}" for k, v in costs.items())


def repair_presentation(text: str) -> str:
    """Upgrade already-guarded output without adding a second guard/fallback.

    Ordinary reaction weights retain their original 100-point distribution;
    their player-safe fallback carries zero extra AI weight. Callback primary
    and lapse actions are mutually exclusive and each carries weight 100.
    """
    edits = []
    for event in parse(text).all("event"):
        eid = int(event.get("id"))
        event_actions = actions(event)
        if eid in CALLBACK_GUARDS:
            primary = [a for _, a in event_actions if a.get("name") != LAPSE]
            assert len(primary) == 1, f"{eid}: callback distribution needs explicit review"
        for key, action in event_actions:
            wanted = None
            if eid in REACTIONS and action.get("name") == KEEP:
                wanted = "0"
            elif eid in CALLBACK_GUARDS:
                wanted = "100"
            if wanted is not None and action.get("ai_chance") != wanted:
                old = action.get("ai_chance")
                if old is None:
                    edits.append((action.start + 1, action.start + 1, "\n\t\tai_chance = " + wanted))
                else:
                    field = action.field("ai_chance")
                    edits.append((field.value_start, field.end, wanted))
            label = ACTION_TEXT.get((eid, key))
            if label is not None and action.get("name") != label:
                field = action.field("name")
                edits.append((field.value_start, field.end, '"' + label + '"'))
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    return text


def transformed(text: str, filename: str) -> str:
    if MARKER in text:
        return repair_presentation(text)
    edits: list[tuple[int, int, str]] = []
    for event in parse(text).all("event"):
        eid = int(event.get("id"))
        event_actions = actions(event)

        def add_guard(node: Node, guard: str):
            if not guard.strip():
                return
            old = node.get("trigger")
            if isinstance(old, Node):
                edits.append((old.start + 1, old.start + 1, " " + guard + " "))
            else:
                edits.append((node.start + 1, node.start + 1, "\n\t\ttrigger = { " + guard + " }"))

        def scalar(node: Node, key: str, value: str):
            field = node.field(key)
            edits.append((field.value_start, field.end, '"' + value + '"'))

        if eid in EVENT_GUARDS:
            add_guard(event, EVENT_GUARDS[eid])
        if eid in TEXT:
            title, description = TEXT[eid]
            if title:
                scalar(event, "name", title)
            scalar(event, "desc", description)
        if eid in {9280356, 9280357, 9280704, 9280705, 9280706}:
            # Replace historical orientation gates with the current commitment.
            old = event.get("trigger")
            segment = text[old.start:old.end]
            for legacy in ("ind_aubm_jp_partnership", "ind_aubm_route_japan"):
                match = re.search(r"\s*NOT\s*=\s*\{\s*flag\s*=\s*" + legacy + r"\s*\}", segment)
                if match:
                    edits.append((old.start + match.start(), old.start + match.end(), ""))
            add_guard(event, "NOT = { flag = ind_aubm_commitment_japan }")
        callback = CALLBACK_GUARDS.get(eid)
        if callback:
            title, description = CALLBACK_TEXT[eid]
            scalar(event, "name", title)
            scalar(event, "desc", description)
        for key, action in event_actions:
            guards = [ACTION_GUARDS.get(eid, {}).get(key, ""), callback or ""]
            if eid in REACTIONS:
                guards.append(cost_guard(action))
            add_guard(action, " ".join(guards))
            if (eid, key) in ACTION_TEXT:
                scalar(action, "name", ACTION_TEXT[eid, key])
        if callback:
            fallback = f'\n\taction = {{\n\t\ttrigger = {{ NOT = {{ AND = {{ {callback} }} }} }}\n\t\tai_chance = 100\n\t\tname = "{LAPSE}"\n\t}}\n'
            edits.append((event.end - 1, event.end - 1, fallback))
        elif eid in REACTIONS:
            flags = [set(c.get("which") for c in a.all("command") if c.get("type") == "setflag") for _, a in event_actions]
            common = set.intersection(*flags) if flags else set()
            # Resolution records only: no extra reward and no route selection.
            common -= {"ind_v3_axis_settlement_1945"}
            commands = "".join(f"\t\tcommand = {{ type = setflag which = {flag} }}\n" for flag in sorted(common))
            fallback = f'\n\taction = {{\n\t\tai_chance = 0\n\t\tname = "{KEEP}"\n{commands}\t}}\n'
            edits.append((event.end - 1, event.end - 1, fallback))
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    parse(text)
    return repair_presentation(MARKER + "\n" + text)


def validate(text: str, filename: str) -> int:
    assert MARKER in text, f"{filename}: context correction missing"
    count = 0
    for event in parse(text).all("event"):
        eid = int(event.get("id")); aa = actions(event)
        for key, action in aa:
            assert len(action.get("name").encode("cp1252")) <= 58, f"{eid} {key}: action label too long"
        if eid in EVENT_GUARDS:
            trigger = event.get("trigger")
            assert isinstance(trigger, Node) and compact(EVENT_GUARDS[eid]) in compact(text[trigger.start:trigger.end]), f"{eid}: event context guard missing"
        if eid in TEXT:
            title, description = TEXT[eid]
            assert event.get("desc") == description and (title is None or event.get("name") == title), f"{eid}: context wording drifted"
        for key, action in aa:
            if action.get("name") in (KEEP, LAPSE):
                continue
            expected = [ACTION_GUARDS.get(eid, {}).get(key, ""), CALLBACK_GUARDS.get(eid, "")]
            if eid in REACTIONS:
                expected.append(cost_guard(action))
            trigger = action.get("trigger")
            actual = compact(text[trigger.start:trigger.end]) if isinstance(trigger, Node) else ""
            for guard in expected:
                assert compact(guard) in actual, f"{eid} {key}: context or affordability guard missing"
        if eid in REACTIONS:
            safe = [a for _, a in aa if a.get("name") == KEEP]
            assert len(safe) == 1 and safe[0].get("trigger") is None, f"{eid}: unconditional safe choice required"
            assert safe[0].get("ai_chance") == "0", f"{eid}: safe choice changes original AI distribution"
            assert sum(int(a.get("ai_chance")) for _, a in aa) == 100, f"{eid}: reaction AI distribution must sum to 100"
            assert all(c.get("type") == "setflag" for c in safe[0].all("command")), f"{eid}: safe choice has effects beyond the record"
            count += 1
        if eid in CALLBACK_GUARDS:
            safe = [a for _, a in aa if a.get("name") == LAPSE]
            assert len(safe) == 1 and not safe[0].all("command"), f"{eid}: effect-free lapse required"
            assert len(aa) == 2 and all(a.get("ai_chance") == "100" for _, a in aa), f"{eid}: complementary callback choices require explicit full weights"
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--patch", action="store_true")
    mode.add_argument("--write", action="store_true", help="apply the mechanical correction to the six repository source modules only")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()
    total = 0; patches = []
    for filename in FILES:
        path = ROOT / "mod/db/events" / filename
        original = path.read_bytes().decode("cp1252").replace("\r\n", "\n")
        updated = transformed(original, filename)
        if args.patch and updated != original:
            diff = list(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), n=3))
            hunks = re.sub(r"(?m)^@@[^\n]*@@[^\n]*$", "@@", "".join(diff[2:]))
            patches.append("*** Update File: " + path.as_posix() + "\n" + hunks)
        elif args.write:
            if updated != original:
                path.write_bytes(updated.replace("\n", "\r\n").encode("cp1252"))
            total += validate(updated, filename)
        else:
            assert updated == original, f"{filename}: unapplied correction"
            total += validate(original, filename)
    if args.patch:
        if patches:
            print("*** Begin Patch\n" + "".join(patches) + "*** End Patch")
    else:
        print(f"OK: {total} reaction/reply events have current-context guards and a safe exit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
