# Six prewar preparations for human Japan

Implementation: `prewar_content.append_events()` runs after the existing R10 catalogue passes, before the final `IDS` refresh. Importing the module is inert. It appends six manual decisions and twelve alternative completion receivers; every pre-existing event and ID is retained. No game, active mod, save or Germany files are edited by the module or its tests.

## Why these programmes

The R10 source has useful big investments, but much of its apparent 1933-40 event count is not ordinary peacetime activity. China settlements need a war outcome; the fuel batch, repair service and wartime fuel works need war; the three service priorities buy production discounts. Seven former annual stories were deliberately retired because their effects were small or overlapped the larger priorities. Convoy offers and commercial contracts already exist in 1934/35/39. This extension therefore adds institutional and physical choices rather than another convoy order, oil contract, production rebate, small range increment or custom formation.

These are optional counterfactual preparation stories, not assertions that Japan historically implemented every proposal. They preserve the player's diplomatic choices and the historical opening through Pearl Harbor. China war is compatible with new funding; the Pacific flag or war with America or Britain closes unfunded proposals. Work already funded can finish during the wider war.

## Calendar and competing outcomes

All numbers are the actual scripted values, before other national modifiers. Each row is one exclusive choice. Money, supplies, oil, energy, metal and civilian manpower are deducted from the real pool at funding.

| Opens | Programme and delay | Inputs paid now | First outcome | Competing outcome |
| --- | --- | --- | --- | --- |
| April 1933 | Rural recovery, 270 days | 45 money, 400 supplies, 300 metal; civilian branch additionally pays 25 manpower | 3 physical IC at Nagoya; the 25 manpower remains committed to civilian employment after success | 40 manpower once after reserve training, with 1 dissent for the levy |
| June 1934 | Carrier safety commission, 240 days | 60 money, 450 supplies, 250 oil | CAG and light CAG: morale +8 and maximum organisation +5 | Fleet/light carriers: sea-defence vulnerability -4, with speed -1; lower vulnerability is better |
| February 1935 | Navigation or coastal warning, 180 days | 75 money, 600 supplies, 500 metal, 1,000 energy | Naval bomber range +300 km and surface detection +2 | 2 AA at Tokyo and 2 at Hiroshima |
| May 1936 | Joint landing experiment, 180 days | 80 money, 800 supplies, 300 oil | Amphibious assault-size limit +1 formation and standard Marine maximum organisation +5 | Standard Marine shore attack +12 percentage points and river attack +8; no assault-size increase |
| March 1938 | Medical service or certified reserve, 180 days | 60 money, 700 supplies | National trickle-back modifier +25 percentage points, improving future casualty recovery | 50 manpower once after fitness examinations and training, with 1 dissent for the levy |
| January 1940 | Factory dispersion, 270 days | 90 money, 900 supplies, 1,000 metal | 2 physical IC and 4 AA at Sendai | 4 physical IC at Tokyo, with no extra AA |

The 1933 civilian choice spends manpower rather than quietly giving industry and men together. The protected deck choice makes the affected carriers slower. Reserve choices impose a finite dissent cost, while treatment capacity helps only when casualties actually occur. Dispersed factories trade two new IC for fixed defences. The choices do not include completed formations, inserted production orders, global unit changes, new technology or recurring recruitment. Normal Marine research and production remain necessary.

The trickle-back modifier is not a promise that 25 percent of all losses return. B&I's base casualty-return factor is 0.15; increasing its country multiplier by 0.25 contributes `0.15 * 0.25 = 0.0375`, or 3.75 percentage points, before the other applicable modifiers. The reserve alternative is a finite medical-fitness intake in peace; it does not invent wartime wounded before a war.

## Player flow and transaction safeguards

Each offer has exactly four actions: fund the first outcome, fund the second, leave it available, or dismiss it permanently. Leaving it spends nothing and schedules nothing. Dismissal is permanent. Funded work closes the original offer and schedules one completion notice for the stated delay. There is no extra claim-reward card and no quarterly reminder chain.

The completion rechecks the pending receipt, the selected branch, the original event's saved funding date, the elapsed days, human Japan and all relevant site/research/building conditions. It either awards that selected result once or returns the exact original money, supplies, metal, energy, oil and manpower payment once. Failure closes the programme; it does not schedule an automatic retry. Duplicate, early, wrong-branch or stale receiver dispatches are inert. No later war cancels work that was validly funded, provided its selected result remains eligible.

For physical construction the action requires Japanese ownership and control, the actual construction-unlock technology, room below the building cap, and infrastructure above 30 for new IC. Both alternatives get their own eligibility checks: losing Hiroshima does not silently redirect a paid AA project into a navigation award. No old factory is removed or relocated. This avoids a destructive partial transfer if a receiving-site construction command fails.

