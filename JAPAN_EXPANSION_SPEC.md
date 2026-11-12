# Blood and Iron: Japan expansion — audit and proposed specification

Design revision 1 — 25 October 2026. Status: specification and source/save audit; no gameplay implementation or installation in this revision.

## 1. Agreed campaign

A 1933 Japanese campaign, preserving the historical diplomatic sequence through Pearl Harbor, followed by an open campaign through 1950. Japan is stronger and more resilient, while Hard remains challenging. China must be difficult but decisively settleable. China and India must become useful Japanese partners or puppets. Japan can dominate both oceans, attack Australia, fight the USSR, reach the Mediterranean, support Germany, negotiate an American peace, or invade America.

Historical sequence means preserving the main crises, alliances, China-war outbreak, embargo and Pearl Harbor opening. Battlefield results can diverge before December 1941: the player's victory in China must remain possible. Prewar preparation can improve production and readiness without introducing an ahistorical alliance route. Large diplomatic departures and new expansion choices open after Pearl Harbor. This resolves the tension between a historical opening and a winnable early China campaign.

Ordinary British India remains in the starting world. The Indian player expansion, its independence opening, special units, economic bonuses, compacts, ledgers and country-resolution scripts are excluded. Japan's later Indian puppet content is a new, limited part of Japan's campaign.

## 2. Baseline and evidence

### Source selection

Use `C:\Users\Mohsin Dingankar\Downloads\Blood and Iron v1.1` as the candidate baseline. Do not clone the installed Indian mod or assume the installed Blood and Iron folder is unmodified.

Compared 1,823 existing gameplay text/data files across `db`, `ai`, `config` and `scenarios`, excluding saves, between that copy and the installed Blood and Iron copy. Two files differ: `db/events/UK.txt` and `db/tech/teams/teams_ind.csv`. No corresponding source file was missing from the installed copy. This comparison covers those files, not every graphic, executable or byte in both installations.

The installed `UK.txt` contains a custom “STABLE UNITED INDIA START” block, including events 2001091 and 2001092. Those IDs collide with British events in `DayofDecision.txt`. The Downloads copy lacks the custom block and has no duplicate event IDs in this audit. Its origin has not been authenticated against an original distribution archive; it is a cleaner local baseline, not a claim of verified publisher authenticity.

The 1933 scenario and its event registry reference 104 event files. The structural reader inventories 4,262 event blocks, including 236 assigned to JAP and 738 to GER, after recovering from one malformed command. These counts include historical, AI and triggered events; they are not counts of meaningful decisions available to a player. All 104 referenced files exist. This is a structural inventory, not an engine certification or a full behavioral audit of every event.

### Campaigns actually inspected

Six Japanese saves from the installed Blood and Iron `scenarios/save games` folder were structurally inspected:

| Save | Relevant evidence |
| --- | --- |
| `China is fallenEmpire of Japan_1938_June_9.eug` | Japan has 72 deployed land divisions, 8 fleet carriers, 13 light carriers and 9 escort carriers; China is within the player's demonstrated capabilities. |
| `WonChinaEmpire of Japan_1939_May_14.eug` | Despite the filename, CHI still exists and Japan is still at war with it. A successful advance and an actual settlement must be distinguished. |
| `pearlEmpire of Japan_1941_December_13.eug` | Japan has 86 deployed land divisions, about 9.8 manpower and 113,384 oil. Its Chinese puppet has only two land divisions and one national province. |
| `indiaEmpire of Japan_1942_July_1.eug` | Japan has about 138 oil and no spare convoy transports. IND exists but is not yet Japan's puppet in this snapshot. China-Nanjing has 68 land divisions but only one national province. |
| `califEmpire of Japan_1942_November_24.eug` | Japan has 14 fleet carriers, 20 light carriers and about 38,374 oil. Germany has zero oil and less than one manpower. |
| `usassautEmpire of Japan_1943_June_11.eug` | Japan has about 2 oil; USA has about 164,222 and eight carrier construction lines. Japanese puppet India exists, with five land divisions. China-Nanjing has 25 land divisions, one national province and about 23 supplies. |

These are snapshots from potentially different campaign histories. They must not be subtracted from one another to invent naval losses or a resource-consumption trend. All six record `set_difficulty = 2`, the Normal setting. They demonstrate structural bottlenecks; they do not establish Hard balance. The intended expansion is tested separately on Hard.

In the June 1943 save, the zero transport pool is **zero unassigned reserve**, not zero merchant ships. Japan has 1,081 transports assigned across 27 routes. Twelve route records have no transports assigned; some could be obsolete or unnecessary, so each needs inspection before being called a supply failure. The largest assignment is 591 transports on the route ending at Suez, followed by 178 on a China-to-Japan route. The campaign has serious shipping pressure, but this is not proof that the entire merchant marine was sunk.

### Confirmed findings and limits

