# Visual Readability Pipeline

## Purpose

The normal political map should answer a combat question without forcing a
player to change map mode: what terrain will this operation cross? The target
is not a decorative topographic map. It is a political map on which all eight
mechanical land classes remain identifiable while borders, ownership colours,
labels, counters, railways and facility icons stay readable.

The eight required land classes are **Plains, Forest, Mountain, Desert, Marsh,
Hills, Jungle and Urban**. Ocean is a separate background class. Snow is a
weather state, not a ninth terrain class.

## Alpha 26 composition and provenance

Alpha 26's terrain surface is an original AUBM procedural layer generated
locally from the player's Darkest Hour Full map. It does **not** reuse a Blood
and Iron or DEC Map lightmap, colour scale, palette, screenshot crop or traced
pixel. Blood and Iron was audited as the former private reference and then
removed from the runtime terrain path.

| Active or relevant asset | Provenance | What it does | Distribution status |
| --- | --- | --- | --- |
| core `map/Map_1/lightmap1.tbl` through `lightmap4.tbl` | player's legally installed Darkest Hour Full | supplies encoded geometry, original leaf ownership and base 6-bit brightness to the local compiler | read locally; not redistributed |
| core `colorscales.csv` fallback | player's Darkest Hour Full | converts the compiled 6-bit brightness into the normal political-map surface | inherited locally; no AUBM or donor replacement ships |
| `mod/map/Map_1/Province.csv` | AUBM gameplay data | assigns each playable province to the current mechanical terrain class, including AUBM terrain corrections | public AUBM content |
| `assets/v4_terrain/aubm_terrain_motifs.json` | original AUBM deterministic recipes | defines eight semantic brightness motifs and four restrained zoom strengths | public AUBM content |
| `tools/aubm_lightmap.py` | clean-room AUBM codec/compiler | preserves the Darkest Hour encoding while applying only the current province's approved motif | public AUBM content |
| `tools/Enable-Aubm-OriginalTerrainVisuals.ps1` | AUBM transactional installer | compiles, validates, backs up, installs or rolls back exactly four lightmaps plus the local colour-scale override state | public tool; generated outputs stay local |
| generated AUBM `lightmap1.tbl` through `lightmap4.tbl` | player-owned Darkest Hour input plus original AUBM recipes | supplies the finished eight-terrain surface at every zoom | local generated binaries; excluded from Git and public installer manifests |
| `aubm_terrain_motif_moodboard.png` | original AI-assisted AUBM concept study | informed vocabulary such as ridges, arcs, reeds and canopy mass | public concept art; no moodboard pixel is sampled by the compiler |
| India's `DarkBlue` country colour, Indian flag/icon and counter strip | AUBM release work using the existing game palette plus AUBM assets | ownership and unit readability above the terrain surface | public AUBM content |
| optional 41-family India sprite profile | reconstructed from the player's local Blood and Iron/Darkest Hour files by a separate tool | unit animation only; unrelated to terrain | local-only and not redistribution-cleared |

The first generated motif fixture was deliberately rejected. It repeated a
global checker every 64 source pixels and measured about 10.7 times more
gradient energy at coarse-cell boundaries than inside them. A second wave/grid
study was also rejected because continuous bands and streets did not express
the requested semantic terrain language. Neither rejected design is installed.

The accepted Alpha 26 source instead uses sparse hash marks, separated canopy
clumps, short ridge pairs, broken dune/contour arcs, short water and reed marks,
dense irregular jungle masses and compact urban fragments. Motif density is
kept stable across zooms while only the brightness amplitude reduces. The atlas
uses one neutral Indian-indigo base for every class and the same 3x diagnostic
contrast as the map renderer, so class identity is not faked by giving each
terrain its own colour.

