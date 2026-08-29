# Gameplay Fun Rework Specification

- Status: Living implementation contract; Alpha 22 implements a focused first subset
- Baseline: A Union Before Midnight 4.2.0-alpha.21
- Current implementation: 4.2.0-alpha.22, built, locally deployed and fresh-start smoked
- Scope: Post-Alpha 21 player-experience, campaign-flow and balance pass
- Last updated: 29 August 2026

This document specifies the changes required to make the campaign more
readable, deliberate and enjoyable for a human player. It remains the complete
forward specification rather than a release note. Alpha 22 implements only the
clean-opening and focused early-event-audit subset recorded below; unmarked
requirements remain planned work. Alpha 22 is the current built and
launch-smoked baseline for this focused subset.

## Alpha 22 Implementation Boundary

Implemented in source for **Alpha 22 - A Clean Opening and Audited Early
Game**:

- The fresh pre-union sequence is reduced from nine windows to three
  player-facing windows total: one scenario-opening premise acknowledgment,
  the cabinet choice during the opening 72 hours and the 6 January union
  choice.
- Fresh initialization and the Union Register are folded into those choices;
  the War Cabinet is gated until the union is complete.
- Compatibility helpers are excluded from fresh campaigns, retain readable
  Compatibility Review copy for upgraded saves and cannot replay fresh-start
  money or manpower.
- The fresh scenario pre-sleeps 218 events total: 216 retired legacy
  wartime/route IDs plus the two generic V3 Gurkha and frontier decisions.
  Fresh games use the unique V4 specialist paths.
- The adjacent-event audit makes 1934/1936 reviews mutually exclusive,
  gives all 18 founding branch identities one modest remembered dividend in
  the one-shot July 1934 Union report, implements two advertised research
  rewards, prevents foreign credit from charging itself, redirects unsafe old
  War Cabinet menus, cross-locks the V3 and V4 Gurkha/frontier systems and
  discloses opening action costs.
- A focused cold-start validator covers the fresh marker, retirement set,
  opening grants, compatibility exclusions, Union Register folding and War
  Cabinet gate.

This is a **completed source subset of Milestone 1**, not completion of the
entire milestone or specification. The State of the Union ledger, global popup
budget, annual-budget redesign, full integration-chapter redesign, general
save migration, national priorities, wider force balance, guided campaign
operations, staged Southeast Asia, settlement ambition and postwar memory all
remain planned. Alpha 22's deterministic build, local deployment and fresh
opening smoke have passed; a complete human wartime/postwar playthrough has not.

The central design decision is:

> Do not add another layer of hidden events. Turn the existing systems into
> visible national projects and chosen military campaigns: announce the goal,
> let the player prepare, show progress, and make the result remember how the
> player achieved it.

## 1. Required Outcome

After this rework, a player must be able to answer the following questions
inside the game without consulting external documentation:

1. What kind of India have I created?
2. What are the next three important domestic or military opportunities?
3. What is due, what is optional, and what will default on a fixed date?
4. Is the army, air force and navy ready for the campaign I am considering?
5. Which alliance or separate-command commitment is binding?
6. What is my selected wartime objective?
7. What has been earned permanently, what is held currently, and what has been
   suspended?
8. What settlement can India request, with what risks?
9. Which of my earlier political and wartime choices will matter later?

Every significant popup must either:

- ask a meaningful question;
- announce a result the player was already pursuing;
- warn that a known objective or settlement has materially changed; or
- deliver a foreign response or final political settlement.

Migration, bookkeeping, state synchronization and recurring counters must not
create standalone player modals. Darkest Hour does not provide a proven hidden
IND-event field in this codebase, so deterministic work must be seeded in the
scenario, folded into an originating player action, or evaluated directly by a
decision. One compatibility review is permitted only when a real human choice
is required.

## 2. Scope and Non-Goals

### In scope

- Cold-start event pacing.
- A permanent State of the Union and readiness ledger.
- Clear programme deadlines and a fixed annual budget calendar.
- Callbacks from founding political choices.
- Optional peacetime map missions and national priorities.
- Air-force, Airfield Security, Gurkha and event-force balance.
- Guided and sandbox War Cabinet navigation.
- Commitment crises when a partner enters a major war.
- Primary wartime-focus protection.
- A player-readable Operations Board.
- Staged Southeast Asian land and sea operations.
- Risk-and-reward armistice demands.
- Mobilisation, readiness and debt exploit closure.
- Postwar memory of route, conduct and settlements.
- Save migration, diagnostics, validators and human playtest fixtures.

### Not in scope

- Adding more country tags to the 236-country campaign matrix.
- Removing the unrestricted any-country sandbox.
- Replacing Darkest Hour combat, production or AI systems.
- Automatically cancelling, reordering or rewriting a human production queue.
- Deleting units from an upgraded save.
- Reassigning or replacing the user's local sprite profile.
- Weakening legal-owner checks, pairwise peace, alliance exclusivity or the
  friendly-liberation safeguards introduced in Alpha 20 and Alpha 21.
- Forcing a separate-command compact into a partner's war. Formal alliances
  retain disclosed automatic war inheritance.

## 3. Evidence Baseline

The following saves and historical snapshots are read-only design and
regression fixtures. Rotating autosave filenames are labeled by the date on
which they were reviewed, not by their current filename on disk. They
demonstrate human behavior and state compatibility, not proof of
future-version stability.

| Fixture | Date and state | Design evidence |
| --- | --- | --- |
| Current Alpha 22 autosave, reviewed 29 Aug | 1 February 1933; sovereign and at peace; clean opening complete | All three opening IDs and Army Oath fired once; no Compatibility Review fired; Union and War Cabinet state are coherent. This validates the opening, not wartime balance. |
| 28 Aug autosave snapshot | 1 August 1934; sovereign and at peace; 52 base IC, 60 land divisions, three transports, zero air wings | The player has a coherent consensual-maritime identity, but no visible readiness plan. About 62.74 IC of orders compete for roughly 29-30 IC assigned to production. |
| Earlier oldautosave snapshot | 1 July 1934; same campaign | July reforms create real progress: dissent reaches zero, manpower rises by roughly 190, and administration/research improve. The game does not synthesize that progress for the player. |
| autosave_AUBM_v42_alpha3_repaired.eug | 1 December 1934; coercive/security branch | A materially different infantry-and-fighter posture proves that branches can express themselves, but their identity is not reported clearly. |
| AltIndia_1941_December_2.eug | 2 December 1941; senior Japanese partnership, but India is outside Japan's new wars | This should produce a dramatic join, limit, or withdraw decision. The current state is powerful but passive. |
| inda firstIndia_1942_April_3.eug | 3 April 1942; sovereign, no war, only 70.69 manpower | Independent intervention is viable, but neutral play needs active goals and a real win condition rather than inactivity. |

No August 2026 save presently available contains India as a war participant.
Older wartime saves in legacy mod folders are not substitutes for a new human
wartime acceptance run.

## 4. Target Player Flow

~~~mermaid
flowchart TD
    A["Found India"] --> B{"Choose cabinet and union method"}
    B --> C["State of the Union ledger opens"]
    C --> D{"Choose one national priority"}
    D --> E["Prepare through programmes and map missions"]
    E --> F["Visible capstone and updated national identity"]
    F --> G["Choose strategic commitment or sovereign command"]
    G --> H{"Partner crisis or independent campaign plan"}
    H --> I["Operations Board publishes readiness and objectives"]
    I --> J["Authorize war"]
    J --> K["Complete and hold staged objectives"]
    K --> L{"Seek limited terms or press for decisive victory"}
    L --> M["Delhi ratifies pairwise settlement"]
    M --> N["Congress and postwar events remember route and conduct"]
~~~

## 5. Change Inventory

