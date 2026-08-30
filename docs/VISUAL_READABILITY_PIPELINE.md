# Visual Readability Pipeline

## Purpose

The normal political map should answer a combat question without forcing a
player to repeatedly change map mode: where are the mountains, jungle, forest,
desert, marsh and snow that will change an operation?  It must remain a
political map first, with readable borders, ownership colours, counters and
air-base icons.

## What the cold comparison found

Blood and Iron obtains its striking default-map look through a replacement
`Map_1` lighting layer, not a small set of ordinary province icons.  Its two
`lightmap*.tbl` binaries differ fundamentally from Darkest Hour Full's four
stock lightmaps.  The local AUBM worktree contains byte-identical copies for
personal research, but they are donor-derived and intentionally excluded from
Git, the public installer and release archive.  They are a useful visual
reference, not an AUBM asset source.

That distinction matters: copying the result into a public release would make
the mod visually attractive at the cost of an unclear redistribution right.
The production path below keeps the player-facing improvement separate from
donor content.

## Alpha 24: safe readability pass

- India uses `DarkBlue` (described in the playtest guide as Indian indigo).
  None of India's immediate neighbours use that colour: Britain is red,
  Afghanistan and Persia are grey, Nepal and Bhutan are dark brown, China is
  pale cyan, Siam is green, Tibet is white, and Japan is yellow.
- `tools/Enable-Aubm-PersonalTerrainVisuals.ps1` offers a strictly local
  reference overlay for a player who already owns Blood and Iron v1.1.  It
  copies only from that local installation into the installed AUBM folder,
  hashes every copied file and backs up any prior local override.  It is never
  part of a GitHub or public-installer package.
- `tools/Enable-Aubm-PersonalIndiaSprites.ps1` restores the player's already
  local 41-family India sprite profile after a public update and rewires only
  the installed registry. It follows the same hash-and-backup rule and is not
  part of a public package.
- This pass does not claim that the donor overlay is an original AUBM terrain
  system.  It makes the desired readability testable during the Alpha 24 human
  playthrough while keeping the public release clean.

## Original AUBM terrain layer: the small asset pipeline

### 1. Establish a technical fixture

Reverse-engineer and write a minimal reader/writer for the Darkest Hour
`lightmap*.tbl` layout against a disposable copy of Map_1.  The first fixture
changes one clearly isolated test province, launches the game, and compares a
screenshot with the untouched map.  No global asset generation begins until
the fixture loads with no map error or crash.

### 2. Build terrain masks from AUBM-owned data

Use the map's province registry and terrain assignments to build masks for:

1. mountains and hills;
2. jungle and forest;
3. desert and marsh;
4. snow; and
5. quiet plains, urban areas and water.

The terrain registry determines *where* a motif may appear.  It should not be
treated as a paint bucket: coastlines, rivers, province labels and boundaries
need masks of their own so the map remains legible.

### 3. Generate a restrained original motif set

Create small, tileable, AUBM-owned source motifs and quantize them to the map's
actual palette and resolution.  The preferred visual language is deliberately
subtle:

| Terrain | Political-map signal |
| --- | --- |
| Mountains | low-contrast ridge hatching |
| Hills | sparse contour stipple |
| Forest | small clustered canopy marks |
| Jungle | darker, denser broadleaf clusters |
| Desert | warm fine grain with no hard outlines |
| Marsh | muted reed/wetland stipple |
| Snow | pale broken highlight, not pure white fill |

AI-generated illustration can be a source for a mood board or a high-level
texture study, but it must be reduced to original, reproducible tile assets
before use.  No Blood and Iron bitmap, palette, lightmap or province
illustration becomes an input to the released generator.

### 4. Compile, inspect and gate the result

The compiler writes a fresh AUBM lightmap layer from those masks.  It records
the generated inputs, output hashes and palette.  A release gate checks that:

- every output is original and has recorded provenance;
- political borders, rail/port/air-base icons and city labels remain readable;
- mountain, jungle, forest and desert can be identified at normal zoom;
- the map loads at the supported resolutions with no log errors; and
- a screenshot comparison confirms no unintended whole-map recolour.

The generated binaries remain opt-in until an executable smoke test and a
human combat playthrough accept the result.  Once accepted, they can become a
fully original AUBM visual package rather than a local reference overlay.

## Playtest questions

During the next Japan-route campaign, evaluate the map with four quick checks:

1. Can Burma's jungle versus hill approaches be recognized without changing
   map mode?
2. Can a player distinguish the Himalayan mountain wall from ordinary hill
   country at normal zoom?
3. Do the Bay of Bengal air and naval icons remain clearer than the terrain
   texture underneath them?
4. Is Indian indigo distinct from every land neighbour and from British-held
   territory during a crowded campaign?

If any answer is no, the right response is to reduce texture contrast or mask
placement before adding more art.
