#!/usr/bin/env python3
"""Build original India map sprites from the preserved V4 source sheets."""

from __future__ import annotations

import csv
import hashlib
import math
import pathlib
import sys
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "tools/art_sources/v4_sprites"
SPRITE_DIR = ROOT / "mod/gfx/map/units"
BITMAP_DIR = SPRITE_DIR / "bmp"
PALETTE_DIR = ROOT / "mod/gfx/palette"
MANIFEST = ROOT / "docs/v4_sprite_manifest.csv"
PREVIEW = ROOT / "dist/v4-service-sprite-preview.png"

CELL_SIZE = 96
TRANSPARENT = (255, 0, 255)
DIRECTIONS = ("E", "NE", "N", "NW", "W", "SW", "S", "SE")
DIRECTION_ANGLES = {
    "E": 0,
    "NE": 45,
    "N": 90,
    "NW": 135,
    "W": 180,
    "SW": 225,
    "S": 270,
    "SE": 315,
}


@dataclass(frozen=True)
class Family:
    name: str
    source_sheet: str
    panel: int
    grid: int
    rotatable: bool
    max_size: tuple[int, int]


FAMILIES = (
    Family("infantry", "india_service_sheet_01.png", 1, 3, False, (72, 74)),
    Family("gurkha", "india_service_sheet_01.png", 2, 3, False, (72, 74)),
    Family("motorized", "india_service_sheet_01.png", 3, 3, False, (82, 64)),
    Family("armor", "india_service_sheet_01.png", 4, 3, True, (76, 62)),
    Family("fighter", "india_service_sheet_01.png", 5, 3, True, (76, 66)),
    Family("bomber", "india_service_sheet_01.png", 6, 3, True, (80, 68)),
    Family("escort", "india_service_sheet_01.png", 7, 3, True, (84, 58)),
    Family("carrier", "india_service_sheet_01.png", 8, 3, True, (84, 60)),
    Family("submarine", "india_service_sheet_01.png", 9, 3, True, (84, 48)),
    Family("capital", "india_service_sheet_02.png", 1, 2, True, (86, 62)),
    Family("cruiser", "india_service_sheet_02.png", 2, 2, True, (86, 58)),
    Family("transport", "india_service_sheet_02.png", 3, 2, True, (86, 62)),
    Family("cavalry", "india_service_sheet_02.png", 4, 2, False, (78, 74)),
)

