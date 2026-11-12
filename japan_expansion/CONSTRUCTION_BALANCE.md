# Construction stacking review

Read-only review of Blood and Iron templates/assembly technologies and the prepared Japan Rising catalogue. This is an arithmetic bound, not a production-screen measurement.

## Command semantics

The installed engine manual states that build_time without `where = relative` is an absolute addition. Japan Rising uses direct days. A value of -40 therefore removes 40 days, not 40 percent. Blood and Iron assembly commands use `where = relative`: -26 means subtract 26% of model-zero time from every model. The previous wording “model-zero days” for the new absolute modifiers was imprecise.

## Method and limits

- Select the latest dated unconditional unit-model unlock at each snapshot. This does not prove the player researched it by that year.
- From 1940, include applicable assembly technology 5140/5150/5160/5180, assuming its prerequisites were researched. The year is a comparison snapshot, not a promised research schedule.
- For each eligible-year programme, choose whichever funded alternative gives the largest time reduction to the row's unit. Each programme is counted once. Map, victory, peace and other availability gates are deliberately relaxed for this upper bound.
- The rows do not form one joint set of choices. Land-doctrine modifiers, ministers, sliders, difficulty, gearing, attachments, upgrade/conversion rules and engine rounding are excluded. CAG inclusion in the air category is a conservative bound that still requires engine confirmation.
- Template IC-days illustrate only these inputs. They are not actual campaign IC-days. Research, doctrine and industrial throughput still constrain production.