| ID | Change | Priority | Primary implementation area |
| --- | --- | --- | --- |
| UX-01 | Compress the fresh 1933 opening | Must | india_v3/00_bootstrap; V4 bootstrap and migration modules |
| UX-02 | Add State of the Union and Readiness Ledger | Must | New player-ledger event module |
| UX-03 | Enforce a player-facing popup budget | Must | All domestic, migration and wartime modules |
| UX-04 | Fix annual budget calendar and programme deadlines | Must | aubm_v4/12_campaign_systems; india_v3 fallbacks |
| POL-01 | Replace opaque integration booleans with chapter outcomes | Must | aubm_v4/05_union_integration |
| POL-02 | Make foundational choices produce later callbacks | Must | Bootstrap, politics, society, integration and diplomacy modules |
| OBJ-01 | Add one active national priority | Should | New peacetime-objectives module |
| OBJ-02 | Add optional peacetime map missions | Should | New peacetime-objectives module |
| BAL-01 | Separate airfield security from an actual air force | Must | aubm_v4/15_operational_command |
| BAL-02 | Rebalance the Gurkha progression | Must | india_v3/30_military; special-unit compatibility |
| BAL-03 | Add soft force ceilings to event rewards | Must | Procurement, reserve and special-unit modules |
| BAL-04 | Remove or replace misleading generic decisions | Must | generic_decisions and AUBM alternatives |
| STR-01 | Split guided War Cabinet play from full sandbox | Must | aubm_v4/32_national_consolidation; wartime state |
| STR-02 | Add partner-entry strategic crises | Must | Allied, German, Soviet, Japanese and sovereign strategy modules |
| OPS-01 | Add the Campaign Operations Board | Must | New operations-board module; wartime state |
| OPS-02 | Protect the selected primary charter focus | Must | aubm_v4/48_route_wartime_consequences |
| SEA-01 | Add consolidation and staged theatre play | Must | aubm_v4/50_southeast_asia_operations |
| SET-01 | Add selectable settlement ambition | Should | Great-power, regional and generated country dockets |
| ECO-01 | Close mobilisation/readiness/debt exploits | Must | Wartime economy and reserve modules |
| MEM-01 | Persist conduct and congress choices | Should | Settlement, congress and postwar modules |
| MIG-01 | Add idempotent save migration | Must | Campaign continuity and version migration |
| QA-01 | Extend save analysis and player-UX validation | Must | tools/analyze_v4_campaign.py; new validator |

## 6. Cold Start and Player Information

### UX-01: Fresh 1933 opening

**Alpha 22 source status:** the three-window target is implemented. Event
9270000 now owns the fresh initialization, and every union action in 9270001
opens the Union Register and integration chain. Event 9280100 is bypassed on a
fresh start; it has not yet become the permanent State of the Union doorway
described in UX-02. The new scenario marker pre-sleeps 218 events: 216 retired
legacy wartime/route IDs and the two generic V3 Gurkha/frontier decisions. It
also excludes the compatibility helpers below. The 1 February engine autosave
records all three opening IDs followed only by Army Oath (`9271200`), and no
Compatibility Review ID.

A fresh campaign may show no more than three mandatory AUBM windows before
10 January 1933:

1. A Union Before Midnight: the narrative premise.
2. The Provisional Cabinet: the first governing coalition.
3. One Administration, Many Nations: the opening union method.

Move the authoritative Union Register initialization commands
aubm_v4_union_register_opened and aubm_v4_integration_active into the opening
union action in 9270001. Event 9280100 then becomes the optional State of the
Union doorway; making it optional before relocating those commands would stall
the whole integration chain.

For fresh starts, fold 9280000's reserve/state initialization and 9281000's
national-consolidation effects into 9270000, then seed fresh-only compatibility
markers such as ind_v32_roster_compatibility and
ind_v41_strategy_ledger_reconciled. Deterministic inherited-technology,
modernization-contract, ledger, roster, campaign-state and compatibility work
must be folded into those originating actions or seeded in british raj.inc,
not placed in separate IND helper events.

Use distinct flags for a fresh rework start and completed old-save migration.
An older save gets one consolidated Compatibility Review only if a real human
choice is required. Version migration must never regrant the fresh-start money
or manpower.

Alpha 22 implements the no-regrant rule and gives each retained helper concise
Compatibility Review language. Full consolidation of every upgraded-save
helper into a single review remains part of MIG-01/UX-03 rather than this
release subset.

The following current classes of notices must not appear separately on a fresh
start:

- inherited archive restoration;
- low-IC or modernization correction;
- campaign-state initialization;
- wartime ledger initialization;
- settlement registry initialization;
- generated-route migration;
- unit roster or procurement compatibility correction.

Acceptance:

- No migration, correction, registry or ledger title appears during the first
  week of a fresh 1933 campaign.
- Cabinet and union choices retain all current choices and costs.
- Saving and reloading immediately after each opening choice does not duplicate
  any effect.

### UX-02: State of the Union and Readiness Ledger

Add a permanent zero-cost decision named Review the State of the Union. It
opens after the initial union choice and remains available through 1964.

Provisional event allocation, subject to the event-ID collision validator:

- 9289000-9289099: State of the Union dispatchers and status variants;
- 9289100-9289199: peacetime priorities and missions;
- 9289200-9289399: Operations Board and Southeast Asian status variants;
- 9289400-9289499: migration and compatibility decisions.

Top-level actions, using the four-action engine limit:

1. Union and Government.
2. Economy and National Programmes.
3. Armed Forces and Readiness.
4. Foreign Policy and Current Operations.

Navigation changes no gameplay state and has no cooldown. Temporary navigation
flags may be used only when necessary and must be cleared on exit. Each child
page reserves action_d for Return or Close; multi-page categories use
Previous, Next, Details and Return. A state report must be reachable in no more
than three player selections, verified against this four-action tree.

#### Union and Government page

Display:

- Cabinet identity.
- Constitution identity after chosen.
- Union style: consensual, provincial, administrative/coercive, or mixed.
- Each resolved integration chapter.
- Exact reason for the forecast 1934 and 1936 outcome.
- The next constitutional review and its date.

#### Economy and National Programmes page

Display:

- Current money, supplies and debt tier by descriptive bands.
- Whether this calendar year's Union Budget is due, completed or defaulted.
- Every active national programme and its real default date.
- The nearest three programme opportunities.
- The current selected national priority, if any.

Darkest Hour cannot interpolate arbitrary values safely in event prose. Use
triggered status variants and bands rather than claims of exact dynamic text.

#### Armed Forces and Readiness page

Display non-binding bands:

- Total deployed land counters: fewer than 48, 48-71, 72-79, or 80-plus.
  Report field/mobile formations separately from garrison/security formations
  when the save analyzer can distinguish them.
- Air: zero, 1, 2-3, 4-7, 8-11, 12-23, or 24-plus deployed, pooled or
  contracted wings; identify the awaiting-deployment state.
- Ready surface fleet: 0-7, 8-11, 12-15, 16-17, 18-35, or 36-plus qualifying
  surface units.
- Transports: absent, limited, or operational.
- Burma-Andaman readiness.
- Whether a First Operational Wing is still outstanding.

The surface-ship count must use the same inclusion and exclusion rules as the
Alpha 21 sea-lane system.

Recommended, explicitly non-binding guide:

| Review date | Land | Air | Sea |
| --- | --- | --- | --- |
| End 1935 | Organize the inherited army into four to six theatre commands | At least two real wings | Escort nucleus; capital ships optional |
| End 1937 | Maintain a western and eastern reserve | At least four real wings | At least eight qualifying surface ships plus transports |
| End 1939 | Avoid further mass expansion above roughly 72 divisions unless a land war demands it | Eight to twelve balanced wings | One operational Indian Ocean fleet |

The ledger may warn that a carrier-heavy programme competes with aircraft,
escorts and factories, but it must never modify the player's queue.

