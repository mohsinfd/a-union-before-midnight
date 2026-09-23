# Worldwide hybrid terrain — local visual test

Build label: **HYBRID-WORLD1**. Gameplay base: **4.2.0-alpha.27**.

Next visual candidate: the user has chosen [pale jade for India](VISUAL_COLOUR_SELECTION.md).
That choice is not installed; the Gray installation described below is unchanged.

Status: **installed in the isolated prototype on 6 September 2026 (India time);
ready for a short manual visual check, not human-accepted or engine-playtested.**
The final installed receipt lives in that mod's `HYBRID_PROTOTYPE.json`.

Installation rechecked 2,685 protected files/settings, including all original
saves; none changed. Both gameplay audits compared 2,649 files with only the
intended India colour and scenario-title differences. The copied autosave still
matches SHA-256 `f5341755cce047bbeb2d2ddac990dd05c952a226db14196bba8863525e4611fc`.
No game process was launched or controlled. No commit, push or release was made.

## Scope

The regional pilot has been extended to the complete world at all four native
zoom levels. There is no country-specific exception: the mechanical terrain of
each province selects the same visual treatment wherever it is on the map.
Political ownership colours remain a separate engine layer.

| Terrain | Shared worldwide treatment |
| --- | --- |
| Plains | Quiet original core shading |
| Mountains | Local B&I/DEC ridge-and-valley artwork at matching province pixels |
| Desert | Local B&I/DEC dune artwork at matching province pixels |
| Forest | Local B&I/DEC tree groups at matching province pixels |
| Hills | Original rounded-relief raster artwork |
| Jungle | Original dense-canopy raster artwork |
| Marsh | Original pools/reeds raster artwork |
| Urban | Original built-up raster artwork |

B&I supplies L1/L2 only. L3/L4 derive donor relief from matching L2 province
pixels, excluding dark lettering samples. They are not described as existing
B&I L3/L4 files. Original artwork is sampled at native, zoom-specific sizes.

The first worldwide close-up review exposed B&I's differently styled and placed
lettering appearing behind core province names. That candidate was not installed.
The corrected pass removes imported dark lettering and its antialias fringe,
fills those pixels from nearby shading, and restores the core font. Forest
symbols are protected outside the immediate core-lettering neighbourhood so a
font cleanup does not erase the tree vocabulary. European before/after crops
were inspected; this is not an exhaustive human check of every province name.

India retains the prototype's Germany-style `Gray` assignment. Afghanistan is
LightGray, Tibet White, Persia DarkGray; other countries' assignments and all
colour scales are unchanged. Facility strips remain exact Darkest Hour Full
originals, including the grey/blue frames.

This is local-only: donor-derived lightmaps and previews remain in ignored
staging or the user's isolated installation. This is not a public alpha release,
and no donor artwork is to be committed, uploaded or packaged for GitHub.

## Save recommendation

**Use the existing 1 June 1934 autosave for the visual check. A new campaign is
not required for this update.** The isolated mod already has a byte-identical
copy. Its game speed is saved at maximum, so pause promptly after loading.

The update does not alter events, AI, units, technology, alliances, terrain
classifications, province IDs, adjacency, borders or save data. It does not
retroactively apply any gameplay changes from older alpha upgrades. This
recommendation concerns this visual update, not a blanket guarantee about saves
from every previous gameplay release.

The old regional indigo revision loaded this copied save in the engine. The
worldwide grey revision still requires the user's in-engine visual check. A
successful encoding audit is not proof of human terrain recognition.

## How to test the installed build

1. Fully exit any old game session and select **AUBM Terrain Prototype P1**.
2. Verify **HYBRID-WORLD1** on the loading/menu screen. This replaces the prior
   HYBRID-P1-GRAY label, without changing the launcher's default selection.
3. Load the copied **autosave**, pause, and inspect India/Burma, then Europe or
   Southeast Asia to verify the treatment now continues outside the pilot.
4. Try all four zooms in political and terrain mode. Compare mountains/hills,
   forest/jungle, marsh/plains, and urban terrain. Check readable province names
   and the familiar grey/blue ports and airbases.
