# Alpha 27 terrain validation record

Version: `4.2.0-alpha.27`
Date: 30 Aug 2026
Scope: native-contrast correction to the original AUBM all-terrain layer

## Why Alpha 27 exists

Alpha 26's files loaded correctly, but its first human fresh-campaign test
failed the actual requirement: the player could not see the advertised terrain
language in either political or terrain mode. A native audit found that the old
preview amplified contrast, while the compiler measured coverage only against
fixed brightness anchors 18-30. At zoom 2, only 0.495% of the audited India
crop reached DeltaE76 >= 2 in political mode and 0.0401% did so under the exact
terrain-mode palette.

Alpha 27 treats that result as a release failure, not user error. It measures
all ordinary mechanical land, uses exact native colour-scale interpolation and
keeps actual-engine human recognition as a separate mandatory gate.

## Provenance and exact inputs

The output remains an original, local-only AUBM procedural layer. It uses no
Blood and Iron or DEC lightmap, pixel, palette or colour scale.

| Input | Role | SHA-256 |
| --- | --- | --- |
| Darkest Hour `colorscales.csv` | exact political, terrain, Snow and Mud LUTs; read-only | `34ec17047e2719671b2afc6fd2e8e5cfaeb1031fa509ee30e3c8483c8128c828` |
| Darkest Hour `Map colors.txt` | authoritative terrain/weather scale mapping; read-only | `48c57c40fb928703231578185690dfd68fbd86276abc8ca54daf706eb8f30acf` |
| AUBM motif recipe | schema-3 mark placement, density and gates | `3811c33414cb14cd6a468461c50d245ff2e798cf36744d649a3485a3ed86cd61` |
| AUBM compiler | clean-room codec, compiler and native renderer | `b31731ac95534f12ec029fbf901754779997f1b9b8ff6870f52f444a8e20de3c` |
| Native DarkBlue motif atlas | unamplified review fixture | `fe1a408abc3a6529edadb6c95ac875e8f1313222d0eb7195cce2ad421d9f443c` |

MapUtility-compatible LUT expansion was verified from its local IL: it computes
the complete positive channel value as a float and then truncates that final
value. CIEDE2000 is the release metric; DeltaE76 is retained only to compare
with the Alpha 26 audit.

## Deterministic four-zoom output

| Zoom | Darkest Hour source SHA-256 | Alpha 27 output SHA-256 | Output bytes |
| --- | --- | --- | ---: |
| 1 | `96f3f65e4f37ba0c522beb0ed9d10fa5856c2c2ea679dae8bdc2fe976a13e043` | `ea62f1661d9877a4c292a0b76a859331049687f8bfaa4a3feb02d60883e0803b` | 49,900,942 |
| 2 | `39f852e4d547d20b6d5a1a68332125bc77298548433baf5065cf521d685da78c` | `ae2c2a438cdb216038ed35ade29cd9dbde73a13e5bba4865ce40ed902208f678` | 26,523,613 |
| 3 | `f2589a2080c937bcd0dc9c056b8a9ed70abd7faea3338231cb60675da16d339c` | `7f7995cd9784ac87d87f0464cdf787e54da00885ed955af7a33a1168bfdf480e` | 12,538,601 |
| 4 | `f66d41faeb4d6ccd14bcd360140e7f629532f841d759cbe18bb634e2089689e4` | `976ec3b9067811394c8c1004c0491eb93636268fd3d7310ae3cf096dc5497a69` | 3,613,178 |

The four files contain 118,136,844; 29,743,429; 7,266,714; and 1,910,419
ordinary mechanical-land pixels respectively. Modified coverage is 30.902%,
31.002%, 31.025% and 30.974% of those all-land denominators. No fixed
brightness-anchor denominator remains.

## Per-terrain all-land coverage

| Terrain | Zoom 1 | Zoom 2 | Zoom 3 | Zoom 4 | Declared band |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plains | 29.868% | 30.023% | 30.018% | 29.982% | 25-35% |
| Forest | 44.072% | 44.147% | 44.205% | 44.095% | 40-55% |
| Mountain | 25.619% | 25.702% | 25.687% | 25.751% | 20-40% |
| Desert | 17.465% | 17.484% | 17.500% | 17.384% | 12-24% |
| Marsh | 18.286% | 18.310% | 18.279% | 18.358% | 15-30% |
| Hills | 19.551% | 19.628% | 19.586% | 19.585% | 18-35% |
| Jungle | 67.666% | 67.972% | 67.984% | 68.011% | 60-75% |
| Urban | 50.640% | 51.388% | 51.159% | 51.656% | 45-65% |

Hills use stronger but sparser contours than Alpha 26. Their motif RMS is
0.689725 of Mountain at every zoom, below the declared 0.70 limit.

## Native perceptual gates

Political mode uses India's actual `DarkBlue`. Terrain mode uses the official
mapping: Orange/Plains, Green/Forest, Gray/Mountain, Yellow/Desert,
LightGreen/Marsh, DarkOrange/Hills, DarkGreen/Jungle and DarkGray/Urban.
Snow uses White and Mud uses Brown.

