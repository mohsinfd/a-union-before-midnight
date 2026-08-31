# A Union Before Midnight 4.2.0-alpha.9

## Honest Arsenal Accounting

- Removed the January modernization event's broad land, air and naval
  build-time and build-cost commands. Darkest Hour applies those commands to
  newly constructed units as well as upgrades; they had reduced a 1933 Indian
  battleship to roughly 400 days.
- Restored Darkest Hour's dedicated paid-upgrade factors: 50% normal cost and
  50% normal time. Cross-type land and naval conversion factors continue to
  apply, so practical modernization remains substantially faster than new
  construction.
- Kept both sources of unfunded upgrade progress disabled. A zero Upgrades
  allocation still means zero progress.
- Added a one-time legacy-save accounting correction that reverses every known
  Alpha 7/8 modifier combination before normalizing its compatibility flags.
  Existing production-queue contracts may retain their original completion
  terms; a new campaign remains the clean balance test.
- Added a static regression gate that rejects broad negative land, air or
  naval unit-build modifiers in the India event layer.

## Playtest Requirement

Start a new 1933 campaign. Expected new-hull times should again be measured in
years for capital ships, while funded conversions use the normal upgrade
budget and the dedicated Darkest Hour factors.