#### Foreign Policy and Current Operations page

At peace, display:

- Current orientation.
- Binding commitment family, if any.
- Compact versus formal alliance.
- Whether wars would be separate or shared.
- Realignment cooldown.
- Date at which the curated War Cabinet becomes available.

At war, this page links directly to the Campaign Operations Board.

### UX-03: Popup budget

The following authored-content limits apply:

- Target no more than one authored automatic domestic informational popup in
  any rolling 30-day peacetime period. Additional information moves to the
  State of the Union ledger.
- Use stable decision visibility predicates so resource fluctuation does not
  deliberately hide and reannounce programmes. Darkest Hour owns
  decision-availability notifications, so repeated engine notifications are an
  executable-test finding rather than a statically guaranteed absence.
- No one-action annual reserve-class modal.
- No standalone helper, synchronizer, retry-counter, debt-register or
  deterministic migration event. Fold its commands into another action or
  scenario initialization.
- The first seven days after a new war begins target one consolidated authored
  campaign-opening briefing and no other automatic informational modal.
- War finance, mobilisation, readiness and ledgers are player-opened decisions.

Player choices, foreign crises and foreign answers are exempt, but two
unrelated scheduled choices should be staggered when they would otherwise fire
on consecutive days.

Add a validator that classifies every AUBM event as choice, consequence,
milestone, foreign response, settlement, helper or migration. Static checks
fail when deterministic helper commands remain in a standalone authored modal.
Fresh-start, rolling cadence and war-opening budgets are fixture and executable
smoke assertions; unsupported state-dependent triggers report indeterminate
rather than a false pass.

### UX-04: Fixed annual budget and disclosed programme defaults

Replace the drifting 360-day Union Budget cooldown with generated,
calendar-year state:

1. Budget becomes due on 1 January.
2. The player may act through 30 November.
3. A State of the Union warning appears from 1 September.
4. If still unresolved on 1 December, Continuing Appropriations executes once:
   no lump-sum money, +1 dissent, and the year is marked closed.
5. The next budget always opens on the following 1 January.

Only one budget may execute per calendar year. Existing taxation, bonds,
foreign credit and austerity identities remain, but currency callbacks in
POL-02 modify their disclosed terms.

Generate due_YYYY and closed_YYYY state for every year from 1934 through 1964.
Each year's events use year = YYYY together with NOT = { year = YYYY+1 };
day = 0 is 1 January/1 December and day = 29 month = november is 30 November.
The generated source and validator must prove exactly one open and one close
path per year.

Old-save migration bridges conservatively at the next 1 January. Whether the
old 360-day cooldown is active, inactive or has just expired, the ambiguous
current calendar year is closed without a payout; opening it midyear could
duplicate a budget already taken. Set the new calendar version flag last and
never pay or deduct money during migration.

The following current automatic fallback dates must be printed in the decision
description and on the ledger:

| Programme | Cabinet default |
| --- | --- |
| Emergency Reconstruction | 1 January 1935 |
| Transport Grid | 1 January 1936 |
| Rebuild the Indian Army | 1 January 1936 |
| Steel Programme | 1 January 1937 |
| Aviation Programme | 1 January 1937 |
| National Power Programme | 1 January 1938 |
| Naval Programme | 1 January 1938 |
| National Science Programme | 1 January 1939 |
| Armaments Programme | 1 January 1939 |
| Second Plan | 1 January 1940 |
| Force Expansion Programme | 1 January 1940 |

Every programme receives an explicit Delegate the Minimum Programme action.
If the programme already uses all four engine actions, expose delegation
through the State of the Union programme page rather than adding an impossible
fifth action. Selecting it executes the same reduced fallback immediately and
closes the decision deliberately. If the date arrives first, one concise
consequence may announce the adopted minimum; content must never simply
disappear without a stated outcome.

## 7. Political Identity and National Priorities

### POL-01: Integration chapters

Stop using repeated writes to a few generic booleans as the sole explanation
of integration. Preserve every historical flag and current review output for
compatibility, but calculate reviews that have not yet fired from resolved
chapters:

1. Opening union settlement.
2. Ceylon.
3. Customs.
4. Bengal revenue.
5. Frontier.
6. Princely settlement.
7. First Union Budget.
8. Provincial forces.
9. Language settlement.
10. Civil administration.
11. Burma implementation.
12. Fiscal federalism.

Each chapter records one dominant method:

- consent;
- provincial bargain;
- administrative capacity; or
- coercion.

The first seven chapters use this fixed classification:

| Chapter | Consent | Provincial | Capacity | Coercion |
| --- | --- | --- | --- | --- |
| Opening union | Negotiated union | Provincial compact | — | Central decree |
| Ceylon | Constituent autonomy | — | Union representation | Strategic administration |
| Customs | Compensated customs | Regional clearing house | Uniform tariff | — |
| Bengal | Guarantee growers | Joint jute board | Back mills/exporters | — |
| Frontier | Constitutional water council | Provincial bargain | Strategic commissioner | — |
| Princes | Dignities for accession | — | — | Compulsory integration |
| First budget | Honour every compact | — | Balance treasury or development loan | — |

Later chapter actions receive an equally explicit one-method mapping in source
and validation. A choice may produce secondary flavor flags, but exactly one
dominant chapter method counts toward the review.

The 1934 review examines the first seven chapters:

- Union by Consent: at least five consent/provincial chapters and no more than
  one coercive chapter.
- Administrative State: at least five capacity/coercive chapters.
- Mixed or Unfinished Bargain: every other valid combination.

The mixed review is not described as a generic failure. Triggered variants name
the two most important unresolved or contradictory chapters. The State of the
Union ledger must forecast the same result using the same predicate.

The 1936 review requires provincial forces, language, civil administration,
Burma and fiscal federalism to be resolved. It then reports a rooted
consensual, administrative or mixed federation according to the accumulated
chapters. Recovery from the 1934 mixed review remains possible and must be
forecast.

Preserve the existing compatibility outputs:

- 1934: aubm_v4_legitimacy_established,
  aubm_v4_capacity_established, aubm_v4_integration_fragile and
  aubm_v4_review_1934.
- 1936: aubm_v4_union_rooted, aubm_v4_union_contested and
  aubm_v4_review_1936.

Add method-specific child flags when needed, but do not clear or repurpose
these outputs. If a save already has a review flag, derive chapter history for
the ledger and future recovery only; never reroll the completed review.

Acceptance:

- The initial consensual, provincial and central union flags are read by later
  reviews and never cleared.
- A coherent branch is not labelled fragile without naming the missing
  chapter.
- Every possible chapter combination reaches exactly one 1934 and one 1936
  result.
- The State of the Union forecast and actual event cannot disagree.

### POL-02: Foundational callbacks

Early choices must provide one later, disclosed callback rather than only an
immediate modifier.

**Alpha 22 source subset:** all 18 branch flags from the six three-way 1933
Union settlements were previously written but never read. Event 9280112,
**Telegraphs, Statistics and a Common Time**, now reads each selected identity
once in the first July 1934 Union report and pays the following modest dividend
without creating another popup:

| Settlement | First branch | Second branch | Third branch |
| --- | --- | --- | --- |
| Ceylon | Autonomy: +8 manpower | Representation: +1 TC | Strategic administration: +200 supplies |
| Customs | Compensated customs: +100 money | Uniform tariff: +150 money | Regional customs: -1 dissent |
| Malaya | Treaty: +100 rare materials | Commercial policy: +150 money | Security policy: +200 supplies |
| Bengal | Growers: +8 manpower | Exporters: +150 money | Board: -1 dissent |
| Frontier | Council: -1 dissent | Commissioner: +200 supplies | Provincial system: +8 manpower |
| Budget | Compacts: -1 dissent | Austerity: +150 money | Loan: +250 supplies |

