# A Union Before Midnight V4.2 Alpha 6

## Stability And Sustainment

- Replaced the live India service-sprite override with Darkest Hour's proven
  country-neutral fallback renderer. Repeated crash dumps failed inside the
  executable's DirectDraw surface path rather than event execution. India
  counters, terrain, map artwork, portraits, flags and event art remain.
- Archived the experimental India sprite sources and manifests for later
  in-engine work without shipping 2,255 descriptors, 2,997 sprite sheets or
  their imported palettes in a campaign build.
- Converted all 131 event production orders into single current-model
  contracts. Sixty-five hidden serials of two to five units are gone; every
  authorized unit now receives the displayed funded progress and normal daily
  IC cost.
- Recalculated 89 action and event manpower gates from the new contracts, so
  choices no longer require manpower for nonexistent later serial items.
- Raised the All-India Revenue Service from +1 to +2 money per day. Together
  with the annual budget, the conservative stress path remains solvent through
  1945 after 1,300 money of discretionary spending every year.
- Raised the annual trained-reserve base from 60 to 85 manpower. A lean
  1934-39 policy now supplies 660 manpower and a typical policy supplies 840,
  before natural growth or wartime call-ups.
- Removed the obsolete save-reconciliation event from clean-game logic. It
  could otherwise fire during a new campaign and correct only the first class.
- Clarified in the mechanization event and operational guide that cavalry and
  other cross-type refits must be fully reinforced before the Upgrades budget
  can advance them. Zero upgrade allocation still grants no free progress.
- Made the Steam Deck controller profile a managed, backed-up install. Alpha 6
  now replaces an obsolete Darkest Hour autosave instead of silently preserving
  it, while retaining timestamped rollback copies.
- Replaced the redundant right-stick mouse with a vertical mouse region fixed
  over the event-action strip. Up/down traverses the choices, stick-click selects
  the hovered action, and `X` sends Enter. The right trackpad remains the
  unrestricted precision cursor.
- Replaced the unrelated stock Darkest Hour loading artwork with dedicated AUBM
  key art for the 1933 Indian union, its federal settlement and its military,
  industrial, naval and aviation ambitions.
- Replaced generic loading quotations with a compact set of explicitly
  in-universe cabinet, planning, naval and strategic memoranda.

## New Release Gates

- Stable-rendering validation requires zero custom live service-sprite
  descriptors, bitmaps or palettes and verifies the stock renderer is present.
- Event procurement validation rejects every serial value other than one.
- A sustained 1934-45 money and manpower simulation now supplements the
  opening-economy check.
- The full build remains idempotent, regenerates exact installer hashes and
  deploys only after all static, art, campaign, combat and construction gates
  pass.

## Campaign Compatibility

Alpha 6 is a clean-campaign release. Existing autosaves are not modified or
repaired. A new 1933 start is required to receive the revised annual revenue,
reserve classes, procurement contracts and rendering profile consistently.
