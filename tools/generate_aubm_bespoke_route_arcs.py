#!/usr/bin/env python3
"""Generate Alpha 23's authored strategic-route campaign overlays.

The opponent, armistice and constitutional-settlement lifecycles remain in
modules 42 and 45-50.  This generator adds the selected route's human-facing
operational story: activation, an intermediate milestone, a strategic
dilemma, culmination, compact-partner consultation and partner collapse.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "mod/db/events/aubm_v4/51_bespoke_route_arcs.txt"
DISPATCHER_ID = 9289499


@dataclass(frozen=True)
class Choice:
    label: str
    flag: str
    commands: tuple[str, ...]


@dataclass(frozen=True)
class Focus:
    key: str
    label: str
    activation_name: str
    activation_desc: str
    activation_condition: str
    intermediate_name: str
    intermediate_desc: str
    intermediate_condition: str
    intermediate_commands: tuple[str, ...]
    dilemma_name: str
    dilemma_desc: str
    choices: tuple[Choice, ...]
    culmination_name: str
    culmination_desc: str
    culmination_condition: str
    culmination_commands: tuple[str, ...]


@dataclass(frozen=True)
class Route:
    key: str
    base: int
    route_trigger: str
    route_flag: str
    picture: str
    status_name: str
    status_desc: str
    compact_condition: str
    partner_war_condition: str
    crisis_name: str
    crisis_desc: str
    crisis_targets: str
    primary_partner: str
    alternate_partner: str
    partner_name: str
    partner_response_name: str
    partner_response_desc: str
    collapse_condition: str
    collapse_name: str
    collapse_desc: str
    collapse_choices: tuple[Choice, ...]
    response_rewards: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]
    focuses: tuple[Focus, ...]


def choice(label: str, flag: str, *commands: str) -> Choice:
    return Choice(label, flag, tuple(commands))


ALPHA23_CONTRACT_FLAG = "ind_aubm_bespoke_route_contract_alpha23"
RESOURCE_TRIGGER_NAMES = {"money": "money", "supplies": "supplies", "oilpool": "oil"}


def resource_costs(commands: tuple[str, ...]) -> dict[str, int]:
    """Return full reserves required by negative stockpile commands."""
    costs: dict[str, int] = {}
    for command in commands:
        match = re.fullmatch(r"(money|supplies|oilpool) value = -(\d+)", command)
        if match:
            costs[match.group(1)] = costs.get(match.group(1), 0) + int(match.group(2))
    return costs


def append_affordability(lines: list[str], commands: tuple[str, ...], *, indent: str = "\t\t") -> None:
    costs = resource_costs(commands)
    if not costs:
        return
    lines.extend([
        f"{indent}trigger = {{",
        f"{indent}\t# AUBM_ACTION_RESERVE_BEGIN",
    ])
    for resource in ("money", "supplies", "oilpool"):
        if resource in costs:
            lines.append(f"{indent}\t{RESOURCE_TRIGGER_NAMES[resource]} = {costs[resource]}")
    lines.extend([
        f"{indent}\t# AUBM_ACTION_RESERVE_END",
        f"{indent}}}",
    ])


def affordability_clause(commands: tuple[str, ...]) -> str:
    costs = resource_costs(commands)
    return "AND = { " + " ".join(
        f"{RESOURCE_TRIGGER_NAMES[resource]} = {costs[resource]}"
        for resource in ("money", "supplies", "oilpool") if resource in costs
    ) + " }"


ROUTES = (
    Route(
        key="allied",
        base=9289500,
        route_trigger="flag = ind_aubm_route_allied",
        route_flag="ind_aubm_route_allied",
        picture="aubm_v4_london_settlement",
        status_name="Allied Route Operations Board",
        status_desc="Delhi's Allied route is not one generic expedition. Eastern Ocean Command wins an Indian-led Asian theatre; Continental Command earns a European settlement voice; the Anti-Colonial Mandate ties liberation to sovereignty; Free Command proves that cooperation does not transfer Indian command.",
        compact_condition="flag = ind_aubm_commitment_allied NOT = { alliance = { country = IND country = ENG } } NOT = { alliance = { country = IND country = USA } }",
        partner_war_condition="OR = { AND = { war = { country = ENG country = GER } NOT = { war = { country = IND country = GER } } } AND = { war = { country = ENG country = JAP } NOT = { war = { country = IND country = JAP } } } AND = { war = { country = USA country = GER } NOT = { war = { country = IND country = GER } } } AND = { war = { country = USA country = JAP } NOT = { war = { country = IND country = JAP } } } }",
        crisis_name="The Allied Compact Faces a New War",
        crisis_desc="London or Washington has entered a major war while India's separate-command treaty leaves Delhi outside it. Formal accession would inherit all coalition wars. Separate campaigning preserves Indian peace authority; material support spends Indian stocks without opening a war; withdrawal remains a peaceful strategic-alignment decision.",
        crisis_targets="Germany or Japan",
        primary_partner="ENG",
        alternate_partner="USA",
        partner_name="London or Washington",
        partner_response_name="The Allies Answer Delhi's Operational Doctrine",
        partner_response_desc="India has submitted a concrete command doctrine rather than a request for ceremonial consultation. The Allied government must recognize the Indian plan, demand integrated supervision, or refuse to reserve coalition resources for a separate Indian theatre.",
        collapse_condition="OR = { AND = { exists = ENG NOT = { control = { province = 29 data = ENG } } } AND = { NOT = { exists = ENG } exists = USA NOT = { control = { province = 1809 data = USA } } } }",
        collapse_name="The Allied Centre Is in Retreat",
        collapse_desc="The principal Allied capital has been lost or displaced. Delhi must decide whether to spend reserves restoring its partner, take full command of the eastern war, demand an immediate decolonization guarantee, or prepare an orderly return to sovereign strategy.",
        collapse_choices=(
            choice("Fund an Indian relief command: -1200 supplies/-250 money", "ind_aubm_allied_collapse_relief", "supplies value = -1200", "money value = -250", "dissent value = 1", "setflag which = ind_aubm_coalition_credit"),
            choice("Assume independent command of the eastern war", "ind_aubm_allied_collapse_independent", "supplies value = 500", "dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
            choice("Make colonial guarantees the price of rescue", "ind_aubm_allied_collapse_decolonization", "money value = -300", "belligerence value = -2", "setflag which = ind_aubm_coalition_consultation"),
            choice("Prepare peaceful strategic disengagement", "ind_aubm_allied_collapse_disengage", "dissent value = 1", "event which = 9281910 where = IND when = 1"),
        ),
        response_rewards=(
            ("supplies value = 500", "dissent value = -1", "setflag which = ind_aubm_coalition_credit"),
            ("supplies value = 250", "dissent value = 1", "setflag which = ind_aubm_coalition_consultation"),
            ("dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
        ),
        focuses=(
            Focus(
                "eastern", "Eastern Ocean Command",
                "Eastern Ocean Command Activates", "The Indian plan begins with a defensible Burma-Andaman hinge, then demands a combined land and sea result through Malaya, the East Indies or the Philippines. Allied victories elsewhere do not substitute for Indian command in this theatre.",
                "OR = { war = { country = IND country = JAP } war = { country = IND country = U05 } war = { country = IND country = HOL } war = { country = IND country = AST } }",
                "The Burma-Andaman Hinge Holds", "Rangoon and Port Blair remain available to Indian command, or the Bay of Bengal lane has been established. Delhi can now choose whether the eastern advance serves coalition logistics, regional liberation or a self-contained Indian fleet base system.",
                "OR = { flag = ind_aubm_sea_lane_bay_current AND = { control = { province = 1415 data = IND } control = { province = 1421 data = IND } } }",
                ("supplies value = 250", "dissent value = -1"),
                "Who Commands the Eastern Advance?", "The operational hinge is secure. Delhi must now define whether the next landings answer to a joint board, an Indian liberation mandate or a sovereign Indian ocean command.",
                (
                    choice("Accept a joint board, retain Indian field command", "ind_aubm_allied_eastern_joint", "supplies value = 300", "dissent value = 1"),
                    choice("Publish an Asian liberation mandate", "ind_aubm_allied_eastern_liberation", "money value = -200", "belligerence value = -2"),
                    choice("Reserve every eastern settlement to Delhi", "ind_aubm_allied_eastern_sovereign", "money value = -150", "dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "Delhi Is the Allied Eastern Command", "Indian command has joined the Southeast Asian land and sea campaign into a sustainable theatre. Allied recognition records how the command was organized, while country settlements remain pairwise and legally separate.",
                "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory flag = ind_aubm_japan_major_victory }",
                ("supplies value = 800", "dissent value = -2", "setflag which = ind_aubm_coalition_credit"),
            ),
            Focus(
                "continental", "Continental Expeditionary Command",
                "The Continental Expedition Forms", "Delhi authorizes a westward expedition only when India is actually fighting a European opponent. Suez, the Gulf and the Mediterranean are staging systems; a European battlefield result is the political culmination.",
                "OR = { war = { country = IND country = GER } war = { country = IND country = ITA } war = { country = IND country = TUR } }",
                "The Expedition Reaches the Western Arc", "Indian command has secured a western corridor or defeated a major regional opponent. The expedition can reinforce the main Allied front, prioritize the Mediterranean, or insist on an autonomous Indian settlement claim.",
                "OR = { flag = ind_aubm_national_western_current flag = ind_aubm_regional_victory_ita flag = ind_aubm_regional_victory_tur }",
                ("money value = 150", "supplies value = 250"),
                "The Continental Command Debate", "The Cabinet must decide what the expedition is for before Indian formations disappear into somebody else's order of battle.",
                (
                    choice("Reinforce the principal European front", "ind_aubm_allied_continental_mainfront", "supplies value = -500", "dissent value = -1"),
                    choice("Make the Mediterranean India's responsibility", "ind_aubm_allied_continental_mediterranean", "money value = -250", "tc_mod value = 1"),
                    choice("Fight under a sovereign Indian mandate", "ind_aubm_allied_continental_sovereign", "dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "The Indian Expedition Earns a European Voice", "An Indian-command result against Germany or another European centre has made consultation a battlefield entitlement rather than a diplomatic courtesy.",
                "OR = { flag = ind_aubm_germany_limited_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_european_capital_victory }",
                ("money value = 350", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "anticolonial", "Anti-Colonial Liberation Mandate",
                "The Liberation Mandate Goes to War", "India enters a campaign capable of displacing an imperial administration or restoring an Asian or African government. The mandate requires a real liberation record and a second regional result, not rhetoric attached to an unrelated victory.",
                "OR = { war = { country = IND country = JAP } war = { country = IND country = GER } war = { country = IND country = ITA } war = { country = IND country = HOL } }",
                "A Liberated Government Returns", "Indian participation has restored a friendly Southeast Asian hub or opened a verified African and western claim. The coalition must now answer whether liberation means sovereignty, supervised transition or renewed imperial administration.",
                "OR = { flag = ind_aubm_sea_land_malaya_liberated_current flag = ind_aubm_sea_land_dei_liberated_current flag = ind_aubm_sea_land_indochina_liberated_current flag = ind_aubm_sea_land_philippines_liberated_current flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf }",
                ("belligerence value = -2", "dissent value = -1"),
                "The Liberation Clause", "Delhi must choose whether to demand immediate sovereignty, accept a timed transition, or use Indian protection to prevent restoration by another empire.",
                (
                    choice("Demand immediate sovereign restoration", "ind_aubm_allied_anticolonial_immediate", "money value = -300", "belligerence value = -3"),
                    choice("Accept a published transition timetable", "ind_aubm_allied_anticolonial_timetable", "money value = -150", "dissent value = -1"),
                    choice("Offer temporary Indian protection", "ind_aubm_allied_anticolonial_protection", "supplies value = -500", "dissent value = 2"),
                ),
                "India Converts Coalition War into Decolonization", "A Southeast Asian operational result now stands beside an African or western liberation record. The mandate is complete without transferring a single province outside the lawful settlement boards.",
                "AND = { OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory } OR = { flag = ind_aubm_national_western_victory flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf flag = ind_aubm_regional_victory_per } }",
                ("money value = 250", "belligerence value = -4", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "free", "Sovereign Free Command",
                "Sovereign Free Command Mobilizes", "India cooperates with the Allies but accepts no named coalition theatre. The doctrine becomes credible only through a current Indian national command and culminates when Delhi becomes decisive across two theatres or breaks a major power.",
                "atwar = yes",
                "An Independent Indian Theatre Is Established", "A southern, western or northern command now exists under Indian authority. Delhi can trade consultation for material, remain a parallel belligerent, or make future cooperation conditional on recognition of Indian peace authority.",
                "OR = { flag = ind_aubm_national_southern_current flag = ind_aubm_national_western_current flag = ind_aubm_national_northern_current }",
                ("supplies value = 300", "money value = 100"),
                "Equality without Integrated Command", "The Allies want predictable coordination; Delhi wants an independent war and peace ledger. The Cabinet must define the bargain before a second theatre opens.",
                (
                    choice("Exchange consultation for replacement stocks", "ind_aubm_allied_free_consultation", "supplies value = 500", "dissent value = 1"),
                    choice("Remain a parallel belligerent", "ind_aubm_allied_free_parallel", "money value = -150", "dissent value = -1"),
                    choice("Demand recognition of separate peace authority", "ind_aubm_allied_free_peaceauthority", "dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "The Allies Must Credit an Independent Indian Victory", "Two Indian theatres or a decisive great-power result now prove that free command was an operational system rather than diplomatic language.",
                "OR = { flag = ind_aubm_decisive_great_power AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory } AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_northern_victory } AND = { flag = ind_aubm_national_western_victory flag = ind_aubm_national_northern_victory } }",
                ("money value = 400", "supplies value = 500", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
        ),
    ),
    Route(
        key="german",
        base=9289540,
        route_trigger="flag = ind_aubm_route_german",
        route_flag="ind_aubm_route_german",
        picture="aubm_v4_barbarossa_reaction",
        status_name="Delhi-Berlin Route Operations Board",
        status_desc="The German relationship can support four different Indian wars. Eurasian Link drives through Persia and the Caucasus; Imperial Dismantlement attacks Britain's western system; Southern Resource Race contests Malaya and the East Indies; Parallel War uses Berlin without accepting German peace authority.",
        compact_condition="flag = ind_aubm_commitment_german NOT = { alliance = { country = IND country = GER } }",
        partner_war_condition="OR = { AND = { war = { country = GER country = ENG } NOT = { war = { country = IND country = ENG } } } AND = { war = { country = GER country = SOV } NOT = { war = { country = IND country = SOV } } } AND = { war = { country = GER country = USA } NOT = { war = { country = IND country = USA } } } }",
        crisis_name="Berlin Opens a War outside the Indian Compact",
        crisis_desc="Germany has entered a major war that the Delhi-Berlin compact does not automatically impose on India. Formal Axis entry would merge every war. Delhi can instead authorize the relevant British or Soviet campaign, send material while staying outside, or review peaceful withdrawal.",
        crisis_targets="Britain, the Soviet Union or the United States",
        primary_partner="GER",
        alternate_partner="ITA",
        partner_name="Berlin",
        partner_response_name="Berlin Answers India's Division of War",
        partner_response_desc="Delhi has defined an Indian theatre that may help Germany without surrendering its settlement claims. Berlin can recognize the division, demand a wider commitment, or withhold support from an Indian war it does not control.",
        collapse_condition="OR = { AND = { exists = GER NOT = { control = { province = 163 data = GER } } } AND = { NOT = { exists = GER } exists = ITA } }",
        collapse_name="The German Front Collapses",
        collapse_desc="Berlin has lost its centre or Germany has ceased to function as the principal continental partner. India can finance a Caucasus lifeline, force the Suez route to divert British pressure, continue an entirely independent war, or prepare peaceful disengagement.",
        collapse_choices=(
            choice("Open a Caucasus lifeline: -1500 supplies/-300 money", "ind_aubm_german_collapse_caucasus", "supplies value = -1500", "money value = -300", "dissent value = 2", "setflag which = ind_aubm_coalition_credit"),
            choice("Force the Suez diversion", "ind_aubm_german_collapse_suez", "supplies value = -900", "tc_mod value = 1", "dissent value = 2"),
            choice("Continue as an independent Indian belligerent", "ind_aubm_german_collapse_parallel", "money value = 250", "dissent value = 1", "setflag which = ind_aubm_victory_sovereign_credit"),
            choice("Prepare peaceful strategic disengagement", "ind_aubm_german_collapse_disengage", "dissent value = 1", "event which = 9281910 where = IND when = 1"),
        ),
        response_rewards=(
            ("supplies value = 600", "dissent value = -1", "setflag which = ind_aubm_coalition_credit"),
            ("supplies value = 250", "dissent value = 1", "setflag which = ind_aubm_coalition_consultation"),
            ("dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
        ),
        focuses=(
            Focus(
                "eurasian", "The Eurasian Link against Moscow",
                "The Eurasian Link Opens", "India's Soviet war begins as a separate southern front. Persia, Afghanistan and Xinjiang may provide access, but only Indian control of a strategic centre turns diplomacy into a continental campaign.",
                "war = { country = IND country = SOV }",
                "Indian Command Reaches the Caucasus Gate", "Baku, Tashkent or the live Northern Command proves that Indian formations have crossed from preparation into the Soviet strategic system.",
                "OR = { flag = ind_aubm_national_northern_current control = { province = 713 data = IND } control = { province = 1103 data = IND } }",
                ("supplies value = 350", "dissent value = -1"),
                "The Caucasus or Central Asia?", "Delhi can concentrate on the oil route to Baku, drive toward Tashkent and Moscow, or preserve a mobile Indian front that refuses Berlin's timetable.",
                (
                    choice("Concentrate on Baku and the Caucasus", "ind_aubm_german_eurasian_caucasus", "supplies value = -600", "mountain_attack which = land value = 1"),
                    choice("Drive through Central Asia", "ind_aubm_german_eurasian_centralasia", "supplies value = -500", "desert_move which = land value = 1"),
                    choice("Preserve a sovereign mobile front", "ind_aubm_german_eurasian_mobile", "money value = -200", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "Indian and German Fronts Meet across Eurasia", "India holds a Northern Command or has forced a recognized Soviet settlement stage. Berlin must now treat the southern front as an independent Indian contribution.",
                "OR = { flag = ind_aubm_national_northern_victory flag = ind_aubm_soviet_limited_victory flag = ind_aubm_soviet_major_victory }",
                ("supplies value = 850", "dissent value = -2", "setflag which = ind_aubm_coalition_credit"),
            ),
            Focus(
                "imperial", "Dismantle Britain's Imperial System",
                "The Imperial Dismantlement Campaign Begins", "India's war against Britain is organized through the Gulf, Suez and East Africa. A captured port is only a raid; the route demands a connected western command and a British campaign result.",
                "war = { country = IND country = ENG }",
                "The Western Ocean Corridor Opens", "Indian command links Suez, the Gulf, Persia or East Africa. Delhi can now choose between a direct Suez blow, an African coastal system or a political liberation campaign.",
                "OR = { flag = ind_aubm_national_western_current flag = ind_aubm_britain_limited_victory }",
                ("money value = 200", "supplies value = 300"),
                "How Will the Imperial System Break?", "Berlin wants pressure on Britain; Delhi must decide whether the decisive mechanism is Suez, African access or sovereign governments replacing imperial administration.",
                (
                    choice("Make Suez the decisive hinge", "ind_aubm_german_imperial_suez", "supplies value = -650", "tc_mod value = 1"),
                    choice("Build an East African coastal command", "ind_aubm_german_imperial_africa", "money value = -250", "supplies value = -350"),
                    choice("Promise sovereign successor governments", "ind_aubm_german_imperial_liberation", "belligerence value = -3", "dissent value = -1"),
                ),
                "India Breaks the Imperial System from the East", "A live western command and a British battlefield result give Delhi, not Berlin, the decisive Indian Ocean claim.",
                "AND = { flag = ind_aubm_national_western_victory OR = { flag = ind_aubm_britain_limited_victory flag = ind_aubm_britain_major_victory } }",
                ("money value = 400", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "southern", "Win the Southern Resource Race",
                "The Southern Resource Race Begins", "Indian command contests the Straits and the East Indies while Germany remains a continental partner. The campaign must establish a land-and-sea theatre before Tokyo or another coalition power can define the settlement.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = U05 } war = { country = IND country = HOL } war = { country = IND country = AST } }",
                "The Straits Enter Indian Command", "Malacca, the East Indies or an equivalent southern result is now held by India. Delhi must decide whether to coordinate with Japan, exclude Tokyo, or turn the resource arc into sovereign regional governments.",
                "OR = { flag = ind_aubm_sea_lane_malacca_current flag = ind_aubm_regional_victory_u05 flag = ind_aubm_national_southern_current }",
                ("supplies value = 350", "money value = 100"),
                "The Delhi-Tokyo Resource Question", "Germany's alliance system does not settle who leads Asia. India must publish its terms before completing the southern theatre.",
                (
                    choice("Coordinate shipping with Tokyo, reserve settlement rights", "ind_aubm_german_southern_coordinate_japan", "supplies value = 300", "relation which = JAP value = 15"),
                    choice("Exclude Japan from the Indian resource arc", "ind_aubm_german_southern_exclude_japan", "money value = -250", "relation which = JAP value = -30", "dissent value = 1"),
                    choice("Commit to sovereign Southeast Asian partners", "ind_aubm_german_southern_sovereign", "belligerence value = -2", "dissent value = -1"),
                ),
                "Delhi Wins the Southern Resource Race", "India has completed the flexible Southeast Asian theatre or a live Southern Command. The result is Indian settlement credit rather than an automatic German or Japanese transfer.",
                "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory }",
                ("supplies value = 900", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
            Focus(
                "parallel", "Sovereign Parallel War",
                "The Parallel War Doctrine Activates", "India accepts German consultation but chooses its own enemy and theatre. One national command proves operational independence; a second theatre or major-power result proves strategic equality.",
                "atwar = yes",
                "A Parallel Indian Front Exists", "A current Indian national command now operates without becoming a German subordinate. Delhi must decide what information, supply and peace authority it will share with Berlin.",
                "OR = { flag = ind_aubm_national_southern_current flag = ind_aubm_national_western_current flag = ind_aubm_national_northern_current }",
                ("money value = 150", "supplies value = 250"),
                "The Limits of Berlin Consultation", "The Cabinet must draw a line between useful coordination and surrender of Indian war aims.",
                (
                    choice("Share intelligence, retain separate settlements", "ind_aubm_german_parallel_intelligence", "intelligence which = us value = 1", "dissent value = -1"),
                    choice("Accept a limited German logistics mission", "ind_aubm_german_parallel_logistics", "supplies value = 500", "dissent value = 1"),
                    choice("Refuse every operational veto", "ind_aubm_german_parallel_noveto", "relation which = GER value = -20", "dissent value = 1", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "India Proves It Is Berlin's Partner, Not Client", "A decisive great-power result or two Indian national theatres establish the parallel war as a complete strategy.",
                "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_soviet_major_victory AND = { flag = ind_aubm_national_western_victory flag = ind_aubm_national_northern_victory } }",
                ("money value = 350", "supplies value = 550", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
        ),
    ),
    Route(
        key="soviet",
        base=9289580,
        route_trigger="OR = { flag = ind_aubm_route_soviet AND = { flag = ind_aubm_route_sovereign flag = ind_aubm_socialist_autonomous } }",
        route_flag="ind_aubm_route_soviet",
        picture="Stalin_5YPlan",
        status_name="Delhi Socialist Route Operations Board",
        status_desc="India's socialist route can be anti-fascist, anti-imperial, republican-Asian or autonomous. Each doctrine uses a different battlefield sequence and forces a different argument with Moscow over command, sovereignty and the political character of victory.",
        compact_condition="flag = ind_aubm_commitment_soviet NOT = { alliance = { country = IND country = SOV } }",
        partner_war_condition="OR = { AND = { war = { country = SOV country = GER } NOT = { war = { country = IND country = GER } } } AND = { war = { country = SOV country = JAP } NOT = { war = { country = IND country = JAP } } } AND = { war = { country = SOV country = ENG } NOT = { war = { country = IND country = ENG } } } }",
        crisis_name="Moscow's War Tests the Equal Compact",
        crisis_desc="The Soviet Union has entered a major war while India remains outside under separate command. Delhi can seek formal Comintern entry, authorize the named anti-fascist or eastern campaign, support Moscow materially without war, or review peaceful withdrawal into autonomous socialism.",
        crisis_targets="Germany, Japan or Britain",
        primary_partner="SOV",
        alternate_partner="CHC",
        partner_name="Moscow",
        partner_response_name="Moscow Answers the Indian War Doctrine",
        partner_response_desc="Delhi's plan combines military cooperation with an independent political programme. Moscow may recognize equal command, demand a consultative veto, or deny aid to a theatre that advances Indian rather than Soviet priorities.",
        collapse_condition="OR = { AND = { exists = SOV NOT = { control = { province = 572 data = SOV } } } AND = { NOT = { exists = SOV } exists = CHC } }",
        collapse_name="Moscow's Strategic Centre Is Lost",
        collapse_desc="The Soviet centre has fallen or Moscow can no longer lead the compact. India must choose between an emergency anti-fascist supply effort, an eastern diversion, autonomous socialist command, or peaceful disengagement.",
        collapse_choices=(
            choice("Send an emergency continental arsenal: -1400 supplies", "ind_aubm_soviet_collapse_arsenal", "supplies value = -1400", "money value = -200", "dissent value = 1", "setflag which = ind_aubm_coalition_credit"),
            choice("Open an eastern diversion", "ind_aubm_soviet_collapse_eastern", "supplies value = -700", "tc_mod value = 1", "dissent value = 2"),
            choice("Proclaim autonomous Indian socialist command", "ind_aubm_soviet_collapse_autonomous", "dissent value = -1", "setflag which = ind_aubm_socialist_autonomous", "setflag which = ind_aubm_victory_sovereign_credit"),
            choice("Prepare peaceful strategic disengagement", "ind_aubm_soviet_collapse_disengage", "dissent value = 1", "event which = 9281910 where = IND when = 1"),
        ),
        response_rewards=(
            ("research_mod value = 1", "supplies value = 350", "dissent value = -1", "setflag which = ind_aubm_coalition_credit"),
            ("supplies value = 200", "dissent value = 1", "setflag which = ind_aubm_coalition_consultation"),
            ("dissent value = 1", "setflag which = ind_aubm_socialist_autonomous", "setflag which = ind_aubm_victory_sovereign_credit"),
        ),
        focuses=(
            Focus(
                "antifascist", "Anti-Fascist Expedition",
                "The Anti-Fascist Expedition Mobilizes", "Indian formations enter a war against Germany or its principal European partners. A western staging system comes first; a German or European capital result completes the independent anti-fascist claim.",
                "OR = { war = { country = IND country = GER } war = { country = IND country = ITA } war = { country = IND country = TUR } }",
                "The Persian-Caucasus Supply Line Functions", "A live western command or European regional result now sustains the expedition. Delhi must decide whether Moscow receives operational consultation, whether the Mediterranean remains Indian, or whether the campaign serves an autonomous socialist policy.",
                "OR = { flag = ind_aubm_national_western_current flag = ind_aubm_regional_victory_ita flag = ind_aubm_regional_victory_tur }",
                ("supplies value = 300", "dissent value = -1"),
                "Command of the Anti-Fascist Expedition", "India and Moscow agree on the enemy but not automatically on command or the postwar political order.",
                (
                    choice("Coordinate operational plans with Moscow", "ind_aubm_soviet_antifascist_coordinate", "supplies value = 350", "dissent value = 1"),
                    choice("Reserve the Mediterranean front to Delhi", "ind_aubm_soviet_antifascist_mediterranean", "money value = -200", "tc_mod value = 1"),
                    choice("Fight as an autonomous socialist belligerent", "ind_aubm_soviet_antifascist_autonomous", "dissent value = 1", "setflag which = ind_aubm_socialist_autonomous"),
                ),
                "India Is an Independent Anti-Fascist Belligerent", "A German or European strategic result gives Delhi its own anti-fascist settlement claim rather than a subordinate place in Moscow's war.",
                "OR = { flag = ind_aubm_germany_limited_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_european_capital_victory }",
                ("supplies value = 750", "dissent value = -2", "setflag which = ind_aubm_coalition_credit"),
            ),
            Focus(
                "antiimperial", "Anti-Imperial Ocean War",
                "The Anti-Imperial Ocean War Begins", "India opens a war capable of breaking a colonial maritime system. One Indian Ocean theatre establishes military leverage; a second southern or western system proves that liberation is not a local raid.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = HOL } war = { country = IND country = POR } war = { country = IND country = USA } }",
                "An Imperial Ocean Arc Breaks", "India holds either the western corridor or a Southeast Asian operational result. Moscow now asks whether the war should serve global bloc strategy or Indian-led decolonization.",
                "OR = { flag = ind_aubm_national_western_current flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_britain_limited_victory }",
                ("money value = 150", "belligerence value = -1"),
                "Whose Anti-Imperial War?", "The Cabinet must choose between a joint socialist maritime command, sovereign liberation settlements or a narrower Indian security belt.",
                (
                    choice("Offer Moscow a joint maritime board", "ind_aubm_soviet_antiimperial_joint", "supplies value = 350", "dissent value = 1"),
                    choice("Reserve liberation settlements to local governments", "ind_aubm_soviet_antiimperial_liberation", "money value = -250", "belligerence value = -3"),
                    choice("Build an Indian security belt", "ind_aubm_soviet_antiimperial_security", "supplies value = -450", "dissent value = 2"),
                ),
                "India Converts Socialist War into Oceanic Liberation", "A western victory and a southern or Southeast Asian result create an Indian anti-imperial system distinct from Soviet territorial priorities.",
                "AND = { flag = ind_aubm_national_western_victory OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory } }",
                ("money value = 300", "belligerence value = -4", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "republican", "A Republican Asian Order",
                "The Republican Asian Campaign Opens", "India enters an Asian war in which China, Siam, Indochina or the southern archipelago can become the political centre. The doctrine requires a regional result and a wider land-and-sea achievement.",
                "OR = { war = { country = IND country = JAP } war = { country = IND country = CHI } war = { country = IND country = CHC } war = { country = IND country = SIA } war = { country = IND country = U05 } war = { country = IND country = HOL } }",
                "An Asian Political Centre Is Secured", "Indian command has produced a China, Siam, Indochina or Philippines result. Delhi must decide whether Asian republics align with Moscow, form an equal Delhi system or remain nationally distinct under mutual guarantees.",
                "OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia flag = ind_aubm_sea_land_indochina flag = ind_aubm_sea_land_philippines }",
                ("money value = 200", "dissent value = -1"),
                "The Political Form of Republican Asia", "Military success has opened the political question that the campaign was meant to answer.",
                (
                    choice("Build a league of equal Asian republics", "ind_aubm_soviet_republican_league", "money value = -300", "belligerence value = -2"),
                    choice("Accept a joint Delhi-Moscow guarantee", "ind_aubm_soviet_republican_joint", "supplies value = 350", "dissent value = 1"),
                    choice("Guarantee national roads to socialism", "ind_aubm_soviet_republican_national", "dissent value = -1", "setflag which = ind_aubm_socialist_autonomous"),
                ),
                "Delhi Establishes an Asian Republican Claim", "A regional Asian victory now stands beside a flexible Southeast Asian theatre result. The doctrine has produced a real political order without bypassing any local constitutional settlement.",
                "AND = { OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia } OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_japan_limited_victory flag = ind_aubm_japan_major_victory } }",
                ("money value = 350", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "autonomous", "Autonomous Indian Socialism",
                "Autonomous Socialist Command Mobilizes", "India fights under a socialist domestic programme without transferring command to Moscow. One current national theatre proves capability; two theatres or a major-power result prove strategic autonomy.",
                "atwar = yes",
                "An Autonomous Socialist Theatre Exists", "Indian command has established a live theatre. Delhi must decide how much science, intelligence and logistics it will exchange without creating a Soviet veto.",
                "OR = { flag = ind_aubm_national_southern_current flag = ind_aubm_national_western_current flag = ind_aubm_national_northern_current }",
                ("research_mod value = 1", "dissent value = -1"),
                "Cooperation without a Veto", "The Cabinet must define a durable line between socialist cooperation and independent Indian strategy.",
                (
                    choice("Exchange science under equal contracts", "ind_aubm_soviet_autonomous_science", "money value = -250", "research_mod value = 1"),
                    choice("Share intelligence but no operational plans", "ind_aubm_soviet_autonomous_intelligence", "intelligence which = us value = 1", "dissent value = -1"),
                    choice("Refuse every external supervisory right", "ind_aubm_soviet_autonomous_noveto", "relation which = SOV value = -20", "dissent value = 1", "setflag which = ind_aubm_socialist_autonomous"),
                ),
                "Indian Socialism Wins on Its Own Ledger", "A decisive result or two national theatres demonstrate that autonomous socialism is a complete strategic route rather than an incomplete compact.",
                "OR = { flag = ind_aubm_decisive_great_power AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory } AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_northern_victory } AND = { flag = ind_aubm_national_western_victory flag = ind_aubm_national_northern_victory } }",
                ("research_mod value = 2", "money value = 250", "dissent value = -2", "setflag which = ind_aubm_socialist_autonomous", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
        ),
    ),
    Route(
        key="japan",
        base=9289620,
        route_trigger="flag = ind_aubm_route_japan",
        route_flag="ind_aubm_route_japan",
        picture="aubm_v4_tokyo_proposition",
        status_name="Delhi-Tokyo Route Operations Board",
        status_desc="The existing southern and northern partnership systems remain authoritative. This overlay completes the other strategic identities: a Philippines and China division for Equal Asian Command, a staged Suez and Africa campaign for Indian Ocean First, and a Tripartite crisis when Germany can no longer carry the continental war.",
        compact_condition="flag = ind_aubm_commitment_japan flag = ind_aubm_jp_partnership NOT = { alliance = { country = IND country = JAP } }",
        partner_war_condition="OR = { AND = { war = { country = JAP country = ENG } NOT = { war = { country = IND country = ENG } } } AND = { war = { country = JAP country = USA } NOT = { war = { country = IND country = USA } } } AND = { war = { country = JAP country = SOV } NOT = { war = { country = IND country = SOV } } } }",
        crisis_name="Tokyo's New War Tests the Separate Compact",
        crisis_desc="Japan has entered a major war outside India's separate-command compact. Formal alliance would inherit every Japanese war. Delhi can instead open the corresponding British, American or Soviet campaign through the War Cabinet, give limited support while remaining outside, or review peaceful withdrawal.",
        crisis_targets="Britain, the United States or the Soviet Union",
        primary_partner="JAP",
        alternate_partner="SIA",
        partner_name="Tokyo",
        partner_response_name="Tokyo Answers India's Asian Command Doctrine",
        partner_response_desc="Delhi's doctrine changes the practical division of China, the Philippines, the Indian Ocean or the Soviet frontier. Tokyo may recognize the Indian command, demand a narrower sphere, or refuse to support an operation outside Japanese priorities.",
        collapse_condition="OR = { AND = { exists = JAP NOT = { control = { province = 1552 data = JAP } } } AND = { NOT = { exists = JAP } exists = SIA } }",
        collapse_name="Tokyo Can No Longer Carry the Pacific War",
        collapse_desc="Tokyo has lost its strategic centre or Japan can no longer lead the partnership. India can assume the full Asian command, prioritize the Indian Ocean and Suez, sustain the continental war to aid Germany, or prepare peaceful strategic separation.",
        collapse_choices=(
            choice("Assume full Asian command: -1200 supplies", "ind_aubm_japan_collapse_asiancommand", "supplies value = -1200", "dissent value = 2", "setflag which = ind_aubm_coalition_credit"),
            choice("Prioritize Suez and the Indian Ocean", "ind_aubm_japan_collapse_ocean", "supplies value = -700", "tc_mod value = 1", "dissent value = 1"),
            choice("Sustain the Caucasus war to aid Germany", "ind_aubm_japan_collapse_tripartite", "supplies value = -1000", "money value = -250", "dissent value = 2"),
            choice("Prepare peaceful strategic separation", "ind_aubm_japan_collapse_disengage", "dissent value = 1", "event which = 9281910 where = IND when = 1"),
        ),
        response_rewards=(
            ("supplies value = 500", "dissent value = -1", "setflag which = ind_aubm_coalition_credit"),
            ("supplies value = 200", "dissent value = 1", "setflag which = ind_aubm_coalition_consultation"),
            ("dissent value = 2", "setflag which = ind_aubm_jp_partnership_strained", "setflag which = ind_aubm_victory_sovereign_credit"),
        ),
        focuses=(
            Focus(
                "southern", "Indian Southern Sphere",
                "The Indian Southern Sphere Activates", "The existing Delhi-Tokyo southern ledger remains the operational authority. Burma and the Andamans open the route; Malaya and either the East Indies or Australia provide the decisive weight.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = U05 } war = { country = IND country = HOL } war = { country = IND country = AST } }",
                "Malaya Enters the Indian Sphere", "Singapore and Kuala Lumpur, the Malacca lane or the existing Japanese partnership objective prove that India commands the hinge of the southern campaign.",
                "OR = { flag = ind_aubm_jp_objective_malaya flag = ind_aubm_sea_lane_malacca_current flag = ind_aubm_national_southern_current }",
                ("supplies value = 400", "dissent value = -1"),
                "The East Indies or Australia?", "Delhi must state whether the next effort secures the resource archipelago, carries the campaign to Australia, or turns victory into sovereign Southeast Asian governments.",
                (
                    choice("Concentrate on the East Indies resource arc", "ind_aubm_japan_southern_eastindies", "supplies value = -600", "oilpool value = 300"),
                    choice("Carry Indian command to Australia", "ind_aubm_japan_southern_australia", "supplies value = -750", "tc_mod value = 1"),
                    choice("Promise sovereign southern governments", "ind_aubm_japan_southern_sovereign", "money value = -250", "belligerence value = -2"),
                ),
                "Tokyo Recognizes the Indian Southern Sphere", "The dedicated partnership victory or the flexible Southeast Asian theatre confirms Indian primacy from Burma through the Straits. Existing country-specific settlement boards remain authoritative.",
                "OR = { flag = ind_aubm_jp_southern_victory flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory }",
                ("supplies value = 900", "dissent value = -2", "setflag which = ind_aubm_jp_india_full_sphere"),
            ),
            Focus(
                "dualfront", "Northern Coalition Campaign",
                "The Northern Coalition Campaign Opens", "This doctrine accepts either a separate Indian Soviet war under the Delhi-Tokyo compact or a formal allied northern campaign. In both cases Indian command must reach the Caucasus or Central Asian strategic system before Delhi can claim relief credit.",
                "OR = { AND = { flag = ind_aubm_jp_independent_soviet_war war = { country = IND country = SOV } NOT = { alliance = { country = IND country = JAP } } } AND = { alliance = { country = IND country = JAP } war = { country = IND country = SOV } } }",
                "The Indian Northern Front Reaches a Strategic Centre", "Baku, Tashkent or a live Northern Command proves that India's second war is operational rather than declaratory.",
                "OR = { flag = ind_aubm_national_northern_current control = { province = 713 data = IND } control = { province = 1103 data = IND } }",
                ("supplies value = 350", "dissent value = -1"),
                "What Should Tokyo Do in the North?", "India can request discreet supply, ask Japan to threaten the Soviet Far East, or explicitly preserve Japanese neutrality and claim the campaign alone.",
                (
                    choice("Request discreet Japanese supply", "ind_aubm_japan_dualfront_supply", "relation which = JAP value = 10", "dissent value = 1"),
                    choice("Ask Tokyo to pressure the Soviet Far East", "ind_aubm_japan_dualfront_pressure", "money value = -200", "relation which = SOV value = -20"),
                    choice("Preserve Japanese neutrality and Indian credit", "ind_aubm_japan_dualfront_independent", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit"),
                ),
                "India Sustains the Northern Coalition Front", "A Soviet campaign result or historical Northern Command victory confirms that Delhi can carry the Caucasus burden under either formal alliance or separate compact without surrendering Indian settlement credit.",
                "OR = { flag = ind_aubm_soviet_limited_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_national_northern_victory }",
                ("money value = 300", "supplies value = 600", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
            Focus(
                "ocean", "Indian Ocean First",
                "Indian Ocean First Goes to War", "India opens a western campaign while Japan concentrates on China and the Pacific. Aden, Suez, the Gulf and East Africa are connected stages; one port alone cannot complete the doctrine.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = USA } war = { country = IND country = IRQ } war = { country = IND country = SAU } war = { country = IND country = ETH } war = { country = IND country = SAF } }",
                "The Red Sea and Gulf Hinge Opens", "Suez, Aden, the Gulf or a live Western Command gives India the first half of the ocean road. Delhi must decide whether to race to Egypt, build an African coast system or use the theatre to sustain Germany's Caucasus front.",
                "OR = { flag = ind_aubm_national_western_current control = { province = 900 data = IND } control = { province = 1053 data = IND } control = { province = 1034 data = IND } }",
                ("supplies value = 350", "money value = 150"),
                "Suez, Africa or the Tripartite Lifeline?", "Tokyo's Pacific priorities leave the western political consequences to Delhi. The Cabinet must choose the campaign's decisive purpose.",
                (
                    choice("Drive through Suez and Egypt", "ind_aubm_japan_ocean_suez", "supplies value = -650", "tc_mod value = 1"),
                    choice("Build an East African maritime system", "ind_aubm_japan_ocean_africa", "money value = -250", "supplies value = -350"),
                    choice("Use the ocean road to sustain Germany", "ind_aubm_japan_ocean_germany", "supplies value = -800", "relation which = GER value = 25", "dissent value = 1"),
                ),
                "India Opens the Western Ocean Road", "A live Western Command and a British or African result connect the Gulf, Suez and East Africa to India's maritime system.",
                "AND = { flag = ind_aubm_national_western_victory OR = { flag = ind_aubm_britain_limited_victory flag = ind_aubm_britain_major_victory flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf } }",
                ("money value = 350", "supplies value = 700", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation"),
            ),
            Focus(
                "equal", "Equal Asian Command",
                "Equal Asian Command Mobilizes", "India seeks equality through operations beyond the original southern map. A Philippines, China or Southeast Asian result provides the first proof; a second theatre or decisive great-power result completes the claim.",
                "atwar = yes",
                "India Shapes the Philippines or China War", "Indian command has produced a Philippines, China, Siam or wider Southeast Asian result. Delhi must now negotiate who determines sovereignty, basing and the final China settlement.",
                "OR = { flag = ind_aubm_sea_land_philippines flag = ind_aubm_sea_land_philippines_liberated_current flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia flag = ind_aubm_sea_theatre_achieved }",
                ("money value = 200", "dissent value = -1"),
                "The Manila and China Division", "The original compact reserved China and the Philippines to Japan. Indian battlefield participation now forces a new division of political responsibility.",
                (
                    choice("Recognize Pacific command; require consultation", "ind_aubm_japan_equal_consultation", "relation which = JAP value = 20", "dissent value = 1"),
                    choice("Demand a sovereign Philippine and Chinese settlement", "ind_aubm_japan_equal_sovereignty", "money value = -300", "belligerence value = -3"),
                    choice("Claim equal command over every Indian-won theatre", "ind_aubm_japan_equal_fullcommand", "supplies value = -400", "dissent value = 2"),
                ),
                "Delhi Becomes Tokyo's Equal Asian Centre", "A second national theatre, a decisive great-power result or combined Asian and Southeast Asian victories establish two real strategic centres in the partnership.",
                "OR = { flag = ind_aubm_decisive_great_power AND = { flag = ind_aubm_sea_theatre_achieved OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_sea_land_philippines } } AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory } AND = { flag = ind_aubm_national_southern_victory flag = ind_aubm_national_northern_victory } }",
                ("money value = 400", "supplies value = 600", "dissent value = -2", "setflag which = ind_aubm_coalition_credit"),
            ),
        ),
    ),
    Route(
        key="sovereign",
        base=9289660,
        route_trigger="AND = { flag = ind_aubm_route_sovereign NOT = { flag = ind_aubm_socialist_autonomous } }",
        route_flag="ind_aubm_route_sovereign",
        picture="aubm_v4_asian_strategy_menu",
        status_name="Sovereign India Route Operations Board",
        status_desc="Sovereign command is not an empty sandbox. Ocean League combines regional pacts with maritime success; Continental Arc joins frontier diplomacy to northern operations; World Balancer intervenes at a great-power hinge; Republican Federation measures victory through multiple sovereign regional settlements.",
        compact_condition="AND = { NOT = { flag = ind_aubm_commitment_allied } NOT = { flag = ind_aubm_commitment_german } NOT = { flag = ind_aubm_commitment_soviet } NOT = { flag = ind_aubm_commitment_japan } OR = { flag = ind_v3_delhi_pact flag = ind_v42_delhi_pact_consultative flag = ind_v42_delhi_china_alliance flag = ind_v42_delhi_siam_alliance flag = ind_v42_delhi_pact_alliance alliance = { country = IND country = CHI } alliance = { country = IND country = SIA } } }",
        partner_war_condition="OR = { AND = { OR = { flag = ind_v3_delhi_pact alliance = { country = IND country = CHI } AND = { flag = ind_v42_delhi_pact_consultative flag = ind_v42_china_accepts_delhi_pact } } war = { country = CHI country = JAP } NOT = { war = { country = IND country = JAP } } } AND = { OR = { flag = ind_v3_delhi_pact alliance = { country = IND country = SIA } AND = { flag = ind_v42_delhi_pact_consultative flag = ind_v42_siam_accepts_delhi_pact } } war = { country = SIA country = JAP } NOT = { war = { country = IND country = JAP } } } AND = { flag = ind_v3_delhi_pact war = { country = PER country = SOV } NOT = { war = { country = IND country = SOV } } } AND = { flag = ind_v3_delhi_pact war = { country = AFG country = SOV } NOT = { war = { country = IND country = SOV } } } }",
        crisis_name="A Delhi-System Partner Enters War",
        crisis_desc="A recognized Delhi-System partner is fighting Japan or the Soviet Union while India remains outside. Delhi can publish an independent response plan, review only those two legal war fronts, send material support without entering, or maintain armed neutrality.",
        crisis_targets="Japan or the Soviet Union",
        primary_partner="SIA",
        alternate_partner="CHI",
        partner_name="The Delhi regional council",
        partner_response_name="The Delhi System Answers India's Doctrine",
        partner_response_desc="India has asked sovereign regional partners to support a concrete operational doctrine. The council may endorse Indian leadership, demand reciprocal guarantees, or refuse to turn consultation into a permanent military hierarchy.",
        collapse_condition="OR = { AND = { exists = SIA NOT = { control = { province = 1423 data = SIA } } } AND = { exists = CHI NOT = { control = { province = 1337 data = CHI } } } AND = { exists = PER NOT = { control = { province = 1085 data = PER } } } AND = { exists = AFG NOT = { control = { province = 2171 data = AFG } } } }",
        collapse_name="A Delhi-System Partner Appeals for Rescue",
        collapse_desc="A regional partner has lost its political centre. India can mount a sovereign relief effort, guarantee an evacuation and reconstruction government, absorb the strategic burden into direct Indian command, or preserve neutrality at the cost of league credibility.",
        collapse_choices=(
            choice("Mount a sovereign relief effort: -1000 supplies", "ind_aubm_sovereign_collapse_relief", "supplies value = -1000", "money value = -200", "dissent value = 1"),
            choice("Guarantee evacuation and reconstruction", "ind_aubm_sovereign_collapse_reconstruction", "money value = -350", "belligerence value = -2", "dissent value = -1"),
            choice("Assume direct Indian strategic command", "ind_aubm_sovereign_collapse_command", "supplies value = -500", "dissent value = 3"),
            choice("Preserve neutrality and accept lost credibility", "ind_aubm_sovereign_collapse_neutrality", "money value = 150", "dissent value = 2"),
        ),
        response_rewards=(
            ("money value = 250", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit"),
            ("supplies value = 150", "tc_mod value = 1", "dissent value = 1", "setflag which = ind_aubm_coalition_consultation"),
            ("dissent value = 2", "setflag which = ind_aubm_victory_sovereign_credit"),
        ),
        focuses=(
            Focus(
                "ocean", "Build an Indian Ocean League",
                "The Indian Ocean League Mobilizes", "A sovereign southern or western war activates the League's military test. Regional pacts provide political depth, but the doctrine requires a live maritime result under Indian command.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = HOL } war = { country = IND country = U05 } war = { country = IND country = AST } war = { country = IND country = SIA } war = { country = IND country = PER } }",
                "A League Sea Gate Is Secure", "Bay of Bengal, Malacca, Java or a live Western Command gives the League an operational centre. Delhi must decide whether membership is open and sovereign, defended through Indian bases, or organized as a common fleet.",
                "OR = { flag = ind_aubm_sea_lane_bay_current flag = ind_aubm_sea_lane_malacca_current flag = ind_aubm_sea_lane_java_current flag = ind_aubm_national_western_current }",
                ("money value = 150", "supplies value = 250"),
                "The League's Military Constitution", "Operational success forces India to define the obligations that regional diplomacy previously left ambiguous.",
                (
                    choice("An open league of sovereign partners", "ind_aubm_sovereign_ocean_openleague", "money value = -250", "belligerence value = -2"),
                    choice("Indian bases with published limits", "ind_aubm_sovereign_ocean_bases", "supplies value = -450", "dissent value = 1", "tc_mod value = 1"),
                    choice("A common Indian Ocean fleet command", "ind_aubm_sovereign_ocean_commonfleet", "money value = -300", "max_organization which = naval value = 1"),
                ),
                "The Indian Ocean League Has a Military Foundation", "A Southeast Asian, southern or western theatre now gives the sovereign League real ports and bargaining power without granting India automatic ownership.",
                "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory }",
                ("tc_mod value = 2", "money value = 300", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
            Focus(
                "continental", "Secure the Continental Arc",
                "The Continental Security Arc Mobilizes", "A northern or frontier war activates India's sovereign continental doctrine. Kabul, Persia, Tibet and Xinjiang are gates; Baku, Tashkent, Astrakhan or Moscow are the strategic centres.",
                "OR = { war = { country = IND country = SOV } war = { country = IND country = AFG } war = { country = IND country = PER } war = { country = IND country = TIB } war = { country = IND country = SIK } }",
                "A Continental Gate Is Secured", "India has a frontier settlement or controls the first northern strategic centre. Delhi must decide whether the arc is a sovereign buffer league, an Indian base network or a mobile frontier guarantee.",
                "OR = { flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_tib flag = ind_aubm_regional_victory_sik flag = ind_aubm_national_northern_current }",
                ("supplies value = 300", "dissent value = -1"),
                "The Political Form of the Continental Arc", "The first gate is open, but the Cabinet must choose a structure before the campaign reaches the Central Asian centres.",
                (
                    choice("A sovereign buffer league", "ind_aubm_sovereign_continental_buffer", "money value = -250", "belligerence value = -2"),
                    choice("A limited Indian base network", "ind_aubm_sovereign_continental_bases", "supplies value = -500", "tc_mod value = 1", "dissent value = 1"),
                    choice("Mobile guarantees without permanent bases", "ind_aubm_sovereign_continental_mobile", "money value = -150", "dissent value = -1"),
                ),
                "India Secures a Continental Strategic Arc", "A live Northern Command or combined frontier victories now establish a sovereign arc from the Himalaya toward Central Asia.",
                "OR = { flag = ind_aubm_national_northern_victory AND = { OR = { flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_per } OR = { flag = ind_aubm_regional_victory_tib flag = ind_aubm_regional_victory_sik } } }",
                ("supplies value = 750", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
            Focus(
                "balancer", "Act as the World Balancer",
                "The World Balancer Intervenes", "India enters a great-power war without accepting another capital's command. A limited result proves leverage; a major armistice position or two national theatres prove that India can alter the global balance.",
                "OR = { war = { country = IND country = ENG } war = { country = IND country = GER } war = { country = IND country = SOV } war = { country = IND country = JAP } war = { country = IND country = USA } }",
                "A Great Power Must Account for Delhi", "India has reached a limited great-power result or created a national theatre. Delhi must choose whether to mediate, sustain the weaker side, or use the balance solely to secure Indian strategic autonomy.",
                "OR = { flag = ind_aubm_britain_limited_victory flag = ind_aubm_germany_limited_victory flag = ind_aubm_soviet_limited_victory flag = ind_aubm_japan_limited_victory flag = ind_aubm_america_limited_victory flag = ind_aubm_national_southern_current flag = ind_aubm_national_western_current flag = ind_aubm_national_northern_current }",
                ("money value = 200", "dissent value = -1"),
                "How Should India Balance the War?", "The Cabinet now has leverage but must define the principle governing its use.",
                (
                    choice("Offer a direct Delhi mediation", "ind_aubm_sovereign_balancer_mediate", "money value = -300", "belligerence value = -3"),
                    choice("Sustain the weaker belligerent temporarily", "ind_aubm_sovereign_balancer_equilibrium", "supplies value = -600", "dissent value = 1"),
                    choice("Convert leverage into Indian strategic autonomy", "ind_aubm_sovereign_balancer_autonomy", "money value = 150", "dissent value = 2"),
                ),
                "A Great Power Negotiates Directly with Delhi", "A decisive great-power result or two Indian national theatres make India a balancer in fact rather than in diplomatic language.",
                "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_america_major_victory }",
                ("money value = 450", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
            Focus(
                "republican", "Build a Republican Federation",
                "The Republican Federation Goes to War", "India enters a regional campaign whose settlement can create or restore a sovereign government. One regional victory opens the constitutional question; a second distinct regional or liberation result completes the federation claim.",
                "OR = { war = { country = IND country = CHI } war = { country = IND country = CHC } war = { country = IND country = SIA } war = { country = IND country = PER } war = { country = IND country = AFG } war = { country = IND country = ETH } war = { country = IND country = SAF } war = { country = IND country = U05 } war = { country = IND country = HOL } }",
                "A Regional Government Enters Settlement", "India has earned one constitutional settlement. Delhi must decide whether federation means equal sovereign membership, mutual guarantees or temporary Indian administration with a published exit.",
                "OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf flag = ind_aubm_sea_land_malaya_liberated_current flag = ind_aubm_sea_land_dei_liberated_current }",
                ("money value = 150", "belligerence value = -1"),
                "The Federation's Constitutional Promise", "The first settlement will define how every later member judges Indian intentions.",
                (
                    choice("Equal sovereign membership from the start", "ind_aubm_sovereign_republican_equal", "money value = -300", "belligerence value = -3"),
                    choice("Mutual guarantees under a Delhi council", "ind_aubm_sovereign_republican_guarantees", "supplies value = -400", "dissent value = 1"),
                    choice("Temporary administration with a published exit", "ind_aubm_sovereign_republican_transition", "money value = -200", "dissent value = -1"),
                ),
                "Indian Arms Create Space for Sovereign Governments", "Two distinct regional or friendly-liberation results establish a federation claim. Each government's actual status still follows its own lawful settlement event.",
                "OR = { AND = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_sia } AND = { flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_afg } AND = { flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf } AND = { flag = ind_aubm_sea_land_malaya_liberated flag = ind_aubm_sea_land_dei_liberated } AND = { flag = ind_aubm_sea_theatre_achieved OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_sia flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf } } }",
                ("money value = 350", "belligerence value = -4", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit"),
            ),
        ),
    ),
)


def header(event_id: int, country: str = "IND", *, persistent: bool = True, one_action: bool = False) -> list[str]:
    lines = ["event = {", f"\tid = {event_id}", "\trandom = no"]
    if persistent:
        lines.append("\tpersistent = yes")
    if one_action:
        lines.append("\tone_action = yes")
    lines.append(f"\tcountry = {country}")
    return lines


def dated(lines: list[str], *, offset: int = 3) -> None:
    lines.extend([
        "\tdate = { day = 0 month = january year = 1937 }",
        f"\toffset = {offset}",
        "\tdeathdate = { day = 29 month = december year = 1964 }",
    ])


def event_text(lines: list[str]) -> str:
    return "\n".join(lines + ["}"])


def route_condition(route: Route) -> str:
    return route.route_trigger


def relationship_condition(route: Route) -> str:
    """Relationship accepted by partner-collapse and cross-theatre reactions."""
    if route.key == "sovereign":
        return f"OR = {{ {sovereign_member_condition('SIA')} {sovereign_member_condition('CHI')} }}"
    formal = {
        "allied": "OR = { alliance = { country = IND country = ENG } alliance = { country = IND country = USA } }",
        "german": "alliance = { country = IND country = GER }",
        "soviet": "alliance = { country = IND country = SOV }",
        "japan": "alliance = { country = IND country = JAP }",
        "sovereign": "flag = ind_v3_delhi_pact",
    }[route.key]
    return f"OR = {{ AND = {{ {route.compact_condition} }} {formal} }}"


def sovereign_member_condition(country: str) -> str:
    if country == "SIA":
        return "OR = { flag = ind_v3_delhi_pact alliance = { country = IND country = SIA } AND = { flag = ind_v42_delhi_pact_consultative flag = ind_v42_siam_accepts_delhi_pact } }"
    if country == "CHI":
        return "OR = { flag = ind_v3_delhi_pact alliance = { country = IND country = CHI } AND = { flag = ind_v42_delhi_pact_consultative flag = ind_v42_china_accepts_delhi_pact } }"
    raise ValueError(country)


def collapse_condition(route: Route) -> str:
    if route.key == "allied":
        return (
            "OR = { "
            "AND = { OR = { flag = ind_aubm_allied_partner_eng alliance = { country = IND country = ENG } } exists = ENG NOT = { control = { province = 29 data = ENG } } } "
            "AND = { OR = { flag = ind_aubm_allied_partner_usa alliance = { country = IND country = USA } } exists = USA NOT = { control = { province = 1809 data = USA } } } "
            "}"
        )
    if route.key == "sovereign":
        return (
            "OR = { "
            f"AND = {{ {sovereign_member_condition('SIA')} exists = SIA NOT = {{ war = {{ country = IND country = SIA }} }} NOT = {{ control = {{ province = 1423 data = SIA }} }} }} "
            f"AND = {{ {sovereign_member_condition('CHI')} exists = CHI NOT = {{ war = {{ country = IND country = CHI }} }} NOT = {{ control = {{ province = 1337 data = CHI }} }} }} "
            "}"
        )
    return route.collapse_condition


def crisis_available(route: Route) -> str:
    return f"AND = {{ year = 1937 {route_condition(route)} {route.compact_condition} {route.partner_war_condition} NOT = {{ flag = ind_aubm_bespoke_partner_crisis_{route.key}_resolved }} }}"


CRISIS_DOCKET_IDS = {
    "allied": 9289525,
    "german": 9289565,
    "soviet": 9289605,
    "japan": 9289653,
    "sovereign": 9289685,
}

CRISIS_CONFIRMATIONS = {
    "ENG": (9281920, "Britain"),
    "GER": (9281921, "Germany"),
    "SOV": (9281922, "the Soviet Union"),
    "JAP": (9281923, "Japan"),
    "USA": (9281924, "the United States"),
}

CRISIS_ROUTE_TARGETS = {
    "allied": ("GER", "JAP"),
    "german": ("ENG", "SOV", "USA"),
    "soviet": ("GER", "JAP", "ENG"),
    "japan": ("ENG", "USA", "SOV"),
    "sovereign": ("JAP", "SOV"),
}

CRISIS_ACTION_LABELS = {
    "allied": "Review war with Germany or Japan",
    "german": "Review war with Britain, USSR or America",
    "soviet": "Review war with Germany, Japan or Britain",
    "japan": "Review war with Britain, America or USSR",
    "sovereign": "Review separate war with Japan or the USSR",
}


def crisis_partner_enemy_condition(route: Route, country: str) -> str:
    """Require the named target to be at war with this route's real partner."""
    if route.key == "allied":
        return (
            "OR = { "
            f"war = {{ country = ENG country = {country} }} "
            f"war = {{ country = USA country = {country} }} "
            "}"
        )
    if route.key == "german":
        return f"war = {{ country = GER country = {country} }}"
    if route.key == "soviet":
        return f"war = {{ country = SOV country = {country} }}"
    if route.key == "japan":
        return f"war = {{ country = JAP country = {country} }}"
    if country == "JAP":
        return (
            "OR = { "
            f"AND = {{ {sovereign_member_condition('CHI')} war = {{ country = CHI country = JAP }} }} "
            f"AND = {{ {sovereign_member_condition('SIA')} war = {{ country = SIA country = JAP }} }} "
            "}"
        )
    if country == "SOV":
        return (
            "OR = { "
            "AND = { flag = ind_v3_delhi_pact war = { country = PER country = SOV } } "
            "AND = { flag = ind_v3_delhi_pact war = { country = AFG country = SOV } } "
            "}"
        )
    raise ValueError((route.key, country))


