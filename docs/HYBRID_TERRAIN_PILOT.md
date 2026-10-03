# Hybrid terrain pilot — 5 September 2026

Historical regional-pilot record. On 6 September (India time), the same isolated
test installation was upgraded to **HYBRID-WORLD1**, with worldwide coverage and
a donor-lettering correction. See [the current world build](HYBRID_TERRAIN_WORLD.md)
for its installed state and autosave recommendation. The account below describes
the earlier pilot and its limited engine test, not a test of the world revision.

Status: **implemented bounded prototype; not a new alpha or approved release.**

## What exists

- A separate installed test mod: `Mods/AUBM Terrain Prototype P1`.
- Current on-disk loading/menu badge: `HYBRID-P1-GRAY`.
- All four compiled lightmaps. The prototype modifies the L1 rectangle
  x=20200, y=3904, width=2944, height=2240 (north/central India and Bengal/Burma).
  Outside that rectangle the maps retain clean Darkest Hour core shading.
- Mountain, desert and forest reference artwork sampled from the player's
  installed Blood and Iron/DEC L1/L2 maps, only at matching province pixels.
  L3/L4 use owner-matched reductions of L2, not nonexistent donor L3/L4 files.
- New hills, jungle, marsh and urban artwork from an original generated raster
  atlas; its actual pixels, not symbolic replacement patterns, feed compilation.
- Quiet core plains; protected non-land and dark label pixels; feathering around
  lettering; native political, terrain, snow and mud offline previews.
- India uses the core `Gray` assignment, matching Germany's named colour in
  vanilla and B&I. Other countries' assignments and colour scales are unchanged.
  Afghanistan retains LightGray, Tibet White and Persia DarkGray.
- The test mod's airfield and harbour strips are exact copies of Darkest Hour
  Full's vanilla files, with their grey/blue frames and original dimensions.

The old atlas-to-shade draft made jungle too dark. It was rejected offline and
revised before the game launch. No claims of superior B&I-wide recognition are
made from those previews.

## Verification actually performed

- Five synthetic tests pass: uniform/mixed-owner encoding round trips, native
  shade range, repeatability, crop-independent placement and live-output refusal.
- 3,950 / 1,080 / 320 / 95 changed blocks at L1/L2/L3/L4 were re-decoded after
  encoding. Province lists, pixel ownership and expected shading matched.
- The four written files were reopened and the entire prototype crop compared
  against its input raster; geometry and shading round trips pass.
- Staged lightmap hashes match `tmp/hybrid-pilot-v2/compiled/HYBRID_PROTOTYPE.json`.
- Staged mechanical Province.csv matches the maintained project file.
- An actual cold launch reached the `HYBRID-P1` menu, then loaded a separate
  copy of the user's June 1, 1934 autosave. The game window named the prototype.
  The closest political view visibly showed donor relief/dunes, new hills,
  Delhi's built surface and Bengal/Burma canopy. This was the **indigo revision**.
- The first launcher-based attempt failed with an early missing-excel dialog;
  starting the existing executable from its game folder succeeded. This suggests
  launch-context failure, not a demonstrated lightmap failure.

The briefing's Start button allowed the disposable simulation to advance to
09:00 before the pause attempt. User input/minimization interrupted that attempt;
pause was not confirmed. The user then explicitly requested no more computer
control. No further UI input or captures were made. No save command was issued.
The original and staged on-disk autosave still had identical SHA-256
`f5341755cce047bbeb2d2ddac990dd05c952a226db14196bba8863525e4611fc`
when checked after the colour/icon changes.

**Pending:** in-engine checks of the grey/icon revision, all four zooms, terrain
mode, representative weather and independent recognition. Offline snow/mud
renders are not proof of the engine's final weather compositing. The first
engine view is not a blind human recognition test.

## User boundary and installation state

The normal `A Union Before Midnight V4.2` mod, its four Alpha 27 lightmaps,
sprites and original saves were not edited. Only the separate prototype was
changed. No release number was bumped and nothing was committed or pushed.

The grey/icon changes were made after the running prototype had loaded its
assets. They therefore require a later full game exit/restart and explicit
selection of `AUBM Terrain Prototype P1`. Do not claim that the already-open
indigo process reflects the current on-disk grey revision.

`Gray` is the staged default because it avoids an exact nearby colour match.
An additional LightGray preview is available, but was not installed: that
assignment would match Afghanistan and needs a separate regional-colour choice.

## Reproduction and evidence

Use Python with NumPy and Pillow (the bundled workspace Python has both).

```
python tools/aubm_hybrid_terrain.py preview --output tmp/hybrid-pilot-review
python tools/aubm_hybrid_terrain.py compile --previews tmp/hybrid-pilot-review --output tmp/hybrid-pilot-review/compiled
python tools/test_aubm_hybrid_terrain.py
```

Generation prompt: `assets/v4_terrain/hybrid/generation.json`.
Runtime original atlas: `assets/v4_terrain/hybrid/terrain-atlas-v1.png`.
Reviewed indigo candidate and encoded rasters: `tmp/hybrid-pilot-v2/`.
Native grey previews: `tmp/hybrid-pilot-gray/`.
Lighter alternative, preview only: `tmp/hybrid-pilot-silver/`.
Pre-test launcher configuration and replaced test icons: `tmp/hybrid-runtime-backup/`.

Next step is a brief visual acceptance check, not another campaign playthrough.
Only after that should the artwork be expanded beyond the pilot region and
packaged as a replaceable local profile. Keep donor-derived output local.
