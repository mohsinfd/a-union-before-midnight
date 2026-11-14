# Japan Rising - JX 1.1 ALPHA 2 R14

Current release: **R14**. See [R14_CHANGES.md](R14_CHANGES.md) for the complete cold-review repairs, tougher Chinese surrender, coalition-safe peace and postwar continuation. Start a new 1933 campaign. No game was run; source and installed checks do not certify long-campaign stability.

Use the existing **Japan Rising JX1 Alpha2** shortcut/folder and start a **new 1933 campaign as Japan**. Confirm **R14** in the scenario name and welcome event. This is a human-Japan expansion on Blood and Iron. The historical diplomatic opening through Pearl Harbor remains, followed by independent campaign choices through 1950. Existing saves are not migration targets for this revision.

R13.1 improves initial enemy transport protection and future escort construction; see [R13_1_CHANGES.md](R13_1_CHANGES.md). A portable installer supports another Windows PC using your own game and Blood and Iron folders.

R13 adds three further naval/air specialists and a full-strength Expeditionary Assault Division. All four have automatic free first issues, ordinary researched upgrades, affordable construction and distinct artwork. The existing heavy-submarine family is preserved. See [R13_UNITS.md](R13_UNITS.md) for costs, roles and unlocks. The four are installed; the older proposal document below is retained as design history.

R12.1 repairs all six specialist introductions for delayed human follow-ups, preserves the island garrisons, adds one finite 180-transport/90-escort allowance to their first call-up and expands the paid merchant programme. See [R12_1_CHANGES.md](R12_1_CHANGES.md). The earlier proposals in [FURTHER_JAPANESE_SPECIALISTS.md](FURTHER_JAPANESE_SPECIALISTS.md) were superseded by R13.

R12 adds six Japanese specialist formations and attachments, with automatic free first issues, researched upgrades, distinct illustrations and existing production, doctrine and minister support. See [R12_UNIQUE_UNITS.md](R12_UNIQUE_UNITS.md) for dates, research requirements, quantities, roles and costs. All first issues cost no national money, manpower or supplies. Further copies use normal production. No game was run during development or the independent cold audits; engine behaviour and campaign balance still need your playtest.

R11 incorporates three independent cold reviews of resources, military production and country/event flow. Japan's own AI was not developed. The separate Germany Overhaul installation and all saved campaigns were not edited. Source and installed-file checks are offline; the game is not launched by this work.

## Final R11.1 audit

The final cold audit found engine rules that the earlier tests missed. Empty decision readiness could disable manual choices; landing trials could set the assault limit to one instead of adding one. R11.1 fixes both, tightens choice and delivery-date checks, and distinguishes current damaged infrastructure from a city's undamaged capacity.

Paid formations now receive explicit, individually targeted full-strength delivery. Aircraft and ships require a maintained airfield or port, with refunds when the site cannot be used. Organisation needs time to recover; existing small island detachments retain their planned strength.

The Alpha2 desktop launcher accepts the current validation record and verifies its version and destination. R12 retains the R11.1 corrections below; see R11_1_FINAL_AUDIT.md for their evidence.

## R11: more to play through

All 383 Japanese minister appointments were checked against their 90 actual traits, offices, commands and localisation. There are no unresolved traits or Generic fallbacks. The 13 custom descriptions are now generated from their command data, including exact Fleet Carrier, equipment-research and resource scopes. See MINISTER_INTEGRITY_AUDIT.md.

Six new prewar programmes open in April 1933, June 1934, February 1935, May 1936, March 1938 and January 1940. Choose rural industry or reserves, flight-deck training or protected carriers, navigation equipment or city AA, landing organisation or assault training, medical recovery or recruits, and dispersed protected factories or concentrated output. Each is optional, paid and finite. PREWAR_CONTENT.md lists every bill and consequence.

China now has Shanghai port-holding and Wuhan interior-campaign choices. Existing Chinese partner aid starts in 1938; expedition/home-defence and reconstruction start in 1939 after actual puppeting. The military aid provides Chinese recruits and equipment, with no unfunded unit order.

The Philippines adds an aircraft deployment choice at Manila and a post-treaty soldiers/shipping agreement. Indonesia adds Destroyer/Light Cruiser commissioning at Soerabaja and finite oil/mineral export missions. Malaya adds Singapore spare-parts/merchant replacements and rubber/tin versus fuel-feedstock contracts. These programmes reserve complete bills including actual unit manpower; loss of the required position returns paid inputs. Neutral treaties qualify only for stated civilian alternatives. See COUNTRY_CAMPAIGNS.md.

A mainland American invasion now has eight additional encounters: the first landing, two American reserve responses, Japanese replacements, the California corridor, a choice about sustaining the inland campaign, a finite US endurance budget and the Denver/Kansas City milestone. US formations use safe American-owned rear hubs and cost actual US manpower/supplies. Existing peace terms remain separate. See US_CAMPAIGN_CONTENT.md.

## What to do in a fresh campaign