def declaration_legality(country: str) -> str:
    """Mirror the strategic-family exclusions on 41's confirmation events."""
    if country in {"ENG", "USA"}:
        return "NOT = { alliance = { country = IND country = ENG } } NOT = { alliance = { country = IND country = USA } } NOT = { flag = ind_aubm_commitment_allied }"
    if country == "GER":
        return "NOT = { alliance = { country = IND country = GER } } NOT = { flag = ind_aubm_commitment_german }"
    if country == "SOV":
        return "NOT = { alliance = { country = IND country = SOV } } NOT = { flag = ind_aubm_commitment_soviet }"
    if country == "JAP":
        return "NOT = { alliance = { country = IND country = JAP } } NOT = { flag = ind_aubm_commitment_japan }"
    raise ValueError(country)


def limited_support_effect_commands(route: Route) -> tuple[str, ...]:
    """Immediate, India-scoped payoff for the paid non-belligerent option."""
    support_flag = f"ind_aubm_bespoke_partner_crisis_{route.key}_limited_support"
    if route.key == "allied":
        relation_commands = (
            f"trigger = {{ flag = {support_flag} exists = ENG NOT = {{ war = {{ country = IND country = ENG }} }} }} type = relation which = ENG value = 10",
            f"trigger = {{ flag = {support_flag} exists = USA NOT = {{ war = {{ country = IND country = USA }} }} }} type = relation which = USA value = 10",
        )
    elif route.key in {"german", "soviet", "japan"}:
        partner = {"german": "GER", "soviet": "SOV", "japan": "JAP"}[route.key]
        relation_commands = (
            f"trigger = {{ flag = {support_flag} exists = {partner} NOT = {{ war = {{ country = IND country = {partner} }} }} }} type = relation which = {partner} value = 20",
        )
    else:
        relation_commands = (
            f"trigger = {{ flag = {support_flag} {sovereign_member_condition('SIA')} exists = SIA NOT = {{ war = {{ country = IND country = SIA }} }} }} type = relation which = SIA value = 10",
            f"trigger = {{ flag = {support_flag} {sovereign_member_condition('CHI')} exists = CHI NOT = {{ war = {{ country = IND country = CHI }} }} }} type = relation which = CHI value = 10",
            f"trigger = {{ flag = {support_flag} flag = ind_v3_delhi_pact exists = PER NOT = {{ war = {{ country = IND country = PER }} }} }} type = relation which = PER value = 10",
            f"trigger = {{ flag = {support_flag} flag = ind_v3_delhi_pact exists = AFG NOT = {{ war = {{ country = IND country = AFG }} }} }} type = relation which = AFG value = 10",
        )
    return (
        *relation_commands,
        f"trigger = {{ flag = {support_flag} }} type = setflag which = ind_aubm_coalition_consultation",
        f"trigger = {{ flag = {support_flag} }} type = dissent value = -1",
    )


