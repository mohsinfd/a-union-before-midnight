# India colour selection

User selected **pale jade**, proposed base swatch **#A9CDB6**, on 10 September 2026.

Status: **implemented as the PALE-JADE-1 local visual override**. Native in-game
appearance still requires the user's restart check.

Implementation requirements:

- Change India's political colour only; preserve neighbouring country colours.
- The dedicated ramp begins at the selected `#A9CDB6` swatch, then darkens to
  `#90B39D` and `#749682`. This moves ordinary provinces toward the earlier
  selected-province appearance while retaining relief and a darker click state.
- India uses the country-only `UserColor2` slot. Its previous users are moved to
  the nearest native `LightBlue` country ramp, so none of India's neighbours
  share pale jade and no terrain colour slot is changed.
- Compare normal and selected provinces at multiple zooms in an isolated test.
  The requested selected-like default appearance remains unverified.
- Keep terrain geometry, classifications, facilities, sprites and gameplay
  unchanged. Do not include donor-derived map assets in a public release.
