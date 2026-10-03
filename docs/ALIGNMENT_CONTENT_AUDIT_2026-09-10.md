# Alignment content audit: Japan is overrepresented

## Verdict and scope

The five alignments are not empty alternatives, but they are not equally rich.
Japan has both a developed partnership campaign and a developed enemy/liberation
campaign. Other alignments have useful diplomacy and objectives but fewer
distinctive outcomes connecting their promises to the postwar world.

This is a read-only script/content audit, not a simulated campaign, win-rate
comparison or native execution signoff. It examines Candidate 1, checks the
specific choice-flag finding against the installed prototype, and excludes
scenario-slept events from claims about new-game content. It changes no gameplay,
save, installation or balance. Candidate 1 remains uninstalled and unverified.

## Existing coverage

All five families have four named themes in module51:

| Alignment | Existing themes | Assessment of distinctive content |
| --- | --- | --- |
| Japanese partnership | Southern sphere; northern coalition; Indian Ocean; equal Asian command | Most developed partner-specific layer: seniority, resource/carrier cooperation, Japanese occupation handovers, regional settlement bargaining and the Tibetan clause. |
| Allied | Eastern Ocean; continental expedition; anti-colonial mandate; free command | Real alternatives exist, including European objectives and defending Suez without owning it. Recognition and postwar consequences are thinner than the Japanese partnership. |
| German/Axis | Eurasian link; dismantling British empire; southern resources; parallel war | Stronger non-Japanese foundation: Persian/Afghan/Xinjiang transit and wars against Britain or USSR. The shared deep Central Asian settlement gives fighting the USSR a substantial payoff; it is not a reward for being Moscow's ally. |
| Soviet/Comintern | Anti-fascist expedition; anti-imperial ocean war; republican Asia; autonomous socialism | Substantial diplomatic setup, but the operational themes often reuse European/Asian victory records and general rewards. The anti-Soviet settlement must not be counted as Comintern content. Distinct joint-war/postwar outcomes need development. |
| Independent | Ocean league; continental arc; world balancer; republican federation | Broad freedom, bilateral diplomacy and general settlement coverage. Richest when fighting Japan and/or the USSR; independent wars elsewhere rely more heavily on shared milestone/armistice templates. |

This assesses narrative and mechanical depth, not equal numbers of events or
equal military difficulty. All paths also share domestic, industrial, military
and optional story content; twelve shared stories do not repair alignment parity.

## Source-confirmed findings

### 1. Many strategic dilemmas do not create the promised differentiation

The route generator defines twenty focuses with three dilemma choices each.
All **60 specific choice flags** are written in both the installed and staged
custom event corpora. **None has a later `flag` condition reader** in either
custom corpus. Their common focus-dilemma completion records advance the arcs;
the individual choice does not select a different culmination condition.

This does not mean every option has no effect: resource costs, terrain bonuses,
transport modifiers, dissent and shared political-credit flags can matter.
It means the specific political/operational promise is often not followed up.

Examples from the staged scripts:

- `9289553`, **The Caucasus or Central Asia?**: Baku costs 600 supplies and adds
  one mountain-attack point; Central Asia costs 500 supplies and adds one desert-
  movement point. The specific choices do not switch the later campaign target
  or create different negotiated spheres.
- `9289513`, **Who Commands the Eastern Advance?**: joint board, liberation
  mandate and reserved Indian settlement rights set different unused specific
  flags. Their labels imply more political divergence than the later arc proves.
- `9289593`, **Command of the Anti-Fascist Expedition**: coordination,
  Mediterranean command and autonomous belligerency change immediate effects
  and records, but do not create three corresponding postwar outcomes.

The reader scan covers the 58 custom event modules, not every stock script,
external tool or executable mechanism. No native campaign outcome is inferred.

### 2. Raw legacy event totals exaggerate non-Japanese campaign depth

Fresh scenario `sleepevent` entries alone yield:

| Original alignment module | Definitions in stage | Slept at scenario start | Not scenario-slept |
| --- | ---: | ---: | ---: |
| Japan, module35 | 59 | 0 | 59 |
| Allied, module36 | 65 | 48 | 17 |
| German, module37 | 78 | 40 | 38 |
| Soviet, module38 | 83 | 36 | 47 |
| Independent, module39 | 90 | 44 | 46 |

Not scenario-slept does not mean reachable, player-facing or an independent
story. These numbers exclude the replacement/shared modules and are not an
overall content score. They explain why old file sizes cannot establish parity.

### 3. The British campaign also funnels the player through Southeast Asia

`9282130` requires Singapore and Kuala Lumpur plus Aden, Suez or Mombasa for
limited British victory. `9282131` requires that limited victory before its
two-of-Aden/Suez/Cape-Town/London major threshold can count.

An independent or Axis India concentrating on Suez and Africa therefore cannot
earn that British major milestone through a wholly western campaign. This is
Southeast-Asia-centric design even when Japan is not the enemy. A separate western
success condition would be more appropriate than insisting on the Straits.

