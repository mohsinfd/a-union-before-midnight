# Japan Rising - R14

A human-Japan campaign for **Darkest Hour 1.05.2 + Blood and Iron v1.1**, beginning in 1933. Historical diplomacy through Pearl Harbor leads into alternative Pacific, Indian Ocean, Chinese, Soviet and American campaigns through 1950.

This is the **japan-rising** branch of `mohsinfd/a-union-before-midnight`. The India project remains on its existing branches; this branch contains the separate Japan mod.

## Download and install

Download the source ZIP from [Releases](https://github.com/mohsinfd/a-union-before-midnight/releases/tag/japan-rising-r14), or clone this branch:

```powershell
git clone --branch japan-rising --single-branch https://github.com/mohsinfd/a-union-before-midnight.git
```

You need your own **Darkest Hour** and **Blood and Iron v1.1** folders, Windows, and Python 3.11 or later. Pillow 12.3.0 is the tested image dependency. The game and foundation are not included.

Extract the ZIP to a folder you will keep, open PowerShell there, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -GameRoot "C:\Games\Darkest Hour" -BloodIronRoot "C:\Mods\Blood and Iron v1.1"
```

Alternatively, double-click **INSTALL.bat** and enter the two folder paths when prompted. The installer checks your local folders, clones the foundation into **Mods\Japan Rising JX1 Alpha2**, applies the mod, runs offline verification and creates a desktop shortcut. It **does not launch the game**. Close the game before installing; the builder refuses to overwrite a running session. The destination must be writable.

Start a **new 1933 campaign as Japan** through **Japan Rising JX1 Alpha2**. Confirm **R14** in the scenario and welcome event. Existing saves are not migrated by this installer. Keep the extracted source folder because the shortcut uses its launcher.

## R14 cold-review repairs

Tougher Chinese surrender requires no more than 60 surviving deployed formations alongside the territorial objectives. Delayed Chinese army replacement is removed. Coalition-safe settlements, recoverable US/Soviet talks, Hawaiian terms before acceptance, current-equipment American reserves and meaningful postwar agreements are included. All ten specialist families have expanded construction-stack comparisons; Matsu and emergency oil are retuned. See [the full change register](japan_expansion/R14_CHANGES.md).

## What is included

- Expanded economic, oil, manpower, production, diplomacy and country-settlement content.
- Ten specialist equipment families, automatic free first issues, normal researched upgrades and distinct artwork. Four latest classes are long-range naval fighters, long-range naval attack aircraft, economical Matsu escorts and full-strength Expeditionary Assault Infantry.
- Reworked Japanese research teams, ministers and commanders.
- Island defence detachments and finite convoy support.
- Transport protection introduced in R13.1 assigns eight existing Allied screens to starting transport groups and shifts thirty AI construction profiles towards Destroyers. Fleet regrouping remains engine-controlled; permanent transport escorts are not guaranteed.
- Source, original generated artwork, complete event catalogue, audit tools and installation instructions. No game files, donor map/graphics payload, saves, credentials, crash dumps or temporary backup trees are bundled.

Read [the campaign overview](japan_expansion/README.md), [specialist costs/research/upgrades](japan_expansion/R13_UNITS.md), [transport AI changes](japan_expansion/R13_1_CHANGES.md), and [the current progress record](japan_expansion/PROGRESS.md).

## Verification and limits

The installer runs fresh specialist-delivery, enemy-AI, player-copy, China/peace/postwar/economic regression and static checks, then compares actual installed event commands, models, artwork and loaded English with source before publishing a matching installation receipt. The release was checked without running Darkest Hour. Actual battle performance, convoy allocation, fleet regrouping and long-campaign stability remain playtest observations.

The repository contains historical audit and save-repair utilities for reference. **Install.ps1 is the supported installation path**; it does not run those older repair scripts. Device paths live in an ignored `japan_expansion/local_paths.json`; no developer image-cache access is required.

See [RIGHTS.md](RIGHTS.md) for original artwork and foundation provenance. The separate Germany mod is not part of this branch.
