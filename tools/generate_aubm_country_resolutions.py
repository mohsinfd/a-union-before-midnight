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


def country_callback_id(tag: str) -> int:
    index = next(index for index, country in enumerate(COUNTRIES) if country.tag == tag)
    return BASE_ID + index * 2 + 1


def base_callback_id(tag: str) -> int:
    index = next(index for index, country in enumerate(COUNTRIES) if country.tag == tag)
    return 9288200 + index


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
            if country.retained_bases else []
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
        cmd(f"event which = {callback_id} where = {country.released} when = 1", f"exists = {country.released}"),
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
        lines.append(cmd(f"secedeprovince which = IND value = {province}"))
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
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_protected exists = MLY }} type = make_puppet which = MLY }}
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_protected exists = MLY }} type = event which = {base_callback_id("MLY")} where = MLY when = 1 }}
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_neutral exists = MLY }} type = guarantee which = IND where = MLY }}
\t\tcommand = {{ trigger = {{ flag = ind_malaya_colonial_neutral exists = MLY }} type = event which = {country_callback_id("MLY")} where = MLY when = 1 }}
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
    sections.extend(major_resolution(*row) for row in MAJOR_EVENTS)
    sections.extend(fragment_callback(*row) for row in FRAGMENT_CALLBACKS)
    sections.extend(fragment_menu(*row) for row in FRAGMENT_PLANS)
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
