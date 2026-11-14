# R15: recover after a lost battle or anchorage

Two finite Japanese recovery choices respond to real setbacks. They do not grant free hulls, change wars, or impose permanent percentage modifiers. The carrier programme is an explicitly paid emergency commissioning project. Starting either project occupies the shared major-investment slot until its dated completion, exact failure refund, or voluntary cancellation. While work is pending, the same card offers a stop-work option: all reserved manpower, oil and metal and 75% of supplies return; money and 25% of supplies remain spent. Stopping permanently ends that plan and frees the shared slot for another emergency. These are decisions, not recurring automatic demands. Leaving one available costs nothing; permanent dismissal closes it.

## The carrier force has been broken

From 1942, after the Pacific opening, Japan must still be fighting America or Britain, have lost at least three fleet carriers over the campaign, and currently have fewer than four fleet carriers. Light/escort carriers do not satisfy the loss test. The engine's loss count is cumulative; it is not described as losses in the last battle. Recovery of carrier numbers before completion does not cancel a paid project.

| Choice | Paid immediately | Time | Outcome |
|---|---|---|---|
| Commission two Light Carriers and escorts | 500 money, 14,000 supplies, 4,000 oil, 3,500 metal, 10.14 manpower reserved | 330 days | Two researched Light Carriers and four researched ordinary Destroyer flotillas at Tokyo, two researched Light CAGs in the deployment pool, and the reserved 4,000 oil. The six ships assemble in one fleet. Fit the pooled air groups before combat. Unused reserved crews return. |
| Fight from the land airfields | 250 money, 6,500 supplies, 1,500 oil, 1,500 metal, 5.4 manpower | 180 days | Two researched ordinary Naval Bomber wings and one researched Multirole Fighter wing at Tokyo. These are land-based aircraft; none can become a CAG. |

Both outcomes use the newest researched equipment whose service year has arrived. Full native crews are paid. The fleet branch reserves the maximum dated 1950 crew total 10.14 manpower (two Light Carriers 3.6, four Destroyers 6.4, two Light CAGs 0.14), then returns any surplus according to the exact delivered models. Each Naval Bomber needs 2.2 and the modern fighter 1 manpower. New map units receive targeted strength restoration up to their actual allowed maximum; organisation recovers normally. The carrier option needs a working Tokyo port, the shore-air option a working Tokyo airfield. Both require continued war with America or Britain, human independent Japan, and Japanese ownership/control of the assembly site at completion. Invalid completion refunds every original input and creates no equipment.

The naval option is slower and consumes more industrial stocks, but provides a usable two-carrier mobile striking group. The delivered oil was reserved at funding: there is no net fuel grant. The shore option arrives five months sooner at a lower economic cost, uses fewer recruits, and remains dependent on useful land airfields. The actual normal Light Carrier templates take 1,200–1,300 base days; emergency commissioning trades a large prepaid stock commitment for earlier completion. It is not a free replacement for sunk fleet carriers. Selecting one closes the competing outcome.

## An important anchorage has fallen

After the Pacific opening, daily silent checks remember Japanese control of Truk, Rabaul, Singapore and Hawaii. Four silent daily checks record the first actual hostile capture of a previously held position. They derive eligible country tags from the native revolt definitions and every 1933 country file, so Dutch, French, British Indian, Philippine, Soviet and other actual hostile controllers qualify. The capture is verified against a current war with the actual controller. The public card uses the recorded loss; recapturing the base does not erase this one-time recovery choice. Peacefully returning Hawaii under the R14 treaty cannot qualify. The decision lists the covered positions and asks for one response. A specific silent flag records which base first qualified. No transfer, annexation, neutral occupation or allied-control assumption substitutes for a verified hostile capture.

| Choice | Paid immediately | Time | Outcome |
|---|---|---|---|
| Protect the remaining sea routes | 150 money, 3,500 supplies, 1,000 oil | 90 days | 160 convoy transports, 100 convoy escorts, 5,000 supplies and 2,000 oil. These are national shipping pools, not troop transports or warship flotillas. |
| Prepare a force to return | 300 money, 6,000 supplies, 2,000 oil, 1,000 metal, 15.5 manpower | 180 days | One researched full Marine division and one researched naval Transport flotilla at Tokyo, plus 2,000 supplies. The player must plan and execute the counterattack. |

The fast shipping choice helps sustain a shorter perimeter and protect remaining forces. The counterattack choice commits many more men and industrial stocks to offensive capability; it is not a teleport back to the fallen base. If the anchorage is retaken during training, the paid programme can still complete while the wider war continues. Losing Tokyo or ending the relevant naval war refunds the exact payment. A funded attempt closes this recovery chapter even after a refund; ordinary production remains available.

## Safeguards and scope

- All preceding event IDs remain unchanged; these events append after R14.1.
- Both projects share `JX_R15_MAJOR_PENDING` with other R15 commitments. Their own pending receipts alone authorise clearing that lock.
- Every funded action rechecks resources and the current situation at command execution; a private receipt prevents its own debit from cancelling later commands in the same accepted transaction.
- Delayed outcomes require the private funding clock's saved date, the selected option, the full elapsed time, the actual pending receipt, current site and war eligibility, and no previous completion. Early, duplicate, wrong-option and cached execution are inert.
- Latest-equipment alternatives are mutually exclusive. Full-strength restoration carries exactly the same researched/year condition as each birth.
- There are no new specialist types, global stat bonuses, claims of guaranteed fleet tactics, scripted invasions, forced wars, or country/territory changes.
- A player can decline or permanently dismiss either recovery investment. Normal production and the existing R14 reinforcement/manpower systems remain available.

Offline tests cover trigger thresholds, actual prior control and hostile loss, peaceful handovers, all funded branches, replay, early completion, changed war/site, insufficient budgets and shared-lock conflicts. Real carrier combat, deployment rendering and convoy allocation remain player tests; the game is not run.