- From 1933, decide whether to fund industry, army production, the supply network, shipping or strategic storage. Leaving a decision available costs nothing. You do not need to purchase everything.
- From 1934, fund **Build an air force Japan can afford**. Both choices improve all six land-based aircraft types; the chosen role receives the larger reduction. Carrier air groups remain part of the naval programme.
- From 1935, choose the first **home fuel and minerals complex**. Balanced industry is the safer mixed-force plan. Fuel priority assumes that imports or conquest can cover more of the metal/rare-material demand.
- Build normal Infantry, Mountain Infantry, Marines and Garrisons. All three experimental classes are retired; the army tooling now supports full Marines.
- From 1940, while at war and after the first complex, fund the larger wartime fuel/mineral expansion. Keep enough stocks for setup and daily operations.
- Keep the historical Blood and Iron diplomatic choices through Pearl Harbor for the intended opening. The new production priorities do not select an alliance or close unrelated wars.
- During the wider war, reserve call-ups support replacement and new construction. Fund the normal reinforcement slider; the extra manpower is not a free completed army.
- Country settlements now appear as **named country decisions** when their conquest conditions are met. They do not automatically interrupt play. Open the country's card to choose puppet/base/neutral terms. Leaving it available does not make peace or spend resources.

## Three independent production priorities

Army (1933): 150 money, 900 supplies, 180 days. Choose infantry/mountain/marine production, or motorised/cavalry/armour production with +10% TC. The event lists exact fixed IC and day reductions.

Air (1934): 180 money, 1,000 supplies, 180 days. Every aircraft type below receives at least **-1.5 IC and -18 days**. The selected priority receives these larger TOTAL reductions instead:

| Priority | Aircraft | IC removed | Days removed |
| --- | --- | --- | --- |
| Fighter | Interceptor | 3.5 | 42 |
| Fighter | Multirole fighter | 4 | 42 |
| Fighter | CAS | 4 | 46 |
| Bomber | Tactical bomber | 5 | 46 |
| Bomber | Naval bomber | 4 | 48 |
| Bomber | Transport aircraft | 5 | 48 |

These are country-specific fixed reductions for future normal orders. Native technology, ministers, policy and gearing still apply. The engine uses model 0 for relative modifiers; R11 shows explicit IC/day awards to avoid misleading percentages. No zero-strength production orders or free aircraft are inserted.

Naval (1935): 220 money, 1,200 supplies, 240 days. Choose carrier/CVL/air-group production or destroyer/light-cruiser/submarine production. The event lists the fixed awards. Native conversions remain available. Extra hulls still need screens, fuel, research and normal production.

The supply network provides +15% supply production and +15% TC, competing with the existing four-IC industrial alternative. From 1939 at war, a repair service costs 220 money and 1,400 supplies over 120 days for +25% reinforcement efficiency across Japan's three services. It improves normal reinforcement spending; destroyed formations are not recreated.

## Fuel and minerals that can support the factories

Both existing fuel cards now represent integrated coal extraction, mineral processing, recycling and refining. These are deliberately substantial ahistorical expansions. Only one alternative per stage can be completed. Provincial increments below are BEFORE resource efficiency:

| Stage | Payment / wait | Balanced industry | Fuel priority |
| --- | --- | --- | --- |
| 1935 home complex | 350 money, 2,400 supplies, 1,000 metal / 240 days | +160 energy, +40 metal, +10 rares, +20 oil | +200 energy, +20 metal, +35 oil |
| 1940 wartime complex, first stage completed | 500 money, 3,600 supplies, 2,000 metal / 270 days | +320 energy, +90 metal, +30 rares, +25 oil | +400 energy, +40 metal, +10 rares, +50 oil |

Each stage also redirects 20 daily energy output from Yokohama. Tokyo, Yokohama and the named northern works must remain owned and controlled at completion. A failed site check returns the exact payment. The completed output stays with its provinces if they are lost. There are no repeatable factory/resource grants.

Illustrative planning budget: both balanced stages give about **651 energy, 151 metal, 81 rares and 42 oil per day**, using the source territorial factors and 0.9 resource efficiency, before other technologies, imports and conquests. At 150 effective IC, industry takes 300 energy, 150 metal and 75 rares. This leaves enough energy for a sustained large fuel-batch cycle; metal and rares have little spare room. Fuel-priority stages yield more oil/coal but need about **62 metal and 21 rares daily from elsewhere at 150 IC**. A first-stage-only 100-IC economy still needs metal imports. See ENDURANCE_AUDIT.md for the full assumptions.

### Imports, storage and overflow

The 1933 import decision offers 24 oil plus 12 metal daily, 48 oil daily, or a smaller 8-oil contract. Later 24-oil agreements remain available. These are ordinary **cancellable trades**. Cancel the specific agreement through Diplomacy when it is no longer useful; its handling fee is spent and ongoing payments stop. War, embargo, expiry or poor trade delivery can stop supply.