An exhaustive encoded-layer audit of all 336,960 Blood and Iron `lightmap1`
blocks confirms the coverage gap before runtime rendering. Mountain and Desert
are strong, highly detailed outliers: a simple cross-validated classifier found
97.8% Mountain recall and 93.9% Desert recall. The other six classes overlap
heavily; examples include 96.5% histogram overlap for Plains/Jungle, 92.3% for
Marsh/Jungle and 89.8% for Plains/Marsh. Jungle recall was 7.4%, Urban 12.5%
and Forest 37.4%; total balanced accuracy was only 40.5% for eight classes.
These are encoded 6-bit brightness/quadtree statistics, not human-visible
rendered luminance, so screenshots are still required. They do establish that
the donor does not contain eight reliably separate terrain signatures. In
practical terms, treat Mountain and Desert as the donor's clear successes,
Forest as partial, and Plains/Marsh/Hills/Jungle/Urban as unresolved rather than
claiming complete coverage.

## Alpha 24 reference pass and Alpha 26 replacement

- India uses `DarkBlue` (described in the playtest guide as Indian indigo).
  None of India's immediate neighbours uses that country colour.
- `tools/Enable-Aubm-PersonalTerrainVisuals.ps1` offers a strictly local
  reference overlay for a player who already owns Blood and Iron v1.1. It
  copies only from that local installation into the installed AUBM folder,
  hashes every copied file and backs up any prior local override. It is never
  part of a GitHub or public-installer package.
- `tools/Enable-Aubm-PersonalIndiaSprites.ps1` restores the player's already
  local India sprite profile after a public update. It follows the same
  hash-and-backup rule and is not part of a public package.
- This pass does not claim that the donor overlay is an original AUBM terrain
  system. It makes the desired readability testable while keeping the public
  release clean.
- Alpha 26 supersedes that reference overlay with the original local compiler
  described above. The personal reference helper remains only for historical
  comparison and is not part of the finished Alpha 26 runtime terrain surface.

## Original AUBM terrain layer

### 1. Establish an exact geometry fixture

Use disposable copies of the clean Darkest Hour core `lightmap1.tbl` through
`lightmap4.tbl` and its colour scale, never the active installation and never
the Blood and Iron binaries. Decode the lightmaps' offset tables, per-block
province lists, quadtree leaves, leaf-owner indexes and packed 6-bit colour
values. The decoded leaf ownership is the exact mask source at each zoom; an
expanded province-ID raster may be generated from it for inspection.

MapUtility 1.2.5b's information package can document the format, but its
executable is not a released build dependency. The audited archive provides no
source-code or redistribution licence, so do not commit or repackage its
executables or DLL. Validate the AUBM decoder against the installed Darkest Hour
binaries rather than a generic dimension table. The audited engine uses
32-by-32 compressed blocks in these grids: `lightmap1`
936x360, `lightmap2` 468x180, `lightmap3` 234x90 and `lightmap4` 117x45. A tool
or document that doubles either distant-zoom dimension is not an acceptable
production fixture.

The engine's `boundbox.tbl`, `index.tbl` and `Modding documentation/DH-IDmap.png`
are useful cross-checks, not mask sources. The PNG is downscaled and annotated.
Likewise, `Province.csv` fill coordinates are seed assertions, not polygons.

The codec's canonical no-op path must parse and rewrite every block in all four
clean core lightmaps byte-for-byte. A separate zero-motif refinement fixture
must then reconstruct the same owner and brightness rasters before an actual
motif build is eligible for installation. Offline success does not waive the
fresh-1933 executable and human visual gates below.

### 2. Join geometry to current AUBM terrain data

At every zoom, resolve each decoded leaf's owner index to its province ID, then
read that ID's terrain from the current `mod/map/Map_1/Province.csv`. The eight
logical masks are mutually exclusive sets of land leaves. Ocean, province ID 0,
the terminal row and encoded special/border IDs are never land masks. Rebuilding
after a `Province.csv` change must move every leaf owned by that province to its
new visual class; no hand-painted province list is allowed.

The terrain class determines where a motif may alter the 6-bit brightness
sample. The safest fixture mode preserves every offset, province ID, owner
index, quadtree bit, border encoding, trailer and other non-colour byte exactly.
Protect special border leaves and unsafe brightness ranges. Static map names,
shadows and relief also live in the colour-scale samples, so their protected
ranges need screenshot verification. Cities, railways, counters, ports,
beaches and airfields are separate rendered layers; the executable and human
gates must verify that motif contrast beneath them remains restrained.

### 2a. Refine coarse leaves only after the fixed-tree fixture passes

