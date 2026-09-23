# Hybrid pilot: original runtime terrain atlas

`terrain-atlas-v1.png` was generated with the built-in image-generation tool on
5 September 2026. The complete prompt and method are in `generation.json`.
There were no donor/reference-image inputs to this generation.

Unlike the earlier concept board, **these pixels are consumed by the compiler**:
top-left hills, top-right jungle, bottom-left marsh, bottom-right urban. The
compiler reduces each quadrant to zoom-specific sizes and quantizes luminance
into Darkest Hour's native six-bit shading values. It does not install this PNG
as a flat map background or invent terrain-specific political colours.

The original image and source code are separate from locally reconstructed
Blood and Iron/DEC terrain. All donor-derived previews and compiled lightmaps
remain in ignored `tmp/` folders or the player's isolated test installation.
They must not enter the public mod folder, GitHub or release packages.

This same atlas now feeds the installed local **HYBRID-WORLD1** test at all four
zooms worldwide. It is not a public or human-accepted release. See
`docs/HYBRID_TERRAIN_WORLD.md` for current verification and save guidance, and
`docs/HYBRID_TERRAIN_PILOT.md` for the historical regional engine test.