def partner_dispatch_commands(route: Route, context: str) -> list[str]:
    pending = f"ind_aubm_bespoke_partner_response_{route.key}_pending"
    done = f"ind_aubm_bespoke_partner_response_{route.key}_done"
    request = f"ind_aubm_bespoke_partner_request_{route.key}_{context}"
    available = f"{relationship_condition(route)} NOT = {{ flag = {pending} }} NOT = {{ flag = {done} }}"
    if route.key == "allied":
        eng_invalid = "OR = { NOT = { exists = ENG } war = { country = IND country = ENG } }"
        usa_invalid = "OR = { NOT = { exists = USA } war = { country = IND country = USA } }"
        no_selection = "AND = { NOT = { flag = ind_aubm_allied_partner_eng } NOT = { flag = ind_aubm_allied_partner_usa } }"
        primary = f"flag = ind_aubm_allied_partner_eng exists = ENG NOT = {{ war = {{ country = IND country = ENG }} }} flag = {request} flag = {pending}"
        alternate = f"NOT = {{ flag = ind_aubm_allied_partner_eng }} flag = ind_aubm_allied_partner_usa exists = USA NOT = {{ war = {{ country = IND country = USA }} }} flag = {request} flag = {pending}"
        fallback_primary = f"OR = {{ {no_selection} AND = {{ NOT = {{ flag = ind_aubm_allied_partner_eng }} flag = ind_aubm_allied_partner_usa {usa_invalid} }} }} exists = ENG NOT = {{ war = {{ country = IND country = ENG }} }} flag = {request} flag = {pending}"
        fallback_alternate = f"OR = {{ AND = {{ {no_selection} {eng_invalid} }} AND = {{ flag = ind_aubm_allied_partner_eng {eng_invalid} }} }} exists = USA NOT = {{ war = {{ country = IND country = USA }} }} flag = {request} flag = {pending}"
        no_partner = f"{eng_invalid} {usa_invalid} flag = {request} flag = {pending}"
        dispatches = [
            f"\t\tcommand = {{ trigger = {{ {primary} }} type = event which = {route.base + 2} where = ENG when = 2 }}",
            f"\t\tcommand = {{ trigger = {{ {alternate} }} type = event which = {route.base + 21} where = USA when = 2 }}",
            f"\t\tcommand = {{ trigger = {{ {fallback_primary} }} type = event which = {route.base + 2} where = ENG when = 2 }}",
            f"\t\tcommand = {{ trigger = {{ {fallback_alternate} }} type = event which = {route.base + 21} where = USA when = 2 }}",
        ]
    else:
        primary_member = f"{sovereign_member_condition('SIA')} " if route.key == "sovereign" else ""
        alternate_member = f"{sovereign_member_condition('CHI')} " if route.key == "sovereign" else ""
        alternate_alliance = "" if route.key == "sovereign" else f"alliance = {{ country = IND country = {route.alternate_partner} }} "
        primary_invalid = f"OR = {{ NOT = {{ exists = {route.primary_partner} }} war = {{ country = IND country = {route.primary_partner} }} }}"
        alternate_invalid = f"OR = {{ NOT = {{ alliance = {{ country = IND country = {route.alternate_partner} }} }} NOT = {{ exists = {route.alternate_partner} }} war = {{ country = IND country = {route.alternate_partner} }} }}"
        if route.key == "sovereign":
            primary_invalid = f"OR = {{ NOT = {{ {sovereign_member_condition('SIA')} }} {primary_invalid} }}"
            alternate_invalid = f"OR = {{ NOT = {{ {sovereign_member_condition('CHI')} }} NOT = {{ exists = {route.alternate_partner} }} war = {{ country = IND country = {route.alternate_partner} }} }}"
        primary = f"{primary_member}exists = {route.primary_partner} NOT = {{ war = {{ country = IND country = {route.primary_partner} }} }} flag = {request} flag = {pending}"
        alternate = f"{alternate_member}{primary_invalid} {alternate_alliance}exists = {route.alternate_partner} NOT = {{ war = {{ country = IND country = {route.alternate_partner} }} }} flag = {request} flag = {pending}"
        no_partner = f"{primary_invalid} {alternate_invalid} flag = {request} flag = {pending}"
        dispatches = [
            f"\t\tcommand = {{ trigger = {{ {primary} }} type = event which = {route.base + 2} where = {route.primary_partner} when = 2 }}",
            f"\t\tcommand = {{ trigger = {{ {alternate} }} type = event which = {route.base + 21} where = {route.alternate_partner} when = 2 }}",
        ]
    return [
        f"\t\tcommand = {{ trigger = {{ {available} }} type = setflag which = {request} }}",
        f"\t\tcommand = {{ trigger = {{ flag = {request} {available} }} type = setflag which = {pending} }}",
        *dispatches,
        f"\t\tcommand = {{ trigger = {{ {no_partner} }} type = setflag which = ind_aubm_bespoke_partner_response_{route.key}_absent }}",
        f"\t\tcommand = {{ trigger = {{ {no_partner} }} type = setflag which = {done} }}",
        f"\t\tcommand = {{ trigger = {{ {no_partner} }} type = clrflag which = {pending} }}",
    ]


