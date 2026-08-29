# A Union Before Midnight: Gameplay Changes and Alpha 22 Status

This is the player-facing guide to the current **4.2.0-alpha.22** source of
*A Union Before Midnight*. It explains what changed, how the new systems are
supposed to play, what has been verified, and what still needs a real campaign
test.

Updated: 29 Aug 2026.

## Current Status

| Area | Status |
| --- | --- |
| Current source version | `4.2.0-alpha.22` |
| Alpha 22 implementation | Clean-opening and focused early-event audit subset complete |
| Alpha 22 build and public package | Passed: deterministic 4,434-file build, full release suite, 342-file donor-safe manifest, 0 static errors/warnings |
| Personal deployment and executable smoke | Passed: 1,531/1,531 local files verified; fresh map reached; 0 exact `ERROR :` lines; no crash dump |
| Personal sprite profile | Exact 41-family/591-descriptor profile verified locally; excluded from the current V4 Git tree and public packages |
| Campaign compatibility | Start a fresh 1933 campaign |
| Reviewed saves | 29 Aug Alpha 22 autosave reaches 1 Feb 1933 and proves the clean opening; earlier wartime saves remain compatibility evidence |
| Human Alpha 22 playthrough | Opening run completed; a full wartime/postwar run is still required |
| Source-control safety | Public-safe exclusions active; local-only assets remain excluded |

The maintained source is the `v4-direct-dh` branch. Its public installer
manifest is designed to contain only AUBM gameplay, documentation and
redistribution-cleared art. Darkest Hour foundation files, the restored local
41-family donor-derived sprite and model-panel profile, unresolved leader
portraits, manuals, screenshots and Steam test backups remain excluded. The
current Alpha 22 public manifest contains 342 donor-safe files. The installed
personal build contains 1,531 verified files because it also reconstructs the
local-only visual profile.

Alpha 18's first fresh engine launch exposed unsupported foreign-country flag
scopes in the Japanese-partnership and wartime-settlement events. Alpha 19
rewrote those callbacks using Darkest Hour-supported event logic and added a
regression check so the invalid form cannot return. Alpha 20 preserved that
launch fix and introduced the commitment and local Southeast Asian foundation.
Alpha 21 extends and hardens those systems as described below. Alpha 22 adds a
clean cold start and repairs defects found by auditing the existing early game.

The practical verdict is: **Alpha 22 is built, locally deployed and
launch-verified, but it is not yet a proven stable long campaign.** The opening
run is complete; a human war and postwar run is still required for balance,
pacing and narrative verification.

The old `India Mod` folder is the original/base workspace. The maintained V4
source of truth is the sibling `India Ascendant` repository, and deployment
targets the separately installed Steam mod listed above.

## What Alpha 22 Changes

### The opening is now about choices, not repairs

The newest campaign previously scheduled nine AUBM windows around the opening
and union decision. A fresh Alpha 22 start reduces that sequence to three
player-facing windows in total: one premise acknowledgment and two genuine
political choices.

1. **Scenario opening — A Union Before Midnight:** acknowledge the campaign
   premise and sovereign starting settlement.
2. **Opening 72 hours — The Provisional Cabinet:** choose the first governing
   coalition with all immediate costs shown.
3. **6 January — One Administration, Many Nations:** choose the union method,
   with its money, supplies, manpower and dissent effects shown.

Only the premise and cabinet appear during the opening 72 hours. Core
campaign-state, service, modernization and strategy initialization is folded into the premise.
The Union Register is folded into the union choice, so no later one-button
register popup is needed and the integration chain remains open.

Fresh 1933 scenarios pre-sleep **218 events total**: 216 retired legacy
wartime/route IDs plus the two generic V3 Gurkha and frontier decisions. Their
unique V4 replacements are the single player-facing specialist paths. These
retirements are fresh-start-only: upgraded saves retain the compatibility logic
they may need.

### Upgrade saves keep repair logic without fresh rewards

Compatibility helpers are excluded from a fresh campaign and have concise,
plain-language **Compatibility Review** titles for upgraded saves. They repair
state only; they do not regrant the fresh opening's money or manpower. This
keeps old-save recovery available without turning a new game into a migration
clickwall.

The retained helpers and their purpose are:

| Event | Upgrade-save review |
| --- | --- |
| 9280000 | **V4 Campaign State** — records the current V4 campaign baseline |
| 9281000 | **Modernization State** — restores modernization and War Cabinet framework flags |
| 9280800 | **Strategy Records** — reconciles the strategy ledger |
| 9270792 | **Cabinet Records** — reconstructs missing cabinet history |
| 9280315 | **Service Archives** — records inherited service and roster state |
| 9281900 | **War Cabinet** — retires superseded wartime entry events |
| 9281949 | **Strategic Commitments** — reconciles binding route commitments |
| 9287613 | **Southern Settlements** — repairs southern refusal and settlement state |
| 9283200 | **Wartime Events** — retires superseded route-wartime events |

They are repair tools for upgraded saves, not intended opening content. A
future migration milestone will consolidate them further where possible.

The six bookkeeping windows seen in the older August 1934 autosave were
`9280000` (campaign state and the old reserve grant), `9281900` (retire the old
war ledger), `9281000` (modernization and the old manpower grant), `9270792`
(cabinet and roster repair), `9280800` (strategy ledger) and `9280100` (open
the Union Register). That file is a different campaign. In the current
1 February 1933 autosave, none of those six fired: fresh initialization is in
the premise, and every union action opens the register directly.

The War Cabinet now requires both a completed union choice and an opened Union
Register. India cannot enter a coalition, choose a compact or declare an
independent War Cabinet campaign before its constitutional opening is settled.

### Existing early-game events were audited, not assumed safe

The cold review covered the existing events feeding the new opening and found
several real defects beyond the popup problem:

- The 1934 and 1936 constitutional review fallbacks now match the exact
  complement of their named branches, so only one review can fire.
- All 18 formerly write-only identity flags from the six three-way founding
  settlements now pay one modest remembered dividend in **Telegraphs,
  Statistics and a Common Time**, the first July 1934 Union report. The report
  remains one-shot and no extra popup was added.
- Two education-policy actions now deliver the research bonuses their text
  already advertised.
- The first foreign-credit package no longer charges itself the prior-credit
  service fee.
- Three obsolete direct-war War Cabinet menus now redirect safely to the
  current guarded War Cabinet instead of bypassing commitment locks.
- The V3 and V4 Gurkha/frontier systems cross-lock, leaving one unique V4 path
  on a fresh campaign and preventing duplicate formations in upgraded games.
- Opening cabinet and union actions disclose their immediate resource,
  manpower and dissent costs within the engine's action-text limit.

This is a completed **Milestone 1 subset**, not the whole Gameplay Fun Rework.
The permanent State of the Union ledger, annual-budget redesign, peacetime
objectives, broader force rebalance, guided operations board, staged Southeast
Asian campaign and postwar-memory work remain specified but unimplemented.

The deterministic build, deployment verification and fresh executable smoke
have passed. The 1 February autosave confirms the three opening event IDs and
contains none of the nine Compatibility Review IDs. Balance and the full
wartime/postwar campaign still need a human playthrough.

## What Alpha 21 Changes

The developer's exact personal **41-family India sprite profile** is restored
in the local installation after the previous public deployment. This is not
public payload: its donor-derived descriptors, animation strips, palettes and
model panels remain outside the current V4 Git tree and the installer manifest. Public players
continue to receive Darkest Hour Full sprites until redistribution-safe Indian
art is available.

For exact objectives, legal-owner rules and examples, use the
[Southeast Asia Victory Matrix](docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md). It is
the canonical Alpha 21 gameplay contract.

### Current commitments cannot be relabelled

- Allied, German, Soviet and Japanese live-state synchronizers now refuse to
  overwrite an existing rival commitment. A Berlin-Tokyo faction merger can no
  longer reinterpret a Delhi-Tokyo commitment as a German one merely because
  the engine reports a shared alliance.
- The sovereign synchronizer cannot erase an active commitment merely because
  an alliance or compact marker changes unexpectedly.
- Every direct coalition command and the retired pre-Alpha20 entry decisions
  now repeat the same rival-commitment and live-alliance guards. This protects
  upgraded saves with an old decision still open.
- This is **not** a lifetime alignment lock. Same-family treaty upgrades remain
  valid. India may withdraw while at peace, enter sovereign command and wait
  through the existing 90-day realignment before choosing another family.

### Every command route recognizes the theatre

The same land, liberation and sea-lane tests operate under Allied, German,
Soviet, Japanese and sovereign command. The full Southeast Asian theatre result
now feeds these named focuses directly:

| Route | Focuses accepting the full theatre result |
| --- | --- |
| Allied | Eastern Ocean Command; Anti-Colonial Liberation Mandate |
| German | Dismantle Britain's imperial system; Win the southern resource race |
| Soviet | Anti-Imperial Ocean War; A Republican Asian Order |
| Japanese | Indian Southern Sphere |
| Sovereign | Build an Indian Ocean League |

Partial land results, friendly liberations and sea lanes do not consume the
route's single wartime-achievement slot. Only the completed mixed theatre
publishes route-level victory credit. A separately won named-country campaign
can still use the existing **Beyond the Charter** fallback.

Autonomous Indian Socialism follows the socialist charter lifecycle while
remaining outside Moscow's formal alliance. Other continental focuses still
receive unexpected victories through the established beyond-the-charter
fallback.

### Four friendly-owner liberation chains

Indochina, the Philippines, Malaya and Batavia/East Indies now recognize Indian
participation even when Darkest Hour immediately returns an allied province to
its legal owner. A liberation is credited only when all four safeguards hold:

1. India is at war with Japan.
2. The system previously observed Japan holding the complete published hub set
   while the friendly legal owner also fought Japan and did not fight India.
3. The complete hub set has returned to India or an eligible friendly owner.
4. India directly controls a hub or an Indian **land division remains
   garrisoned in one published hub** when the liberation is recorded.

This produces operational and modest campaign credit only. It opens no peace
against the friendly owner, creates no armistice lock, transfers no friendly
territory and does not end the Japanese war. Keep the Indian formation in a
listed hub until the liberation message appears.

### Liberation and sea lanes interoperate

Current friendly Malaya credit can satisfy the Singapore-Kuala Lumpur hinges
of Malacca and the Singapore hinge of the South China Sea. Current Batavia
credit can satisfy Malacca's Batavia alternative. Current Indochina or
Philippine credit can satisfy the Saigon or Manila side of the South China Sea.

Java Sea Command remains deliberately stricter: Batavia-only liberation does
not replace the Batavia-Soerabaja two-base operating system or its sixteen
ready surface combatants. Bay of Bengal likewise retains its own published
Rangoon-Port Blair chain and fleet test.

### A flexible three-result victory

**India Wins the Southeast Asian Operational Theatre** now requires exactly
one of two mixed structures:

- two different land categories plus one sea lane; or
- one land category plus two different sea lanes.

Three land results without a lane and three lanes without a land result do not
qualify. Repeated results within one category, such as two Malayan country
victories, count once. The permanent award grants operational and settlement
standing, not provinces or an automatic peace.

### An optional weaker Japanese peace

**Delhi Can Offer a Southern Armistice to Japan** has a live, Japan-specific
gate. India must still be at war with Japan and must hold either:

- `ind_aubm_japan_current` from the recoverable direct limited-victory map,
  provided the decisive Japan victory has not already replaced this weaker
  path; or
- permanent `ind_aubm_sea_theatre_achieved` history **plus at least one current
  anti-Japanese friendly-liberation flag** in Indochina, the Philippines,
  Malaya or Batavia/East Indies.

The permanent route-neutral theatre result alone does not qualify. It cannot be
earned under one route, carried through a route switch and converted into free
Japanese terms after all current Japanese leverage has been lost. Loss of the
direct Japan claim or every current qualifying liberation suspends eligibility;
recovery restores it. Delhi may always decline and keep fighting toward Okinawa
or the Home Islands. A decisive Okinawa or Home Islands result uses the normal
great-power armistice board, not the weaker southern decision.

Tokyo's fixed response is **45% acceptance, 35% counteroffer and 20% refusal**.
Acceptance or counteroffer produces only a pairwise India-Japan peace. Refusal
continues the war. Southern in-flight state plus a shared great-power
terms-dispatch lock prevents initial, retry and cross-opponent dockets from
opening duplicate or disabled response popups. At the end
of the 90-day refusal cooldown, Japan's file reopens only if the same live gate
still holds; otherwise it waits for a direct claim or qualifying liberation to
recover. If India earns decisive victory during that cooldown, the retry moves
to the normal great-power board. Even on acceptance, a position transfers only when Japan legally owns
it and India actually controls it; territory owned by Britain, Malaysia,
Singapore, U05, the Netherlands, Indonesia or another friendly government is
never taken.