| Ref | Finding | Design consequence |
| --- | --- | --- |
| A01 | The installed baseline contains old Indian edits and duplicate IDs. | Build from the cleaner Downloads source with a new manifest. Never import the installed Indian override. |
| A02 | `Add_on.txt:2587` has `command = [` instead of an opening brace, producing an unmatched closing brace. The defect exists in both copies. | Repair this inherited syntax defect in the new mod before adding content. Its exact runtime impact is not established here. |
| A03 | `revolt.txt` gives China-Nanjing U87 Nanjing as its sole minimum/core province and much of China as claims. Actual saves show one national province. | A consolidated Chinese puppet needs Chinese cores, industry and research suited to its own territory. Claims are not an adequate substitute. This is a source-design limitation, not proof of an engine malfunction. |
| A04 | India is already releasable through the engine, and a Japanese puppet India exists in the 1943 save. Much of the bespoke Bose settlement in `new_events.txt` is Germany-specific. | Japan needs its own reliable Indian surrender, government formation, recovery and military assistance content. Do not describe India as technically impossible to puppet. |
| A05 | Light-cruiser conversions use nominal CVL time/cost factors 0.40/0.55; heavy-cruiser conversions use 0.45/0.50. CVE conversions also exist. | Preserve the enjoyable conversion option. Calculate full cost including the original ship, conversion, air group and attachments before changing it. |
| A06 | Carrier templates have long base times: the Fleet Carrier model is 1,140 days, Improved Carrier 1,200. Industry technologies reduce these. Actual queued Japanese carriers in the 1943 save have a 612-day saved duration. | Balance actual completed ships and IC-days, not raw template days. A blanket naval discount would stack with existing technologies and conversion advantages. |
| A07 | The Chinese puppet and Japan repeatedly lack supplies/fuel; Japan has no spare shipping in several later saves. | Industrial, fuel, convoy and puppet development must be designed together. Additional IC alone will increase shortages. |
| A08 | Japan's 1933 historical North Strike choice sleeps much of the old Soviet expansion/settlement chain. Its ahistorical alternative sleeps Pearl Harbor. | A new post-Pearl Harbor Soviet option must work after the historical 1933 choice. It cannot depend on having selected an ahistorical route in 1933. |
| A09 | Afrika Korps event 9300225 in `Mods.txt` has `trigger = { ai = no }`. The 1933 scenario sleeps the older 2003182 event. | AI Germany needs a functioning, supplied African assistance mechanism. Simply increasing Italy's IC will not repair this exclusion. Other AI assistance must also be audited for human-only gates. |
| A10 | June 1943: Germany has 295 deployed land divisions, about 158 oil and 0.425 manpower; USSR has 708 and about 15,405 manpower. Germany is still alive. | The saves support an Axis endurance problem, but not a universal assertion that Germany always loses in 1942. Measure fuel, manpower, deployment and aid before choosing bonuses. |
| A11 | Soviet aid and recovery are distributed across `Gameplay.txt`, `Add_on.txt`, mobilization and lend-lease. One AI event supplies 30 off-map oil/day, 200,000 supplies and numerous units; other events activate separate reserves. | Trace total reinforcement and modifier stacking. Preserve Soviet resistance while preventing multiple systems from overwhelming an AI Germany by accident. |
| A12 | The existing American surrender event 2049046 normally requires a mainland foothold and 55% lost national territory, with lower thresholds for nuclear cases. | Add a distinct, difficult Pacific armistice. Do not mislabel the current national-defeat settlement as a practical naval victory. |
| A13 | Sydney and Pearl Harbor milestone events currently give modest dissent/supply rewards. | Keep their historical recognition, but attach consequential follow-up choices and settlements to the actual military situation. |
| A14 | Japanese research has real strengths and specific holes. Yamamoto matches all five components of several carrier doctrines, but the 1940 Carrier Division technology has only two matching components in the best available team. The marine school matches 4/5 components in 1940 and 3/5 in 1943. | Add targeted institutional development rather than raising every team's skill. Component matching is a screening measure, not a full research-time calculation. |

## 3. What stays, what changes

Keep Blood and Iron's map, terrain treatment, sprites, unit roster, Japanese historical identity, core research tree and historical opening. Preserve good existing naval conversion and specialist-unit mechanics until measured. Retain useful China surrender, Pearl Harbor and conquest content, but give each outcome one authoritative settlement implementation.

Revise the economy, naval recovery, partner states, Soviet-war availability, Axis assistance, late-war AI and surrender logic. Remove or disable an old event only when its replacement covers the same outcomes and the dependency audit identifies callers, follow-ups, flags and AI switches. Record every removal in a migration table.

The design has no permanent “Pacific route,” “Soviet route” or “Indian Ocean route.” Decisions depend on current enemies, controlled provinces, treaties, available resources and completed projects. Japan can pursue all ambitions, sequentially or simultaneously, if it can support them. A signed treaty, completed project or permanent refusal can close its specific action; an unrelated campaign must remain available.

## 4. Balance targets

All figures below are **initial tuning targets**, not measured outcomes or guarantees. Use consistent game options: Hard, unchanged default aggression initially, no full occupied-IC takeover, and a recorded tech-team-takeover setting. Reference runs should use team takeover off, with a second check for players who enable it.

| System | Initial target | Limit |
| --- | --- | --- |
| Japanese industry | Earn roughly 15–20% more usable capacity than an equivalent baseline campaign by 1942; up to 30–35% by 1945 with successful investment and secure resources. | No free industrial doubling or forced expansion of every resource stockpile. Record base IC separately from usable IC. |
| Naval construction | A funded wartime programme reduces effective IC-days of comparable new ships by at most about 20–25% versus the same baseline technology/policy state. | This is the combined extra benefit, not another 25% layered over several new discounts. Conversions receive no automatic extra discount. |
| Recovery | One major naval defeat can be recovered from through roughly 12–24 months of repairs, conversions and construction. A destroyed carrier force still takes time to replace. | No restored sunk ships and no free fleet triggered by intentional scuttling. |
| Merchant shipping | Sustained investment can keep pace with ordinary losses; severe enemy interdiction remains dangerous. | Protecting oil routes must matter even after seizing the oilfields. |
| China | A well-prepared campaign can win a decisive settlement; repeated refusal is limited and explained. | No surrender for taking one city; no requirement to occupy every remote province. |
| China/India partners | Provide armies, useful research and regional defence within 6–18 months of a stable settlement. | They cannot instantly supply unlimited troops or automatically fund Japan's entire war. |
| European Axis | In hands-off Hard trials, aim for Germany to remain a credible combatant through the end of 1943 in at least 6 of 8 runs; 1944 remains contested. | Early defeats remain possible; there is no immunity, scripted Soviet collapse or guaranteed German victory. |
| USA | Strong rebuilding and organised naval counteroffensives. Japan can force a limited settlement through sustained success. | Capturing Hawaii alone or sinking one fleet cannot automatically end the war. |

Measure hull + air-group + attachments + upgrades + repairs + fuel + convoy support. A low hull price can conceal a very expensive operational navy. Report these together in balancing notes.

## 5. Economy, oil and shipping

### Industry and military production

Prewar investment offers comparable, focused alternatives: shipbuilding capacity, aircraft/engine works, or army supply/vehicle production. Each develops over time and consumes actual money, supplies and industrial construction effort. The largest payoff arrives after the Pacific war begins. There is no single option combining the most IC with the largest dissent reduction.

An initial series of two industrial investments should add about 8–12 physical IC over 18–30 months, subject to affordability checks against the 1933 economy. A later wartime standardisation programme adds efficiency rather than another large batch of factories. Exact province allocation and prices follow the province/resource audit. Physical industry remains vulnerable to bombing and invasion.

China, India and Manchukuo develop their own industry. Japan can receive contracted supplies, resources or technical benefits; releasing a puppet must not secretly copy its factories into Japan. Occupied administration can reduce transport burden without turning all occupied Asia into Japanese national provinces.

### Fuel production and delivery

