# Japan Grand Campaign Guide

## Verdict

The proposed campaign is feasible, but it is a **9/10 difficulty run**: join or formalize with Japan, win Southeast Asia, take useful Philippine positions, help decide China, break the British route through Suez and then open a Caucasus front against the Soviet Union.

The difficulty is not any one objective. It is the combination of four supply systems, a weak starting transport/fleet position, occupation load, dissent from repeated declarations, and the formal alliance's single shared-war system. A player can do it by sequencing the wars. Trying to fight China, Britain, the Netherlands, Australia, the United States and the Soviet Union at full intensity at the same time is likely to collapse India before Germany is helped.

This guide is based on the event source, not a completed Alpha 23 campaign playtest. Province control must be Indian unless an event explicitly accepts friendly-owner liberation credit.

## Current playtest save

The newest 29 Aug autosave is a different game from the older December 1941
manual save. It is an **Alpha 22** India campaign at **1 December 1934**. India
is peaceful, uncommitted and still recorded as sovereign; it has not yet tested
the Japanese alliance or Alpha 23 route events.

Its production plan is already maritime: five transports, twelve destroyer
flotillas, two carriers, long fighter series, three marines, convoy/escort
capacity and six parallel factory programmes are in the queue. The deployed
force is less ready than that queue suggests: 57 mostly brigade/cadre land
formations, one transport flotilla, no combat surface fleet and two air-defence
wings. There is no visible dedicated mountain formation. Before the Soviet
phase, add a mountain/mobile Caucasus group and protect reinforcement, upgrade
and supply IC from the very long naval and air series.

The installed V4.2 folder identifies itself as Alpha 22. It is the correct
installed mod family, but it is not this Alpha 23 source candidate. Its early
Emergency War Cabinet is therefore the old behaviour that Alpha 23 replaces.

## What Alpha 23 changes from Alpha 22

| Mechanic | Alpha 22 behaviour | Alpha 23 behaviour |
| --- | --- | --- |
| Formalizing a senior Tokyo compact | War Cabinet event `9281914` unconditionally replaces senior/full-sphere status with peer/core. | Event `9281914` preserves and repairs an existing senior/full-sphere pair. Only a fresh formal entrant receives peer/core. |
| China policy after formal entry | Event `9281130` can appear because the partnership flag survives, even though its text says China is outside the compact. | Event `9281130` is compact-only: neither an engine alliance nor the formal-alliance flag may be present. Formal allies already share Japan's China war and do not receive a contradictory separate-policy choice. |
| Indian Ocean settlement warning | Event `9281160` converts a formal Japanese relationship to separate command when its separate peace is ratified, but its player text does not make that consequence explicit. | Both the decision summary and ratification description warn that separate peace ends formal shared-war membership and continues the relationship as a separate-command Tokyo compact. Peace legality is unchanged. |
| Out-of-focus victories | A generic victory outside the chosen wartime charter can consume the single route-achievement flag and block the intended primary achievement. | Secondary victories are recorded as secondary standing. They do not complete or relabel the selected primary focus and do not unlock its congress by themselves. |
| Route campaign | Distant fronts rely mainly on common country and theatre ledgers. | Four authored Japanese primary arcs now have activation, intermediate milestone, three-way dilemma and culmination. An optional four-theatre ledger tracks this exact human plan without replacing the selected primary. |
| Southern theatre under a compact | The India-led board waits for Japan itself to enter a listed southern war. | India's own war against Britain, the East Indies, the Netherlands or Australia can open the board. Japan is not falsely treated as a belligerent. |
| Caucasus help for Germany | Indian success helps only by physically diverting Soviet forces. | India may also send one finite, conditional German-scoped relief convoy after taking Baku plus Tbilisi or Astrakhan while Germany still holds Berlin and both fight Moscow. |

Alpha 23 therefore fixes the two most dangerous Japan-route state
contradictions--formal entry no longer erases earned Tokyo seniority, and a
compact-only China choice cannot fire after formal entry--while also giving the
human grand campaign an explicit optional ledger and finite Caucasus relief.

## The first irreversible choice: compact or formal alliance

### Strategic compact

`9281100`, **Open the Delhi-Tokyo Strategic Conference**, is available from 1937. It costs 350 money and 600 supplies. The compact is not an engine alliance: India and Japan choose wars and peace separately.

Tokyo evaluates India as follows:

| Bid | Required Indian position | Japanese response |
| --- | --- | --- |
| Senior/full sphere | Influence 7, IC 160, and either 75% of Japan's land force, 45% of its navy or 12 air wings | 70% accept / 25% counter / 5% reject |
| Peer/core sphere | Influence 4 and IC 110 | 40% accept / 45% counter / 15% reject |
| Aspirant | Below the peer threshold | 15% accept / 50% counter / 35% reject |

A later review, `9281135`, opens from 1938 at influence 7 and IC 140 with either 65% of Japan's army, 35% of its navy or 10 air wings. It costs 300 money and 500 supplies; Tokyo's fixed result is 60% accept, 30% defer and 10% reject.

The compact is the safer framework for an independent Soviet war. Event `9281180` is available from 1940 only while India is outside a formal Japanese alliance. It costs 700 money, 1,800 supplies and 5 dissent. Japan then chooses 55% neutrality plus supplies, 25% pressure without war, 15% entry into the Soviet war or 5% condemnation.

### Formal alliance

War Cabinet event `9281914` is available from 1937 and creates one engine alliance. Base cost is 4 dissent. A commercial-policy reversal adds 3 dissent and costs 300 money; lacking the early Japanese policy adds another 2 dissent. A fresh entrant receives peer/core status. In Alpha 23, an existing senior/full-sphere compact keeps that rank.

The older compact conversion decision, `9270407` in `india_v3/40_diplomacy.txt`, opens from 1939 and costs 6 dissent. It also creates one shared war system and does not rewrite the Tokyo tier.

Formal entry has three consequences:

1. India inherits all current Japanese wars, including China. Japan inherits all current Indian wars, including a Soviet war.
2. Future declarations by either partner normally become wars of both partners.
3. A separate peace is incompatible with continuing formal shared-war membership. Ratification converts the political relationship back to a separate-command compact.

For this campaign, the best political sequence is:

1. Open the compact conference first if India can credibly earn peer or senior terms.
2. Resolve compact-only China policy `9281130` before formalization if the player wants that political choice. Backing Japan gives +2 influence and +4 dissent.
3. Formalize through `9281914` when ready to inherit Japan's live wars. Alpha 23 preserves an earned senior/full sphere.
4. If India cannot meet the 1937 conference thresholds, direct formal entry is faster but begins at peer/core. Earn the full southern sphere through the southern charter or a later seniority review.

## Recommended campaign sequence

### Phase 1: 1933-1937 preparation

India begins too militia-heavy and transport-poor for a four-ocean war. Before formal entry:

- create one mobile Burma-Malaya army, one amphibious reserve and one mountain force for Persia/Caucasus;
- build enough transports to move a corps without emptying the home coast;
- build escorts and modern surface ships instead of counting obsolete hulls as a sea-control plan;
- stockpile supplies, money and oil for treaty costs, declarations and overseas operations;
- improve air cover over the Bay of Bengal and Malacca before exposing the transport fleet.

Practical planning targets, not event gates, are roughly 9-12 good divisions for the Burma-Malaya axis, 6-9 divisions in the amphibious reserve and 9 mountain/mobile divisions reserved for Persia and the Caucasus. The exact mix depends on difficulty and the state of China.

### Phase 2: choose the Tokyo rank and war system

The safest high-ceiling route is compact first, seniority if achievable, then formalization. The fastest route is direct formal entry in 1937, accepting peer/core and high dissent.

Once at war, `9283213`, **The Delhi-Tokyo Wartime Charter**, asks for one primary focus:

- **Indian Southern Sphere** is the cleanest Southeast Asian specialization and grants full-sphere recognition.
- **Northern Coalition Campaign** supports either a separate compact Soviet war or a formal Delhi-Tokyo coalition war.
- **Indian Ocean First** rewards a western victory through the Gulf, Suez or East Africa.
- **Equal Asian Command** rewards broad two-theatre or decisive performance.

For the exact China-Philippines-SEA-Australia-Suez-Caucasus plan, select
**Equal Asian Command**. Its first authored milestone accepts a Philippine,
China, Siam or Southeast Asian result, and its culmination accepts Southeast
Asia plus China/Philippines or two national theatres. If the immediate goal is
instead the easiest southern political payoff, **Indian Southern Sphere** is a
valid lower-risk primary. In either case, the optional grand-campaign ledger
tracks all four theatres as secondary history and cannot steal the primary.

### Phase 3: limit the China commitment

Formal entry joins Japan's China war. Current common campaign logic recognizes an Indian capture of Nanjing (province 1337) through `9282200`; settlement `9282210` offers a 60/25/15 pairwise armistice or post-annexation political choices. India must control the objective itself. Japanese occupation does not earn Indian credit.