def render_dispatcher() -> str:
    lines = header(DISPATCHER_ID)
    lines.extend([
        '\tname = "Authored Strategic Campaigns"',
        '\tdesc = "Open the current route-specific operations board, answer an available compact-partner war crisis, inspect the shared national campaign ledger, or return to the War Cabinet. This doorway is available only through the current War Cabinet gate and never declares war by itself."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_grand_strategy"',
        "\taction_a = {",
        f"\t\ttrigger = {{ OR = {{ {' '.join(route_condition(route) for route in ROUTES)} }} }}",
        '\t\tname = "Open the current authored route plan"',
    ])
    for route in ROUTES:
        lines.append(f"\t\tcommand = {{ trigger = {{ {route_condition(route)} }} type = event which = {route.base} where = IND when = 1 }}")
    lines.extend([
        "\t}",
        "\taction_b = {",
        f"\t\ttrigger = {{ OR = {{ {' '.join(crisis_available(route) for route in ROUTES)} }} }}",
        '\t\tname = "Answer the current compact-partner war crisis"',
    ])
    for route in ROUTES:
        lines.append(f"\t\tcommand = {{ trigger = {{ {crisis_available(route)} }} type = event which = {route.base + 1} where = IND when = 1 }}")
    lines.extend([
        "\t}",
        "\taction_c = {",
        '\t\tname = "Open the shared campaign and settlement ledger"',
        "\t\tcommand = { type = event which = 9281913 where = IND when = 1 }",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to the War Cabinet"',
        "\t\tcommand = { type = event which = 9281001 where = IND when = 1 }",
        "\t}",
    ])
    return event_text(lines)