Recognise major oil regions separately: southern Sakhalin's relevant holdings, Borneo/Brunei/Sarawak, Sumatra, Java where appropriate, and later Persia/Iraq if reached. Province IDs and actual oil values must be taken from this map, not assumed from another mod.

Capturing a site opens repairs, then production recovery, then optional expansion. Suggested recovery checks occur around 60 and 180 days after investment; a successful completion needs continued friendly control. Improved provincial output is the preferred mechanism because transport and enemy attack remain relevant. Any use of off-map output must be explicit, small, capped and tied to the represented facility, with a tested suspension mechanism if that facility is lost.

Puppet oil agreements must account for the partner's domestic consumption, reserved stockpile and existing engine tribute. Do not create oil in both countries as if two independent deliveries occurred. Recovery and expansion cannot be repeatedly claimed after recapturing the same site.

Synthetic fuel is an expensive late-war supplement, with energy consumption and technology prerequisites. Fuel discipline and modern logistics give limited savings; permanent universal fuel reductions do not replace the need for oilfields and shipping.

### Merchant marine

Offer merchant construction, escorts, naval patrol aircraft and emergency allocation as different responses. Merchant shipping uses the convoy pool; naval troop transports are a separate fleet unit. Event wording must say which is being provided.

An emergency merchant programme should commission a delayed, paid batch, initially around 80–120 convoy transports, with a 180-day cooldown and a small maximum number of uses. If the engine cannot create a delayed order at the intended price, use a paid project with a delayed completion event and deduct its cost transparently. Cancellation and loss of the producing port require explicit handling.

Warnings distinguish low total shipping from an exhausted unassigned reserve and excessive commitments. The source engine has a total-convoy trigger, but it cannot necessarily test every route's unmet requirement. Where automatic diagnosis is unavailable, provide a short practical prompt without claiming that a particular route is broken.

The Suez example is a test case: a huge supply route must not be “fixed” by unlimited free merchantmen. Test smaller forward forces, local allied supply, nearer bases, appropriate puppet arrangements and convoy allocation alongside construction.

## 6. Naval rebuilding and the three services

### Navy

Three viable investments compete for funds:

| Choice | Benefit | Opportunity cost |
| --- | --- | --- |
| Fleet-carrier construction | Best sustained offensive carrier force, with contemporary air groups. | Slowest large investment; needs screens, aircraft and oil. |
| Conversion programme | Quicker use of existing hulls and continuity with enjoyable Blood and Iron gameplay. | Consumes the old ship; smaller capability and limits inherited from the actual converted model. |
| Escorts and repair capacity | Protects the force already built and keeps overseas resources moving. | Delays another offensive capital ship. |

Preserve light/heavy-cruiser conversions initially. Test whether the AI uses or fails to use them, how upgrades choose models, and whether obsolete cheap hulls can become the newest carrier too cheaply. Do not globally remove conversions because they are powerful. If a correction is necessary, retain a useful conversion strategy and publish before/after total IC-days.

Port projects at home and selected forward bases improve basing and recovery. The engine's `repair_mod` is a general reinforcement-efficiency modifier, not a proven naval-only repair-speed control. Prefer naval bases and tested unit repair parameters. Do not implement a large general modifier and advertise it as affecting ships alone.

After a genuine serious defeat, offer one limited emergency programme: prioritise repairs and escorts, fund replacement carrier construction, or concentrate on land-based naval air while the fleet recovers. It pays through resources and delayed production. Availability requires verified combat-loss counters or another tested loss signal; voluntary disbandment must not farm rewards. If suitable counters cannot distinguish the intended loss, keep this as a manual paid wartime investment rather than pretending automatic diagnosis works.

For event-created ships, define attachments once: correct CAG/light CAG, radar, AA, hull or ASW as appropriate, within brigade capacity. Account for any engine-added brigade before adding another. No land brigade on a ship and no accidental second air group. Named hulls cannot be commissioned twice, including after peace/reload.

### Army

Make existing formations more rewarding before adding unit types:

- Naval infantry: amphibious operations, islands and port seizures; properly funded equipment and marine research.
- Regular infantry with artillery/engineers: China's main fighting force and sustained operations in India.
- Mountain troops: western China, Burma and difficult Soviet approaches.
- Cavalry/light mobile forces: exploitation and economy in suitable low-infrastructure regions; no universal jungle or mountain speed bonus.
- Motorised formations and a limited armour programme: expensive exploitation forces useful in India, Australia and America; their fuel burden remains real.
- Garrisons and partner armies: base security and occupation, releasing Japan's best divisions for the front.
- Army engineers and logistical development: bridges, captured transport corridors and better-supported distant operations.

Lessons from campaigns unlock paid training, doctrine research assistance or modest specialist improvements. Capturing one jungle province must not grant every formation an unexplained permanent combat bonus. Provide research and production choices, rather than repeated free division packages.

### Air force and pilot training

Preserve early strengths while allowing a player to sustain them. Offer deeper training and replacement capacity, immediate front-line reinforcement, or expanded naval reconnaissance. Benefits must be implemented through supported production, research, experience or unit parameters.

The engine does not provide a separate historical pilot population for every wing. A pilot-training project is an abstraction with explicit cost and modest effects, not a fictitious new pilot simulation. Carrier air groups, light carrier groups and land-based naval aviation must all be checked; improving only CAGs leaves converted ships or land aircraft behind.

Develop useful forward airfields at captured hubs. Keep visible distinctions between construction capacity, actual aircraft and security forces. No event called an aircraft programme may award only an airbase or an infantry division.

## 7. China: a hard war followed by an actual settlement

Keep the historical outbreak and meaningful Chinese defence, mobilisation and external aid. Audit the total bonuses from all China files before raising Japanese combat values. China's difficulty should come from defending armies, distance and supply, not from a victory settlement that remains unavailable after decisive defeat.

Use three stages, each independent of the year in which the player reaches it:

1. **Coastal and central defeat:** Japan holds major coastal/central objectives and China has suffered substantial industrial/VP losses. A limited armistice becomes possible, with a chance of rejection while China retains a viable western army.
2. **Decisive national defeat:** China loses its western capital and major connected production/supply centres, or suffers comparable deeper losses. Japan can force a full political settlement without occupying every frontier province.
3. **Unfinished resistance:** Communist or regional forces still fighting are named explicitly. A settlement with Nationalist China does not falsely announce that every Chinese war has ended.