The best use of India in China is a bounded southwest/central thrust that fixes Chinese formations and seeks Nanjing only if the route is open. Do not feed the whole Indian army into the Chinese interior while the southern fleet is still unprepared. Current base events do not give a staged reward for merely helping Japanese AI advance; the compact-only political support choice and Indian-controlled campaign objectives are what count.

Do not sign a separate Chinese peace while formal shared-war membership is still needed for later fronts.

### Phase 4: open and win the southern theatre

`9281140`, **Open the India-Led Southern Theatre**, is available from 1938 after the Tokyo partnership exists and either India or Japan is at war with Britain, the East Indies (`U05`), the Netherlands or Australia. Under a formal alliance, the war is shared. Under a compact, India's own qualifying war opens its Indian ledger but does **not** force Japan into that war.

The published six-point victory is much smaller than conquering every victory province:

| Event | Indian-controlled objectives | Score |
| --- | --- | --- |
| `9281142` | Rangoon 1415 + Imphal 1442 + Port Blair 1421 | 1 |
| `9281143` | Singapore 1432 + Kuala Lumpur 1438 | 2 |
| `9281144` | Palembang 1636 + Batavia 1647 + Soerabaja 1653 | 3 |
| `9281145` | Darwin 1697 + Canberra 1707 + Sydney 1705 | 3 |
| `9281146` | Six total points, Malaya still held, and either the DEI trio or Australian trio still held | Southern victory |

The shortest reliable line is Burma-Andamans (1) + Malaya (2) + the three DEI hubs (3). **There is no requirement to occupy every Dutch East Indies victory province.** Australia is an alternative three-point wider theatre, not an additional requirement for southern victory.

Japanese occupation transfers are tier-sensitive:

- `9281150` returns Japanese-controlled Burma-Andaman positions to Indian controller status.
- `9281151` returns Malaya/British Borneo under core or full-sphere terms.
- `9281152` returns Japanese-controlled East Indies only under full-sphere terms.
- `9281153` returns Japanese-controlled Australia only under full-sphere terms.

These are controller corrections, not final ownership. A strained partnership disables them. A peer/core formal entrant should race for Palembang, Batavia and Soerabaja or earn full-sphere status before Japan occupies them.

### Phase 5: establish the sea lanes

The route-neutral Southeast Asian module does not infer naval victory from land control. It checks ready Indian surface combatants:

| Event | Port chain | Ready surface ships |
| --- | --- | --- |
| `9287660` | Rangoon + Port Blair | 8 |
| `9287661` | Singapore/Kuala Lumpur + Palembang or Batavia | 12 |
| `9287662` | Batavia + Soerabaja | 16 |
| `9287663` | Singapore + Saigon or Manila | 18 |

The six-point Japan partnership victory does not require these fleet thresholds, but a convincing land-and-sea theatre and several route achievements do. Lost ports or insufficient ready ships suspend current sea-lane credit while preserving the historical one-time achievement.

### Phase 6: take the Philippines before Japan

The Tokyo treaty assigns China, the Philippines and the Pacific to Japan even under senior terms. No Japan-partnership event transfers the Philippines to India.

India can still earn route-neutral operational credit through `9287650` by controlling Manila 1565 and Davao 1579 against the same legal owner in a live war. If the United States is the legal owner, `9282139` adds a limited American victory when India also controls Guam 1683 or Wake 1673.

The practical rule is simple: land before Japan. If Japanese forces take the islands first, the Tokyo boundary does not hand them to India. An accepted American armistice (`9282189` -> `9282187`) can transfer Manila, Davao, Guam and Wake only when America legally owns the relevant province and India controls it. That armistice is a separate peace, so delay it until formal shared-war membership is no longer needed.

### Phase 7: open the western road to Suez

The British campaign brief, `9282120`, defines:

- limited victory: Singapore + Kuala Lumpur + one of Aden 1053, Suez 900 or Mombasa 842;
- decisive victory: the limited result plus any two of Aden, Suez, Cape Town 880 and London 29.

Therefore Singapore + Kuala Lumpur + Aden + Suez is already enough for a decisive British result: Aden satisfies the western hinge and Aden plus Suez satisfy the two decisive objectives.

National western event `9281941` also recognizes any two connected arcs:

- Suez plus a Gulf objective (Aden, Baghdad or Tehran);
- Suez plus an East African objective;
- a Gulf objective plus an East African objective.

