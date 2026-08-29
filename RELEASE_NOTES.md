# Release Notes

## 4.2.0-alpha.22 / Alpha 22 - A Clean Opening and Audited Early Game

*29 Aug 2026*

Alpha 22 implements the first focused subset of the Gameplay Fun Rework. It
removes fresh-start compatibility clickwork, makes the first political costs
legible and repairs defects found by auditing the existing events on which the
new opening depends. It does not yet implement the later ledger, national
priority, force-balance, operations-board, staged-theatre or postwar-memory
milestones in the full specification.

### Three Meaningful Opening Choices

- Reduced the newest campaign's opening sequence from **nine windows to three
  player-facing windows total**: one premise acknowledgment at scenario
  opening, the provisional-cabinet choice during the opening 72 hours and the
  union-method choice on 6 January.
- Folded fresh campaign-state, service, modernization and strategy
  initialization into the premise instead of presenting one-button repair
  events.
- Folded the authoritative Union Register and integration-start flags into all
  three union actions. A fresh campaign no longer needs the later one-action
  Union Register popup, and the constitutional chain remains reachable.
- Disclosed the immediate money, supplies, manpower and dissent effects in all
  opening cabinet and union action labels within Darkest Hour's action-text
  limit.
- Gated the permanent War Cabinet behind both the completed union and opened
  Union Register. Coalition, compact and independent-war commands cannot open
  during the unfinished constitutional prologue.
- Confirmed that the six bookkeeping windows in the older August 1934
  autosave were campaign state (`9280000`), wartime retirement (`9281900`),
  modernization (`9281000`), cabinet records (`9270792`), strategy records
  (`9280800`) and the Union Register (`9280100`). None appears in the current
  1 February 1933 autosave.

### Fresh Retirement, Upgrade-Save Compatibility

- Added a fresh-1933 marker and pre-slept **218 events total** only for that new
  scenario: 216 retired legacy wartime/route IDs plus the two generic V3
  Gurkha and frontier decisions. Fresh games use the unique V4 specialist
  paths.
- Excluded compatibility helpers from fresh starts while retaining them for
  upgraded saves that may need state repair. Their names and descriptions now
  identify them plainly as Compatibility Reviews.
- Removed fresh-style money and manpower grants from upgrade-save repair
  events. Migration can restore flags but cannot replay the opening treasury or
  service pool.

### Existing-Event Audit Repairs

- Made the 1934 and 1936 constitutional review branches mutually exclusive by
  defining each fallback as the exact complement of its named outcomes.
- Gave all 18 previously write-only identity flags from the six three-way 1933
  founding settlements one modest remembered dividend in event 9280112, the
  first July 1934 Union report. The existing one-shot report carries the
  callbacks, so this adds no popup or repeatable reward.
- Added the +1 and +2 research modifiers promised by two education-policy
  actions whose descriptions previously advertised rewards they did not give.
- Moved the foreign-credit marker until after the prior-credit service check,
  preventing a first credit package from charging its own service fee.
- Converted three obsolete, unreachable direct-war War Cabinet menus into
  one-action redirects to the current guarded War Cabinet. Upgraded saves with
  an old menu queued cannot bypass current commitment locks.
- Cross-locked the legacy and V4 Gurkha/frontier systems. Either version closes
  its duplicate, while a fresh campaign exposes the unique V4 unit path.

### Alpha 22 Status

Alpha 22 passed the deterministic **4,434-file** build, complete release suite,
**342-file** donor-safe public manifest, **1,531/1,531-file** personal local
deployment and fresh Darkest Hour executable smoke. Static validation ended
with 0 errors and 0 warnings; the engine log contained 0 exact `ERROR :` lines,
province validation reported no errors and no crash dump appeared.

The user's 1 February 1933 autosave contains all three opening event IDs
9270000, 9270002 and 9270001, followed only by the Army Oath (`9271200`). It
contains none of the nine Compatibility Review IDs and has the expected fresh,
integrated and Union Register flags. Live history exposed the War Cabinet after
the union choice. The opening run is therefore verified, but no complete human
wartime/postwar Alpha 22 playthrough has been completed.

The release gate also now fails immediately on a stale generated route file,
and the economy analyzers evaluate selected conditional branches instead of
summing mutually exclusive dividends.

The maintained `validate_v4.py` pipeline is the authoritative production
validator. The standalone `validate_v3_legacy.py` harness is deprecated and is
not a mandatory release gate because its required `tools/v3_config.json` is no
longer present.

## 4.2.0-alpha.21 / Alpha 21 - Every Indian Route Through Southeast Asia

*29 Aug 2026*

The exact personal **41-family India sprite profile** has been restored in the
developer's local installation after the previous public deployment. It is a
local-only overlay: its donor-derived descriptors, animation strips, palettes
and model panels are excluded from the current V4 Git tree and do **not** ship in the public
installer. Public installations continue to use redistribution-safe Darkest
Hour Full visuals.