Exact objective lists must be province-verified, including Nanjing, Shanghai, Wuhan, Chongqing and relevant western supply centres. There must be alternate tests for an enemy that has already moved its capital or lost provinces to another belligerent. Countdown checks reset if required objectives are lost.

Settlement alternatives:

| Offer | Japan receives | China receives / consequence |
| --- | --- | --- |
| Consolidated Chinese puppet | Bases, access, economic agreements and a useful allied army. | Core status over appropriate Chinese territory, a coherent government, research and a reconstruction programme. |
| Regional Chinese governments | Several smaller partners and selected Japanese bases. | Distinct territory, non-overlapping cores and local defence; more separate borders and coordination. Existing usable tags only. |
| Limited Chinese peace | Named concessions and a clear ceasefire. | Independent surviving China; Japan receives no implied control over its army. |
| Continued occupation | Direct control of conquered territory. | Japan continues paying occupation and transport costs and fighting remaining enemies. |

China's cores are Chinese, not Japanese. Manchukuo and any separately agreed Mongolia are excluded from automatic territorial consolidation. For the main consolidated puppet, fix the one-core limitation at establishment rather than keeping its entire economy foreign forever. Restricted local autonomy can be represented without using blanket non-core status as a permanent economic penalty.

Preserve surviving Chinese formations where technically safe. If the settlement destroys or strands them, explicitly reconstruct a small defence force from a costed pool, then rebuild over time. Initial target: a coherent 12–18-division army within six months and 30–45 within eighteen months if territory, industry and supply allow; existing forces count toward these totals. Never add the entire package on top of an intact 68-division army.

China chooses home defence or a limited expeditionary contribution. Its AI prioritises supply and land forces, not an unaffordable navy. Japan can fund officer training, equipment and transport connections. Excess resource tribute cannot drain it below a useful operating reserve. Annual investment must return something visible: more capable forces, stable supply, research cooperation or a specified economic delivery.

## 8. India: a Japanese settlement and a useful Indian Ocean partner

The starting Raj remains historical. After Japan's war with Britain begins, offer support for an Indian independence movement, recruitment and a provisional government when Japan has an actual regional base. This cannot create a fully equipped army or transfer all India merely for spending money.

An initial Bengal campaign can establish a regional provisional administration without forcing the whole Raj to capitulate. A national settlement needs Delhi plus other major centres, meaningful Raj losses and sustained Japanese/partner control. Design around Bengal, Delhi, Bombay and the main supply corridors, with verified map IDs. No magical national surrender from a single isolated city.

Full settlement offers a unified Indian puppet, an independent friendly India with a base treaty, or continued occupation. An alternative partition should appear only if available tags, territorial logic and a complete outcome are implemented; do not advertise an unfinished option. India is not an honorary name for the old Indian player mod.

The puppet receives Indian cores, appropriate surviving forces or a limited paid reconstruction force, historical institutional teams, ministers and leaders through 1950, a domestic supply reserve and an AI focused on regional defence. Initial recovery target: 6–10 useful land divisions within three months and 18–30 within a year, counting existing troops; a small air component follows. Fleet development is initially coastal defence and escorts. The 1943 save's five divisions and five light-cruiser construction lines are the specific poor outcome to avoid.

Offer clearly priced Japanese base reservations at selected ports: access-only for maximum Indian economic integrity, or actual Japanese ownership of specific naval bases for stronger control. Calcutta, Bombay, Cochin and Colombo are candidates, not all mandatory prizes. Colombo/Ceylon is handled separately where its ownership requires it. A choice states which port province remains Japanese and what India receives in return. Released-country core claims must not silently reclaim that base through a later event.

Once stable, Indian support can cover the Indian Ocean, Burma, the Middle East or a Soviet front. Each contribution is bounded and paid. India must be able to supply itself before sending major expeditionary armies. No national-plan, federal-union or Indian compact events from the previous mod are imported.

## 9. Country settlements across both oceans

Use one shared technical procedure with individual country events, not player-facing theatre menus. The UI names the defeated country, requirements, proposed borders, bases and war effects. Simultaneous settlements remain independently actionable.

| Country/territory | Settlement content | Consequential reward or trade-off |
| --- | --- | --- |
| Philippines | Puppet, friendly independence, direct occupation. | Manila/Subic base choice, coastal defence and a reconstruction force; reconcile US ownership and surviving Philippine forces. |
| Dutch East Indies / Indonesia | Oil centres plus Dutch authority determine an offer. | Occupation versus Indonesian puppet with resource agreements; choose actual Soerabaja and/or other bases explicitly. No phantom province transfers. |
| Brunei and Sarawak | Separate small states or inclusion in a larger agreed settlement. | Oil, naval access and modest local defence. Neutral association uses independence where puppet status would automatically import wars. |
| Malaya | Country settlement distinct from Singapore. | Retain Singapore as a Japanese naval base, or grant it with access in exchange for a stronger Malayan partner. |
| Hong Kong | Explicit territorial award and port development. | Japan retains the port or transfers it to its Chinese partner with a stated agreement. No silent transfer through broad China regions. |
| Indochina | Deal with actual colonial owner, local government and current controller. | Unified administration where supported, or Vietnam/Laos/Cambodia; specify Cam Ranh and other reserved facilities. |
| Thailand | Voluntary ally, coerced settlement or puppet according to circumstances. | Regional support and transit; settling Thailand cannot terminate the unrelated American or Soviet war. |
| Burma | Japanese partner or direct occupation. | Regional army, supply corridor and a clear relation to India. No automatic annexation into another puppet. |
| Australia | Defeat the main population/industry belt and field army before a national settlement. | Puppet/neutralised Australia, selected bases, or occupation. Sydney alone is a milestone, not nationwide surrender. |
| New Zealand | Separate requirements and settlement. | Local defence, Pacific basing or neutralisation. Australian peace does not silently settle New Zealand. |
| Hawaii | Occupation, fortified base or an explicitly traded bargaining asset. | Logistics, basing and stronger negotiation grounds; not instant US collapse. |
| Pacific island groups | Capture milestones attached to useful bases. | Airfields, port repair, Japanese control or transfer to a named partner; avoid an event for every empty atoll. |
| Persia / Iraq | Local conquest or negotiated access where feasible. | Genuine fuel arrangements and retained transit; Japanese troops cannot become trapped by settlement. |
| Egypt / Suez | Separate local settlement and canal objective. | Transit and naval basing; Egypt's status does not imply British surrender. |
| Soviet Far East / Mongolia | Limited border settlement or much deeper negotiated defeat. | Named borders and viable client states where supported; no total Soviet surrender from Vladivostok alone. |
| United States | Pacific armistice, mainland defeat terms or continued war. | Named territories, base rights and treaty restrictions, scaled to the actual defeat. |

