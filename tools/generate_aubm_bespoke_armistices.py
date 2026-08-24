#!/usr/bin/env python3
"""Generate negotiated armistices for AUBM's eight bespoke regional wars."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "mod/db/events/aubm_v4/49_bespoke_armistices.txt"


@dataclass(frozen=True)
class Target:
    tag: str
    key: str
    name: str
    capital: int
    seat: str
    picture: str


TARGETS = (
    Target("PER", "per", "Persia", 1085, "Tehran", "aubm_v4_indian_ocean_war"),
    Target("IRQ", "irq", "Iraq", 1034, "Baghdad", "aubm_v4_indian_ocean_war"),
    Target("SAU", "sau", "Saudi Arabia", 1045, "Riyadh", "aubm_v4_indian_ocean_war"),
    Target("YEM", "yem", "Yemen", 1050, "Sana'a", "aubm_v4_indian_ocean_war"),
    Target("OMN", "omn", "Oman", 1052, "Muscat", "aubm_v4_indian_ocean_war"),
    Target("AFG", "afg", "Afghanistan", 2171, "Kabul", "aubm_v4_barbarossa_reaction"),
    Target("TIB", "tib", "Tibet", 1289, "Lhasa", "aubm_v4_grand_strategy"),
    Target("SIK", "sik", "Xinjiang", 1281, "Urumqi", "aubm_v4_grand_strategy"),
)


def header(event_id: int, country: str, *, one_action: bool = False) -> list[str]:
    out = ["event = {", f"\tid = {event_id}", "\trandom = no", "\tpersistent = yes"]
    if one_action:
        out.append("\tone_action = yes")
    out.append(f"\tcountry = {country}")
    return out


def command(body: str, *, trigger: str | None = None) -> str:
    if trigger:
        return f"\t\tcommand = {{ trigger = {{ {trigger} }} type = {body} }}"
    return f"\t\tcommand = {{ type = {body} }}"


def target_flag(target: Target) -> str:
    return f"ind_aubm_bespoke_target_{target.key}"


def retry_flag(target: Target) -> str:
    return f"ind_aubm_bespoke_retry_{target.key}"


def clear_campaign(target: Target) -> list[str]:
    return [
        command(f"setflag which = ind_aubm_regional_settled_{target.key}"),
        command(f"clrflag which = ind_aubm_regional_pending_{target.key}"),
        command(f"clrflag which = ind_aubm_regional_current_{target.key}"),
        command(f"clrflag which = ind_aubm_regional_victory_{target.key}"),
        command(f"clrflag which = ind_aubm_regional_suspended_{target.key}"),
    ]


def post_annex_commands(target: Target, outcome: str) -> list[str]:
    out = [command("setflag which = ind_aubm_global_campaign_victory")]
    if outcome == "sovereign":
        out.extend(
            [
                command(f"independence which = {target.tag} value = 1 when = 0"),
                command(f"guarantee which = IND where = {target.tag}", trigger=f"exists = {target.tag}"),
                command("dissent value = -1"),
            ]
        )
    elif outcome == "protected":
        out.extend(
            [
                command(f"independence which = {target.tag} value = 1 when = 0"),
                command(f"make_puppet which = {target.tag}", trigger=f"exists = {target.tag}"),
            ]
        )
        if target.tag == "TIB":
            out.append(command("dissent value = 4", trigger="NOT = { flag = ind_aubm_jp_tibet_clause }"))
            out.append(command("dissent value = -1", trigger="flag = ind_aubm_jp_tibet_clause"))
        else:
            out.append(command("dissent value = 4"))
    else:
        out.extend(
            [
                command("dissent value = 7"),
                command("belligerence value = 5"),
                command(f"province_revoltrisk which = {target.capital} value = 3"),
                command("setflag which = ind_aubm_occupation_upkeep"),
                command("event which = 9282093 where = IND when = 1"),
            ]
        )
    out.append(command(f"setflag which = ind_aubm_bespoke_{outcome}_{target.key}"))
    out.extend(clear_campaign(target))
    return out


def proposal_event(index: int, target: Target) -> str:
    event_id = 9282270 + index
    protection_label = (
        "Protect Tibet: +4 dissent; earned Tokyo clause waives"
        if target.tag == "TIB"
        else f"Protect {target.name}: +4 dissent"
    )
    live = (
        f"exists = {target.tag} war = {{ country = IND country = {target.tag} }} "
        f"owned = {{ province = {target.capital} data = {target.tag} }} "
        f"control = {{ province = {target.capital} data = IND }} "
        f"flag = ind_aubm_regional_current_{target.key} "
        f"NOT = {{ flag = ind_aubm_regional_settled_{target.key} }} "
        "NOT = { flag = ind_aubm_bespoke_armistice_outstanding } "
        f"NOT = {{ flag = {retry_flag(target)} }}"
    )
    annexed = (
        f"NOT = {{ exists = {target.tag} }} "
        f"owned = {{ province = {target.capital} data = IND }} "
        f"control = {{ province = {target.capital} data = IND }} "
        f"NOT = {{ flag = ind_aubm_regional_settled_{target.key} }}"
    )
    out = header(event_id, "IND")
    out.extend(
        [
            f'\tname = "The {target.name} Settlement Docket"',
            f'\tdesc = "India holds the published objective at {target.seat}. While {target.name} exists, Delhi may submit a 60/25/15 armistice and receive a real foreign answer. After annexation, India may restore sovereignty, establish protection, or accept the dissent and occupation burden of direct rule."',
            "\tstyle = 2",
            f'\tpicture = "{target.picture}"',
            "\taction_a = {",
            f"\t\ttrigger = {{ {live} }}",
            '\t\tname = "Submit an armistice: 60/25/15"',
            command(f"setflag which = {target_flag(target)}"),
            command("setflag which = ind_aubm_bespoke_armistice_outstanding"),
            command("setflag which = ind_aubm_global_campaign_victory"),
            command(f"event which = {9282280 + index} where = {target.tag} when = 2"),
            "\t}",
            "\taction_b = {",
            f"\t\ttrigger = {{ {annexed} }}",
            f'\t\tname = "Restore sovereign {target.name}"',
        ]
    )
    out.extend(post_annex_commands(target, "sovereign"))
    out.extend(
        [
            "\t}",
            "\taction_c = {",
            f"\t\ttrigger = {{ {annexed} }}",
            f'\t\tname = "{protection_label}"',
        ]
    )
    out.extend(post_annex_commands(target, "protected"))
    out.extend(
        [
            "\t}",
            "\taction_d = {",
            f"\t\ttrigger = {{ {annexed} }}",
            '\t\tname = "Direct administration: +7 dissent and occupation"',
        ]
    )
    out.extend(post_annex_commands(target, "direct"))
    out.extend(["\t}", "}"])
    return "\n".join(out)


def gulf_board() -> str:
    out = header(9282278, "IND")
    out.extend(
        [
            '\tname = "The Gulf Settlement Board"',
            '\tdesc = "Iraq, Saudi Arabia, Yemen and Oman are separate sovereign files. Settling one never hides or settles the others, and each government receives its own response roll."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_indian_ocean_war"',
        ]
    )
    for letter, index, label in zip("abcd", (1, 2, 3, 4), ("Iraq", "Saudi Arabia", "Yemen", "Oman")):
        out.extend(
            [
                f"\taction_{letter} = {{",
                f'\t\tname = "Open the {label} file"',
                command(f"event which = {9282270 + index} where = IND when = 1"),
                "\t}",
            ]
        )
    out.append("}")
    return "\n".join(out)


def lapse_event() -> str:
    clauses = " ".join(
        f"AND = {{ flag = {target_flag(t)} NOT = {{ exists = {t.tag} }} }}" for t in TARGETS
    )
    out = header(9282279, "IND", one_action=True)
    out.extend(
        [
            f"\ttrigger = {{ flag = ind_aubm_bespoke_armistice_outstanding OR = {{ {clauses} }} }}",
            '\tname = "A Regional Government Falls during Negotiation"',
            '\tdesc = "The government considering Delhi\'s armistice has ceased to exist. The dead response lock is removed and, where India legally owns the capital, the constitutional settlement docket reopens."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_liberated_territory"',
            "\tdate = { day = 0 month = january year = 1933 }",
            "\toffset = 1",
            "\tdeathdate = { day = 29 month = december year = 1964 }",
            "\taction_a = {",
            '\t\tname = "Close the vanished response and reopen settlement"',
        ]
    )
    for index, target in enumerate(TARGETS):
        condition = (
            f"flag = {target_flag(target)} NOT = {{ exists = {target.tag} }} "
            f"owned = {{ province = {target.capital} data = IND }}"
        )
        out.append(command(f"event which = {9282270 + index} where = IND when = 1", trigger=condition))
    for target in TARGETS:
        out.append(command(f"clrflag which = {target_flag(target)}", trigger=f"NOT = {{ exists = {target.tag} }}"))
    out.extend([command("clrflag which = ind_aubm_bespoke_armistice_outstanding"), "\t}", "}"])
    return "\n".join(out)


def response_event(index: int, target: Target) -> str:
    live = (
        f"war = {{ country = IND country = {target.tag} }} "
        f"owned = {{ province = {target.capital} data = {target.tag} }} "
        f"control = {{ province = {target.capital} data = IND }}"
    )
    out = header(9282280 + index, target.tag)
    out.extend(
        [
            f'\tname = "{target.name} Answers the Delhi Armistice"',
            f'\tdesc = "India holds {target.seat}. {target.name} has a fixed 60 percent chance to accept peace and Indian access, 25 percent to counter with peace but no access, and 15 percent to refuse. A lost capital claim makes refusal the only valid answer."',
            "\tstyle = 2",
            f'\tpicture = "{target.picture}"',
            "\taction_a = {",
            f"\t\ttrigger = {{ {live} }}",
            "\t\tai_chance = 60",
            '\t\tname = "Accept peace and Indian strategic access"',
            command("access which = IND"),
            command("relation which = IND value = 30"),
            command("event which = 9282288 where = IND when = 2"),
            "\t}",
            "\taction_b = {",
            f"\t\ttrigger = {{ {live} }}",
            "\t\tai_chance = 25",
            '\t\tname = "Counter with peace but no access"',
            command("relation which = IND value = 10"),
            command("event which = 9282289 where = IND when = 2"),
            "\t}",
            "\taction_c = {",
            "\t\tai_chance = 15",
            '\t\tname = "Refuse Delhi\'s armistice"',
            command("relation which = IND value = -30"),
            command("event which = 9282290 where = IND when = 2"),
            "\t}",
            "}",
        ]
    )
    return "\n".join(out)


def callback_event(event_id: int, kind: str) -> str:
    names = {
        "accept": ("A Regional Government Accepts Delhi's Armistice", "Publish the full armistice", -2),
        "counter": ("A Regional Government Counters Delhi's Armistice", "Ratify the limited peace", -1),
    }
    title, action, dissent = names[kind]
    out = header(event_id, "IND", one_action=True)
    out.extend(
        [
            f'\tname = "{title}"',
            f'\tdesc = "The selected opponent has accepted a country-specific peace. Delhi now ratifies only that armistice; every unrelated war and occupation remains live."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_liberated_territory"',
            "\taction_a = {",
            f'\t\tname = "{action}"',
            command(f"dissent value = {dissent}"),
            command(f"setflag which = ind_aubm_bespoke_{kind}"),
            command("event which = 9282291 where = IND when = 1"),
            "\t}",
            "}",
        ]
    )
    return "\n".join(out)


def refusal_event() -> str:
    out = header(9282290, "IND", one_action=True)
    out.extend(
        [
            '\tname = "A Regional Government Refuses Delhi\'s Armistice"',
            '\tdesc = "The selected opponent refuses. India keeps its battlefield record, but the same country file cannot be resubmitted for ninety days."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_liberated_territory"',
            "\taction_a = {",
            '\t\tname = "Continue the war and reopen the file in ninety days"',
            command("dissent value = 1"),
            command("setflag which = ind_aubm_bespoke_retry_pending"),
        ]
    )
    for target in TARGETS:
        out.append(command(f"setflag which = {retry_flag(target)}", trigger=f"flag = {target_flag(target)}"))
    for target in TARGETS:
        out.append(command(f"clrflag which = {target_flag(target)}"))
    out.extend(
        [
            command("clrflag which = ind_aubm_bespoke_armistice_outstanding"),
            command("event which = 9282292 where = IND when = 90"),
            "\t}",
            "}",
        ]
    )
    return "\n".join(out)


def ratify_event() -> str:
    out = header(9282291, "IND", one_action=True)
    out.extend(
        [
            '\tname = "Delhi Ratifies the Country-Specific Armistice"',
            '\tdesc = "Delhi converts any formal coalition into its named strategic compact before making separate peace. Only the recorded opponent leaves the campaign ledger; all other wars and earned achievements survive."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_liberated_territory"',
            "\taction_a = {",
            '\t\tname = "Ratify this pairwise peace"',
            command("setflag which = ind_v4a_treaty_cobelligerent", trigger="OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } }"),
            command("clrflag which = ind_v4a_treaty_formal_alliance", trigger="OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } }"),
            command("setflag which = ind_gc_cobelligerent", trigger="alliance = { country = IND country = GER }"),
            command("clrflag which = ind_gc_formal_axis", trigger="alliance = { country = IND country = GER }"),
            command("setflag which = ind_v4_sov_equal_compact", trigger="alliance = { country = IND country = SOV }"),
            command("clrflag which = ind_v4_sov_supervised_compact", trigger="alliance = { country = IND country = SOV }"),
            command("setflag which = ind_aubm_jp_partnership", trigger="alliance = { country = IND country = JAP }"),
            command("setflag which = ind_aubm_jp_independent_cobelligerent", trigger="alliance = { country = IND country = JAP }"),
            command("clrflag which = ind_aubm_jp_formal_alliance", trigger="alliance = { country = IND country = JAP }"),
        ]
    )
    for target in TARGETS:
        out.append(
            command(
                f"peace which = {target.tag} value = 1",
                trigger=f"flag = {target_flag(target)} war = {{ country = IND country = {target.tag} }}",
            )
        )
    for target in TARGETS:
        tf = target_flag(target)
        out.extend(
            [
                command(f"setflag which = ind_aubm_regional_settled_{target.key}", trigger=f"flag = {tf}"),
                command(f"setflag which = ind_aubm_bespoke_negotiated_{target.key}", trigger=f"flag = {tf}"),
                command(f"clrflag which = ind_aubm_regional_pending_{target.key}", trigger=f"flag = {tf}"),
                command(f"clrflag which = ind_aubm_regional_current_{target.key}", trigger=f"flag = {tf}"),
                command(f"clrflag which = ind_aubm_regional_victory_{target.key}", trigger=f"flag = {tf}"),
                command(f"clrflag which = ind_aubm_regional_suspended_{target.key}", trigger=f"flag = {tf}"),
            ]
        )
    for target in TARGETS:
        out.append(command(f"clrflag which = {target_flag(target)}"))
        out.append(command(f"clrflag which = {retry_flag(target)}"))
    out.extend(
        [
            command("setflag which = ind_aubm_bespoke_armistice"),
            command("clrflag which = ind_aubm_bespoke_armistice_outstanding"),
            command("clrflag which = ind_aubm_bespoke_retry_pending"),
            command("clrflag which = ind_aubm_bespoke_accept"),
            command("clrflag which = ind_aubm_bespoke_counter"),
            command("clrflag which = ind_v3_joined_allies"),
            command("clrflag which = ind_v3_joined_axis"),
            command("clrflag which = ind_v3_joined_comintern"),
            command("clrflag which = ind_v3_joined_japan"),
            "\t}",
            "}",
        ]
    )
    return "\n".join(out)


def retry_event() -> str:
    out = header(9282292, "IND", one_action=True)
    out.extend(
        [
            '\tname = "The Regional Armistice Cooling Period Ends"',
            '\tdesc = "Ninety days have passed since the refusal. Any still-valid country file may now be submitted again from its settlement board."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_war_aims"',
            "\taction_a = {",
            '\t\tname = "Reopen the recorded country file"',
        ]
    )
    for target in TARGETS:
        out.append(command(f"clrflag which = {retry_flag(target)}"))
    out.extend([command("clrflag which = ind_aubm_bespoke_retry_pending"), "\t}", "}"])
    return "\n".join(out)


def render() -> str:
    sections = [
        "#########################################################################\n"
        "# A Union Before Midnight V4: bespoke regional armistices\n"
        "# Generated by tools/generate_aubm_bespoke_armistices.py; do not edit.\n"
        "#########################################################################"
    ]
    sections.extend(proposal_event(index, target) for index, target in enumerate(TARGETS))
    sections.append(gulf_board())
    sections.append(lapse_event())
    sections.extend(response_event(index, target) for index, target in enumerate(TARGETS))
    sections.append(callback_event(9282288, "accept"))
    sections.append(callback_event(9282289, "counter"))
    sections.append(refusal_event())
    sections.append(ratify_event())
    sections.append(retry_event())
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="ascii") != generated:
            print(f"STALE: {OUTPUT.relative_to(ROOT)}")
            return 1
        print("OK: eight bespoke armistice lifecycles are current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generated, encoding="ascii", newline="\n")
    print(f"WROTE: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