| Year | Unit | Model | Raw days | Assembly reduction | Maximum new reduction | Subtotal days | Illustrative IC-days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1939 | carrier | 3 | 1200 | 0 | 153 | 1047 | 4313.64 |
| 1939 | light_carrier | 0 | 980 | 0 | 147 | 833 | 1057.91 |
| 1939 | destroyer | 6 | 540 | 0 | 54 | 486 | 544.32 |
| 1939 | light_cruiser | 5 | 1060 | 0 | 192 | 868 | 937.44 |
| 1939 | submarine | 5 | 360 | 0 | 54 | 306 | 330.48 |
| 1939 | transport | 2 | 150 | 0 | 0 | 150 | 450 |
| 1939 | interceptor | 8 | 210 | 0 | 54 | 156 | 2262 |
| 1939 | multi_role | 5 | 210 | 0 | 54 | 156 | 2340 |
| 1939 | cas | 1 | 230 | 0 | 58 | 172 | 1892 |
| 1939 | naval_bomber | 2 | 240 | 0 | 60 | 180 | 1980 |
| 1939 | tactical_bomber | 6 | 230 | 0 | 58 | 172 | 2752 |
| 1939 | cag | 3 | 170 | 0 | 37.5 | 132.5 | 424 |
| 1939 | light_cag | 3 | 170 | 0 | 37.5 | 132.5 | 209.35 |
| 1939 | infantry | 10 | 290 | 0 | 43.5 | 246.5 | 986 |
| 1939 | marine | 3 | 420 | 0 | 63 | 357 | 2284.8 |
| 1939 | bergsjaeger | 10 | 420 | 0 | 43.5 | 376.5 | 1807.2 |
| 1939 | motorized | 1 | 315 | 0 | 47.25 | 267.75 | 2945.25 |
| 1939 | paratrooper | 0 | 410 | 0 | 0 | 410 | 4100 |
| 1939 | cavalry | 11 | 330 | 0 | 49.5 | 280.5 | 2468.4 |
| 1939 | transport_plane | 2 | 200 | 0 | 60 | 140 | 2800 |
| 1939 | d_10 | 1 | 100 | 0 | 0 | 100 | 400 |
| 1939 | d_11 | 1 | 190 | 0 | 0 | 190 | 760 |
| 1939 | d_12 | 0 | 240 | 0 | 0 | 240 | 1440 |
| 1941 | carrier | 4 | 1320 | 265.2 | 153 | 901.8 | 4617.22 |
| 1941 | light_carrier | 1 | 1200 | 235.2 | 147 | 817.8 | 1651.96 |
| 1941 | destroyer | 7 | 570 | 113.4 | 54 | 402.6 | 491.17 |
| 1941 | light_cruiser | 6 | 1090 | 220.8 | 192 | 677.2 | 866.82 |
| 1941 | submarine | 6 | 360 | 72.9 | 54 | 233.1 | 251.75 |
| 1941 | transport | 3 | 150 | 30 | 0 | 120 | 360 |
| 1941 | interceptor | 9 | 210 | 41.76 | 54 | 114.24 | 1770.72 |
| 1941 | multi_role | 6 | 210 | 41.76 | 54 | 114.24 | 1827.84 |
| 1941 | cas | 2 | 230 | 42 | 58 | 130 | 1560 |
| 1941 | naval_bomber | 3 | 240 | 47.52 | 60 | 132.48 | 1589.76 |
| 1941 | tactical_bomber | 7 | 230 | 46.08 | 58 | 125.92 | 2140.64 |
| 1941 | cag | 4 | 170 | 34 | 37.5 | 98.5 | 364.45 |
| 1941 | light_cag | 4 | 170 | 34 | 37.5 | 98.5 | 180.25 |
| 1941 | infantry | 10 | 290 | 58 | 43.5 | 188.5 | 754 |
| 1941 | marine | 4 | 420 | 42 | 63 | 315 | 2016 |
| 1941 | bergsjaeger | 10 | 420 | 42.05 | 43.5 | 334.45 | 1605.36 |
| 1941 | motorized | 1 | 315 | 63 | 47.25 | 204.75 | 2252.25 |
| 1941 | paratrooper | 1 | 410 | 41 | 0 | 369 | 3690 |
| 1941 | cavalry | 11 | 330 | 66 | 49.5 | 214.5 | 1887.6 |
| 1941 | transport_plane | 3 | 200 | 80 | 60 | 60 | 900 |
| 1941 | d_10 | 1 | 100 | 20 | 0 | 80 | 320 |
| 1941 | d_11 | 1 | 190 | 38 | 0 | 152 | 608 |
| 1941 | d_12 | 1 | 240 | 24 | 0 | 216 | 1296 |
| 1945 | carrier | 5 | 1380 | 265.2 | 153 | 961.8 | 5886.22 |
| 1945 | light_carrier | 2 | 1240 | 235.2 | 147 | 857.8 | 2590.56 |
| 1945 | destroyer | 8 | 570 | 113.4 | 54 | 402.6 | 531.43 |
| 1945 | light_cruiser | 7 | 1110 | 220.8 | 192 | 697.2 | 892.42 |
| 1945 | submarine | 7 | 420 | 72.9 | 54 | 293.1 | 404.48 |
| 1945 | transport | 3 | 150 | 30 | 0 | 120 | 360 |
| 1945 | interceptor | 11 | 210 | 41.76 | 54 | 114.24 | 2113.44 |
| 1945 | multi_role | 8 | 210 | 41.76 | 54 | 114.24 | 2056.32 |
| 1945 | cas | 4 | 230 | 42 | 58 | 130 | 1820 |
| 1945 | naval_bomber | 5 | 240 | 47.52 | 60 | 132.48 | 2252.16 |
| 1945 | tactical_bomber | 9 | 230 | 46.08 | 58 | 125.92 | 2518.4 |
| 1945 | cag | 5 | 170 | 34 | 37.5 | 98.5 | 413.7 |
| 1945 | light_cag | 5 | 170 | 34 | 37.5 | 98.5 | 204.88 |
| 1945 | infantry | 12 | 290 | 58 | 43.5 | 188.5 | 754 |
| 1945 | marine | 5 | 420 | 42 | 63 | 315 | 2016 |
| 1945 | bergsjaeger | 12 | 420 | 42.05 | 43.5 | 334.45 | 1605.36 |
| 1945 | motorized | 3 | 315 | 63 | 47.25 | 204.75 | 1842.75 |
| 1945 | paratrooper | 2 | 410 | 41 | 0 | 369 | 3690 |
| 1945 | cavalry | 12 | 350 | 66 | 49.5 | 234.5 | 3001.6 |
| 1945 | transport_plane | 4 | 200 | 80 | 60 | 60 | 900 |
| 1945 | d_10 | 3 | 100 | 20 | 0 | 80 | 320 |
| 1945 | d_11 | 3 | 190 | 38 | 0 | 152 | 608 |
| 1945 | d_12 | 2 | 240 | 24 | 0 | 216 | 1296 |
| 1950 | carrier | 6 | 1440 | 265.2 | 153 | 1021.8 | 7275.22 |
| 1950 | light_carrier | 3 | 1300 | 235.2 | 147 | 917.8 | 3230.66 |
| 1950 | destroyer | 8 | 570 | 113.4 | 54 | 402.6 | 531.43 |
| 1950 | light_cruiser | 7 | 1110 | 220.8 | 192 | 697.2 | 892.42 |
| 1950 | submarine | 8 | 450 | 72.9 | 54 | 323.1 | 607.43 |
| 1950 | transport | 4 | 150 | 30 | 0 | 120 | 360 |
| 1950 | interceptor | 13 | 210 | 41.76 | 54 | 114.24 | 2341.92 |
| 1950 | multi_role | 10 | 210 | 41.76 | 54 | 114.24 | 2399.04 |
| 1950 | cas | 5 | 230 | 42 | 58 | 130 | 2080 |
| 1950 | naval_bomber | 6 | 240 | 47.52 | 60 | 132.48 | 2384.64 |
| 1950 | tactical_bomber | 10 | 230 | 46.08 | 58 | 125.92 | 2644.32 |
| 1950 | cag | 6 | 170 | 34 | 37.5 | 98.5 | 512.2 |
| 1950 | light_cag | 6 | 170 | 34 | 37.5 | 98.5 | 254.13 |
| 1950 | infantry | 13 | 290 | 58 | 43.5 | 188.5 | 754 |
| 1950 | marine | 7 | 420 | 42 | 63 | 315 | 2016 |
| 1950 | bergsjaeger | 13 | 420 | 42.05 | 43.5 | 334.45 | 1605.36 |
| 1950 | motorized | 4 | 315 | 63 | 47.25 | 204.75 | 1842.75 |
| 1950 | paratrooper | 4 | 410 | 41 | 0 | 369 | 3690 |
| 1950 | cavalry | 13 | 350 | 66 | 49.5 | 234.5 | 3236.1 |
| 1950 | transport_plane | 5 | 200 | 80 | 60 | 60 | 900 |
| 1950 | d_10 | 4 | 100 | 20 | 0 | 80 | 320 |
| 1950 | d_11 | 4 | 190 | 38 | 0 | 152 | 608 |
| 1950 | d_12 | 4 | 240 | 24 | 0 | 216 | 1296 |

92 unit/year combinations inspected. 0 nonpositive subtotal(s) under this stated bound. This does not certify the total game stacking or Hard difficulty.

## Affordability correction

R3 moved shared budget and manpower requirements onto the applicable funded actions. L3 replaces Japanese paid military queue grants with construction-time reductions and manual ordering, so those programmes no longer require manpower to insert an order. The player's own construction still requires normal manpower and IC. Setup budgets and programme prerequisites remain; delay and dismissal remain available without funding.