Existing partners remain partners unless a later explicit choice changes that. Postwar consolidation offers must not annex a small puppet the player intentionally kept.

Small new island states need a minimal defence kit: local security units, supplies, a few suitable coastal/escort assets when justified, and an AI that can maintain them. The initial package comes from surviving local forces, transferred equipment or a Japanese-funded programme. Releasing one-province states cannot create free carriers, modern fleets or repeatable manpower.

## 10. Japan helping the European Axis

Japan normally retains its own alliance while coordinating with Germany. Formal Axis entry remains optional after Pearl Harbor, with every inherited war listed before confirmation. Cooperation is not conditional on formal entry, and a separate Japanese Soviet war remains available.

| Action | Requirements and costs | Actual effect |
| --- | --- | --- |
| Submarine exchange missions | Suitable ports, limited supplies/oil and relations; finite missions. | Specific blueprints, small reciprocal deliveries and occasional mission losses. No ocean-spanning unlimited trade. |
| Protect Axis resource access | Japan controls useful routes/resources and can deliver aid. | Bounded shipments with an explicit origin, destination and cost to Japan. |
| Pressure Britain in the Indian Ocean | Successful operations against British bases and shipping. | Geographic AI reaction and diversion of some British effort; benefits follow actual pressure rather than pressing a “help Germany” button. |
| Advance to Suez | Secure a continuous practical sequence of bases and supplies. | Opens a viable Mediterranean expedition and threatens British logistics. Naval passage follows actual canal/strait rules. |
| Pressure the USSR | Border deployment, preparation and a deliberate diplomatic choice. | Soviet AI must maintain a credible eastern defence. Mere Japanese strength does not permanently freeze a huge fraction of the Soviet army. |
| Declare a Soviet war | Post-Pearl Harbor, no binding treaty without an explicit break, sufficient readiness. | Separate Japanese war, with visible consequences and objectives. Neither Germany nor America must already be fighting the USSR for it to appear. |
| Joint Soviet settlement | Germany and Japan both meet their own military requirements. | Territory based on actual contributions and agreed borders; Japanese gains survive Germany's separate peace. |

Soviet operations offer limited Far Eastern objectives and a deeper Siberian campaign. Capturing the coast unlocks logistics and local administration; reaching the trans-Siberian transport belt creates a much more serious strategic problem for Moscow. A full Russian defeat requires deep military losses and major centres, accounting for the western front's outcome. Negotiating a limited eastern peace does not falsely announce Soviet national surrender.

The old 1933 route locks must not gate these actions. The new decisions read current treaty/war state and post-Pearl Harbor availability. Historical neutrality before Pearl Harbor stays intact.

### Shared Axis repairs

Germany: audit oil conversion and synthetic fuel, Romanian trade and delivery, reinforcement/upgrade allocation, manpower mobilisation, reserve use, front/garrison split, occupation demands and strategic redeployment. In the reference save, more factories alone would not repair almost-empty oil and manpower pools. New mobilisation represents a finite population and replaces overlapping grants; it is not an annual unlimited refill.

Italy: repair the AI Afrika Korps path, then test whether it arrives at a friendly supplied port and stays useful. Improve reinforcement of Libya, defence of Greece/Crete and Italian ports, escorts and convoy replacement. An expedition cannot appear in an enemy-held port or add the same divisions every time Italy loses ground. German participation consumes resources or reallocates real forces, with any scripted compensation capped.

Finland: audit German/Finnish assistance and arrival requirements, supply, winter defence and armistice triggers. Do not claim these are human-only until the individual event audit proves it. Finland can lose, but a nominal event that never produces useful assistance is not adequate.

Romania/Hungary/Bulgaria: production and supply should support plausible army contributions and defend essential territory. Romanian oil and its delivery are strategic. Do not drain every minor's resources or army into one front and leave it helpless.

Norway/Balkans: give the AI realistic port defence and reserves. Allied landings still work when supported; neither a token unopposed raid nor immortal coast garrisons should decide the region by default.

USSR: retain mobilisation, winter recovery and lend-lease, but inventory each grant and time its delivery. Verify that human-Germany challenge packages do not inadvertently combine with all AI-versus-AI packages. A two-front war should divert and redistribute forces; do not simply delete Soviet divisions or award Germany free victories.

USA/UK: keep real counterpressure, fuel consumption, convoy dependence and vulnerability to losses. Review unusually rapid or distant air operations against the engine's AI rules before calling them illegal. Do not promise human-equivalent naval/air range restrictions if the engine cannot enforce them.

## 11. American peace and invasion

### Pacific armistice

Create an attainable but demanding alternative to occupying most of America. Initial requirements for testing:

- War has lasted at least 24 months, and it is 1943 or later.
- Japan securely holds the Philippines and the main western-Pacific possessions in the proposed treaty, while retaining its home islands and core supply bases.
- At least one major additional defeat: sustained loss of Hawaii, a defended mainland foothold, or another equivalently severe combination that has been explicitly implemented and tested.
- America has suffered substantial naval/air losses or Japan has a credible remaining carrier force and sustained advantage at the relevant objectives. Transport hull counts cannot substitute for carrier strength.
- A 180-day pressure period completes without the required position being reversed. A one-day capture cannot qualify.

An initial moderate demand can receive roughly a 40–60% acceptance chance when eligible. Much stronger leverage can raise it, but precise probabilities are tuning inputs. Rejection allows another approach after 180 days, with better odds only for improved leverage or sustained duration; it cannot produce daily offers. A finite campaign must not depend on infinite bad random rolls: after two refusals and a materially stronger maintained position, the moderate offer gets a deterministic acceptance tier or a clearly stated remaining requirement.

Possible terms: recognition of Japanese/partner territory in the western Pacific, specified US withdrawals and a treaty over Hawaii if occupied. Returning Hawaii can purchase a less demanding settlement. Do not make Japan stronger through the same resources or territory counted in several reward systems.

The settlement affects only the named belligerents and wars. If the engine cannot preserve the desired war relationships while the US remains in the Allied alliance, the offer must disclose a wider Pacific armistice or a US alliance withdrawal. This is a high-risk prototype gate, not a solved implementation detail. No wording may promise a bilateral peace while secretly ending the German war or abandoning Japan's puppets at war.

