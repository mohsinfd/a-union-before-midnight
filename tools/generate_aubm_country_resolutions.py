#!/usr/bin/env python3
"""Generate the small, country-specific Indian peace system.

This replaces the former global, regional and theatre matrices.  Every visible
decision names one country, changes only that country and states its cost in
the button text.
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
    Country("IRQ", "Iraq", 1034, "Baghdad", "aubm_v4_indian_ocean_war"),
    Country("SAU", "Saudi Arabia", 1045, "Riyadh", "aubm_v4_indian_ocean_war"),
    Country("YEM", "Yemen", 1050, "Sana'a", "aubm_v4_indian_ocean_war"),
    Country("OMN", "Oman", 1052, "Muscat", "aubm_v4_indian_ocean_war"),
    Country("AFG", "Afghanistan", 2171, "Kabul", "aubm_v4_barbarossa_reaction"),
    Country("TIB", "Tibet", 1289, "Lhasa", "aubm_v4_grand_strategy"),
    Country("SIK", "Xinjiang", 1281, "Urumqi", "aubm_v4_grand_strategy"),
    Country("CHI", "China", 1337, "Nanjing"),
    Country("CHC", "Communist China", 1354, "Yan'an"),
    Country("SIA", "Siam", 1423, "Bangkok", "aubm_v4_indian_ocean_war"),
    Country("U03", "Indochinese Union", 1395, "Hanoi"),
    Country("BUR", "Burma", 1415, "Rangoon"),
    Country("MLY", "Malaysia", 1438, "Kuala Lumpur"),
    Country("PHI", "Philippines", 1565, "Manila"),
    Country("U05", "Dutch East Indies", 1647, "Batavia", "aubm_v4_indian_ocean_war", "INO"),
    Country("INO", "Indonesia", 1654, "Jogjakarta", "aubm_v4_indian_ocean_war"),
    Country("BRU", "Brunei", 1625, "Bandar Seri Begawan"),
    Country("SAR", "Sarawak", 1624, "Kuching"),
    Country("AST", "Australia", 1707, "Canberra"),
    Country("NZL", "New Zealand", 1721, "Wellington"),
    Country("TUR", "Turkey", 1075, "Ankara"),
    Country("ITA", "Italy", 419, "Rome"),
    Country("FRA", "France", 55, "Paris"),
    Country("POR", "Portugal", 476, "Lisbon"),
    Country("ETH", "Ethiopia", 825, "Addis Ababa"),
    Country("SAF", "South Africa", 876, "Pretoria"),
)


def cmd(body: str, trigger: str | None = None) -> str:
    prefix = f"trigger = {{ {trigger} }} " if trigger else ""
    return f"\t\tcommand = {{ {prefix}type = {body} }}"


def live(country: Country) -> str:
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


def common_finish(country: Country, outcome: str) -> list[str]:
    return [
        cmd(f"setflag which = ind_country_resolution_{country.key}_{outcome}"),
        cmd(f"setflag which = ind_country_resolution_{country.key}_complete"),
        cmd(f"clrflag which = ind_aubm_regional_pending_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_current_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_victory_{country.key}"),
        cmd(f"clrflag which = ind_aubm_regional_suspended_{country.key}"),
    ]


def resolution(index: int, country: Country) -> str:
    event_id = BASE_ID + index * 2
    callback_id = event_id + 1
    conditions = f"OR = {{ AND = {{ {live(country)} }} AND = {{ {annexed(country)} }} }}"
    lines = [
        "event = {",
        f"\tid = {event_id}",
        "\trandom = no",
        "\tpersistent = yes",
        "\tcountry = IND",
        f'\tname = "{country.name}: Decide the Peace"',
        (
            f'\tdesc = "India controls {country.seat} and {country.name} has lost at least half of its national territory. '
            f'This decision changes {country.name} only. It cannot end, suspend or alter any other war."'
        ),
        "\tstyle = 2",
        f'\tpicture = "{country.picture}"',
        (
            f"\tdecision = {{ ai = no NOT = {{ flag = ind_country_resolution_{country.key}_complete }} "
            f"{conditions} }}"
        ),
        (
            f"\tdecision_trigger = {{ ai = no NOT = {{ flag = ind_country_resolution_{country.key}_complete }} "
            f"{conditions} }}"
        ),
        "\taction_a = {",
        '\t\tname = "Protectorate: -250 supplies, no dissent; joins wars"',
        cmd(f"inherit which = {country.tag}", f"exists = {country.tag} war = {{ country = IND country = {country.tag} }}"),
        cmd(f"independence which = {country.released} value = 1 when = 0"),
        cmd(f"make_puppet which = {country.released}", f"exists = {country.released}"),
        cmd("supplies value = -250"),
    ]
    lines.extend(common_finish(country, "protected"))
    lines.extend(
        [
            "\t}",
            "\taction_b = {",
            '\t\tname = "Independent partner: -1 dissent; Indian access"',
            cmd(f"inherit which = {country.tag}", f"exists = {country.tag} war = {{ country = IND country = {country.tag} }}"),
            cmd(f"independence which = {country.released} value = 1 when = 0"),
            cmd(f"make_puppet which = {country.released}", f"exists = {country.released}"),
            cmd(f"end_mastery which = {country.released}", f"exists = {country.released}"),
            cmd("dissent value = -1"),
            cmd(f"event which = {callback_id} where = {country.released} when = 1", f"exists = {country.released}"),
        ]
    )
    lines.extend(common_finish(country, "independent"))
    lines.extend(
        [
            "\t}",
            "\taction_c = {",
            f"\t\ttrigger = {{ {live(country)} }}",
            '\t\tname = "Continue the war; make no settlement"',
            "\t}",
            "\taction_d = {",
            f"\t\ttrigger = {{ {annexed(country)} }}",
            '\t\tname = "Military rule: +2 dissent; local resistance"',
            cmd("dissent value = 2"),
            cmd("belligerence value = 1"),
            cmd(f"province_revoltrisk which = {country.capital} value = 2"),
        ]
    )
    lines.extend(common_finish(country, "occupied"))
    lines.extend(["\t}", "}", "", "event = {", f"\tid = {callback_id}", "\trandom = no", "\tone_action = yes", f"\tcountry = {country.released}", f'\tname = "{country.name} Grants India Military Access"', f'\tdesc = "The new government of {country.name} remains independent and grants Indian forces military access."', "\tstyle = 2", f'\tpicture = "{country.picture}"', "\taction_a = {", '\t\tname = "Confirm the agreement"', cmd("access which = IND"), cmd("relation which = IND value = 30"), "\t}", "}"])
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
\tname = "{name}: India Can End Its War"
\tdesc = "{explanation} India may now make a separate peace with {name}. This ends only India's war with {name}; India's other wars continue."
\tstyle = 2
\tpicture = "aubm_v4_liberated_territory"
\tdecision = {{ ai = no {condition} }}
\tdecision_trigger = {{ ai = no {condition} }}
\taction_a = {{
\t\tname = "Separate peace: -3 dissent; +300 money"
\t\tcommand = {{ type = peace which = {tag} value = 1 }}
\t\tcommand = {{ type = dissent value = -3 }}
\t\tcommand = {{ type = money value = 300 }}
\t\tcommand = {{ type = setflag which = ind_country_resolution_major_{key} }}
\t\tcommand = {{ trigger = {{ atwar = no }} type = setflag which = ind_aubm_postwar_congress_completed }}{legacy}
\t}}
\taction_b = {{
\t\tname = "Continue the war with {name}"
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
    sections.extend(major_resolution(*row) for row in MAJOR_EVENTS)
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
