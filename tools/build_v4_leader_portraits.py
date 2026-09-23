#!/usr/bin/env python3
"""Build the additional AUBM Indian leader portraits in Darkest Hour format."""

from __future__ import annotations

import argparse
import io
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "mod" / "gfx" / "interface" / "pics"
CACHE_DIR = Path(os.environ.get("TEMP", ROOT / ".cache")) / "aubm_leader_sources"


@dataclass(frozen=True)
class Portrait:
    leader_id: int
    name: str
    url: str
    crop: tuple[float, float, float, float]


PORTRAITS = (
    Portrait(251016, "P. N. Thapar", "https://commons.wikimedia.org/wiki/Special:Redirect/file/General_Pran_Nath_Thapar.jpg?width=500", (0.04, 0.00, 0.96, 1.00)),
    Portrait(251017, "J. K. Bhonsle", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Major_General_Jagannathrao_Krishnarao_Bhonsle.jpg?width=500", (0.04, 0.00, 0.96, 1.00)),
    Portrait(251024, "Premindra Singh Bhagat", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Premindra_Singh_Bhagat_VC.jpg?width=500", (0.02, 0.00, 0.98, 1.00)),
)


def download(source: Portrait, refresh: bool) -> bytes:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{source.leader_id}.img"
    if cached.exists() and not refresh:
        return cached.read_bytes()

    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "AUBM-Mod-Development/1.0 (personal project)"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read()
    cached.write_bytes(payload)
    return payload


def crop_fraction(image: Image.Image, crop: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    left, top, right, bottom = crop
    box = (
        round(left * width),
        round(top * height),
        round(right * width),
        round(bottom * height),
    )
    return image.crop(box)


def render(payload: bytes, crop: tuple[float, float, float, float]) -> Image.Image:
    image = Image.open(io.BytesIO(payload)).convert("RGB")
    image = crop_fraction(image, crop)
    image = ImageOps.fit(image, (36, 50), method=Image.Resampling.LANCZOS)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.filter(ImageFilter.UnsharpMask(radius=0.7, percent=85, threshold=3))
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="redownload cached sources")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source in PORTRAITS:
        output = OUTPUT_DIR / f"INDL{source.leader_id}.bmp"
        render(download(source, args.refresh), source.crop).save(output, format="BMP")
        print(f"{source.leader_id}: {source.name} -> {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