The complete operational contract is published in the
[Southeast Asia Victory Matrix](docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md).

### Alliance Exclusivity Without A Lifetime Lock

- Hardened the Allied, German, Soviet and Japanese live-state synchronizers so
  an existing rival commitment cannot be relabelled by engine alliance state.
  This explicitly covers a Berlin-Tokyo faction merger reporting India as
  allied to Germany while Delhi's binding commitment remains Japanese.
- Prevented the sovereign synchronizer from silently erasing a current
  commitment when a compact or alliance marker changes unexpectedly.
- Added the same rival-commitment and live-alliance guards to every direct and
  retired legacy coalition-entry action, including the old Pacific-entry and
  independent-war choices that may remain open briefly in an upgraded save.
- Retained Alpha 20's deliberate same-family compact upgrade and explicit
  at-peace withdrawal. Withdrawal clears the current commitment, returns India
  to sovereign command and starts the documented **90-day realignment** before
  a different coalition can be negotiated; this is not a lifetime alignment
  lock.

### One Southeast Asian War System For All Five Routes

- Integrated the complete Southeast Asian theatre result directly into the
  relevant Allied, German, Soviet, Japanese and sovereign wartime focuses.
  Autonomous Indian Socialism uses the same operational tests through the
  socialist charter while retaining sovereign command.
- Kept partial land operations, friendly liberations and sea lanes as
  operational credit. Only the completed mixed three-result theatre publishes
  the route-level campaign victory, so the generic "Beyond the Charter" fallback
  cannot consume a route's one achievement slot after the first local result.
- Added four anti-Japanese friendly-owner liberation chains for **Indochina,
  the Philippines, Malaya and Batavia/East Indies**. Each requires recorded
  prior Japanese occupation, friendly restoration and direct Indian control or
  an Indian land garrison at a published hub before India receives credit.
- Kept liberation purely operational: it opens no terms against the friendly
  owner, transfers no friendly territory and does not end India's war with
  Japan.
- Made liberation credit interoperable with the Malacca and South China Sea
  lane hinges where Darkest Hour returns allied provinces to their legal owner.
  Java Sea Command remains stricter and still requires the Batavia-Soerabaja
  operating pair plus its sixteen-ship screen.
- Rebuilt the flexible theatre victory around exactly three distinct results
  across both arms: either **two different land categories plus one sea lane**
  or **one land category plus two different sea lanes**. Three land results or
  three lanes alone do not qualify, and repeated results in one land category
  cannot be counted twice.

### Optional Japanese Southern Armistice

- Added a weaker, optional pairwise peace offer while India is still fighting
  Japan. Its exact live gate is an India-Japan war plus either
  `ind_aubm_japan_current` from the recoverable direct limited-victory map
  or `ind_aubm_sea_theatre_achieved` together with at least one **current**
  anti-Japanese friendly-liberation flag. The stronger Okinawa or Home Islands
  result uses the normal decisive great-power board instead of this weaker
  decision.
- Prevented a permanent route-neutral theatre record from being carried across
  a route switch into free Japanese terms. The theatre award alone is not
  sufficient; loss of the direct Japan claim or all current friendly
  liberations suspends armistice eligibility until live leverage recovers.
- Added southern in-flight state plus a shared great-power terms-dispatch lock,
  so initial, retry and different-opponent dockets cannot race into duplicate
  or disabled armistice popups. If decisive victory is
  earned during a refusal cooldown, the retry is promoted to the normal
  great-power board instead of being marked as a declined southern offer.
- Reused Japan's disclosed **45% accept / 35% counter / 20% refuse** response.
  Acceptance or counteroffer ends only the India-Japan war. Refusal continues
  the war. After the existing **90-day retry**, Japan's docket reopens only if
  the exact live Japan-specific gate still holds; otherwise it waits for the
  direct claim or a qualifying friendly liberation to recover.
- Limited any accepted southern transfer to a province Japan legally owns and
  India actually controls. British, Malaysian, Singaporean, U05, Dutch,
  Indonesian or other friendly-owner territory is never transferred by this
  armistice.

### Reviewed Saves

- The newest file, the **28 Aug autosave**, is a fresh 1934 campaign rather
  than a later wartime test.
- The **23 Aug manual save** records India as non-aligned and not at war. It is
  useful as chronology evidence but cannot validate alliance switching,
  liberation, sea-lane or armistice behavior.
- A new Alpha 21 wartime playthrough is therefore still required.

### Alpha 21 Status

Alpha 21 passed its final deterministic build, complete static suite, public
manifest, deployment verification and fresh executable smoke on 29 Aug 2026.
The release gate validated 4,434 overlay files, 40,357 global-campaign checks,
1,860 wartime checks, 668 route checks and the 21-event Southeast Asian
contract with **0 static errors and 0 warnings**. The public installer contains
**342 managed files** and final deployment verified all 342 hashes.