5. For this first check, no new campaign or lengthy autoplay is needed. If
   continuing the campaign after testing, use a new manual save name in the test
   mod; keep the original campaign as a fallback.

The normal **A Union Before Midnight V4.2** remains unchanged Alpha 27. Selecting
it will not show the hybrid world build. The game is not launched, foregrounded,
paused or otherwise controlled by this workflow.

## Technical verification boundary

- Eleven tests cover codec round trips, native shade range, repeatability,
  crop-independent art, installation-output refusal, full-world tile coverage,
  halo seam equivalence, pilot/world raster equivalence at all four zooms,
  imported-lettering removal and retention of separate forest symbols.
- The corrected world is processed in bounded tiles with a 64-pixel surrounding
  halo so text cleanup and feathering are continuous across boundaries.
- Every core block is considered; tiles containing only water, special pixels
  and plains can be copied unchanged.
- Changed blocks are encoded and independently decoded, checking their exact
  province words, pixel owners and expected six-bit shading.
- Written files are reopened. Changed blocks are independently decoded again;
  unchanged blocks are compared byte-for-byte to the input map; trailers match.
  The initial worldwide pass used the core; the lettering pass uses that fully
  verified world build and reuses the already verified L3/L4 files unchanged.
- Core/donor/atlas/province input hashes are checked before and after the build.
- Installation verifies the four completed file hashes, compares gameplay with
  the normal mod, backs up every replaced test file, and rechecks protected
  original mod files, all original saves and launcher settings afterwards.
- In-engine all-zoom, unit/counter, weather and human recognition checks remain
  pending. Offline native-palette previews are not game screenshots; all land
  uses one comparison colour and weather is an approximation of engine display.
- The regional artwork vocabulary is deliberately reused, not redesigned for
  each continent. Repetition in very large continuous jungle areas can be
  noticeable in the distant African overview; aesthetic acceptance is still
  pending, even though its texture differs clearly from separated forest trees.

## Reproduction

Use Python with NumPy and Pillow. The compiler refuses game/public-mod output
locations and refuses to overwrite an existing staging build.

```
python tools/test_aubm_hybrid_terrain.py
python tools/aubm_hybrid_world.py --output tmp/hybrid-world-fresh/compiled --workers 4
python tools/install_aubm_hybrid_world.py --audit-only
python tools/install_aubm_hybrid_world.py --source tmp/hybrid-world-fresh/compiled --backup tmp/hybrid-world-fresh/backup
```

For this run, the first candidate is `tmp/hybrid-world-v1/compiled`. The corrected
candidate is `tmp/hybrid-world-v3/compiled`, built with `--base` pointing to the
verified first candidate. A receipt-bookkeeping error was corrected before
restarting the incremental pass; the partial v2 directory was not installed.
Use the final candidate and a fresh backup directory for installation. A fresh
full build with the current compiler includes the lettering cleanup directly.

The installer has no arbitrary target option: it can update only the existing
isolated prototype. It refuses installation if Darkest Hour is running. The
backup includes the prior test lightmaps, both screen badges, scenario title,
facility strips and prototype receipt. No files are deleted.

The completed installation used `tmp/hybrid-world-v3/compiled` and its backup is
`tmp/hybrid-world-v3/backup`. Corrected native-palette previews are in the same
v3 folder under `india`, `india-close`, `europe`, `europe-close` and `africa`.
The prototype's older base-install and personal-profile manifests describe its
Alpha 27 foundation, not the new map override; `HYBRID_PROTOTYPE.json` is the
authoritative receipt for this local override.

| Installed map | SHA-256 |
| --- | --- |
| L1 | `6c8bc18af1facdd116439b2d1f10d1ff2b31509a1f08dcefde40b5b2a098fadc` |
| L2 | `b21a5f4c88a94372a05bcde6f46e34d4c945efb950f1de71ac08c62815e90116` |
| L3 | `19c59e0aabaa3025482f3668dd7268ff5a14635ded9a853b3dbbc5ffe9e285e1` |
| L4 | `e82f789c20d097b48d1086e9780edb2808056903e6ca4ab99edbf20fb967d04f` |
