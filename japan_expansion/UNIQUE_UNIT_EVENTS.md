# Japanese first-issue formations and attachments - R13

R13 adds four further free formations: Expeditionary Assault Infantry (1937), Naval Attack (1938), Naval Fighters (1940) and Matsu escorts (1944). See R13_UNITS.md for their research, equipment, prices, tradeoffs and upgrades. The existing heavy-submarine family is preserved.

R12.1 fixes the original activation-ordering risk. The first notice starts a pending request; the follow-up owns activation, researched-model/effect catch-up, equipment creation, named strength restoration and final completion. Every command rechecks its transaction. A delayed acknowledgement cannot close activation prematurely, and replay cannot duplicate units or bonuses. Losing every usable base while waiting resets the request without consuming its free issue.

The six original R12 introductions below remain automatic for independent human Japan after the expansion begins. They require the listed service year and research, **not a war or a funding decision**. The first issue is already recruited and funded: the events deduct no Japanese money, manpower, supplies or fuel. Additional units use ordinary production and operating costs.

| Introduction | Earliest service and research | Free first issue | Later equipment through 1950 |
| --- | --- | --- | --- |
| Type 93 Oxygen Torpedoes | 1935; Improved Destroyer | Two naval attachments in the deployment pool | 1942, 1945, 1948 |
| Dokuritsu Konsei Mixed Brigade | 1937; 1936 Infantry Division | Two land attachments in the deployment pool | 1939, 1942, 1945, 1948 |
| Maritime Flying Boat Wing | 1938; Naval Bomber 1938 | One H6K-era patrol wing | H8K from 1942, then 1943, 1945, 1949 |
| Ka-Mi Naval Tank Detachment | 1942; Improved Light Tank | Two land attachments in the deployment pool | 1944, 1949 |
| Akizuki Anti-Air Escort Flotilla | 1942; Modern Destroyer | One anti-air escort flotilla | 1945; a further 1955 data model lies beyond this campaign's 1950 end |
| Teishin Airborne Division | 1942; 1941 Airborne Infantry Division | One airborne division, following the training begun in 1941 | 1944, 1947, 1950 |

The initial models represent **24.7 manpower in total**: 12.7 in the three full formations and 12 in the six attachments. That is a finite first-issue programme, not a new recurring manpower source. There are no later free replacement formations or repeatable attachment claims. Losing an introduced unit does not issue it again.

## Where the formations appear

The anti-air escort selects the first operational, Japanese-owned and Japanese-controlled home port: Tokyo, Hiroshima, Kobe, then Yokohama. The flying-boat wing and Teishin division select a current level-one-or-higher home airfield: Tokyo, Hiroshima, Nagoya, then Sendai.

If every listed base is unavailable, the automatic introduction remains eligible to occur later; no completion is recorded and no free formation is lost. It waits quietly for a usable base rather than opening repeated retry windows. When the event does occur, its single eligible action names the actual deployment city. The three formations receive scoped, uniquely named strength restoration to their existing allowed maximum. Organisation and subsequent damage follow ordinary deployment and combat rules.

The Type 93, mixed and Ka-Mi attachments go directly to the deployment pool through native `add_brigade value = <type> when = <model>` commands. They are actual attachments, not incomplete production orders. They still need compatible host formations. Type 93 fits the allowed Japanese destroyer/cruiser types, including the new anti-air escort; the mixed brigade fits Infantry, Garrison and Militia; Ka-Mi fits Infantry and Marines. The extra attachment options do not rewrite existing garrison models or the 31 local-defence templates.

## Research, service years and existing bonuses

Early research cannot introduce equipment before its advertised service year. Each first issue chooses the latest model for which **both year and research** are satisfied. Researching a future H8K, tank or torpedo model early therefore neither grants that equipment prematurely nor blocks the earlier free issue.

Seventeen automatic, once-only model resolvers cover upgrades through 1950. They catch research completed before a model's service year; ordinary native technology hooks handle research completed after the year opens. Research and model receipts are separate, so an early-research stat bonus cannot consume the later model unlock. Cross-tree research cannot revive obsolete lower models. The three classes and three attachments retain relevant Japanese technology and minister effects.

For a **new R12 campaign**, concrete programme bonuses are mirrored onto the registered classes even before their introduction. Unlocking the class does not replay those programme bonuses. Technology bonuses researched before introduction instead catch up once at activation; bonuses researched later use the same receipts in the native research hooks. The before/after results have been compared using actual installed hooks, including research effects executed before the just-completed technology is marked known. Old R11 saves are not migrated or given guessed programme alternatives.

The 1938 introduction uses its own H6K illustration with parasol wing and twin tail. Later flying-boat models use the distinct H8K artwork. All six families have dedicated model cards and event images, with appropriate native counter/attachment glyphs. Both small and large cards are installed for the physical model indices.

## Event flow and audit

`unique_unit_events.py` adds six substantive automatic introductions, six guarded technical activation receivers, and seventeen equipment-year resolvers: **29 appended events**, preserving all **1,773 previous IDs** for a total of **1,802**. Visible introduction actions have fewer than 20 commands; the longer researched-effect catch-up stays in guarded technical receivers. Those receivers require the introduction to be in progress and not completed; forcing or replaying them cannot duplicate the first issue. Native technical acknowledgements are not claimed to be visually silent without a running-game check.

`python japan_expansion/UNIQUE_UNIT_EVENTS_review.py`: **13 tests passed against the actual R13 installation across all ten specialist families**, including deferred human acknowledgements, cached command replay and loss of deployment bases while waiting. The independent review covers all six free issues; unchanged national pools; unavailable-base waiting and fallback; full-strength named grants; replay guards; every in-scope model/year transition and all 17 resolvers; early and sparse research; later lower-tech research; Japanese/foreign country scopes; installed technology-bonus parity before versus after unlock; programme-bonus order without double application; registered physical indices and model counts; available Japanese minister parity; attachment compatibility; actual event registration and art paths; and distinct H6K/H8K cards.

`UNIQUE_UNIT_COLD_AUDIT.json` is the machine-readable receipt. All seven source illustrations were also visually inspected: the early/late flying boats are distinct, and ship, torpedo fitting, airborne troops, mixed infantry/support and amphibious tank subjects are appropriate to their roles.

The older `EVENT_ACCESSIBILITY_MATRIX.json` is explicitly scoped to **113 legacy campaign entries and 62 paid deliveries**. R13 has **39 automatic roots** (ten introductions and twenty-nine equipment resolvers), covered by this separate native-class review rather than falsely counted as old paid-programme fixtures. Combined active roots are **152**; the ten technical activation receivers are triggered helpers, not additional offers. No new funding cards were added.

This was a cold native-contract/data audit. No game was launched, no save was edited and no Germany mod was changed. Actual AI manoeuvres, combat balance, sprite animation and running-game UI behaviour remain playtest observations.