A fresh fullscreen 1933 India campaign reached the playable map and opening
AUBM events with 0 logged engine errors, province validation reporting **No
errors found**, no new crash dump and all 27 existing saves unchanged. The
developer's local-only 41-family visual overlay was restored after deployment
and verified separately. A new human wartime and postwar playthrough remains
required for balance, pacing and narrative acceptance.

## 4.2.0 Alpha 20 - Committed Alliances and Southeast Asian Victories

### Alliance Commitment

- Made formal Allied, German, Soviet and Japanese coalitions mutually exclusive
  with every rival binding compact.
- Preserved same-family compact-to-coalition upgrades, including the
  Delhi-Tokyo compact's independent Soviet-war design.
- Added serialized negotiation guards so a delayed foreign acceptance lapses
  after India makes another commitment.
- Replaced instant coalition transfer with an explicit at-peace withdrawal to
  sovereign command and a 90-day reset before another alignment can open.
- Reconciled old saves from live engine alliances and binding compact flags.
- Blocked declarations against current coalition partners in both bespoke
  campaign menus and all 210 generated country lifecycles.
- Made partner-collapse and rupture paths enter the same 90-day sovereign reset
  as voluntary withdrawal, so a failed coalition cannot become an instant
  side-switch shortcut.

### Southeast Asian Land and Sea Operations

- Added a Batavia-only U05 docket and a separate colonial-Netherlands docket.
  Both can settle locally without the full national Southern Theatre flag.
- Made colonial cessions legal-owner-only and pairwise. East Indies terms now
  include western New Guinea provinces 1594-1601 when the defeated owner
  actually holds them, while third-party territory remains untouched.
- Added a standalone British Malaya settlement for Indian control of Singapore
  and Kuala Lumpur, without requiring Borneo or the wider British campaign.
- Added Hanoi-Saigon and Manila-Davao land-operation milestones.
- Added one-time Bay of Bengal, Malacca, Java Sea and South China Sea naval
  milestones requiring 8/12/16/18 surface ships plus their operating ports;
  their live operating status suspends and recovers with those conditions.
- Added a flexible Southeast Asian theatre achievement based on combined land
  and sea results rather than compulsory conquest of every hub.
- Counted friendly released or protected Indonesia and Malaya as continuing
  victories instead of treating decolonization as a reversal.

### Campaign-State Recovery

- Fixed the 1934 union-integration dead state in which legitimacy and state
  capacity were present but neither provincial bargain nor coercion had been
  recorded.
- Added truth-table coverage for every 1934 integration-flag combination.
- Added dedicated validators for alliance commitment, southern settlements and
  Southeast Asian operations.
- Made global and southern peace callbacks transactional: every delayed step
  rechecks the live pairwise war and occupied objective, while military access
  is granted only after the ratified peace exists.
- Corrected 20 naval construction modifiers to use Darkest Hour's supported
  `build_time when = on_upgrade` syntax.
- Corrected the American campaign and armistice from Wake's sea-zone ID 2414 to
  the actual land province 1673, and added static gates for both engine rules.

### Save Review

- The later file by modification time is a May 1933 launch autosave, not a
  second developed campaign.
- The newest developed manual save is `AltIndia_1941_December_2.eug`. It
  records the Delhi-Tokyo compact, no formal Indian coalition and no Indian
  participant in a live war. This confirmed that the exposed Berlin action was
  an event-gating defect rather than a saved coalition transfer.
- The same save contains the mixed 1934 integration state that Alpha 20 now
  repairs.

### Status

Alpha 20 passes automated validation, deterministic rebuild, installed-file
verification and a fresh 1933 executable smoke with 0 logged errors. Start a
fresh 1933 campaign for gameplay testing; a complete human wartime and postwar
playthrough is still required. Focused results and remaining risks are tracked
in the gameplay status guide.

## 4.2.0 Alpha 19 - 1933 Launch Hotfix

### Engine Crash Fix

- Fixed unsupported foreign-country flag scopes in Japanese-partnership and
  wartime-settlement events that caused Darkest Hour to abort while loading the
  1933 campaign.
- Reworked those cross-country checks into Darkest Hour-supported event and
  callback logic while preserving the intended global flag contract.
- Added a validation gate that rejects the unsupported syntax before deployment.
- Confirmed that a fresh 1933 campaign reaches the playable map without the
  Alpha 18 parser failure.

### Public-Safe Source Snapshot

- Split public installer content from developer-only personal visual outputs.
- Excluded copied foundation and donor map files, donor-derived unit sprites and
  palettes, donor-derived model panels, and unresolved visual overrides.
- Kept local personal assets outside the release's Git tree and public
  manifests.
- Verified every file in the active installer manifest by SHA-256.

### Status

Alpha 19 passes static validation, installed-file verification and a fresh 1933
engine smoke test. A complete human wartime and postwar playthrough is still
required. This remains an alpha branch snapshot rather than a stable packaged
release.

