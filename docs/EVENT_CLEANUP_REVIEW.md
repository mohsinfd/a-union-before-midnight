# Event cleanup review: 1933 onward

Reviewed 8 September 2026, using `mod/db/events.txt` and its loaded custom modules. This is a module-wide structural review plus a detailed editorial pass on the early political, social, economic and military chains. It does not claim that every branch was run in the engine. Recommendations below are not claims that modules have already been merged or removed.

The starting inventory contains 57 modules, 5,544 event definitions and 139 decisions. Definitions are not the number of popups a player sees. Compatibility events `9281900` and `9283200` already sleep 217 distinct legacy IDs; fresh 1933 scenarios also sleep `9270306` and `9270340`, bringing that count to 219. Old IDs must remain for saved history and compatibility. Fresh V4 games use `9281800` and `9281801` for Gurkha and Frontier commissioning.

India should retain population, industrial scale, competent research, geography and diplomatic freedom as advantages. Repeated meetings should not each add a permanent national combat bonus. Schools are particularly sensitive: a bonus to every unit of a class becomes stronger as the human builds a larger army.

## Keep, trim, merge and retire

Keep political choices, historical developments, military institutions and significant campaign milestones. Merge navigation into War Cabinet, Campaigns, Peace Talks and War Economy during war. Keep compatibility and progress tracking in the background. Retire superseded entry points with guards and sleep lists rather than deleting IDs. Trim repeated briefings, confirmation clicks and rewards unrelated to the event's subject.

Each option should clearly state what it delivers or orders, its costs, whether a bonus affects a unit or the whole country, and whether it changes a war or alliance. “Cancel” must mean no changes. A choice between immediate forces and long-term training should remain a real choice at both 50 and 250 divisions.

## Original India modules

All paths in this table are under `mod/db/events/india_v3/`. ID ranges identify a sequence, not necessarily every integer in the range.