The rejected checker fixture showed that changing one value per existing coarse
leaf was not enough for organic 1-3 px cues. The Alpha 26 refinement compiler
split eligible ordinary-land leaves larger than four pixels, inheriting the
exact original owner index. It must not split Ocean, ID 0, protected/special
leaves or protected static artwork.

This mode is structurally higher risk and must follow the binary format exactly:

- preserve each block's province-list words and order; special IDs index that
  list, so deduplication or reordering is unsafe;
- copy the source leaf's original stored colour into every refined child before
  adding a motif offset; the zero-motif raster must therefore remain exact;
- write quadtree bits least-significant-bit first in bottom-right, bottom-left,
  top-right, top-left order; a level-one split has four implicit pixel leaves;
- pack owner indexes least-significant-bit first at 0/1/2/4/8 bits according to
  province-list length, then pack four 6-bit colours into each three bytes; and
- rebuild the `N+1` 32-bit offset table and preserve any source trailer.

The unchanged canonical codec remains the reference oracle. Refinement is
acceptable only if its zero-motif owner and raw-brightness rasters are exact.

### 3. Generate eight restrained original motifs

Alpha 26 uses small deterministic AUBM-owned procedural motifs quantized to the
actual map brightness range and resolution. Every mechanical land class has a
recognizable signal; “quiet” does not mean invisible.

| Mechanical land class | Required political-map signal | Critical distinction |
| --- | --- | --- |
| Plains | fine irregular grain, offsets -1..+1, 25-35% coverage | not Urban, Desert or an unpainted gap |
| Forest | rounded 1-3 px canopy clusters, offsets -2..+3, 40-55% coverage | lighter and at least 20 percentage points less dense than Jungle |
| Mountain | broken diagonal ridge/shadow pairs, offsets -3..+4 | stronger than Hills; no mirrored X or checker hatch |
| Desert | sparse staggered dune arcs/flecks, offsets -2..+2 | texture without a uniform pale wash |
| Marsh | short horizontal water dashes plus isolated reeds | not Forest; no complete repeated row or column |
| Hills | soft broken crescents/contours, offsets -2..+2 | RMS contrast at least 30% below Mountain |
| Jungle | irregular interlocking clusters, offsets -3..+3, 60-75% coverage | at least 20 percentage points denser than Forest |
| Urban | broken streets and 2x2 blocks, offsets -3..+3, 45-65% coverage | no continuous Cartesian grid; not a city icon by itself |

Ocean remains a quiet background and must not receive a land motif. Snow does
not belong in this table: it is tested as a weather layer over the terrain.

AI-generated illustration may be used for a mood board or texture study, but
released motifs must be original, reproducible build inputs. No Blood and Iron,
DEC Map or other donor bitmap, palette, lightmap, screenshot crop or traced
province illustration may enter the generator.

Use a 16x16 one-pixel master motif where possible, or at minimum an 8x8 motif
with two-pixel cells. Add deterministic low-amplitude irregularity so no global
Cartesian grid is visible. Derive a separately simplified profile for each zoom
instead of sampling one coarse grid unchanged at all four scales.

### 4. Compile every zoom layer deterministically

Compile `lightmap1.tbl` through `lightmap4.tbl` from the same class masks and
the four zoom-specific reductions of the approved master motifs. Use either a
hash-pinned Darkest Hour core colour scale or an
AUBM-owned replacement; never silently substitute the personal Blood and Iron
files. A clean build run twice with identical inputs must produce byte-identical
outputs and an input/output hash manifest.

After compilation, extract the result again and verify that province IDs,
borders and coast geometry still match the fixture. Check the world-wrap seam,
32-pixel block boundaries and motif clipping at every zoom before copying any
output into a playable mod.

## Weather is a separate acceptance matrix

Weather markers animate over the map and can obscure a subtle motif. They must
therefore be tested independently from province classification. Every cell
below is required in the offline composite fixture; engine screenshots cover
every combination the engine can produce in a disposable scenario.

| Weather state | Plains | Forest | Mountain | Desert | Marsh | Hills | Jungle | Urban |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clear / no marker | required | required | required | required | required | required | required | required |
| Rain | required | required | required | required | required | required | required | required |
| Storm | required | required | required | required | required | required | required | required |
| Snow | required | required | required | required | required | required | required | required |

