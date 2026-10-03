#!/usr/bin/env python3
"""Generate the small, country-specific Indian peace system.

This replaces the former global, regional and theatre matrices.  Every visible
decision names one country, changes only that country and states its cost in
the button text.  A protected neutral is deliberately not a puppet and does
not inherit India's wars.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "mod/db/events/aubm_v4/53_country_resolutions.txt"
BASE_ID = 9288000


@dataclass(frozen=True)
class Country:
    tag: str
    name: str
    capital: int
    seat: str
    picture: str = "aubm_v4_liberated_territory"
    release_tag: str | None = None
    retained_bases: tuple[tuple[int, str], ...] = ()

    @property
    def key(self) -> str:
        return self.tag.lower()

    @property
    def released(self) -> str:
        return self.release_tag or self.tag


COUNTRIES = (
    Country("NEP", "Nepal", 1457, "Kathmandu", "aubm_v4_grand_strategy"),
    Country("BHU", "Bhutan", 1456, "Thimphu", "aubm_v4_grand_strategy"),
    Country("PER", "Persia", 1085, "Tehran", "aubm_v4_indian_ocean_war"),
    Country("IRQ", "Iraq", 1034, "Baghdad", "aubm_v4_indian_ocean_war", retained_bases=((1032, "Basrah"),)),
    Country("SAU", "Saudi Arabia", 1045, "Riyadh", "aubm_v4_indian_ocean_war"),
    Country("YEM", "Yemen", 1050, "Sana'a", "aubm_v4_indian_ocean_war", retained_bases=((1053, "Aden"),)),
    Country("OMN", "Oman", 1052, "Muscat", "aubm_v4_indian_ocean_war"),
    Country("AFG", "Afghanistan", 2171, "Kabul", "aubm_v4_barbarossa_reaction"),
    Country("TIB", "Tibet", 1289, "Lhasa", "aubm_v4_grand_strategy"),
    Country("SIK", "Xinjiang", 1281, "Urumqi", "aubm_v4_grand_strategy"),
    Country("CHI", "China", 1337, "Nanjing"),
    Country("CHC", "Communist China", 1354, "Yan'an"),
    Country("SIA", "Siam", 1423, "Bangkok", "aubm_v4_indian_ocean_war"),
    Country("U03", "Indochinese Union", 1395, "Hanoi"),
    Country("BUR", "Burma", 1415, "Rangoon"),
    Country("MLY", "Malaysia", 1438, "Kuala Lumpur", retained_bases=((1432, "Singapore"),)),
    Country("PHI", "Philippines", 1565, "Manila", retained_bases=((1579, "Davao"),)),
    Country("U05", "East Indies / Indonesia", 1647, "Batavia or Jogjakarta", "aubm_v4_indian_ocean_war", "INO", ((1653, "Soerabaja"),)),
    Country("BRU", "Brunei", 1625, "Bandar Seri Begawan"),
    Country("SAR", "Sarawak", 1624, "Kuching"),
    Country("AST", "Australia", 1707, "Canberra", retained_bases=((1697, "Darwin"),)),
    Country("NZL", "New Zealand", 1721, "Wellington"),
    Country("TUR", "Turkey", 1075, "Ankara"),
    Country("ITA", "Italy", 419, "Rome"),
    Country("FRA", "France", 55, "Paris"),
    Country("POR", "Portugal", 476, "Lisbon"),
    Country("ETH", "Ethiopia", 825, "Addis Ababa"),
    Country("SAF", "South Africa", 876, "Pretoria"),
)


@dataclass(frozen=True)
class IslandDefense:
    tag: str
    name: str
    land_base: int
    naval_base: int
    baseline_infantry: int
    baseline_garrison: int
    baseline_destroyers: int
    baseline_transports: int
    aid_infantry: int
    aid_marines: int
    aid_destroyers: int


ISLAND_DEFENSES = (
    IslandDefense("INO", "Indonesia", 1654, 1647, 2, 2, 1, 1, 1, 1, 1),
    IslandDefense("MLY", "Malaysia", 1438, 1438, 2, 1, 1, 1, 1, 0, 1),
    IslandDefense("PHI", "Philippines", 1565, 1565, 3, 1, 1, 1, 1, 0, 1),
    IslandDefense("BRU", "Brunei", 1625, 1625, 0, 1, 1, 0, 1, 0, 0),
    IslandDefense("SAR", "Sarawak", 1624, 1624, 0, 1, 1, 0, 1, 0, 0),
)

ISLAND_BY_TAG = {island.tag: island for island in ISLAND_DEFENSES}
COUNTRY_BY_RELEASE = {country.released: country for country in COUNTRIES}


def country_callback_id(tag: str) -> int:
    index = next(index for index, country in enumerate(COUNTRIES) if country.tag == tag)
    return BASE_ID + index * 2 + 1


def base_callback_id(tag: str) -> int:
    index = next(index for index, country in enumerate(COUNTRIES) if country.tag == tag)
    return 9288200 + index


def island_index(tag: str) -> int:
    return next(index for index, island in enumerate(ISLAND_DEFENSES) if island.tag == tag)


def island_setup_id(tag: str) -> int:
    return 9288380 + island_index(tag)


def island_baseline_id(tag: str) -> int:
    return 9288400 + island_index(tag)


def island_aid_id(tag: str) -> int:
    return 9288410 + island_index(tag)


def cmd(body: str, trigger: str | None = None) -> str:
    prefix = f"trigger = {{ {trigger} }} " if trigger else ""
    return f"\t\tcommand = {{ {prefix}type = {body} }}"


def live(country: Country) -> str:
    if country.tag == "U05":
        return (
            "OR = { "
            "AND = { exists = U05 war = { country = IND country = U05 } "
            "control = { province = 1647 data = IND } "
            "lost_national = { country = U05 value = 50 } NOT = { exists = INO } } "
            "AND = { exists = INO war = { country = IND country = INO } "
            "control = { province = 1654 data = IND } "
            "lost_national = { country = INO value = 50 } } }"
        )
    extra = f" NOT = {{ exists = {country.released} }}" if country.release_tag else ""
    return (
        f"exists = {country.tag} war = {{ country = IND country = {country.tag} }} "
        f"control = {{ province = {country.capital} data = IND }} "
        f"lost_national = {{ country = {country.tag} value = 50 }}{extra}"
    )


def annexed(country: Country) -> str:
    if country.release_tag:
        return (
            f"owned = {{ province = {country.capital} data = IND }} "
            f"control = {{ province = {country.capital} data = IND }} "
            f"NOT = {{ exists = {country.released} }}"
        )
    return (
        f"NOT = {{ exists = {country.tag} }} "
        f"owned = {{ province = {country.capital} data = IND }} "
        f"control = {{ province = {country.capital} data = IND }}"
    )


def indian_puppet(country: Country) -> str:
    return (
        f"exists = {country.released} "
        f"puppet = {{ country = {country.released} country = IND }}"
    )


def common_finish(country: Country, outcome: str) -> list[str]:
    return [
        cmd(f"setflag which = ind_country_resolution_{country.key}_{outcome}"),
        cmd(f"setflag which = ind_country_resolution_{country.key}_complete"),
        cmd(f"clrflag which = ind_aubm_regional_pending_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_current_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_victory_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_suspended_{country.key}"),
    ]


def defeat_commands(country: Country) -> list[str]:
    commands = [
        cmd(f"inherit which = {country.tag}", f"exists = {country.tag} war = {{ country = IND country = {country.tag} }}")
    ]
    if country.tag == "U05":
        commands.append(cmd("inherit which = INO", "exists = INO war = { country = IND country = INO }"))
    return commands


def resolution(index: int, country: Country) -> str:
    event_id = BASE_ID + index * 2
    callback_id = event_id + 1
    conditions = (
        f"OR = {{ AND = {{ {live(country)} }} AND = {{ {annexed(country)} }} "
        f"AND = {{ {indian_puppet(country)} }} }}"
    )
    lines = [
        "event = {",
        f"\tid = {event_id}",
        "\trandom = no",
        "\tpersistent = yes",
        "\tcountry = IND",
        "\ttrigger = { ai = no }",
        f'\tname = "{country.name}: Decide the Peace"',
        (
            f'\tdesc = "India controls {country.seat} and {country.name} has lost at least half of its national territory. '
            f'This decision changes {country.name} only. It cannot end, suspend or alter any other war."'
        ),
        "\tstyle = 2",
        f'\tpicture = "{country.picture}"',
        "\tdate = { day = 0 month = january year = 1933 }",
        "\toffset = 1",
        "\tdeathdate = { day = 29 month = december year = 1964 }",
        (
            f"\tdecision = {{ NOT = {{ flag = ind_country_resolution_{country.key}_complete }} "
            f"{conditions} }}"
        ),
        (
            f"\tdecision_trigger = {{ NOT = {{ flag = ind_country_resolution_{country.key}_complete }} "
            f"{conditions} }}"
        ),
        "\taction_a = {",
        f"\t\ttrigger = {{ NOT = {{ puppet = {{ country = {country.released} country = IND }} }} }}",
        '\t\tname = "Protectorate: -250 supplies, no dissent; joins wars"',
    ]
    lines.extend(defeat_commands(country))
    lines.extend([
        cmd(f"independence which = {country.released} value = 1 when = 0"),
        cmd(f"make_puppet which = {country.released}", f"exists = {country.released}"),
        *(
            [cmd(f"event which = {base_callback_id(country.tag)} where = {country.released} when = 1", f"exists = {country.released}")]
            if country.retained_bases and country.released not in ISLAND_BY_TAG else []
        ),
        *(
            [
                cmd(f"setflag which = ind_island_setup_{country.released.lower()}_protected"),
                cmd(f"event which = {island_setup_id(country.released)} where = IND when = 1"),
            ]
            if country.released in ISLAND_BY_TAG else []
        ),
        cmd("supplies value = -250"),
    ])
    lines.extend(common_finish(country, "protected"))
    lines.extend(
        [
            "\t}",
            "\taction_b = {",
            '\t\tname = "Protected neutrality: no dissent; Indian access"',
        ]
    )
    lines.extend(defeat_commands(country))
    lines.extend([
        cmd(f"independence which = {country.released} value = 1 when = 0"),
        cmd(f"end_mastery which = {country.released}", f"puppet = {{ country = {country.released} country = IND }}"),
        cmd(f"guarantee which = IND where = {country.released}", f"exists = {country.released}"),
        *(
            [cmd(f"event which = {callback_id} where = {country.released} when = 1", f"exists = {country.released}")]
            if country.released not in ISLAND_BY_TAG else []
        ),
        *(
            [
                cmd(f"setflag which = ind_island_setup_{country.released.lower()}_neutral"),
                cmd(f"event which = {island_setup_id(country.released)} where = IND when = 1"),
            ]
            if country.released in ISLAND_BY_TAG else []
        ),
    ])
    lines.extend(common_finish(country, "neutral"))
    lines.extend(
        [
            "\t}",
            "\taction_c = {",
            '\t\tname = "Dismiss permanently; make no settlement"',
        ]
    )
    lines.extend(common_finish(country, "dismissed"))
    lines.append("\t}")
    if country.tag == "U05":
        lines.extend(
            [
                "\taction_d = {",
                f"\t\ttrigger = {{ {annexed(country)} }}",
                '\t\tname = "Breakup options: Indonesia, Brunei, Sarawak"',
                cmd("event which = 9288093 where = IND when = 1"),
            ]
        )
    elif country.tag == "U03":
        lines.extend(
            [
                "\taction_d = {",
                f"\t\ttrigger = {{ {annexed(country)} }}",
                '\t\tname = "Breakup options: Vietnam, Cambodia, Laos"',
                cmd("event which = 9288094 where = IND when = 1"),
            ]
        )
    else:
        lines.extend(
            [
                "\taction_d = {",
                f"\t\ttrigger = {{ {annexed(country)} }}",
                '\t\tname = "Military rule: +2 dissent; local resistance"',
                cmd("dissent value = 2"),
                cmd("belligerence value = 1"),
                cmd(f"province_revoltrisk which = {country.capital} value = 2"),
                cmd("setflag which = ind_aubm_occupation_upkeep"),
            ]
        )
        lines.extend(common_finish(country, "occupied"))
    lines.extend(["\t}", "}", "", "event = {", f"\tid = {callback_id}", "\trandom = no", "\tone_action = yes", f"\tcountry = {country.released}", f'\tname = "{country.name}: Protected Neutrality"', f'\tdesc = "{country.name} leaves India\'s alliance, ends inherited major-power wars and grants Indian forces access. India\'s own wars do not change."', "\tstyle = 2", f'\tpicture = "{country.picture}"', "\taction_a = {", '\t\tname = "Confirm protected neutrality"', cmd("leave_alliance when = 1", f"participant = {{ country = {country.released} value = 4 }}"), cmd("peace which = ENG value = 1", f"war = {{ country = {country.released} country = ENG }}"), cmd("peace which = GER value = 1", f"war = {{ country = {country.released} country = GER }}"), cmd("peace which = SOV value = 1", f"war = {{ country = {country.released} country = SOV }}"), cmd("peace which = JAP value = 1", f"war = {{ country = {country.released} country = JAP }}"), cmd("peace which = USA value = 1", f"war = {{ country = {country.released} country = USA }}"), cmd("peace which = ITA value = 1", f"war = {{ country = {country.released} country = ITA }}"), cmd("peace which = HOL value = 1", f"war = {{ country = {country.released} country = HOL }}"), cmd("peace which = AST value = 1", f"war = {{ country = {country.released} country = AST }}"), cmd("access which = IND"), cmd("relation which = IND value = 50"), cmd(f"non_aggression which = {country.released} where = IND when = 1080"), "\t}", "}"])
    return "\n".join(lines)


def base_callback(country: Country) -> str:
    bases = ", ".join(name for _, name in country.retained_bases)
    lines = [
        "event = {",
        f"\tid = {base_callback_id(country.tag)}",
        "\trandom = no",
        "\tone_action = yes",
        f"\tcountry = {country.released}",
        f'\tname = "{country.name}: Indian Base Treaty"',
        f'\tdesc = "The protectorate grants India sovereign base territory at {bases}. The remaining country stays under its own government and shares India\'s wars."',
        "\tstyle = 2",
        f'\tpicture = "{country.picture}"',
        "\taction_a = {",
        f'\t\tname = "Transfer {bases} to India"',
    ]
    for province, _ in country.retained_bases:
        # Darkest Hour documents the default secede mode as flawed.  Mode 2
        # deterministically assigns both ownership and control to India, which
        # is what a sovereign-base treaty promises even when the grantor keeps
        # the province as a national claim.
        lines.append(cmd(f"secedeprovince which = IND value = {province} when = 2"))
    lines.extend([
        cmd("access which = IND"),
        cmd("relation which = IND value = 40"),
        "\t}",
        "}",
    ])
    return "\n".join(lines)


FRAGMENT_CALLBACKS = (
    (9288090, "CMB", "Cambodia"),
    (9288091, "LAO", "Laos"),
    (9288092, "VIE", "Vietnam"),
)

FRAGMENT_PLANS = (
    (
        9288093,
        next(country for country in COUNTRIES if country.tag == "U05"),
        (
            ("BRU", "Brunei", country_callback_id("BRU")),
            ("SAR", "Sarawak", country_callback_id("SAR")),
            ("INO", "Indonesia", country_callback_id("U05")),
        ),
    ),
    (
        9288094,
        next(country for country in COUNTRIES if country.tag == "U03"),
        (("CMB", "Cambodia", 9288090), ("LAO", "Laos", 9288091), ("VIE", "Vietnam", 9288092)),
    ),
)


def fragment_callback(event_id: int, tag: str, name: str) -> str:
    return f'''event = {{
\tid = {event_id}
\trandom = no
\tone_action = yes
\tcountry = {tag}
\tname = "{name}: Protected Neutrality"
\tdesc = "{name} is independent, remains outside India's wars and grants Indian forces military access."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Confirm protected neutrality"
\t\tcommand = {{ type = access which = IND }}
\t\tcommand = {{ type = relation which = IND value = 50 }}
\t\tcommand = {{ type = non_aggression which = {tag} where = IND when = 1080 }}
\t}}
}}'''


def fragment_menu(event_id: int, country: Country, fragments: tuple[tuple[str, str, int], ...]) -> str:
    names = ", ".join(name for _, name, _ in fragments)
    lines = [
        "event = {",
        f"\tid = {event_id}",
        "\trandom = no",
        "\tpersistent = yes",
        "\tcountry = IND",
        f'\tname = "{country.name}: Choose the Breakup"',
        f'\tdesc = "The named states are {names}. Active protectorates become Indian puppets and share India\'s wars. Protected neutrals remain independent, stay outside India\'s wars, grant access and receive Indian guarantees."',
        "\tstyle = 2",
        f'\tpicture = "{country.picture}"',
        "\taction_a = {",
        '\t\tname = "Active protectorates: -500 supplies; share wars"',
    ]
    for tag, _, _ in fragments:
        lines.append(cmd(f"independence which = {tag} value = 1 when = 0"))
    for tag, _, _ in fragments:
        lines.append(cmd(f"make_puppet which = {tag}", f"exists = {tag}"))
        if tag in ISLAND_BY_TAG:
            lines.append(cmd(f"setflag which = ind_island_setup_{tag.lower()}_protected"))
            lines.append(cmd(f"event which = {island_setup_id(tag)} where = IND when = 1"))
    lines.append(cmd("supplies value = -500"))
    lines.extend(common_finish(country, "fragmented_protected"))
    lines.extend([
        "\t}",
        "\taction_b = {",
        '\t\tname = "Protected neutrals: -250 supplies; separate wars"',
    ])
    for tag, _, _ in fragments:
        lines.append(cmd(f"independence which = {tag} value = 1 when = 0"))
    for tag, _, callback_id in fragments:
        lines.append(cmd(f"guarantee which = IND where = {tag}", f"exists = {tag}"))
        if tag in ISLAND_BY_TAG:
            lines.append(cmd(f"setflag which = ind_island_setup_{tag.lower()}_neutral"))
            lines.append(cmd(f"event which = {island_setup_id(tag)} where = IND when = 1"))
        else:
            lines.append(cmd(f"event which = {callback_id} where = {tag} when = 1", f"exists = {tag}"))
    lines.append(cmd("supplies value = -250"))
    lines.extend(common_finish(country, "fragmented_neutral"))
    lines.extend([
        "\t}",
        "\taction_c = {",
        '\t\tname = "Dismiss this breakup permanently"',
    ])
    lines.extend(common_finish(country, "dismissed"))
    lines.extend(["\t}", "}"])
    return "\n".join(lines)


def island_baseline_event(island: IslandDefense) -> str:
    lines = [
        "event = {",
        f"\tid = {island_baseline_id(island.tag)}",
        "\trandom = no",
        "\tone_action = yes",
        f"\tcountry = {island.tag}",
        "\ttrigger = { year = 1940 }",
        f'\tname = "{island.name}: Founding Defence Force"',
        '\tdesc = "The new state forms a territorial army, coastal fleet and supply reserve so independence does not leave it defenceless."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_liberated_territory"',
        "\tdate = { day = 0 month = january year = 1933 }",
        "\toffset = 5",
        "\tdeathdate = { day = 29 month = december year = 1964 }",
        "\taction_a = {",
        '\t\tname = "Muster the founding forces"',
        cmd(f'add_corps which = "{island.name} Defence Command" value = land where = {island.land_base}'),
    ]
    for number in range(1, island.baseline_infantry + 1):
        lines.append(cmd(f'add_division which = "{number}. National Infantry Division" value = infantry when = -1'))
    for number in range(1, island.baseline_garrison + 1):
        lines.append(cmd(f'add_division which = "{number}. Island Garrison Division" value = garrison when = -1'))
    if island.baseline_destroyers or island.baseline_transports:
        lines.append(cmd(f'add_corps which = "{island.name} Coastal Fleet" value = naval where = {island.naval_base}'))
    for number in range(1, island.baseline_destroyers + 1):
        lines.append(cmd(f'add_division which = "{number}. Coastal Defence Flotilla" value = destroyer when = -1'))
    for number in range(1, island.baseline_transports + 1):
        lines.append(cmd(f'add_division which = "{number}. National Transport Flotilla" value = transport when = -1'))
    lines.extend([
        cmd("manpowerpool value = 30"),
        cmd("supplies value = 1200"),
        cmd("oilpool value = 500"),
        "\t}",
        "}",
    ])
    return "\n".join(lines)


def island_aid_event(island: IslandDefense) -> str:
    lines = [
        "event = {",
        f"\tid = {island_aid_id(island.tag)}",
        "\trandom = no",
        "\tone_action = yes",
        f"\tcountry = {island.tag}",
        f'\tname = "{island.name}: Indian Defence Mission"',
        '\tdesc = "India supplies instructors, mobile troops and escorts to an aligned protectorate. These forces supplement the local founding defence force."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_indian_ocean_war"',
        "\taction_a = {",
        '\t\tname = "Receive the Indian defence mission"',
        cmd(f'add_corps which = "Indian Ocean Defence Mission" value = land where = {island.land_base}'),
    ]
    for number in range(1, island.aid_infantry + 1):
        lines.append(cmd(f'add_division which = "{number}. Protectorate Infantry Division" value = infantry when = -1'))
    for number in range(1, island.aid_marines + 1):
        lines.append(cmd(f'add_division which = "{number}. Protectorate Marine Division" value = marine when = -1'))
    if island.aid_destroyers:
        lines.append(cmd(f'add_corps which = "Indian Ocean Escort Group" value = naval where = {island.naval_base}'))
    for number in range(1, island.aid_destroyers + 1):
        lines.append(cmd(f'add_division which = "{number}. Protectorate Escort Flotilla" value = destroyer when = -1'))
    lines.extend([
        cmd("supplies value = 800"),
        cmd("oilpool value = 300"),
        cmd("relation which = IND value = 30"),
        "\t}",
        "}",
    ])
    return "\n".join(lines)


def island_setup_event(island: IslandDefense) -> str:
    country = COUNTRY_BY_RELEASE[island.tag]
    protected = f"ind_island_setup_{island.tag.lower()}_protected"
    neutral = f"ind_island_setup_{island.tag.lower()}_neutral"
    lines = [
        "event = {",
        f"\tid = {island_setup_id(island.tag)}",
        "\trandom = no",
        "\tpersistent = yes",
        "\tone_action = yes",
        "\tcountry = IND",
        f'\tname = "{island.name}: Complete the Settlement"',
        f'\tdesc = "The {island.name} government now exists. India can apply the chosen relationship and establish its initial defence forces without relying on same-day release commands."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_liberated_territory"',
        "\taction_a = {",
        f"\t\ttrigger = {{ flag = {protected} exists = {island.tag} }}",
        '\t\tname = "Complete the protectorate agreement"',
        cmd(f"make_puppet which = {island.tag}"),
    ]
    if country.retained_bases:
        lines.append(cmd(f"event which = {base_callback_id(country.tag)} where = {island.tag} when = 1"))
    lines.extend([
        cmd(f"event which = {island_baseline_id(island.tag)} where = {island.tag} when = 1"),
        cmd(f"event which = {island_aid_id(island.tag)} where = {island.tag} when = 1"),
        cmd(f"clrflag which = {protected}"),
        cmd(f"clrflag which = {neutral}"),
        "\t}",
        "\taction_b = {",
        f"\t\ttrigger = {{ flag = {neutral} exists = {island.tag} }}",
        '\t\tname = "Complete protected neutrality"',
        cmd(f"end_mastery which = {island.tag}", f"puppet = {{ country = {island.tag} country = IND }}"),
        cmd(f"guarantee which = IND where = {island.tag}"),
        cmd(f"event which = {country_callback_id(country.tag)} where = {island.tag} when = 1"),
        cmd(f"event which = {island_baseline_id(island.tag)} where = {island.tag} when = 1"),
        cmd(f"clrflag which = {protected}"),
        cmd(f"clrflag which = {neutral}"),
        "\t}",
        "\taction_c = {",
        f"\t\ttrigger = {{ NOT = {{ exists = {island.tag} }} }}",
        '\t\tname = "The state was not created"',
        cmd(f"clrflag which = {protected}"),
        cmd(f"clrflag which = {neutral}"),
        "\t}",
        "}",
    ])
    return "\n".join(lines)


def legacy_island_recovery() -> str:
    return f'''event = {{
\tid = 9288389
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {{
\t\tai = no
\t\tflag = ind_country_resolution_u05_fragmented_protected
\t\tNOT = {{ flag = ind_island_defence_alpha33_recovered }}
\t\texists = INO
\t\texists = BRU
\t\texists = SAR
\t}}
\tname = "Island Agreements Corrected"
\tdesc = "The earlier breakup created weak governments and omitted Indonesia's Soerabaja base clause. The recorded choices will be preserved while the missing defence and base arrangements are applied."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\tdate = {{ day = 0 month = january year = 1933 }}
\toffset = 1
\tdeathdate = {{ day = 29 month = december year = 1964 }}
\taction_a = {{
\t\tname = "Apply the recorded agreements"
\t\tcommand = {{ type = setflag which = ind_island_setup_ino_protected }}
\t\tcommand = {{ type = event which = {island_setup_id("INO")} where = IND when = 1 }}
\t\tcommand = {{ type = setflag which = ind_island_setup_bru_protected }}
\t\tcommand = {{ type = event which = {island_setup_id("BRU")} where = IND when = 1 }}
\t\tcommand = {{ trigger = {{ flag = ind_country_resolution_sar_neutral }} type = setflag which = ind_island_setup_sar_neutral }}
\t\tcommand = {{ trigger = {{ NOT = {{ flag = ind_country_resolution_sar_neutral }} }} type = setflag which = ind_island_setup_sar_protected }}
\t\tcommand = {{ type = event which = {island_setup_id("SAR")} where = IND when = 1 }}
\t\tcommand = {{ trigger = {{ puppet = {{ country = MLY country = IND }} }} type = setflag which = ind_island_setup_mly_protected }}
\t\tcommand = {{ trigger = {{ puppet = {{ country = MLY country = IND }} }} type = event which = {island_setup_id("MLY")} where = IND when = 1 }}
\t\tcommand = {{ type = setflag which = ind_island_defence_alpha33_recovered }}
\t}}
}}'''


def soerabaja_handover_recovery() -> str:
    """Repair saves where the visible treaty used legacy secession mode."""
    return '''event = {
\tid = 9288390
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {
\t\tai = no
\t\texists = INO
\t\tpuppet = { country = INO country = IND }
\t\towned = { province = 1653 data = INO }
\t\tOR = {
\t\t\tflag = ind_country_resolution_u05_protected
\t\t\tflag = ind_country_resolution_u05_fragmented_protected
\t\t}
\t\tNOT = { flag = ind_soerabaja_base_handover_complete }
\t}
\tname = "Soerabaja Base Handover Completed"
\tdesc = "Indonesia has signed the base treaty. India now receives both legal ownership and control of Soerabaja; Indonesia keeps its national claim and the rest of the country."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\tdate = { day = 0 month = january year = 1933 }
\toffset = 1
\tdeathdate = { day = 29 month = december year = 1964 }
\taction_a = {
\t\tname = "Complete the Soerabaja transfer"
\t\tcommand = { type = setflag which = ind_soerabaja_base_handover_complete }
\t\tcommand = { type = event which = 9288391 where = INO when = 0 }
\t}
}

event = {
\tid = 9288391
\trandom = no
\tone_action = yes
\tcountry = INO
\tname = "Soerabaja Base Handover"
\tdesc = "Indonesia transfers legal ownership and control of Soerabaja to India under the signed base treaty. Indonesia keeps its national claim."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\taction_a = {
\t\tname = "Transfer Soerabaja to India"
\t\tcommand = { type = secedeprovince which = IND value = 1653 when = 2 }
\t}
}'''


MAJOR_EVENTS = (
    (
        "ENG", "Britain", "London", 9288080,
        "control = { province = 29 data = IND } lost_national = { country = ENG value = 40 }",
        "India controls London and Britain has lost at least 40 percent of its national territory.",
    ),
    (
        "GER", "Germany", "Berlin", 9288081,
        "control = { province = 163 data = IND } lost_national = { country = GER value = 50 }",
        "India controls Berlin and Germany has lost at least half of its national territory.",
    ),
    (
        "SOV", "Soviet Union", "Moscow", 9288082,
        "control = { province = 572 data = IND } control = { province = 663 data = IND } OR = { AND = { control = { province = 713 data = IND } control = { province = 1103 data = IND } } AND = { control = { province = 713 data = IND } control = { province = 706 data = IND } } AND = { control = { province = 1103 data = IND } control = { province = 706 data = IND } } }",
        "India controls Moscow and Stalingrad, plus two of Baku, Tashkent and Astrakhan.",
    ),
    (
        "JAP", "Japan", "Tokyo", 9288083,
        "control = { province = 1552 data = IND } control = { province = 1553 data = IND } lost_national = { country = JAP value = 35 }",
        "India controls Tokyo and Osaka and Japan has lost at least 35 percent of its national territory.",
    ),
    (
        "USA", "United States", "Washington", 9288084,
        "control = { province = 1734 data = IND } OR = { control = { province = 1809 data = IND } control = { province = 1887 data = IND } control = { province = 1889 data = IND } } lost_national = { country = USA value = 30 }",
        "India controls Pearl Harbor, one listed mainland objective and at least 30 percent of American national territory has been lost.",
    ),
)


def major_resolution(tag: str, name: str, seat: str, event_id: int, requirements: str, explanation: str) -> str:
    key = tag.lower()
    condition = f"exists = {tag} war = {{ country = IND country = {tag} }} {requirements} NOT = {{ flag = ind_country_resolution_major_{key} }}"
    legacy = (
        "\n\t\tcommand = { type = setflag which = ind_v3_japan_settlement_1945 }"
        if tag == "JAP" else ""
    )
    return f'''event = {{
\tid = {event_id}
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {{ ai = no }}
\tname = "{name}: India Can End Its War"
\tdesc = "{explanation} India may now make a separate peace with {name}. This ends only India's war with {name}; India's other wars continue."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\tdate = {{ day = 0 month = january year = 1933 }}
\toffset = 1
\tdeathdate = {{ day = 29 month = december year = 1964 }}
\tdecision = {{ {condition} }}
\tdecision_trigger = {{ {condition} }}
\taction_a = {{
\t\tname = "Separate peace: -3 dissent; +300 money"
\t\tcommand = {{ type = peace which = {tag} value = 1 }}
\t\tcommand = {{ type = dissent value = -3 }}
\t\tcommand = {{ type = money value = 300 }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_major_{key} }}
\t\tcommand = {{ trigger = {{ atwar = no }} type = setflag which = ind_aubm_postwar_congress_completed }}{legacy}
\t}}
\taction_b = {{
\t\tname = "Dismiss this peace; continue the war"
\t\tcommand = {{ type = setflag which = ind_country_resolution_major_{key} }}
\t}}
}}'''


def soviet_resolution() -> str:
    groups = (
        ("KAZ", "Kazakhstan", (506, 507, 505, 500, 498, 504), (1114, 1117, 1118, 1116, 503, 1110, 1108, 1113, 1115, 1111, 502, 499, 1109, 1112, 501)),
        ("KYG", "Kyrgyzstan", (1107, 1106), ()),
        ("TAJ", "Tajikistan", (1105, 1104), ()),
        ("TRK", "Turkmenistan", (1097, 1098), ()),
        ("UZB", "Uzbekistan", (1101, 1102, 1100, 1103, 1099), ()),
        ("ARM", "Armenia", (711,), (712, 714)),
        ("AZB", "Azerbaijan", (713,), (712, 714)),
        ("GEO", "Georgia", (708, 709), (710, 707)),
    )
    western = (
        "AND = { control = { province = 572 data = IND } "
        "control = { province = 663 data = IND } "
        "OR = { AND = { control = { province = 713 data = IND } control = { province = 1103 data = IND } } "
        "AND = { control = { province = 713 data = IND } control = { province = 706 data = IND } } "
        "AND = { control = { province = 1103 data = IND } control = { province = 706 data = IND } } } }"
    )
    eastern = (
        "AND = { control = { province = 713 data = IND } control = { province = 1103 data = IND } "
        "control = { province = 706 data = IND } control = { province = 1131 data = IND } "
        "control = { province = 1132 data = IND } control = { province = 1138 data = IND } "
        "control = { province = 1151 data = IND } lost_national = { country = SOV value = 40 } }"
    )
    condition = (
        f"exists = SOV war = {{ country = IND country = SOV }} OR = {{ {western} {eastern} }} "
        "NOT = { flag = ind_country_resolution_major_sov }"
    )
    transfer_lines: list[str] = []
    release_lines: list[str] = []
    puppet_lines: list[str] = []
    for tag, _, minimum, extra in groups:
        full_control = " ".join(
            f"control = {{ province = {province} data = IND }}" for province in minimum
        )
        for province in minimum + extra:
            transfer_lines.append(
                cmd(
                    f"secedeprovince which = IND value = {province}",
                    f"{full_control} control = {{ province = {province} data = IND }}",
                )
            )
        full_owned = " ".join(
            f"owned = {{ province = {province} data = IND }}" for province in minimum
        )
        release_lines.append(cmd(f"independence which = {tag} value = 1 when = 0", full_owned))
        puppet_lines.append(cmd(f"make_puppet which = {tag}", f"exists = {tag}"))
    transfers = "\n".join(transfer_lines)
    releases = "\n".join(release_lines)
    puppets = "\n".join(puppet_lines)
    return f'''event = {{
\tid = 9288082
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {{ ai = no }}
\tname = "Soviet Union: India Can Dictate a Settlement"
\tdesc = "India may qualify by taking Moscow and Stalingrad, or by breaking the southern and Ural belt through Baku, Tashkent, Astrakhan, Ufa, Chelyabinsk, Omsk and Sverdlovsk while the USSR has lost 40 percent. Fully occupied Caucasian and Central Asian republics can become Indian protectorates. Incomplete republics remain Soviet."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\tdate = {{ day = 0 month = january year = 1933 }}
\toffset = 1
\tdeathdate = {{ day = 29 month = december year = 1964 }}
\tdecision = {{ {condition} }}
\tdecision_trigger = {{ {condition} }}
\taction_a = {{
\t\tname = "Liberation peace: aligned republics; -4 dissent"
\t\tcommand = {{ type = setflag which = ind_soviet_liberation_pending }}
\t\tcommand = {{ type = event which = 9288360 where = SOV when = 1 }}
\t}}
\taction_b = {{
\t\tname = "Continue the war; keep this decision open"
\t}}
\taction_c = {{
\t\tname = "Dismiss this settlement permanently"
\t\tcommand = {{ type = setflag which = ind_country_resolution_major_sov }}
\t}}
}}

event = {{
\tid = 9288360
\trandom = no
\tone_action = yes
\tcountry = SOV
\tname = "Soviet Union Transfers the Occupied Republics"
\tdesc = "The Soviet government transfers legal title only to republics whose entire required territory is under Indian occupation."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Transfer the fully occupied republics"
{transfers}
\t\tcommand = {{ type = event which = 9288361 where = IND when = 1 }}
\t}}
}}

event = {{
\tid = 9288361
\trandom = no
\tone_action = yes
\tcountry = IND
\tname = "Caucasian and Central Asian Independence"
\tdesc = "India establishes every republic for which all required provinces were transferred. A final agreement will align the new governments and end India's Soviet war."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Establish the eligible republics"
{releases}
\t\tcommand = {{ type = event which = 9288362 where = IND when = 1 }}
\t}}
}}

event = {{
\tid = 9288362
\trandom = no
\tone_action = yes
\tcountry = IND
\tname = "The Delhi-Moscow Liberation Peace"
\tdesc = "The new republics become Indian protectorates. India and the Soviet Union end their war; India's other wars continue."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Sign the liberation peace"
{puppets}
\t\tcommand = {{ type = peace which = SOV value = 1 }}
\t\tcommand = {{ type = dissent value = -4 }}
\t\tcommand = {{ type = money value = 500 }}
\t\tcommand = {{ type = supplies value = 1000 }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_major_sov }}
\t\tcommand = {{ type = clrflag which = ind_soviet_liberation_pending }}
\t}}
}}'''


def malaya_colonial_resolution() -> str:
    controls = " ".join(
        f"control = {{ province = {province} data = IND }}"
        for province in (1432, 1433, 1434, 1435, 1436, 1437, 1438)
    )
    condition = (
        "NOT = { exists = MLY } exists = ENG war = { country = IND country = ENG } "
        "owned = { province = 1438 data = ENG } "
        f"{controls} NOT = {{ flag = ind_country_resolution_malaya_colonial_complete }}"
    )
    transfer_commands = "\n".join(
        cmd(f"secedeprovince which = IND value = {province}")
        for province in (1432, 1433, 1434, 1435, 1436, 1437, 1438)
    )
    return f'''event = {{
\tid = 9288300
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {{ ai = no }}
\tname = "Malaysia: Settle the British Colony"
\tdesc = "India occupies Singapore and the Malayan peninsula, but Britain still owns them. This decision transfers Malaya from Britain and settles Malaysia only."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\tdate = {{ day = 0 month = january year = 1933 }}
\toffset = 1
\tdeathdate = {{ day = 29 month = december year = 1964 }}
\tdecision = {{ {condition} }}
\tdecision_trigger = {{ {condition} }}
\taction_a = {{
\t\tname = "Protectorate; India keeps Singapore"
\t\tcommand = {{ type = setflag which = ind_malaya_colonial_protected }}
\t\tcommand = {{ type = event which = 9288301 where = ENG when = 1 }}
\t}}
\taction_b = {{
\t\tname = "Protected neutral; Malaysia keeps Singapore"
\t\tcommand = {{ type = setflag which = ind_malaya_colonial_neutral }}
\t\tcommand = {{ type = event which = 9288301 where = ENG when = 1 }}
\t}}
\taction_c = {{
\t\tname = "Dismiss Malaysia permanently"
\t\tcommand = {{ type = setflag which = ind_country_resolution_malaya_colonial_complete }}
\t}}
}}

event = {{
\tid = 9288301
\trandom = no
\tone_action = yes
\tcountry = ENG
\tname = "Britain Transfers Malaya"
\tdesc = "Indian forces hold the Malayan peninsula. Britain transfers the occupied territory so its future can be settled."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\taction_a = {{
\t\tname = "Transfer the occupied territory"
{transfer_commands}
\t\tcommand = {{ type = event which = 9288302 where = IND when = 1 }}
\t}}
}}

event = {{
\tid = 9288302
\trandom = no
\tone_action = yes
\tcountry = IND
\tname = "Malaysia: Independence"
\tdesc = "British ownership has ended. Malaysia can now receive the settlement India chose."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Establish Malaysia"
\t\tcommand = {{ type = independence which = MLY value = 1 when = 0 }}
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_protected }} type = setflag which = ind_island_setup_mly_protected }}
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_neutral }} type = setflag which = ind_island_setup_mly_neutral }}
\t\tcommand = {{ type = event which = {island_setup_id("MLY")} where = IND when = 1 }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_malaya_colonial_complete }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_mly_complete }}
\t\tcommand = {{ type = clrflag which = ind_malaya_colonial_protected }}
\t\tcommand = {{ type = clrflag which = ind_malaya_colonial_neutral }}
\t}}
}}'''


def arab_federation_resolution() -> str:
    minimum = (
        778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788,
        790, 791, 792, 793, 794, 795, 796, 798, 799, 900,
        1016, 1017, 1021, 1022, 1023, 1024, 1025, 1026,
    )
    held = "\n\t\t".join(
        f"control = {{ province = {province} data = IND }}" for province in minimum
    )
    constituents = "\n\t\t".join(
        f"OR = {{ NOT = {{ exists = {tag} }} puppet = {{ country = {tag} country = IND }} AND = {{ owned = {{ province = {capital} data = IND }} control = {{ province = {capital} data = IND }} }} }}"
        for tag, capital in (("IRQ", 1034), ("SAU", 1045), ("YEM", 1050), ("OMN", 1052))
    )
    condition = (
        "NOT = { exists = ARA }\n\t\t"
        f"{held}\n\t\t{constituents}\n\t\t"
        "NOT = { flag = ind_country_resolution_ara_complete }"
    )
    inherit = "\n".join(
        cmd(f"inherit which = {tag}", f"puppet = {{ country = {tag} country = IND }}")
        for tag in ("IRQ", "SAU", "YEM", "OMN")
    )
    base_commands = "\n".join(
        cmd(f"secedeprovince which = IND value = {province}")
        for province in (900, 1053, 1032)
    )
    transfer_owners = ("ENG", "EGY", "FRA", "U01", "SYR", "JOR", "ITA", "GER", "TUR")
    transfer_calls = "\n".join(
        cmd(f"event which = {9288320 + index} where = {tag} when = 1", f"exists = {tag}")
        for index, tag in enumerate(transfer_owners)
    )
    transfer_events = "\n\n".join(
        f'''event = {{
\tid = {9288320 + index}
\trandom = no
\tone_action = yes
\tcountry = {tag}
\tname = "Transfer Indian-Occupied Arab Territory"
\tdesc = "India controls the listed Arab territory. Its former owner transfers legal title before the Arab Federation is established."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\taction_a = {{
\t\tname = "Transfer the occupied territory"
{chr(10).join(cmd(f"secedeprovince which = IND value = {province}") for province in minimum)}
\t}}
}}'''
        for index, tag in enumerate(transfer_owners)
    )
    return f'''event = {{
\tid = 9288310
\trandom = no
\tpersistent = yes
\tcountry = IND
\ttrigger = {{ ai = no }}
\tname = "Arab Federation: Unite the Defeated States"
\tdesc = "India must control Egypt, Suez, Syria and Jordan. Iraq, Saudi Arabia, Yemen and Oman must be gone, Indian-held or Indian protectorates. Colonial owners transfer the occupied land before federation."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\tdate = {{ day = 0 month = january year = 1933 }}
\toffset = 1
\tdeathdate = {{ day = 29 month = december year = 1964 }}
\tdecision = {{ {condition} }}
\tdecision_trigger = {{ {condition} }}
\taction_a = {{
\t\tname = "Indian protectorate; keep three bases"
\t\tcommand = {{ type = setflag which = ind_ara_choice_protected }}
{transfer_calls}
\t\tcommand = {{ type = event which = 9288330 where = IND when = 2 }}
\t\tcommand = {{ type = supplies value = -750 }}
\t}}
\taction_b = {{
\t\tname = "Protected neutral; keep no territory"
\t\tcommand = {{ type = setflag which = ind_ara_choice_neutral }}
{transfer_calls}
\t\tcommand = {{ type = event which = 9288330 where = IND when = 2 }}
\t\tcommand = {{ type = supplies value = -500 }}
\t}}
\taction_c = {{
\t\tname = "Dismiss Arab unification permanently"
\t\tcommand = {{ type = setflag which = ind_country_resolution_ara_complete }}
\t}}
}}

event = {{
\tid = 9288311
\trandom = no
\tone_action = yes
\tcountry = ARA
\tname = "Arab Federation: Indian Base Treaty"
\tdesc = "The new federation transfers Suez, Aden and Basrah to India as permanent naval and air bases."
\tstyle = 2
\tpicture = "aubm_v4_indian_ocean_war"
\taction_a = {{
\t\tname = "Transfer Suez, Aden and Basrah"
{base_commands}
\t\tcommand = {{ type = access which = IND }}
\t\tcommand = {{ type = relation which = IND value = 50 }}
\t}}
}}

event = {{
\tid = 9288312
\trandom = no
\tone_action = yes
\tcountry = ARA
\tname = "Arab Federation: Protected Neutrality"
\tdesc = "The federation remains outside India's wars, grants Indian access and receives an Indian guarantee."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Confirm protected neutrality"
\t\tcommand = {{ type = leave_alliance when = 1 }}
\t\tcommand = {{ type = access which = IND }}
\t\tcommand = {{ type = relation which = IND value = 50 }}
\t\tcommand = {{ type = non_aggression which = ARA where = IND when = 1080 }}
\t}}
}}

{transfer_events}

event = {{
\tid = 9288330
\trandom = no
\tone_action = yes
\tcountry = IND
\tname = "Arab Federation: Independence"
\tdesc = "The occupied Arab lands have been transferred. India can now establish the federation selected two days ago."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\taction_a = {{
\t\tname = "Establish the Arab Federation"
{inherit}
\t\tcommand = {{ type = independence which = ARA value = 1 when = 0 }}
\t\tcommand = {{ trigger = {{ flag = ind_ara_choice_protected exists = ARA }} type = make_puppet which = ARA }}
\t\tcommand = {{ trigger = {{ flag = ind_ara_choice_protected exists = ARA }} type = event which = 9288311 where = ARA when = 1 }}
\t\tcommand = {{ trigger = {{ flag = ind_ara_choice_neutral exists = ARA }} type = guarantee which = IND where = ARA }}
\t\tcommand = {{ trigger = {{ flag = ind_ara_choice_neutral exists = ARA }} type = event which = 9288312 where = ARA when = 1 }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_ara_complete }}
\t\tcommand = {{ type = clrflag which = ind_ara_choice_protected }}
\t\tcommand = {{ type = clrflag which = ind_ara_choice_neutral }}
\t}}
}}'''


def render() -> str:
    sections = [
        "#########################################################################\n"
        "# A Union Before Midnight: country-specific peace decisions\n"
        "# Generated by tools/generate_aubm_country_resolutions.py; do not edit.\n"
        "#########################################################################"
    ]
    sections.extend(resolution(index, country) for index, country in enumerate(COUNTRIES))
    sections.extend(base_callback(country) for country in COUNTRIES if country.retained_bases)
    sections.extend(major_resolution(*row) for row in MAJOR_EVENTS if row[0] != "SOV")
    sections.append(soviet_resolution())
    sections.extend(fragment_callback(*row) for row in FRAGMENT_CALLBACKS)
    sections.extend(fragment_menu(*row) for row in FRAGMENT_PLANS)
    sections.extend(island_setup_event(island) for island in ISLAND_DEFENSES)
    sections.extend(island_baseline_event(island) for island in ISLAND_DEFENSES)
    sections.extend(island_aid_event(island) for island in ISLAND_DEFENSES)
    sections.append(legacy_island_recovery())
    sections.append(soerabaja_handover_recovery())
    sections.append(malaya_colonial_resolution())
    sections.append(arab_federation_resolution())
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
        print(f"OK: {len(COUNTRIES)} minor and {len(MAJOR_EVENTS)} major country resolutions")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generated, encoding="ascii", newline="\n")
    print(f"WROTE: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
