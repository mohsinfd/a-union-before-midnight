# CONTINUE1 campaign continuation

Load **CONTINUE1 - India June 1941 - overdue fleets 90 percent** in the
installed **AUBM Terrain Prototype P1** mod. Its filename is
`CONTINUE1_India_1941_June_1_90pct.eug`. Restart the game before loading so the
updated event definitions and portraits are read.

The new save continues NAVAL1. Its ten recovered Bay of Bengal and Oceanic
orders remain at exactly **0.9000** progress, including INS Samudra. Every
production entry, resource balance, province, war, treaty, flag and queued
event is byte-identical to NAVAL1. Only the save title, configuration filename
and existing fictional reserve officers' picture fields change. The NAVAL1
catch-up notices remain queued for the first one and two game hours after
unpausing. The previous autosave and NAVAL1 save are preserved.

## Timers in this save and new campaigns

NAVAL1 already replaced five naval elapsed-event dependencies with saved,
delayed callbacks. CONTINUE1 fixes the remaining fourteen persistent campaign
clock sources using integer flags and saved daily callbacks:

| Campaign clock | Required days |
| --- | ---: |
| Four-city China hold | 60 |
| Soviet frontier hold | 90 |
| Japanese-city hold | 60 |
| Himalayan consolidation | 90 |
| Western corridor | 90 |
| Indochinese consolidation | 30 |
| Siamese consolidation | 21 |
| Seven protectorate constitutional reviews | 730 each |

Counters advance only through one pending daily callback per clock. The first
seven retain the original continuous campaign conditions; losing them
invalidates partial progress. Restarting while an older callback is pending
discards that partial day, preventing premature completion or multiplied
callbacks. This can add up to one day after a restart. Protectorate clocks
measure age; their final decisions retain existing peace and sovereignty
requirements. Timers never grant territory, sign peace or release countries.

None of these fourteen watches is active in the inspected June 1941 save.
There is no elapsed campaign time to seed for them. Other older saves with
active watches and no recoverable counter conservatively start counting from
zero; existing new counters are preserved. This avoids inventing earned
campaign completion from missing timestamps. The 90% exception applies to
the ten specifically recovered naval orders.

## Diplomacy decisions

Council choices now synchronize both the legacy programme flags and the newer
strategy flags. Choosing non-alignment, a Soviet posture or an Asian strategy
closes a stale European partner offer. Independent Asian cooperation retains
its deliberately combined independent-Asia and non-alignment flags.

European partner choices preserve their existing money/supply costs and
negotiation outcomes. New guards prevent an offer from overriding another
posture, binding treaty, pending negotiation or realignment cooldown. Choosing
London or Berlin clears rival legacy orientation flags. The current European
direction in this save is preserved; no partner is selected automatically.

The four visible entries are not four required outstanding decisions:

- **Diplomacy and Campaigns** is a permanent navigation menu; its description
  now states this explicitly.
- **Choose a European Partner** opens a negotiation.
- The **Strategic Council** changes strategic posture.
- **Respond to Japanese Aggression** is an optional war response. Its costs,
  effects and availability rules are unchanged by CONTINUE1.

## Commander portraits

Sixteen new fictional portraits expand the reserve pool from 48 to 64:
eight navy, four army and four air-force faces. They are interleaved through
the existing 375-officer reserve. Historical identities, traits, skills,
ranks and service dates are unchanged. Base-game portrait inheritance works;
the previously reported group of 94 missing/identical images was an audit
error, corrected in the NAVAL1 report.

The built-in image-generation tool produced
`assets/continue1/reserve-officers-atlas.png`. The full final prompt is in
`assets/continue1/generation-prompt.txt`. Mechanical packing creates sixteen
36 x 50, 24-bit BMP files in `mod/gfx/interface/pics`. A magnified contact sheet
is saved to `build/continue1/portraits-preview.png`.

## Installation and validation

The installer changes four installed event modules, the Indian leader roster
and sixteen new bitmap files, and adds the separately named continuation
save/configuration. Source roster and bitmap files are updated; the future
event compiler applies both CONTINUE1 overlays at its end. Existing NAVAL1
naval modules remain installed.

`tools/install_continue1_recovery.py` prepares and validates the package.
Adding `--install` applies it with preflight hashes, explicit backups and
rollback on a write failure. It refuses changed/played inputs or an existing
CONTINUE1 recovery to prevent accidental reapplication. The installed
`CONTINUE1.json` and `build/continue1/manifest.json` record exact file hashes,
clock IDs and the backup directory.

Validation includes twelve protocol/diplomacy/portrait tests, the build and
NAVAL1 regression suite, installed-overlay parsing, unique event IDs,
callback format, idempotence and an inverse-edit proof that the continuation
changes no bytes outside picture/header fields. Counter simulations cover
both pre-evaluated and sequential command guards, save/reload without event
timestamps, cancellation, control loss, restart and completion.

These are static checks and simulations, **not a native Darkest Hour play
test**. The game must still confirm silent daily callbacks and queue progress
in play. NAVAL1's saved initial ship IC costs use the published hull/fitting
and technology costs; minister/slider recalculation was not emulated. The
original requested schedules imply 9–36 funded days remaining.
