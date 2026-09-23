# 27-ROSTER1: people worth choosing

ROSTER1 includes the installed BALANCE1 changes. It is for a **new 1933 game**,
not an existing-save migration. The actual Steam target remains **AUBM Terrain
Prototype P1**. Look for **PLAY 27-ROSTER1** on the menu and **27-ROSTER1** in
the 1933 scenario title and first Indian event. Background art is unchanged.

Installed on 13 September 2026 with an 11-file backup. **46 regression tests
pass**; the registered 8,902-event set is unchanged and validation reports no
errors. All 29 save-folder files were unchanged during installation. The live
installation has its own `AUBM_ROSTER1_INSTALL_RECEIPT.json`; the preceding
BALANCE1 receipt is preserved. No native game launch was performed.

## What was wrong

The minister file contained 111 records. Many were ideological copies of the
same person in the same job: Katari, Cariappa, Mukerjee, Ambedkar and others had
several entries with the same effects. Earlier cabinet scripts appointed those
different IDs. They provided compatibility, not real political competition.

The research complaint was also measurable. In a component-match audit of the
installed 1933–47 technology tree:

- Mukerjee was a best fit for **all 47 air-doctrine applications** checked.
- Quetta was a best fit for **43 of 51 land-doctrine applications**.
- The combined ship-design board led **31 of 36 naval hardware applications**.
- Tata's broad aircraft team led **39 of 42 aircraft applications**.

These are weighted component matches with skill as a tie-breaker, not predicted
research days. Only the Indian CSV roster is compared, not foreign loaned or
captured teams. Ties are counted for every matching team. Exact in-game speed
also depends on blueprints, dates, policy, ministers and other modifiers.

India already has **512 commanders**, including 375 fictional reserve entries.
The issue here was identity and differentiation, not another shortage of IDs.

## Cabinet competition

**34 redundant same-person/same-office records are consolidated. Seven distinct
candidates are added, leaving 84 minister records.** The same person may still
appear in different offices; those are separate, intentional appointments.

All **45 affected minister references in five registered event files** now point
to retained IDs. Team and commander IDs are deliberately not remapped, even when
their numbers happen to match minister numbers. No new cabinet decision loop,
party flag or election event is added. Existing full-cabinet choices remain.

Native ideology and start-year eligibility still apply. This patch does not
make every minister selectable under every political system. Heads of state
and government still follow the game's appointment/election rules; the new
procurement, security and military candidates are ordinary departmental choices.

### Navy

| Candidate | Why choose them? | Cost of that emphasis |
|---|---|---|
| Katari | Carrier/light-carrier organisation +5%, naval-bomber morale +4%, fleet research time -3%, detection +5%. | Battleships take 3% longer. His former broad shipbuilding discounts are removed. |
| Soman | Battleship, battlecruiser and heavy-cruiser attack +5%. | Carriers take 4% longer. |
| Choudri, from 1933 | Destroyer organisation +5%, detection +6%, transport/convoy-transport cost -5%. | Battleships take 4% longer. |
| Ahsan, from 1936 | Submarine attack +6% and organisation +4%. | Carriers take 4% longer. |

The BALANCE1 yard standard remains 25% peace/40% war before other applicable
modifiers. This pass does not add another universal naval construction discount.

### Army and air

- **Cariappa:** retains his existing broad army-reform profile.
- **Thimayya:** mobile columns—tank organisation and motorised/mechanised morale;
  infantry construction is slightly slower.
- **Shrinagesh:** frontier service—mountain/marine organisation and cheaper engineer
  brigades; tank construction is slightly slower. He also replaces the old
  Rajendra Prasad chief-of-staff entry, with the existing defensive-school role.
- **Mukerjee:** air-defence institutions—air doctrine and fighter organisation.
  His old broad aircraft/naval/research bundle is narrowed; strategic bombers
  receive less procurement priority.
- **Aspy Engineer, available from 1933:** maritime aviation—naval-bomber attack
  and organisation, plus carrier organisation; slower strategic bombers.
- **Mehar Singh:** army air support—close-support attack, tactical-bomber morale
  and air-transport organisation; slower interceptor procurement.
- **Darshan Singh:** long-range bomber organisation/morale and a small aircraft
  research benefit; slower interceptors.
- **Karun Krishna Majumdar, from 1936:** another politically distinct army-air
  candidate, using his existing named portrait.

These are alternate-campaign gameplay roles, not claims that the historical
people actually held these appointments in 1933.

### Civilian departments

- **Chhotu Ram:** resource-first armaments. Energy +10%, metal/rares +8%, oil +5%,
  but factory output -2%. A genuine alternative to more factory demand.
- **Rajagopalachari:** frugal procurement. Civilian demand and upgrade cost -4%,
  money +5%, but factory construction takes 3% longer.
- **Kidwai:** district organisation. National manpower growth +6% and supplies
  +4%, at a 3% money penalty.
- **Kania:** civil liberties. Lower civilian demand and dissent, better money
  output, but a smaller domestic intelligence network.
- **Ambedkar:** retains the distinct existing rights/participation profile.
- Hitendra Desai's armaments availability moves to 1935; Homi Bhabha's technical
  intelligence entry to 1936. These are deliberate alternate-campaign timings.

Nehru, Patel, Bose, the development engineer and scientific-planning alternatives
remain. This is not a universal minister-skill buff or a hidden IC grant.

## Commanders with clearer identities

The roster stays at **512**. **43 named officers** receive focused trait
profiles. Rank dates, initial/max skill, experience, availability and portraits
stay unchanged. Highlight examples:

| Commander | Gameplay role |
|---|---|
| Cariappa | Logistics, defence and disciplined holding actions. |
| Thimayya | Offensive mountain/commando operations. |
| Manekshaw | Deception, logistics and elastic defence. |
| J. N. Chaudhuri | Armour, offensive doctrine and encirclement. |
| Harbaksh Singh | Defence and counterattacks. |
| Bhagat | Engineers, offensive operations and logistics. |
| Aurora | Engineers, jungle campaigning and logistics. |
| Jacob | Fortifications, urban fighting and deception. |
| Sagat Singh | Commandos, jungle fighting and breakthroughs. |
| Rajinder Singh Sparrow | Armour and breakthroughs. |
| Nanda | Surface tactics and blockade-running. |
| Ahsan | Submarine operations and spotting. |
| Arjan Singh | Fighter tactics and spotting. |
| Aspy Engineer | Naval bombing and spotting. |
| Majumdar | Ground attack and night operations. |
| P. C. Lal | Strategic bombing and spotting. |

Profiles use documented branch-appropriate traits, with at most three per
spotlighted officer. They are not “good at everything” stacks. Commando traits
still have their normal disadvantages when used with ordinary troops.

The **375 fictional reserves** now have individual given names instead of
repeating “A. A.”-style initials. The **(R)** suffix remains, distinguishing this
fictional expansion from named historical entries. Their stats and portraits
are not buffed or regenerated. Existing mod and base-game portraits are reused;
this patch does not claim to add newly sourced photographs.

## Research: choose a specialist for the programme

There are **35 teams**, up from 31: 22 existing profiles are revised and four
specific missing roles are added. No new global research modifier is granted.
Revised teams have at most seven specialties and skill at most eight; the
existing later skill-nine fundamental-research institution is unchanged.

### Land

| Research programme | First teams to compare |
|---|---|
| Centralised staff work and mass-army doctrine | Cariappa General Staff |
| Mobile warfare, manoeuvre and armoured doctrine | Thimayya Mobile Warfare School |
| Decentralised infantry and frontier doctrine | Quetta-Delhi Frontier Staff College |
| Field exercises, infantry equipment and practical training | Messervy's Field Exercises Board, now available from 1933 |
| Tank and vehicle hardware | Armoured Vehicle Development School |
| Guns, munitions and equipment | Indian Ordnance Factories; Bhatnagar Applied Science |
| Mountain troops | Quetta-Delhi; Military Engineer Services for relevant equipment components |
| Marines and amphibious operations | Cochin Landing Warfare School, from 1934 |
| Airborne training | Army-Air Cooperation School |
| Medicine and field health | Bengal Chemical and Army Medical Service |

### Navy

| Research programme | First teams to compare |
|---|---|
| Surface ships and gunnery | Mazagon Surface Ship Bureau |
| Escorts, submarine hardware and machinery | Garden Reach Escort and Submarine Works |
| Carrier hardware | Indian Carrier Design Board |
| Surface fleet doctrine | Monsoon Surface Fleet Staff |
| Carrier doctrine and naval-air coordination | Aspy Engineer's Carrier Warfare School |
| Submarine and small-force doctrine | Visakhapatnam Undersea Warfare School |
| Fleet operations and logistics | Katari's Ocean Operations Staff |
| Maritime electronics and replenishment components | Bose Maritime Signals Centre |
| Landing doctrine and marine development | Cochin Landing Warfare School |

### Air

| Research programme | First teams to compare |
|---|---|
| Fighter design | Walchand's Fighter Design Bureau |
| Transports, support aircraft and civil-derived bombers | Tata Transport and Bomber Works |
| Armed bombers, naval aircraft and carrier air groups | Aircraft Armament Trials Unit, from 1934 |
| Advanced aeronautics and rockets | Ghatage Aeronautical Laboratory |
| Centralised fighter control | Mukerjee Air Defence Staff |
| Fighter training and dispersed operations | No. 1 Squadron Fighter School |
| Tactical air support and airborne work | Army-Air Cooperation School, from 1933 |
| Strategic/night-bomber doctrine | Long-Range Air Navigation School, from 1936 |

IACS becomes a useful fuel/chemical research laboratory instead of being a
weaker copy of Bhabha's nuclear group. Ordnance receives training coverage so
it can genuinely compete with the broad applied-science team. Railways, Tata
Steel, IISc, the Planning Board, atomic research and later rocket institutions
retain their own productive niches.

The resulting weighted-match audit finds **at least one leading job for every
team** among 369 applications dated 1933–47. This does not mean all 35 should
be used in every campaign: some technology paths exclude others, and a carrier
campaign naturally uses different specialists from a submarine campaign.
Availability, event unlocks and occupied research slots still matter.

## Verification, installation and limits

The implementation adds **no new events** and changes no peace/alliance logic,
unit definitions, country colours, terrain or savegames. The release consists of
11 changed files on the installed BALANCE1 baseline. Regression checks cover
duplicate removal, all affected minister references, separate ID namespaces,
trait validity, unchanged leader strengths, preserved research specialties,
specific technology/team matches, and version labels.

`python tools/build_roster1.py` stages and validates;
`python tools/build_roster1.py --install` applies the hash-guarded delta while
the game is closed. Immutable inputs, research comparisons, validation and
backups are under `build/roster1`. The install receipt lists exact hashes and
the backup directory; it does not overwrite the preceding BALANCE1 receipt.

Run the roster and BALANCE1 tests from `tools` with:

```text
python -m unittest test_aubm_roster1 test_aubm_balance1_economy test_aubm_balance1_playtest test_aubm_balance1_world_ai test_build_balance1
```

This is static/regression validation, **not an in-engine playtest**. No game
has been launched or advanced by this work. Actual cabinet eligibility,
research durations and tooltip rendering still need normal native playtesting.
Start a new 1933 campaign after installation; an old save keeps much of its own
roster state and is not a valid test of these changes.
