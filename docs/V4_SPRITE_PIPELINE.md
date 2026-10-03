# AUBM India Sprite Pipeline

This is the optional personal-play visual pipeline for **A Union Before
Midnight**. The public build does not invoke it and uses Darkest Hour Full's
stock sprite keys. With `-IncludePersonalSprites`, it installs local copies of
proven Darkest Hour and donor sprite assets; those outputs must not be treated
as redistributable AUBM artwork without permission from their authors.

## Current Build

The verified build contains:

- 41 independently addressable India unit families
- 591 `C-IND` descriptors: 41 stand, 328 walk, and 222 fire descriptors
- 553 copied sprite bitmap strips and 44 copied external palettes
- 1,188 manifest-owned files, totalling 329,100,316 bytes
- eight-direction movement for every family
- genuine multi-frame movement and combat for every family
- 41 unique stand bitmap-and-palette signatures
- Blood and Iron v1.1 assets for 40 families
- the Darkest Hour core nuclear-submarine family for the one visual B&I does not distinguish

The complete machine-readable inventory and donor provenance is in:

`mod/gfx/map/units/AUBM-IND-GENERATED-MANIFEST.json`

## Sprite Keys

Darkest Hour normally shares several sprite keys, including carriers, rockets, and fighter variants. `Ensure-Aubm-UniqueSpriteKeys.ps1` changes only the `sprite =` field inside the 41 existing registry blocks. It does not add, remove, reorder, or alter the statistics of a unit type.

| Unit type | India sprite key | Visual family |
| --- | --- | --- |
| infantry | `d_41` | Indian line infantry |
| cavalry | `d_42` | Indian cavalry |
| motorized | `d_43` | Indian motorised infantry |
| mechanized | `d_44` | Indian mechanised infantry |
| light_armor | `d_45` | Indian light armour |
| armor | `d_46` | Indian armour |
| paratrooper | `d_47` | Indian paratroops |
| marine | `d_48` | Indian marines |
| bergsjaeger | `d_49` | Indian mountain troops |
| garrison | `d_50` | Indian garrison |
| hq | `d_51` | Indian headquarters |
| militia | `d_52` | Indian militia |
| multi_role | `d_53` | Indian multirole fighter |
| interceptor | `d_54` | Indian interceptor |
| strategic_bomber | `d_55` | Indian strategic bomber |
| tactical_bomber | `d_56` | Indian tactical bomber |
| naval_bomber | `d_57` | Indian naval bomber |
| cas | `d_58` | Indian close-support wing |
| transport_plane | `d_59` | Indian air transport |
| flying_bomb | `d_60` | Indian flying bomb |
| flying_rocket | `d_61` | Indian ballistic rocket |
| battleship | `d_62` | Indian battleship |
| light_cruiser | `d_63` | Indian light cruiser |
| heavy_cruiser | `d_64` | Indian heavy cruiser |
| battlecruiser | `d_65` | Indian battlecruiser |
| destroyer | `d_66` | Indian destroyer |
| carrier | `d_67` | Indian fleet carrier |
| escort_carrier | `d_68` | Indian escort carrier |
| submarine | `d_69` | Indian submarine |
| nuclear_submarine | `d_70` | Indian nuclear submarine |
| transport | `d_71` | Indian naval transport |
| light_carrier | `d_72` | Indian light carrier |
| rocket_interceptor | `d_73` | Indian rocket interceptor |
| d_rsv_33 | `d_74` | Gurkha Rifles |
| d_rsv_34 | `d_75` | Frontier Force |
| d_rsv_35 | `d_76` | Chindit Columns |
| d_rsv_36 | `d_77` | Indian Airborne |
| d_rsv_37 | `d_78` | Coromandel Marines |
| d_rsv_38 | `d_79` | Guards Armour |
| d_rsv_39 | `d_80` | Guards Motorised |
| d_rsv_40 | `d_81` | Indian Pioneers |

## Build Behaviour

Run from the repository root:

```powershell
& .\tools\Build-Aubm-IndiaSprites.ps1
```

The builder:

1. Applies the idempotent 41-key registry patch.
2. Indexes the required B&I and Darkest Hour descriptor families.
3. Selects a complete family with one stand descriptor, all eight walk directions, and donor-supported fire directions.
4. Rejects one-frame movement or combat candidates.
5. Preserves donor frame counts, origins, speeds, directions, bitmap bytes, and palette bytes.
6. Writes normalized `T-<key> ... C-IND L-1` descriptors.
7. Records the source mod, source path, source hash, output hash, size, and role of every generated file.

The pipeline never creates a vertical-translation or bobble animation. It copies complete donor strips, and the validator confirms that animated strips contain multiple distinct frames. It also never generates a magenta-background bitmap: transparency remains palette-indexed, the referenced external palette is copied locally, and palette/index integrity is validated frame by frame.

Cleanup is manifest-based. A later build may remove only stale files named in the preceding generated manifest and only when their resolved paths remain under `mod/gfx/map/units` or `mod/gfx/palette`. It does not recursively delete either tree and leaves unrelated or user-authored assets alone.

## Validation

Run the complete gate:

```powershell
py -3 .\tools\validate_aubm_sprites.py
```

The validator checks:

- all 41 registry blocks and unique sprite keys
- exact `C-IND`, `L-1`, action, and direction descriptor naming
- descriptor braces and required fields
- every bitmap and palette reference
- manifest ownership, SHA-256 hashes, byte counts, and donor provenance
- Windows BMP headers, dimensions, compression, bit depth, and pixel bounds
- strip width divisibility by `Frames` and real per-frame dimensions
- all eight walk directions and native donor combat coverage
- multi-frame and multi-image movement/combat animation
- per-frame visible pixels and palette-indexed transparent mattes
- unique stand bitmap-and-palette signatures for all 41 families
- an automatic second build followed by byte-for-byte idempotence comparison

Use `--skip-idempotence` only inside a parent build that has already run the builder once:

```powershell
py -3 .\tools\validate_aubm_sprites.py --skip-idempotence
```

## Rebase Integration

`tools/Rebase-V4-DirectDH.ps1` defaults to a donor-free public profile. It first
restores Darkest Hour Full's stock registry keys, then
`Ensure-Aubm-SpecialUnits.ps1` establishes the eight reserved unit blocks with
stock-family sprite fallbacks. Passing `-IncludePersonalSprites` runs the sprite
builder and deep validator after that public baseline; the parent build's second
complete rebase supplies the byte-for-byte repeat-build test.

```powershell
BUILD_AND_DEPLOY_V4.bat -ValidateOnly -IncludePersonalSprites
```

This order matters: the special-unit builder owns the definitions of
`d_rsv_33..40`; the optional sprite builder then assigns and validates the
engine-native numeric visual keys `d_74..81` without touching their statistics.
Without the switch, reserved units reuse the nearest stock sprite family.

Donor-derived special-unit model cards and panels are not packaged. Reserved
models 33-40 currently use the engine's missing-art placeholder in unit-detail
and production views; original redistribution-safe panels remain future work.
