# A Union Before Midnight: Gameplay Changes and Alpha 19 Status

This is the player-facing guide to the current **4.2.0-alpha.19** build of
*A Union Before Midnight*. It explains what changed, how the new systems are
supposed to play, what has been verified, and what still needs a real campaign
test.

Updated: 25 August 2026.

## Current Status

| Area | Status |
| --- | --- |
| Current source version | `4.2.0-alpha.19` |
| Build and static validation | Passed: 0 errors, 0 warnings after the launch-syntax fix |
| Public manifest | Passed: copied foundation/donor map files, donor sprites/palettes, donor model panels and unresolved art excluded |
| Installed-file verification | Passed: every file in the active installed manifest is present and hash-matched |
| Campaign compatibility | Start a fresh 1933 campaign |
| 1933 engine smoke | Passed: a fresh campaign reaches the playable map without the Alpha 18 parser crash |
| Human wartime playthrough | Still required |
| Source-control safety | Public-safe branch snapshot prepared; local-only assets remain excluded |

The maintained source is the `v4-direct-dh` branch. Its public installer
manifest contains only AUBM gameplay, documentation and redistribution-cleared
art. Darkest Hour foundation files, locally reconstructed donor sprites and
model panels, unresolved leader portraits, manuals, screenshots and Steam test
backups remain on the developer machine but are ignored and cannot enter the
manifest accidentally.

Alpha 18's first fresh engine launch exposed unsupported foreign-country flag
scopes in the Japanese-partnership and wartime-settlement events. Alpha 19
rewrites those callbacks using Darkest Hour-supported event logic and adds a
regression check so the invalid form cannot return.

The practical verdict is: **Alpha 19 passes a fresh 1933 executable smoke test
and is suitable for continued alpha playtesting, but it is not yet a proven
stable campaign release.** A complete human war and postwar run is still
required for balance, pacing and narrative verification.

The old `India Mod` folder is the original/base workspace. The maintained V4
source of truth is the sibling `India Ascendant` repository, and the playable
copy is the separately installed Steam mod listed above.

## What the Alpha 18 Gameplay Rework Changed

The previous playthrough exposed a clear problem: India could take Persia,
Suez, Malaya or the East Indies and receive little acknowledgement, no usable
intermediate settlement, and no satisfying sense of victory. Old V3 plans,
new V4 flags, actual alliances and current wars could also contradict each
other. That produced problems such as pro-Japanese India receiving
anti-Japanese criticism, a Japanese alliance disabling India's own southern
campaign, money collapsing during war, and no meaningful mobilisation choice.

The replacement design follows six rules:

1. **Live state outranks old choices.** Actual alliances, wars, control and
   ownership determine current policy; obsolete route flags are historical
   records rather than active commands.
2. **Every war publishes an objective.** India knows what battlefield result
   will open political leverage before it earns a reward.
3. **Victory is acknowledged immediately.** India does not wait for the entire
   world war to finish before receiving theatre feedback or opening terms.
4. **Each opponent settles separately.** Peace with Persia does not end India's
   war with Britain, Germany, Japan or another country.
5. **Annexation requires a political decision.** Restored sovereignty,
   protection and direct rule have different consequences.
6. **War has a domestic cost.** Mobilisation, debt, occupation and
   demobilisation are gameplay systems rather than flavour text.

## The Campaign Loop

The complete campaign now has five broad phases.

### 1. Build the Union

India begins independent on 1 January 1933, stretching from Ceylon to Burma.
The opening game is still about integrating an uneven federation: fiscal
settlement, rail and telegraph links, food security, industrial location,
research institutions, military reorganization, provincial politics and
constitutional leadership.

The intended economy forces priorities. India can become a top-tier industrial
power, but it should not be able to buy every premium civil, military and
diplomatic programme in the same year without debt or political cost.

#### Starting position

- 10 dissent, 425 manpower, 3,000 money and 4,000 supplies in the scenario;
  the sovereignty bootstrap immediately adds another 1,000 money.
- 46 land formations: 4 infantry, 33 militia, 4 garrisons and 5 cavalry. The
  first twelve field corps contain three divisions each.
- One naval transport flotilla and no starting air force.
- 232 inherited technologies, matching Britain's Raj-era baseline. India does
  not start with modern wartime designs, but it no longer repeats
  nineteenth-century prerequisites.

