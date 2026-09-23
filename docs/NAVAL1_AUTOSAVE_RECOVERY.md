# NAVAL1 — June 1941 campaign recovery

Scope: the inspected `AUBM Terrain Prototype P1` autosave dated 1 June 1941.
The source autosave and its configuration are preserved. The recovery is a
separately named save: **NAVAL1_India_1941_June_1_90pct.eug**.

## Continuing this campaign

Restart Darkest Hour with **AUBM Terrain Prototype P1**, load the NAVAL1 save,
and advance the clock. Two catch-up event notices are queued for game hours
one and two. The orders are already in production in this save; acknowledging
the notices does not create ships or charge resources again.

All ten overdue event orders have `total_progress = 0.9000`, one unit per
line, and the single fitting specified by their event. Current unlocked hull
and fitting models are used. Existing orders, deployed forces, commanders,
territory, diplomacy, research, other countries, and existing queued events
are preserved byte for byte outside the specifically documented recovery edits.

| Fleet | Orders | Remaining scheduled funded days |
| --- | --- | --- |
| Bay of Bengal | INS Purvasagar | 36 |
| Bay of Bengal | INS Chilika, INS Coromandel | 15 each |
| Bay of Bengal | 1st and 2nd Bengal Escort Flotillas | 9 each |
| Oceanic | INS Samudra, with CAG | 33 |
| Oceanic | INS Makran, INS Malacca | 21 each |
| Oceanic | 1st and 2nd Ocean Escort Flotillas | 9 each |

The two unclaimed appropriations are accounted for once: **1400 money,
3200 supplies, and 14.05 manpower** for the ten current-model crews/fittings.
The June 1937 carrier design authorization and September 1937 Arabian fleet
are not charged again. Their existing ships are not duplicated.

The original event-requested first-item schedules are used as the recovery
lines' duration. Initial daily IC costs use the published current hull plus
single fitting cost, including saved technology cost adjustments. This save
repair does **not** emulate the engine's minister/slider price calculations.
Native recalculation and actual completion dates have not been verified in
Darkest Hour. The orders need production funding; prioritise them in the queue
if existing orders consume the available IC. Static 90% progress is verified.

The subsequent Oceanic commissioning review is eligible because the credited
297 of 330 construction days exceed its 210-day review threshold. It remains
a separate decision, with its existing effects and affordability guards.

## General naval progression fix

The installed autosave has paid/completed flags for the Arabian fleet, but no
entry for its event in the save's `save_date` table. The next event requires
that missing entry. Its paid-contract flag also disables its legacy calendar
fallback. This is the confirmed deadlock. The exact engine reason for omitting
the persistent decision's timestamp has not been reproduced in-engine.

NAVAL1 replaces all five naval elapsed-event dependencies with delayed
callbacks. The engine stores these in `globaldata.queued_events`, a mechanism
already observed surviving reload in the source save. Paying an appropriation
arms a callback once. Cancel does not arm or reset it. At expiry, the callback
sets a readiness flag; the next decision retains its resource, doctrine,
ownership and already-completed guards. Existing contracts without a new clock
use their established calendar fallback.

The preserved intervals are:

- Arabian → Bengal: 225 days.
- Bengal → Oceanic keels: 225 days.
- Oceanic keels → commissioning: 210/170/210 days for the three doctrines.
- Naval Board → modernisation: 60 days.
- Himalaya → sister-ship programme: 265 days.

The carrier authorization description now explicitly explains that it funds
design/training and does not itself order a carrier. Its cost is unchanged.

The future-build compiler applies the fix as its final overlay. Only the two
naval event modules are replaced in the installed mod. No broad redeployment
of the existing, modified source tree is performed. The installation manifest
and backup paths are recorded in `build/naval1/manifest.json` and installed
`NAVAL1.json`.

## Other findings; not changed by NAVAL1

1. **Fourteen other campaign clock sources are persistent events referenced
   by elapsed-event checks.** They cover Chinese-city, Soviet-frontier,
   Japanese-city, Himalayan, western-corridor, Indochinese and Siamese
   consolidation, plus seven protectorate reviews. They use the same fragile
   pattern, but are not all currently earned or proven stalled in this save.
   Their exact source/target IDs are in the manifest. A separate lifecycle
   repair must preserve cancellation, loss of control and clock-reset rules.
2. **Strategic Council / European partner flag mismatch.** Council changes
   leave the legacy European-program flag set. The old partner offer can
   remain available and overwrite the new posture while leaving conflicting
   older orientation flags. Current European direction is preserved here.
3. **Decision clutter.** Diplomacy and Campaigns is a permanent navigation
   hub. The European partner offer is a negotiation. The Council changes
   posture. Respond to Japanese Aggression is an optional independent war
   response, including after the witnessed aggression has ended. They are
   not four obligations to complete.
4. **Portrait repetition (corrected audit).** All 512 roster references resolve
   when both mod overrides and base-game fallback assets are checked: zero
   missing references, 176 distinct bitmap hashes before CONTINUE1. The earlier
   claim that 94 entries shared identical bytes incorrectly grouped assets
   absent from the mod directory; those assets exist in the base game.
   The actual repetition is 375 reserves reusing 48 portraits, with visually
   similar naval faces, plus nine historical entries explicitly using the
   unknown-leader image. No portrait/leader changes are included in NAVAL1.

CONTINUE1 subsequently repairs findings 1 and 2, clarifies the navigation hub,
and expands the reserve portrait pool. See `CONTINUE1_CAMPAIGN_RECOVERY.md`.

## Validation

Regression tests cover missing-date legacy recovery, delayed readiness after
reload, cancellation, programme-specific intervals, completion/resource
guards, callback format, collision rejection, exact 90% progress, resource
accounting, unchanged existing production/world state and refusal to apply
the recovery twice. Build integration checks include all registered event IDs
and presentation limits. Native engine execution is not claimed.