The inherited rule destroys **50% of oil ABOVE its stockpile limit each day**. The strategic-storage project (100 money, 800 supplies, 90 days) adds 200 percentage points to Japan's oil-and-supply stockpile modifier in peace and war. Oil and supplies are grouped by the engine. This does not promise an absolute storage volume or change provincial depot caps. Check the displayed cap; no selective automatic trade pause is claimed.

### Repeatable wartime fuel orders

| Packet | Payment | Additional prerequisite |
| --- | --- | --- |
| 1,500 oil | 3,000 energy, 200 supplies, 25 money | Oil below 1,500 |
| 6,000 oil | 12,000 energy, 800 supplies, 100 money | Storage and first works completed; oil below 6,000 |
| 12,000 oil | 24,000 energy, 1,600 supplies, 200 money | Storage and wartime works completed; oil below 12,000 |

Each order must leave at least 9,000 energy unspent. Delivery takes 45 days, then another 45 days before a new order. Only one packet can be pending. The delivery offers the oil or an exact refund of the paid inputs, with the same cooldown. Above its low-stock threshold only cancellation remains available. The actual dynamic storage cap cannot be measured by these events, so inspect it before accepting. A small packet is available for a low-capacity economy.

The large packet averages 133 oil/day and consumes about 267 energy/day, plus 17.8 supplies and 2.2 money daily over its 90-day cycle. This is a funded emergency conversion, not free oil. Native conversion uses the same coal and is excluded from the assured planning budget. The three developed occupied southern fields add roughly 42 effective oil/day under the audit assumptions, and still require shipping.

The latest old save's force templates total about 442 oil/day if everything operates at its saved template rate. That is not an observed daily ledger. A worked rotation of 30% land movement, 40% naval operation and 30% air activity is about 165/day before combat and other effects. Both balanced works plus sustained large packets supply about 176/day before conquest/imports, or about 217/day with those three developed occupied fields. Operating the entire expanded force continuously remains expensive.

## Recruiting and replacing a larger army

The reserve programme opens from 1941 after the Pacific war begins, or during a Japanese-Soviet war. It gives an explicit **160 manpower** and **+0.65 daily manpower for five years** (about 237/year), plus +12% wartime IC. Later waves give **140** and **120 manpower**, with their 1942/1943 dates and at least 300 days between waves. The last adds another +8% wartime IC.

These replace the earlier ambiguous fractional provincial-manpower awards. They create no units and do not change native mobilisation-law effects. The five-year supplement ends exactly once; normal recruitment continues. Native recruitment, casualties, repair spending and your production choices still determine the army you can sustain.

## Units, ministers and research

The three custom classes are retired from recruitment. Their lower strength per command/landing slot made the claimed advantages unconvincing. Ordinary island Garrisons remain. Unit slots and IDs stay registered for data compatibility. The army infantry priority now supports full Marines (-1.6 IC/-63 days), Infantry (-1 IC/-43.5 days) and Mountain Infantry (-1.2 IC/-43.5 days).

From 1937 you may appoint **Fujiwara Ginjiro (Civil Works)** as Armaments Minister. While appointed: infrastructure IC cost and time -12%; factory IC cost and time -5%; naval division construction time +4%. The old R9 version changed time only. The original Administrative Genius Fujiwara remains a separate policy; it does not have these discounts. These are appointment effects, not an automatic construction event.

The ten added research entries now use real Japanese names in romanisation, including Kaigun Daigakko, Rikugun Hohei Gakko and Gunjusho. See RESEARCH_NAMES.md for every name, role, availability date and archival sources. The total is 64 across all dates; ten new teams are not immediately available in 1933.

Japan's borrowed d_01 Guards recruitment also remains retired; it caused the SS Infantry label.

## Event flow

The R7 cleanup retired 35 weak/redundant offers, including 26 old decision cards. R11 retires another seven small-stat early offers. Useful imports/procurement are manual choices, while the historical Tomozuru and typhoon stories remain. Closing a manual proposal leaves it available without scheduling a quarterly reminder.

All 17 country settlement offers are manual. Successful settlement uses two fewer Japanese callbacks, preserves necessary creation/commit delays, and gives a final checked result. Some engine callbacks can still display; complete silence is not claimed. Stale callbacks, duplicate payments/refunds and repeated regional grants have state guards. Failure retries wait 30 days and re-enter preparation rather than looping verification every few days. Dismissing a settlement keeps the current borders and relationships.

## What has been checked

Three cold agents reviewed independent areas and implemented fixes. Tests cover the funded resource plans, all three packet sizes, refunds and duplicates; shared versus priority aircraft rebates and specialist minister effects; manual triggers, reminders, country terms and regional receipts; explicit recruit amounts, wave spacing and five-year expiry. Existing event IDs remain stable. Construction arithmetic includes native assembly effects and excludes retired offers.

These checks execute models and inspect installed files. They do not run Darkest Hour. Actual UI, save/reload, convoy routing, battle performance and sustained Hard campaign balance still require the player's test. R11 is prepared for a new-campaign playtest; a guaranteed crash-free or balanced multi-year campaign is not claimed.