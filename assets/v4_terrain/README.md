# Alpha 27 original terrain assets

This folder contains the **original, distributable source side** of A Union
Before Midnight's all-terrain political-map layer. It does not contain a
compiled Darkest Hour lightmap or a Blood and Iron/DEC map asset.

## Files

- `aubm_terrain_motifs.json` is the authoritative schema-3 deterministic recipe
  for all eight mechanical land classes and all four zoom levels.
- `aubm_terrain_motif_atlas.png` is an Indian-indigo offline native-colour
  diagnostic sheet. Every terrain uses Darkest Hour's real `DarkBlue` colour
  scale with no diagnostic contrast multiplier and no terrain-specific hue.
- `aubm_terrain_motif_moodboard.png` is original AI-assisted concept art used to
  discuss field grain, canopy, ridges, contours, reeds and built fragments. Its
  pixels are never read or sampled by the runtime compiler.

## What the local compiler reads

1. The player's clean Darkest Hour Full `lightmap1.tbl` through
   `lightmap4.tbl`, for encoded geometry, leaf ownership and base brightness.
2. The player's clean Darkest Hour Full `colorscales.csv` and authoritative
   `Modding documentation/Map colors.txt`, used read-only for exact political,
   terrain, Snow and Mud previews and perceptual release measurements.
3. AUBM's current `mod/map/Map_1/Province.csv`, for the actual mechanical
   terrain assigned to each province.
4. `aubm_terrain_motifs.json`, for original mark placement and magnitude.

It does not read a Blood and Iron or DEC lightmap, colour scale, screenshot,
palette or other donor pixel. It does not install or redistribute Darkest
Hour's colour scale, and it does not execute MapUtility.

## Build and install

`tools/aubm_lightmap.py` is the clean-room codec, compiler and QA utility.
`tools/validate_aubm_terrain.py` is the public-source release gate.
`tools/Enable-Aubm-OriginalTerrainVisuals.ps1` performs the complete local
roundtrip, compile, structure check, pixel-ownership comparison, transactional
backup, atomic install and rollback workflow.

The resulting four `.tbl` files remain on the player's machine because they
derive from Darkest Hour. `.gitignore` and the public-installer denylist block
all four lightmaps plus a mod-local `colorscales.csv` from publication.

## Acceptance boundary

Alpha 26's first human test failed because its diagnostic renderer overstated
native political-map contrast and its coverage denominator excluded much of
the map. Schema 3 therefore measures every ordinary mechanical-land pixel and
uses MapUtility-compatible truncating interpolation of the player's real Dark
Hour colour scales. CIEDE2000 is the release metric; DeltaE76 remains in reports
only for continuity with the Alpha 26 audit.

At every zoom, every terrain must meet its density band. Under India's real
`DarkBlue` political colour, each class must have marked-pixel median DeltaE00
at least 3.0 and at least 80% of modified pixels at DeltaE00 >= 2. Under its
official terrain-mode colour, each class must reach median 2.25 and the same
80% threshold. The aggregate political layer must put at least 18% of all
ordinary land at DeltaE00 >= 2. Snow/White and Mud/Brown have a separate
provisional median-1.5 gate with 75% of modified pixels at DeltaE00 >= 1.

The terrain-mode target is deliberately 2.25 rather than 3.0: with the reviewed
maximum offset of ten shade indexes, the official Orange, Yellow and Green
scales cannot all reach 3.0 without making plains/desert/forest more forceful
than mountains and overdriving the political map. That technical limit is
recorded in every local build manifest; it does not waive the human test.

Those gates establish deterministic structure, provenance, density, native
colour contrast, seam control, protected/non-land identity and all-zoom
coverage. They still cannot establish whether the result is enjoyable over a
full campaign. Alpha 27 therefore requires a cold 1933 in-engine review at
every zoom, followed by the blind terrain-recognition and weather matrix in
`docs/VISUAL_READABILITY_PIPELINE.md`.