### Invasion of America

Keep a genuinely difficult alternative. Hawaii and intermediate bases support operations; western ports enable a sustainable foothold; American mobilisation and counterattack react to the invasion. Gaining one coastal province does not destroy US industry or morale.

Offer staged territorial demands after substantial victories: a Pacific settlement, stronger American neutralisation, or total conquest. West-coast territorial/client arrangements require deep defeat, plausible supported tags and explicit borders. Optional breakup terms appear only if fully implemented. Occupation brings supply, garrison and political costs. No victory event is forced merely because Japan took the cities it was asked to take.

## 12. Content through 1950

The postwar game must respond to victory, stalemate and recovery:

| Period | Content that remains active |
| --- | --- |
| 1933–1936 | Historical politics and diplomacy; economic recovery; naval/air/merchant investment; military schools. |
| 1937–1941 | China war, mobilisation, occupation versus settlements, actual partner development, embargo and Pacific preparations. |
| 1941–1943 | Pearl Harbor, southern resources, naval losses and recovery, Philippines/Indonesia/Malaya/India, Australian preparations, German cooperation. |
| 1943–1945 | American rebuilding, fleet and air modernisation, Australia, Soviet intervention, Suez, mature puppet armies and initial Pacific negotiations. |
| 1945–1947 | Continued war or peace implementation, reconstruction, alliance commitments, occupied territories, demobilisation versus readiness, rockets/jets and atomic competition. |
| 1947–1950 | Partner autonomy, economic agreements, naval limitation talks, renewed tensions, Soviet/US rivalry and optional renewed wars with explicit treaty consequences. |

Do not hard-code the historical Japanese surrender, occupation government or postwar institutions into a victorious empire. Conversely, genuine military defeat must still have a coherent surrender and reconstruction sequence. Technology names, ministries and teams must match the state that actually exists.

A peace settlement is followed by concrete implementation, then reconstruction, then later political choices. No generic annual “report” events that do nothing. Examples of meaningful late events: reopen naval construction after treaty expiry; grant India greater autonomy in exchange for a renewed base agreement; finance Chinese recovery or keep more Japanese resources; reduce the army to fund civilian industry while a rival rearms.

Japan's empire should not receive an automatic daily rebellion penalty simply to manufacture content. Instability follows actual occupation, war damage, extraction or denied agreements; cooperation also has real costs and benefits. Local opposition is not erased by naming every government a liberator.

## 13. Research, people and visuals

Build a 1933/1937/1941/1945/1950 research coverage matrix against the actual technology components, availability dates, skill levels, research prerequisites and active doctrine path. Screening every branch does not imply giving Japan excellent teams for every foreign doctrine.

Develop naval staff work, maritime escort research, amphibious logistics, engine production, radar/electronics, army logistics and modern combined-arms work where gaps are verified. Existing strong institutions remain useful. Initial additions should be about 6–10 distinct institutions/upgrades, with event investment or historical availability; avoid twelve near-identical skill-9 teams.

New institutional teams are preferred where a single famous person is already doing every job. Separate carrier doctrine, submarine doctrine and merchant protection. Improve the marine school's missing equipment/vehicle coverage through an appropriately dated development, without making it a universal aircraft or industrial team.

Ministers and military leaders retain historical identities, real role distinctions, balanced traits and sensible availability. A national defeat, victory or survival can change retirements. Do not force a death merely because the historical calendar has reached it if that death depended on a battle that did not happen. Do not arbitrarily resurrect leaders who actually died in this campaign. Cabinet alternatives must offer credible naval, army, industrial and diplomatic choices.

Keep existing Japanese sprites and national model art. Audit every new unit model for the correct icon, sprite and brigade image. New portraits use distinct historical images where available; new institutions and fictional formations receive unique appropriate art rather than repeated stock faces. Budget an initial 12–16 distinct event illustrations for major new content, with reusable national frames but distinct subjects. The first playable version must not depend on completing a cosmetic overhaul of the entire world.

Use Blood and Iron's terrain treatment as the starting map. Any later map/UI improvement is a separately tested change; the India terrain prototypes, colours and experimental overlays are not imported.

## 14. Event and interface rules

Routine decisions stay short and actionable. Normally show about 4–6 recurring investment/cooperation choices plus whatever country settlements are genuinely eligible. This is a presentation target, not a hard cap that hides another country's settlement. Multiple wars and settlements must work together.

Every decision answers: what can I do, why now, what will it cost, what will change, and what becomes unavailable. Country, port and treaty names replace “theatre,” “ledger,” “record” and “route” language. Backend flags are not shown as a game mechanic.

Descriptions normally use 60–120 plain-language words; major settlements can use up to about 160 after in-game layout testing. Action labels should usually fit within 55–65 characters. Actual window fit takes precedence over those provisional limits. No appended coloured helper paragraph, dangling localisation control code or unreadable yellow/white text. Consequences belong in the localised text and supported command tooltip.

Most investment choices have three credible alternatives, including delay. Permanent changes explicitly say permanent. Expensive optional settlements can be declined for now or dismissed permanently without closing an unrelated country. Country surrender triggers never require the player to reopen a monthly council or record a result manually.

Example player text:

> **A government for China**
>
> The Nationalist government has lost Chongqing and the army can no longer defend the main industrial centres. We can establish a Chinese government, keep the occupation, or offer a narrower peace. A Chinese government will hold its own national territory and rebuild an army. Japan will retain the ports named below.
>
> **Establish a Chinese puppet; keep the agreed naval bases**
>
> **Offer a limited peace and keep our listed gains**
>
> **Continue the occupation**

Every offer must use the actual validated objective list and ports; this example is tone guidance, not final event text or a promised exact trigger.

## 15. Initial event catalogue

These are player-facing content beats, not engine IDs. Each may reuse/rewrite an existing event and require several hidden receiver/completion events. Do not inflate the content count by treating every country acknowledgement as a new decision.