The deterministic default ledger leaves about 1,530 money, 1,150 supplies and
722 manpower after the opening 1933 commitments, and about 1,080 money, 1,000
supplies and 730 manpower after the default 1934 institutions. Daily production
and trade are deliberately excluded from those figures.

#### Opening political settlement

The provisional cabinet can begin with Gandhi-Nehru constitutional reform,
Patel's administrative and defence consolidation, or Bose-Saha mobilization and
a Soviet opening. Domestic leadership does not permanently dictate foreign
alignment.

The first integration bargain then chooses among:

| Union settlement | Main opening consequence |
| --- | --- |
| Negotiated union | -150 money, -350 supplies, -10 manpower, -5 dissent and four trunk routes |
| Provincial compact | -75 money, -200 supplies, -3 dissent and three trunk routes |
| Central decree | +150 money, -400 supplies, -5 manpower, +4 dissent, army professionalization and Delhi infrastructure |

The early national-consolidation event adds 250 manpower and opens the permanent
War Cabinet. Later integration choices cover Ceylon, Burma, Bengal, the Indus,
princely and frontier forces, fiscal federalism, transport, food security and
the 1938 maturation review.

#### Peacetime budget

An annual Union Budget begins in 1934. Taxation gives 700 money for 2 dissent
and its first use adds a permanent 5% money-output modifier; domestic bonds give
1,250 for 1 dissent and can deepen development debt only through tier three;
one-time foreign credit gives 1,100 money and 300 supplies for 1 dissent and
closer Anglo-American ties; one-time austerity gives 700 money and a stronger
revenue modifier at the price of 3 dissent and 5% total IC. Debt produces annual
service instead of disappearing.

A 1934 Revenue Service adds a permanent 2 money per day for 1 dissent. The 1937
Federal Income Tax Settlement adds 500 money, another permanent 2 money per day
and 1 dissent. From 1940, an Indian or global war can establish the National War
Finance Board for 750 money, a further permanent 2 money per day and one step
toward the defence lobby. After 1940, an India with at least 200 IC can also
receive a full-stretch review that converts part of an overgrown national IC
modifier into fiscal capacity, defence readiness or consumer stability. The
purpose is to keep a great-power India solvent without letting every programme
or accumulated industrial bonus become free.

### 2. Choose a Strategic Relationship

India can operate in five strategic universes:

| Command | Relationship choices | Main wartime identity |
| --- | --- | --- |
| Allied | Formal coalition with Britain or the United States, or a separate-command treaty | Indian contribution to a wider Allied war without surrendering Indian campaign credit |
| German | Formal Berlin coalition or co-belligerent compact | Anti-Soviet, anti-imperial or southern resource campaigns under Indian settlement authority |
| Soviet | Formal coalition, equal compact, supervised compact or autonomous Indian socialism | Anti-fascist, anti-imperial or republican Asian war |
| Japanese | Formal alliance or separate Delhi-Tokyo compact | Indian southern sphere, Indian Ocean war and an optional independent Soviet campaign |
| Sovereign | No permanent great-power coalition | Country-by-country wars under Delhi's own command |

The permanent **War Cabinet** is the control panel. It can inspect the current
relationship, join a coalition, open compact negotiations, return to sovereign
command, change sides through a safe transfer, or declare a separate war.

A formal alliance merges the partners' wars because that is how Darkest Hour's
engine works. A compact preserves separate declarations. This distinction is
especially important for the Japanese route: the Delhi-Tokyo compact lets
India fight the Soviet Union without automatically dragging Japan into that
war.

### 3. Adopt a Wartime Charter

Each route has four operational doctrines. These are not one-time modifier
buttons; they define which battlefield results build political standing.

- **Allied:** Eastern Ocean Command, Continental Expeditionary Command,
  Anti-Colonial Liberation Mandate, or Sovereign Free Command.
- **German:** Eurasian Link, Imperial Dismantlement, Southern Resource Race,
  or Sovereign Parallel War.
- **Soviet:** Anti-Fascist Expedition, Anti-Imperial Ocean War, Republican
  Asian Order, or Autonomous Indian Socialism.
- **Japanese:** Indian Southern Sphere, Independent Soviet Campaign, Indian
  Ocean First, or Equal Asian Command.
- **Sovereign:** Indian Ocean League, Continental Security Arc, World
  Balancer, or Republican Federation.

The charter determines the route achievement and the character of the later
Delhi peace congress. A legitimate side change does not erase battlefield
credit already earned.