UNIT_FAMILIES = {
    "INFANTRY": "infantry",
    "MILITIA": "infantry",
    "GARRISON": "infantry",
    "MARINE": "infantry",
    "PARATROOPER": "infantry",
    "CAVALRY": "cavalry",
    "MOUNTAIN": "gurkha",
    "d_05": "gurkha",
    "MOTORIZED": "motorized",
    "MECHANIZED": "motorized",
    "HQ": "motorized",
    "PANZER": "armor",
    "FIGHTER": "fighter",
    "INTERCEPTOR": "fighter",
    "ESCORT": "fighter",
    "ROCKET_INTERCEPTOR": "fighter",
    "BOMBER": "bomber",
    "CAS": "bomber",
    "TACTICAL": "bomber",
    "NAVAL": "bomber",
    "STRATEGIC": "bomber",
    "TRANSPORTPLANE": "bomber",
    "DESTROYER": "escort",
    "LIGHT_CRUISER": "cruiser",
    "HEAVY_CRUISER": "capital",
    "BATTLECRUISER": "capital",
    "BATTLESHIP": "capital",
    "CARRIER": "carrier",
    "escort_carrier": "carrier",
    "SUBMARINE": "submarine",
    "nuclear_submarine": "submarine",
    "TRANSPORT": "transport",
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dark_line(image: Image.Image, index: int, vertical: bool) -> bool:
    if vertical:
        line = image.crop((index, 0, index + 1, image.height)).convert("L")
        length = image.height
    else:
        line = image.crop((0, index, image.width, index + 1)).convert("L")
        length = image.width
    histogram = line.histogram()
    return sum(histogram[:24]) / length >= 0.94


def content_bands(image: Image.Image, vertical: bool) -> list[tuple[int, int]]:
    length = image.width if vertical else image.height
    dark = [dark_line(image, index, vertical) for index in range(length)]
    bands: list[tuple[int, int]] = []
    start: int | None = None
    for index, is_dark in enumerate(dark + [True]):
        if not is_dark and start is None:
            start = index
        elif is_dark and start is not None:
            if index - start >= length * 0.18:
                bands.append((start, index))
            start = None
    return bands


def remove_white_background(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    rgba = Image.new("RGBA", rgb.size)
    output: list[tuple[int, int, int, int]] = []
    for red, green, blue in rgb.getdata():
        distance = max(255 - red, 255 - green, 255 - blue)
        alpha = max(0, min(255, (distance - 5) * 12))
        output.append((red, green, blue, alpha))
    rgba.putdata(output)
    alpha = rgba.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value >= 24 else 0).getbbox()
    if bbox is None:
        raise ValueError("source panel contains no foreground artwork")
    return rgba.crop(bbox)


def fit_icon(icon: Image.Image, family: Family) -> Image.Image:
    target_width, target_height = family.max_size
    scale = min(target_width / icon.width, target_height / icon.height)
    size = (
        max(1, round(icon.width * scale)),
        max(1, round(icon.height * scale)),
    )
    rendered = icon.resize(size, Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL_SIZE, CELL_SIZE))
    x = (CELL_SIZE - rendered.width) // 2
    y = CELL_SIZE - rendered.height - 8
    cell.alpha_composite(rendered, (x, y))
    return cell


def load_icons() -> dict[str, Image.Image]:
    sheets: dict[str, Image.Image] = {}
    icons: dict[str, Image.Image] = {}
    for family in FAMILIES:
        path = SOURCE_DIR / family.source_sheet
        if not path.is_file():
            raise FileNotFoundError(path)
        sheet = sheets.setdefault(family.source_sheet, Image.open(path).convert("RGB"))
        x_bands = content_bands(sheet, vertical=True)
        y_bands = content_bands(sheet, vertical=False)
        if len(x_bands) != family.grid or len(y_bands) != family.grid:
            raise ValueError(
                f"{path.name}: expected {family.grid}x{family.grid} cells, "
                f"found {len(x_bands)}x{len(y_bands)}"
            )
        panel_index = family.panel - 1
        row, column = divmod(panel_index, family.grid)
        left, right = x_bands[column]
        top, bottom = y_bands[row]
        source = sheet.crop((left, top, right, bottom))
        border = max(6, round(min(source.size) * 0.018))
        source = source.crop(
            (border, border, source.width - border, source.height - border)
        )
        icons[family.name] = fit_icon(remove_white_background(source), family)
    return icons


def oriented_icon(icon: Image.Image, family: Family, direction: str) -> Image.Image:
    if family.rotatable:
        return icon.rotate(
            DIRECTION_ANGLES[direction],
            resample=Image.Resampling.BICUBIC,
            expand=False,
        )
    if direction in {"W", "NW", "SW"}:
        return ImageOps.mirror(icon)
    return icon.copy()


def shifted(icon: Image.Image, dx: int, dy: int) -> Image.Image:
    frame = Image.new("RGBA", icon.size)
    frame.alpha_composite(icon, (dx, dy))
    return frame


def muzzle_flash(frame: Image.Image, family: Family, direction: str) -> None:
    draw = ImageDraw.Draw(frame)
    if family.rotatable:
        angle = math.radians(DIRECTION_ANGLES[direction])
        dx = math.cos(angle)
        dy = -math.sin(angle)
    elif direction in {"W", "NW", "SW"}:
        dx, dy = -1.0, -0.08
    else:
        dx, dy = 1.0, -0.08
    x = round(CELL_SIZE / 2 + dx * 35)
    y = round(CELL_SIZE / 2 + dy * 35)
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 203, 84, 255))
    draw.point((x + round(dx * 3), y + round(dy * 3)), fill=(255, 244, 190, 255))


