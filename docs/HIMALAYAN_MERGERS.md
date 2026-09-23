# Nepal and Bhutan: offers, retries and national status

10 September 2026. Bhutan extends the staged Nepal lifecycle. Neither the new
retries nor delayed integration changes are installed or engine-playtested.

## Acceptance odds

| Offer | Nepal | Bhutan | Both accept, if both offers are valid |
| --- | ---: | ---: | ---: |
| Ordinary offers | 45% | 60% | 27% |
| Grand dual offer | 60% | 75% | 45% |
| Funded retry after refusal, staged only | 65% | 80% | 52% |

These are independent fixed AI response weights, not relation-based diplomacy
rolls. Relations, army size, IC, guarantees and pressure flags do not improve
them. Probabilities assume both countries still exist, the proposals remain
valid and the AI controls their replies. A human-controlled kingdom can choose.

The grand offer costs 500 money, 750 supplies and +2 dissent. It now requires
both kingdoms to be eligible before payment. Ordinary first invitations cost
275/400 for Nepal and 200/300 for Bhutan (money/supplies). The later ordinary
mission to the other, unresolved kingdom costs 325/450 or 250/350 respectively;
it does not improve the ordinary odds.

After a refusal, wait 360 game days before a funded retry. Each retry costs
650 money, 1,000 supplies and +2 dissent for that kingdom, with no refund if the
talks lapse. Bhutan's new 80% retry preserves its higher willingness compared
with Nepal's existing staged 65%. A further refusal permits another paid retry
after another 360 days. Both countries must be at peace, and rival-master cases
are blocked. British puppetry remains allowed under the authored starting
context, but the engine/master consequences still require native verification.

With the grand offer, followed by one funded retry for each kingdom that refuses,
the mathematical chance both eventually accept is **81.7%**:
Nepal 60% + 40% × 65% = 86%; Bhutan 75% + 25% × 80% = 95%; 86% × 95% = 81.7%.
This is not a guaranteed in-game outcome or a claim that the engine has been tested.

## Merger and national territory

Both kingdoms now use the same lifecycle implementation, with independent flags
and callbacks. The ordinary/grand refusal and acceptance events retain their
original probabilities and choices. Bhutan's original +5 manpower / -1 dissent
merger reward is preserved, but paid only after inheritance actually succeeds;
Nepal retains +20 manpower / +1 dissent. Neither immediately grants a core.

- A verified voluntary merger starts an elapsed **1,080-day** integration period.
- Conquest alone gives no national province. After annexation, invest **1,500
  money, 2,500 supplies and +5 dissent** to start an elapsed **1,800-day** period.
- At maturity, India must own and control the province and the old country must
  remain absent. Otherwise a completion decision waits for those facts to return;
  no second payment or fresh timer is required.
- Only **Kathmandu 1457** and **Thimphu 1456**, respectively, become national
  provinces. The timers do not represent uninterrupted occupation.
- Refusal followed by military enforcement grants a claim, not an immediate core.

New Bhutan IDs: 9398210–9398216. They were checked against authored and installed
custom event definitions before allocation. This is fresh-campaign work; no
existing save's cores, borders or completed actions are altered.

Focused script tests cover separate simultaneous replies, current-state checks,
prices, cooldowns, verified rewards, both delays, lost-territory recovery,
idempotence, ID collisions and text budgets. They do not execute inheritance,
simulate the native clock, or certify save/reload callback persistence.

Verification for this extension: **14 Nepal + 11 Bhutan + 9 integrated-build
tests passed (34 total)**. The previous full 214-test run belongs to the preceding
Stage5 build, not this extension; it has not been represented as a new full-suite
run. No game was launched and no save or installation was edited.