| Module | Planned content beats | Behaviour |
| --- | --- | --- |
| Historical preparation, 8 | Naval estimates; aircraft works; army supply works; merchant expansion; naval schools; army logistics school; mobilisation readiness; Pacific preparations. | Paid preparation that preserves the historical diplomatic sequence. |
| Naval recovery, 8 | Wartime shipbuilding; conversion choice; escort programme; home dockyards; forward repair base; emergency rebuilding; naval aviation replacements; second construction review. | Competing investments and a way back from defeat. |
| Fuel and shipping, 8 | Southern oil repair; oilfield expansion; tanker programme; convoy escorts; maritime patrols; fuel discipline; synthetic fuel; shipping emergency. | Gains depend on real facilities, shipping and costs. Site-specific completions are technical subevents. |
| China, 9 | First peace offer; decisive settlement; government/borders; army reconstruction; industrial recovery; equipment mission; expeditionary agreement; remaining resistance; later autonomy. | Difficult conquest followed by a useful state and continued choices. |
| India, 8 | Independence contacts; recruitment; Bengal administration; national settlement; base treaty; army recovery; Indian Ocean contribution; later autonomy. | Japan-specific content without importing the Indian player overhaul. |
| Southern partners, 9 | Philippines; Indonesia; Malaya/Singapore; Brunei/Sarawak arrangements; Indochina; Thailand; Burma; Hong Kong; local defence financing. | Country-specific outcomes with explicit territory and costs. |
| Pacific/Australia, 7 | Hawaii; Australian preparation; Australian settlement; New Zealand; Pacific base investment; forward airfields; American counteroffensive warning. | Useful conquests and changing operational pressure. |
| Germany/USSR/Mediterranean, 10 | Submarine exchanges; Axis material mission; Soviet pressure; Soviet-war confirmation; Far East settlement; deeper Siberian settlement; joint Soviet terms; Indian Ocean pressure; Egypt/Suez; Mediterranean expedition. | Choices remain available together when the actual situation permits. |
| USA and 1945–1950, 12 | Initial peace approach; revised terms; armistice implementation; mainland demands; US defeat; empire reconstruction; Chinese autonomy; Indian autonomy; demobilisation; naval limitation talks; arms modernisation; treaty expiry/renewed crisis. | Multiple satisfying endings and a substantial aftermath. |

Total planning envelope: **79 substantive new or substantially revised content beats**. Counts are a scope estimate, not a quota and not 79 events guaranteed to appear in one campaign. The catalogue includes related follow-ups across alternative outcomes. Broad world-AI repairs and inherited historical events are additional work, not padding for this number.

## 16. Settlement implementation contract

The country-specific front end uses a shared tested technical pattern:

1. Confirm that the proposed recipient exists or can legally be released; identify its current master, alliance, wars and relevant units.
2. Confirm actual ownership and control of every affected province. A Japanese controller cannot simply transfer an allied owner's province as if it owns it.
3. Record the specific intended outcome, using a unique country transaction flag. Validate all preconditions before charging the player.
4. Handle alliance withdrawal, former puppet mastery and intended peace with receiver events in the appropriate countries. Test the engine's order of operations.
5. Create/change the government, transfer only the specified territory, assign the intended master and grant the access/base rights stated in the offer.
6. Preserve or reconstruct local forces once; provide a modest operating reserve and load the correct AI.
7. Recheck after one day and again after about seven days. Mark settlement complete only after ownership, mastery and relevant war relationships match the offer. A failed grant triggers a specific repair/refund, not a false victory announcement.

Some steps may need reordering for the engine; the required final invariants are fixed. The prototype must establish the safe ordering before this procedure is copied across countries.

The event manual documents `peace value = 0` as alliance-wide peace and `value = 1` as separate peace with alliance withdrawal. Neither is a universally safe single-country surrender command. Puppeting may change war participation. A puppet cannot be promised protected neutrality until that combination is actually proven; the default neutral association is an independent state with treaties.

`independence value = 0` can switch units in the area; `value = 1` leaves them with their existing owner. Do not unintentionally give Japan's expeditionary army to a newly released state. Territory transfers distinguish ownership, control, cores and claims. Access is not ownership, and removing a core is not a universal fix for a failed transfer.

No peace reward adds automatic Japanese dissent for winning or creating a puppet. A harsher settlement or breached promise can carry a clearly stated political cost. If the engine automatically applies a release penalty, offset only the known transaction-specific penalty once, rather than giving a blanket dissent reduction or farming bonus.

Treaties do not trap units without transit or supply. Preserve access until troops can withdraw, or explicitly keep agreed bases and corridors. Verify both directions of access, allied-owner cases and forces in a third country. Manual annexation must be recognised so the appropriate subsequent release decision can still appear.

Cooldown events require `save_date = yes` when using elapsed-event-day tests. Timed holdings are rechecked at completion and reset when lost. Recurring benefits are bounded, cannot stack on reload, and cannot be farmed by release/reannexation. Avoid a giant shared flag tree: each country/project owns its small state and has one authoritative completion.

## 17. Technical feasibility and design audit

| Proposal | Supported basis | Remaining proof before implementation is accepted |
| --- | --- | --- |
| Country puppet, access, ownership and core repairs | Documented engine commands and existing Blood and Iron examples. | Order, alliance effects, unit allegiance and third-party ownership. |
| Delayed paid construction | Documented event scheduling and build commands. | Costs, manpower checks, queue recalculation, cancellation and repeat safety. |
| Production improvements | Unit/brigade build modifiers exist. | Full stacking, conversions, queued versus newly ordered units and actual IC-days. |
| Ship repair projects | Ports, unit reinforcement parameters and general reinforcement efficiency exist. | A safe naval-specific effect; no undocumented naval repair command. |
| Combat-loss-triggered rebuilding | The manual documents equipment-loss triggers. | Exact categories, counter timing and whether intentional scrapping can be excluded. |
| Merchant shortage warnings | Total convoy trigger and economic state checks exist. | Route demand/unassigned reserve may not be directly observable from an event. |
| Pilot training | Existing modifiers and institutions can represent training. | No invented independent pilot pool; appropriate impact on CAG/CVL/land air. |
| US naval defeat/armistice | Ship-type counts, losses, holdings and timed events exist. | Usable loss categories, adequate non-exploitable thresholds and safe limited peace. |
| Useful puppets | Core/territory/AI/force/resource commands exist. | Tribute thresholds, supply retention, local IC, recruitment and real deployment. |
| Axis endurance | AI files, economic events and finite assistance can be changed. | Multi-run evidence; not guaranteed by changing one front ratio. |

The main design risks are deliberate and visible:

- Improving Japanese industry, ship discounts, oil, pilot training and puppets all at once can multiply into an effortless campaign. Add them in stages and compare combined outcomes.
- Fixing Chinese cores can create a very strong partner. Count its existing army and constrain export commitments, not its legitimate homeland economy forever.
- Helping Germany too much can collapse the USSR and remove the player's later Soviet challenge. Test Germany-alone and two-front Soviet cases separately.
- A negotiated US peace can accidentally become easier than conquering Australia. Require duration, maintained holdings and a surviving threat, then test plausible counterexamples.
- More content can recreate India's clutter. Keep country-specific conditions, permanent dismissals and a limited routine decision list.
- 1950 content can become a new railroad. Tie it to the existing government, victory terms, rival powers and actual treaties.
- The clean-copy comparison is strong local evidence, but inherited syntax defects still exist. Source cleanliness and gameplay correctness are different checks.

## 18. Delivery order and acceptance

| Stage | Deliverable | Exit condition |
| --- | --- | --- |
| 0: baseline | Separate Japanese mod folder; manifest; corrected inherited syntax; visible build identity; documented source exclusions. | Clean 1933 launch, correct launcher target, no custom Indian opening, unique IDs and no source errors. |
| 1: foundations | China/India settlement prototypes; resource/shipping measures; research coverage; naval production baseline. | Both puppets work, own correct territory, preserve access and retain useful armies/supply. |
| 2: endurance | Paid production/recovery programmes; Axis AI assistance; Soviet reaction to two fronts. | Germany/Italy have working assistance and the player can recover from naval losses without infinite rewards. |
| 3: expansion | Country settlements, Australia, Suez, Siberia and German cooperation. | Parallel campaigns resolve independently and the historical 1933 choice still permits later Soviet war. |
| 4: endings | Pacific armistice, US invasion outcomes and 1945–1950 content. | Treaties preserve the promised wars/territory; late content follows the actual outcome. |
| 5: release | Complete Hard calibration, event-art pass, walkthrough and issue list. | New-game and reload tests pass; remaining limitations are named. |

The first playable alpha follows stages 0–2, not an unfinished collection of all 79 content beats. A full-content release includes stages 3–5. Do not call the full expansion complete because the title screen loads.

Required test scenarios:

| Test | Expected result |
| --- | --- |
| Historical 1933 opening to Pearl Harbor | Main historical diplomacy preserved; no Indian player expansion or early forced route selection. |
| Hard China war, early and late victory | Tough fighting; decisive defeat produces a settlement; remote provinces cannot permanently block it. |
| Chinese puppet with a tiny surviving army and with a large intact army | Correct cores/industry; useful recovery; existing divisions counted; no duplicate grants. |
| Japan conquers India without German help | Japan-specific settlement, correct master, useful ministers/teams/forces and explicit bases. |
| Three eligible country settlements at once | All independently usable; no “choose one theatre” restriction. |
| Settlement where an ally owns a port but Japan controls it | Correct owner's receiver handles transfer, or the offer clearly excludes that port. |
| British/US/Soviet wars overlap | Settling a minor does not end those wars. A major peace has exactly the disclosed scope. |
| Troops crossing a newly settled country | Transit and supply remain usable; no stranded Siberian/Indian expedition. |
| Serious naval defeat, successful rebuild and repeated emergency request | Real paid recovery; no sunk-ship restoration, disband exploit or endlessly stackable bonuses. |
| Resource region lost during recovery project | Benefits pause/fail according to stated rules; no invisible permanent oil source. |
| Historical North Strike rejection, then Soviet war after Pearl Harbor | New Soviet decision appears without an old route flag; separate-war options function. |
| Germany AI / Italy AI / Finland AI | Assistance actually arrives and remains supplied; no human-only replacement chain. |
| Eight hands-off Hard runs plus focused human Japan tests | Record Axis survival, front positions, oil, manpower, usable IC, army strength and US naval rebuilding. Report the small sample honestly. |
| Pacific armistice, rejected offer, mainland invasion and continued war | Separate, understandable outcomes; no infinite daily offers or accidental global peace. |
| Manual annexation, liberation, treaty refusal and permanent dismissal | Subsequent decisions recognise the real state; declined content stays dismissed as promised. |
| Save/reload during pending construction, negotiations and settlement | Costs and rewards apply once, cooldowns survive, outstanding grants complete correctly. |
| 1947, 1949 and 1950 checkpoints | Appropriate leaders, teams, units, artwork and politics; victorious Japan is not forced into historical occupation. |
| Long decision descriptions and all major reward tooltips | Readable at the actual game resolution; no spillover, raw keys or coloured helper debris. |

Use source validation, targeted test saves and manual play. Structural parsing is not a substitute for engine execution. No game was launched for this specification, and no performance or balance target above is yet playtested.

## 19. Review decisions

The proposed direction is: improve Japan's capacity to sustain and rebuild a war; make China and India useful; repair European Axis support; keep America capable of returning; and make victories lead somewhere through 1950.

Implementation should start with the cleaner baseline and the two puppet/peace prototypes. These determine whether the larger content plan can deliver reliable outcomes. Follow with shipping/fuel and Axis endurance, then expand the campaign. This order addresses the specific failures observed in the saves before increasing the event count.

### Source references and reproduction

Candidate baseline: `C:\Users\Mohsin Dingankar\Downloads\Blood and Iron v1.1`.

Save source: `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\Blood and Iron v1.1\scenarios\save games`.

Primary local references: `Readme.txt`; `scenarios/1933.eug`; `db/events.txt`; `db/revolt.txt`; `db/difficulty.csv`; `db/events/japan.txt`; `db/events/USA.txt`; `db/events/UK.txt`; `db/events/new_events.txt`; `db/events/Mods.txt`; `db/events/Add_on.txt`; `db/events/Gameplay.txt`; the `db/events/Japan`, `db/events/China` and `db/events/AI` folders; Japanese unit, team, minister and leader files; relevant Axis/Allied AI files.

Engine reference: `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Modding documentation\event commands.txt`, `AI Files Modifiers.txt`, and `Invasion AI - How To.txt`. Some AI documentation identifies an older engine version; all important assumptions still need runtime confirmation on the installed executable.

Read-only audit helper: `tools/audit_japan_baseline.py`. `events` inventories the scenario event files and reports structural warnings; `inventory JAP` summarises Japanese content; `save '<filename>'` reads an installed Blood and Iron campaign and reports countries, resources, deployed forces, queues, provincial IC and convoy allocations. It does not modify saves or source files. Compact division types are decoded using the unit-file MODEL indices; template and save statistics are not a calculated effective-combat-strength rating.