def render_status(route: Route) -> str:
    lines = header(route.base)
    lines.extend([
        f'\tname = "{route.status_name}"',
        f'\tdesc = "{route.status_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
        "\taction_a = {",
    ])
    if route.key == "japan":
        lines.extend([
            f"\t\ttrigger = {{ year = 1937 flag = {ALPHA23_CONTRACT_FLAG} {relationship_condition(route)} }}",
            '\t\tname = "Open the multi-theatre Delhi-Tokyo grand-campaign ledger"',
            f"\t\tcommand = {{ type = event which = {route.base + 25} where = IND when = 1 }}",
        ])
    else:
        lines.append('\t\tname = "Keep the selected focus on the operations map"')
    lines.extend([
        "\t}",
        "\taction_b = {",
        '\t\tname = "Record cumulative secondary theatre standing"',
        f"\t\tcommand = {{ type = event which = {route.base + 3} where = IND when = 1 }}",
        "\t}",
        "\taction_c = {",
        '\t\tname = "Open the shared national campaign ledger"',
        "\t\tcommand = { type = event which = 9281913 where = IND when = 1 }",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to authored strategic campaigns"',
        f"\t\tcommand = {{ type = event which = {DISPATCHER_ID} where = IND when = 1 }}",
        "\t}",
    ])
    return event_text(lines)


