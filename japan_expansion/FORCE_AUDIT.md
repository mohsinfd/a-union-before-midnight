# R9 force-value audit

Historical R9 manufacturing and model-value analysis. The final recruitment policy is documented in FORCE_DELIVERY_AUDIT.md: the three custom classes are retired in new campaigns, and full Marines replace the Jungle Light production subsidy. Model comparisons below describe retained compatibility data, not a recommendation to recruit those classes.

- Catalogue application is idempotent; no event IDs or ordering change.
- Both funded choices cover six aircraft classes exactly once, with stronger chosen roles; no units or research awarded.
- 5 concrete minister effects mirrored; native effects retained, shared land effects not duplicated, second pass adds nothing.
- Expanded personnel roster + specialist mirroring serialise and parse successfully using an in-memory build, with no installed-file writes.
- Every sampled 1933/1937/1941/1945/1950 air model retains positive raw cost/time under the stronger priority plus native assembly line.
- All 15 specialist models have real prerequisite tech IDs, lower manpower and lower IC-days than their contemporary native class.

## Aircraft manufacturing

The existing selected-role rebates are retained. The other three aircraft classes now receive 1.5 IC / 18 days of common tooling from the same funded choice. Selected totals replace the common rebate. This supports a mixed air force without a second decision or a second setup bill.

| Year | Unit | Base IC / days | Priority IC / days | Priority + native assembly days |
| --- | --- | --- | --- | --- |
| 1933 | interceptor | 17 / 210 | 13.5 / 168 | 126.24 |
| 1933 | multi_role | 18 / 210 | 14 / 168 | 126.24 |
| 1933 | tactical_bomber | 20 / 230 | 15 / 184 | 137.92 |
| 1933 | naval_bomber | 14 / 230 | 10 / 182 | 134.48 |
| 1933 | transport_plane | 30 / 200 | 25 / 152 | 72 |
| 1937 | interceptor | 18 / 210 | 14.5 / 168 | 126.24 |
| 1937 | multi_role | 18 / 210 | 14 / 168 | 126.24 |
| 1937 | cas | 15 / 230 | 11 / 184 | 142 |
| 1937 | tactical_bomber | 20 / 230 | 15 / 184 | 137.92 |
| 1937 | naval_bomber | 14 / 230 | 10 / 182 | 134.48 |
| 1937 | transport_plane | 30 / 200 | 25 / 152 | 72 |
| 1941 | interceptor | 19 / 210 | 15.5 / 168 | 126.24 |
| 1941 | multi_role | 20 / 210 | 16 / 168 | 126.24 |
| 1941 | cas | 16 / 230 | 12 / 184 | 142 |
| 1941 | tactical_bomber | 22 / 230 | 17 / 184 | 137.92 |
| 1941 | naval_bomber | 16 / 240 | 12 / 192 | 144.48 |
| 1941 | transport_plane | 20 / 200 | 15 / 152 | 72 |
| 1945 | interceptor | 22 / 210 | 18.5 / 168 | 126.24 |
| 1945 | multi_role | 22 / 210 | 18 / 168 | 126.24 |
| 1945 | cas | 18 / 230 | 14 / 184 | 142 |
| 1945 | tactical_bomber | 25 / 230 | 20 / 184 | 137.92 |
| 1945 | naval_bomber | 21 / 240 | 17 / 192 | 144.48 |
| 1945 | transport_plane | 20 / 200 | 15 / 152 | 72 |
| 1950 | interceptor | 24 / 210 | 20.5 / 168 | 126.24 |
| 1950 | multi_role | 25 / 210 | 21 / 168 | 126.24 |
| 1950 | cas | 20 / 230 | 16 / 184 | 142 |
| 1950 | tactical_bomber | 26 / 230 | 21 / 184 | 137.92 |
| 1950 | naval_bomber | 22 / 240 | 18 / 192 | 144.48 |
| 1950 | transport_plane | 20 / 200 | 15 / 152 | 72 |

These are raw model and national-adjustment comparisons, not final production queue quotes. Native aircraft assembly removes 41.76 INT/FTR, 42 CAS, 46.08 TAC, 47.52 NAV and 80 transport days. It stacks with the service programme. Domestic policy, minister effects, gearing and conversion/upgrade factors remain active; cheaper factories do not reduce fuel, manpower or operating supply.

## Specialists and personnel

The R8 specialist economy is already substantial: base forces cost 400 vs 640 IC-days with half the manpower; jungle infantry cost 760 vs 1,450 with 8 vs 13 manpower; SNLF cost 1,440 vs 3,360 with 9 vs 15 manpower before the native postwar Marine mechanisation model. Jungle terrain and SNLF landing/river advantages already exist. Added combat strength would obscure those distinct roles and create cheap replacements for full divisions. Their five-model progression and existing technology catch-up are retained.

The change mirrors concrete garrison/infantry/marine minister effects onto their corresponding Japanese specialist class, including adverse values. Shared land effects are left as one copy. This keeps personnel choices useful across the selected force structure. Native formations, personalities and appointment dates retain their original entries.

The current Japanese roster has five applicable concrete infantry effects across Static Defence, Decisive Battle and Razor personalities. Those now cover Jungle Light Infantry. Base Force/SNLF retain existing generic land benefits; there are no applicable concrete garrison/marine effects in that roster to duplicate. Foreign-only personalities are untouched.

## Germany comparison and integration

Read the installed Germany Overhaul Campaign GMO force-preparation and manufacturing-retooling events plus their secret-weapons tech entries. Reused the principle of independent service priorities, fixed production improvements and actual research/IC requirements. Did not copy Germany's very large research-unlock/retooling event graph into Japan or edit any German file.

In build.prepare_catalog(), import force_value and call force_value.apply() immediately after human_campaign.apply(). In compile_mod(), call force_value.apply_personnel(TARGET, read, write, parse, serialise) immediately after japan_personnel.apply_roster(). No model/configure hook is needed; specialist_units.py remains untouched.

## Validation limits

- Static source/data inspection only; no engine or campaign was launched.
- Raw air arithmetic excludes doctrine surcharges, sliders, minister multipliers, conversion ratios, upgrades, gearing and rounding; these are not displayed queue prices.
- Latest nominal-year research is a comparison, not a claim that Japan can or should research every branch by then.
- Some obsolete pre-1930 aircraft can reach the engine time floor after stacking native assembly with priority; modern sampled models remain positive.
- Custom-class minister targeting requires engine validation; source structure permits explicit unit commands but this audit cannot prove runtime inheritance behavior.