The most efficient route is India -> Arabia/Aden -> Suez, with East Africa used only if the Red Sea route is blocked. The British armistice transfers occupied Malayan positions, not Suez, Aden or African territory. Western occupation creates recognition and settlement leverage; it is not an automatic Indian annexation award.

### Phase 8: Australia after the bases, not before

Australia requires Darwin, Canberra and Sydney for the three-point Japan-route objective. The distance makes it much easier after Singapore, Batavia and Soerabaja are secure repair and supply hubs.

Event `9281160` deliberately does not turn the Australian continent into stable Indian annexation. Its outcomes are sovereign commonwealth, protectorates or direct mandates for captured Malayan/Indonesian territory; Australia remains sovereign or protected. Treat Australia as a military and political objective, not a permanent map-painting prize.

### Phase 9: attack the Soviet Union while Germany can still benefit

Do this last among the opening wars, ideally in 1940 or early 1941. The main
benefit remains physical: Soviet formations, oil and supply are diverted from
Germany. Alpha 23 adds only one modest convoy after India proves the Caucasus
road; it does not give Germany a passive survival modifier or rewrite German AI.

The Soviet campaign brief, `9282122`, defines:

- limited victory: Baku 713 plus Tashkent 1103 or Astrakhan 706;
- decisive victory: Moscow 572 plus one of Stalingrad 663, Baku or Tashkent.

National northern event `9281942` recognizes any two among Baku, Tashkent, Astrakhan and Moscow. For the intended campaign, Persia -> Baku -> Astrakhan is the shortest coherent pair. Afghanistan/Central Asia -> Tashkent is a second axis, but it should not be opened until the southern supply line is stable.

Under a formal Japanese alliance, War Cabinet confirmation `9281922` costs 5 dissent and Japan inherits the Soviet war. Under the compact, use `9281180` for a separate Indian war and accept that Japan has only a 15% chance to join; 80% of outcomes keep Japan out. The Alpha 23 **Northern Coalition Campaign** can culminate under either legal structure.

The optional Caucasus relief becomes selectable only when India and Germany
are both fighting the Soviet Union, Germany exists and controls Berlin (163),
and India controls Baku (713) plus Tbilisi (709) or Astrakhan (706). Dispatch
costs India 1,200 supplies and 500 oil. Germany receives 900 supplies and 350
oil through a German-country callback, once. Defer simply leaves the manual
option open; decline closes it without cost.

### Phase 10: complete the optional four-theatre ledger

The ledger (`9289645-9289652`) is available under a live Tokyo compact or
formal alliance. Its final acknowledgement requires all of the following:

- Southeast Asian victory **and** the Australian regional result;
- a formal-alliance China field-command posture and an actual victory over
  China or Communist China;
- a Philippine land or liberation allocation;
- Aden, then Suez, then an Ethiopian, South African or national Western result;
- confirmed delivery of the one-time Caucasus relief convoy.

Completion gives 200 money, 300 supplies and -2 dissent. It is secondary
acknowledgement only: it awards no second charter, Congress, territory or peace.

## The settlement rule that can end the campaign plan

`9281160`, **Convene the Indian Ocean Settlement**, is available after the southern victory. Its three paths cost:

| Settlement | Cost and immediate political effect |
| --- | --- |
| Sovereign Commonwealth | 300 money, -2 dissent |
| Protectorates | 700 money, 1,200 supplies, +5 dissent |
| Direct mandates | 1,000 money, +9 dissent, occupation burden |

The event offers separate peace to the relevant British, East Indies, Dutch and Australian opponents. If India is formally allied with Japan, ratification ends formal shared-war membership and continues the Tokyo relationship as a separate-command compact.

**Do not press this decision when it first appears.** Complete every front for which Japanese war inheritance is still useful first: Philippine landings, the desired China result, Suez and the Soviet declaration. Then settle. The same caution applies to other pairwise great-power or regional armistices.

## Feasibility by objective

| Objective | Difficulty | Feasibility judgment |
| --- | --- | --- |
| Burma, Malaya, Singapore | 4/10 | Strong opening if forces and air cover are prepared before 1938. |
| DEI three-hub victory | 6/10 | Feasible; the player needs only Palembang, Batavia and Soerabaja, but must beat Japan to control or have full-sphere transfer rights. |
| Philippines + Guam/Wake | 8/10 | Feasible only with an early amphibious race and enough fleet/air cover against the United States. |
| Australia trio | 8/10 | Feasible after DEI bases; inefficient as the first wider theatre. |
| Useful China contribution | 6/10 | Feasible as a bounded thrust; full conquest is a manpower and supply trap. Indian control of Nanjing is the published common result. |
| Aden and Suez | 7/10 | Feasible after Malaya; strong event payoff because it can complete the decisive British result. |
| Baku and Astrakhan/Tashkent | 9/10 | Feasible only after southern stabilization and with a dedicated mountain/mobile army. |
| Entire combined campaign | **9/10** | Winnable with phased declarations and delayed peace; likely to fail if all theatres are opened simultaneously. |