### 4. Fight a Country-Specific Campaign

Every supported war uses the same visible lifecycle:

1. The War Cabinet opens the opponent's campaign ledger.
2. A brief names the first decisive objective, normally a capital or a defined
   theatre group.
3. Indian control of that objective creates an immediate victory milestone and
   opens a settlement claim.
4. Losing the objective suspends the live claim without deleting the historical
   achievement.
5. Recovering it restores the same campaign file.
6. A surviving government receives disclosed accept, counteroffer or refusal
   odds.
7. Delhi, not the foreign event, ratifies the selected pairwise peace.
8. A refusal affects only that opponent and returns after a guarded cooldown.
9. Annexation opens a separate constitutional settlement.

The standard generated-country terms are **60% acceptance, 25% counteroffer,
15% refusal**. Recognized coalition, sovereign or great-power standing can
improve them to **75/20/5**. Bespoke negotiations may use their own disclosed
odds. The decision text states the real roll before the player pays or commits.

Generic campaigns provide small, visible feedback rather than a second economy:

| State change | Standard feedback |
| --- | --- |
| First verified objective | +50 money and -1 dissent |
| Objective lost | +1 dissent; the live claim is suspended |
| Objective recovered | -1 dissent; the claim returns |
| Full or limited armistice | -2 dissent |
| Refusal | +1 dissent and a 90-day country-specific retry |
| Restore after annexation | -2 dissent |
| Establish protection | +4 dissent |
| Direct rule | +7 dissent, +3 belligerence and occupation upkeep |
| Defer constitutional choice | Reopens after 90 days |

Bespoke great-power and regional systems may use different rewards or costs,
but they retain the same live-control and pairwise-settlement safeguards.

If another power annexes the opponent while its answer is in transit, the
response lock is released. If the state later returns, its campaign can reopen.
One vanished or refusing country should no longer freeze every other peace
file.

### 5. Decide the Political Ending

Annexing a country is no longer the silent end of its story. India must choose
among:

- restoring a sovereign government and building influence through guarantees,
  access and partnership;
- establishing a protected government at a political cost;
- retaining direct administration and accepting dissent, belligerence and
  recurring occupation upkeep; or
- deferring the decision for a limited period.

A completed campaign also earns one route achievement and can unlock that
route's **Delhi peace congress**. The congress offers a sovereign concert, an
Indian security sphere, or renewed strategic autonomy in route-appropriate
language. Autonomous Indian socialism keeps its socialist identity even when
it remains outside Moscow's coalition.

| Congress settlement | Common mechanical result |
| --- | --- |
| Sovereign concert | -4 dissent, -3 belligerence, +1% research and +25 relations with four route partners that still exist |
| Indian security sphere | +2 dissent, +3% transport capacity and +1,000 supplies |
| Strategic autonomy | +600 money, +3% supply output, -1 dissent and withdrawal from the formal alliance into sovereign command |

Only one route achievement and one congress can be completed in a campaign;
individual charter achievements also provide their own smaller, route-specific
reward.

## Campaign Coverage

India has **236 practical country-specific campaigns**:

- **5 bespoke great powers:** Britain, Germany, the Soviet Union, Japan and the
  United States.
- **21 bespoke regional opponents:** Persia, Iraq, Saudi Arabia, Oman, Yemen,
  Afghanistan, Tibet, Xinjiang, both Chinas, Siam, Italy, France, Turkey, the
  East Indies, the Netherlands, Australia, Portugal, New Zealand, Ethiopia and
  South Africa.
- **210 generated campaigns** for other loaded sovereign tags, including many
  states that can be created later in the world simulation.

The generated matrix contains 3,223 smaller lifecycle events. Six earlier
universal routers, some containing as many as 1,695 commands, were removed.
The largest generated event is now 210 commands, below the largest comparable
stock-event scale used as the safety ceiling.

## Route-Specific Gameplay

### Allied Command

- Formal entry asks the player to choose Britain or the United States rather
  than treating the Allies as an abstract flag.
- Separate-command cooperation remains possible if India does not want every
  coalition war.
- If the chosen Allied leader disappears, command can fail over to the other
  surviving Allied great power without deleting India's current campaign or
  peace standing.
- Western, African, Gulf, European and anti-Japanese results all feed an Indian
  ledger rather than being credited only to London or Washington.

### German Command

- India can formally join Berlin, cooperate as a co-belligerent, or prosecute
  parallel wars.