The report remains nonpersistent, one-action and guarded by its existing
completion flag. The validator requires exactly one approved callback for each
of the 18 identities and requires the completion flag to be set only after all
callbacks. This closes the write-only choices but does not implement the wider
cabinet, constitution, land, currency and strategic callbacks below.

| Foundational choice | Required callback |
| --- | --- |
| Federal cabinet | At the 1934 review, a consensual or mixed outcome receives -1 dissent and the text credits civilian bargaining. |
| Developmental cabinet | At the 1934 review, an administrative or mixed outcome receives +2 TC and the text credits implementation capacity. |
| Social cabinet | At the citizenship/land review, receive +10 manpower and -1 dissent if a social-rights or redistribution policy was also chosen. |
| Parliamentary constitution | The 1936 mandate receives -2 dissent and an additional provincial-consent option. |
| Planning constitution | The 1936 mandate receives +2 TC and an additional coordinated-programme option. |
| Social constitution | The 1936 mandate receives +15 manpower and a rights-enforcement option with a lower dissent cost. |
| Land redistribution | The public-granary option costs 25 less money. |
| Rural investment | The public-granary option yields 250 additional supplies. |
| Property compact | The trade-granary option yields 75 additional money. |
| Sovereign currency | Domestic bonds yield 100 additional money but add the same debt tier as before. |
| Sterling currency | Foreign credit yields 100 additional supplies and a disclosed British-relations callback. |
| League/collective-security support | The first Allied strategic consultation costs 100 less money and explicitly credits League work. |
| American expertise | The first National Science Programme action costs 100 less money. |
| Soviet expertise | The first state-led Steel or Power action costs 100 less money and 200 less supplies. |
| Ceylon and Malaya policy | Alters the wording and one readiness condition of later island-base and Southeast Asian planning. It never changes legal ownership. |

Callbacks must:

- be visible before the later choice;
- execute once;
- use modest deterministic effects;
- never create an undisclosed alliance;
- never make one founding choice permanently dominate every later system.

### OBJ-01: One active national priority

Add zero-cost decisions to select one national priority. A priority highlights
existing work; it does not disable unrelated decisions. Exactly one may be
active, persists until completion or explicit abandonment, and pays its modest
capstone once. Abandonment costs 1 dissent and immediately permits another
eligible priority; no relative timer or cancellation helper is required.

| Priority | Completion requirements | Capstone |
| --- | --- | --- |
| Consolidate the Federation | Opens when the Burma/fiscal sequence is available; requires language settlement, provincial forces, Burma implementation and fiscal federalism | -2 dissent, +2 TC, and a political callback at the 1936 review |
| Complete the Industrial Spine | Opens with the Steel Programme; requires Reconstruction, Transport Grid and Steel Programme | +2 supply-output modifier and one disclosed industrial follow-up |
| Build a Mobile Continental Army | Opens after Army Reform; requires Gurkha Stage II and the western/eastern field exercise | +1 land organization and a named command review |
| Command the Indian Ocean | Opens with the Naval Programme; requires First Operational Air Group, Port Blair network and at least eight surface ships | +1 naval organization, +1 air organization and the Indian Ocean planning brief |

Completing underlying work before selecting a priority is valid, but the
capstone cannot repeat. There is no expiry; late selection remains valid.

### OBJ-02: Peacetime map missions

Add three optional, one-time missions between 1934 and the start of India's
first war:

#### Frontier Field Exercise

- Require the Gurkha establishment flag ind_v3_gurkha_arm or
  ind_aubm_gurkha_rifles_commissioned.
- Require a validated Indian land-garrison test at Quetta (1529) or Peshawar
  (1537).
- Require another validated Indian land-garrison test at Imphal (1442) or
  Rangoon (1415).
- Maintain both for 30 days.
- Reward +1 land organization and one named command/leader follow-up.

#### First Air Exercise

- Require at least one real Indian air wing.
- Require a usable air base at Delhi, Calcutta or Rangoon.
- Maintain readiness for 30 days.
- Reward +1 air organization and -1 dissent.

#### Eastern Fleet Exercise

- Require eight qualifying surface ships, adequate transports, Port Blair
  (1421), and Ceylon under Indian control.
- Maintain readiness for 30 days.
- Reward +1 naval organization and the first Indian Ocean operational brief.

The engine test proves a Gurkha establishment plus deployed field forces; it
does not claim that the specific formation in a province is Gurkha. Air and
fleet location requirements become acceptance criteria only after a real-engine
proof of the relevant trigger. Otherwise use the closest validated
formation/base test and state that limitation honestly.

## 8. Force Structure and Balance

### BAL-01: Airfield Security and the first real air wing

Refactor event 9280152, The Airfield Security Act. It remains a ground-security
decision and must say so explicitly.

| Choice | New force result | Additional effect |
| --- | --- | --- |
| Static shield | Three regional garrison-AA formations: Delhi, Calcutta and Rangoon | Fixed AA/radar improvements |
| Mobile security | Two mobile militia-AA formations | +1 TC and mobile-security flag |
| Provincial network | Three light regional guard formations | -1 dissent and territorial-network flag |

No action may create more than three new land commands. Grandfather all current
outcomes: six garrison-AA formations
(ind_v4_airfield_guard_battalions), four militia-AA formations
(ind_v4_mobile_airfield_security), and eight provincial militia
(ind_v4_provincial_airfield_guards), under ind_v4_airfield_security. Migration
never deletes or duplicates them.

Add a separate First Operational Air Group decision after Air Staff, Flying
Schools and Airfield Security:

| Air doctrine | Contract |
| --- | --- |
| Independent fighter command | Two interceptor or multirole wings |
| Army cooperation | One interceptor plus one tactical/CAS wing |
| Maritime patrol | One interceptor plus one naval bomber wing |
| Doctrine first | No immediate wing; one-time +1 air organization, then only paid wing contracts remain |

All aircraft are normal event-funded production contracts using the currently
researched model and normal daily IC cost. Initial tuning targets are
250-350 money, 900-1,350 supplies and 5-8 manpower according to package. Final
numbers require deterministic resource and five-year balance tests. For
build_division contracts, manpower is an eligibility/estimate only: normal
procurement already consumes manpower, so the event must not subtract it a
second time.

Set a one-use doctrine flag before granting organization. Reopening or closing
the persistent decision cannot repeat it. Count deployed, pooled and already
contracted aircraft before exposing the First Operational Air Group; a pooled
wing reports Awaiting Deployment and suppresses a duplicate package.

By 1 January 1935, a player who completed the prerequisite institutions must
either own a real air wing, have one under contract, or see the uncompleted
decision prominently in the readiness ledger.

### BAL-02: Gurkha progression

Treat Constitute the Gurkha Brigade (9281800) as Stage I and rewrite The Gurkha
Settlement (9270306) as Stage II: Expand the Gurkha Establishment.

For a new campaign, Stage II requires
ind_aubm_gurkha_rifles_commissioned. All Stage II formations use the dedicated
d_rsv_33 Gurkha Rifles family and all Stage II doctrine modifiers target that
family, not ordinary bergsjaeger. This preserves the special-unit gameplay and
visual identity without buffing unrelated mountain divisions.

Stage II identities:

| Choice | Immediate result | Long-term identity |
| --- | --- | --- |
| Field corps | Three brigaded field-ready d_rsv_33 Gurkha divisions | Immediate combat strength and a small +2 organization/+2 morale specialization |
| Regimental system | Two field-ready d_rsv_33 Gurkha divisions | Lower dissent, stronger Nepal relationship and +5 manpower with each annual trained class |
| Mountain school | One engineer-supported d_rsv_33 training cadre | +3 d_rsv_33 organization and morale, one leader/research callback, no instant corps |

