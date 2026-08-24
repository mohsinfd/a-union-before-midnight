#!/usr/bin/env python3
"""Build the V4 event-art manifest and review gallery from source mappings."""

from __future__ import annotations

import csv
import hashlib
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "mod/db/events/aubm_v4"
PICTURE_DIR = ROOT / "mod/gfx/events_pics"
MANIFEST = ROOT / "docs/v4_event_art_manifest.csv"
GALLERY = ROOT / "dist/v4-event-art-gallery.png"
ART_MANIFEST = ROOT / "docs/art_manifest.csv"
FULL_GALLERY = ROOT / "dist/event-art-gallery.png"

SOURCE_KIND = "generated alternate-history reconstruction"
CREATOR = "OpenAI image generation"
CREDIT = (
    "Original AI-assisted reconstruction created for A Union Before Midnight; "
    "not an archival photograph"
)

SHEETS: tuple[tuple[str, tuple[tuple[int, str], ...]], ...] = (
    (
        "tools/art_sources/v4_events/sheet_01_foundation.png",
        (
            (9280000, "aubm_v4_continental_state"),
            (9280100, "aubm_v4_union_register"),
            (9280101, "aubm_v4_ceylon_council"),
            (9280102, "aubm_v4_customs_union"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_02_integration.png",
        (
            (9280103, "aubm_v4_railway_board"),
            (9280104, "aubm_v4_malayan_bargain"),
            (9280105, "aubm_v4_bengal_jute"),
            (9280106, "aubm_v4_indus_frontier_council"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_03_reviews.png",
        (
            (9280107, "aubm_v4_first_union_budget"),
            (9280108, "aubm_v4_union_by_consent"),
            (9280109, "aubm_v4_administrative_state"),
            (9280110, "aubm_v4_unfinished_bargain"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_04_institutions.png",
        (
            (9280111, "aubm_v4_provincial_oath"),
            (9280112, "aubm_v4_telegraph_statistics"),
            (9280113, "aubm_v4_provincial_granaries"),
            (9280114, "aubm_v4_rangoon_conference"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_05_federal_development.png",
        (
            (9280115, "aubm_v4_fiscal_federalism"),
            (9280116, "aubm_v4_union_takes_root"),
            (9280117, "aubm_v4_capacity_without_settlement"),
            (9280118, "aubm_v4_federal_works_compact"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_06_storm_and_diplomacy.png",
        (
            (9280119, "aubm_v4_development_loan_due"),
            (9280120, "aubm_v4_union_before_storm"),
            (9280300, "aubm_v4_league_of_nations"),
            (9280301, "aubm_v4_london_settlement"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_07_expertise_and_command.png",
        (
            (9280302, "aubm_v4_foreign_expertise"),
            (9280303, "aubm_v4_tokyo_proposition"),
            (9280150, "aubm_v4_field_service_regulations"),
            (9280151, "aubm_v4_army_commands"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_08_air_security_and_exercises.png",
        (
            (9280152, "aubm_v4_airfield_security"),
            (9280153, "aubm_v4_observer_corps"),
            (9280154, "aubm_v4_corps_exercise_1935"),
            (9280155, "aubm_v4_joint_exercise_1937"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_09_operational_survival.png",
        (
            (9280156, "aubm_v4_operational_review_1939"),
            (9280157, "aubm_v4_damage_control_school"),
            (9280158, "aubm_v4_forward_basing"),
            (9280159, "aubm_v4_command_rotation"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_10_command_and_organization.png",
        (
            (9280160, "aubm_v4_second_command_board"),
            (9280161, "aubm_v4_combat_command_board"),
            (9280200, "aubm_v4_standard_toe"),
            (9280201, "aubm_v4_four_wing_standard"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_11_fleet_and_war_aims.png",
        (
            (9280202, "aubm_v4_fleet_tactical_units"),
            (9280203, "aubm_v4_joint_replacement_pool"),
            (9280400, "aubm_v4_war_aims"),
            (9280401, "aubm_v4_liberated_territory"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_12_return_and_v3_priority.png",
        ((9280402, "aubm_v4_soldiers_return"),),
    ),
    (
        "tools/art_sources/v4_events/sheet_13_campaign_finance.png",
        (
            (9280310, "aubm_v4_budget_conference"),
            (9280311, "aubm_v4_union_budget_choices"),
            (9280313, "aubm_v4_retire_development_debt"),
            (9280312, "aubm_v4_next_budget_year"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_14_growth_and_islands.png",
        (
            (9280314, "aubm_v4_economy_full_stretch"),
            (9280315, "aubm_v4_inherited_archives"),
            (9280320, "aubm_v4_island_base_stage_one"),
            (9280321, "aubm_v4_island_base_stage_two"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_15_china_and_burma.png",
        (
            (9280350, "aubm_v4_china_war_deepens"),
            (9280351, "aubm_v4_burma_road_refugees"),
            (9280352, "aubm_v4_bangkok_chooses_war"),
            (9280353, "aubm_v4_china_interior"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_16_widening_war.png",
        (
            (9280354, "aubm_v4_indian_ocean_war"),
            (9280355, "aubm_v4_barbarossa_reaction"),
            (9280356, "aubm_v4_japan_southern_choice"),
            (9280357, "aubm_v4_malaya_burma_conference"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_17_wartime_strategy.png",
        (
            (9280358, "aubm_v4_india_world_war"),
            (9280359, "aubm_v4_wartime_social_contract"),
            (9280500, "aubm_v4_strategic_council"),
            (9280501, "aubm_v4_grand_strategy"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_18_asian_strategy.png",
        (
            (9280502, "aubm_v4_asian_strategy_menu"),
            (9280503, "aubm_v4_strategic_council_returns"),
        ),
    ),
)

LEGACY_SHEETS: tuple[tuple[str, tuple[tuple[int, str], ...]], ...] = (
    (
        "tools/art_sources/v4_events/sheet_12_return_and_v3_priority.png",
        (
            (2, "all_india_congress"),
            (3, "Gurkha"),
            (4, "india_v3_japan_bose"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_13_legacy_politics.png",
        (
            (1, "all_india_party"),
            (2, "british_parliament"),
            (3, "japan_cabinet"),
            (4, "india_v3_german_mission"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_14_legacy_elite_forces.png",
        (
            (1, "india_v3_elite_airborne"),
            (2, "india_v3_elite_frontier"),
            (3, "india_v3_elite_marines"),
            (4, "india_v3_elite_penetration"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_15_legacy_japan_compacts.png",
        (
            (1, "india_v3_japan_yokosuka"),
            (2, "india_v3_japan_china"),
            (3, "india_v3_japan_ina"),
            (4, "india_v3_japan_imphal"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_16_legacy_japan_war.png",
        (
            (1, "india_v3_japan_war_aims"),
            (2, "india_v3_japan_imphal_campaign"),
            (3, "india_v3_japan_imphal_victory"),
            (4, "india_v3_japan_settlement"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_17_legacy_reckoning.png",
        (
            (1, "india_v3_revisionist_reckoning"),
            (2, "india_v3_revisionist_settlement"),
            (3, "india_v3_world_abyssinia"),
            (4, "india_v3_world_spain"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_18_legacy_world_crises.png",
        (
            (1, "india_v3_world_china"),
            (2, "india_v3_world_anschluss"),
            (3, "india_v3_world_munich"),
            (4, "india_v3_world_prague"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_19_legacy_war_and_soviet.png",
        (
            (1, "india_v3_world_poland"),
            (2, "Russian_Airborne"),
            (3, "Stalin_5YPlan"),
            (4, "india_v3_independence"),
        ),
    ),
    (
        "tools/art_sources/v4_events/sheet_20_core_event_art.png",
        (
            (1, "india_v3_industry"),
            (2, "india_v3_armed_forces"),
            (3, "india_v3_german_panzer"),
            (4, "india_v3_german_war_aims"),
        ),
    ),
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_catalog() -> dict[int, tuple[str, str]]:
    catalog: dict[int, tuple[str, str]] = {}
    event_pattern = re.compile(r"(?m)^event\s*=\s*\{")
    id_pattern = re.compile(r"(?m)^\s*id\s*=\s*(928\d+)\s*$")
    name_pattern = re.compile(r'(?m)^\s*name\s*=\s*"([^"]+)"\s*$')
    picture_pattern = re.compile(r'(?m)^\s*picture\s*=\s*"([^"]+)"\s*$')
    for path in sorted(EVENT_DIR.glob("*.txt")):
        text = path.read_text(encoding="cp1252")
        starts = [match.start() for match in event_pattern.finditer(text)] + [len(text)]
        for start, end in zip(starts, starts[1:], strict=False):
            block = text[start:end]
            event_id = id_pattern.search(block)
            title = name_pattern.search(block)
            picture = picture_pattern.search(block)
            if event_id and title and picture:
                numeric_id = int(event_id.group(1))
                if numeric_id in catalog:
                    raise ValueError(f"duplicate V4 event id {numeric_id}")
                catalog[numeric_id] = (title.group(1), picture.group(1))
    return catalog


def referenced_custom_event_assets() -> set[str]:
    pattern = re.compile(r'(?m)^\s*picture\s*=\s*"([^"]+)"')
    assets: set[str] = set()
    for directory in (ROOT / "mod/db/events/india_v3", EVENT_DIR):
        for path in sorted(directory.glob("*.txt")):
            text = path.read_text(encoding="cp1252")
            for name in pattern.findall(text):
                if (PICTURE_DIR / f"{name}.bmp").is_file():
                    assets.add(name)
    return assets


def records() -> list[dict[str, str | int]]:
    catalog = event_catalog()
    expected_ids = {event_id for _, entries in SHEETS for event_id, _ in entries}
    if set(catalog) != expected_ids:
        missing = sorted(set(catalog) - expected_ids)
        stale = sorted(expected_ids - set(catalog))
        raise ValueError(f"V4 mapping mismatch; unmapped={missing}, stale={stale}")

    output: list[dict[str, str | int]] = []
    seen_assets: set[str] = set()
    for sheet, entries in SHEETS:
        source = ROOT / sheet
        if not source.is_file():
            raise FileNotFoundError(source)
        for panel, (event_id, asset) in enumerate(entries, 1):
            title, referenced = catalog[event_id]
            if referenced != asset:
                raise ValueError(
                    f"event {event_id} references {referenced}, expected {asset}"
                )
            if asset in seen_assets:
                raise ValueError(f"duplicate V4 asset mapping {asset}")
            seen_assets.add(asset)
            picture = PICTURE_DIR / f"{asset}.bmp"
            if not picture.is_file():
                raise FileNotFoundError(picture)
            with Image.open(picture) as image:
                if image.size != (400, 116) or image.mode != "RGB":
                    raise ValueError(
                        f"{picture.name} is {image.size} {image.mode}, expected 400x116 RGB"
                    )
            output.append(
                {
                    "asset": asset,
                    "event_id": event_id,
                    "event_title": title,
                    "source_sheet": sheet,
                    "panel": panel,
                    "source_kind": SOURCE_KIND,
                    "creator": CREATOR,
                    "credit": CREDIT,
                    "sha256": sha256(picture),
                }
            )
    if len(output) != 67:
        raise ValueError(f"expected 67 V4 art records, built {len(output)}")
    return output


def legacy_records() -> list[dict[str, str | int]]:
    output: list[dict[str, str | int]] = []
    for sheet, entries in LEGACY_SHEETS:
        source = ROOT / sheet
        if not source.is_file():
            raise FileNotFoundError(source)
        for panel, asset in entries:
            picture = PICTURE_DIR / f"{asset}.bmp"
            if not picture.is_file():
                raise FileNotFoundError(picture)
            with Image.open(picture) as image:
                if image.size != (400, 116) or image.mode != "RGB":
                    raise ValueError(
                        f"{picture.name} is {image.size} {image.mode}, expected 400x116 RGB"
                    )
            output.append(
                {
                    "asset": asset,
                    "source_sheet": sheet,
                    "panel": panel,
                    "sha256": sha256(picture),
                }
            )
    return output


def technology_team_records() -> list[dict[str, str]]:
    if not ART_MANIFEST.is_file():
        raise FileNotFoundError(ART_MANIFEST)
    output: list[dict[str, str]] = []
    with ART_MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("kind") != "tech_team":
                continue
            relative_output = row["output"].replace("\\", "/")
            rendered = ROOT / "mod" / relative_output
            if not rendered.is_file():
                raise FileNotFoundError(rendered)
            output.append(
                {
                    "asset": row["asset"],
                    "kind": "tech_team",
                    "source": f"mod/{relative_output}",
                    "output": relative_output,
                    "sha256": sha256(rendered),
                    "provenance": (
                        "generated original; packaged 96x96 master retained as source"
                    ),
                }
            )
    if len(output) != 31:
        raise ValueError(f"expected 31 technology-team records, found {len(output)}")
    return output


def write_full_art_manifest(
    v4_rows: list[dict[str, str | int]],
    old_rows: list[dict[str, str | int]],
) -> list[dict[str, str]]:
    event_rows: list[dict[str, str]] = []
    for row in (
        [
            {
                "asset": item["asset"],
                "source_sheet": item["source_sheet"],
                "panel": item["panel"],
                "sha256": item["sha256"],
            }
            for item in v4_rows
        ]
        + old_rows
    ):
        asset = str(row["asset"])
        event_rows.append(
            {
                "asset": asset,
                "kind": "event",
                "source": f"{row['source_sheet']}#panel={row['panel']}",
                "output": f"gfx/events_pics/{asset}.bmp",
                "sha256": str(row["sha256"]),
                "provenance": (
                    "generated alternate-history reconstruction; "
                    "not an archival photograph"
                ),
            }
        )
    mapped = {row["asset"] for row in event_rows}
    referenced = referenced_custom_event_assets()
    if mapped != referenced:
        raise ValueError(
            "custom event-art coverage mismatch; "
            f"unmapped={sorted(referenced - mapped)}, stale={sorted(mapped - referenced)}"
        )
    all_rows = sorted(event_rows, key=lambda row: row["asset"].lower())
    all_rows.extend(sorted(technology_team_records(), key=lambda row: row["asset"]))
    with ART_MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    return event_rows


def write_manifest(rows: list[dict[str, str | int]]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_gallery(rows: list[dict[str, str | int]]) -> None:
    columns = 3
    image_width, image_height = 400, 116
    label_height = 38
    gutter = 12
    rows_high = (len(rows) + columns - 1) // columns
    width = columns * image_width + (columns + 1) * gutter
    height = rows_high * (image_height + label_height) + (rows_high + 1) * gutter
    gallery = Image.new("RGB", (width, height), (24, 25, 27))
    draw = ImageDraw.Draw(gallery)
    font = ImageFont.load_default()
    for index, row in enumerate(rows):
        grid_x = index % columns
        grid_y = index // columns
        x = gutter + grid_x * (image_width + gutter)
        y = gutter + grid_y * (image_height + label_height + gutter)
        with Image.open(PICTURE_DIR / f"{row['asset']}.bmp") as source:
            gallery.paste(source.convert("RGB"), (x, y))
        label = f"{row['event_id']}  {row['event_title']}"
        draw.text((x + 4, y + image_height + 5), label, fill=(235, 235, 232), font=font)
        draw.text(
            (x + 4, y + image_height + 20),
            str(row["asset"]),
            fill=(155, 184, 193),
            font=font,
        )
    GALLERY.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(GALLERY, optimize=True)


def write_full_gallery(rows: list[dict[str, str]]) -> None:
    columns = 4
    image_width, image_height = 400, 116
    label_height = 22
    gutter = 10
    ordered = sorted(rows, key=lambda row: row["asset"].lower())
    rows_high = (len(ordered) + columns - 1) // columns
    width = columns * image_width + (columns + 1) * gutter
    height = rows_high * (image_height + label_height) + (rows_high + 1) * gutter
    gallery = Image.new("RGB", (width, height), (24, 25, 27))
    draw = ImageDraw.Draw(gallery)
    font = ImageFont.load_default()
    for index, row in enumerate(ordered):
        grid_x = index % columns
        grid_y = index // columns
        x = gutter + grid_x * (image_width + gutter)
        y = gutter + grid_y * (image_height + label_height + gutter)
        with Image.open(PICTURE_DIR / f"{row['asset']}.bmp") as source:
            gallery.paste(source.convert("RGB"), (x, y))
        draw.text(
            (x + 4, y + image_height + 5),
            row["asset"],
            fill=(188, 210, 216),
            font=font,
        )
    FULL_GALLERY.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(FULL_GALLERY, optimize=True)


def main() -> int:
    try:
        rows = records()
        old_rows = legacy_records()
        write_manifest(rows)
        write_gallery(rows)
        full_event_rows = write_full_art_manifest(rows, old_rows)
        write_full_gallery(full_event_rows)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Wrote {len(rows)} records to {MANIFEST.relative_to(ROOT)}")
    print(f"Wrote review gallery to {GALLERY.relative_to(ROOT)}")
    print(
        f"Wrote {len(full_event_rows)} event and 31 technology-team records "
        f"to {ART_MANIFEST.relative_to(ROOT)}"
    )
    print(f"Wrote full event-art gallery to {FULL_GALLERY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
