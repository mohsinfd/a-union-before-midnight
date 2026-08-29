#!/usr/bin/env python3
"""Generate route-specific wartime charters, achievements and congresses."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "mod/db/events/aubm_v4/48_route_wartime_consequences.txt"


LEGACY_WARTIME_IDS = (
    *range(9280400, 9280406),
    9281220, 9281221, 9281222, 9281223, 9281224, 9281229,
    *range(9281230, 9281239), 9281240, 9281241, 9281242, 9281243,
    *range(9281250, 9281276),
    *range(9281341, 9281349), *range(9281350, 9281353),
    *range(9281354, 9281356), 9281359, *range(9281360, 9281386),
    *range(9281460, 9281469), *range(9281470, 9281497),
    *range(9281551, 9281566), *range(9281570, 9281596),
)


@dataclass(frozen=True)
class Focus:
    key: str
    label: str
    achievement_name: str
    achievement_desc: str
    trigger: str
    reward: tuple[str, ...]


@dataclass(frozen=True)
class Route:
    key: str
    route_flag: str
    charter_name: str
    charter_desc: str
    picture: str
    focuses: tuple[Focus, ...]
    congress_name: str
    congress_desc: str
    legacy_flag: str
    relations: tuple[str, ...]


ROUTES = (
    Route(
        "allied",
        "ind_aubm_route_allied",
        "The Delhi Allied War Charter",
        "India must decide what equality inside or beside the Allied system means in operations. Eastern Ocean Command makes Japan and the southern resource arc the test. Continental Command measures India in Europe. The Anti-Colonial Mandate makes liberation and regional settlements the test. Free Command asks only for a decisive Indian victory, independent of Allied priorities.",
        "aubm_v4_london_settlement",
        (
            Focus("eastern", "Eastern Ocean Command", "Delhi Is Recognized as the Allied Eastern Command", "Indian command has broken a Japanese objective or completed the flexible Southeast Asian land-and-sea theatre. London and Washington can no longer describe India as a supporting contingent; the result earns coalition credit and immediate replacement stocks.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory flag = ind_aubm_japan_limited_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_major_annex_victory_jap flag = ind_aubm_pacific_capital_victory flag = ind_aubm_regional_victory_sia flag = ind_aubm_regional_victory_u05 flag = ind_aubm_regional_victory_hol flag = ind_aubm_regional_victory_ast }", ("supplies value = 700", "dissent value = -2", "setflag which = ind_aubm_coalition_credit")),
            Focus("continental", "Continental Expeditionary Command", "The Indian Expedition Has Earned a European Voice", "Indian-command formations have produced a German, Italian, French or Turkish result. Delhi receives a formal consultation claim for the European settlement.", "OR = { flag = ind_aubm_germany_limited_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_major_annex_victory_ger flag = ind_aubm_european_capital_victory flag = ind_aubm_regional_victory_ita flag = ind_aubm_regional_victory_fra flag = ind_aubm_regional_victory_tur }", ("money value = 250", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation")),
            Focus("anticolonial", "Anti-Colonial Liberation Mandate", "India Turns Allied War into Decolonization", "A Southeast Asian operational victory or a western and African result lets Delhi tie military cooperation to sovereign postwar governments. This strengthens Indian settlement standing without granting territory automatically.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_western_victory flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_irq flag = ind_aubm_regional_victory_sau }", ("belligerence value = -3", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation")),
            Focus("free", "Sovereign Free Command", "The Allies Must Credit an Independent Indian Victory", "India has won a decisive campaign under its own command. Coalition recognition now improves armistice odds, but Delhi has accepted no automatic territorial settlement.", "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_america_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_major_annex_victory_ger flag = ind_aubm_major_annex_victory_jap flag = ind_aubm_major_annex_victory_usa }", ("money value = 300", "supplies value = 400", "setflag which = ind_aubm_victory_sovereign_credit")),
        ),
        "The Delhi Allied Peace Congress",
        "India has ended an Allied-route war with a measurable independent achievement. The settlement now defines whether Delhi builds a concert of sovereign partners, a treaty sphere with forward responsibilities, or a self-contained arsenal that cooperates without permanent alignment.",
        "ind_v3_allied_settlement_1945",
        ("ENG", "USA", "AST", "CAN"),
    ),
    Route(
        "german",
        "ind_aubm_route_german",
        "The Delhi-Berlin Division of War",
        "Cooperation with Germany does not decide India's enemy. The Eurasian Link makes the Soviet southern system the objective. Imperial Dismantlement targets Britain and the ocean routes. The Southern Race makes India, not Japan, master of the resource arc. Sovereign Parallel War accepts German coordination but reserves every Indian settlement claim.",
        "aubm_v4_barbarossa_reaction",
        (
            Focus("eurasian", "The Eurasian Link against Moscow", "Indian and German Fronts Meet across Eurasia", "India has broken a Soviet or Northern objective. Berlin must recognize Delhi's continental claim as an independent front, not a colonial auxiliary.", "OR = { flag = ind_aubm_soviet_limited_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_major_annex_victory_sov flag = ind_aubm_national_northern_victory }", ("supplies value = 700", "dissent value = -2", "setflag which = ind_aubm_coalition_credit")),
            Focus("imperial", "Dismantle Britain's imperial system", "India Breaks the Imperial System from the East", "A British, flexible Southeast Asian, southern or western victory gives Delhi the decisive claim in the Indian Ocean while Germany remains a continental partner.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_britain_limited_victory flag = ind_aubm_britain_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory }", ("money value = 300", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation")),
            Focus("southern", "Win the southern resource race", "Delhi Wins the Southern Race", "Indian command has secured the flexible Southeast Asian theatre or the wider southern resource arc before another coalition power could define it. The result becomes sovereign settlement credit.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory flag = ind_aubm_regional_victory_sia flag = ind_aubm_regional_victory_u05 flag = ind_aubm_regional_victory_hol flag = ind_aubm_regional_victory_ast }", ("supplies value = 800", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit")),
            Focus("parallel", "Sovereign parallel war", "India Proves It Is Berlin's Partner, Not Client", "A decisive Indian result establishes a separate peace claim. German recognition can improve the terms, but Delhi retains authority over the campaign ledger.", "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_america_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_major_annex_victory_sov flag = ind_aubm_major_annex_victory_usa }", ("money value = 250", "supplies value = 500", "setflag which = ind_aubm_victory_sovereign_credit")),
        ),
        "The Delhi-Berlin Settlement Congress",
        "India has completed a measurable campaign on the German route. Delhi can preserve a continental balance, construct an Indian security sphere from the Gulf to Southeast Asia, or end the partnership and retain only technical and commercial cooperation.",
        "ind_v3_axis_settlement_1945",
        ("GER", "ITA", "TUR", "JAP"),
    ),
    Route(
        "soviet",
        "ind_aubm_route_soviet",
        "The Delhi Socialist War Charter",
        "The Soviet relationship can produce very different wars. Anti-Fascist Expedition sends Indian command west. Anti-Imperial War targets colonial systems. Republican Asia ties victory to sovereign Asian governments. Autonomous Socialism cooperates where useful but measures success only by an independent Indian campaign.",
        "aubm_v4_barbarossa_reaction",
        (
            Focus("antifascist", "Anti-Fascist Expedition", "India Becomes an Independent Anti-Fascist Belligerent", "A German, Italian or European result gives India its own seat in the anti-fascist settlement rather than a subordinate role in Moscow's war.", "OR = { flag = ind_aubm_germany_limited_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_major_annex_victory_ger flag = ind_aubm_european_capital_victory flag = ind_aubm_regional_victory_ita flag = ind_aubm_regional_victory_fra }", ("supplies value = 700", "dissent value = -2", "setflag which = ind_aubm_coalition_credit")),
            Focus("antiimperial", "Anti-Imperial Ocean War", "India Converts Socialist War into Oceanic Liberation", "A flexible Southeast Asian, British, southern or western result gives Delhi anti-colonial leverage distinct from Soviet territorial interests.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_britain_limited_victory flag = ind_aubm_britain_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory }", ("belligerence value = -3", "dissent value = -2", "setflag which = ind_aubm_coalition_consultation")),
            Focus("republican", "A Republican Asian Order", "Delhi Establishes an Asian Republican Claim", "A flexible Southeast Asian result or an Indian victory in China, Siam or against Japan establishes a specifically Asian socialist-republican programme outside Moscow's direct command.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_japan_limited_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_major_annex_victory_jap flag = ind_aubm_pacific_capital_victory flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia }", ("money value = 250", "dissent value = -1", "setflag which = ind_aubm_coalition_consultation")),
            Focus("autonomous", "Autonomous Indian Socialism", "Indian Socialism Wins on Its Own Ledger", "A decisive Indian campaign establishes that ideological cooperation never transferred command authority to Moscow.", "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_america_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_major_annex_victory_ger flag = ind_aubm_major_annex_victory_jap flag = ind_aubm_major_annex_victory_usa }", ("research_mod value = 1", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit")),
        ),
        "The Delhi Socialist Peace Congress",
        "India has completed a measurable Soviet-route campaign. The postwar order may be a league of sovereign republics, a protected security belt, or autonomous Indian socialism with no permanent military bloc. Each outcome closes the missing Soviet postwar line used by the long campaign audit.",
        "ind_v3_soviet_postwar_line",
        ("SOV", "MON", "CHI", "CHC"),
    ),
    Route(
        "japan",
        "ind_aubm_route_japan",
        "The Delhi-Tokyo Wartime Charter",
        "Partnership with Japan requires an explicit division of labour. Southern Sphere assigns Malaya, the East Indies and Australia to Indian influence. Dual Continental War permits an Indian Soviet campaign beside a Japanese non-aggression policy. Indian Ocean First pushes through the Gulf and Suez. Equal Asian Command measures status through any two-theatre or decisive Indian result.",
        "aubm_v4_japan_southern_choice",
        (
            Focus("southern", "Indian Southern Sphere", "Tokyo Recognizes the Indian Southern Sphere", "India has won either the flexible Southeast Asian land-and-sea theatre or the wider published southern command. The result confirms Indian primacy from Burma through Malaya and the East Indies; country-specific settlements still decide sovereignty.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_jp_southern_victory flag = ind_aubm_national_southern_victory }", ("supplies value = 800", "dissent value = -2", "setflag which = ind_aubm_jp_india_full_sphere")),
            Focus("dualfront", "Independent Soviet campaign", "India Sustains a Second Continental War", "India has produced a Northern or Soviet result without surrendering the southern division of labour. Tokyo records the Soviet war as an Indian theatre rather than an automatic Japanese obligation.", "AND = { flag = ind_aubm_jp_independent_soviet_war NOT = { alliance = { country = IND country = JAP } } OR = { flag = ind_aubm_soviet_limited_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_major_annex_victory_sov flag = ind_aubm_national_northern_victory } }", ("money value = 250", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit")),
            Focus("ocean", "Indian Ocean First", "India Opens the Western Ocean Road", "A western victory links the Gulf, Suez or East Africa to the Indian maritime system. Japan retains its Pacific focus while Delhi owns the western political consequences.", "OR = { flag = ind_aubm_national_western_victory flag = ind_aubm_britain_limited_victory flag = ind_aubm_britain_major_victory flag = ind_aubm_major_annex_victory_eng }", ("supplies value = 600", "money value = 200", "setflag which = ind_aubm_coalition_consultation")),
            Focus("equal", "Equal Asian Command", "Delhi Becomes Tokyo's Equal Asian Centre", "A decisive Indian result proves that the partnership has two strategic centres. The achievement strengthens every later armistice without predetermining occupation policy.", "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_japan_major_victory flag = ind_aubm_britain_major_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_major_annex_victory_sov }", ("money value = 300", "supplies value = 500", "setflag which = ind_aubm_coalition_credit")),
        ),
        "The Delhi-Tokyo Asian Settlement Congress",
        "India has completed a measurable campaign beside Japan. Delhi must choose an equal Asian concert, an Indian-led ocean sphere with Japanese Pacific primacy, or strategic separation after victory. Settlements already concluded remain intact; this decision defines the relationship that follows them.",
        "ind_v3_japan_settlement_1945",
        ("JAP", "SIA", "CHI", "AST"),
    ),
    Route(
        "sovereign",
        "ind_aubm_route_sovereign",
        "The Sovereign Indian War Charter",
        "India answers to no coalition plan. Indian Ocean League makes southern and western settlements the goal. Continental Security Arc makes the Himalaya and Central Asia decisive. World Balancer seeks a great-power armistice. Republican Federation measures victory through sovereign governments rather than direct annexation.",
        "aubm_v4_grand_strategy",
        (
            Focus("ocean", "Build an Indian Ocean League", "The Indian Ocean League Has a Military Foundation", "A flexible Southeast Asian, southern or western victory gives Delhi the ports, access treaties and bargaining power needed for a sovereign ocean order.", "OR = { flag = ind_aubm_sea_theatre_achieved flag = ind_aubm_national_southern_victory flag = ind_aubm_national_western_victory flag = ind_aubm_britain_limited_victory flag = ind_aubm_major_annex_victory_eng }", ("tc_mod value = 2", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit")),
            Focus("continental", "Secure the Continental Arc", "India Secures a Continental Strategic Arc", "A northern or Soviet result gives Delhi leverage from the Himalaya toward Central Asia. Local constitutional settlements, not this announcement, decide each government's status.", "OR = { flag = ind_aubm_national_northern_victory flag = ind_aubm_soviet_limited_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_major_annex_victory_sov flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_tib flag = ind_aubm_regional_victory_sik }", ("supplies value = 700", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit")),
            Focus("balancer", "Act as the World Balancer", "A Great Power Negotiates Directly with Delhi", "A decisive Indian result proves that sovereign command can compel a great power to negotiate without inherited coalition wars.", "OR = { flag = ind_aubm_decisive_great_power flag = ind_aubm_britain_major_victory flag = ind_aubm_germany_major_victory flag = ind_aubm_soviet_major_victory flag = ind_aubm_japan_major_victory flag = ind_aubm_america_major_victory flag = ind_aubm_major_annex_victory_eng flag = ind_aubm_major_annex_victory_ger flag = ind_aubm_major_annex_victory_sov flag = ind_aubm_major_annex_victory_jap flag = ind_aubm_major_annex_victory_usa }", ("money value = 350", "dissent value = -2", "setflag which = ind_aubm_victory_sovereign_credit")),
            Focus("republican", "Build a Republican Federation", "Indian Arms Create Space for Sovereign Governments", "A regional capital has fallen and entered a constitutional settlement. Delhi's announced measure of success is a network of sovereign partners rather than an unexamined annexation map.", "OR = { flag = ind_aubm_regional_victory_chi flag = ind_aubm_regional_victory_chc flag = ind_aubm_regional_victory_sia flag = ind_aubm_regional_victory_per flag = ind_aubm_regional_victory_afg flag = ind_aubm_regional_victory_eth flag = ind_aubm_regional_victory_saf }", ("belligerence value = -4", "dissent value = -1", "setflag which = ind_aubm_victory_sovereign_credit")),
        ),
        "The Congress of India's Independent Peace",
        "India has completed a measurable war without accepting another capital's command. The postwar choice is an open league, a defended sphere, or a self-contained great-power republic. None changes a country's sovereignty without its separate settlement event.",
        "ind_v3_nam_settlement_1945",
        ("AFG", "PER", "SIA", "ETH"),
    ),
)


def header(event_id: int, *, persistent: bool = True) -> list[str]:
    lines = ["event = {", f"\tid = {event_id}", "\trandom = no"]
    if persistent:
        lines.append("\tpersistent = yes")
    lines.append("\tcountry = IND")
    return lines


def strategic_autonomy_commands(route: Route) -> tuple[str, ...]:
    """Return India to a real sovereign command after the peace congress."""
    commands = [
        "leave_alliance when = 1",
        "clrflag which = ind_aubm_commitment_allied",
        "clrflag which = ind_aubm_commitment_german",
        "clrflag which = ind_aubm_commitment_soviet",
        "clrflag which = ind_aubm_commitment_japan",
        "clrflag which = ind_aubm_negotiation_allied",
        "clrflag which = ind_aubm_negotiation_german",
        "clrflag which = ind_aubm_negotiation_soviet",
        "clrflag which = ind_aubm_negotiation_japan",
        "clrflag which = ind_aubm_diplomatic_negotiation_pending",
        "clrflag which = ind_v4a_treaty_commonwealth",
        "clrflag which = ind_v4a_treaty_naval_compact",
        "clrflag which = ind_v4a_treaty_formal_alliance",
        "clrflag which = ind_v4a_treaty_cobelligerent",
        "clrflag which = ind_aubm_allied_partner_eng",
        "clrflag which = ind_aubm_allied_partner_usa",
        "clrflag which = ind_v4a_allied_framework_started",
        "clrflag which = ind_v4a_allied_framework_settled",
        "clrflag which = ind_v4a_proposal_commonwealth",
        "clrflag which = ind_v4a_proposal_naval_compact",
        "clrflag which = ind_v4a_proposal_formal_alliance",
        "clrflag which = ind_v4a_proposal_cobelligerent",
        "clrflag which = ind_v4a_war_entry_cooldown",
        "clrflag which = ind_gc_formal_axis",
        "clrflag which = ind_gc_cobelligerent",
        "clrflag which = ind_gc_sovereign",
        "clrflag which = ind_gc_berlin_negotiating",
        "clrflag which = ind_gc_berlin_cooldown",
        "clrflag which = ind_gc_berlin_aloof",
        "clrflag which = ind_v4_sov_equal_compact",
        "clrflag which = ind_v4_sov_supervised_compact",
        "clrflag which = ind_v4_sov_program_defined",
        "clrflag which = ind_v4_sov_equal_compact_proposed",
        "clrflag which = ind_v4_sov_technical_only",
        "clrflag which = ind_v4_sov_moscow_consultation",
        "clrflag which = ind_v4_sov_moscow_retry_pending",
        "clrflag which = ind_v4_sov_moscow_terms_rejected",
        "clrflag which = ind_aubm_jp_partnership",
        "clrflag which = ind_aubm_jp_formal_alliance",
        "clrflag which = ind_aubm_jp_independent_cobelligerent",
        "clrflag which = ind_aubm_jp_proposal_pending",
        "clrflag which = ind_aubm_jp_retry_cooldown",
        "clrflag which = ind_aubm_jp_retry_ready",
        "clrflag which = ind_aubm_jp_retry_recovery_dispatched",
        "clrflag which = ind_aubm_jp_tier_senior",
        "clrflag which = ind_aubm_jp_tier_peer",
        "clrflag which = ind_aubm_jp_tier_junior",
        "clrflag which = ind_aubm_jp_tier_counter",
        "clrflag which = ind_aubm_jp_india_full_sphere",
        "clrflag which = ind_aubm_jp_india_core_sphere",
        "setflag which = ind_aubm_jp_rupture",
        "clrflag which = ind_aubm_route_allied",
        "clrflag which = ind_aubm_route_german",
        "clrflag which = ind_aubm_route_soviet",
        "clrflag which = ind_aubm_route_japan",
        "setflag which = ind_aubm_route_sovereign",
        "clrflag which = ind_v3_allied_orientation",
        "clrflag which = ind_v3_axis_orientation",
        "clrflag which = ind_v3_soviet_orientation",
        "clrflag which = ind_v3_japanese_orientation",
        "clrflag which = ind_v3_joined_allies",
        "clrflag which = ind_v3_joined_axis",
        "clrflag which = ind_v3_joined_comintern",
        "clrflag which = ind_v3_joined_japan",
        "clrflag which = ind_v4_strategy_allied",
        "clrflag which = ind_v4_strategy_axis",
        "clrflag which = ind_v4_strategy_soviet",
        "clrflag which = ind_v4_strategy_japan",
        "setflag which = ind_aubm_realignment_cooldown",
        "event which = 9281938 where = IND when = 90",
    ]
    if route.key == "soviet":
        commands.extend(
            [
                "setflag which = ind_v4_sov_autonomous_socialism",
                "setflag which = ind_aubm_socialist_autonomous",
                "setflag which = ind_v3_soviet_orientation",
                "setflag which = ind_v4_strategy_soviet",
            ]
        )
    else:
        commands.extend(
            [
                "clrflag which = ind_v4_sov_autonomous_socialism",
                "clrflag which = ind_aubm_socialist_autonomous",
                "setflag which = ind_v3_non_aligned",
                "setflag which = ind_v4_strategy_nam",
            ]
        )
    return tuple(commands)


def current_route_trigger(route: Route) -> str:
    """Map autonomous socialism to its own Soviet-route doctrine lifecycle."""
    if route.key == "soviet":
        return (
            "OR = { flag = ind_aubm_route_soviet "
            "AND = { flag = ind_aubm_route_sovereign flag = ind_aubm_socialist_autonomous } }"
        )
    if route.key == "sovereign":
        return "AND = { flag = ind_aubm_route_sovereign NOT = { flag = ind_aubm_socialist_autonomous } }"
    return f"flag = {route.route_flag}"


def initializer() -> str:
    out = header(9283200)
    out.extend([
        "\ttrigger = { flag = ind_aubm_wartime_framework NOT = { flag = ind_aubm_legacy_wartime_retired } }",
        '\tname = "The Canonical War Office Replaces the Old Dossiers"',
        '\tdesc = "The new War Cabinet retires overlapping generic and route-specific reward stacks. Prewar treaty conferences remain available, but only the canonical campaign, reversal, armistice and constitutional-settlement system now scores battlefield results."',
        "\tstyle = 2",
        '\tpicture = "aubm_v4_grand_strategy"',
        "\tdate = { day = 0 month = january year = 1933 }",
        "\toffset = 1",
        "\tdeathdate = { day = 29 month = december year = 1964 }",
        "\taction_a = {",
        '\t\tname = "Retire duplicate wartime chains"',
    ])
    for event_id in LEGACY_WARTIME_IDS:
        out.append(f"\t\tcommand = {{ type = sleepevent which = {event_id} }}")
    out.extend([
        "\t\tcommand = { trigger = { flag = ind_aubm_occupation_upkeep NOT = { OR = { flag = ind_aubm_occupation_tier_1 flag = ind_aubm_occupation_tier_2 flag = ind_aubm_occupation_tier_3 flag = ind_aubm_occupation_tier_4 } } } type = setflag which = ind_aubm_occupation_tier_1 }",
        "\t\tcommand = { type = setflag which = ind_aubm_legacy_wartime_retired }",
        "\t}",
        "}",
    ])
    return "\n".join(out)


def route_events() -> str:
    out: list[str] = []
    for route_index, route in enumerate(ROUTES):
        charter_id = 9283210 + route_index
        out.extend(header(charter_id))
        out.extend([
            f"\ttrigger = {{ flag = ind_aubm_wartime_framework {current_route_trigger(route)} atwar = yes NOT = {{ flag = ind_aubm_route_charter_{route.key} }} }}",
            f'\tname = "{route.charter_name}"',
            f'\tdesc = "{route.charter_desc}"',
            "\tstyle = 2",
            f'\tpicture = "{route.picture}"',
            "\tdate = { day = 0 month = january year = 1933 }",
            "\toffset = 3",
            "\tdeathdate = { day = 29 month = december year = 1964 }",
        ])
        for letter, focus in zip("abcd", route.focuses):
            out.extend([
                f"\taction_{letter} = {{",
                f'\t\tname = "{focus.label}"',
                f"\t\tcommand = {{ type = setflag which = ind_aubm_route_focus_{route.key}_{focus.key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_route_charter_{route.key} }}",
                "\t}",
            ])
        out.extend(["}", ""])

        base = 9283220 + route_index * 10
        for focus_index, focus in enumerate(route.focuses):
            event_id = base + focus_index
            out.extend(header(event_id))
            out.extend([
                "\ttrigger = {",
                "\t\tflag = ind_aubm_wartime_framework",
                f"\t\t{current_route_trigger(route)}",
                f"\t\tflag = ind_aubm_route_focus_{route.key}_{focus.key}",
                f"\t\tNOT = {{ flag = ind_aubm_route_achievement_{route.key}_{focus.key} }}",
                "\t\tNOT = { flag = ind_aubm_route_war_achievement }",
                "\t\tNOT = { flag = ind_aubm_postwar_congress_completed }",
                f"\t\t{focus.trigger}",
                "\t}",
                f'\tname = "{focus.achievement_name}"',
                f'\tdesc = "{focus.achievement_desc}"',
                "\tstyle = 2",
                f'\tpicture = "{route.picture}"',
                "\tdate = { day = 0 month = january year = 1933 }",
                "\toffset = 2",
                "\tdeathdate = { day = 29 month = december year = 1964 }",
                "\taction_a = {",
                '\t\tname = "Enter the achievement in India\'s war ledger"',
            ])
            for reward in focus.reward:
                out.append(f"\t\tcommand = {{ type = {reward} }}")
            out.extend([
                f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key}_{focus.key} }}",
                f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key} }}",
                "\t\tcommand = { type = setflag which = ind_aubm_route_war_achievement }",
                "\t}",
                "}",
                "",
            ])

        fallback_id = base + 4
        out.extend(header(fallback_id))
        out.extend([
            "\ttrigger = {",
            "\t\tflag = ind_aubm_wartime_framework",
            f"\t\t{current_route_trigger(route)}",
            f"\t\tflag = ind_aubm_route_charter_{route.key}",
            "\t\tflag = ind_aubm_global_campaign_victory",
            f"\t\tNOT = {{ flag = ind_aubm_route_achievement_{route.key}_global }}",
            "\t\tNOT = { flag = ind_aubm_route_war_achievement }",
            "\t\tNOT = { flag = ind_aubm_postwar_congress_completed }",
            "\t}",
            '\tname = "India Wins Beyond the Charter\'s Named Front"',
            f'\tdesc = "India has won a published campaign outside the four fronts named by {route.charter_name}. The War Cabinet records the result as a valid national achievement, so a distant or emergent-state war can still lead to India\'s peace congress."',
            "\tstyle = 2",
            f'\tpicture = "{route.picture}"',
            "\tdate = { day = 0 month = january year = 1933 }",
            "\toffset = 2",
            "\tdeathdate = { day = 29 month = december year = 1964 }",
            "\taction_a = {",
            '\t\tname = "Enter the wider victory in India\'s war ledger"',
            "\t\tcommand = { type = money value = 100 }",
            "\t\tcommand = { type = supplies value = 300 }",
            "\t\tcommand = { type = dissent value = -1 }",
            "\t\tcommand = { type = setflag which = ind_aubm_victory_sovereign_credit }",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key}_global }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_route_achievement_{route.key} }}",
            "\t\tcommand = { type = setflag which = ind_aubm_route_war_achievement }",
            "\t}",
            "}",
            "",
        ])

        congress_id = 9283270 + route_index
        out.extend(header(congress_id))
        out.extend([
            f"\ttrigger = {{ flag = ind_aubm_wartime_framework {current_route_trigger(route)} flag = ind_aubm_route_war_achievement atwar = no NOT = {{ flag = ind_aubm_postwar_congress_completed }} NOT = {{ flag = ind_aubm_postwar_congress_{route.key} }} }}",
            f'\tname = "{route.congress_name}"',
            f'\tdesc = "{route.congress_desc}"',
            "\tstyle = 2",
            f'\tpicture = "{route.picture}"',
            "\tdate = { day = 0 month = january year = 1933 }",
            "\toffset = 10",
            "\tdeathdate = { day = 29 month = december year = 1964 }",
            "\taction_a = {",
            '\t\tname = "A concert of sovereign partners: -4 dissent, +1 research"',
            "\t\tcommand = { type = dissent value = -4 }",
            "\t\tcommand = { type = belligerence value = -3 }",
            "\t\tcommand = { type = research_mod value = 1 }",
            f"\t\tcommand = {{ type = setflag which = {route.legacy_flag} }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_postwar_congress_{route.key} }}",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_congress_completed }",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_concert }",
        ])
        for tag in route.relations:
            out.append(f"\t\tcommand = {{ trigger = {{ exists = {tag} }} type = relation which = {tag} value = 25 }}")
        out.extend([
            "\t}",
            "\taction_b = {",
            '\t\tname = "An Indian security sphere: +2 dissent, +3 TC"',
            "\t\tcommand = { type = dissent value = 2 }",
            "\t\tcommand = { type = tc_mod value = 3 }",
            "\t\tcommand = { type = supplies value = 1000 }",
            f"\t\tcommand = {{ type = setflag which = {route.legacy_flag} }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_postwar_congress_{route.key} }}",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_congress_completed }",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_security_sphere }",
            "\t}",
            "\taction_c = {",
            '\t\tname = "Strategic autonomy: +600 money, +3 supply output"',
            "\t\tcommand = { type = money value = 600 }",
            "\t\tcommand = { type = industrial_modifier which = supplies value = 3 }",
            "\t\tcommand = { type = dissent value = -1 }",
        ])
        for command in strategic_autonomy_commands(route):
            out.append(f"\t\tcommand = {{ type = {command} }}")
        out.extend([
            f"\t\tcommand = {{ type = setflag which = {route.legacy_flag} }}",
            f"\t\tcommand = {{ type = setflag which = ind_aubm_postwar_congress_{route.key} }}",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_congress_completed }",
            "\t\tcommand = { type = setflag which = ind_aubm_postwar_strategic_autonomy }",
            "\t}",
            "}",
            "",
        ])
    return "\n".join(out).rstrip()


def render() -> str:
    return (
        "#########################################################################\n"
        "# A Union Before Midnight V4: route-specific wartime consequences\n"
        "# Generated by tools/generate_aubm_route_consequences.py; do not edit.\n"
        "#########################################################################\n\n"
        + initializer()
        + "\n\n"
        + route_events()
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
        print("OK: five route-specific wartime lifecycles are current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generated, encoding="ascii", newline="\n")
    print(f"WROTE: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