Retain the present broad cost bands: field corps is highest in manpower and
supplies, regimental system is cheapest politically, and the school is cheapest
in manpower. The exact action labels must show unit count and five-year effect.

No option may dominate simultaneously on price, immediate divisions and
permanent doctrine. Map exact legacy Stage II flags
ind_v3_gurkha_corps_ready, ind_v3_gurkha_regimental_system or
ind_v3_gurkha_training_cadre plus ind_v3_gurkha_arm. A Stage II save without
Stage I is grandfathered as Stage-I-complete without spawning 9281800's
brigade, changing old bergsjaeger units, or granting doctrine a second time.

### BAL-03: Soft force ceilings

Never delete formations or prohibit manual construction. Event-granted forces
must instead expose a capacity alternative when India is already large:

- 80 or more deployed land divisions: doctrine, reinforcement, supply or
  leader development instead of another unavoidable land formation.
- 36 or more qualifying surface units: dockyard, repair or organization
  benefit instead of another unavoidable flotilla.
- 24 or more air wings: radar, doctrine or organization benefit instead of
  another unavoidable wing.

The alternative must be a real one-time choice, not an automatic conversion
hidden from the player. Every capacity alternative sets its own claimed flag
before granting a doctrine, supply or leader benefit. Late 1941/1942 fixtures
must shift from force accumulation toward operations.

### BAL-04: Generic decision cleanup

Exclude India from the stock or generic versions of:

- Create Public Works (9000021);
- Money Devaluation (9000023); and
- Wargames (9000033).

Their functions move to AUBM systems:

- public works through the Union Budget and national priorities;
- currency management through the currency settlement and budget;
- exercises through the disclosed peacetime map missions.

This removes decisions whose visible threshold, actual cost or random reward
conflicts with the bespoke Indian economy. Add the IND exclusion to both the
decision and automatic trigger paths; do not globally sleep/delete these event
IDs or erase already queued generic follow-ups in an upgraded save.

## 9. Strategy, Commitments and War Entry

### STR-01: Guided War Cabinet and unrestricted sandbox

The permanent State of the Union ledger replaces the Emergency War Cabinet as
the day-one doorway.

The curated War Cabinet becomes available when any of these is true:

- the year is 1937 or later;
- India is already at war;
- a recognized world-war crisis has opened; or
- the player explicitly enables Unrestricted Sandbox Campaigns.

The sandbox opt-in is free, permanent and clearly warns that it exposes
arbitrary early declarations and the full 210-tag index. It grants no reward
and does not bypass alliance or legal-target guards.

War Cabinet top level:

1. Strategic Alignment.
2. Campaign Operations.
3. Settlements and Occupations.
4. War Economy and Reserves.

The complete country catalogue remains under Campaign Operations -> Unrestricted
Targets. Curated play presents three to five authored plans first.

Each route retains its existing four identities:

- Allied: Eastern Ocean, Continental Expedition, Anti-Colonial Liberation,
  Sovereign Free Command.
- German: Eurasian Link, Imperial Dismantlement, Southern Resource Race,
  Sovereign Parallel War.
- Soviet: Anti-Fascist Expedition, Anti-Imperial Ocean War, Republican Asian
  Order, Autonomous Indian Socialism.
- Japanese: Indian Southern Sphere, Independent Soviet Campaign, Indian Ocean
  First, Equal Asian Command.
- Sovereign: Indian Ocean League, Continental Security Arc, World Balancer,
  Republican Federation.

### STR-02: Partner-entry crisis

A formal alliance inherits partner wars automatically under the Darkest Hour
engine. This must be disclosed before accession. When a formal ally enters a
new major war, India receives one consolidated wartime briefing, not an
impossible choice to remain outside.

When a separate-command compact or partnership enters a major war and India
remains outside it, fire one route-specific four-action crisis:

1. Upgrade to the formal alliance and inherit all partner wars.
2. Retain separate command and authorize the listed legal pairwise campaign
   declarations.
3. Give limited economic/intelligence support while staying outside the war.
4. Withdraw while at peace and begin the existing 90-day realignment cooldown.

A compact never forces entry. The pairwise action must name its targets and
recheck that none is a current partner; it cannot ambiguously become a formal
alliance.

The December 1941 Japanese fixture must receive this compact crisis once. It
opens focus selection but must not infer Indian Southern Sphere merely from
generic partnership/full-sphere history. Limited support keeps India out and
creates a real material/diplomatic cost. Withdrawal clears the entire Japanese
commitment family, treaty/proposal state and live route state, preserves
historical credit, and starts the cooldown.

Equivalent crises are required for Allied, German and Soviet commitments.
Sovereign India receives a world-war briefing offering an independent plan or
continued neutrality.

Neutrality must be active rather than empty. A sovereign player may select an
Armed Neutrality programme with objectives such as maintaining both ocean
approaches, guaranteeing selected neighbors, escorting trade and mediating a
regional crisis. Completing it grants sovereign standing but no free conquest
credit.

### Commitment rules retained and clarified

India may have exactly one binding family: Allied, German, Soviet, Japanese or
none. Compacts and formal alliances both occupy the lock.

- Same-family treaty upgrades remain possible.
- Rival conferences and stale delayed acceptances are blocked.
- Current compact and formal partners are invalid war targets.
- Withdrawal requires India to be at peace with no treaty proposal or reply,
  declaration, terms dispatch or armistice answer pending.
- Withdrawal enters sovereign command and a 90-day cooldown.
- Historical victories and conduct survive; current route state does not.
- During cooldown India may fight as sovereign but cannot bind itself again.

## 10. Campaign Operations and Objective Protection

### OPS-01: Campaign Operations Board

The board is reachable in one click from the War Cabinet and navigation has no
cost or cooldown.

Top-level pages:

1. Charter and Readiness.
2. Active Country Campaigns.
3. Southeast Asia Operations.
4. Return to War Cabinet.

It must show:

- command family;
- compact or formal alliance;
- separate versus shared wars;
- primary focus and its Planned, Active, Achieved or Abandoned state;
- every current Indian war and published objective;
- current settlement leverage;
- terms already in transit and opponent-specific retry state;
- mobilisation, reserve-pool and debt state;
- Southeast Asian summary.

Any exact current objective must be reachable in no more than three clicks.
Use triggered event variants for state reporting; do not put stale Alpha 20
formulae in a static ledger.

Southeast Asia uses a four-action submenu: Theatre Summary, Land Operations,
Sea Commands and Return. The Theatre Summary page links to Japan and Southern
Settlements while reserving its own action_d for Return. Country-campaign
pages use bounded regional pagination with Previous, Next, Details and Return.

### OPS-02: Primary charter focus lock

Lifecycle:

~~~text
Unselected -> Planned -> Active -> Achieved -> Campaign primary closed
                  |
                  -> Revised while at peace before activation

Active -> Abandoned only by peaceful route withdrawal
~~~

Rules:

- India has one primary focus and one route congress per campaign.
- Focus revision is locked whenever India is at war, even before activation.
- A focus becomes Active only when a published campaign brief capable of
  satisfying that focus opens.
- A matching named-country or flexible Southeast Asian result completes it.
- An unrelated victory grants secondary standing only.
- ind_aubm_global_campaign_victory cannot consume the primary slot.
- ind_aubm_route_war_achievement means only that the selected primary focus
  was completed.
- India Wins Beyond the Charter's Named Front remains useful secondary credit,
  but cannot open the route congress or block the selected focus.
- Congress entitlement records the route under which the focus was completed;
  later realignment cannot relabel it.
- After the primary focus and route congress are achieved, later realignment
  permits secondary country and theatre campaigns but no second primary focus
  or second route congress.
- Before primary achievement, a route switch may choose a new eligible focus.
  Only results earned after that focus activates can complete it. One-shot
  objectives already settled, annexed or historically exhausted are hidden;
  old history remains secondary standing.

