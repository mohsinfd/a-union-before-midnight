# ROSTER1 artwork repair — research teams complete, officers pending

Generated with the built-in image-generation tool on 13 September 2026.
Sources and prompt specifications are in `manifest.json`. These are original
fictional institutional scenes, not archival photographs. The four PNG sources
are preserved here. `preview.png` shows the engine-ready images enlarged 2x.

Installed to the Steam game's `Mods/AUBM Terrain Prototype P1`, not the old
Downloads/India Mod folder. Only four picture assignments and their four new
96x96, 24-bit BMP files changed. No gameplay values, events, or saves changed.
The menu continues to say 27-ROSTER1; this is an art-only addition, not another
gameplay release. Live receipt: `AUBM_ART1_INSTALL_RECEIPT.json`.

Validation: all 35 research teams have distinct decoded RGB pixel hashes;
all references resolve; dimensions and BMP format checked; non-picture CSV
columns byte-preserved. All 29 save files unchanged. No native game launch.

## Not complete: officer artwork

Do not describe this patch as unique portraits for every officer.
The existing 375 fictional reserves cycle 64 faces, requiring 311 additional
faces for one-to-one coverage while retaining one assignment per existing face.
Nine named historical commanders still reference `unknownleader`:
251018, 251019, 251020, 251021, 251022, 251023, 251025, 251107, 251108.
Their identities must not be represented as verified archival likenesses by
generating arbitrary faces. Existing historical provenance is recorded in
`tools/data/personnel_art_manifest.csv`.

The 84 minister rows use 69 distinct pixel images. Shared images in the audit
are repeated appearances of the same person in different offices, which is
appropriate; changing a person's face between offices is not an improvement.

The pre-change audit is `build/art1/audit-before.json`. Installation backup is
`build/art1/backups/20260913-132404`. Installer: `tools/build_roster_art1.py`.
It refuses a changed ROSTER1 baseline rather than silently overwriting it.
Do not rerun old artwork builders: their modulo mapping recreates shared faces.