### Current save review

The newest **28 Aug autosave** is only a fresh 1934 campaign. The **23 Aug
manual save** has India non-aligned and not at war. Neither file exercises the
reported alliance transition or the new operational chains, so Alpha 21 still
needs a fresh wartime playthrough.

## What Alpha 20 Changes

Alpha 20 is the direct response to the December 1941 India save and the
Southeast Asian playtest report. The save records a binding Delhi-Tokyo compact
but no formal Indian alliance and no live Indian war. Under Alpha 19, the Berlin
entry action could still appear and use Darkest Hour's coalition-transfer
command; that made a Japanese-to-German switch possible in a single click.

### One binding strategic commitment

- A formal Allied, German, Soviet or Japanese coalition and a binding
  separate-command compact now exclude every rival alignment.
- A compact may still be upgraded to the formal coalition of the same family.
- Delayed foreign acceptances are serialized. If India commits elsewhere while
  an answer is in transit, the stale answer lapses instead of changing route.
- India can withdraw to sovereign command only while at peace. A 90-day reset
  follows before another binding relationship becomes available.
- Country-campaign menus hide coalition partners, and their delayed declaration
  callbacks recheck the alliance. Declaring on a partner can no longer be used
  as an undeclared coalition-transfer button.
- Old saves receive a live-state reconciliation pass. Actual formal alliance
  membership wins over obsolete route flags; existing binding compacts are
  recognized as commitments.

### Local Southeast Asian outcomes

India no longer has to capture every Southern Theatre victory province before
a decisive local campaign can produce terms.

| Operation | Decisive condition | Result |
| --- | --- | --- |
| Batavia against the East Indies | India controls Batavia (1647) in a live war with U05 | A local Dutch East Indies response and Delhi ratification open without the national Southern-route flag |
| Colonial Batavia against the Netherlands | India controls Dutch-owned Batavia in a live war with HOL | A distinct colonial settlement path; Amsterdam itself is not required |
| Malaya against Britain | India controls Singapore (1432) and Kuala Lumpur (1438) in a live war with ENG | A Malaya-only response and pairwise peace can open without requiring Borneo or the whole British war |
| Indochina | India controls Hanoi (1395) and Saigon (1399) during the relevant war | An achievement-only land milestone records Indian leverage; the existing U03/FRA country docket remains the sole peace path |
| Philippines | India controls Manila (1565) and Davao (1579) during the relevant war | An achievement-only land milestone records Indian leverage; the existing PHI/USA/JAP country docket remains the sole peace path |

Every local settlement claim is reversible: losing the required ports or
leaving the relevant war cancels a pending answer and suspends the live claim.
Settlement commands end only the named bilateral war. Cessions run in the
defeated legal owner's event scope, so another country's occupation or
ownership is untouched. The East Indies transfer explicitly includes western
New Guinea provinces 1594-1601 when U05 or HOL legally owns them. The Indochina
and Philippine additions award permanent historical credit while suspending
and restoring current operational standing; they do not open a duplicate
response, peace or territorial settlement.

Friendly released or protected Indonesia and Malaya count as a continuing
political success. India therefore does not lose a route achievement merely
because it chose decolonization instead of direct ownership.

### Operational sea-lane achievements

Naval victories now require both the ports that sustain a theatre and a
minimum surface fleet; transports, submarines and nuclear submarines do not
count.

| Sea lane | Ports under Indian control | Surface fleet |
| --- | --- | ---: |
| Bay of Bengal | Rangoon (1415) and Port Blair (1421) | 8 |
| Strait of Malacca | Singapore (1432), Kuala Lumpur (1438), and Palembang (1636) or Batavia (1647) | 12 |
| Java Sea | Batavia (1647) and Soerabaja (1653) | 16 |
| South China Sea | Singapore (1432), and Saigon (1399) or Manila (1565) | 18 |

These are one-time, modest operational rewards rather than territorial
settlements. A relevant colonial or Southeast Asian war is required, preventing
India from receiving the Bay of Bengal reward merely because an unrelated war
started. Port loss suspends current control and recapture restores it without
duplicating the reward. A flexible regional achievement recognizes a
combination of land and sea successes instead of demanding every hub on the
map.

### 1934 integration recovery