The player may revise a planned focus once freely before activation. A later
prewar revision while India is fully at peace costs 250 money, 500 supplies and
2 dissent. There is no wartime revision.

## 11. Southeast Asian Campaign

Alpha 21's legal-owner, route-neutral and pairwise-settlement rules remain the
foundation. This pass changes pacing and presentation, not who legally owns or
may cede territory.

### SEA-01: Operations Board pages

Southeast Asia submenu:

1. Theatre Summary.
2. Land Operations.
3. Sea Commands.
4. Return to Campaign Operations.

Theatre Summary contains the link to Japan and Southern Settlements.

The summary distinguishes:

- no result;
- one land;
- one sea;
- one land plus one sea;
- two land without sea;
- two sea without land;
- two land plus one sea, qualified;
- one land plus two sea, qualified;
- theatre earned with current Japanese leverage;
- theatre earned without current Japanese leverage.

Each result reports one state:

- Not earned.
- Consolidating.
- Interrupted; restart pending.
- Historical credit, currently suspended.
- Historical credit, currently operational.

### Land categories retained

| Category | Published hubs or source |
| --- | --- |
| Indochina | Hanoi 1395 and Saigon 1399 |
| Philippines | Manila 1565 and Davao 1579 |
| Malaya | Kuala Lumpur 1438, Singapore 1432, or both where the legal campaign requires both |
| East Indies | Batavia 1647 or Jogjakarta 1654 through the correct legal campaign |
| Siam | Bangkok 1423 |
| Burma | Rangoon 1415 |
| Borneo | Bandar Seri Begawan 1625 or Kuching 1624 |

### Sea commands retained

| Command | Required ports | Ready surface fleet |
| --- | --- | ---: |
| Bay of Bengal | Rangoon 1415 and Port Blair 1421 | 8 |
| Malacca | Singapore 1432, Kuala Lumpur 1438, plus Palembang 1636 or Batavia 1647 | 12 |
| Java Sea | Batavia 1647 and Soerabaja 1653 | 16 |
| South China Sea | Singapore 1432 plus Saigon 1399 or Manila 1565 | 18 |

### First-time consolidation

Every result first attempted after the rework-version flag uses its own
published predicate and an interruption-safe consolidation state:

1. Initial conditions set a result-specific consolidating flag and schedule a
   30-day verification.
2. A periodic invalidation watcher sets an interruption flag immediately when
   that result's predicate fails. Recovery does not clear the interruption for
   the old attempt.
3. The day-30 verification requires no interruption and rechecks the result's
   published predicate.
4. Success sets permanent historical credit and current operational status.
5. Failure clears the attempt, pays no reward and permits a fresh attempt.
6. Recovery of an already earned result restores only current status.

Predicates are result-specific:

- direct land uses its opponent/legal-owner and Indian-control claim;
- friendly liberation uses occupation history, eligible friendly ownership and
  Indian participation;
- sea command uses its port chain, relevant war and fleet capacity.

A direct land category can qualify through either 30 uninterrupted days or
Delhi's lawful ratification/annexation settlement while the current direct
claim is still valid. This prevents a fast legitimate Batavia, Malaya or other
pairwise settlement from erasing the regional land credit. Friendly liberation
and sea command always require the full 30-day hold.

Alpha 21 achievements migrated into this version are grandfathered as
historical credit without a timer, command cost or repeated reward. Their
current/suspended state is revalidated against the live map; stale current
flags are not blindly preserved.

Sea-command establishment is an explicit player decision when requirements
are met. Initial tuning cost: 500 supplies and 250 oil. Only one new sea command
may be consolidating at a time. Text must say that the fleet threshold proves
national sustainable capacity, not the presence of those ships in a particular
sea zone.

### Friendly liberation

Friendly anti-Japanese liberation retains all Alpha 21 safeguards and adds the
same 30-day restored-control requirement:

1. India is at war with Japan.
2. Japan was previously observed holding the complete hub set.
3. The hubs return to India or an eligible friendly legal owner.
4. India controls a hub or has an Indian land division at a hub.
5. The restored state lasts 30 days.

It transfers no territory, opens no terms against the friendly owner and counts
once for its land category. Current Japanese Southern Armistice leverage may
depend on it.

### Theatre culmination

The flexible theatre result still requires:

- two different land categories plus one sea command; or
- one land category plus two different sea commands.

At culmination, all three historical components must exist and at least one
contributing land plus one contributing sea result must be currently
operational. When the historical formula exists without both live arms, the
board reports Components earned; culmination suspended. Recovery of one land
and one sea restores qualification without replaying component rewards.

Three land results alone do not qualify. Three sea commands alone do not
qualify. Multiple victories within Malaya, East Indies or Borneo remain one
category.

Batavia remains deliberately contextual:

- Batavia alone may support East Indies operational credit.
- Batavia may open the correct U05 or colonial-Netherlands convention.
- Direct administration still requires another legally owned center.
- Java Sea still requires Batavia, Soerabaja and sixteen surface ships.
- Tokyo's separate East Indies directive still requires Palembang, Batavia and
  Soerabaja.

The player never needs to color every Dutch East Indies victory province merely
to obtain a defensible local political result.

### Japan-specific paths retained

When fighting Japan:

- direct limited victory remains valid;
- flexible theatre history needs a current qualifying friendly liberation for
  the weaker Southern Armistice;
- decisive victory remains Okinawa 1563/1564 or Tokyo 1552 plus Osaka 1553;
- no friendly-owned territory transfers.

When cooperating with Japan:

- the six-point Southern Theatre Directive remains separate;
- current Malaya plus current East Indies or Australia remains required;
- flexible theatre credit may complete the Japanese charter focus but cannot
  replace the stricter Delhi-Tokyo treaty settlement.

## 12. Settlements, War Economy and Postwar Memory

### SET-01: Selectable settlement ambition

Every opponent with a defined settlement profile follows:

~~~text
Historical victory
  -> current leverage
  -> player selects terms
  -> foreign accept, counter or refuse
  -> Delhi ratifies
  -> pairwise peace only
~~~

Standard demands:

| Demand | Base response |
| --- | --- |
| Modest withdrawal or status quo | 75% accept / 20% counter / 5% refuse |
| Strategic settlement | 60% / 25% / 15% |
| Maximal political settlement | 40% / 35% / 25% |
| Continue the campaign | No dispatch; leverage retained |

Recognized standing may improve acceptance by up to 10 points. Remove up to
five from refusal, take the remainder from counter, floor both at zero, and add
exactly the amount removed to acceptance. Every final distribution must total
100. Exact odds and territorial/political consequences must be visible before
dispatch.

Japanese Southern Armistice:

- limited southern withdrawal: 60/30/10;
- Indian Ocean security settlement: 45/35/20;
- maximal southern terms: 25/40/35;
- decisive Japanese victory docket: 75/20/5.

Only opponent-owned positions currently controlled by India may transfer.
Foreign response events never execute peace. Delhi always confirms. One global
dispatch lock and opponent-specific locks prevent collisions.

Each demand tier needs an opponent-specific command mapping. Maximal terms do
not bypass Batavia's extra-centre rule for direct administration, Japan's
limited/decisive distinction, friendly-owner exclusions, legal ownership,
Indian control or annexation-only constitutional choices. Preserve and
deliberately map the Soviet, British Malaya, Batavia, great-power and generated
country dockets rather than applying one generic territorial package.

Opponent existence, pairwise war, legal ownership, Indian control and
friendly-owner exclusions are rechecked both at dispatch and immediately
before Delhi ratification. If legality changes in transit, the response lapses
without peace or transfer.

Refusal protection:

- First refusal: 60-day retry.
- A repeated same-or-softer offer against the same opponent in the same war
  receives up to +10 acceptance under the floor-safe calculation above.