| Zoom | Political marked median DE00 | Political all-land DE00 >= 2 | Terrain marked median DE00 | Snow marked median DE00 | Mud marked median DE00 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 4.0755 | 30.882% | 2.8766 | 4.5166 | 3.5897 |
| 2 | 4.0933 | 30.967% | 2.8766 | 4.5166 | 3.6399 |
| 3 | 4.0470 | 31.025% | 2.8300 | 4.9509 | 4.2522 |
| 4 | 4.0453 | 30.974% | 2.8274 | 4.8711 | 4.2970 |

Every terrain passes independently at every zoom:

- Political minimum: marked median DE00 3.0 and 80% of modified pixels at
  DE00 >= 2. Observed weakest median is 3.4578 (Hills, zoom 4); observed weakest
  fraction is 99.57% (Urban, zoom 2).
- Terrain-mode minimum: marked median DE00 2.25 and the same 80% fraction.
  Observed weakest median is 2.3700 (Desert, zoom 1); the weakest fraction is
  again 99.57%.
- Provisional Snow/Mud minimum: marked median DE00 1.5 and 75% of modified
  pixels at DE00 >= 1. The weakest observed Snow fraction is 81.56% (Jungle,
  zoom 4); every Mud fraction is 100%.

The terrain-mode threshold is 2.25 rather than 3.0 because the official Orange,
Yellow and Green scales cannot all reach 3.0 under the reviewed +/-10
shade-index cap without making those classes more forceful than Mountain and
overdriving political mode. The local manifest records both signed cap values
for every terrain scale; this technical limit does not waive human acceptance.

## Geometry, installation and human boundary

The candidate passed canonical parse/write identity, schema-3 source checks,
the Alpha 26 failure-profile regression and all native-colour gates above. A
second independent comparison decoded all 447,525 blocks and every raster
pixel at all four zooms. Province ownership, protected/non-land pixels and
trailers were exact; no gate error was suppressed. The local manifest SHA-256
is `5f0cbf59e722db3f9e5dc6744d48778698ca4f993e10dd6913f53cb766424304`;
the exhaustive comparison record SHA-256 is
`9a59c59f22586602a4e650b1c56c75650abcc886955b301de793806ef88196a9`.

All offline and static release gates are complete. The normal Alpha 27 overlay
has also been deployed and its visible version assets verified. The separate
transactional terrain installer completed successfully: its installed-file
check decoded all 447,525 blocks and the four live lightmaps match the release
hashes below. The game has not been launched after installation.

### Local installation receipt

| Receipt item | Final value |
| --- | --- |
| Transaction result | Installed successfully at `2026-08-31T00:04:17.9217611+05:30`; 447,525 live blocks decoded and verified |
| Backup directory | `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\A Union Before Midnight V4.2\AUBM_ORIGINAL_TERRAIN_BACKUP\20260831-000125` |
| Transaction state record | `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\A Union Before Midnight V4.2\AUBM_ORIGINAL_TERRAIN_BACKUP\20260831-000125\AUBM_ORIGINAL_TERRAIN_TRANSACTION.json` (`status: installed`) |
| Installed-state marker | `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\A Union Before Midnight V4.2\AUBM_ORIGINAL_TERRAIN_VISUALS.json` |
| Colour-scale state | Mod-local `map/Map_1/colorscales.csv` absent; verified Darkest Hour core fallback retained |

| Zoom | Expected Alpha 27 SHA-256 | Installed SHA-256 |
| --- | --- | --- |
| 1 | `ea62f1661d9877a4c292a0b76a859331049687f8bfaa4a3feb02d60883e0803b` | `ea62f1661d9877a4c292a0b76a859331049687f8bfaa4a3feb02d60883e0803b` |
| 2 | `ae2c2a438cdb216038ed35ade29cd9dbde73a13e5bba4865ce40ed902208f678` | `ae2c2a438cdb216038ed35ade29cd9dbde73a13e5bba4865ce40ed902208f678` |
| 3 | `7f7995cd9784ac87d87f0464cdf787e54da00885ed955af7a33a1168bfdf480e` | `7f7995cd9784ac87d87f0464cdf787e54da00885ed955af7a33a1168bfdf480e` |
| 4 | `976ec3b9067811394c8c1004c0491eb93636268fd3d7310ae3cf096dc5497a69` | `976ec3b9067811394c8c1004c0491eb93636268fd3d7310ae3cf096dc5497a69` |

Before any deployment, all 27 save/config files were copied to a new snapshot
and verified byte-for-byte. The final post-transaction comparison proves the
snapshot and live set each contain 27 files and 172,625,181 bytes, with zero
SHA-256 differences. The separate installed personal-sprite profile also
retains all 41 unit families, 591 descriptors, 553 unit BMPs and 44 palettes,
with zero missing files or hash mismatches. The lightmap-only correction is
save-neutral and does not require another new campaign, but Darkest Hour must
be fully exited and cold-started because it loads these files at process start.

Native offline political, terrain, Snow and Mud images are evidence that the
correct LUTs and shade offsets are being measured. They are not engine
screenshots and do not reproduce labels, counters, borders, facilities,
animation or final weather compositing perfectly. Alpha 27 must not be called
human-accepted until the player recognizes the installed terrain language in
political and terrain mode at all four zooms and checks representative weather.