def animation_frames(
    icon: Image.Image,
    family: Family,
    action: str,
    direction: str,
) -> list[Image.Image]:
    oriented = oriented_icon(icon, family, direction)
    if action == "STAND":
        return [oriented]
    if action == "WALK":
        return [shifted(oriented, 0, offset) for offset in (0, -1, 0, 1)]
    frames = [oriented.copy(), oriented.copy(), oriented.copy()]
    muzzle_flash(frames[1], family, direction)
    return frames


def build_master_palette(icons: dict[str, Image.Image]) -> Image.Image:
    contact = Image.new("RGB", (CELL_SIZE * len(icons), CELL_SIZE), TRANSPARENT)
    for index, icon in enumerate(icons.values()):
        background = Image.new("RGB", icon.size, TRANSPARENT)
        background.paste(icon.convert("RGB"), mask=icon.getchannel("A"))
        contact.paste(background, (index * CELL_SIZE, 0))
    quantized = contact.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette() or []
    colors: list[tuple[int, int, int]] = [TRANSPARENT]
    for index in range(0, len(raw), 3):
        color = tuple(raw[index : index + 3])
        if len(color) != 3 or color == TRANSPARENT or color in colors:
            continue
        colors.append(color)
        if len(colors) == 256:
            break
    colors.extend([(0, 0, 0)] * (256 - len(colors)))
    palette = Image.new("P", (1, 1), 0)
    palette.putpalette([channel for color in colors for channel in color])
    return palette


def save_sheet(
    frames: list[Image.Image],
    palette: Image.Image,
    path: pathlib.Path,
) -> None:
    rgba = Image.new("RGBA", (CELL_SIZE * len(frames), CELL_SIZE))
    for index, frame in enumerate(frames):
        rgba.alpha_composite(frame, (index * CELL_SIZE, 0))
    rgb = Image.new("RGB", rgba.size, TRANSPARENT)
    rgb.paste(rgba.convert("RGB"), mask=rgba.getchannel("A"))
    indexed = rgb.quantize(palette=palette, dither=Image.Dither.NONE)
    path.parent.mkdir(parents=True, exist_ok=True)
    indexed.save(path, format="BMP")


def bitmap_name(family: str, action: str, direction: str | None) -> str:
    suffix = f" D-{direction}" if direction else ""
    return f"AUBM-IND-{family.upper()} A-{action}{suffix}.bmp"


def descriptor_text(
    bitmap: str,
    palette: str,
    frames: int,
) -> str:
    return (
        "Sprite = {\n"
        f'\tBitmap = "{bitmap}"\n'
        "\tOrigin = { x = 48 y = 82 }\n"
        f"\tFrames = {frames}\n"
        "\tSpeed = 5\n"
        f'\tPalette = "{palette}"\n'
        "}\n"
    )


def write_descriptors() -> list[tuple[pathlib.Path, str]]:
    outputs: list[tuple[pathlib.Path, str]] = []
    for unit_type, family in UNIT_FAMILIES.items():
        palette = f"AUBM-IND-{family.upper()}.bmp"
        stand_bitmap = bitmap_name(family, "STAND", None)
        stand_names = [f"T-{unit_type} A-STAND C-IND L-1.spr"]
        if unit_type in {"INFANTRY", "CARRIER", "escort_carrier"}:
            stand_names.append(f"T-{unit_type} A-STAND C-IND.spr")
        for name in stand_names:
            path = SPRITE_DIR / name
            path.write_text(descriptor_text(stand_bitmap, palette, 1), encoding="ascii")
            outputs.append((path, family))

        for action, frames in (("WALK", 4), ("FIRE", 3)):
            for direction in DIRECTIONS:
                bitmap = bitmap_name(family, action, direction)
                names = [f"T-{unit_type} A-{action} C-IND L-1 D-{direction}.spr"]
                if unit_type in {"INFANTRY", "CARRIER", "escort_carrier"}:
                    names.append(f"T-{unit_type} A-{action} C-IND D-{direction}.spr")
                for name in names:
                    path = SPRITE_DIR / name
                    path.write_text(
                        descriptor_text(bitmap, palette, frames),
                        encoding="ascii",
                    )
                    outputs.append((path, family))
    return outputs