- Routes support an anti-Soviet drive through Persia, Afghanistan, Xinjiang and
  Central Asia, an anti-British Indian Ocean campaign, and competition with
  Japan for Southeast Asian primacy.
- German collapse or a direct rupture returns India to sovereign command while
  preserving verified Indian victories.

### Soviet Command

- India can join Moscow, accept an equal or supervised compact, or pursue
  autonomous Indian socialism without joining the Comintern.
- Campaign themes include an anti-fascist expedition, anti-colonial ocean war,
  and republican intervention in Asia.
- India receives its own response to a Soviet Bitter Peace: accept the new
  armistice, continue a separate Soviet war, or inherit peace without losing
  earned claims.

### Japanese Command

This is the most extensively bespoke route.

- The Tokyo partnership retry deadlock is repaired. Influence now credits the
  China-policy concession, recognition of Japan's position and Indian-led
  Imphal planning.
- A strategic partnership can be converted into a formal alliance through the
  War Cabinet, but the compact remains preferable when India wants separate
  wars.
- Pro-Japanese India no longer receives anti-Japanese threat commentary unless
  India actually fights Japan.
- The southern campaign publishes concrete objectives: Rangoon, Imphal and
  Port Blair for the approach; Singapore and Kuala Lumpur for Malaya;
  Palembang, Batavia and Soerabaja for the East Indies; and Darwin, Canberra and
  Sydney for Australia.
- Japanese occupation inside India's agreed theatre can transfer to Indian
  control while legal ownership remains for the peace settlement.
- India can settle Malaya, Indonesia and Australia before Japan's entire
  Pacific war ends. Australia remains sovereign or protected rather than being
  silently annexed.
- A victorious southern partnership can improve Tibet's settlement terms, but
  it does **not** transfer Tibet automatically. India must conduct a real Tibetan
  campaign, control the verified objective and complete the constitutional
  settlement.
- Under the separate compact, India can open a simultaneous Soviet war. Tokyo
  may supply India, pressure the Soviet Far East, intervene, or condemn the
  campaign without automatically ending the southern war.

### Sovereign Command

- India can declare a bilateral campaign against any modeled sovereign state.
- The same objective, reversal, response, pairwise peace and annexation rules
  apply without a great-power patron.
- Distant victories still count toward the current sovereign charter and Delhi
  congress; they are not discarded because they fall outside a short list of
  expected theatres.

## War Finance, Manpower and Occupation

### War Finance

Whenever India is at war without an active wartime account, a War Finance Act
opens. That includes a later war after an earlier account has closed:

| Choice | Immediate result |
| --- | --- |
| Defence bonds | +2,200 money, +1 dissent, advance the debt register |
| Progressive levy | +1,500 money, +3 dissent, no debt |
| External credit | +2,600 money, +2 dissent, advance the debt register |
| Ordinary revenue | No lump sum, -1 dissent |

One annual wartime budget follows while the account is active. Repeated
borrowing advances a four-tier debt register; borrowing beyond tier four adds
an overhang. A negative wartime treasury can use +750 emergency credit once per
180 days for +1 dissent.

At the next wartime-account review after peace, India can redeem the recorded
principal, convert it into annually serviced long bonds, or repudiate it at a
severe dissent and diplomatic cost. This replaces both the old negative-money
spiral and the opposite problem of consequence-free event cash.

### Mobilisation

India also receives one **Annual Trained Reserve Class** from 1934 through
1964. Its base is 150 manpower, with transparent additions from the chosen
provincial army structure, civic or technical service policy, wartime service
law and active war. This represents trained, equipped establishments rather
than India's raw population.

The first mobilisation debate offers:

- limited service: +260 manpower, -800 supplies, +2 dissent;
- national service: +450 manpower, -1,200 supplies, +5 dissent;
- technical reserve: +190 manpower, -600 supplies;
- delay, with a political cost and a later return of the bill.

If trained manpower later falls below 150 during war, one second service debate
can add 140-350 manpower at different supply and dissent costs. Peace then
opens rapid demobilisation, an expeditionary reserve, or full retained
readiness.

Separately, from 1939 a wartime reserve below 100 can open one emergency
call-up per calendar year: a broad levy gives 250 manpower for 1,200 supplies
and 4 dissent, a reserve levy gives 180 for 750 supplies and 2 dissent, or a
volunteer appeal gives 120 for 450 supplies while reducing dissent by 1.