## 4.2.0 Alpha 18 - Every War Has an Indian Ending

Alpha 18 turns the wartime framework into a complete campaign system. India
can align with Britain or the United States, Berlin, Moscow or Tokyo; retain a
separate-command compact; return to sovereign command; or declare a bilateral
war against any modeled country. Battlefield control now creates immediate
political feedback, a reversible settlement claim and a constitutional end
state instead of waiting silently for the global war to finish.

### Alliance And Command Routes

- Added deterministic formal-coalition precedence and canonical synchronizers
  for Allied, German, Soviet, Japanese and sovereign command.
- Added an explicit British or American choice for formal Allied entry and
  preserved that partner identity when India presents battlefield claims.
- Added chronology and state gates to every formal alliance and compact
  conference, plus recovery for completed or orphaned Allied negotiations.
- Added clean alliance departure and relationship cleanup when India attacks a
  former partner, changes sides, or loses its strategic partner to annexation.
- Added Allied command failover between London and Washington when the selected
  partner disappears, preserving India's current campaign and peace standing.
- Added an Indian Bitter Peace response: accept the armistice, continue a
  separate Soviet war, or record inherited peace without losing earned claims.
- Autonomous Indian socialism now uses the socialist wartime charter and Delhi
  congress while remaining under sovereign Indian command.
- Choosing postwar autonomy at the Socialist Peace Congress now preserves the
  domestic Indian socialist programme instead of relabelling it as ordinary
  non-alignment.

### Campaigns And Settlements

- Expanded the generated matrix to 210 country lifecycles. With five bespoke
  great powers and 21 bespoke regional opponents, India has 236 practical
  country-specific campaigns, including later successor states.
- Opened campaign recognition, reversals, recoveries, wartime finance and
  mobilisation from 1933 so an early sovereign war is no longer invisible.
- Rebuilt all 21 regional victory checks around live war, legal capital
  ownership and Indian control. Occupying a capital owned by a third country
  can no longer produce a false victory.
- Kept annexed-country monitors persistent: every annexation opens a choice to
  restore sovereignty, establish protection or assume costly direct rule.
- Added one-country refusal and retry locks so failed negotiations do not block
  unrelated settlements or allow repeated rewards.
- Replaced six universal declaration and armistice helpers containing up to
  1,695 commands with country-specific callbacks. The generated matrix now has
  3,223 small lifecycle events, and its largest event contains 210 commands.
- Added vanished-government recovery: if an opponent is annexed by another
  power while its reply is in transit, the dead response lock is removed and
  the country file can reopen if that state later returns.
- Hardened Central Asian peace terms. Moscow can transfer only a complete
  republic it legally owns and India controls; a failed transfer continues the
  war and reopens negotiation after cooldown.
- Added independent 60/25/15 foreign-response files for Persia, Iraq, Saudi
  Arabia, Yemen, Oman, Afghanistan, Tibet and Xinjiang. One refusal can no
  longer lock every other regional settlement.
- Removed the automatic Tibet transfer from the Japan path. Tokyo's Himalayan
  clause now improves the terms of a verified Indian-controlled settlement.

### Victory Feedback And Occupation

- Added one route achievement and one postwar Delhi congress per completed
  campaign, with current-route recognition after a legitimate side change.
- Added a route-wide achievement fallback so victory over any modeled country,
  including a late-created state outside the selected charter, can reach the
  Delhi peace congress.
- Preserved campaign credit through coalition collapse, rupture, armistice and
  strategic autonomy while preventing duplicate route rewards.
- Added an annual option to civilianize one occupation tier. Direct rule keeps
  an irreducible tier-one annual burden until sovereignty is actually changed;
  administrative reform alone cannot erase the cost of retained territory.
- Retained immediate theater feedback, local pairwise peace and provisional
  governments without requiring every Indian war to end.

### Production Gates

- Expanded the canonical wartime suite to 1,434 checks, alongside 28,175
  generated-country checks and 595 five-route consequence checks.
- New assertions cover coalition precedence, partner identity and collapse,
  direct-war cleanup, Bitter Peace, early-war monitors, all regional legal-owner
  guards, Central Asian transfer safety and occupation devolution.
- A new 1933 campaign is required to exercise the complete route state cleanly.

## 4.2.0 Alpha 17 - The War Has Consequences

Alpha 17 replaces overlapping wartime reward chains with one state-driven War
Cabinet and settlement system. India can follow Allied, German, Soviet,
Japanese or sovereign command, switch formal coalitions through an explicit
transfer rule, retain bilateral compacts, or declare an independent campaign
against any modeled sovereign country.

### Five Complete Strategic Routes

- Added four operational doctrines for each strategic route, selected when
  India enters its first live war on that route.
- Added twenty route-specific achievements tied to Indian-controlled
  objectives rather than another country's progress or a brittle event flag.
- Added five Delhi peace congresses. A completed campaign can produce a concert
  of sovereign partners, an Indian security sphere or renewed strategic
  autonomy.
