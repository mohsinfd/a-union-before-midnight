#!/usr/bin/env python3
"""Convert a four-panel V4 source sheet into Darkest Hour event pictures."""

from __future__ import annotations

import argparse
import pathlib
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageStat


TARGET_SIZE = (400, 116)
TARGET_RATIO = TARGET_SIZE[0] / TARGET_SIZE[1]


def dark_row(image: Image.Image, y: int) -> bool:
    row = image.crop((0, y, image.width, y + 1)).convert("L")
    histogram = row.histogram()
    dark_pixels = sum(histogram[:24])
    return dark_pixels / image.width >= 0.94


def content_bands(image: Image.Image) -> list[tuple[int, int]]:
    dark = [dark_row(image, y) for y in range(image.height)]
    bands: list[tuple[int, int]] = []
    start: int | None = None
    for y, is_dark in enumerate(dark + [True]):
        if not is_dark and start is None:
            start = y
        elif is_dark and start is not None:
            if y - start >= image.height * 0.12:
                bands.append((start, y))
            start = None
    return bands


def crop_to_ratio(image: Image.Image) -> Image.Image:
    current_ratio = image.width / image.height
    if current_ratio > TARGET_RATIO:
        width = round(image.height * TARGET_RATIO)
        left = (image.width - width) // 2
        return image.crop((left, 0, left + width, image.height))
    height = round(image.width / TARGET_RATIO)
    top = (image.height - height) // 2
    return image.crop((0, top, image.width, top + height))


def render_panel(sheet: Image.Image, bounds: tuple[int, int], output: pathlib.Path) -> None:
    top, bottom = bounds
    panel = sheet.crop((0, top, sheet.width, bottom)).convert("RGB")
    panel = crop_to_ratio(panel)
    panel = ImageEnhance.Contrast(panel).enhance(1.06)
    panel = panel.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    panel = panel.filter(ImageFilter.UnsharpMask(radius=0.7, percent=65, threshold=3))
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output, format="BMP")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet", type=pathlib.Path)
    parser.add_argument("names", nargs=4)
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("mod/gfx/events_pics"),
    )
    args = parser.parse_args()

    sheet = Image.open(args.sheet).convert("RGB")
    bands = content_bands(sheet)
    if len(bands) != 4:
        print(f"ERROR: expected four source panels, detected {len(bands)}: {bands}")
        return 1

    for name, bounds in zip(args.names, bands, strict=True):
        output = args.output_dir / f"{name}.bmp"
        render_panel(sheet, bounds, output)
        with Image.open(output) as rendered:
            print(f"{name}: source rows {bounds[0]}-{bounds[1]}, output {rendered.size} {rendered.mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