def render_crisis(route: Route) -> str:
    lines = header(route.base + 1)
    availability = crisis_available(route)
    lines.extend([
        "\ttrigger = {",
        f"\t\t{availability}",
        "\t}",
        f'\tname = "{route.crisis_name}"',
        f'\tdesc = "{route.crisis_desc} Paid support immediately improves partner relations and earns shared settlement consultation standing."',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    dated(lines, offset=3)
    lines.append("\taction_a = {")
    if route.key == "sovereign":
        lines.extend([
            '\t\tname = "Publish an independent Indian response plan"',
            "\t\tcommand = { type = setflag which = ind_aubm_bespoke_partner_crisis_sovereign_independent_plan }",
            "\t\tcommand = { type = setflag which = ind_aubm_bespoke_partner_crisis_sovereign_resolved }",
        ])
    else:
        lines.extend([
            '\t\tname = "Seek formal entry; inherit every partner war"',
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_formal_review }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_resolved }}",
            "\t\tcommand = { type = event which = 9281910 where = IND when = 1 }",
        ])
    lines.extend([
        "\t}",
        "\taction_b = {",
        f'\t\tname = "{CRISIS_ACTION_LABELS[route.key]}"',
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_separate_campaign }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_resolved }}",
    ])
    lines.append(f"\t\tcommand = {{ type = event which = {CRISIS_DOCKET_IDS[route.key]} where = IND when = 1 }}")
    lines.extend([
        "\t}",
        "\taction_c = {",
        '\t\tname = "Send support; earn consultation: -600 supplies/-150 money"',
    ])
    support_cost = ("supplies value = -600", "money value = -150")
    append_affordability(lines, support_cost)
    lines.extend([
        "\t\tcommand = { type = supplies value = -600 }",
        "\t\tcommand = { type = money value = -150 }",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_limited_support }}",
    ])
    for command in limited_support_effect_commands(route):
        lines.append(f"\t\tcommand = {{ {command} }}")
    lines.append(f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_resolved }}")
    lines.extend(["\t}", "\taction_d = {"])
    if route.key == "sovereign":
        lines.extend([
            '\t\tname = "Maintain armed neutrality and Delhi Pact talks"',
            "\t\tcommand = { type = setflag which = ind_aubm_bespoke_partner_crisis_sovereign_armed_neutrality }",
            "\t\tcommand = { type = setflag which = ind_aubm_bespoke_partner_crisis_sovereign_resolved }",
            "\t\tcommand = { type = dissent value = 1 }",
        ])
    else:
        lines.extend([
            '\t\tname = "Remain outside and review peaceful withdrawal"',
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_neutral }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_crisis_{route.key}_resolved }}",
            "\t\tcommand = { type = event which = 9281910 where = IND when = 1 }",
        ])
    lines.append("\t}")
    return event_text(lines)


def render_crisis_docket(route: Route) -> str:
    """Manual-only bridge to the existing, constitutionally checked war flow."""
    lines = header(CRISIS_DOCKET_IDS[route.key])
    lines.extend([
        f'\tname = "{route.status_name}: Separate-War Docket"',
        f'\tdesc = "The partner crisis names only {route.crisis_targets}. Each available action requires that enemy to remain at war with the route partner and sends India to the existing confirmation and Foreign Ministry executor. This docket neither declares war nor changes a settlement."',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    for letter, country in zip("abc", CRISIS_ROUTE_TARGETS[route.key]):
        confirmation_id, country_name = CRISIS_CONFIRMATIONS[country]
        lines.extend([
            f"\taction_{letter} = {{",
            "\t\ttrigger = {",
            f"\t\t\tyear = 1937 flag = {ALPHA23_CONTRACT_FLAG}",
            f"\t\t\t{route_condition(route)}",
            f"\t\t\t{relationship_condition(route)}",
            f"\t\t\tflag = ind_aubm_bespoke_partner_crisis_{route.key}_separate_campaign",
            f"\t\t\texists = {country}",
            f"\t\t\tNOT = {{ war = {{ country = IND country = {country} }} }}",
            f"\t\t\t{crisis_partner_enemy_condition(route, country)}",
            f"\t\t\t{declaration_legality(country)}",
            "\t\t}",
            f'\t\tname = "Review a separate war against {country_name}"',
            f"\t\tcommand = {{ type = event which = {confirmation_id} where = IND when = 1 }}",
            "\t}",
        ])
    return_letter = "d" if len(CRISIS_ROUTE_TARGETS[route.key]) == 3 else "c"
    lines.extend([
        f"\taction_{return_letter} = {{",
        '\t\tname = "Return without widening the war"',
        f"\t\tcommand = {{ type = event which = {DISPATCHER_ID} where = IND when = 1 }}",
        "\t}",
    ])
    return event_text(lines)


def render_partner_response(route: Route, event_id: int, country: str) -> str:
    lines = header(event_id, country)
    lines.extend([
        f'\tname = "{route.partner_response_name}"',
        f'\tdesc = "{route.partner_response_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
        "\taction_a = {",
        "\t\tai_chance = 55",
        '\t\tname = "Recognize the Indian command doctrine"',
        "\t\tcommand = { type = relation which = IND value = 25 }",
        f"\t\tcommand = {{ type = event which = {route.base + 22} where = IND when = 2 }}",
        "\t}",
        "\taction_b = {",
        "\t\tai_chance = 30",
        '\t\tname = "Demand consultation and narrower Indian claims"',
        "\t\tcommand = { type = relation which = IND value = 5 }",
        f"\t\tcommand = {{ type = event which = {route.base + 23} where = IND when = 2 }}",
        "\t}",
        "\taction_c = {",
        "\t\tai_chance = 15",
        '\t\tname = "Refuse to support the independent Indian theatre"',
        "\t\tcommand = { type = relation which = IND value = -20 }",
        f"\t\tcommand = {{ type = event which = {route.base + 24} where = IND when = 2 }}",
        "\t}",
    ])
    return event_text(lines)


def render_secondary(route: Route) -> str:
    lines = header(route.base + 3, one_action=True)
    lines.extend([
        f'\tname = "{route.status_name}: Secondary Theatre Ledger"',
        '\tdesc = "This zero-reward review preserves cumulative secondary standing without completing or blocking the selected primary focus. Historical victories remain recorded even when current settlement leverage is suspended."',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
        "\taction_a = {",
        '\t\tname = "Record current historical standing; no primary reward"',
        f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_national_southern_victory }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_southern }}",
        f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_national_western_victory }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_western }}",
        f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_national_northern_victory }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_northern }}",
        f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_sea_theatre_achieved }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_southeast_asia }}",
        f"\t\tcommand = {{ trigger = {{ OR = {{ flag = ind_aubm_european_capital_victory flag = ind_aubm_pacific_capital_victory flag = ind_aubm_decisive_great_power }} }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_great_power }}",
        f"\t\tcommand = {{ trigger = {{ flag = ind_aubm_global_campaign_victory }} type = setflag which = ind_aubm_bespoke_secondary_{route.key}_worldwide }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_secondary_ledger_{route.key} }}",
        "\t}",
    ])
    return event_text(lines)