## Critical blockers and edge cases

- A compact can open `9281140` from India's own qualifying southern war; that does not put Japan at war.
- A formal alliance shares declarations. It is the easiest way to force the southern and Soviet wars, but it also imports every unwanted Japanese war.
- Fresh formal entry is peer/core. DEI and Australian Japanese-controller transfers require full-sphere status.
- Tokyo's treaty always leaves the Philippines to Japan. India must capture its own objectives and cannot expect a post-capture handover.
- All published land achievements require Indian control, not merely alliance control, unless their text explicitly permits friendly-owner liberation credit.
- Southern victory needs six points and current Malaya plus DEI or Australia. A stale historical flag is not enough if the key objectives have been lost.
- Great-power and regional settlements are pairwise. They do not end unrelated Indian wars, but separate peace ends formal shared-war membership.
- Suez, Aden, Africa, the Caucasus and the Australian continent are not automatically granted to India by their victory events.
- Full grand-campaign completion deliberately requires formal China command boundaries; a permanently separate compact can record the other chapters but cannot finish that acknowledgement.
- The Germany convoy is one finite callback, not a global German survival fix. It requires Berlin to be held when India reaches the Caucasus gate.
- Static validation can prove event structure and state contracts; only a full campaign playtest can prove AI timing, naval survivability and late-war performance.

## Event source index

| System | Event IDs | Source |
| --- | --- | --- |
| Tokyo conference, China policy, seniority, southern theatre, transfers, settlement, independent Soviet war | `9281100`, `9281130`, `9281135`, `9281140-9281165`, `9281180-9281185` | `mod/db/events/aubm_v4/35_japan_partnership.txt` |
| War Cabinet formal entry and declarations | `9281911-9281925` | `mod/db/events/aubm_v4/41_wartime_state.txt` |
| National southern, western and northern victories | `9281940-9281942` | `mod/db/events/aubm_v4/42_wartime_theatres.txt` |
| British, Soviet and American campaign objectives/armistices | `9282120`, `9282122`, `9282139`, `9282187`, `9282189` | `mod/db/events/aubm_v4/45_enemy_campaigns.txt` |
| Regional China result and settlement | `9282200`, `9282210` | `mod/db/events/aubm_v4/46_regional_campaigns.txt` |
| Japan wartime charter and legacy achievements | `9283213`, `9283250-9283253` | `mod/db/events/aubm_v4/48_route_wartime_consequences.txt` |
| Alpha 23 Japanese authored arcs and grand ledger | `9289620-9289652` | `mod/db/events/aubm_v4/51_bespoke_route_arcs.txt` |
| Philippines land victory and sea-lane achievements | `9287650`, `9287660-9287663` | `mod/db/events/aubm_v4/50_southeast_asia_operations.txt` |
| Older compact-to-alliance conversion | `9270407` | `mod/db/events/india_v3/40_diplomacy.txt` |

## Short play checklist

1. Build transports, escorts, mobile infantry, mountain troops and air cover before formal entry.
2. Seek the best Tokyo compact rank India can actually qualify for.
3. Resolve compact-only China policy if desired, then formalize.
4. Choose **Equal Asian Command** for the full grand campaign, or **Indian Southern Sphere** for the lower-risk southern specialization.
5. In China, make a bounded supporting thrust; do not drain the southern army.
6. Open the southern theatre from 1938.
7. Hold Rangoon/Imphal/Port Blair, Singapore/Kuala Lumpur and Palembang/Batavia/Soerabaja.
8. Race India, not Japan, into Manila and Davao; add Guam or Wake if fighting America.
9. Take Aden and Suez for the decisive British result.
10. Use the DEI chain as the base for Australia.
11. Open the Soviet war in 1940/41 and drive Persia -> Baku -> Tbilisi or Astrakhan.
12. If Germany still holds Berlin and fights Moscow, dispatch the one-time relief convoy.
13. Ratify separate settlements only after formal shared-war membership has served its final purpose.
