# Alpha 27: failed human terrain-readability review

Follow-up: a separate local **HYBRID-WORLD1** correction was installed on
6 September (India time). See [its current status](HYBRID_TERRAIN_WORLD.md).
The failure analysis below remains the historical Alpha 27 assessment; the
normal Alpha 27 installation has not been changed.

Date: 5 September 2026

Status: **visual requirement failed; correction not implemented or installed.**

The player reports that the terrain classes remain barely distinguishable,
including at the closest zoom. This supersedes any impression that Alpha 27's
offline numerical gates established visual success. The installed four
lightmap hashes were rechecked on this date and all match the Alpha 27 hashes
in `ALPHA27_TERRAIN_VALIDATION.md`. The assets themselves exhibit the problem;
this review does not establish which executable/mod the player last launched.

## Direct visual evidence

The installed Blood and Iron v1.1 and AUBM lightmaps were decoded into matching
native-size crops. No contrast multiplier, sharpening or invented terrain hues
were applied. The controlled comparison uses the same Darkest Hour core
`DarkBlue` colour scale for both artworks. Additional Blood and Iron renders
use its own colour scale to separate palette effects from artwork effects.

Local-only evidence is in `tmp/bi-visual-review/` and is excluded from Git:

| Region / zoom | Alpha 27 | Blood and Iron, same indigo palette |
| --- | --- | --- |
| Northwest India, L1; x=20200, y=3904, 1280x960 | `a27-l1-indigo.png` | `bi-l1-core-indigo.png` |
| Same extent, L2; x=10100, y=1952, 640x480 | `a27-l2-indigo.png` | `bi-l2-core-indigo.png` |
| Central India, L1; x=20800, y=4920, 1024x800 | Not rendered in this review | `bi-central-l1-core-indigo.png` |
| Bengal/Burma, L1; x=21900, y=4600, 1280x768 | Not rendered in this review | `bi-bengal-l1-core-indigo.png` |

Additional palette controls: `bi-l1-own-palette.png` uses Blood and Iron's
LightRed (its India assignment), and `bi-l2-own-indigo.png` uses its DarkBlue.

These are **offline surface reconstructions, not game screenshots**. The
single-colour political renderer does not reproduce country ownership colours,
all water compositing, counters, facilities or the final engine display.
Land artwork and the same-colour comparison are the evidence here. No campaign
was launched, advanced, saved or modified during this review.

## What Blood and Iron actually does better

- Mountains have irregular, connected ridge-and-valley relief, with lit faces
  and shadowed slopes. Their larger structures remain recognizable at L2.
- Desert uses flowing, shaded dune relief rather than isolated repeated rings.
- Forest in the central-India sample has recognizable tree silhouettes in
  separated groups on a quiet background.
- Plains are largely untextured, providing a strong visual reference against
  which rough terrain stands out.
- Its colour scale increases the available light/shadow range. However, its
  mountain and desert artwork remains clearly more legible even under AUBM's
  unchanged core indigo scale. Palette changes alone are not the main fix.

The mod author explicitly credits Decriser's DEC Map for political-map terrain:
https://www.moddb.com/mods/blood-iron-for-darkest-hour

The local B&I map folder overrides `lightmap1.tbl` and `lightmap2.tbl`, but not
L3 or L4. This review directly inspected the two closest zooms; do not claim
four custom B&I zoom layers or a four-zoom engine acceptance result.

B&I is not an eight-class solution either. In the inspected Bengal/Burma
surface, much of the jungle and marsh land is blank. Delhi has no distinctive
urban surface in the northwest sample. Several central-India hill provinces
also lack a distinctive hill surface. These are the coverage gaps the original
request wanted improved, not justification for replacing the successful relief
and tree vocabulary with abstract patterns.

## Why Alpha 27 misses the requirement

Its recipe uses two-screen-pixel cells at every zoom. Mountains look like
diagonal hatching; deserts like repeated loops; plains like speckling. Increasing
mark strength and measuring how many pixels change does not demonstrate that a
human can identify mountains, hills, forest, jungle or marsh without a tooltip.
Giving plains substantial visual noise also reduces the distinction between
open ground and difficult terrain.

The preceding tests remain useful for geometry and encoding safety, but their
contrast/coverage pass is not a terrain-recognition pass. Do not tune the same
motifs again and present the resulting metric increase as completion.

## Recommended correction, not yet implemented

Use recognizable cartographic relief and silhouettes, with this class language:

| Terrain | Required visual treatment |
| --- | --- |
| Plains | Quiet, nearly blank open ground; no blanket speckle |
| Mountain | Large irregular ridge chains, sharp peaks and valley shadows |
| Hills | Lower, rounded and separated relief; clearly gentler than mountains |
| Forest | Readable tree groups with open gaps |
| Jungle | Dense broad-canopy masses, visibly different from forest groups |
| Desert | Flowing dune ridges with consistent lit and shadowed faces |
| Marsh | Shallow water pools/channels with reed clusters |
| Urban | Distinct building blocks and street gaps |

Preserve India's distinct ownership colour. Design contrast around the actual
palette rather than blindly copying B&I's global palette, which changes other
countries and map modes too. Match the mechanical terrain in AUBM's current
Province.csv; do not assume donor artwork always describes AUBM's terrain.

Use B&I/DEC as a visual reference. If donor artwork is reused for the player's
local profile, keep it explicitly local and outside GitHub/public packages;
public original artwork must not be described as a copy-free product if donor
pixels were actually used.

First prove a small representative set covering all eight classes at native
display size, with zoom-specific simplification. Then check the actual engine
at all four zooms in political and terrain mode, including labels/counters and
representative weather. The acceptance question is whether the terrain can be
identified promptly without hovering, not whether a numerical difference is
detectable. Only after that proof should a full-world build be called ready.

This is a visual-only correction: no gameplay changes or new campaign should
be required. Any eventual install must preserve saves and the separate unit
sprite profile, and require a game restart to reload map assets.
