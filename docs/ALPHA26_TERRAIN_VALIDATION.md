# Alpha 26 terrain validation record

Version: `4.2.0-alpha.26`
Date: 30 Aug 2026
Scope: original AUBM all-terrain political-map source and local compilation

## Provenance result

The finished terrain surface uses **no Blood and Iron or DEC Map pixel**.

- Geometry, source leaf ownership and base 6-bit brightness come from the
  player's legally installed Darkest Hour Full map.
- Terrain identity comes from AUBM's current `mod/map/Map_1/Province.csv`.
- Mark placement and contrast come from the original deterministic recipes in
  `assets/v4_terrain/aubm_terrain_motifs.json`.
- Darkest Hour's normal core `colorscales.csv` is used by fallback. No mod-local
  donor or AUBM replacement colour scale remains active.
- The compiled `.tbl` files are generated locally and are excluded from GitHub
  and public installer manifests.

The former Blood and Iron reference was used only for comparative measurement.
Its two lightmaps and colour scale are forbidden output hashes. It performed
well for Mountain and Desert but did not reliably separate the other six
terrain classes, so none of it was retained in Alpha 26's terrain runtime.

## Exact source and output hashes

| Zoom | Darkest Hour source SHA-256 | Deterministic local output SHA-256 |
| --- | --- | --- |
| 1 | `96f3f65e4f37ba0c522beb0ed9d10fa5856c2c2ea679dae8bdc2fe976a13e043` | `05c3c1acf987b347cce147a99b43d4f150296d9cf661ca3f3760009d1ad640ad` |
| 2 | `39f852e4d547d20b6d5a1a68332125bc77298548433baf5065cf521d685da78c` | `f25f85a4049d4092a924967d48ba60820f516830db6464a180f6cf5cdab2fe29` |
| 3 | `f2589a2080c937bcd0dc9c056b8a9ed70abd7faea3338231cb60675da16d339c` | `2b534f58114603e6c0d2634f4bf6b1213bb781621f2064cc4220a25b26071107` |
| 4 | `f66d41faeb4d6ccd14bcd360140e7f629532f841d759cbe18bb634e2089689e4` | `99cdd1a6724b2e574459139081aca3681bbc073c32634701ea50e00aeb443be8` |

Three independent full compiles produced those same four output hashes. The
generator hash was
`188497c1cc9e53017cd1903d9f4ba4052722206f70aab547cb54fa7a53e4fc4a`;
the motif-recipe hash was
`886378c6423b0f164bb2c193eaea2aef8a7f11aa190355fc9a85a41c115990be`.

## Geometry and protection proof

The canonical codec parsed and rewrote all **447,525** source blocks across the
four zooms byte-for-byte. A separate zero-motif refinement build then passed an
exhaustive raw-raster comparison:

| Zoom | Eligible land pixels compared | Ownership | Brightness changes |
| --- | ---: | --- | ---: |
| 1 | 114,752,179 | identical | 0 |
| 2 | 28,754,372 | identical | 0 |
| 3 | 3,861,615 | identical | 0 |
| 4 | 937,236 | identical | 0 |

The real motif build changed only approved terrain-anchor brightness pixels:

| Zoom | Changed pixels | Share of eligible pixels | Ownership / protected pixels / trailer |
| --- | ---: | ---: | --- |
| 1 | 36,296,765 | 31.631% | exact |
| 2 | 9,093,343 | 31.624% | exact |
| 3 | 1,196,833 | 30.993% | exact |
| 4 | 286,904 | 30.612% | exact |

All eight terrain classes are non-empty at every zoom. Actual compiled coverage
remained inside each class's declared band:

| Terrain | Zoom 1 | Zoom 2 | Zoom 3 | Zoom 4 | Allowed band |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plains | 30.000% | 30.022% | 30.103% | 29.903% | 25-35% |
| Forest | 44.158% | 44.146% | 44.166% | 44.635% | 40-55% |
| Mountain | 25.711% | 25.707% | 25.719% | 25.776% | 20-40% |
| Desert | 17.487% | 17.489% | 17.567% | 17.211% | 12-24% |
| Marsh | 18.321% | 18.310% | 18.273% | 18.276% | 15-30% |
| Hills | 26.165% | 26.157% | 26.055% | 25.755% | 20-40% |
| Jungle | 68.000% | 67.997% | 67.863% | 67.833% | 60-75% |
| Urban | 51.502% | 51.374% | 51.448% | 51.788% | 45-65% |

## Release and visual boundary

The public Alpha 26 release passed a repeat-stable 4,436-file build, a 344-file
donor-safe installer manifest, the visible-version gate and all gameplay, art,
economy, combat, construction and platform audits with 0 errors and 0 warnings.
The public base install preserved all 27 existing save files byte-for-byte.

The local terrain transaction also completed. All four installed lightmaps
match the deterministic hashes above; a post-install decoder traversed all
447,525 blocks; core `colorscales.csv` fallback is active; and no forbidden
Blood and Iron/DEC hash remains live. The separately restored personal India
sprite profile still reports 41 independent families, 591 descriptors and 553
unique animated strips. A final save comparison found 27 of 27 files present,
no extras and no byte changes (172,625,181 bytes on both sides).

The installed Alpha 26 executable reached the main menu at native 1024x768
fullscreen and visibly displayed `AUBM BUILD 4.2.0-ALPHA.26`. Two windowed
attempts stopped before mod loading at the host's legacy DirectDraw video-mode
initialization, and detailed debug mode displayed 444 missing-translation
warnings for non-English language columns. Fullscreen initialization succeeded;
neither observation is a lightmap parse failure. The fresh-1933 campaign part
of the smoke was intentionally cancelled while the player used the machine,
so this record makes no fresh-map runtime claim and does not misclassify the
manual exits as crashes.

The neutral atlas and local India diagnostic crop were reviewed for motif
identity, block seams, labels and borders. That is not equivalent to human
in-engine acceptance. A cold fresh-1933 launch can prove that the engine loads
the files without a map error; the player's new campaign must still judge
long-session readability, weather overlap and whether every class is fun rather
than merely measurable. The complete human matrix is in
`docs/VISUAL_READABILITY_PIPELINE.md`.
