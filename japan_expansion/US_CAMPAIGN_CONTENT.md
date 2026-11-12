# A continental American campaign for human Japan

## Scope and integration

`us_campaign_content.append_events()` appends **17 event IDs** for **eight substantive campaign encounters** and nine completion/cooldown/report receivers. Call it last, after the existing content passes and before refreshing `build.IDS`. It changes no existing event, war, peace, ownership, core, AI file, country or unit template. Its `REPORT` includes the final appended ID map; the builder's generated registry remains authoritative if other new modules append earlier.

All encounters start from 1941, require human-controlled independent Japan, AI-controlled USA, the active expansion, an existing Japanese-American war and a Japanese-held major Pacific coast port. The first captured-store milestone additionally requires that America legally owns the captured port. Nothing in 1933–1940 or the historical diplomatic opening is changed. These events declare no war and provide no new peace flow.

The existing occupation-safe `american_base` supply/convoy project remains intact. This content complements it with replacements, captured stores, campaign scope and an American ground response. It creates **no additional Japanese convoy programme, completed Japanese units, permanent industrial bonuses or daily free resources**.

## Encounters and cascade

| Entry | Actual opening condition | Concrete result |
| --- | --- | --- |
| A foothold on the American mainland | From 1941; Japan controls American-owned San Diego, Los Angeles, San Francisco or Seattle, once | Choose 3,500 supplies, or 1,500 supplies plus 1,000 oil. Records the first landing date. The captured port remains American-owned. |
| America calls a continental defence reserve | First landing recorded; AI America still at war with human Japan and a listed port remains Japanese-held | Six American infantry divisions at the first safe American-owned **and** American-controlled hub: Denver, Salt Lake City, Phoenix, then Kansas City. Costs America **78 actual manpower and 2,400 actual supplies**. A separate Japanese notice reports whether formations or the alternative budget actually occurred. |
| A replacement reserve for the American campaign | First landing recorded; manual Japanese decision while the war and coastal foothold persist | Pay 200 money and 2,500 supplies; after 60 days receive **50 manpower** for ordinary production/reinforcement, or **6,000 supplies**. No units are promised or queued. Losing the qualifying front returns both payments exactly. |
| The California corridor is in Japanese hands | Japan controls **San Diego, Los Angeles, Sacramento and San Francisco**, at least 90 days after first landing | Choose **12,000 energy, 8,000 metal, 1,500 rares**, or **6,000 supplies and 1,500 oil**, once. No land transfer or premature surrender. |
| America organizes a second continental reserve | At least 60 days since first landing and Japan controls **Las Vegas, Salt Lake City or Denver** | A second and final six-division response, again costing 78 American manpower and 2,400 supplies. Safe rear hubs: Kansas City, Chicago, Washington. Japanese notice reports the actual outcome. |
| Push inland or sustain limited aims? | At least 180 days since first landing; manual Japanese decision while war and a listed port persist | Pay 250 money and 4,000 supplies; after 60 days choose **50 manpower and 4,000 supplies** for an inland commitment, or **8,000 supplies and 2,000 oil** to sustain a coastal position. These are finite resource choices, with no route flags or diplomatic lockout. |
| America funds a long continental war | At least 180 days since first landing; continuing Japanese foothold and war | One explicit American emergency budget: **60 manpower, 9,000 supplies and 5,000 oil**. No immediate units or repeat annual rescue. A Japanese notice explains the reinforcement/operating consequence. |
| The American staging belt has been breached | Japan controls **Denver and Kansas City**, at least 180 days since first landing | Choose **15,000 energy, 6,000 metal and 2,000 rares**, or **9,000 supplies and 4,500 oil**, once. Existing national-surrender requirements still apply. |

The time gates measure elapsed campaign time after the first landing and recheck current possession. They do not claim uninterrupted occupation between dates. Captured-stock rewards and paid reserve deliveries enter the country's national pools, remain subject to normal storage limits, and still need ordinary shipping/supply delivery to the front.

Selecting limited aims neither starts negotiations nor dismisses the existing American national surrender, Pacific armistice, bridgehead support or replacement offers. Selecting inland replacements also makes no irreversible strategic commitment. Each programme has its own pending/done/dismissed state; milestone rewards cannot repeat after losing and retaking a city.

## Verified American formations and fallback

The six-division responses use normal **Infantry**, not a custom class. Clean Blood and Iron definitions verify:

- Infantry model **10** is the 1939 model; technology **1110** unlocks it.
- Infantry model **9** is the 1936 model; technology **1100** unlocks it.
- Both models require **13 manpower per division**. Six divisions therefore deduct **78 manpower**. The response additionally deducts 2,400 supplies.
- The 1939 model is selected only when America knows 1110. Otherwise the 1936 model requires 1100. No unresearched modern formations are granted.
- Every spawning action requires legal American ownership and American control of its staging city, selecting the first valid city in the listed order. Enemy-held and third-party-owned cities are rejected.

If America lacks resources, either eligible infantry technology, or a safe hub, the response instead authorizes a **visible, one-time 40-manpower and 2,000-supply budget**. It creates **no formations**. The Japanese notice states that outcome explicitly. This prevents a silent, permanently stalled response while avoiding hidden negative-resource deductions or units behind Japanese lines.

There are only two formation waves: a maximum of **12 completed American infantry divisions**, costing **156 manpower and 4,800 supplies** if both can form. The separate endurance budget and low-budget alternatives are transparent finite reserves. Existing American forces and AI scripts remain in place; newly formed units operate under the normal American AI.

The installed map's province-name data and the clean USA's national territory verify all named port and hub IDs: San Diego 1886, Los Angeles 1887, San Francisco 1889, Seattle 1874, Sacramento 1888, Las Vegas 1893, Salt Lake City 1896, Phoenix 1900, Denver 1908, Kansas City 1914, Chicago 1832 and Washington 1809.

## Validation

`python japan_expansion/US_CAMPAIGN_review.py`: **11 tests passed**.

Tests evaluate compiled decision/automatic triggers and then execute actual scheduled commands. Coverage includes all four major ports; no prewar or wrong-controller activation; exact US manpower/supply costs; six researched model-10 or fallback model-9 formations; insufficient-stock/research/site alternatives; rejection of enemy-held and foreign-owned hubs; the 60-/90-/180-day gates; the maximum twelve formations; replacement payments, once-only delivery and exact refunds; named-city milestone rewards; national ownership preservation; readable descriptions; and unchanged existing peace/war content and IDs. Maximum new description length is below 1,100 characters.

The controller gates use Darkest Hour's documented `ai = TAG` country-controller predicate (`Modding documentation/event commands.txt`, line 74), rather than incorrectly testing the American receiver with `ai = no`. Test models that previously treated all AI predicates as true must implement the tag form when assessing these entries. The focused `CampaignWorld` does so.

These are offline command/state tests, not observed engine combat. They verify placement conditions and normal unit commands; they do not promise an exact American AI counterattack route, automatic supply delivery or silent callbacks. No game launch, install, save edit or Germany-mod change was performed for this work.