### Direct Occupation

Each direct mandate advances a recurring register. Annual funding scales from
300 money and 500 supplies at tier one to 1,200 money and 2,000 supplies at
tier four; overextension adds another 300 money and 500 supplies. Refusing to
fund it creates tier-scaled dissent and belligerence.

Annual civilianisation can remove overextension or reduce a higher tier, but
tier one remains while India still records direct rule. Administrative reform
therefore reduces the burden without pretending retained territory has become
free or sovereign.

## Military Changes Retained in Alpha 19

### Leaders and Specialist Forces

- 31 additional real Indian and subcontinental officers expand the wartime
  reserve.
- The validated floor is 80 active land leaders in 1938 and 90 in 1940.
- Commando coverage is restored: at least nine commando-qualified leaders are
  active by 1938.
- Eight Indian specialist families use 42 research-linked equipment models.
  Existing formations upgrade through the normal IC-and-time system rather
  than free events.
- Gurkhas emphasize mountain and snow combat; Frontier Forces emphasize
  mountain, hill and desert operations; Chindits emphasize jungle, forest,
  swamp and night fighting. Airborne, Coromandel Marines, Pioneers, Guards
  Armour and Guards Motorised have separate operational roles and research
  ladders.

### Navy

- Arabian Sea Fleet: 1 battleship, 2 light cruisers and 2 destroyer flotillas.
- Bay of Bengal Fleet: 1 battleship, 2 light cruisers and 2 destroyer flotillas.
- Indian Ocean programmes always have a true capital core: a fleet carrier,
  two light carriers or a battlecruiser. Cruisers remain auxiliaries.
- Mature national yards subtract 50% of model-zero build time from newly
  ordered hulls while retaining normal daily IC cost. Ships already in the
  production queue keep their serialized dates.
- The two late super-heavy contracts are half-completed programmes rather than
  instant free ships.
- Darkest Hour can attach only one brigade directly to an event-ordered ship.
  Each contract therefore fits one legal module and sends the remaining legal
  components to the deployment pool for manual fitting.

### Equipment, Research and Combat

- Invalid fighter, CAS, submarine, mountain, garrison, airborne, armoured and
  jet attachments were replaced with equipment the receiving unit can use.
- 31 Indian technology teams cover the full industrial, land, air, naval,
  electronics, rocket and atomic programme.
- India inherits the mature foundations of the British Raj rather than
  spending 1937 research slots on nineteenth-century prerequisites; modern
  equipment and doctrines still require research.
- Normal upgrades use 50% base cost and 50% base time. Reinforcement does not
  create hidden upgrade progress and in-supply units do not upgrade passively;
  zero IC on the Upgrades slider means zero progress.
- Air and naval combat pacing emphasizes organization loss and withdrawal over
  routine annihilation. Relative strength damage per organization damage is
  about 36% of stock in air combat, 44% for air against ships, 31% for ships
  against aircraft and 44% in ship combat. Critical hits can still destroy a
  badly handled wing or ship.
- The automatic retreat threshold rises from 5 to 12 average organization.
  Rebase orders take 35% less travel time, while Support Defence and Reserves
  take 30% less travel time than stock.
- Players still must rebase threatened aircraft; the executable provides no
  safe automatic event command for that action. Airfield guards, dispersal,
  warning systems and faster rebasing create time for the player to respond.

## Decision and Information Changes

- Major diplomatic choices state money, supply, manpower and dissent costs
  before commitment.
- Foreign negotiations show the actual fixed accept, counter and refusal odds.
- Tokyo explicitly shows how influence, IC and armed strength affect the
  partnership tier.
- Major decisions remain selectable when at least one complete action is
  affordable. Each action retains its own full resource gate, and the decision
  description discloses the costs of unavailable alternatives.
- Strategic orientation can be reconsidered; it is not the same thing as a
  compact, formal alliance or declaration of war.

## What Requires a Fresh Campaign

Start a **new 1933 campaign** for Alpha 19. The complete route ledger, leader
roster, scenario technologies, economy curve, campaign monitors and successor
state coverage cannot be reconstructed safely from an older save.

- V3 saves are unsupported.
- Earlier V4 alpha saves may receive individual migration or repair events,
  but they are not valid tests of the complete Alpha 19 wartime architecture.
- Existing ships already in production cannot receive a newly changed build
  schedule.
- Personnel records are serialized into saves, so the expanded leader roster
  requires a new campaign.