- Preserved the distinct Delhi-Tokyo division of labour, including an Indian
  southern sphere and an independent Soviet war that does not automatically
  involve Japan under the strategic compact.

### Campaigns Against Any Country

- Added audited campaign lifecycles for 58 sovereign states not already covered
  by bespoke British, German, Soviet, Japanese, American or regional systems.
- Every lifecycle includes a declaration page, campaign brief, capital
  objective, reversal, recovery, fixed foreign response, India-scoped peace,
  refusal cooldown and post-annex constitutional settlement.
- Country-specific peace closes only that opponent. It does not silently end
  India's other wars or award territory before the relevant settlement choice.
- Previously settled regional and great-power files can reopen after a genuine
  later war; old victory and annex flags no longer block the new campaign.

### War Economy And Mobilisation

- Added an initial War Finance Act and one guarded annual budget cycle with
  bonds, progressive taxation, external credit and ordinary-revenue choices.
- Borrowing advances a cumulative four-tier debt register with postwar
  redemption, conversion, annual service or repudiation.
- Added cooldown-protected emergency credit for a negative wartime treasury.
- Added limited, national and technical mobilisation, one low-manpower service
  escalation and a real demobilisation or retained-readiness choice.
- Direct mandates now advance a scalable annual occupation register instead of
  granting cost-free map colour. The Japanese settlement uses the same ledger.

### Settlement Reliability

- Moved foreign accept, counter and refusal results into delayed callbacks;
  only India executes pairwise peace commands.
- Added one-response locks and 90-day retry files so a refusal cannot duplicate
  rewards or lose the selected country.
- Limited Arabian and Central Asian settlements to governments whose actual
  objectives India won. Existing unrelated republics can no longer become
  puppets merely because they exist.
- Formal Allied, German, Soviet and Japanese route state now converts to the
  appropriate separate-command compact before a local armistice.
- Retired the old overlapping wartime stacks while leaving prewar diplomacy,
  procurement and treaty conferences intact.

### Production Gates

- Added 620 canonical wartime checks, 2,852 every-country lifecycle checks and
  433 five-route consequence checks to the build.
- The build rejects foreign-scoped peace commands, stale generated matrices,
  missing retry locks, non-persistent reusable events, duplicate legacy reward
  stacks and a Japanese direct mandate without occupation upkeep.

## 4.0.0 Alpha 1 - The Direct Darkest Hour Rebuild

*Freedom came early. Unity came at a price.*

V4 rebuilds A Union Before Midnight as a standalone Darkest Hour Full
modification. India becomes independent on 1 January 1933, inheriting a vast
but uneven continental state from Ceylon to Burma. The player must turn that
political settlement into a functioning union, modern economy and credible
great power before the world crisis reaches Asia.

This is a genuine foundation change rather than a balance patch. V4 no longer
requires Blood and Iron, removes donor-dependent visual overrides, returns the
rest of the world to Darkest Hour Full and preserves the complete India
campaign developed through V3.

### New Foundation

- Rebased the mod directly onto the user's installed Darkest Hour Full.
- Removed the Blood and Iron runtime requirement.
- Removed inherited donor model panels, palettes, map sprites and unrelated
  event or AI overrides.
- Rebuilt the stock 1933 world around an independent India beginning on
  1 January rather than the stock March start.
- Made India the only selectable country while retaining the complete
  Darkest Hour Full world simulation.
- Preserved Ceylon as Indian territory at the start and Goa as Portuguese.
- Relocated Britain's inherited East Indies naval presence to Singapore.
- Limited map-data overrides to the India-region province scope.

### Campaign Scope

- 255 India-focused entries across 31 isolated event modules.
- 44 player-timed decisions and 211 scheduled, reactive or consequence events.
- Campaign content extending from the 1933 settlement through the Second World
  War, postwar reconstruction and early Cold War.
- A dedicated opening event explaining the alternate-history divergence,
  constitutional bargain and cost of keeping the subcontinent together.
- Stable constitutional leadership changes tied to political milestones rather
  than ordinary democratic and authoritarian slider movement.
- Five strategic routes: Allied cooperation, German alignment, Soviet
  partnership, armed non-alignment and a separate Japanese relationship.
- Japan remains an independent strategic path rather than an appendage of the
  German route.
- Indian reactions to Abyssinia, Spain, China, Anschluss, Munich, Prague,
  Albania and the invasion of Poland.
- Route-specific military missions, diplomacy, procurement, wartime policy,
  settlements and postwar consequences.

### Union Integration

- Added a Union Register covering the territories and obligations inherited
  by the new state.
- Added Ceylon settlement, customs-union, railway, telegraph, food-security and
  fiscal-federalism programmes.
- Added political and economic integration for Bengal, the Indus, Burma,
  Malaya-facing trade and the princely forces.
- Added recurring budget, public-works and provincial-force reviews.
- Added costs, dissent, supply and autonomy trade-offs so integration is a
  process rather than a free opening bonus.