| Module | Recommendation | Concrete IDs and reason |
|---|---|---|
| `00_bootstrap` | Keep | `9270000`, `9270002`, `9270001`: explain the Union, choose the first cabinet, establish government. One opening sequence is useful. |
| `10_politics` | Keep; simplify | `9270100–9270103`: constitution, land, language and election define India. Preserve political outcomes, not just the lowest dissent option. |
| `12_society` | Keep; balance | `9271304` has a real reform/unrest tradeoff; retain Burma autonomy `9271305`. Technical education `9271307` gave more research and factories with no money cost; add a modest cost and explain both outcomes. |
| `20_development` | Keep; trim presentation | `9270200–9270205` are reconstruction through the second plan. `9270200` gives concentrated 24 IC, dispersed 16 IC or cheaper private 12 IC: this is a tangible choice worth keeping. `9270206` is a useful culmination. |
| `21_fallbacks` | Keep recovery; trim notices | `9270700–9270704` prevent missed plans from blocking the campaign. `9270792` is old-save appointment repair. `9270794–9270795` unlock types, not deliveries. Keep debt consequence `9270796`. |
| `22_resources` | Keep | `9271400–9271408`: coal, steel, oil and minerals explain industrial strength geographically. Put `9271408` in the economy menu during war. |
| `30_military` | Keep core; retain legacy fallback | `9270300–9270305` establish the services, arms and defence. `9270306` is retired on fresh starts; correct its concealed 3/3/1 full-division bargain for old saves. |
| `31_air_force` | Keep; correct deliveries | `9271000–9271008` provide staff, school, doctrine and officer history. Rename `9271006`, whose Fifteen-Wing title actually orders two or three wings. |
| `32_navy` | Keep; cap advantage | `9271111` should own dockyard standardisation, with a tracked wartime increment above a peace baseline. Keep carrier choice `9271103`. Main integration pass owns the naval change. |
| `33_command_research` | Keep; correct false choices | `9271200–9271211` give institutions and research. `9271205` orders a mountain division, not infantry retraining. `9271206` offered three combined-arms units cheaper than two infantry; correct it. |
| `34_elite_forces` | Keep; trim class bonuses | `9270340` is fresh-start retired. `9270341–9270343` are meaningful airborne, eastern and marine choices; make all-class school bonuses modest and explicit. |
| `40_diplomacy` | Keep contacts; merge route entry | `9270401–9270403` are early contacts. `9270404–9270409` are already retired alliance entries. One current relationship must own later offers. |
| `41_allied` | Keep missions; retain retirement | Keep early cooperation `9272000–9272002`; `9272003`, `9272005` are retired war/settlement logic. |
| `42_axis` | Keep industry; retain retirement | Keep `9272200–9272201` industry and armour identity; `9272204` war aims are retired. |
| `43_soviet` | Keep planning; merge war choice | Keep `9272400–9272402` planning and domestic consequences. `9272403–9272405` are retired; `9272406` must respect the current relationship. |
| `44_non_aligned` | Keep identity | `9272600–9272603` establish independent cooperation; `9272604–9272606` are retired. Sovereignty does not mean India is at peace. |
| `45_japan` | Keep early missions; trim war aims | `9272202`, `9272203`, `9272210–9272212` need current Japan-war guards. `9272205`, `9272213–9272215` are retired. |
| `46_world_reactions` | Keep context; branch responses | `9270450–9270455` world events can continue, but India's response must match current enemies. `9270456` is retired. |
| `47_revisionist_aftermath` | Keep conditional outcomes | `9272206–9272207` must require the relevant former partnership and defeat, not just an old diplomatic contact. |
| `50_wartime` | Keep mobilisation; merge finance | Keep `9270500–9270502`, `9270504`; `9270503`, `9270505` are retired. `9270500` falsely claimed 35%/50% strength where delivery commands set no such strength. |
| `51_theatres` | Retain retired IDs | All `9273000–9273007` are retired. Their subjects belong in current campaign briefs, not a parallel theatre chain. |
| `52_home_front` | Keep unique science/social choices | `9273200–9273203`, `9273208` are retired. Preserve the other subjects; avoid duplicate budgets or manpower payouts. |
| `60_postwar` | Keep payoff; clarify scope | `9270600–9270604` cover science, fleet, industry, world role and demobilisation. `9270601` carrier wording conceals all-ship effects and a duplicate organisation command. |
| `61_cold_war` | Keep long campaign payoff | `9274000–9274015` give reasons to play beyond 1945. Decolonisation/borders must check surviving countries, actual ownership and earlier Indian settlements. |
| `62_victory` | Keep sparse reports | `9275000–9275005`: retain milestone outcomes, without repeated passive menu buttons. |

## V4 modules

All paths are under `mod/db/events/aubm_v4/`.