- Second refusal: 90-day retry.
- On the third valid same-or-softer dispatch, refusal becomes zero and its
  former share moves to counteroffer.
- Loss of live leverage pauses retry.
- Harder terms do not inherit retry protection earned by softer terms.
- A decisive result supersedes a weaker cooldown or undispatched retry, but
  never mutates terms already in flight. Submitted terms resolve under their
  original tier or lapse if legality/leverage fails.
- Refusal memory clears on pairwise peace, annexation, opponent disappearance
  or a genuinely new war.

Annexation keeps four choices: restore sovereignty, establish protection, rule
directly, or defer. Record restoration, protection and direct-rule conduct in
tiered flags so later events can read the player's pattern.

### ECO-01: Exploit closure

#### Mobilisation

- Limited, full, emergency and route-specific mobilisation share one
  reserve-pool-drawn lock.
- Mobilisation sets active mobilisation and reserve-pool-drawn flags.
- Demobilisation clears only active mobilisation.
- The pool does not refill merely because a short war ended.
- Reconstitution requires 365 continuous days at peace plus 500 money and
  1,500 supplies; it grants no immediate manpower.
- Any new war resets the 365-day reconstitution timer.
- Pairwise peace cannot demobilize India while another Indian war continues.

Retained readiness costs 75 money and 300 supplies every 90 peacetime days.
Failure to pay ends readiness and adds 1 dissent. When war begins, peacetime
invoices stop and readiness converts to active mobilisation without another
manpower grant. Demobilisation is evaluated only when India has no remaining
wars.

#### War debt

- Wartime borrowing stops after the fourth recorded principal tier unless
  additional repayable tiers are implemented.
- No fifth unrecorded loan is available.
- Repayment and postwar penalties match the principal actually accumulated.
- Debt-register work is folded into the borrowing/repayment action rather than
  a standalone helper modal.
- A migrated save already beyond tier four maps to maximum recorded principal
  plus its existing overhang penalty and cannot borrow again.

#### Reward safety

- First completion sets permanent reward flags.
- Suspension clears only live eligibility.
- Recovery never repeats first-time rewards.
- Consolidation prevents province-touch farming.
- Migration may reconstruct live state but never replay rewards.

### MEM-01: Postwar persistence

Permanent history:

- named-country victories;
- land and sea operational achievements;
- flexible Southeast Asian theatre victory;
- completed primary charter and its route;
- settlement-conduct tiers;
- occupation obligations and debt.

Live and suspendable:

- current country claim;
- current land operation;
- current sea command;
- current friendly liberation;
- Japanese Southern Armistice eligibility.

Mutable/pending state that persists through save/reload until resolved:

- current commitment and treaty type, ending only through withdrawal, rupture,
  collapse or migration repair;
- opponent-specific refusal tier and retry cooldown;
- terms dispatch and submitted demand tier;
- consolidation attempt and interruption state.

Route congresses and later events must read both the completed charter and
conduct:

- anti-colonial focus plus direct-rule tiers creates a legitimacy crisis;
- a security sphere plus protected states creates access and recurring security
  cost;
- restoration-heavy conduct creates legitimacy and friendly cooperation;
- strategic autonomy alters at least Bandung, Suez, Goa, Tibet and UN choices.

Every new congress outcome flag must be consumed by at least two later events
and the final audit. Narrative-only setters are invalid.

## 13. Save Migration

Migration priority:

1. One unambiguous existing Alpha 21 commitment.
2. If none exists, one explicit legacy compact or war-command family.
3. If none exists, actual engine membership only when exactly one route patron
   can be identified.
4. Legacy orientation as historical context, not proof of a binding treaty.
5. Sovereign fallback.

Never infer a German commitment merely because India and Japan appear inside a
merged GER-JAP engine alliance. Preserve the unambiguous Japanese commitment.
If rival commitments coexist during war, preserve alliance/wars, quarantine
all route-changing decisions and defer the recovery choice until India is at
peace with no proposal, declaration, terms or dispatch state pending.

Migration must preserve:

- resources, dissent, manpower and modifiers;
- deployed and pooled units;
- production and research queues;
- owned and controlled provinces;
- wars, treaties and access;
- historical and current operational results;
- settlement and occupation records;
- unit type, model, name and brigades.

Sprite registry/type configuration is installation-local, not stored fully in
the save. Validate it separately through the sprite/install audit rather than
claiming save migration preserves the registry.

Rules:

- Conditional mappings execute first.
- The version-complete flag is set last.
- Running migration twice changes nothing.
- No migration action grants resources, units or victory rewards.
- All six-, four- and eight-formation Airfield Security outcomes and exact
  route flags are grandfathered.
- Only exact Gurkha Stage II flags map Stage II; Stage I alone leaves Stage II
  open.
- Completed 1934/1936 reviews and permanent union-choice flags are never
  recomputed, consumed or cleared.
- Alpha 21 commitment, SEA historical/current/suspended state, opponent retry
  state and armistice dispatch locks map without duplicate rewards. In
  particular preserve or safely reconstruct
  ind_aubm_japan_southern_armistice_inflight and
  ind_aubm_major_armistice_terms_dispatching.
- Existing mobilisation or demonstrable prior mobilisation sets the common
  reserve-pool-drawn lock.
- Current budget year closes conservatively and the new calendar begins next
  January.
- Fresh 1933 starts bypass every legacy migration path.

## 14. Tooling and Validation

Extend tools/analyze_v4_campaign.py with save, JSON and comparison modes. Report:

- date, route, commitment and wars;
- base IC and a clearly labelled derived effective-IC estimate reconciled
  against the engine display during human tests;
- IC allocated to production;
- total queue IC and funding ratio;
- resources;
- deployed and pooled land/naval/air forces, separating field/mobile land
  counters from garrison/security counters where supported;
- qualifying surface ships and transports;
- Airfield Security formations;
- open decisions;
- player-choice, automatic-notice and availability-notice cadence;
- duplicate notices and migration flags.

Funding classifications:

- READY: 0.90 or above.
- STRETCHED: 0.65-0.89.
- OVERCOMMITTED: below 0.65.

The August 1934 fixture must report OVERCOMMITTED without modifying its queue.

Add tools/validate_aubm_player_ux.py to verify:

- authored-event classification and deterministic command placement;
- State of the Union reachability;
- integration forecast/result equivalence for reviews not yet fired, plus
  preservation of already-recorded reviews;
- fixed annual budget;
- disclosed fallback dates;
- national-priority exclusivity;
- no duplicate Airfield/Gurkha rewards;
- soft force-ceiling alternatives;
- route focus protection;
- commitment crisis reachability;
- operations-board reachability;
- settlement odds and refusal progression;
- migration idempotence.

Validation is split by authority:

- Static source checks verify classifications, event IDs, guards, mutexes,
  generated budget years and disclosed requirements.
- Save-transform tests verify idempotence and semantic state invariance.
- Real-engine/human tests verify popup cadence, decision notifications, event
  ordering, UI reachability and unsupported dynamic triggers.

Any decision evaluator supports a documented trigger subset and returns
indeterminate for unsupported nested or dynamic predicates. It must not guess.
Telemetry classifies events by ID/manifest, not localized title text.

All migration fixtures are copied to a temporary test directory. Hash the
original before and after, and compare resources, units and pools, production,
research, provinces, wars, treaties and dispatch state semantically. Never
write a migration test into the user's original save.

Maintained production validators remain mandatory:

- validate_v4.py;
- validate_aubm_cold_start.py;
- validate_aubm_union_integration.py;
- validate_aubm_diplomatic_clarity.py;
- validate_aubm_global_campaigns.py;
- validate_aubm_route_consequences.py;
- validate_aubm_southeast_asia.py;
- validate_aubm_southern_settlements.py;
- validate_aubm_japan.py;
- validate_aubm_wartime.py;
- validate_aubm_units.py;
- sprite and art audits;
- complete deterministic build/release gate.