## Verification Performed

The current source was rechecked on 24 August 2026:

- full static validator: **0 errors, 0 warnings**;
- global campaign matrix: **28,175 checks**, 210 countries, 3,223 events;
- canonical wartime system: **1,434 checks**;
- five-route consequences: **595 checks**;
- specialist units: **3,620 checks**;
- diplomatic disclosure: **431 checks**;
- Japan partnership: event IDs, braces, references, pictures, AI files and
  transfer safety passed;
- installed deployment: every managed file checked, with **0 missing and 0
  mismatched**;
- fresh Darkest Hour launch: the 1933 India campaign reached the live map and
  `savedebug.txt` ended with **Scenario Validation: no errors found**;
- unsupported foreign-country-scope regression gate: passed;
- public-manifest deny-list and redistribution-boundary check: passed.

The production run also completed repeat-build stability, art, sprite,
economy, resource, campaign, combat and construction-cap gates. The launch
hotfix removed 116 unsupported country-tag wrappers around global flags and
added a validator that rejects the syntax before deployment.

## Remaining Risks and Playtest Priorities

These are the important unfinished items, not hidden claims of completion:

1. **The successful 1933 startup smoke is not a war playthrough.** Event timing,
   AI behavior, balance and player satisfaction still require a complete
   campaign.
2. **Wartime balance needs observation.** Test whether finance and mobilisation
   relieve emergencies without becoming free resources, and whether occupation
   upkeep is meaningful without becoming tedious.
3. **Coalition play needs stress testing.** Verify inherited wars, side changes,
   partner collapse, Allied failover and separate peaces in a real save.
4. **Late-game force scale remains a balance question.** Record effective IC,
   formations, manpower and treasury in 1940 and 1942 on a no-cheat run.
5. **The Japanese route should be the first narrative test.** Confirm that a
   pro-Japanese India receives no hostile commentary, southern objectives fire
   as captured, Japanese-held assigned territory transfers correctly, and an
   Indian settlement opens before the Pacific war ends.
6. **Postwar closure needs a complete run.** Trigger at least one armistice, one
   annexation settlement, one occupation year and one Delhi congress.
7. **The public-safe branch snapshot is reproducible, but it is not a tagged
   stable release.** A versioned release and default-branch merge should wait
   for the human war and postwar tests above.
8. **Repository safety is separate from package clearance.** Local donor
   graphics are excluded, but a downloadable or forum package still needs a
   current V4 rights and provenance review.

## Recommended First Alpha 19 Playtest

For the fastest coverage of the original complaints:

1. Start a fresh 1933 campaign and keep milestone saves at the start of 1937,
   before the first war, before the first settlement and before demobilisation.
2. Pursue the Delhi-Tokyo **separate compact**, not the formal alliance, so the
   separate-war design is exercised.
3. Open the southern campaign and verify the published Burma-Andaman, Malayan,
   East Indies and Australian objectives.
4. Capture one objective, deliberately lose and recover it, then verify the
   settlement claim suspends and returns.
5. Submit one peace, accept the actual foreign roll without reloading, and
   verify a refusal locks only that opponent.
6. Annex one state and compare restoration, protection and direct-rule costs.
7. Open a simultaneous Soviet or other bilateral war to test separate command.
8. Record treasury, debt tier, manpower, dissent, occupation tier, effective IC
   and force totals at each yearly save.
9. Finish one qualifying campaign and verify the correct route achievement and
   Delhi congress.

## Detailed References

- [Release Notes](RELEASE_NOTES.md) records the cumulative release history.
- [Wartime Campaign Map](docs/WARTIME_CAMPAIGN_MAP.md) is the canonical wartime
  contract.
- [Design Notes](docs/DESIGN.md) records the broader V4 design and content
  counts.
- [Playthrough Roadmap](docs/PLAYTHROUGH_ROADMAP.md) records earlier
  playthrough findings and the balance questions that still need real-game
  evidence.
- [Alpha 13](docs/RELEASE_NOTES_4.2_ALPHA13.md),
  [Alpha 14](docs/RELEASE_NOTES_4.2_ALPHA14.md),
  [Alpha 15](docs/RELEASE_NOTES_4.2_ALPHA15.md) and
  [Alpha 16](docs/RELEASE_NOTES_4.2_ALPHA16.md) cover the military, Tokyo,
  specialist and information improvements that Alpha 19 retains.