A cell passes only when the weather state is recognizable, the underlying land
class is still recognizable, and borders, labels, counters and facility icons
remain legible. The stock `Snow.bmp`, `rain.bmp` and `storm.bmp` may be used as
Darkest Hour runtime foundations if their exact hashes are recorded; they are
not evidence that the terrain below them has passed.

## Validator contract

The original layer remains a post-install local step because its generated
lightmaps derive from the player's Darkest Hour files. Installation requires
the automated gates that can be established offline. Executable smoke, weather
coverage and blind human recognition remain explicit acceptance boundaries,
not facts inferred from static validation. Reports name the mod version, source
revision, clean game fixture and hashes of every generated output.

The current generator's `validate` command is a binary-structure check only.
Passing it proves that every block decodes and that the four files are not
truncated; it does not satisfy the provenance, weather, executable or human
readability gates below.

### Gate A: provenance and clean-fixture preflight

- Fail if a Blood and Iron/DEC personal-overlay file is active in the test mod,
  because it can mask a missing or broken AUBM layer.
- Fail if any source or generated output matches a Blood and Iron/DEC donor
  hash. Separately, fail if a path excluded by
  `installer/nonredistributable-overlay-patterns.txt` is selected for a public
  installer manifest.
- Require a manifest entry for every motif, palette/colour-scale input,
  `Province.csv`, geometry input, compiler version and generated lightmap.
- Hash the generator source itself and record logical source roles/relative
  paths; do not write a user's absolute game or profile path into a report that
  may be shared.
- Require two clean builds to produce identical hashes.
- The installer exclusion is deliberately path-based and blocks all
  `lightmap1.tbl` through `lightmap4.tbl` payloads and any local
  `colorscales.csv`. The public-safe release ships the AUBM generator and motif
  definitions while compiling the player's Darkest Hour-derived binaries
  locally. Do not weaken this guard to publish a generated output hash.

### Gate B: terrain-data and mask integrity

- Require exactly eight named integer master motifs and no extra terrain key,
  plus a deterministic reduction for each of the four zooms. Each profile must
  be non-zero and unique even under cyclic translation or rotation, obey the
  per-class offset and coverage limits above, and use source cells no larger
  than two pixels.
- Keep every motif's absolute mean offset at or below 0.5 so it remains a
  texture rather than a replacement ownership colour. Reject a constant
  rectangular motif feature larger than three screen pixels at combat zoom.
- Require the protected source-colour interval and every allowed motif offset
  to remain inside the engine's 0-63 colour range without relying on clamping.
- Parse `Province.csv` and require exactly the eight supported land values.
  Treat Ocean, the ID-zero sentinel, the terminal `-1` row and non-province
  pixels separately.
- Require every decoded playable province ID to have exactly one current CSV
  record and every playable CSV province ID to occur in at least one decoded
  zoom-one leaf. Report province, leaf and reconstructed pixel area for all
  eight classes, and fail if any class is empty.
- Require every eligible land leaf to map to exactly one land-class mask at
  every zoom. Pairwise intersections must be zero and the union must equal all
  eligible land-leaf pixels.
- Require non-zero eligible and modified pixels for each class at every zoom,
  and enforce that class's declared coverage band: Plains 25-35%, Forest
  40-55%, Mountain 20-40%, Desert 12-24%, Marsh 15-30%, Hills 20-40%, Jungle
  60-75% and Urban 45-65%. Zoom strength changes magnitude rather than erasing
  marks. Coverage is still an absence/aliasing guard; the blind human gate
  remains the visibility proof.
- Validate each province's declared fill coordinate against its own ID mask and
  report every mismatch. The exact ID raster remains authoritative; never
  repair geometry by assigning a province from a fill coordinate alone.
- Cross-check every terrain-changing row in
  `tools/data/province_overrides.csv`; its rendered class must match
  `new_terrain`, not `old_terrain`.
- Fail if province ID 0, Ocean, a terminal/special ID, a protected colour sample
  or any byte outside a declared 6-bit colour payload changes.