The standalone `validate_v3_legacy.py` harness is deprecated and is not a
production gate: its required `tools/v3_config.json` is absent. The
authoritative `validate_v4.py` pipeline loads and validates the retained V3
event modules together with V4, and Alpha 22's cold-start assertions live in
`validate_aubm_cold_start.py`. Reinstating a standalone legacy harness would
require a maintained configuration and parity tests; its filename alone is not
evidence that an event is safe.

## 15. Required Human Test Scenarios

### Test 1: Fresh 1933 cold start

- Play through 10 January.
- Exactly three mandatory pre-union AUBM choices: premise at scenario opening,
  cabinet during the opening 72 hours and union on 6 January.
- No migration/correction title.
- No one-button Union Register window; the integration state is available
  after the union choice.
- War Cabinet is unavailable before union and available afterward.
- Save/reload after every opening choice.
- Verify that selected cabinet and union identity appear correctly.

### Test 2: August 1934 sovereign fixture

- Preserve 117 provinces and the exact human queue/research.
- Preserve 60 land, three transports and zero air wings.
- Verify the Union Budget state and Gurkha affordability.
- Preserve the already-recorded fragile/mixed 1934 result and explain its
  future recovery; do not reroll it.
- Verify readiness warns about zero air and the overcommitted programme.
- Confirm no guard or Gurkha duplication.

### Test 3: Separate December 1934 branch

- Preserve the coercive/security identity.
- Confirm the State of the Union describes a different India.
- Preserve grandfathered guard units.
- Recognize the existing pooled air unit as Awaiting Deployment and suppress a
  duplicate First Operational Air Group.

### Test 4: December 1941 Japanese partnership

- Migrate to one Japanese commitment.
- Lock Allied, German and Soviet commitment.
- Fire one partner-war crisis.
- Test join, limited support and withdrawal on separate copies.
- Open focus selection; do not auto-select Southern Sphere from generic
  partnership history.
- Withdrawal applies sovereign command and the 90-day cooldown.
- In a separate formal-alliance copy, verify automatic inheritance of partner
  wars, one wartime briefing and no compact-style join/support crisis.

### Test 5: April 1942 sovereign India

- Preserve sovereign status and low manpower.
- No coalition is forced.
- Guided independent plans and unrestricted targets remain available.
- Soft ceilings prevent unavoidable force bloat.
- Southeast Asian land/sea play remains reachable.

### Test 6: Route exclusivity and focus protection

- Test Allied, German, Soviet, Japanese and sovereign primary focuses.
- Win an unrelated country campaign first.
- Verify secondary credit does not consume the primary focus.
- Complete the selected focus and verify congress entitlement.
- Switch only after peace, withdrawal and cooldown.
- Before primary achievement, verify historical credit survives a legitimate
  switch but only post-activation results can complete the replacement focus.
- After primary achievement, verify later routes offer secondary campaigns and
  no second primary focus/congress.

### Test 7: Southeast Asian combinations

- Malaya + East Indies + Malacca qualifies after consolidation.
- One land + two distinct sea commands qualifies.
- Three land or three sea results alone do not.
- Malaysia and Singapore remain one Malaya category.
- Batavia and Jogjakarta remain one East Indies category.
- First credit requires 30 days except the explicit direct-land
  lawful-ratification path.
- A day-15 interruption followed by recovery before the old day-30 endpoint
  fails that attempt and requires a new timer.
- A direct lawful country settlement ratified before day 30 still records its
  direct land category.
- A historical two-land/one-sea set with all live results suspended reports
  Components earned; culmination suspended until one land and one sea recover.
- Suspension/recovery pays no duplicate reward.
- Friendly liberation requires prior Japanese occupation and Indian
  participation.
- Theatre history alone cannot create Japanese Southern terms.
- No friendly-owned province transfers.
- Migrated Alpha 21 historical credit receives no timer, command cost or
  duplicate reward.

### Test 8: Settlements and economy

- Test modest, strategic, maximal and continue-war demands.
- Verify all odds before dispatch.
- Verify foreign acceptance waits for Delhi.
- Verify peace remains pairwise.
- Verify refusal progression cannot loop forever.
- Verify every modified probability distribution totals 100.
- Verify harder terms do not inherit softer-term retry protection.
- Verify a decisive victory replaces a cooldown but does not mutate an
  in-flight offer.
- Verify repeated short wars cannot farm mobilisation manpower.
- Verify readiness upkeep and debt ceilings.
- Verify migrated debt overhang and mobilisation-pool state.

### Test 9: Migration matrix

- Test all six-, four- and eight-formation Airfield Security variants.
- Test Gurkha Stage I only and every exact Stage II identity.
- Test Japanese commitment inside a merged GER-JAP engine alliance.
- Test rival commitments during war and recovery only after peace.
- Test old budget cooldown active, inactive and just expired at year end.
- Test SEA historical/current/suspended state and in-flight dispatch state.
- Hash and preserve every original fixture.

### Test 10: Real engine and save/reload

- Fresh 1933 engine smoke through the opening.
- Save/reload before and after a national-priority capstone.
- Save/reload before and after commitment crisis.
- Save/reload during SEA consolidation.
- Save/reload with a terms dispatch in flight.
- Run at least one complete human war, settlement, demobilisation and postwar
  congress before release.

## 16. Implementation Order

### Milestone 1: Visibility and cold-start safety

- **Implemented in Alpha 22 source:** UX-01 clean opening; fresh/upgrade-save
  separation foundation; Union Register folding; pre-union War Cabinet gate;
  focused cold-start validation; and adjacent-event safety fixes found during
  the audit.
- **Still required for full Milestone 1:** UX-02 State of the Union ledger;
  UX-03 global popup budget and consolidated migration review; UX-04 fixed
  annual budget; full POL-01 chapter outcomes; complete idempotent MIG-01
  migration; and the remaining QA-01 popup/save instrumentation.

Release gate for the Alpha 22 subset: deterministic build, local deployment and
fresh 1933 smoke through the opening have passed, including no Compatibility
Review in the 1 February autosave. A copied-upgrade-save engine test for state
preservation and no resource regrant remains pending.

Release gate for the complete milestone: fresh 1933 opening, August 1934
migration and no state loss.

### Milestone 2: Peacetime agency and force identity

- POL-02.
- OBJ-01 and OBJ-02.
- BAL-01 through BAL-04.
- Save analyzer expansion.

Release gate: both 1934 branches feel different, real air-force path works,
Gurkha choices are non-dominant, and old units remain untouched.

### Milestone 3: Guided war and Southeast Asia

- STR-01 and STR-02.
- OPS-01 and OPS-02.
- SEA-01.

Release gate: all five routes, Japanese partnership fixture, focus protection
and full SEA combination matrix.

### Milestone 4: Settlements and persistent consequences

- SET-01.
- ECO-01.
- MEM-01.

Release gate: complete human war-to-postwar run with pairwise settlements,
demobilisation, congress callbacks and no exploit or duplicate reward.

## 17. Definition of Done

The rework is complete only when:

- the opening feels like governing India rather than migrating a database;
- a 1934 player can name the next objective and understand the force gap;
- foundational choices visibly return in later events;
- a partner entering war produces an unmistakable human decision;
- every route provides a guided campaign while preserving full sandbox freedom;
- Southeast Asia rewards operational hubs, sustained control and mixed land/sea
  power rather than exhaustive province coloring;
- the selected charter focus cannot be stolen by an unrelated victory;
- settlement demands are chosen, disclosed and pairwise;
- postwar events remember both India's route and its conduct;
- supported saves lose no player-owned state and receive no duplicate reward;
- static validators, deterministic build, engine smoke and a full human
  wartime/postwar playthrough all pass.