- Added a 1938 maturation review reflecting the cumulative shape of the union.

### Economy And Development

- Begins India with 40 usable IC and a broad but uneven resource base.
- Retains a route-dependent 1933-40 provincial IC range of approximately
  151-210, with a representative middle path around 183 before wartime bonuses.
- Keeps further wartime industrial potential available without making every
  early investment affordable.
- Adds an inherited sterling reserve to make the opening state solvent without
  removing the need for trade, consumer production and spending choices.
- Rebalanced routine 1933-34 administrative costs while retaining expensive
  strategic programmes.
- The deterministic opening ledger leaves approximately 470 money after the
  standard V3 and V4 institutional programme, before ordinary daily trade and
  production income.
- Preserves a genuinely expensive full Airfield Security Act as an optional
  commitment rather than a compulsory early drain.
- Caps infrastructure at 100 and air bases, naval bases, radar, AA and forts at
  their engine limits.
- Prevents completed or in-progress construction from pushing a province over
  its supported maximum.

### Army Organization

- Reorganized the starting field army into twelve named three-unit formations:
  Southern, Western, Eastern, Central, Delhi, Baluchistan, Indus, Northern,
  Lahore, Waziristan, Peshawar and Kohat Mobile commands.
- Assigned historical or plausibly accelerated Lieutenant-Generals to the
  operational corps.
- Retained Ceylon, Burma and princely formations as territorial commands.
- Added Field Service Regulations, theatre commands, operational reserves,
  standardized corps tables and joint exercises.
- Made Support Defence and Reserves movement 30 percent faster.
- Added 1935, 1937 and 1939 exercises plus command-board rotations in 1940,
  1942 and 1944.
- Command-board choices develop officers outside the visible corps counter,
  approximating subordinate command experience that the engine cannot award.
- Retains the player's ability to detach a division, assign a Major-General and
  later merge it back into its named corps.

### Air Force Operations

- Standardized four-wing operational groups.
- Enabled Air Scramble missions from the start.
- Added the Airfield Security Act with garrison, mobile-security and provincial
  guard alternatives.
- Added dispersal fields, observer networks, radar coverage, hardened hubs and
  a wartime forward-basing protocol.
- Made emergency rebase orders resolve 35 percent faster.
- Increased the importance of organization, morale, detection and timely
  withdrawal over replacing entire destroyed wings.
- Preserved the intended 10-18 event-supported air-wing range by 1940 before
  normal player production.

### Naval Operations

- Retains Arabian Sea, Bay of Bengal and Indian Ocean fleet ambitions.
- Added repeatable tactical concepts for carrier groups, battle groups and
  escort or sea-control groups.
- Supports the intended one-to-three naval-aviation ships by 1942 depending on
  doctrine and strategic investment.
- Added the Bombay Damage-Control School and a joint replacement pool.
- Enabled Naval Scramble and improved harbor reaction time.
- Preserved carrier aviation, naval doctrine and oceanic research paths for
  India.

### Air And Naval Combat Pacing

This is a global V4 rules change and affects every country, not only India.

- Air-versus-air physical loss relative to organization loss is reduced to
  36 percent of the Darkest Hour Full ratio.
- Air-versus-ship physical loss is reduced to 44 percent of stock.
- Ship-versus-air physical loss is reduced to 31 percent of stock.
- Ship-versus-ship physical loss is reduced to 44 percent of stock.
- Increased organization pressure so fleets and wings usually disengage as
  damaged, repairable formations.
- Raised the automatic retreat threshold from 5 to 12 organization.
- Reduced air-to-naval critical-hit probability from 10 to 5 percent.
- Reduced naval critical-hit probability from 10 to 6 percent.
- Retained a 6x critical strength multiplier, allowing rare disasters without
  making catastrophic destruction the normal result of a four-hour battle.
- Reduced carrier strength damage during attacks on bases.

The intended result is not immortal ships or aircraft. Bad positioning,
inadequate screens, exhausted wings and critical hits can still destroy
expensive formations, but routine contact should create a repair decision
rather than an instant replacement programme.

### Procurement And Force Growth

- Added standard land tables, four-wing air-group doctrine and fleet tactical
  units.
- Added a wartime Joint Replacement Pool improving reinforcement efficiency.
- Preserved event support for approximately 67-108 effective land formations,
  10-18 air wings and 14-31 naval formations by 1940 before ordinary player
  queues and route-specific bonuses.
- Retained Gurkhas, frontier forces, airborne formations, marines and
  long-range penetration groups.
- Preserved Indian formation, corps, air-group, fleet and ship naming pools.
- Added immediate type and model availability before all 156 event-built force
  orders, preventing advanced formations from disappearing from production or
  deployment.

### Leadership And Research

- Retains 31 Indian technology teams covering civil industry, railways,
  medicine, armour, aircraft, carrier aviation, signals, radar, rocketry,
  atomic science and all major doctrines.