### 4. Coalition contribution is narrower than the narrative suggests

The German-war brief `9282121` and milestones `9282132/33` require Indian control
of specified cities. Allied control alone does not count. Fighting successfully
alongside a coalition does not necessarily award India the required province
control or those milestone records. A player can contribute substantially and
still receive little bespoke recognition. Native occupation assignment was not
tested here.

### 5. The best late-war systems cluster around Japan and the Soviet enemy

The extra layer includes Nanjing's break/protection, Siam and Indochina leaving
Japan, home-island consolidation and an investment dividend, and the deep Soviet
settlement with actual Central Asian governments, optional independence reviews
and a development choice. These are stronger consequences than a final supplies/
money payment alone. They also carry stricter verification requirements.

Candidate 1 genuinely broadens access: the deep Soviet hold `9289910` checks war
with the USSR and excludes being its ally, without requiring a Japanese war;
the canal defence `9289860` checks the real Axis threat and relations with Britain/
Egypt rather than requiring an independent Japanese route. These are improvements,
not proof all formerly restricted content is now universally available.

The combined legacy `9289872`, **The Two-Front Settlement**, still requires the
independent LIBERATOR/sovereign context, southern peace and Central Asian
reconstruction. Its southern requirements retain Japanese-war-linked conditions.
It is not an all-alignment endgame reward.

### 6. Shared worldwide coverage is infrastructure, not rich variety

Module47 contains 3,433 definitions for a 210-country fallback system. They
provide target handling, replies, retries, leverage and constitutional settlement
coverage. They are not thousands of different Indian adventures. Module50's
21 events concentrate on Southeast Asian hubs, sea lanes and liberation from
Japanese occupation. There is no equivalent module-sized operational treatment
in this set for Mediterranean/African coalition campaigns.

### 7. Formal alliance entry needs coalition-compatible rewards

The staged full-peace authority guard permits a sovereign India to sign when
unallied or leading its alliance. A junior member cannot simply use the same
independent peace action. This protects against the reported accidental wider
peace, but it also means a formal Allied, Axis or Comintern campaign needs useful
coalition recognition and postwar rewards while independent bargaining is
unavailable. Separate-command compacts and formal membership are not equivalent
content access. Do not remove the safety guard to fill this content gap.

## Recommended correction — not implemented by this audit

Do not create another five mutually exclusive national routes. Use a small
number of current-war theatre decisions, with local, meaningful choices and
clear terminal outcomes.

1. **British war:** offer alternative eastern and western limited/major victory
   conditions. An earned Suez–East Africa or Gulf–Red Sea campaign should not
   require Singapore merely to count.
2. **Allied war:** make Mediterranean/European contribution and coalition rescue
   earn an actual agreed outcome: Indian base rights, a supported decolonization
   settlement, or a durable military/logistics agreement. Do not promise transfers
   unless the relevant owner agrees and the result is verified.
3. **Axis war:** make Caucasus, Central Asian and imperial-sea choices change
   objectives and negotiated rewards. Add consequences for competing German and
   Indian claims, and a meaningful continuation if the German front collapses.
4. **Comintern war:** give India a distinct anti-fascist expedition payoff,
   reconstruction cooperation, and negotiated limits on Moscow's control. Fighting
   beside Moscow must have its own ending, not borrow the rewards for defeating it.
5. **Independent wars:** develop the existing Gulf/Red Sea, continental buffer
   and Indian Ocean federation themes into short campaigns with rival responses,
   a setback/recovery phase and a verified postwar result. Neither a Japanese war
   nor a great-power alliance should be a hidden requirement.
6. **Existing dilemmas first:** make a small, explicit selection of the unused
   choice records affect later terms, objectives or costs. Where a choice is only
   a tactical bonus, say so instead of implying a new political system. Do not
   activate all sixty flags into sixty extra callback chains.
7. **Coalition parity:** provide negotiated recognition or deferred postwar
   claims for junior alliance members, using verified coalition outcomes rather
   than forcing an Indian separate peace. Keep sovereign-war settlements for
   genuinely independent command.

Acceptance: every alignment should support a worthwhile campaign without fighting
or joining Japan; a western independent war should produce objectives, meaningful
decisions, setbacks and a satisfying settlement without an eastern prerequisite.
At least one decision per developed theatre must change a later outcome, not just
its wording. Test these situations independently; neither event totals nor the
existing 318 script tests certify fun or equal campaign depth.

## Evidence

Inspected staged modules35–39,43,45,47,50,51; the scenario retirement list;
`tools/generate_aubm_bespoke_route_arcs.py`,
`tools/generate_aubm_global_campaigns.py`, and
`tools/aubm_redesign_route_finish.py`. The 60-choice reader/writer check was
repeated against both staged and installed custom modules. This report records
findings and recommendations only; no corrective gameplay edit was made.