def render_collapse(route: Route) -> str:
    lines = header(route.base + 4)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\t{route_condition(route)}",
        f"\t\t{relationship_condition(route)}",
        f"\t\t{collapse_condition(route)}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_partner_collapse_{route.key}_handled }}",
        "\t\tNOT = { flag = ind_aubm_postwar_congress_completed }",
        "\t}",
        f'\tname = "{route.collapse_name}"',
        f'\tdesc = "{route.collapse_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    if route.key == "german":
        lines.insert(lines.index("\t\tNOT = { flag = ind_aubm_postwar_congress_completed }"), "\t\tNOT = { flag = ind_gc_german_collapse_answered }")
    dated(lines, offset=5)
    for letter, option in zip("abcd", route.collapse_choices):
        lines.extend([
            f"\taction_{letter} = {{",
            f'\t\tname = "{option.label}"',
        ])
        append_affordability(lines, option.commands)
        lines.append(f"\t\tcommand = {{ type = setflag which = {option.flag} }}")
        for command in option.commands:
            lines.append(f"\t\tcommand = {{ type = {command} }}")
        lines.extend([
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_collapse_{route.key}_handled }}",
            *( ["\t\tcommand = { type = setflag which = ind_gc_german_collapse_answered }"] if route.key == "german" else [] ),
            "\t}",
        ])
    return event_text(lines)


def render_activation(route: Route, focus: Focus, event_id: int) -> str:
    active_flag = f"ind_aubm_bespoke_focus_active_{route.key}_{focus.key}"
    lines = header(event_id)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        "\t\tflag = ind_aubm_wartime_framework",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\t{route_condition(route)}",
        f"\t\tflag = ind_aubm_route_focus_{route.key}_{focus.key}",
        f"\t\tOR = {{ AND = {{ atwar = yes {focus.activation_condition} }} {focus.culmination_condition} }}",
        "\t\tNOT = { flag = ind_aubm_route_war_achievement }",
        f"\t\tNOT = {{ flag = {active_flag} }}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key} }}",
        "\t\tNOT = { flag = ind_aubm_postwar_congress_completed }",
        "\t}",
        f'\tname = "{focus.activation_name}"',
        f'\tdesc = "{focus.activation_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    dated(lines, offset=2)
    lines.extend([
        "\taction_a = {",
        f'\t\tname = "Activate {focus.label}"',
        f"\t\tcommand = {{ type = setflag which = {active_flag} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_primary_focus_active_{route.key} }}",
        "\t}",
    ])
    return event_text(lines)


def render_intermediate(route: Route, focus: Focus, event_id: int) -> str:
    lines = header(event_id)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        "\t\tflag = ind_aubm_wartime_framework",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\t{route_condition(route)}",
        f"\t\tflag = ind_aubm_route_focus_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_active_{route.key}_{focus.key}",
        f"\t\tOR = {{ AND = {{ atwar = yes {focus.intermediate_condition} }} {focus.culmination_condition} }}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_intermediate_{route.key}_{focus.key} }}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key} }}",
        "\t}",
        f'\tname = "{focus.intermediate_name}"',
        f'\tdesc = "{focus.intermediate_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    dated(lines, offset=3)
    lines.extend([
        "\taction_a = {",
        '\t\tname = "Record the intermediate objective"',
    ])
    for command in focus.intermediate_commands:
        lines.append(f"\t\tcommand = {{ type = {command} }}")
    lines.extend([
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_focus_intermediate_{route.key}_{focus.key} }}",
        "\t}",
    ])
    return event_text(lines)


def render_dilemma(route: Route, focus: Focus, event_id: int) -> str:
    lines = header(event_id)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        "\t\tflag = ind_aubm_wartime_framework",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\t{route_condition(route)}",
        f"\t\tflag = ind_aubm_route_focus_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_active_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_intermediate_{route.key}_{focus.key}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_dilemma_{route.key}_{focus.key} }}",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key} }}",
        f"\t\tOR = {{ atwar = yes {focus.culmination_condition} }}",
        "\t}",
        f'\tname = "{focus.dilemma_name}"',
        f'\tdesc = "{focus.dilemma_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    if all(resource_costs(option.commands) for option in focus.choices):
        gate = "\t\tOR = { " + " ".join(affordability_clause(option.commands) for option in focus.choices) + " }"
        lines.insert(lines.index("\t}"), gate)
    dated(lines, offset=2)
    for letter, option in zip("abcd", focus.choices):
        lines.extend([
            f"\taction_{letter} = {{",
            f'\t\tname = "{option.label}"',
        ])
        append_affordability(lines, option.commands)
        lines.append(f"\t\tcommand = {{ type = setflag which = {option.flag} }}")
        for command in option.commands:
            lines.append(f"\t\tcommand = {{ type = {command} }}")
        lines.extend([
            f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_focus_dilemma_{route.key}_{focus.key} }}",
        ])
        lines.extend(partner_dispatch_commands(route, f"focus_{focus.key}"))
        lines.append("\t}")
    return event_text(lines)


def render_culmination(route: Route, focus: Focus, event_id: int) -> str:
    lines = header(event_id)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        "\t\tflag = ind_aubm_wartime_framework",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\t{route_condition(route)}",
        f"\t\tflag = ind_aubm_route_focus_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_active_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_intermediate_{route.key}_{focus.key}",
        f"\t\tflag = ind_aubm_bespoke_focus_dilemma_{route.key}_{focus.key}",
        f"\t\t{focus.culmination_condition}",
        "\t\tNOT = { flag = ind_aubm_route_war_achievement }",
        f"\t\tNOT = {{ flag = ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key} }}",
        "\t\tNOT = { flag = ind_aubm_postwar_congress_completed }",
        "\t}",
        f'\tname = "{focus.culmination_name}"',
        f'\tdesc = "{focus.culmination_desc}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
    ])
    dated(lines, offset=2)
    lines.extend([
        "\taction_a = {",
        "\t\tname = \"Enter the completed authored focus in India's war ledger\"",
    ])
    for command in focus.culmination_commands:
        lines.append(f"\t\tcommand = {{ type = {command} }}")
    lines.extend([
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_focus_culminated_{route.key}_{focus.key} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_route_culminated_{route.key} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key}_{focus.key} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_congress_entitlement_{route.key} }}",
        "\t\tcommand = { type = setflag which = ind_aubm_route_war_achievement }",
        "\t}",
    ])
    return event_text(lines)


def render_callback(route: Route, event_id: int, result: str, reward: tuple[str, ...]) -> str:
    lines = header(event_id, one_action=True)
    title = {"accepted": "Partner Recognition", "countered": "Partner Counterproposal", "refused": "Partner Refusal"}[result]
    description = {
        "accepted": f"{route.partner_name} recognizes India's current operational doctrine and releases limited support while preserving the route's separate legal settlements.",
        "countered": f"{route.partner_name} accepts consultation but narrows the political claim. India retains the selected focus and may still complete it under its own command.",
        "refused": f"{route.partner_name} refuses the requested operational recognition. The Indian campaign remains legal and active, but Delhi must carry the burden without partner endorsement.",
    }[result]
    lines.extend([
        f"\ttrigger = {{ {route_condition(route)} flag = ind_aubm_bespoke_partner_response_{route.key}_pending NOT = {{ flag = ind_aubm_bespoke_partner_response_{route.key}_done }} }}",
        f'\tname = "{route.status_name}: {title}"',
        f'\tdesc = "{description}"',
        "\tstyle = 2",
        f'\tpicture = "{route.picture}"',
        "\taction_a = {",
        '\t\tname = "Record the response in the route ledger"',
        f"\t\tcommand = {{ type = clrflag which = ind_aubm_bespoke_partner_response_{route.key}_pending }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_response_{route.key}_{result} }}",
        f"\t\tcommand = {{ type = setflag which = ind_aubm_bespoke_partner_response_{route.key}_done }}",
    ])
    for command in reward:
        lines.append(f"\t\tcommand = {{ type = {command} }}")
    lines.append("\t}")
    return event_text(lines)


