# Fictional reserve officer portraits

`reserve-officers-atlas.png` was generated with the built-in image-generation
tool for this patch. These are fictional faces for fictional academy reserves,
not archival photographs or identities of named historical commanders.

Prompt specification: one monochrome atlas of 48 distinct fictional Indian
male military officers from the 1930s and 1940s, in an exact eight-column by
six-row grid without gutters, text or watermarks; period studio head-and-shoulder
portraits, varied ages and facial features, appropriate army, naval and air-force
uniforms, including Sikh and non-Sikh officers; army in the top three rows,
naval officers across the fourth row and the beginning of the fifth, air officers
in the remaining cells. Keep hats, faces and uniform details readable at tiny
strategy-game portrait sizes. No modern uniforms and no named real people.

The atlas is packaged by `tools/aubm_reserve_portraits.py` into 48 RGB BMPs at
36x50 pixels. The 375 reserve IDs 252000–252374 reuse that pool by service. This
is more varied than one anonymous image, not 375 individually unique portraits.
Historical roster rows and their images are preserved. The atlas has been
visually checked as a native-size contact sheet; in-game appearance is untested.

Outputs: `build/cleanup1/mod/gfx/interface/pics/aubm_reserve_01.bmp` through
`aubm_reserve_48.bmp`; contact sheet `build/cleanup1/reserve-portraits-preview.png`.
