# R13 Japanese unique divisions - native contract audit

All seven specialist classes and 29 model stages are covered. The table below records the three original families; R13_UNITS.md gives the four additional families, full costs, tradeoffs, research and free issues.

Three full-size native-family classes replace neither the regular army nor the retired d_10–d_12. Normal production, crews, research, operating costs and allowed attachments remain necessary. Initial free introductions are owned by unique_unit_events.

| Class | First model | Useful advantage | Cost / tradeoff |
| --- | --- | --- | --- |
| Akizuki AA Escort | 1942, DD research 12000 | AA attack 9 vs 6, full 1.5 manpower crew | Sea attack 5.6 vs 7; IC 1.495 vs 1.3, time 598 vs 570 |
| H6K / H8K Flying Boat | 1938 H6K, then year-gated 1942 H8K | Range 2,125 vs 1,250 km, surface detection 3 vs 1, full 2.2 manpower wing | Naval strike 3 vs 4; IC 17.25 vs 15, time 264 vs 240 |
| Teishin Airborne | 1942, Para research 1680 | Full native firepower and 9 manpower; organisation 43 vs 35, morale 48 vs 40, supply -10% | IC 11.5 vs 10, time 451 vs 410; native transports and airborne rules still apply |

Akizuki may use the Type 93 fitting added by the attachment installer, competing for the normal slot. Flying-boat range never regresses at the native 1945 transition; later variants retain native equipment tradeoffs. Postwar aircraft and the 1955 AA model are campaign continuations rather than claims about a historical Japanese production programme. Teishin is a full division-sized game formation, not a cheaper understrength subdivision.

## Research, programmes and ministers

Each concrete research application has a private per-class receipt. Past research catches up once at activation; research after activation applies once through the same ledger. Native group bonuses already cover the real land/air/naval family and are never duplicated. Native relative production modifiers are converted to fixed amounts from the original base class model zero: modern custom model zero must not increase an old assembly-line discount.

New model zero stays implicit. Model unlocks require both their advertised year and native research; automatic once-per-model resolvers catch research completed before the year. Lower out-of-order callbacks cannot revive an older model. The 1955 AA model remains in data/tech hooks but has no post-1950 campaign resolver.

Concrete Japanese programme awards are mirrored while classes are registered but still locked for production. Activation does not replay programme awards. This makes completing aircraft factories in 1934 and activating flying boats in 1938 equivalent to activating first and completing the programme later. Fresh R12 campaigns are the supported baseline; no old-save branch is guessed from a generic DONE flag.

The installer also preserves the four stock Japanese DD/NAV effects in Mods.txt. Applicable Japanese minister effects, including cost/time penalties, receive concrete aliases; group effects stay single. The attachment module separately handles brigade effects and later Type 93 compatibility.

## Registry, artwork and integration

Run unique_divisions.apply() after the older catalogue preparation passes. Append unique_unit_events introductions/model resolvers, then run final integrity/copy passes. Run unique_divisions.install(SOURCE,TARGET,read,write,parse,serialise) after specialist_units.install. It reads current target tech files and retains old hooks. Run install_personnel after all old roster/personality writers and before final minister validation; the attachment installer can follow it. Merge localisation_rows() into the normal localisation writer.

The installer appends d_13–d_15 and all modifier columns without touching old class slots. It adds explicit full-factor conversion routes to and from the native class and preserves native alternate conversion paths. Counter strip cells 53–55 inherit functional Destroyer/NAV/Para glyphs plus distinct AA/P/AB markers, with the old palette and every old indexed pixel preserved. It does not claim bespoke animated map sprites. Parent art must provide jx_unique_akizuki / jx_unique_patrol / jx_unique_teishin event pictures and the corresponding unit cards; early H6K artwork is separate from later H8K artwork.

## Validation

- Catalogue parity pass is idempotent and allocates no event IDs.
- All 29 models retain full native manpower/equipment; the four new classes provide reach, economical ASW or expeditionary terrain/endurance with explicit tradeoffs and IC-day checks.
- Fixture installer appends d_13 through d_19, preserves retired d_10 through d_12, copies native attachment/conversion choices and adds full-factor normal conversion routes.
- All terrain/weather columns match their native parent except the six intended expeditionary bonuses. Model names precede EOF; the 60-cell counter atlas preserves old pixels and adds distinct AA/P/AB/LR/NA/AS/EX markers.
- Research-before/after activation gives identical modifiers exactly once; year-bound catch-up, reverse resolver order, sparse research, foreign countries and implicit model zero all behave correctly without reviving old models.
- Every Japanese concrete-class programme award and penalty is mirrored; programme-before-unlock versus after-unlock gives identical cost/time/range/organisation without guessing old-save choices or replaying payments.
- All applicable Japanese concrete minister effects, including penalties, are mirrored (45 entries); shared air/navy/land modifiers are not copied and the personnel pass is idempotent.

## Limits

- No engine launch: subtype airborne missions, naval conversion queues, animation families and modifier caches still need runtime testing.
- Model dates are hard-gated by year+research; resolvers through 1950 must be appended by unique_unit_events. The 1955 AA data model is retained beyond campaign end.
- Flying boats use native surface detection and naval strike, with no invented independent submarine-attack statistic.
- Full historical programme parity requires a new R12 campaign; old R11 completion flags do not prove which alternative was selected.
- Only the division counter atlas is authored here; parent supplies original model cards and event illustrations.