- Retains historically researched and plausibly embellished military leaders,
  ministers and service chiefs.
- Validates every scenario and event reference to an Indian leader, minister
  or technology team.
- Keeps advanced institutions dormant until their corresponding policy or
  investment event makes them available.
- Uses staged promotions and exercises rather than granting India a fully
  mature 1945 command system in 1933.

### Decisions And Event Design

- Decisions remain reserved for discretionary programmes the player may delay.
- Events handle crises, deadlines, responses, implementation disputes and
  consequences.
- Action labels show their principal costs and rewards.
- Routine one-option narrative events do not silently remove large amounts of
  money, supplies or manpower.
- Major alternatives pursue different strategic priorities rather than
  presenting one correct reward and several deliberately inferior choices.
- Added London, League, American, Soviet and Japanese responses to India's
  emergence as a continental power.
- Added war-aim, liberated-territory and demobilization settlements.

### Crash Prevention And Data Safety

- Every numeric event construction command is guarded by current Indian
  ownership.
- Every infrastructure, base, radar, AA and fort command is dynamically capped.
- Removed self-secession and unsafe force-trigger patterns.
- Prevented dated future events from being forcibly executed out of sequence.
- Validated all event IDs, flags, action probability totals and picture
  references.
- Validated scenario braces, quotes, province IDs, duplicate units and corps
  sizes.
- Validated Ceylon ownership and removed the former UK conflict.
- Validated every event-built division and brigade availability gate.
- Excluded the generic Purge the Army decision for India.
- The source validator currently reports zero errors and zero warnings.

### Visuals

- Removed the donor-derived V3 sprite, palette and model-panel package.
- Added 80 byte-distinct custom event pictures covering all India-specific
  picture names used by the campaign.
- Added one subject-specific reconstruction for every one of the 45 new V4
  events.
- Replaced all 30 former fallback copies with unique political, diplomatic,
  global-crisis and elite-force scenes.
- Rebuilt the founding, industry, armed-forces, German, Japanese, Soviet and
  world-reaction art from preserved local source sheets.
- Records every generated picture as an alternate-history reconstruction, not
  an archival photograph.
- Added machine-readable event-ID, source-panel and SHA-256 manifests plus
  complete V4 and campaign review galleries.
- The strict visual gate reports zero unresolved pictures, zero duplicate
  custom event images and zero provenance or hash issues.
- Added an original India map-sprite package with 13 visual families covering
  32 Darkest Hour unit types.
- Added 595 India-specific sprite descriptors and 234 indexed animation or
  palette files for infantry, Gurkhas, cavalry, mobile troops, armour, aircraft
  and the principal naval families.
- Generated the sprite source sheets specifically for this project rather than
  deriving them from a donor mod.
- Added a machine-readable sprite manifest, review preview and strict
  descriptor, bitmap, palette and coverage audit.
- Darkest Hour Full model and production-screen art remains in use; original
  India model panels are the next visual release phase.

### Installer And Build Pipeline

- The release overlay contains 1,042 managed files.
- `INSTALL.bat` detects Darkest Hour, clones Darkest Hour Full into an isolated
  V4 mod folder and applies the overlay.
- Every source and installed overlay file is checked against a SHA-256 manifest.
- Updates repair changed managed files while preserving unrelated saves.
- The developer pipeline rebases twice and rejects any byte-level
  non-idempotence.
- Build gates cover parser safety, personnel references, province ownership,
  opening economy, combat pacing, cumulative construction and installer
  integrity.
- The isolated installer passed both fresh-install and update-preservation
  tests.

### Installation

1. Install or verify Darkest Hour 1.05.2.
2. Run `INSTALL.bat`.
3. Select **A Union Before Midnight V4** in the Darkest Hour launcher.
4. Start **A Union Before Midnight: India 1933**.

The installed folder is separate from Darkest Hour Full and does not modify
the original foundation.

### Compatibility

- A new 1933 campaign is required.
- V3 saves are not supported.
- Blood and Iron is neither required nor used as the V4 runtime foundation.
- Other mods that replace Darkest Hour Full scenario, India, event or global
  combat data are not supported.
- The combat-pacing changes affect the entire simulated world.

### Engine Limitations

- Darkest Hour permits only one leader per formation and cannot nest
  Major-General divisions beneath a Lieutenant-General corps counter.
- The executable exposes no event command that finds all wings at a threatened
  airfield and automatically rebases them to the nearest friendly base.
- V4 therefore uses named three-unit corps, officer rotations, guarded bases,
  scramble missions, detection and faster player-issued rebase orders.
- Threatened aircraft still require a player rebase order.
- These limitations cannot be removed without executable-level development or
  creating a new game.

### Alpha 18 Superseded Status

Alpha 18 passed its static gates but failed its first fresh 1933 launch because
of unsupported foreign-country event syntax. Alpha 19 supersedes it with the
launch fix and public-packaging hardening.