def write_preview(icons: dict[str, Image.Image]) -> None:
    columns = 4
    scale = 2
    tile_width = CELL_SIZE * scale
    tile_height = CELL_SIZE * scale + 24
    rows = (len(FAMILIES) + columns - 1) // columns
    preview = Image.new("RGB", (columns * tile_width, rows * tile_height), (33, 35, 37))
    draw = ImageDraw.Draw(preview)
    font = ImageFont.load_default()
    for index, family in enumerate(FAMILIES):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        tile = Image.new("RGB", (CELL_SIZE, CELL_SIZE), (84, 92, 82))
        tile.paste(icons[family.name].convert("RGB"), mask=icons[family.name].getchannel("A"))
        preview.paste(
            tile.resize((tile_width, CELL_SIZE * scale), Image.Resampling.NEAREST),
            (x, y),
        )
        draw.text(
            (x + 6, y + CELL_SIZE * scale + 6),
            family.name,
            fill=(235, 235, 230),
            font=font,
        )
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    preview.save(PREVIEW, optimize=True)


def write_manifest(outputs: list[tuple[pathlib.Path, str]]) -> None:
    rows: list[dict[str, str]] = []
    family_lookup = {family.name: family for family in FAMILIES}
    for path, family_name in outputs:
        family = family_lookup[family_name]
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "kind": path.suffix.lstrip("."),
                "family": family_name,
                "source": (
                    f"tools/art_sources/v4_sprites/{family.source_sheet}"
                    f"#panel={family.panel}"
                ),
                "provenance": (
                    "generated original India service sprite; "
                    "not derived from another mod"
                ),
                "sha256": sha256(path),
            }
        )
    rows.sort(key=lambda row: row["path"].lower())
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    try:
        icons = load_icons()
        palette = build_master_palette(icons)
        outputs: list[tuple[pathlib.Path, str]] = []
        for family in FAMILIES:
            palette_path = PALETTE_DIR / f"AUBM-IND-{family.name.upper()}.bmp"
            palette_path.parent.mkdir(parents=True, exist_ok=True)
            swatch = Image.new("P", (4, 4), 0)
            swatch.putpalette(palette.getpalette())
            swatch.putdata(list(range(16)))
            swatch.save(palette_path, format="BMP")
            outputs.append((palette_path, family.name))

            stand_path = BITMAP_DIR / bitmap_name(family.name, "STAND", None)
            save_sheet(
                animation_frames(icons[family.name], family, "STAND", "E"),
                palette,
                stand_path,
            )
            outputs.append((stand_path, family.name))
            for action in ("WALK", "FIRE"):
                for direction in DIRECTIONS:
                    path = BITMAP_DIR / bitmap_name(family.name, action, direction)
                    save_sheet(
                        animation_frames(
                            icons[family.name],
                            family,
                            action,
                            direction,
                        ),
                        palette,
                        path,
                    )
                    outputs.append((path, family.name))

        outputs.extend(write_descriptors())
        write_preview(icons)
        write_manifest(outputs)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    bitmap_count = sum(path.suffix == ".bmp" for path, _ in outputs)
    descriptor_count = sum(path.suffix == ".spr" for path, _ in outputs)
    print(
        f"Built {len(FAMILIES)} India sprite families: "
        f"{bitmap_count} bitmap/palette files and {descriptor_count} descriptors"
    )
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {PREVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
