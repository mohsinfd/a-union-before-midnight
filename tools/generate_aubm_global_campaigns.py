#!/usr/bin/env python3
"""Generate AUBM's fallback lifecycle for baseline and emergent states."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "mod/db/events/aubm_v4/47_global_campaign_matrix.txt"

WORLD_INDEX_ID = 9282300
MENU_FIRST_ID = 9285800
ARMISTICE_LAPSE_ID = 9283306
DECLARATION_CALLBACK_BASE = 9286100
ARMISTICE_ACCEPT_BASE = 9286400
ARMISTICE_COUNTER_BASE = 9286700
ARMISTICE_REFUSE_BASE = 9287000
ARMISTICE_LAPSE_BASE = 9287300
CORE_COUNTRY_COUNT = 99
CORE_LIFECYCLE_BASES = (9282400, 9282500, 9282600, 9282700, 9282800, 9282900, 9283000, 9283100)
EXTENSION_LIFECYCLE_BASES = (9283400, 9283600, 9283800, 9284000, 9284200, 9284400, 9284600, 9284800)
ANNEX_MONITOR_BASE = 9285200
RETRY_RELEASE_BASE = 9285500


@dataclass(frozen=True)
class Country:
    tag: str
    name: str
    capital: int
    seat: str
    group: str
    dissent: int

    @property
    def key(self) -> str:
        return self.tag.lower()


# Capital IDs are taken from AUBM's installed 1933 scenario and map-aligned
# revolt file. Countries already receiving bespoke campaigns in modules 35 and
# 41-46 are intentionally excluded. The second part of the table covers the
# standard successor, civil-war and liberation tags that can appear later.
CORE_COUNTRIES = (
    Country("ALB", "Albania", 359, "Tirana", "Europe", 3),
    Country("AUS", "Austria", 195, "Vienna", "Europe", 3),
    Country("BEL", "Belgium", 116, "Brussels", "Europe", 3),
    Country("BUL", "Bulgaria", 321, "Sofia", "Europe", 3),
    Country("CZE", "Czechoslovakia", 207, "Prague", "Europe", 3),
    Country("U06", "Danzig", 181, "Danzig", "Europe", 2),
    Country("DEN", "Denmark", 294, "Copenhagen", "Europe", 3),
    Country("EST", "Estonia", 270, "Tallinn", "Europe", 3),
    Country("FIN", "Finland", 525, "Helsinki", "Europe", 4),
    Country("GRE", "Greece", 377, "Athens", "Europe", 3),
    Country("HUN", "Hungary", 284, "Budapest", "Europe", 3),
    Country("IRE", "Ireland", 34, "Dublin", "Europe", 3),
    Country("LAT", "Latvia", 264, "Riga", "Europe", 3),
    Country("LIT", "Lithuania", 262, "Kaunas", "Europe", 3),
    Country("LUX", "Luxembourg", 109, "Luxembourg", "Europe", 2),
    Country("NOR", "Norway", 483, "Oslo", "Europe", 4),
    Country("POL", "Poland", 232, "Warsaw", "Europe", 4),
    Country("ROM", "Romania", 316, "Bucharest", "Europe", 3),
    Country("SPR", "Spain", 460, "Madrid", "Europe", 4),
    Country("SWE", "Sweden", 2159, "Stockholm", "Europe", 4),
    Country("SCH", "Switzerland", 392, "Bern", "Europe", 5),
    Country("YUG", "Yugoslavia", 338, "Belgrade", "Europe", 3),
    Country("SPA", "Spanish State", 451, "Burgos", "Europe", 4),
    Country("DDR", "German Democratic Republic", 163, "Berlin", "Europe", 4),
    Country("DFR", "Federal Republic of Germany", 131, "Cologne", "Europe", 4),
    Country("RSI", "Italian Social Republic", 407, "Milan", "Europe", 4),
    Country("CRO", "Croatia", 352, "Zagreb", "Europe", 3),
    Country("SER", "Serbia", 338, "Belgrade", "Europe", 3),
    Country("MTN", "Montenegro", 332, "Cetinje", "Europe", 3),
    Country("SLO", "Slovakia", 208, "Bratislava", "Europe", 3),
    Country("BOS", "Bosnia", 355, "Sarajevo", "Europe", 3),
    Country("SLV", "Slovenia", 349, "Ljubljana", "Europe", 3),
    Country("SCO", "Scotland", 12, "Edinburgh", "Europe", 4),
    Country("FLA", "Flanders", 116, "Brussels", "Europe", 3),
    Country("WLL", "Wallonia", 113, "Namur", "Europe", 3),
    Country("UKR", "Ukraine", 617, "Kiev", "Europe", 4),
    Country("BLR", "Byelorussia", 599, "Minsk", "Europe", 4),
    Country("BHU", "Bhutan", 1456, "Thimphu", "Asia", 3),
    Country("CGX", "Guangxi", 1378, "Nanning", "Asia", 3),
    Country("UPE", "East Turkestan", 1279, "Kashgar", "Asia", 3),
    Country("CSX", "Shanxi", 1252, "Taiyuan", "Asia", 3),
    Country("CXB", "Xibei San Ma", 1264, "Xining", "Asia", 3),
    Country("CYN", "Yunnan", 1390, "Kunming", "Asia", 3),
    Country("U03", "Indochinese Union", 1395, "Hanoi", "Asia", 3),
    Country("MAN", "Manchukuo", 1208, "Xinjing", "Asia", 4),
    Country("MON", "Mongolia", 1124, "Ulaanbaatar", "Asia", 4),
    Country("NEP", "Nepal", 1457, "Kathmandu", "Asia", 3),
    Country("TAN", "Tannu Tuva", 1119, "Kyzyl", "Asia", 4),
    Country("ARM", "Armenia", 711, "Yerevan", "Asia", 3),
    Country("AZB", "Azerbaijan", 713, "Baku", "Asia", 3),
    Country("GEO", "Georgia", 709, "Tbilisi", "Asia", 3),
    Country("KAZ", "Kazakhstan", 506, "Taldy-Kurgan", "Asia", 4),
    Country("UZB", "Uzbekistan", 1103, "Tashkent", "Asia", 4),
    Country("TAJ", "Tajikistan", 1105, "Dushanbe", "Asia", 3),
    Country("KYG", "Kyrgyzstan", 1107, "Frunze", "Asia", 3),
    Country("TRK", "Turkmenistan", 1097, "Ashkhabad", "Asia", 3),
    Country("MEN", "Mengjiang", 1246, "Zhangyuan", "Asia", 3),
    Country("U74", "Imperial China", 1247, "Beijing", "Asia", 4),
    Country("U87", "Nanjing China", 1337, "Nanjing", "Asia", 4),
    Country("KOR", "Korea", 1228, "Seoul", "Asia", 4),
    Country("PRK", "People's Republic of Korea", 1221, "Pyeongyang", "Asia", 4),
    Country("PHI", "Philippines", 1565, "Manila", "Asia", 4),
    Country("MLY", "Malaysia", 1438, "Kuala Lumpur", "Asia", 3),
    Country("BUR", "Burma", 1415, "Rangoon", "Asia", 3),
    Country("LAO", "Laos", 1405, "Vientiane", "Asia", 3),
    Country("CMB", "Cambodia", 1401, "Siem Reap", "Asia", 3),
    Country("VIE", "State of Vietnam", 1399, "Saigon", "Asia", 3),
    Country("ISR", "Israel", 1008, "Tel Aviv", "Asia", 4),
    Country("JOR", "Jordan", 1022, "Amman", "Asia", 3),
    Country("LEB", "Lebanon", 1019, "Beirut", "Asia", 3),
    Country("SYR", "Syria", 1016, "Damascus", "Asia", 3),
    Country("PAK", "Pakistan", 1533, "Karachi", "Asia", 4),
    Country("ARG", "Argentina", 2050, "Buenos Aires", "Americas", 5),
    Country("BOL", "Bolivia", 2020, "La Paz", "Americas", 4),
    Country("BRA", "Brazil", 2075, "Rio de Janeiro", "Americas", 5),
    Country("CAN", "Canada", 2108, "Ottawa", "Americas", 5),
    Country("CHL", "Chile", 2023, "Santiago", "Americas", 5),
    Country("COL", "Colombia", 1991, "Bogota", "Americas", 4),
    Country("COS", "Costa Rica", 2081, "San Jose", "Americas", 4),
    Country("CUB", "Cuba", 1776, "Havana", "Americas", 5),
    Country("DOM", "Dominican Republic", 1780, "Santo Domingo", "Americas", 4),
    Country("ECU", "Ecuador", 2042, "Quito", "Americas", 4),
    Country("GUA", "Guatemala", 2088, "Guatemala City", "Americas", 4),
    Country("HAI", "Haiti", 1781, "Port-au-Prince", "Americas", 4),
    Country("HON", "Honduras", 2085, "Tegucigalpa", "Americas", 4),
    Country("MEX", "Mexico", 1974, "Mexico City", "Americas", 5),
    Country("NIC", "Nicaragua", 2080, "Managua", "Americas", 4),
    Country("PAN", "Panama", 2078, "Panama City", "Americas", 5),
    Country("PAR", "Paraguay", 2047, "Asuncion", "Americas", 4),
    Country("PRU", "Peru", 2016, "Lima", "Americas", 4),
    Country("SAL", "El Salvador", 2079, "San Salvador", "Americas", 4),
    Country("U60", "Newfoundland", 2137, "St. John's", "Americas", 4),
    Country("URU", "Uruguay", 2052, "Montevideo", "Americas", 4),
    Country("VEN", "Venezuela", 1993, "Caracas", "Americas", 4),
    Country("GUY", "Guyana", 1997, "Georgetown", "Americas", 4),
    Country("EGY", "Egypt", 787, "Cairo", "Africa", 3),
    Country("LIB", "Liberia", 969, "Monrovia", "Africa", 4),
    Country("U04", "Syria and Lebanon", 1019, "Damascus", "Africa", 3),
    Country("LBY", "Libya", 750, "Tripoli", "Africa", 4),
)

EXTENSION_COUNTRIES = (
    Country("CYP", "Cyprus", 388, "Nicosia", "Europe", 4),
    Country("EUS", "Euskadi", 443, "Bilbao", "Europe", 4),
    Country("ICL", "Iceland", 1, "Reykjavik", "Europe", 4),
    Country("OTT", "Ottoman Empire", 409, "Istanbul", "Europe", 5),
    Country("RUS", "Russia", 553, "Leningrad", "Europe", 5),
    Country("SCA", "Scandinavia", 2159, "Stockholm", "Europe", 5),
    Country("U01", "Free France", 55, "Paris", "Europe", 4),
    Country("U10", "Dutch Socialist Union", 122, "Amsterdam", "Europe", 4),
    Country("U11", "People's Republic of France", 55, "Paris", "Europe", 4),
    Country("U12", "English Republic", 29, "London", "Europe", 4),
    Country("U13", "Hungarian Socialist Republic", 284, "Budapest", "Europe", 4),
    Country("U14", "Italian Union", 419, "Rome", "Europe", 4),
    Country("U15", "Socialist Portugal", 476, "Lisbon", "Europe", 4),
    Country("U16", "Austrian Democratic Republic", 195, "Vienna", "Europe", 4),
    Country("U17", "People's Republic of Belgium", 116, "Brussels", "Europe", 4),
    Country("U18", "Luxembourg Republic", 109, "Luxembourg", "Europe", 3),
    Country("U19", "People's Republic of Norway", 483, "Oslo", "Europe", 4),
    Country("U20", "Finnish Democratic Republic", 525, "Helsinki", "Europe", 4),
    Country("U21", "Swedish Socialist Union", 2159, "Stockholm", "Europe", 4),
    Country("U22", "People's Republic of Denmark", 294, "Copenhagen", "Europe", 4),
    Country("U23", "Saar Protectorate", 127, "Saarbrucken", "Europe", 3),
    Country("U24", "Allied Germany", 131, "Cologne", "Europe", 4),
    Country("U25", "Soviet Germany", 163, "Berlin", "Europe", 4),
    Country("U26", "Swiss Socialist Republic", 392, "Bern", "Europe", 4),
    Country("U27", "Socialist Yugoslavia", 338, "Belgrade", "Europe", 4),
    Country("U28", "Socialist Albania", 359, "Tirana", "Europe", 3),
    Country("U29", "People's Republic of Bulgaria", 321, "Sofia", "Europe", 4),
    Country("U30", "Romanian People's Republic", 316, "Bucharest", "Europe", 4),
    Country("U31", "Socialist Czechoslovakia", 207, "Prague", "Europe", 4),
    Country("U32", "People's Republic of Poland", 232, "Warsaw", "Europe", 4),
    Country("U33", "Democratic Republic of Greece", 377, "Athens", "Europe", 4),
    Country("U35", "Democratic Spanish Union", 460, "Madrid", "Europe", 4),
    Country("U40", "Ostland", 264, "Riga", "Europe", 4),
    Country("U41", "Ukraine Commissariat", 244, "Rowne", "Europe", 4),
    Country("U43", "Moscow Commissariat", 572, "Moscow", "Europe", 4),
    Country("U44", "General Government", 235, "Krakow", "Europe", 4),
    Country("U45", "Norway Commissariat", 483, "Oslo", "Europe", 4),
    Country("U46", "Netherlands Commissariat", 122, "Amsterdam", "Europe", 4),
    Country("U47", "Belgien-Nordfrankreich", 116, "Brussels", "Europe", 4),
    Country("U71", "Northern Ireland", 36, "Belfast", "Europe", 4),
    Country("U73", "England", 29, "London", "Europe", 4),
    Country("U76", "Wales", 22, "Cardiff", "Europe", 4),
    Country("U92", "Malta", 429, "Malta", "Europe", 4),
    Country("BRU", "Brunei", 1625, "Bandar Seri Begawan", "Asia", 3),
    Country("IDC", "Indochina", 1395, "Hanoi", "Asia", 3),
    Country("INO", "Indonesia", 1654, "Jogjakarta", "Asia", 4),
    Country("KUR", "Kurdistan", 1036, "Kirkuk", "Asia", 3),
    Country("PAL", "Palestine", 1172, "Jerusalem", "Asia", 4),
    Country("PRI", "Primorsk", 1191, "Vladivostok", "Asia", 4),
    Country("SAR", "Sarawak", 1624, "Kuching", "Asia", 3),
    Country("SIB", "Siberia", 1142, "Novosibirsk", "Asia", 5),
    Country("TRA", "Transural Republic", 1137, "Kurgan", "Asia", 4),
    Country("U02", "British Raj", 1459, "Delhi", "Asia", 5),
    Country("U34", "Socialist Turkey", 1075, "Ankara", "Asia", 4),
    Country("U39", "Hatay State", 1054, "Antakya", "Asia", 3),
    Country("U42", "Caucasus Commissariat", 709, "Tbilisi", "Asia", 4),
    Country("U48", "Turkestan Commissariat", 1070, "Kachug", "Asia", 4),
    Country("U50", "Hejaz", 1048, "Medina", "Asia", 3),
    Country("U51", "Qatar", 1038, "Doha", "Asia", 3),
    Country("U53", "Trucial States", 1039, "Abu Dhabi", "Asia", 3),
    Country("U72", "Democratic Vietnam", 1393, "Hoa Binh", "Asia", 3),
    Country("U75", "Singapore", 1432, "Singapore", "Asia", 4),
    Country("U80", "Kashmir", 1540, "Srinagar", "Asia", 4),
    Country("U83", "Ceylon", 1511, "Colombo", "Asia", 4),
    Country("U91", "Kuwait", 1041, "Kuwait", "Asia", 3),
    Country("CAL", "California", 1888, "Sacramento", "Americas", 5),
    Country("CSA", "Confederate States", 1813, "Richmond", "Americas", 5),
    Country("QUE", "Quebec", 2117, "Quebec", "Americas", 5),
    Country("TEX", "Texas", 1925, "Austin", "Americas", 5),
    Country("U77", "Greater Colombia", 1991, "Santa Fe de Bogota", "Americas", 5),
    Country("U78", "Central America", 2079, "San Salvador", "Americas", 5),
    Country("U79", "West Indies", 1758, "Trinidad", "Americas", 5),
    Country("U89", "Jamaica", 1782, "Jamaica", "Americas", 4),
    Country("U98", "Trinidad and Tobago", 1758, "Trinidad", "Americas", 4),
    Country("ALG", "Algeria", 727, "Algiers", "Africa", 4),
    Country("ANG", "Angola", 895, "Luanda", "Africa", 4),
    Country("ARA", "Arab Federation", 787, "Cairo", "Africa", 4),
    Country("BEN", "Benin-Sahel", 951, "Cotonou", "Africa", 4),
    Country("CAM", "Cameroon", 909, "Yaounde", "Africa", 4),
    Country("CON", "Congo", 899, "Leopoldville", "Africa", 4),
    Country("EAF", "East African Union", 850, "Dar es Salaam", "Africa", 4),
    Country("EQA", "Equatorial Africa", 926, "Bangui", "Africa", 4),
    Country("GAB", "Gabon", 915, "Libreville", "Africa", 4),
    Country("GLD", "Ghana", 956, "Accra", "Africa", 4),
    Country("GUI", "Guinea", 966, "Conakry", "Africa", 4),
    Country("MAD", "Madagascar", 1001, "Tananarive", "Africa", 4),
    Country("MAL", "Union of Mali", 976, "Bamako", "Africa", 4),
    Country("MOR", "Morocco", 717, "Rabat", "Africa", 4),
    Country("MOZ", "Mozambique", 855, "Lourenco Marques", "Africa", 4),
    Country("NAM", "Namibia", 884, "Windhoek", "Africa", 4),
    Country("NIG", "Nigeria", 929, "Lagos", "Africa", 4),
    Country("RHO", "Rhodesia-Nyasaland", 867, "Salisbury", "Africa", 4),
    Country("SIE", "Sierra Leone", 964, "Freetown", "Africa", 4),
    Country("SOM", "Somalia", 836, "Mogadishu", "Africa", 4),
    Country("SUD", "Sudan", 810, "Khartoum", "Africa", 4),
    Country("TUN", "Tunisia", 747, "Tunis", "Africa", 4),
    Country("U49", "Italian East Africa", 825, "Addis Ababa", "Africa", 4),
    Country("U70", "Uganda", 844, "Kampala", "Africa", 4),
    Country("U81", "Upper Volta", 957, "Ouagadougou", "Africa", 4),
    Country("U82", "Central Africa", 926, "Bangui", "Africa", 4),
    Country("U84", "Chad", 920, "Fort Lamy", "Africa", 4),
    Country("U85", "Congo-Brazzaville", 907, "Brazzaville", "Africa", 4),
    Country("U86", "Gambia", 979, "Banjul", "Africa", 4),
    Country("U88", "Ivory Coast", 962, "Abidjan", "Africa", 4),
    Country("U90", "Kenya", 841, "Nairobi", "Africa", 4),
    Country("U93", "Mauritania", 981, "Nouakchott", "Africa", 4),
    Country("U94", "Niger", 944, "Niamey", "Africa", 4),
    Country("U95", "Rwanda", 846, "Kigali", "Africa", 4),
    Country("U96", "Senegal", 978, "Dakar", "Africa", 4),
    Country("U97", "Tanganyika", 850, "Dar es Salaam", "Africa", 4),
    Country("U99", "Togo", 950, "Lome", "Africa", 4),
)

COUNTRIES = CORE_COUNTRIES + EXTENSION_COUNTRIES

assert len(CORE_COUNTRIES) == CORE_COUNTRY_COUNT, "core country IDs must remain stable"
assert len(EXTENSION_COUNTRIES) < 200, "extension lifecycle bands support at most 199 countries"


@dataclass(frozen=True)
class LifecycleIds:
    brief: int
    victory: int
    reversal: int
    recovery: int
    normal_response: int
    docket: int
    backed_response: int
    settlement: int
    annex_monitor: int
    retry_release: int
    declaration: int
    accept: int
    counter: int
    refuse: int
    lapse: int


def lifecycle_ids(index: int) -> LifecycleIds:
    if index < CORE_COUNTRY_COUNT:
        offset = index
        bases = CORE_LIFECYCLE_BASES
    else:
        offset = index - CORE_COUNTRY_COUNT
        bases = EXTENSION_LIFECYCLE_BASES
    phases = tuple(base + offset for base in bases)
    return LifecycleIds(
        *phases,
        ANNEX_MONITOR_BASE + index,
        RETRY_RELEASE_BASE + index,
        DECLARATION_CALLBACK_BASE + index,
        ARMISTICE_ACCEPT_BASE + index,
        ARMISTICE_COUNTER_BASE + index,
        ARMISTICE_REFUSE_BASE + index,
        ARMISTICE_LAPSE_BASE + index,
    )


PICTURES = {
    "Europe": "aubm_v4_india_world_war",
    "Asia": "aubm_v4_china_interior",
    "Americas": "aubm_v4_indian_ocean_war",
    "Africa": "aubm_v4_liberated_territory",
}


def event_header(event_id: int, country: str = "IND", *, one_action: bool = False) -> list[str]:
    lines = ["event = {", f"\tid = {event_id}", "\trandom = no", "\tpersistent = yes"]
    if one_action:
        lines.append("\tone_action = yes")
    lines.append(f"\tcountry = {country}")
    return lines


def menu_events() -> str:
    out: list[str] = []
    groups = ["Europe", "Asia", "Americas", "Africa"]
    pages: dict[str, list[tuple[int, tuple[Country, ...]]]] = {}
    next_id = MENU_FIRST_ID
    for group in groups:
        members = tuple(c for c in COUNTRIES if c.group == group)
        chunks = tuple(members[i : i + 3] for i in range(0, len(members), 3))
        pages[group] = []
        for chunk in chunks:
            pages[group].append((next_id, chunk))
            next_id += 1

    out.extend(event_header(WORLD_INDEX_ID))
    out.extend(
        [
            '\tname = "War Cabinet: Every Sovereign State"',
            '\tdesc = "Every baseline state and standard wartime successor not already covered by a bespoke theatre appears here. Diplomatic route and enemy are independent: Allied, German, Soviet, Japanese and sovereign India may open any listed campaign. Each war receives a brief, live capital objective, reversal, recovery, armistice and post-annexation constitutional settlement."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_grand_strategy"',
        ]
    )
    for letter, group in zip("abcd", groups):
        first = pages[group][0][0]
        out.extend(
            [
                f"\taction_{letter} = {{",
                f'\t\tname = "{group} campaign index"',
                f"\t\tcommand = {{ type = event which = {first} where = IND when = 1 }}",
                "\t}",
            ]
        )
    out.extend(["}", ""])

    for group in groups:
        group_pages = pages[group]
        for page_no, (event_id, chunk) in enumerate(group_pages):
            out.extend(event_header(event_id))
            out.extend(
                [
                    f'\tname = "War Cabinet: {group} Campaigns {page_no + 1}/{len(group_pages)}"',
                    '\tdesc = "Selecting a target is a deliberate declaration. If it shares India\'s formal alliance, India first leaves that alliance and inherited wars; the declaration follows one day later. The selected enemy then enters the same audited campaign lifecycle used by every diplomatic route."',
                    "\tstyle = 2",
                    f'\tpicture = "{PICTURES[group]}"',
                ]
            )
            for letter, country in zip("abc", chunk):
                country_ids = lifecycle_ids(COUNTRIES.index(country))
                out.extend(
                    [
                        f"\taction_{letter} = {{",
                        f"\t\ttrigger = {{ exists = {country.tag} NOT = {{ war = {{ country = IND country = {country.tag} }} }} }}",
                        f'\t\tname = "War with {country.name}: +{country.dissent} dissent"',
                        f"\t\tcommand = {{ trigger = {{ alliance = {{ country = IND country = {country.tag} }} }} type = leave_alliance when = 1 }}",
                        f"\t\tcommand = {{ type = dissent value = {country.dissent} }}",
                        f"\t\tcommand = {{ type = event which = {country_ids.declaration} where = IND when = 1 }}",
                        "\t}",
                    ]
                )
            next_page = group_pages[page_no + 1][0] if page_no + 1 < len(group_pages) else WORLD_INDEX_ID
            label = "Next page" if page_no + 1 < len(group_pages) else "Return to the world index"
            out.extend(
                [
                    "\taction_d = {",
                    f'\t\tname = "{label}"',
                    f"\t\tcommand = {{ type = event which = {next_page} where = IND when = 1 }}",
                    "\t}",
                    "}",
                    "",
                ]
            )
    return "\n".join(out)


def lapse_detector() -> str:
    out = event_header(ARMISTICE_LAPSE_ID, one_action=True)
    out.extend(
        [
            "\ttrigger = {",
            "\t\tflag = ind_aubm_universal_armistice_outstanding",
            "\t\tOR = {",
        ]
    )
    for index, country in enumerate(COUNTRIES):
        out.append(
            f"\t\t\tAND = {{ flag = ind_aubm_armistice_target_{country.key} NOT = {{ exists = {country.tag} }} }}"
        )
    out.extend(
        [
            "\t\t}",
            "\t}",
            '\tname = "A Negotiating Government Vanishes"',
            '\tdesc = "A government answering Delhi has ceased to exist before its reply arrives. The country-specific audit will preserve an Indian annexation claim or reset a third-party disappearance without blocking any other peace file."',
            "\tstyle = 2",
            '\tpicture = "aubm_v4_liberated_territory"',
            "\tdate = { day = 0 month = january year = 1933 }",
            "\toffset = 1",
            "\tdeathdate = { day = 29 month = december year = 1964 }",
            "\taction_a = {",
            '\t\tname = "Route the vanished file to its own audit"',
        ]
    )
    for index, country in enumerate(COUNTRIES):
        ids = lifecycle_ids(index)
        out.append(
            f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_armistice_target_{country.key} NOT = {{ exists = {country.tag} }} }} type = event which = {ids.lapse} where = IND when = 1 }}"
        )
    out.extend(["\t}", "}"])
    return "\n".join(out)


def coalition_to_compact_lines() -> list[str]:
    return [
        "\t\tcommand = { trigger = { OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } } } type = setflag which = ind_v4a_treaty_cobelligerent }",
        "\t\tcommand = { trigger = { OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } } } type = clrflag which = ind_v4a_treaty_formal_alliance }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = GER } } type = setflag which = ind_gc_cobelligerent }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = GER } } type = clrflag which = ind_gc_formal_axis }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = SOV } } type = setflag which = ind_v4_sov_equal_compact }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = SOV } } type = clrflag which = ind_v4_sov_supervised_compact }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = JAP } } type = setflag which = ind_aubm_jp_partnership }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = JAP } } type = setflag which = ind_aubm_jp_independent_cobelligerent }",
        "\t\tcommand = { trigger = { alliance = { country = IND country = JAP } } type = clrflag which = ind_aubm_jp_formal_alliance }",
    ]


def negotiated_cleanup_lines(country: Country) -> list[str]:
    key = country.key
    return [
        f"\t\tcommand = {{ type = setflag which = ind_aubm_global_settled_{key} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_global_negotiated_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_pending_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_active_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_victory_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_current_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_suspended_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
        "\t\tcommand = { type = clrflag which = ind_aubm_universal_armistice_outstanding }",
        "\t\tcommand = { type = clrflag which = ind_v3_joined_allies }",
        "\t\tcommand = { type = clrflag which = ind_v3_joined_axis }",
        "\t\tcommand = { type = clrflag which = ind_v3_joined_comintern }",
        "\t\tcommand = { type = clrflag which = ind_v3_joined_japan }",
    ]


def lifecycle_events() -> str:
    out: list[str] = []
    backed = "OR = { flag = ind_aubm_coalition_credit flag = ind_aubm_coalition_consultation flag = ind_aubm_victory_sovereign_credit flag = ind_aubm_decisive_great_power }"
    for i, country in enumerate(COUNTRIES):
        key = country.key
        picture = PICTURES[country.group]
        ids = lifecycle_ids(i)

        out.extend(event_header(ids.brief))
        out.extend(
            [
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\texists = {country.tag}",
                f"\t\twar = {{ country = IND country = {country.tag} }}",
                f"\t\tNOT = {{ flag = ind_aubm_global_active_{key} }}",
                "\t}",
                f'\tname = "Campaign Brief: {country.name}"',
                f'\tdesc = "The War Cabinet opens a separate {country.group.lower()} ledger. {country.seat} is the first decisive objective. India must control it while {country.name} still owns it, or legally own it after annexation. Alliance choice affects consultation and armistice support, never the battlefield test itself."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 1",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                f'\t\tname = "Open the {country.seat} campaign ledger"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_active_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_settled_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_post_annex_resolved_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.victory))
        out.extend(
            [
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\tNOT = {{ flag = ind_aubm_global_victory_{key} }}",
                "\t\tOR = {",
                f"\t\t\tAND = {{ exists = {country.tag} war = {{ country = IND country = {country.tag} }} owned = {{ province = {country.capital} data = {country.tag} }} control = {{ province = {country.capital} data = IND }} }}",
                f"\t\t\tAND = {{ flag = ind_aubm_global_active_{key} NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} control = {{ province = {country.capital} data = IND }} }}",
                "\t\t}",
                "\t}",
                f'\tname = "Indian Command Secures {country.seat}"',
                f'\tdesc = "India has taken the published objective against {country.name}, or completed annexation and now legally owns it. The result immediately opens armistice terms while the government survives, or a sovereign, protected or direct constitutional settlement after annexation."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 1",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                '\t\tname = "Record the result and open the settlement file"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_pending_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_active_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_victory_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_current_{key} }}",
                "\t\tcommand = { type = setflag which = ind_aubm_global_campaign_victory }",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ flag = ind_aubm_global_rewarded_{key} }} }} type = dissent value = -1 }}",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ flag = ind_aubm_global_rewarded_{key} }} }} type = money value = 50 }}",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ flag = ind_aubm_global_rewarded_{key} }} }} type = event which = 9282170 where = IND when = 1 }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_rewarded_{key} }}",
                f"\t\tcommand = {{ trigger = {{ exists = {country.tag} war = {{ country = IND country = {country.tag} }} }} type = event which = {ids.docket} where = IND when = 2 }}",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} }} type = setflag which = ind_aubm_global_post_annex_resolved_{key} }}",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} }} type = event which = {ids.settlement} where = IND when = 2 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.reversal))
        out.extend(
            [
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\tflag = ind_aubm_global_current_{key}",
                f"\t\texists = {country.tag}",
                f"\t\twar = {{ country = IND country = {country.tag} }}",
                f"\t\towned = {{ province = {country.capital} data = {country.tag} }}",
                f"\t\tNOT = {{ control = {{ province = {country.capital} data = IND }} }}",
                "\t}",
                f'\tname = "The {country.seat} Settlement Claim Is Suspended"',
                f'\tdesc = "India no longer controls the published objective against {country.name}. The victory remains historical, but no armistice or occupation order can use it until Indian command recovers {country.seat}."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 2",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                '\t\tname = "Suspend current leverage"',
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_current_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_suspended_{key} }}",
                "\t\tcommand = { type = dissent value = 1 }",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.recovery))
        out.extend(
            [
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\tflag = ind_aubm_global_suspended_{key}",
                f"\t\texists = {country.tag}",
                f"\t\twar = {{ country = IND country = {country.tag} }}",
                f"\t\towned = {{ province = {country.capital} data = {country.tag} }}",
                f"\t\tcontrol = {{ province = {country.capital} data = IND }}",
                "\t}",
                f'\tname = "Indian Command Recovers {country.seat}"',
                f'\tdesc = "India again controls the published objective against {country.name}. Current leverage is restored and the country-specific settlement docket returns."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 2",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                '\t\tname = "Restore the live claim"',
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_suspended_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_current_{key} }}",
                "\t\tcommand = { type = dissent value = -1 }",
                f"\t\tcommand = {{ type = event which = {ids.docket} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        for response_id, odds in ((ids.normal_response, (60, 25, 15)), (ids.backed_response, (75, 20, 5))):
            response_live = (
                f"war = {{ country = IND country = {country.tag} }} "
                f"owned = {{ province = {country.capital} data = {country.tag} }} "
                f"control = {{ province = {country.capital} data = IND }}"
            )
            out.extend(event_header(response_id, country.tag))
            out.extend(
                [
                    '\tname = "India Offers a Country-Specific Armistice"',
                    f'\tdesc = "Delhi presents terms after verified control of {country.seat}. The fixed response is accept {odds[0]}%, counter with peace but no access {odds[1]}%, refuse {odds[2]}%. If India loses the objective before the answer, refusal becomes the only valid response. Delhi alone ratifies peace."',
                    "\tstyle = 2",
                    f'\tpicture = "{picture}"',
                    "\taction_a = {",
                    f"\t\ttrigger = {{ {response_live} }}",
                    f"\t\tai_chance = {odds[0]}",
                    '\t\tname = "Accept peace and reciprocal Indian access"',
                    "\t\tcommand = { type = access which = IND }",
                    "\t\tcommand = { type = relation which = IND value = 20 }",
                    f"\t\tcommand = {{ type = event which = {ids.accept} where = IND when = 3 }}",
                    "\t}",
                    "\taction_b = {",
                    f"\t\ttrigger = {{ {response_live} }}",
                    f"\t\tai_chance = {odds[1]}",
                    '\t\tname = "Counter with peace but no access"',
                    "\t\tcommand = { type = relation which = IND value = 5 }",
                    f"\t\tcommand = {{ type = event which = {ids.counter} where = IND when = 3 }}",
                    "\t}",
                    "\taction_c = {",
                    f"\t\tai_chance = {odds[2]}",
                    '\t\tname = "Refuse and continue the war"',
                    "\t\tcommand = { type = relation which = IND value = -10 }",
                    f"\t\tcommand = {{ type = event which = {ids.refuse} where = IND when = 3 }}",
                    "\t}",
                    "}",
                    "",
                ]
            )

        out.extend(event_header(ids.docket))
        out.extend(
            [
                f'\tname = "Armistice Docket: {country.name}"',
                f'\tdesc = "Terms are available only while India has current control of {country.seat}. Base response odds are 60/25/15. Recognized coalition credit, conditioned consultation, sovereign victory credit or decisive great-power standing improves them to 75/20/5. Ratifying separate peace converts any formal coalition to its strategic compact."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
				f"\t\ttrigger = {{ exists = {country.tag} war = {{ country = IND country = {country.tag} }} flag = ind_aubm_global_current_{key} NOT = {{ flag = ind_aubm_universal_armistice_outstanding }} NOT = {{ flag = ind_aubm_armistice_retry_{key} }} }}",
                '\t\tname = "Submit terms: 60/25/15, or 75/20/5 with standing"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_armistice_target_{key} }}",
                "\t\tcommand = { type = setflag which = ind_aubm_universal_armistice_outstanding }",
                f"\t\tcommand = {{ trigger = {{ {backed} }} type = event which = {ids.backed_response} where = {country.tag} when = 3 }}",
                f"\t\tcommand = {{ trigger = {{ NOT = {{ {backed} }} }} type = event which = {ids.normal_response} where = {country.tag} when = 3 }}",
                "\t}",
                "\taction_b = {",
                f"\t\ttrigger = {{ exists = {country.tag} war = {{ country = IND country = {country.tag} }} }}",
                '\t\tname = "Continue the campaign; review in ninety days"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ type = event which = {ids.retry_release} where = IND when = 90 }}",
                "\t}",
                "\taction_c = {",
                '\t\tname = "Return to the world campaign index"',
                f"\t\tcommand = {{ type = event which = {WORLD_INDEX_ID} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        def cleanup_lines() -> list[str]:
            return [
                f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_armistice_target_{key} }} type = clrflag which = ind_aubm_universal_armistice_outstanding }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_pending_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_active_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_victory_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_current_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_global_suspended_{key} }}",
            ]

        out.extend(event_header(ids.settlement))
        out.extend(
            [
                f'\tname = "Constitutional Settlement of {country.name}"',
                f'\tdesc = "{country.name} no longer exists and India legally owns {country.seat}. Delhi must now restore a sovereign government, establish a protected government at a political cost, retain direct administration with recurring occupation burden, or defer the decision for ninety days."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} }}",
                '\t\tname = "Restore sovereignty: -2 dissent"',
                f"\t\tcommand = {{ type = independence which = {country.tag} value = 1 when = 0 }}",
                f"\t\tcommand = {{ trigger = {{ exists = {country.tag} }} type = guarantee which = IND where = {country.tag} }}",
                "\t\tcommand = { type = dissent value = -2 }",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_sovereign_{key} }}",
            ]
        )
        out.extend(cleanup_lines())
        out.extend(
            [
                "\t}",
                "\taction_b = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} }}",
                '\t\tname = "Establish a protectorate: +4 dissent"',
                f"\t\tcommand = {{ type = independence which = {country.tag} value = 1 when = 0 }}",
                f"\t\tcommand = {{ trigger = {{ exists = {country.tag} }} type = make_puppet which = {country.tag} }}",
                "\t\tcommand = { type = dissent value = 4 }",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_protected_{key} }}",
            ]
        )
        out.extend(cleanup_lines())
        out.extend(
            [
                "\t}",
                "\taction_c = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} owned = {{ province = {country.capital} data = IND }} }}",
                '\t\tname = "Retain direct administration: +7 dissent"',
                "\t\tcommand = { type = dissent value = 7 }",
                "\t\tcommand = { type = belligerence value = 3 }",
                "\t\tcommand = { type = setflag which = ind_aubm_occupation_upkeep }",
				"\t\tcommand = { type = event which = 9282093 where = IND when = 1 }",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_direct_{key} }}",
            ]
        )
        out.extend(cleanup_lines())
        out.extend(
            [
                "\t}",
                "\taction_d = {",
                '\t\tname = "Defer the constitutional decision for ninety days"',
                f"\t\tcommand = {{ type = event which = {ids.settlement} where = IND when = 90 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.annex_monitor, one_action=True))
        out.extend(
            [
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\tflag = ind_aubm_global_active_{key}",
                f"\t\tflag = ind_aubm_global_victory_{key}",
                f"\t\tNOT = {{ exists = {country.tag} }}",
                f"\t\towned = {{ province = {country.capital} data = IND }}",
                f"\t\tNOT = {{ flag = ind_aubm_global_post_annex_resolved_{key} }}",
                "\t}",
                f'\tname = "Annexation Docket: {country.name}"',
                f'\tdesc = "{country.name} disappeared after India had already opened its campaign and secured {country.seat}. The armistice file is cancelled and the constitutional settlement now returns without waiting for global peace."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 2",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                '\t\tname = "Open the constitutional settlement"',
                f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_armistice_target_{key} }} type = clrflag which = ind_aubm_universal_armistice_outstanding }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_post_annex_resolved_{key} }}",
                f"\t\tcommand = {{ type = event which = {ids.settlement} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.retry_release, one_action=True))
        out.extend(
            [
                f'\tname = "Armistice Review Returns: {country.name}"',
                f'\tdesc = "The ninety-day cooling period for {country.name} has expired. If India still holds {country.seat} and the war continues, the country-specific docket reopens; no other negotiation is affected."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                '\t\tname = "Recheck the live claim"',
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ trigger = {{ exists = {country.tag} war = {{ country = IND country = {country.tag} }} flag = ind_aubm_global_current_{key} }} type = event which = {ids.docket} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.declaration, one_action=True))
        out.extend(
            [
                f'\tname = "The Declaration Against {country.name}"',
                f'\tdesc = "India has completed any required coalition withdrawal. If {country.name} still exists and peace remains in force, the Foreign Ministry now opens the authorized war without affecting any unrelated campaign."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                f'\t\tname = "Open the {country.seat} campaign"',
                f"\t\tcommand = {{ trigger = {{ exists = {country.tag} NOT = {{ war = {{ country = IND country = {country.tag} }} }} }} type = war which = {country.tag} }}",
                "\t\tcommand = { type = setflag which = ind_aubm_war_declared_by_cabinet }",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.accept))
        out.extend(
            [
                f'\tname = "{country.name} Accepts Delhi\'s Armistice"',
                f'\tdesc = "{country.name} accepts the published peace and Indian strategic access. Delhi alone ratifies this pairwise settlement; every other Indian war and every earned route achievement remains live."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                f"\t\ttrigger = {{ exists = {country.tag} }}",
                '\t\tname = "Ratify the full country-specific peace"',
            ]
        )
        out.extend(coalition_to_compact_lines())
        out.extend(
            [
                f"\t\tcommand = {{ trigger = {{ war = {{ country = IND country = {country.tag} }} }} type = peace which = {country.tag} value = 1 }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_armistice_full_{key} }}",
                "\t\tcommand = { type = dissent value = -2 }",
            ]
        )
        out.extend(negotiated_cleanup_lines(country))
        out.extend(
            [
                "\t}",
                "\taction_b = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} }}",
                '\t\tname = "The government vanished; audit the settlement"',
                f"\t\tcommand = {{ type = event which = {ids.lapse} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.counter))
        out.extend(
            [
                f'\tname = "{country.name} Counters Delhi\'s Armistice"',
                f'\tdesc = "{country.name} accepts peace but withholds access and wider recognition. India may ratify the limited country-specific settlement or continue operations and reopen only this file after ninety days."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                f"\t\ttrigger = {{ exists = {country.tag} }}",
                '\t\tname = "Ratify limited peace without access"',
            ]
        )
        out.extend(coalition_to_compact_lines())
        out.extend(
            [
                f"\t\tcommand = {{ trigger = {{ war = {{ country = IND country = {country.tag} }} }} type = peace which = {country.tag} value = 1 }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_global_armistice_limited_{key} }}",
                "\t\tcommand = { type = dissent value = -2 }",
            ]
        )
        out.extend(negotiated_cleanup_lines(country))
        out.extend(
            [
                "\t}",
                "\taction_b = {",
                f"\t\ttrigger = {{ exists = {country.tag} }}",
                '\t\tname = "Reject the counteroffer; review in ninety days"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ type = event which = {ids.retry_release} where = IND when = 90 }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
                "\t\tcommand = { type = clrflag which = ind_aubm_universal_armistice_outstanding }",
                "\t}",
                "\taction_c = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} }}",
                '\t\tname = "The government vanished; audit the settlement"',
                f"\t\tcommand = {{ type = event which = {ids.lapse} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        out.extend(event_header(ids.refuse))
        out.extend(
            [
                f'\tname = "{country.name} Refuses Delhi\'s Armistice"',
                f'\tdesc = "{country.name} refuses. India keeps its verified battlefield record, but this country-specific file cannot be submitted again for ninety days."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                f"\t\ttrigger = {{ exists = {country.tag} }}",
                '\t\tname = "Continue the war; reopen this file in ninety days"',
                "\t\tcommand = { type = dissent value = 1 }",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_armistice_retry_{key} }}",
                f"\t\tcommand = {{ type = event which = {ids.retry_release} where = IND when = 90 }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
                "\t\tcommand = { type = clrflag which = ind_aubm_universal_armistice_outstanding }",
                "\t}",
                "\taction_b = {",
                f"\t\ttrigger = {{ NOT = {{ exists = {country.tag} }} }}",
                '\t\tname = "The government vanished; audit the settlement"',
                f"\t\tcommand = {{ type = event which = {ids.lapse} where = IND when = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

        lost_settlement = (
            f"NOT = {{ exists = {country.tag} }} "
            f"NOT = {{ owned = {{ province = {country.capital} data = IND }} }}"
        )
        indian_annexation = (
            f"NOT = {{ exists = {country.tag} }} "
            f"owned = {{ province = {country.capital} data = IND }} "
            f"control = {{ province = {country.capital} data = IND }}"
        )
        out.extend(event_header(ids.lapse, one_action=True))
        out.extend(
            [
                f'\tname = "The {country.name} Armistice File Lapses"',
                f'\tdesc = "{country.name} vanished before its answer reached Delhi. An Indian-owned {country.seat} proceeds to constitutional settlement; a third-party disappearance resets only this interrupted campaign and preserves every historical reward."',
                "\tstyle = 2",
                f'\tpicture = "{picture}"',
                "\taction_a = {",
                '\t\tname = "Close the dead response without blocking another war"',
                f"\t\tcommand = {{ trigger = {{ {lost_settlement} }} type = clrflag which = ind_aubm_global_pending_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {lost_settlement} }} type = clrflag which = ind_aubm_global_active_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {lost_settlement} }} type = clrflag which = ind_aubm_global_victory_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {lost_settlement} }} type = clrflag which = ind_aubm_global_current_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {lost_settlement} }} type = clrflag which = ind_aubm_global_suspended_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {indian_annexation} }} type = setflag which = ind_aubm_global_post_annex_resolved_{key} }}",
                f"\t\tcommand = {{ trigger = {{ {indian_annexation} }} type = event which = {ids.settlement} where = IND when = 1 }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_target_{key} }}",
                f"\t\tcommand = {{ type = clrflag which = ind_aubm_armistice_retry_{key} }}",
                "\t\tcommand = { type = clrflag which = ind_aubm_universal_armistice_outstanding }",
                "\t}",
                "}",
                "",
            ]
        )
    return "\n".join(out)


def render() -> str:
    sections = [
        "#########################################################################\n"
        "# A Union Before Midnight V4: baseline and emergent country campaign fallback\n"
        "# Generated by tools/generate_aubm_global_campaigns.py; do not hand edit.\n"
        "#########################################################################",
        menu_events(),
        lapse_detector(),
        lifecycle_events(),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the generated file is stale")
    args = parser.parse_args()
    generated = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="ascii") != generated:
            print(f"STALE: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"OK: {len(COUNTRIES)} fallback country campaigns are current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generated, encoding="ascii", newline="\n")
    print(f"WROTE: {OUTPUT.relative_to(ROOT)} ({len(COUNTRIES)} countries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
