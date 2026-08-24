# A Union Before Midnight 4.2.0-alpha.10

> Superseded by Alpha 11. A runtime screenshot established that Alpha 10
> targeted the large `ill_div` illustration and an unindexed text table, while
> the visible defects were the 67x44 model icon and active unit-name table.

## Special-Unit Presentation Repair

- Published all 40 special-unit name and description strings into Darkest
  Hour's indexed `extra_text.csv` table. Reserved formations no longer expose
  raw `AUBM_SNAME_*`, `AUBM_SDESC_*` or `MODEL_*` keys in game.
- Replaced the invalid alphabetic reserved sprite keys with the engine's
  numeric continuation: division IDs 33-40 now use sprite families
  `d_74`-`d_81`. The Gurkha formation should render as an animated unit rather
  than falling back to the yellow NATO counter.
- Added valid 192x104, uncompressed 24-bit model-panel illustrations for all
  eight AUBM special formations, under both India-specific and generic lookup
  names. The yellow missing-art X is no longer an accepted fallback.
- Moved the Dehradun Gurkha Brigade's control gate and deployment location from
  Delhi (1459) to Dehradun (1451).
- Extended the build gates to verify loaded localization, exact model-art
  dimensions and format, numeric sprite sequencing, complete animated sprite
  families and installer inclusion.

## Compatibility

An existing save containing the Gurkha formation can verify the corrected
name, description, illustration and map sprite after reload. Start a new 1933
campaign only to verify that the commissioning event now places the formation
in Dehradun.
