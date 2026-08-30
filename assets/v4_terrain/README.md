# Alpha 26 original terrain assets

This folder contains the **original, distributable source side** of A Union
Before Midnight's all-terrain political-map layer. It does not contain a
compiled Darkest Hour lightmap or a Blood and Iron/DEC map asset.

## Files

- `aubm_terrain_motifs.json` is the authoritative deterministic recipe for all
  eight mechanical land classes and all four zoom strengths.
- `aubm_terrain_motif_atlas.png` is a neutral Indian-indigo diagnostic sheet.
  Every terrain uses the same base colour; the displayed contrast is 3x so the
  motif shape can be reviewed without pretending that terrain classes have
  different ownership colours.
- `aubm_terrain_motif_moodboard.png` is original AI-assisted concept art used to
  discuss field grain, canopy, ridges, contours, reeds and built fragments. Its
  pixels are never read or sampled by the runtime compiler.

## What the local compiler reads

1. The player's clean Darkest Hour Full `lightmap1.tbl` through
   `lightmap4.tbl`, for encoded geometry, leaf ownership and base brightness.
2. AUBM's current `mod/map/Map_1/Province.csv`, for the actual mechanical
   terrain assigned to each province.
3. `aubm_terrain_motifs.json`, for original mark placement and magnitude.

It does not read a Blood and Iron or DEC lightmap, colour scale, screenshot,
palette or other donor pixel. It does not execute MapUtility.

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

Automated checks establish deterministic structure, provenance, density,
neutrality, distinctness, seam control, protected-pixel identity and all-zoom
coverage. They cannot establish whether the visual result is enjoyable over a
full campaign. Alpha 26 therefore still requires a fresh 1933 in-engine review
at every zoom, followed by the blind terrain-recognition and weather matrix in
`docs/VISUAL_READABILITY_PIPELINE.md`.
