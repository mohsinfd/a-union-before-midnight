#!/usr/bin/env python3
"""Compare V4 air/naval damage pacing with Darkest Hour Full."""

from __future__ import annotations

import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "tools/v4_config.json").read_text(encoding="utf-8"))
STOCK = pathlib.Path(CONFIG["baseline_mod"]) / "db/misc.txt"
V4 = ROOT / "mod/db/misc.txt"

COMMENTS = {
    "air_air_org": "Air vs. Air - Org dmg - Increasing this will increase ORG damage air unit takes in battle with other air units [multiplier]",
    "air_air_str": "Air vs. Air - Str dmg - Increasing this will increase STR damage air unit takes in battle with other air units [multiplier]",
    "air_navy_org": "Air vs Navy - Org dmg - Increasing this will increase ORG damage naval unit takes from air units [multiplier]",
    "air_navy_str": "Air vs. Navy - Str dmg - Increasing this will increase STR damage naval unit takes from air units [multiplier]",
    "navy_air_org": "Navy vs. Air - Org dmg - Increasing this will increase ORG damage air unit takes from naval units [multiplier]",
    "navy_air_str": "Navy vs. Air - Str dmg - Increasing this will increase STR damage air unit takes from naval units [multiplier]",
    "navy_navy_org": "Navy vs. Navy - Org dmg - Increasing this will increase ORG damage naval unit takes from other naval units [multiplier]",
    "navy_navy_str": "Navy vs. Navy - Str dmg - Increasing this will increase STR damage naval unit takes from other naval units [multiplier]",
    "air_critical_chance": "Air vs. Navy - Critical hit chance - Chance for air units to inflict a critical hit (extra STR damage) to ships - checked for each hit inflicted in combat. 0-100 (0 - No critical hits ever, 100 - Every hit is critical)",
    "air_critical_mult": "Air vs. Navy - Str dmg modifier for critical hits inflicted in combats (see above) [multiplier]",
    "navy_critical_chance": "Navy vs. Navy - Critical hit chance - Chance for naval units to inflict a critical hit (extra STR damage) to other ships - checked for each hit inflicted in combat. 0-100 (0 - No critical hits ever, 100 - Every hit is critical)",
    "navy_critical_mult": "Navy vs. Navy - Str dmg modifier for critical hits inflicted in combats (see above) [multiplier]",
    "retreat": "Auto-retreat from combat when average ORG for own or controlled units drop below THIS",
}


def value_after_comment(text: str, comment: str) -> float:
    match = re.search(rf"(?m)^# {re.escape(comment)}\r?\n\s*([-+]?[0-9.]+)", text)
    if not match:
        raise ValueError(f"Cannot find misc setting: {comment}")
    return float(match.group(1))


def mission_speed(text: str, mission: str) -> float:
    match = re.search(
        rf"(?m)^# _MISSION_{mission}_\r?\n\s*\d+[^\r\n]*\r?\n\s*[0-9.]+[^\r\n]*\r?\n\s*([0-9.]+)",
        text,
    )
    if not match:
        raise ValueError(f"Cannot find mission block: {mission}")
    return float(match.group(1))


def main() -> int:
    stock_text = STOCK.read_text(encoding="cp1252")
    v4_text = V4.read_text(encoding="cp1252")
    stock = {key: value_after_comment(stock_text, comment) for key, comment in COMMENTS.items()}
    v4 = {key: value_after_comment(v4_text, comment) for key, comment in COMMENTS.items()}

    theatres = (
        ("Air vs air", "air_air"),
        ("Air vs ships", "air_navy"),
        ("Ships vs air", "navy_air"),
        ("Ship vs ship", "navy_navy"),
    )
    errors: list[str] = []
    print("A Union Before Midnight V4 combat-pacing audit")
    print("  Theatre          Stock STR/ORG   V4 STR/ORG   Relative")
    for label, prefix in theatres:
        stock_ratio = stock[f"{prefix}_str"] / stock[f"{prefix}_org"]
        v4_ratio = v4[f"{prefix}_str"] / v4[f"{prefix}_org"]
        relative = v4_ratio / stock_ratio
        print(f"  {label:16} {stock_ratio:>8.3f}       {v4_ratio:>8.3f}      {relative:>6.1%}")
        if relative > 0.60:
            errors.append(f"{label} still inflicts too much physical loss relative to organization.")
        if v4_ratio < 0.15:
            errors.append(f"{label} physical loss is too low to preserve credible combat risk.")

    for prefix, label in (("air", "air-to-naval"), ("navy", "naval")):
        stock_expected = 1 + (stock[f"{prefix}_critical_chance"] / 100) * (
            stock[f"{prefix}_critical_mult"] - 1
        )
        v4_expected = 1 + (v4[f"{prefix}_critical_chance"] / 100) * (
            v4[f"{prefix}_critical_mult"] - 1
        )
        print(
            f"  {label.title()} critical expected STR multiplier: "
            f"{stock_expected:.2f} stock -> {v4_expected:.2f} V4"
        )
        if not 3 <= v4[f"{prefix}_critical_chance"] <= 8:
            errors.append(f"{label} critical chance no longer represents a rare catastrophe.")
        if v4[f"{prefix}_critical_mult"] < 5:
            errors.append(f"{label} critical hits are no longer meaningfully dangerous.")

    support = mission_speed(v4_text, "SUPPORT_DEFENSE")
    reserves = mission_speed(v4_text, "RESERVES")
    rebase = mission_speed(v4_text, "REBASE")
    print(f"  Auto-retreat organization threshold: {stock['retreat']:g} -> {v4['retreat']:g}")
    print(f"  Emergency rebase move-time multiplier: 1 -> {rebase:g}")
    print(f"  Support-defence move-time multiplier: 0.5 -> {support:g}")
    print(f"  Reserve move-time multiplier: 0.5 -> {reserves:g}")
    if not 10 <= v4["retreat"] <= 15:
        errors.append("Auto-retreat threshold is outside the recoverable-defeat design band.")
    if not 0.30 <= support <= 0.45 or not 0.30 <= reserves <= 0.45:
        errors.append("Operational reserve reaction speed is outside the intended band.")
    if not 0.55 <= rebase <= 0.75:
        errors.append("Emergency rebase speed is outside the intended band.")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("COMBAT PACING GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
