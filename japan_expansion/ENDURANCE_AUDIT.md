# Endurance economy cold audit and implemented correction

Read-only evidence: Blood and Iron v1.1 files, the actual Germany Overhaul Campaign event files, and Japan Rising's latest autosave (1 November 1942, SHA256 recorded in ENDURANCE_AUDIT.json). No game launch, save edit, installation, or Germany edit.

The save has 0.0019 manpower, 3,107 oil, 53,115 energy, 21,020 metal, 17,395 rares, 9,336 supplies and 127.84 money. Its 121 land, 186 naval and 25 air formations have saved template oil consumption totaling 441.96/day before duty and combat adjustments. This is not a measured daily burn: stationary land uses 0.1, port/base aircraft and ships 0.01; combat changes consumption again. The shortage is credible; the save does not prove the exact historical rate of depletion.

## What changes

`endurance_economy.apply()` must run immediately after `human_campaign.apply()`, before final ID/reference indexing. It revises the two existing fuel cards rather than adding another family of decisions. All prior event IDs remain stable. Three receivers are appended: alternate home works, alternate wartime works, and a small fuel batch. Existing project output is replaced, not awarded again. New campaign scope; existing saves are not migrated.

Both stages are substantial, explicitly ahistorical coal extraction, mineral processing, recycling and fuel infrastructure. Provincial resources remain tied to their sites, territorial efficiency and shipping. Northern resource sites are 1544 and 1545; fuel is at Tokyo (1552), with the existing energy reallocation at Yokohama (1550). Both sites and the relevant northern mine must be Japanese-owned and controlled at commissioning. Invalid commissioning refunds the actual money/supply/metal investment once and grants no output.

| Stage | Cost now | Delay | Balanced provincial additions E / M / R / oil | Fuel priority additions E / M / R / oil |
| --- | --- | --- | --- | --- |
| Home works, 1935 | 350 money, 2,400 supplies, 1,000 metal | 240 days | 160 / 40 / 10 / 20 | 200 / 20 / 0 / 35 |
| Wartime expansion, 1940+, at war, home stage completed | 500 money, 3,600 supplies, 2,000 metal | 270 days | 320 / 90 / 30 / 25 | 400 / 40 / 10 / 50 |

Each stage also subtracts 20 provincial energy at Yokohama. The source gate retains 500 metal after payment. Each stage is a single, exclusive choice. Mixed paths work; the table below shows the two endpoints.

The original stock conversions remain available at their existing costs and 45-day delivery plus 45-day cooldown. A small 1,500-oil batch costs 3,000 energy, 200 supplies and 25 money. It uses the existing card, replacing its redundant no-op action; the card can simply be ignored. Standard and large batches require strategic storage; standard also requires home works and large requires the wartime expansion. Every order must leave 9,000 energy unspent, rather than consuming the last factory feedstock. Batch sizes remain 1,500, 6,000 and 12,000 oil.

Orders and acceptance require current oil below their own batch size. At delivery an exact-input cancellation is always available while pending; if the threshold is exceeded, cancellation is the only available action. Receiving or cancelling clears pending and begins the same cooldown. This prevents repeated refunds or fuel awards. A prepaid order may finish in peace.

The native cap is dynamic and cannot be read with the event contract. Low-stock thresholds and a smaller batch reduce waste; they do not prove that 1,500 or 12,000 oil fits. Acceptance explicitly tells the player to check the displayed storage limit, with exact cancellation available if it does not fit. No arbitrary unlimited stockpile, off-map oil income, or global misc change is introduced.

## Reproducible resource budget

1933 owned/core membership and actual Map_1 province data give territorial raw E283.6 / M37.6 / R49.6 / oil2.0. B&I starts the four resource production efficiencies at 0.9, giving E255.24 / M33.84 / R44.64 / oil1.8. These illustrative budgets exclude every other JX industrial reward, technology/minister changes, imports, conquest and native conversion. They therefore do not quietly add another award on top of existing projects. Country modifiers, damage and convoy delivery change actual results.

| Completed path | Effective IC budget | Daily E / M / R / oil | Metal/rares balance after industry | Energy after industry + standard batch | Energy after industry + large batch |
| --- | --- | --- | --- | --- | --- |
| Home, balanced | 100 | 381.24 / 69.84 / 53.64 / 19.80 | -30.16 / +3.64 | +47.91 | unavailable until wartime stage |
| Home, fuel | 100 | 417.24 / 51.84 / 44.64 / 33.30 | -48.16 / -5.36 | +83.91 | unavailable until wartime stage |
| Both, balanced | 150 | 651.24 / 150.84 / 80.64 / 42.30 | +0.84 / +5.64 | +217.91 | +84.57 |
| Both, fuel | 150 | 759.24 / 87.84 / 53.64 / 78.30 | -62.16 / -21.36 | +325.91 | +192.57 |