| Module | Recommendation | Concrete IDs and reason |
|---|---|---|
| `00_world_bootstrap` | Keep background | `9280000` compatibility is state repair, not a strategic choice. |
| `05_union_integration` | Keep | `9280100–9280120` explain Ceylon, Burma, customs, rail and federation. Put `9280118` under national affairs in wartime. |
| `10_world_reactions` | Keep; guard current state | `9280300–9280303` diplomatic approaches must not offer a friendly Tokyo choice during an existing Japan war. |
| `12_campaign_systems` | Keep; merge economy entry | `9280310–9280314`, `9280320–9280321` belong in War Economy. Borrowing and repayment need one consistent debt register. |
| `15_operational_command` | Keep | `9280150–9280162` give practical forces. `9280152` airfield security and `9280162` first air group must separate bases from aircraft delivery. |
| `18_manpower_reserves` | Keep; merge call-up | `9280840–9280843` annual reserves, emergency call-up and mobile cadres. Show `9280841` under War Economy when usable. |
| `20_procurement` | Keep; one procurement page | `9280200–9280203` army, wing and fleet organisation; replacement pool `9280203` belongs in economy navigation. |
| `22_crisis_interventions` | Keep actual crises; guard peace | `9280900–9280968` includes Abyssinia/Aden. `9280940` is retired. A regional crisis must not end unrelated coalition wars. |
| `25_global_war` | Keep world changes; branch India replies | `9280350–9280359`, especially `9280356`, must distinguish Indian neutrality, partnership and existing war. |
| `26_grand_strategy` | Merge entry | `9280500–9280503` remain useful; reach `9280500` through War Cabinet during war. |
| `27_dynamic_strategy` | Keep limited review | `9280510` reviews the current relationship through War Cabinet. `9280530–9280534` are retired. Do not reopen incompatible completed offers. |
| `28_foreign_responses` | Keep replies; trim repeat notices | `9280600–9280645` should retain meaningful accept/refuse outcomes. Reduce generic permanent rewards for acknowledgements. |
| `29_world_pressure` | Keep; separate war and peace language | `9280704` cannot offer neutrality during India's Japan war. `9280706` cannot infer actual carrier raids from a Japan–Britain war alone. |
| `30_war_settlements` | Retain retired IDs | All `9280400–9280405` are retired. Do not add another peace-table owner here. |
| `31_campaign_continuity` | Keep repair/research | `9280801–9280802` are retired. Keep `9280800`, `9280810–9280811`; expose `9280830` only when actionable. |
| `32_national_consolidation` | Keep accounting; trim visible ledgers | `9281000`, `9281005–9281007` are accounting/repair. `9281012–9281013` should not force extra navigation. `9281008` early wars is an exceptional setting. |
| `35_japan_partnership` | Keep bespoke compact; merge menus | `9281100–9281190` owns Japan's compact and concessions. Entry points such as `9281133`, `9281140`, `9281160`, `9281180` need current-partnership guards. |
| `36_allied_campaigns` | Keep compact; retain 48 retired IDs | Keep `9281200–9281204` negotiation identity. Forty-eight later IDs including `9281217`, `9281240` are retired; current route arcs own operations. |
| `37_german_campaigns` | Keep compact; retain 40 retired IDs | `9281300–9281304` distinguish alliance and independent Soviet war. Forty old outcomes including `9281341`, `9281385` are retired. Clearly disclose added wars. |
| `38_soviet_campaigns` | Keep compact; retain 36 retired IDs | `9281400–9281404` equality/veto/refusal choices are useful. Thirty-six legacy outcomes are retired. Fighting Japan independently must remain distinct from joining every Soviet war. |
| `39_non_aligned_campaigns` | Keep identity; trim branches | `9281500–9281504` define the Delhi system. Forty-four legacy IDs are retired. Each independent mission needs its own enemy/settlement checks. |
| `40_special_units_and_capital_ships` | Keep unique units; merge orders | `9281800–9281807` are fresh-game special-unit contracts; `9281880–9281881` upgrades belong on the same procurement page. Preserve distinct models and sprites. |
| `41_wartime_state` | Keep central owner; trim menus | `9281910` and related menus should own current relationship/war status. Use one root, immediate navigation and a safe cancel. |
| `42_wartime_theatres` | Merge into Campaigns | `9281930–9281933` theatre menus and milestones such as `9281940` should show active fronts and reward actual progress once. |
| `43_wartime_settlements` | Keep rewards; guard every peace | 862 definitions at review start. `9282000–9282008` and LIBERATOR outcomes require explicit enemy/coalition ownership. |
| `44_wartime_economy` | Keep one visible root | `9282080–9282094` budgets, treasury and postwar debt. Explain costs that persist after peace; use one debt owner. |
| `45_enemy_campaigns` | Keep briefs; trim repeated pages | `9282120–9282124` explain major-power wars. Show objectives and holds without several passive ledgers. |
| `46_regional_campaigns` | Keep geography; repair ownership | Siam `9282232`, `9282242`, `9282260` must establish the intended new regime and preserve India's Japanese war. Capital capture does not authorise India to leave a coalition war. |
| `47_global_campaign_matrix` | Keep fallback; trim navigation | 3,433 definitions; `9282300` and sequences from `9285800` expose too much browsing. Show current enemies/actionable campaigns, with shared settlement checks. |
| `48_route_wartime_consequences` | Keep one route charter | `9283200` retires old logic. `9283210`, `9283220–9283222` and counterparts must match actual partnership and war state. |
| `49_bespoke_armistices` | Keep; simple names and safe peace | `9282270–9282274`: use “Peace terms” instead of “settlement docket.” Keep country-specific rewards; no unsafe India-issued coalition-member peace. |
| `50_southeast_asia_operations` | Keep cross-route milestones | `9287640` Indochina, `9287650` Philippines, `9287660` Bay of Bengal need real control/enemy tests. `9287657–9287658` suspension/restoration is background tracking. |
| `51_bespoke_route_arcs` | Keep flavour; one campaign page | `9289499`, `9289500`, `9289540`, `9289580`, `9289620`, `9289660`: open the relevant route and alternative wars. Remove “authored” from player language; keep hold/defeat/reward stages. |