The reviewed campaign also exposed an early-state gap: legitimacy and state
capacity could both be present while neither a provincial bargain nor coercion
had been recorded. None of the three 1934 reviews accepted that combination,
stalling the later integration chain. Alpha 20 routes the mixed state through
the unfinished-review event and adds a complete truth-table regression test.

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
relationship, enter one coalition or compact, withdraw to sovereign command
while at peace, or declare a separate war against a non-partner. Rival
alignment actions remain unavailable until the 90-day reset ends.

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
Delhi peace congress. An at-peace withdrawal does not erase battlefield credit
already earned, but it does not permit an immediate side switch.

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

The generated matrix contains 3,433 smaller lifecycle events. Six earlier
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
  preserving verified Indian victories and enforcing the 90-day reset before
  another alignment.

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
- If India instead fights Japan, the optional weaker Southern Armistice needs a
  live Japan war plus either the current direct limited-victory claim before
  decisive victory, or the
  permanent all-route theatre record backed by a current friendly liberation.
  The record alone cannot survive a route switch as free leverage. Its 45/35/20
  response remains pairwise; southern in-flight and shared dispatch locks
  prevent initial, retry and cross-opponent races,
  and a 90-day refusal reopens only after live leverage is present again. No
  friendly legal owner's territory can be transferred.

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

## Military Changes Retained Through Alpha 22

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

Start a **new 1933 campaign** for the intended Alpha 22 playtest. The complete
route ledger, leader roster, scenario technologies, economy curve, campaign
monitors and successor-state coverage cannot be reconstructed safely from an
older save.

- V3 saves are unsupported.
- Earlier V4 alpha saves may receive individual migration or repair events,
  but they are not complete tests of Alpha 22's fresh-only opening retirement
  or Alpha 21's liberation, lane and armistice architecture.
- Existing ships already in production cannot receive a newly changed build
  schedule.
- Personnel records are serialized into saves, so the expanded leader roster
  requires a new campaign.

## Verification State

The final **Alpha 22 acceptance run on 29 August 2026** passed:

- deterministic repeat build: **4,434 overlay files**;
- global campaign matrix: **40,357 checks**, 210 countries, 3,433 events;
- canonical wartime system: **1,860 checks**;
- five-route consequences: **668 checks**;
- specialist units: **2,957 checks**;
- diplomatic disclosure: **431 checks**;
- Japan partnership: event IDs, braces, references, pictures, AI files and
  transfer safety passed;
- southern settlements: **305 checks**;
- Southeast Asian operations: **21 unique operational events**, four
  friendly-owner liberation chains, four fleet-backed lanes and one flexible
  theatre award;
- unsupported foreign-country-scope regression gate: passed;
- union-integration and remembered-dividend contracts: **79 checks**;
- fresh/upgrade split: **36 checks**; audited opening/early game: **24 checks**;
- complete static validation: **0 errors and 0 warnings**;
- art release gate: **4,588 picture entries**, 109 names and 102 custom event
  pictures, with 0 duplicate or release issues;
- economy, sustained resources, cold start, combat pacing, construction caps
  and Steam Deck checks: passed.

The public installer manifest contains **342 managed files** and passed the
donor-free validate-only gate. Foundation files, donor-derived personal visuals
and unresolved assets remain outside that payload. The local personal build
verified and installed **1,531/1,531 files**, including 41 distinct India
families, 591 descriptors, 553 bitmap strips and 44 palettes.

A real fresh fullscreen launch of Darkest Hour 1.05.2 selected **A Union Before
Midnight V4.2**, loaded the 1933 India campaign and reached the playable map.
Province validation ended with **No errors found**, the exact `ERROR :` count
was 0 and no crash dump appeared. The user's resulting 1 February autosave
contains opening history IDs 9270000, 9270002 and 9270001, none of the nine
Compatibility Review IDs, and the expected fresh, integrated and Union Register
flags. Live history exposed the War Cabinet only after the union choice. The
save count remains 27; only the normal autosave rotation changed. This verifies
packaging, parsing and the clean opening, not a complete wartime campaign.

The obsolete standalone
`validate_v3_legacy.py` harness is not a production release gate because its
required `tools/v3_config.json` no longer exists; V3 syntax and cross-event
checks are covered through the maintained V4 pipeline.

## Remaining Risks and Playtest Priorities

These are the important unfinished items, not hidden claims of completion:

1. **Upgrade-save migration still needs a controlled engine run.** Fresh-start
   separation is proven; now verify a copied older V4 save receives only the
   Compatibility Reviews it genuinely needs and no fresh resource regrant.
2. **Wartime balance needs observation.** Test whether finance and mobilisation
   relieve emergencies without becoming free resources, and whether occupation
   upkeep is meaningful without becoming tedious.
3. **Coalition commitment needs stress testing.** Verify rival offers and
   retired legacy entries stay hidden, a Berlin-Tokyo faction merger cannot
   relabel a Japan commitment, same-family upgrades remain possible, wartime
   withdrawal is blocked and the at-peace 90-day reset releases correctly.
4. **Late-game force scale remains a balance question.** Record effective IC,
   formations, manpower and treasury in 1940 and 1942 on a no-cheat run.
5. **Southeast Asia should be the first operational test.** Confirm all-route
   focus integration, the four prior-occupation plus Indian-garrison liberation
   chains, friendly-hub lane interoperability, the mixed three-result theatre
   test and the optional 45/35/20 Japanese armistice's current-leverage and
   in-flight locks, with no friendly-owner transfers.
6. **Postwar closure needs a complete run.** Trigger at least one armistice, one
   annexation settlement, one occupation year and one Delhi congress.
7. **Repository safety is separate from package clearance.** Local donor
   graphics are excluded, but a downloadable or forum package still needs a
   current V4 rights and provenance review.

## Recommended First Alpha 22 Playtest

For the fastest coverage of the original complaints:

1. Start a fresh 1933 campaign. Record every AUBM window through 10 January:
   the premise should appear at scenario opening, the cabinet during the
   opening 72 hours and the union choice on 6 January. Confirm no compatibility helper or one-button
   Union Register appears, and save/reload once before choosing the union.
2. Confirm the War Cabinet is unavailable before the union choice, becomes
   reachable afterward, and the chosen cabinet and union costs match their
   action text. Keep later milestone saves before the first commitment,
   Japanese war, liberation, theatre award and armistice response.
3. Select one named Southeast Asian focus on the chosen command route and
   confirm the full theatre result feeds that focus; repeat from a save under a
   second route if practical.
4. Form the Delhi-Tokyo separate compact. Confirm rival formal and compact
   entries disappear while the Japanese same-family upgrade remains. If the
   wider factions merge, confirm the route remains Japanese rather than German.
5. While fighting Japan, let Japan occupy a complete Indochina, Philippine,
   Malayan or Batavia hub set, then restore it to its friendly legal owner. Keep
   an Indian land division in a published hub until the liberation records.
6. Repeat once without Indian control or a garrison and confirm another ally's
   liberation gives India no credit. Verify no terms, transfer or peace opens
   against the friendly owner.
7. Use eligible liberation credit at a Malacca or South China Sea hinge. Then
   verify Batavia-only liberation does not satisfy Java Sea without Soerabaja
   and sixteen ready surface ships.
8. Earn two distinct land categories plus one lane, or one land category plus
   two lanes, and confirm the flexible theatre award. Confirm three land-only
   or three lane-only results do not qualify.
9. Offer the Japanese Southern Armistice once with the current direct Japan
   claim and once with permanent theatre history plus a current friendly
   liberation. Confirm theatre history alone is insufficient after loss or a
   route switch. Test its 45/35/20 branches: refusal must wait 90 days, avoid a
   duplicate initial/retry popup and reopen only with recovered live leverage;
   acceptance must end only the Japanese war and transfer no friendly-owner
   territory.
10. After all Indian wars end, withdraw to sovereign command. Rival offers must
   remain closed through the 90-day realignment and reopen afterward; repeat
   from a save made during the cooldown.
11. Complete one Batavia or Malaya pairwise docket, one annexation settlement,
    one occupation year and one Delhi congress while recording treasury, debt,
    manpower, dissent, effective IC and force totals.

## Detailed References

- [Southeast Asia Victory Matrix](docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md) is the
  canonical Alpha 21 specification for all-route focuses, liberation proof,
  sea lanes, the mixed theatre result and the Japanese Southern Armistice.
- [Release Notes](RELEASE_NOTES.md) records the cumulative release history.
- [Alpha 20 Save and Playtest Review](docs/ALPHA20_SAVE_AND_PLAYTEST_REVIEW.md)
  preserves the previous release's installed-save chronology and diagnosis.
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
  specialist and information improvements retained through Alpha 21.