### Gate C: compiled-output integrity

- Require fresh, manifested `lightmap1.tbl` through `lightmap4.tbl`; no zoom may
  fall back to Blood and Iron or an older generated run.
- Require the exact block grids 936x360, 468x180, 234x90 and 117x45. Decode the
  full offset table and every quadtree block; reject invalid offsets, province
  IDs, packed ownership data, colour-scale values outside 0-63, or unexplained
  trailing bytes in an AUBM-generated file.
- Re-extract the compiled result and require province-ID, coast and border
  geometry to match the clean fixture exactly.
- In fixed-tree mode, require output length and every non-colour byte to be
  byte-identical to the corresponding clean Darkest Hour source. Before using
  refinement mode, require a byte-identical unchanged parse/write round trip,
  exact per-block province-list bytes and an exact zero-motif 32x32 raw owner
  raster, including special IDs.
- In refinement mode, require the zero-motif 32x32 raw brightness raster to be
  exact. Ocean, sentinel, special and protected pixels must remain unchanged.
- Enforce the declared straight-run caps for every motif; separately require
  Hills RMS contrast to be at most 70% of Mountain and pairwise motif
  correlation to remain below the declared limit.
- Fail on world-wrap discontinuities, new 32-pixel block seams, corrupt headers,
  invalid palette indexes, truncated files or non-deterministic hashes.
- Require per-province mean rendered-luminance drift no greater than 3/255 and
  a coarse-cell-boundary/interior gradient ratio no greater than 2.0. Reject any
  visible global grid or checker pattern.
- Produce a contact sheet at all four zooms under Indian indigo, British red,
  Japanese yellow and a neutral grey ownership colour. Review must confirm that
  the motif does not become an ownership recolour.

### Gate D: executable smoke and regression test

- Start the shipped mod from a cold process and launch a fresh 1933 campaign.
- Visit every zoom, pan across India, Burma, the Himalayas, Southeast Asia and
  the world-wrap seam, then return to the political map.
- Exercise clear, rain, storm and snow markers where the engine permits them.
- Fail on a crash, map parse/lightmap error, missing texture, flicker, stale
  zoom layer, displaced border/icon, or unacceptable pan/zoom slowdown.
- Repeat once from a save to confirm the visual package is save-neutral. This
  is a compatibility check, not permission to validate gameplay on an old save.

### Gate E: blind human readability test

- Capture at least four unlabeled normal-combat-zoom crops per land class from
  more than one theatre: 32 clear-weather crops total.
- Without tooltips or switching map mode, a tester must identify at least 90%
  overall and at least three of four examples for each class.
- Explicitly review the confusion pairs Hills/Mountain, Forest/Jungle,
  Plains/Urban, Plains/Desert and Forest/Marsh.
- Require at least 80% correct identification within each named confusion pair.
- Repeat one representative crop per class under Rain, Storm and Snow. Require
  correct weather recognition in all 24 crops and underlying terrain
  recognition in at least 20 of 24.
- Small Urban and Marsh crops must each contain at least two recognizable motif
  features. Border local contrast must retain at least 90% of baseline, and a
  50-label sample may introduce no additional reading error.
- Fail if any gain in terrain recognition makes borders, ownership, labels,
  counters, ports, beaches or airfields harder to read during combat.

## Playtest focus

The first campaign review should answer these concrete questions:

1. Can Burma's plains, jungle and hill approaches be recognized without a map
   mode change, including provinces changed by AUBM's terrain corrections?
2. Can a player distinguish Himalayan Mountains from ordinary Hills at normal
   combat zoom?
3. Can Forest and Jungle be told apart in Southeast Asia while Rain or Storm is
   visible?
4. Are Plains and Urban provinces visibly different without relying on the city
   icon?
5. Do Bay of Bengal air/naval/facility icons and borders remain clearer than the
   texture beneath them?
6. Does the same terrain signal survive Indian indigo, British red, Japanese
   yellow and neutral grey ownership colours at all four zooms?

If a class fails recognition, adjust that class's motif density or shape. If
political information fails, reduce motif contrast or expand the protection
masks. Do not solve either failure by reintroducing donor lightmaps.
