# R14: the peace Japan has to live with

This adds three connected families of postwar outcomes. There are four player-facing offers: the existing Japanese recovery, China and India agreements, plus one new American agreement. Country confirmations, dated deliveries, interruption checks and refunds are internal events, not extra Japanese decisions. No game was launched for validation.

## 1. Japan after the long war (1945 onward)

Replaces `civil_recovery` in place, preserving its event number. Japan must be independent, at peace and active. One choice permanently closes the other.

| Choice | Investment | Completion | Actual result |
| --- | --- | --- | --- |
| Rebuild civilian Japan | 400 money, 2,500 supplies, 60 manpower temporarily assigned to work | 360 days | Six Tokyo IC, three dissent removed, all 60 workers returned |
| Keep training camps open | 400 money, 5,000 supplies, 2,000 oil | 180 days | 80 trained manpower, 3,000 supplies and 1,000 oil; no instant divisions |
| Retain the present economy | Nothing | Immediate | Closes the offer; no reward |

Civilian construction requires Japanese ownership/control of Tokyo, technology 5800, infrastructure above 30 percent and room under the 200 IC cap. Any renewed war interrupts civilian construction, even if peace returns before its finish. On failure, the original money, supplies and all workers return once. Reserve training can finish during a new war if Japan remains independent and controls Tokyo. If that fails, its investment returns once. No ongoing manpower or production modifier is added.

Cascade: `civil_recovery` -> `r14_civil_recovery_civilian` (360 days) **or** `r14_civil_recovery_reserves` (180 days). `r14_home_work_interrupted` remembers renewed war without opening a window.

## 2. China's and India's postwar agreements (1947 onward)

Replaces `china_autonomy` and `india_autonomy`, preserving their event numbers and the explicit sovereignty option. China means the U87 government; India means IND. The country must exist and be Japan's puppet. One agreement closes all alternatives for that country.

| Choice | Japanese investment | Partner's benefit and obligations |
| --- | --- | --- |
| Sovereignty and civilian aid | 250 money, 3,000 supplies | Ends Japanese puppet status immediately; existing alliance is retained; renews Japanese access; four local IC and 3,000 supplies after 360 days |
| Present treaty and civilian recovery | 250 money, 3,000 supplies | Remains a puppet; renews Japanese access; four local IC and 3,000 supplies after 360 days |
| Present treaty and standing-army support | 250 money, 5,000 supplies | Remains a puppet; renews Japanese access; 80 local manpower and 5,000 supplies after 180 days |
| No new grant | Nothing | Existing relationship remains; no reward; closes the offer |

Civilian agreements can be selected only while Japan is at peace. Partner acceptance happens after one day. The military agreement funds the **partner's** army, not Japan's manpower pool. Access enables use of existing bases; no territory is transferred, no new bases are confiscated, and no country is put into a new alliance or war.

Civilian factories are built in Nanjing (1337) or Delhi (1459), only if the recipient still owns/controls the site, has technology 5800, infrastructure above 30 percent and capacity below the IC cap. The government must remain in the chosen relationship and at peace. A new war during construction invalidates the civilian delivery even if peace returns later. Standing-army training requires the puppet relationship to survive and no war against Japan.

Cascade per country/policy: existing autonomy offer -> `r14_<country>_autonomy_<policy>` acceptance at one day -> `_finish` at 180/360 days. An unreceived acceptance is checked at two days, returning Japan's investment if the government has disappeared or rejected the relationship. A failed later completion also returns the full original Japanese investment once. If the recipient is annexed after accepting, a Japanese-owned due-date check returns the investment and closes its foreign completion; recreating that country cannot collect the cancelled award. The political choice is not reversed by a refund. Hidden `_check`, `_refund`, `_government_lost` and civilian `_interrupted` events handle these failures. Old direct access/grant receivers remain at their IDs but cannot grant unfunded rewards.

## 3. America across the Pacific (1945 onward)

New decision `r14_american_future` requires verified `JX_US_PEACE`, an existing USA, no Japanese-American war, and **360 days since `us_signed`**. A broken armistice permanently closes this postwar offer. The verified Hawaii treaty choice determines which agreement is available.

| Treaty outcome | Investment | 180-day result |
| --- | --- | --- |
| Hawaii returned | 600 money, 3,000 supplies | A finite shipment of 12,000 oil, 12,000 metal and 6,000 rares; American exporters receive the payment |
| Hawaii retained | 400 money, 5,000 supplies, 3,000 oil | Three coastal-fort and three anti-aircraft levels at Pearl Harbor (1734), plus 3,000 supplies |
| No new agreement | Nothing | Keeps the existing treaty; no reward; closes the offer |

Retained Hawaii must still be Japanese-owned/controlled and have room for both building additions. American-Japanese war invalidates either agreement and returns the investment; the interruption is remembered even if peace returns before delivery. Fortification also prompts the USA to spend **its own** 400 money and 5,000 supplies for 120 convoy transports and 80 escorts, if it can afford them. These are shipping pools, not map warships. No event declares war or alters another alliance.

Cascade: `r14_american_future` -> `r14_r14_american_future_commerce` or `_hawaii` (180 days) -> American `r14_us_export_receipt` or `r14_us_pacific_rebuild` (one day). `r14_armistice_broken` records renewed war once. Native cancellation/refund branches replace delivery when conditions fail.

## Offline checks and limits

Run `python r14_afterwar_review.py`. Tests cover both partners and all three funded policies; actual factory construction; workforce return and insufficient manpower; finite reserve training; early/cached/replayed actions and callbacks; decline without rewards; vanished partners and occupied capitals; dated US treaty eligibility; opposing Hawaii policies; renewed war/refunds; remembered brief wars; American payment and escort spending. Existing event numbers are asserted unchanged.

The tests execute the compiled command contract in the repository's state model. They cannot prove engine presentation, native scheduling, diplomatic access or building-cap behavior in a live game. The user retains that final playtest. There are no new percentage modifiers, recurring grants or unit types here, and no save migration.