As with normal engine construction, a home-city building still needs supply. The local command contract supplies no reliable province-in-supply predicate for this event gate. The owned home-city sites make this a narrow qualification, but offline tests do not prove successful engine construction under every blockade or supply condition. The text does not claim to inspect that hidden engine state.

## Affordability and economy

B&I Japan begins with 100 money, 500 supplies, 1,000 metal, 1,000 energy, 500 oil and 200 manpower. Either April 1933 outcome is fundable from those raw opening pools. The civilian choice leaves 55 money, 100 supplies, 700 metal and 175 manpower; the reserve choice leaves the same economic stocks and retains the original 200 manpower until its later 40-manpower intake. Other preparation spending can change that position, so the offer remains available without reminders when funds are short.

Funding one outcome from each row costs a total 410 money, 3,850 supplies, 1,800 metal, 1,000 energy and 550 oil across 1933-40. The civilian branch additionally commits 25 manpower. Those totals do not include the existing service, fuel, research or trade budgets. Relative to the raw starting cash/supplies, the extra 310 money and 3,350 supplies correspond to 1,550 gross consumer-goods IC-days at 0.2 money/IC and 837.5 supply IC-days at 4 supplies/IC. Spread across seven years this is roughly 0.94 additional gross IC before ongoing research, import and military expenses. These are preparation choices to budget over years, not six bills intended to be funded on opening day.

Industrial paths can add at most 7 physical IC (3 Nagoya plus 4 Tokyo). They create no energy, metal, rares or free IC modifier. At a one-to-one effective IC illustration, the additional seven require 14 energy, 7 metal and 3.5 rares daily. Actual effective output and inputs depend on the country's other modifiers. The existing endurance economy's approximate 150-effective-IC balanced ceiling is not raised by these factory awards: trade or conquest must fund output beyond the available feedstocks.

## Local evidence

The actual `map/Map_1/province_names.csv` and `province.csv` identify Nagoya as **1557**, Tokyo **1552**, Hiroshima **1554** and Sendai **1549**. Initial infrastructure is Nagoya 60, Tokyo 70, Hiroshima 60 and Sendai 60. Sapporo (1545) was rejected as a new-IC site because its starting infrastructure is exactly 30; new IC requires more than 30. Province 1556 is Kanazawa, not Nagoya.

Native `industry_tech.txt` technology **5800** unlocks IC construction. Native `armor_tech.txt` technology **2800** unlocks static AA. Both appear in Japan's 1933 starting `techapps`. The extension gates the specific construction alternative on those technologies at funding and completion. Building caps are IC 200 and AA 10, with required increments included in the room check.

The installed game's `Modding documentation/event commands.txt` documents month and year lower-bound predicates, `event = { id = ... days = ... }` with `save_date = yes`, construction ownership/research/supply conditions, air surface detection/range, naval additive modifiers, shore/river attack, trickle-back and maximum amphibious-size modifiers. The renderer already emits `save_date = yes` for each event.

Native B&I `db/events/Mods.txt` event **9300392**, the Illustrious-class event, uses `naval_defense which = carrier value = -2` and explicitly labels it a bonus. Submarine events also use negative naval-defence values as bonuses. Accordingly, this extension uses **-4**, never +4, for protection. All nine native carrier models remain above zero in sea vulnerability and speed after -4/-1; all four light-carrier models do too. A carrier template with sea vulnerability 27 becomes 23 before other modifiers; light carriers with 30 become 26. This is meaningful protection with a permanent speed cost, rather than a positive number that secretly makes ships easier to hit.

Native naval doctrines use `max_amphib_mod` values of 2, 3, 5 and 7 as absolute assault limits. The local command contract specifies that omitted `when` (or `when = 0`) sets this limit; `when = 1` adds to it. This programme therefore explicitly uses `value = 1 when = 1`, preserving researched limits: a limit of five becomes six. Native medical technologies and land doctrines use `trickleback_mod`, whose default mode is additive. These are existing engine systems, not new invented unit properties.

## Validation

`python japan_expansion/PREWAR_review.py` passes ten tests covering all twelve alternative transactions, exact costs, full delays, selected-branch exclusivity, one reward, stale/early/duplicate dispatch, every missing input, civilian manpower deduction and exact refund, site loss, research loss, building caps, insufficient infrastructure, work completing after Pearl Harbor, raw opening affordability, dates, war exclusions, no-op leaving, dismissal, native vulnerability direction, positive ship floors, a pre-existing amphibious limit of five increasing to six, append-only IDs and the absence of automatic diplomacy, free daily production or custom-unit recruitment.

All 18 generated event blocks parse through the existing compiler. Parent integration must include the documented new command types in static validation and the offline state model where needed: `surface_detection`, `shore_attack`, `max_amphib_mod`, `trickleback_mod`, and `speed`. The module also exposes `DOCUMENTED_NEW_COMMANDS`. Engine popup readability, simultaneous source/technology effects and sustained Hard balance remain player-test qualifications; no engine test was performed.
