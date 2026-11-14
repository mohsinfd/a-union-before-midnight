# Japan Rising R15 — specialist units introduced in R13

R14 updated the Matsu figures below; R15 preserves that balance. See R14_CONSTRUCTION_AUDIT.md for research, programmes, ministers, sliders and gearing.

Start a new 1933 campaign through **Japan Rising JX1 Alpha2**. Confirm **R15** in the scenario and welcome. No game was launched during this work. All six R12 first issues and the R12.1 activation/shipping repairs remain. Historical R13 audit counts below describe that earlier revision; current R14 counts and checks are recorded in R14_COLD_AUDIT.json.

Blood and Iron already has Japan's heavy-submarine family, registered internally as nuclear_submarine even for its prewar models. Its models, registry and Japanese starting boats are preserved. The proposed additional ocean submarine is replaced by a full-size land formation: **Expeditionary Assault Division**. This is a counterfactual organisation combining Japanese infantry, assault engineers and a lighter support train; it is not a claim that Japan historically fielded a separate division class with these exact statistics.

## Automatic free introductions

| Service year and required research | Free first issue | Upgrade path |
| --- | --- | --- |
| 1937; **1936 Infantry Division** (1100) | One Expeditionary Assault Division | 1939 Infantry (1110), 1942 (1120), 1945 (1130), 1948 (1140) |
| 1938; **Naval Bomber 1938** (4190) | One G3M Long-Range Naval Attack Wing | G4M 1941 (4200), 1943 (4210), 1945 (15140), 1949 (15150) |
| 1940; **Multi-Role Fighter 1940** (4070) | One A6M Naval Long-Range Fighter Wing | 1943 (4100), A7M 1945 (4350), 1948 (15030) |
| 1944; **Modern Destroyer** (12000) | One Matsu Economical Escort Flotilla | Tachibana 1945 (3080); a 1955 data model (3090) lies beyond the 1950 event period |

These first issues charge **no national money, manpower, supplies or oil**. Required research and the service year must both be satisfied. Each family gets one free formation once, not a repeatable replacement source. Additional copies use normal production. Later models use normal upgrade funding. A6M/A7M and G3M/G4M have distinct early/late model illustrations; later continuation equipment uses its family's illustration.

The R12.1 transaction pattern is retained: introduction request, then activation, researched-model/effect catch-up, equipment creation, named full-strength restoration and final completion. Deferred acknowledgements and cached actions cannot invalidate the request or duplicate rewards. Aircraft require a maintained Japanese home airfield, escorts a home port, and the expeditionary division a controlled and owned home assembly province. No airfield is required for ordinary expeditionary Infantry. Losing usable bases while waiting leaves the gift available later. Formation organisation still recovers normally.

## First-model costs and benefits

These are base values before national research, programmes, policy, ministers and gearing. IC-days multiply IC cost by construction days; they are a useful construction comparison, not a statement of the final production-screen price.

| Unit | Specialist vs ordinary counterpart | Why build more? | What it gives up |
| --- | --- | --- | --- |
| Naval Long-Range Fighter | **21 IC x 200 days = 4,200**, versus 20 x 210 = 4,200. Base range **1,100 vs 550 km**; air attack 6 in both. | Twice the parent base range at the same total base IC-days, with ordinary full-strength fighter firepower. Range follows normal later improvements without regression. Existing land-air range programmes also apply. | Speed **570 vs 600**; air-defence vulnerability **10.35 vs 9** (higher is worse); fuel **2.09 vs 1.9/day**. It is land-based, not a CAG. |
| Long-Range Naval Attack | **14.25 x 228 = 3,249**, versus 15 x 240 = 3,600. Range **1,875 vs 1,250 km**; naval attack 4 in both. | About **10% fewer base IC-days**, 50% more base range and full naval strike. Flying boats retain their greater range and detection. | Air-defence vulnerability **37.5 vs 30**, fuel **3.45 vs 3/day**, ground attack halved. It needs fighter cover when opposition is strong. |
| Economical Escort | **1.04 x 456 = 474.24**, versus 1.3 x 570 = 741. ASW attack **16.8 vs 14**. Full 1.5-manpower crew retained. | About **36% fewer base IC-days**, shorter replacement time and stronger ASW. Useful for local escort and submarine-hunting groups. | Speed **27.2 vs 34**, range **5,200 vs 8,000 km**, surface attack **3.85 vs 7**, AA **4.8 vs 6**. It is a map Destroyer flotilla; it does not fill the national convoy escort pool. |
| Expeditionary Assault | **5.25 x 276 = 1,449**, versus 5 x 290 = 1,450. Full **13 manpower**, soft attack 10 and speed 6 retained. | Almost identical base IC-days. Supplies **0.8 vs 1/day**, oil **0.225 vs 0.3/day**; useful over long supply routes. Jungle attack/movement **+15**, forest attack/movement **+10**, river attack **+15**, urban attack **+10 percentage points** relative to normal Infantry. | Defence **31.5 vs 35**, hard attack reduced by one. Ordinary mountain, winter and amphibious limitations remain: it does not replace Mountain Infantry or Marines. |

Each specialist retains its full native manpower/equipment complement, normal command footprint, attachment capacity and ordinary operating rules. Construction discounts for the parent family mirror to it, including choices made before introduction. Concrete doctrine, minister and stock-event effects also follow their parent, including penalties. Research has once-only guards so activation cannot replay an already-applied effect. All base aircraft and land/ship model statistics stay unchanged.

## What remains from R12.1

All 31 local garrison templates remain capped at 25 strength. Their first successful call-up supplies **180 convoy transports and 90 convoy escorts once**. The paid prewar merchant programme still offers **160/40** or **100/80** transports/escorts for its unchanged bill and delay. The new Matsu is a combat unit, separate from this shipping allowance.

The earlier Type 93, mixed brigade, flying boat, Akizuki, Teishin and Ka-Mi introductions and upgrades remain. Type 93 fits Matsu escorts; mixed and Ka-Mi attachments can fit the new expeditionary division. No attachment is silently inserted with a free formation.

## Art and validation

Six new paintings were generated with the built-in image tool and retained under art/: four families plus late A7M and G4M variants. **R13_ART_SOURCES.json** records their exact prompts and source paths; **UNIQUE_ART_MANIFEST.json** adds hashes for all thirteen specialist illustrations. Native sprites use the correct parent family, with distinct new counter markers. Bespoke animated sprite sets are not claimed.

R13 appends twenty events after all 1,802 existing IDs: four introductions, four guarded transactions and twelve model-year catch-ups. Total: **1,822 events**, with no additional decision cards. See **R13_COLD_AUDIT.json**, **UNIQUE_UNIT_COLD_AUDIT.json** and **R13_INSTALL_RECEIPT.json** for final results. Offline checks cannot establish campaign balance, animation, real convoy routing or all running-engine behaviour.