def render_japan_grand_campaign() -> str:
    """Optional cumulative chapters for the user's multi-theatre Japan run."""
    base = 9289620
    relationship = relationship_condition(next(route for route in ROUTES if route.key == "japan"))
    events: list[str] = []

    lines = header(base + 25)
    lines.extend([
        f"\ttrigger = {{ year = 1937 flag = {ALPHA23_CONTRACT_FLAG} flag = ind_aubm_route_japan {relationship} }}",
        '\tname = "Delhi-Tokyo Multi-Theatre Campaign Ledger"',
        '\tdesc = "The selected charter focus remains India\'s only automatic primary arc. This optional ledger records a human-led grand campaign across Southeast Asia and Australia, China and the Philippines, Aden-Suez-East Africa, and the Caucasus without stealing settlement authority from the country boards."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_tokyo_proposition"',
        "\taction_a = {",
        '\t\tname = "Review Asian and Australian operations"',
        f"\t\tcommand = {{ type = event which = {base + 26} where = IND when = 1 }}",
        "\t}",
        "\taction_b = {",
        '\t\tname = "Review the staged Aden-Suez-East Africa chapter"',
        f"\t\tcommand = {{ type = event which = {base + 27} where = IND when = 1 }}",
        "\t}",
        "\taction_c = {",
        '\t\tname = "Review the northern coalition and Caucasus relief"',
        f"\t\tcommand = {{ type = event which = {base + 28} where = IND when = 1 }}",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to the Delhi-Tokyo operations board"',
        f"\t\tcommand = {{ type = event which = {base} where = IND when = 1 }}",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 26)
    lines.extend([
        '\tname = "Asian Operational Allocations"',
        '\tdesc = "Formal alliance makes China an inherited coalition war, but it does not decide who commands Indian formations. Philippine allocation and the Southeast Asia-Australia chapter are separately acknowledged battlefield milestones; their legal settlements remain in the shared country systems."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_tokyo_proposition"',
        "\taction_a = {",
        '\t\ttrigger = { alliance = { country = IND country = JAP } OR = { AND = { war = { country = IND country = CHI } war = { country = JAP country = CHI } } AND = { war = { country = IND country = CHC } war = { country = JAP country = CHC } } } NOT = { flag = ind_aubm_japan_grand_china_posture } }',
        '\t\tname = "Publish formal-alliance China field-command boundaries"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_china_posture }",
        "\t\tcommand = { type = setflag which = ind_aubm_coalition_consultation }",
        "\t}",
        "\taction_b = {",
        '\t\ttrigger = { OR = { flag = ind_aubm_sea_land_philippines flag = ind_aubm_sea_land_philippines_liberated flag = ind_aubm_sea_land_philippines_liberated_current } NOT = { flag = ind_aubm_japan_grand_philippines_allocation } }',
        '\t\tname = "Record the Philippines allocation milestone"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_philippines_allocation }",
        "\t}",
        "\taction_c = {",
        '\t\ttrigger = { OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_jp_southern_victory flag = ind_aubm_national_southern_victory } flag = ind_aubm_regional_victory_ast NOT = { flag = ind_aubm_japan_grand_southern_australia } }',
        '\t\tname = "Record the Southeast Asia-Australia chapter"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_southern_australia }",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to the multi-theatre ledger"',
        f"\t\tcommand = {{ type = event which = {base + 25} where = IND when = 1 }}",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 27)
    lines.extend([
        '\tname = "The Western Ocean Road: Three Stages"',
        '\tdesc = "The route is deliberately staged. Aden opens the Red Sea hinge; Suez connects it to the Mediterranean; an East African campaign result turns ports into a durable ocean system. Each stage records command only and never transfers territory or signs peace."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_indian_ocean_war"',
        "\taction_a = {",
        '\t\ttrigger = { control = { province = 1053 data = IND } NOT = { flag = ind_aubm_japan_grand_ocean_aden } }',
        '\t\tname = "Stage I: record Indian control of Aden"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_ocean_aden }",
        "\t}",
        "\taction_b = {",
        '\t\ttrigger = { flag = ind_aubm_japan_grand_ocean_aden control = { province = 900 data = IND } NOT = { flag = ind_aubm_japan_grand_ocean_suez } }',
        '\t\tname = "Stage II: connect Aden to Suez"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_ocean_suez }",
        "\t}",
        "\taction_c = {",
        '\t\ttrigger = { flag = ind_aubm_japan_grand_ocean_suez OR = { flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf flag = ind_aubm_national_western_victory } NOT = { flag = ind_aubm_japan_grand_ocean_africa } }',
        '\t\tname = "Stage III: complete the East African ocean system"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_ocean_africa }",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to the multi-theatre ledger"',
        f"\t\tcommand = {{ type = event which = {base + 25} where = IND when = 1 }}",
        "\t}",
    ])
    events.append(event_text(lines))

    relief_trigger = (
        f"year = 1937 flag = {ALPHA23_CONTRACT_FLAG} flag = ind_aubm_route_japan {relationship} "
        "war = { country = IND country = SOV } war = { country = GER country = SOV } "
        "exists = GER control = { province = 163 data = GER } control = { province = 713 data = IND } "
        "OR = { control = { province = 709 data = IND } control = { province = 706 data = IND } } "
        "NOT = { flag = ind_aubm_japan_caucasus_relief_handled }"
    )
    lines = header(base + 28)
    lines.extend([
        '\tname = "Northern Coalition and Caucasus Relief"',
        '\tdesc = "Both formal Delhi-Tokyo alliance and separate compact service can support an Indian Soviet front. Once India holds Baku and either Tbilisi or Astrakhan while Germany still holds Berlin and fights Moscow, Delhi may fund one modest, explicitly German-scoped relief convoy."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_barbarossa_reaction"',
        "\taction_a = {",
        f'\t\ttrigger = {{ {relationship} war = {{ country = IND country = SOV }} NOT = {{ flag = ind_aubm_japan_grand_northern_posture }} }}',
        '\t\tname = "Record the formal-or-compact northern operational posture"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_northern_posture }",
        "\t}",
        "\taction_b = {",
        '\t\ttrigger = { control = { province = 713 data = IND } OR = { control = { province = 709 data = IND } control = { province = 706 data = IND } } NOT = { flag = ind_aubm_japan_grand_caucasus_gate } }',
        '\t\tname = "Record Baku plus the Tbilisi-Astrakhan Caucasus gate"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_caucasus_gate }",
        "\t}",
        "\taction_c = {",
        f"\t\ttrigger = {{ {relief_trigger} }}",
        '\t\tname = "Convene the Delhi-Tokyo-Berlin relief decision"',
        f"\t\tcommand = {{ type = event which = {base + 29} where = IND when = 1 }}",
        "\t}",
        "\taction_d = {",
        '\t\tname = "Return to the multi-theatre ledger"',
        f"\t\tcommand = {{ type = event which = {base + 25} where = IND when = 1 }}",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 29)
    lines.extend([
        f"\ttrigger = {{ {relief_trigger} }}",
        '\tname = "The Delhi-Tokyo-Berlin Caucasus Lifeline"',
        '\tdesc = "Indian control of Baku and the Caucasus gate can sustain Germany without granting Berlin a passive global bonus. Delhi must pay the full convoy cost; only the German-country callback receives the smaller delivered stockpile."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_barbarossa_reaction"',
    ])
    lines.extend([
        "\taction_a = {",
        '\t\tname = "Dispatch one relief convoy: -1200 supplies/-500 oil"',
    ])
    relief_cost = ("supplies value = -1200", "oilpool value = -500")
    append_affordability(lines, relief_cost)
    lines.extend([
        "\t\tcommand = { type = supplies value = -1200 }",
        "\t\tcommand = { type = oilpool value = -500 }",
        "\t\tcommand = { type = setflag which = ind_aubm_japan_caucasus_relief_handled }",
        "\t\tcommand = { type = setflag which = ind_aubm_japan_caucasus_relief_dispatched }",
        f"\t\tcommand = {{ type = event which = {base + 30} where = GER when = 2 }}",
        "\t}",
        "\taction_b = {",
        '\t\tname = "Defer the convoy; keep the option open"',
        "\t}",
        "\taction_c = {",
        '\t\tname = "Decline German relief and preserve Indian stocks"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_caucasus_relief_handled }",
        "\t\tcommand = { type = setflag which = ind_aubm_japan_caucasus_relief_declined }",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 30, "GER", one_action=True)
    lines.extend([
        '\ttrigger = { NOT = { flag = ger_aubm_indian_caucasus_relief_received } }',
        '\tname = "Indian Relief Reaches the German Caucasus Front"',
        '\tdesc = "A finite Indian convoy has crossed the Baku corridor. Germany receives only the delivered portion; the effect belongs to Germany and cannot become a passive world modifier."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_barbarossa_reaction"',
        "\taction_a = {",
        '\t\tname = "Receive 900 supplies and 350 oil"',
        "\t\tcommand = { type = supplies value = 900 }",
        "\t\tcommand = { type = oilpool value = 350 }",
        "\t\tcommand = { type = setflag which = ger_aubm_indian_caucasus_relief_received }",
        f"\t\tcommand = {{ type = event which = {base + 31} where = IND when = 2 }}",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 31, one_action=True)
    lines.extend([
        '\tname = "Berlin Confirms the Indian Relief Convoy"',
        '\tdesc = "Germany confirms receipt of the limited convoy. India gains only operational acknowledgement; Baku, Tbilisi, Astrakhan and every future settlement remain governed by their existing legal systems."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_barbarossa_reaction"',
        "\taction_a = {",
        '\t\tname = "Record the completed Caucasus relief chapter"',
        "\t\tcommand = { type = setflag which = ind_aubm_japan_caucasus_relief_delivered }",
        "\t\tcommand = { type = setflag which = ind_aubm_coalition_credit }",
        "\t}",
    ])
    events.append(event_text(lines))

    lines = header(base + 32, one_action=True)
    lines.extend([
        "\ttrigger = {",
        f"\t\tyear = 1937 flag = {ALPHA23_CONTRACT_FLAG} flag = ind_aubm_route_japan",
        "\t\tflag = ind_aubm_japan_grand_southern_australia",
        "\t\tflag = ind_aubm_japan_grand_china_posture",
        "\t\tOR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc }",
        "\t\tflag = ind_aubm_japan_grand_philippines_allocation",
        "\t\tflag = ind_aubm_japan_grand_ocean_africa",
        "\t\tflag = ind_aubm_japan_caucasus_relief_delivered",
        "\t\tNOT = { flag = ind_aubm_japan_grand_campaign_complete }",
        "\t}",
        '\tname = "India Completes the Four-Theatre Grand Campaign"',
        '\tdesc = "One campaign now links Southeast Asia and Australia, the China-Philippines allocation, Aden-Suez-East Africa, and the Caucasus relief road. This is cumulative secondary acknowledgement, not a second primary charter award and not an automatic territorial settlement."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_tokyo_proposition"',
    ])
    dated(lines, offset=5)
    lines.extend([
        "\taction_a = {",
        '\t\tname = "Record the grand campaign as secondary credit"',
        "\t\tcommand = { type = money value = 200 }",
        "\t\tcommand = { type = supplies value = 300 }",
        "\t\tcommand = { type = dissent value = -2 }",
        "\t\tcommand = { type = setflag which = ind_aubm_japan_grand_campaign_complete }",
        "\t\tcommand = { type = setflag which = ind_aubm_bespoke_secondary_japan_grand_campaign }",
        "\t}",
    ])
    events.append(event_text(lines))
    return "\n\n".join(events)


def resettable_current_flags() -> tuple[str, ...]:
    """Live route state cleared by lawful withdrawal; historical credit survives."""
    flags = {ALPHA23_CONTRACT_FLAG}
    for route in ROUTES:
        flags.update({
            f"ind_aubm_route_charter_{route.key}",
            f"ind_aubm_bespoke_primary_focus_active_{route.key}",
            f"ind_aubm_bespoke_partner_response_{route.key}_pending",
            f"ind_aubm_bespoke_partner_request_{route.key}_crisis",
        })
        for focus in route.focuses:
            flags.update({
                f"ind_aubm_route_focus_{route.key}_{focus.key}",
                f"ind_aubm_bespoke_focus_active_{route.key}_{focus.key}",
                f"ind_aubm_bespoke_partner_request_{route.key}_focus_{focus.key}",
            })
    return tuple(sorted(flags))


def render_route_mismatch_watchdog() -> str:
    mismatches = " ".join(
        f"AND = {{ flag = ind_aubm_route_charter_{route.key} NOT = {{ {route_condition(route)} }} }}"
        for route in ROUTES
    )
    lines = header(9289698, one_action=True)
    lines.extend([
        "\ttrigger = {",
        "\t\tyear = 1937",
        f"\t\tflag = {ALPHA23_CONTRACT_FLAG}",
        f"\t\tOR = {{ {mismatches} }}",
        "\t}",
        '\tname = "The Authored Route Contract No Longer Matches"',
        '\tdesc = "Partner collapse, partner hostility or a new strategic family has changed India\'s canonical route. This single acknowledgement archives the obsolete live charter. Paid stages and every earned historical result remain protected against replay."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_grand_strategy"',
    ])
    dated(lines, offset=1)
    lines.extend([
        "\taction_a = {",
        '\t\tname = "Archive the obsolete route contract"',
    ])
    for flag in resettable_current_flags():
        lines.append(f"\t\tcommand = {{ type = clrflag which = {flag} }}")
    lines.extend([
        "\t\tcommand = { type = setflag which = ind_aubm_bespoke_route_contract_reset_alpha23 }",
        "\t}",
    ])
    return event_text(lines)


def render_route_reset() -> str:
    lines = header(9289699, one_action=True)
    lines.extend([
        '\tname = "Close the Current Authored Route Contract"',
        '\tdesc = "Lawful withdrawal clears only the active Alpha 23 contract, charter selection, focus activation and pending foreign request. Paid intermediate and dilemma guards, partner and collapse results, crises, grand-campaign history, culminations, achievements and congress entitlements remain permanent so no reward can be replayed."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_grand_strategy"',
        "\taction_a = {",
        '\t\tname = "Archive current plans; preserve earned history"',
    ])
    for flag in resettable_current_flags():
        lines.append(f"\t\tcommand = {{ type = clrflag which = {flag} }}")
    lines.extend([
        "\t\tcommand = { type = setflag which = ind_aubm_bespoke_route_contract_reset_alpha23 }",
        "\t}",
    ])
    return event_text(lines)


def render_route(route: Route) -> str:
    events = [
        render_status(route),
        render_crisis(route),
        render_partner_response(route, route.base + 2, route.primary_partner),
        render_secondary(route),
        render_collapse(route),
    ]
    for index, focus in enumerate(route.focuses):
        events.append(render_activation(route, focus, route.base + 5 + index))
    for index, focus in enumerate(route.focuses):
        events.append(render_intermediate(route, focus, route.base + 9 + index))
    for index, focus in enumerate(route.focuses):
        events.append(render_dilemma(route, focus, route.base + 13 + index))
    for index, focus in enumerate(route.focuses):
        events.append(render_culmination(route, focus, route.base + 17 + index))
    events.extend([
        render_partner_response(route, route.base + 21, route.alternate_partner),
        render_callback(route, route.base + 22, "accepted", route.response_rewards[0]),
        render_callback(route, route.base + 23, "countered", route.response_rewards[1]),
        render_callback(route, route.base + 24, "refused", route.response_rewards[2]),
        render_crisis_docket(route),
    ])
    if route.key == "japan":
        events.append(render_japan_grand_campaign())
    return "\n\n".join(events)


def render() -> str:
    return (
        "#########################################################################\n"
        "# A Union Before Midnight V4: authored strategic-route campaign arcs\n"
        "# Generated by tools/generate_aubm_bespoke_route_arcs.py; do not edit.\n"
        "#########################################################################\n\n"
        + render_dispatcher()
        + "\n\n"
        + "\n\n".join(render_route(route) for route in ROUTES)
        + "\n\n"
        + render_route_mismatch_watchdog()
        + "\n\n"
        + render_route_reset()
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="ascii") != generated:
            print(f"STALE: {OUTPUT.relative_to(ROOT)}")
            return 1
        print("OK: five bespoke strategic-route overlays are current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generated, encoding="ascii", newline="\n")
    print(f"WROTE: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
