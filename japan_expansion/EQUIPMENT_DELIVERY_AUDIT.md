# R11.1 equipment and delivery cold audit

The final source explicitly restores each freshly issued formation to its existing allowed maximum strength. This follows the native named damage_division command contract; it is not inferred from a simulator division count. No global army strength, organisation, cap, equipment-stat or brigade bonus is applied.

## Native evidence

- Engine event commands.txt lines 227–234 documents land/air/naval add_corps, subsequent add_division placement, negative where damaged-unit creation, and named negative-damage strength gain clamped at Max Strength.
- The same native document lines 695–722 distinguishes changing current unit strength from strength_cap values that may apply to future units. Lines 550 documents current-size building checks with when=now.
- Read both actual 1933 event registries and their event files. Native 33/66% demobilisation commands affect existing land units at execution; they do not establish a permanent 33% new-unit template. The only loaded strength caps found are Italian infantry at 70 and British/American custom d_05/d_06 at 40. None targets Japanese awards or ordinary American infantry.
- The clean model templates contain normal organisation/morale and equipment metadata; none of these award models imposes a 33% strength cap. Native add_corps/add_division examples, including Op Zet aircraft and Empire Transports, support the placement syntax. New named restoration makes the intended strength explicit instead of relying solely on default creation behaviour.

## Delivered source corrections

- Four Japanese aircraft/ship alternatives now require a current level-one airfield/naval base both at payment and receipt, with the same predicate included in the exact-refund complement.
- All 14 potential Japanese awards use realistic distinct formation names and one scoped restoration per created unit. Each of seven American staging alternatives retains its two exclusive researched model paths, with an identically conditioned scoped restoration.
- Western Reserve and Central Reserve names distinguish the two American waves. Kansas City can host both without a second-wave restoration healing wounded first-wave formations.
- American reserves now choose among five researched and dated models. Manpower bills, supply/money/resource bills, elapsed times, branch markers, receipts, ownership/control predicates and maximum actual American reserve count (12) remain unchanged. Existing intentionally quarter-strength island detachments remain unchanged.

## Japanese model / crew / deployment verification

| Formation | Type / model | Research | Manpower | Deployment |
| --- | --- | --- | --- | --- |
| Shanghai Port Defence Division | garrison / 4 | 1090 | 10 | 1338 |
| Wusong Defence Division | garrison / 4 | 1090 | 10 | 1338 |
| Shanghai Expeditionary Infantry | infantry / 9 | 1100 | 13 | 1338 |
| Wuhan Mountain Division | bergsjaeger / 9 | 1250 | 13 | 1317 |
| Yangtze Mountain Division | bergsjaeger / 9 | 1250 | 13 | 1317 |
| Manila Fighter Wing | interceptor / 8 | 4030 | 0.75 | 1565 |
| Luzon Fighter Wing | interceptor / 8 | 4030 | 0.75 | 1565 |
| Manila Naval Air Wing | naval_bomber / 2 | 4190 | 2.2 | 1565 |
| Luzon Naval Air Wing | naval_bomber / 2 | 4190 | 2.2 | 1565 |
| Philippine Expeditionary Division | infantry / 9 | 1100 | 13 | 1552 |
| Luzon Expeditionary Division | infantry / 9 | 1100 | 13 | 1552 |
| Soerabaja Escort Flotilla | destroyer / 6 | 3070 | 1.25 | 1653 |
| Java Escort Flotilla | destroyer / 6 | 3070 | 1.25 | 1653 |
| Soerabaja Patrol Cruiser | light_cruiser / 5 | 3160 | 0.75 | 1653 |

## Checks and installation parity

- Native engine docs establish named negative-damage strength gain, clamp-to-cap semantics, damaged-unit where values and current-size building predicates.
- Both actual 1933 loaded-event sets scanned for strength caps and 33/66% changes; no Japanese new-award class strength cap exists.
- All 14 Japanese and 42 potential American names are distinct, absent from clean scenario/unit lists/events, and occur only in their own final award/model alternatives; no event-ID names.
- Every Japanese birth has a valid researched native model, complete model manpower, explicit controlled site, unmodified brigade field and one matching post-creation heal; no extra recruitment charge or organisation boost.
- All seven USA staging options preserve exact technology conditions on both birth and heal, 78 manpower/2400-supply cost and American-owned/controlled hubs; only six researched divisions can form per wave.
- Eight Japanese state fixtures prove named 33%-strength births restore to 100, exact manpower is spent once, placement is correct and replay is inert; all four air/naval facility failures block funding or refund completely.
- Thirty-five USA hub/model fixtures create six full-strength researched divisions each; both Kansas City waves coexist with distinct names, and the second wave leaves wounded first-wave units unchanged.
- All R11 regional, prewar and American event blocks exactly match the installed final compiler output.

**Installed matches final source: True.**

Organisation is deliberately not filled by a scripted bonus. Normal deployment/reorganisation and maintenance still apply. The strength guarantee is the documented command intent up to the existing cap, not an engine observation. The hook changes no global strength or mobilisation rule.

Integration: import equipment_delivery and call apply() after final_event_integrity and all R11 appenders, before player-copy/localisation generation and the final ID refresh. The hook adds no event IDs. After the parent rebuild, run equipment_delivery_review.py --require-installed; it rejects any remaining source/install mismatch.

## Limits

- Documented-command arithmetic and state fixtures do not execute the game engine.
- Named restoration clamps to an existing cap; it never changes that cap or organisation.
- Later native demobilisation, combat, attrition or unsupplied operation can reduce the newly delivered forces.
- The 31 intentionally quarter-strength legacy island garrisons remain unchanged.
- Final deployment UI, engine rounding, organisation defaults and mobilisation timing still require a game playtest.

This audit did not launch the game, change saves, edit German files or install a mod. Full command records, cap findings and parity exceptions are in EQUIPMENT_DELIVERY_REVIEW.json.