## Edits made in the bounded editorial pass

1. `9270306`: legacy Gurkha choices now give three/two/one full mountain divisions. The three-division option loses its global mountain bonus. The school falls from +5 organisation/+5 morale to +2/+2. Costs and flags remain intact. No existing units are removed.
2. `9270340`: Frontier school +3/+3 becomes +1/+1. `9270341`: airborne school +4/+4 becomes +2/+2. `9270342`: mountain school +4/+3 becomes +1/+1; reconnaissance's all-infantry morale +3 becomes +1. `9270343`: marine school +4/+4 becomes +2/+2. Deliveries stay intact; descriptions disclose scope and mission limits.
3. `9271006`: renamed to “1938 Air Expansion Plan”; choices state their actual two or three production orders and funding requirement.
4. `9271205`: cheaper choice correctly says it orders a mountain division with engineers.
5. `9271206`: combined-arms choice costs 600 money/1,500 supplies instead of 425/1,050, against the unchanged two-infantry choice's 450/1,100. Labels explain the real unit counts and training choice.
6. `9270500`: remove unsupported 35%/50% strength claims from the mobilisation label.
7. `9270601`: replace carrier-only wording with fleet combat training. Remove duplicate +2 naval organisation, leaving +3 organisation/+2 morale. Explain all three options' national scope.
8. `9271307`: technical education costs 200 money instead of nothing; explain both outcomes. Research remains +3 versus +4.
9. `9270794–9270795`: describe unit-type unlocks accurately, without promising delivered tanks or aircraft.

These affect unfired events. They do not retroactively subtract old modifiers, delete units, reset political decisions or erase completed flags. Shared menu cleanup, diplomatic guards, new events, save migration and deployment belong to the main integration pass.

## Verification and limits

Check event IDs, balanced syntax, text lengths, preserved completion flags and actual unit-command counts. Check the decision-description generator preserves the manually written Gurkha summary. Existing generators do not own the edited V3 prose; `ensure_decision_visibility.py` regenerates generic cost summaries from action labels and costs, so the Gurkha summary is marked with its supported manual-description marker.

For a fresh campaign, test opening choices, a missed development plan, education costs, 1936 military orders, fresh special-unit commissioning and first war. At war, count visible decisions and check immediate exits. Test Japan as partner, enemy and neutral observer, plus independent Japanese/Soviet wars. Siam's new peace must leave Japan an enemy unless a separate Japanese peace was chosen.

Static checks cannot establish separate-peace scope, delivery strength, queue timing or the final on-screen readability. Those need an engine test. Do not delete the global matrix or retired modules until their callers, delayed replies and saved flags all have replacements.