Industry uses 2 energy, 1 metal and 0.5 rares per effective IC. Standard conversion adds 133.33 energy/day on average; large adds 266.67. Oil delivered averages 66.67/133.33 daily. The large batch also costs 17.78 supplies and 2.22 money/day on average: about 4.44 supply IC and 11.11 gross consumer-goods IC at the unmodified 4 supplies/IC and 0.2 money/IC rates. Research and ordinary forces require additional supply/money budgets. This is a real continuing operating cost.

The balanced endpoint supplies raw materials for approximately 150 effective IC; further industry needs further trade/conquest. Fuel priority supports only about 88 IC on its own metal, and needs 62.16 metal and 21.36 rares imported or obtained from overseas to operate 150 IC. It is intended for an expansionist player who captures and convoys minerals, not a second self-sufficient choice with extra oil.

Prewar metal imports remain essential. After the first balanced stage, 100 IC still needs 30.16 metal/day before other projects. The existing 12-metal contracts help but do not make factories self-sufficient. The player must use normal trade, conserve factory expansion, or obtain overseas feedstocks. Home energy is no longer the hidden time bomb it was in R8.

## Affordability and lead time

B&I starts Japan with 100 money, 500 supplies, 1,000 metal, 1,000 energy and 500 oil. The first works are deliberately unavailable immediately. Ignoring all other spending, accumulating its additional 250 money costs 1,250 gross consumer-goods IC-days at 0.2 money/IC; adding the missing 1,900 supplies costs 475 IC-days at 4 supplies/IC. The 500-metal post-payment reserve also requires additional metal accumulation. Over the two-year 1933-35 preparation window, 250 additional money is a net saving target of approximately 0.35/day. Research, storage, trade fees, army programmes and daily imports increase the actual requirement. Defer optional programmes rather than promise that all cards are affordable simultaneously.

The second stage costs another 500 money, 3,600 supplies and 2,000 metal; it has five years to prepare its money/metal fund before 1940. Its supply cost is 900 unmodified IC-days; 500 money is 2,500 gross consumer-goods IC-days. Funding in early 1940 while already at war in China can commission it before Pearl Harbor. Waiting until Pearl Harbor means a nine-month vulnerable period: the first stage, prewar reserves, standard conversions and actual captured oil must bridge it. Stage two is not an instant emergency grant.

## Fleet duty and captured oil

The three chosen oilfield sites have base output of only 6 (Palembang), 3 (Borneo) and 2 (Java). All three 20-output options yield `(11 + 60) * 0.65 * 0.9 = 41.535` daily if occupied and fully shipped. Medan's 5 base oil contributes another 2.925 under the same assumptions. Annexed non-core resource efficiency is 0.8 instead of occupied 0.65. Puppet output is not guaranteed income: misc.txt transfers only stocks above 1.2 times the puppet's own critical reserve, and shipping must work. No puppet surplus is included in the assured budget.

Using the actual autosave's force templates, an illustrative rotation with 30% of land formations moving, 40% of ships operating and 30% of aircraft flying, with the rest stationary/in port, consumes approximately 165.06 oil/day before combat multipliers. This is a planning scenario, not an engine result or suggested daily micromanagement. Balanced works + a large batch cycle + the three developed occupied fields provide roughly 217.17 oil/day, excluding native conversion and all other oil. Fuel priority provides roughly 253.17. Both cover that rotation with a margin, provided the batch inputs and convoys are sustained. Neither promises to support every formation continuously in combat; land combat multiplies fuel by 1.25, naval combat by 2 and air combat by 1.5.

Native industry technology already grants energy-to-oil conversion modifiers. The autosave contains `energy_to_oil = 0.25`; the game's local command documentation describes the conversion multiplier contract. This correction deliberately changes neither it nor the global conversion settings. Native conversion draws from the same coal margin and is excluded from guaranteed oil totals, avoiding double counting an engine-dependent contribution.

## Germany evidence and verification

The actual Germany Overhaul Campaign `db/events/GMO/synthetic_fuel_agency.txt` commits and commissions a regional works for a total 2,500 metal and 2,500 supplies over at least 540 days, with ownership, control, industry and technology checks. The output is six provincial oil for twenty provincial energy. `industrial_endurance27.txt` allows a low-energy player to write off that allocation and restore its coal, without returning the sunk investment. `wartime_input_security.txt` negotiates cancellable Romanian oil for a continuing energy or supply cost and permits supplier refusal. These support funded physical capacity and ongoing-input choices; their small historical scale would not solve this Japan campaign's much larger force economy. No German events, country AI, political tree or global unit rescale were copied.

Run `python japan_expansion/ENDURANCE_review.py`: seven focused tests cover all four works choices, exclusive completion, mine-loss exact refunds, three packet charge/delivery/cooldown paths, insufficient inputs and energy reserve, storage/site prerequisites, peace, changed-stock cancellation, duplicate receipts and idempotence. Run `ENDURANCE_audit.py` to regenerate the read-only evidence and arithmetic JSON. These tests exercise event contracts, not the engine economy. Multi-year Hard balance, actual convoy performance, dynamic cap behavior and sustained combat attrition still require a player test. Manpower and force replacement changes belong to the separate campaign integration.