## 3.4.1 Open Beta Hardening

### Balance And Exploit Fixes

- Rebalanced the national science decision and capped the conservative
  permanent research upper bound at 22% in 1940 and 34% in 1945.
- Replaced deliberate-bankruptcy and free-manpower rewards with conditional
  emergency measures, political costs and a later fiscal settlement.
- Added event-level reachability gates to all 23 mandatory events whose
  actions require resources.
- Removed the light carrier from the submarine doctrine package.
- Reduced the Allied broad-basing windfall.

### Strategic Outcomes

- Required actual Comintern membership for Soviet war command.
- Made Imphal recognition require a wartime Malayan objective.
- Prevented German and Japanese settlements from overlapping.
- Route settlements now require peace, a secure Delhi and the relevant active
  alignment.

### Art, Attribution And Packaging

- Replaced three confirmed swastika-bearing images with original, symbol-free
  reconstructions and rebuilt the public event gallery.
- Added explicit creator and credit fields for Creative Commons portraits.
- Removed 15 unrelated or retired inherited files from the overlay.
- Corrected installer updates so retired overlay files revert to the user's
  Blood and Iron foundation instead of being deleted blindly.
- Corrected distributed documentation and added a forum-release audit.

### Validation

- Source and installed-mod parser validation: zero errors and zero warnings.
- Event/decision audit: 210 entries, 41 decisions and 169 events.
- Research, economy, force, province-construction and all five deterministic
  prewar route gates pass.
- Managed overlay: 2,911 files.

V3.4.1 requires a new 1933 campaign. The 1942-1964 content remains beta
pending full-war and postwar playthroughs.

## 3.4.0 Narrative And Decision Update

### A Union Before Midnight

- Renamed the campaign **A Union Before Midnight**.
- Added a dedicated opening event explaining the alternate 1933 transfer of
  power before the player chooses a provisional cabinet.
- Grounded the divergence in the Round Table Conferences, the Poona settlement,
  the all-India federation debate and Britain's planned 1933 constitutional
  White Paper.
- Renamed the founding art and removed the discarded working-title namespace.

### Events And Decisions

- Audited all 209 India entries individually.
- The campaign now contains 41 player-timed decisions and 168 scheduled or
  reactive events.
- Decisions are reserved for optional authorizations the player may defer.
- Events cover constitutional deadlines, external crises, foreign replies,
  implementation disputes, milestones and consequences.
- Added a build gate and public row-by-row audit enforcing that distinction.
- Automatic one-option events may no longer silently deduct money, supplies or
  manpower.

### Programme Timing

Converted these costly automatic appropriations into decisions:

- Arabian Sea Fleet;
- Bay of Bengal Fleet;
- carrier keels;
- 1940 resource-grid resilience;
- Aeronautics and Rocket Centre;
- Indo-Soviet Science Exchange.

The automatic commissioning of Arjan Singh's generation no longer carries an
unexplained cash and supply charge.

### War Finance

- Standardized **Finance the Long War** as a player decision.
- Reworked the 1941 **Second War Budget** into a genuine wartime consequence
  that follows the original financing authorization.
- The economy gate reports zero decision-affordability mismatches.

### Validation

- Source and installed-mod parser validation: zero errors and zero warnings.
- Event/decision audit: 209 entries passed.
- Infrastructure remains capped at 100.
- Air and naval bases remain capped at level 10.
- All five deterministic strategic paths reach 1940 solvent.
- Installed overlay verification: all 2,923 files passed SHA-256 checks.

## 3.3.0 Reliability And Visual Update

- Corrected event-created serial manpower checks and removed double charging.
- Enabled advanced unit types and models before event queues request them.
- Added save-compatible reserve, armoured-corps and air-transport registration.
- Guarded all infrastructure, air-base and naval-base construction.
- Expanded India's land, air and naval sprite distinction while retaining
  Blood and Iron animation compatibility.
- Preserved dedicated Gurkha presentation.

## 3.2.0 Government, Research And Service Update

- Fixed the invalid anti-tank attachment crash.
- Stabilized constitutional governments and cabinet transitions.
- Expanded researched minister, commander and technology-team traits.
- Added carrier aviation, radar, signals, rocket and atomic research coverage.
- Separated the Japanese strategic route from the German route.
- Added global-crisis reactions and four elite-force programmes.
- Added bespoke technology-team and personnel art.

## 3.0.0 Rebuild

- Rebuilt the campaign in the reserved `9270000-9279999` namespace.
- Added Allied, German, Japanese, Soviet and armed non-aligned paths.
- Added a three-fleet navy, expanded air arm and postwar content through 1964.
- Added Indian formation naming, provincial corrections and resource
  redistribution.

## Foundation Behaviour

Blood and Iron defines naval transports as convertible into light carriers.
With automatic upgrades funded, transport flotillas may become light carriers.
This global foundation rule remains unchanged because altering it would affect
every country.
