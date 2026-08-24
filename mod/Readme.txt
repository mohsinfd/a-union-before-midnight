=======================================================================
 A UNION BEFORE MIDNIGHT - V4.2.0 ALPHA 19
 For Darkest Hour 1.05.2
=======================================================================

Freedom came early. Unity came at a price.

A Union Before Midnight is an independent-India alternate-history campaign
beginning on 1 January 1933. India inherits a united but unsettled continental
state from Ceylon to Burma and must build a working federation, modern economy
and credible armed forces before the world crisis reaches Asia.

Alpha 19 passes the automated release gates and a fresh 1933 executable smoke
test. It remains an alpha playtest build pending a complete wartime and postwar
campaign.

-----------------------------------------------------------------------
 PLAYER REQUIREMENTS
-----------------------------------------------------------------------

- Darkest Hour 1.05.2.
- Darkest Hour Full, included with the game.
- A fresh 1933 campaign.

Blood and Iron is not a runtime foundation and is not required to play an
already built local installation. The developer-only personal sprite rebuild
does use a locally installed Blood and Iron v1.1 as a donor and records every
source hash. Those donor graphics are not cleared for redistribution.

-----------------------------------------------------------------------
 INSTALLATION
-----------------------------------------------------------------------

1. Install Darkest Hour 1.05.2.
2. Run INSTALL.bat from the A Union Before Midnight source/release folder.
3. Select "A Union Before Midnight V4.2" in the launcher.
4. Start "A Union Before Midnight: India 1933".

The installer creates or updates an isolated copy of Darkest Hour Full, checks
every overlay hash before and after copying, removes stale managed files, and
preserves existing save files. It does not modify Darkest Hour Full itself.

For a non-standard Steam library, run the PowerShell installer with -GameRoot.

-----------------------------------------------------------------------
 THE ALPHA 18 GAMEPLAY REWORK (RETAINED IN ALPHA 19)
-----------------------------------------------------------------------

Alpha 19 fixes the unsupported foreign-country event scopes that caused Alpha
18 to abort while loading the 1933 scenario. The validator now rejects that
syntax before deployment.

Earlier builds could let India capture Persia, Suez, Singapore or the East
Indies without meaningful feedback until the entire world war ended. Old route
flags could also disagree with India's actual alliances and wars. Alpha 18
replaced that overlap with one state-driven War Cabinet and one common campaign
contract.

The new rules are:

1. Actual alliances, wars, control and ownership outrank old policy flags.
2. Every supported war publishes an Indian-controlled objective.
3. Capturing it produces immediate theatre feedback and a live settlement.
4. Losing it suspends the claim; recovering it restores the same file.
5. Each opponent accepts, counters or refuses separately.
6. Delhi ratifies only that pairwise peace; India's other wars continue.
7. Annexation opens a sovereign, protected or direct-rule settlement.
8. A completed campaign earns route standing and a Delhi peace congress.

One refusal cannot block another country. If a government vanishes while its
answer is in transit, the dead reply lock is removed and the campaign can reopen
if that country later returns.

-----------------------------------------------------------------------
 STRATEGIC COMMAND
-----------------------------------------------------------------------

The permanent War Cabinet supports five command universes:

- Allied: join Britain or the United States, or retain separate command.
- German: join Berlin or cooperate as an independent co-belligerent.
- Soviet: join Moscow, negotiate a compact, or pursue autonomous socialism.
- Japanese: form an engine alliance or a separate Delhi-Tokyo compact.
- Sovereign: fight country-by-country without a permanent patron.

A formal alliance merges every current war because that is Darkest Hour engine
behavior. A compact preserves separate declarations and peace authority. India
can change sides through a guarded transfer, attack a former partner, or return
to sovereign command without losing verified battlefield credit.

Each route has four wartime doctrines and its own postwar Delhi congress. The
final settlement can establish a concert of sovereign partners, an Indian
security sphere, or renewed strategic autonomy.

-----------------------------------------------------------------------
 CAMPAIGN COVERAGE AND PEACE
-----------------------------------------------------------------------

India has 236 practical country-specific campaigns:

- 5 bespoke great powers: Britain, Germany, Soviet Union, Japan and USA.
- 21 bespoke regional opponents across Asia, Europe, Africa and Oceania.
- 210 generated campaigns for other loaded and later-created sovereign tags.

The common generated terms are 60 percent acceptance, 25 percent counteroffer
and 15 percent refusal. Earned coalition, sovereign or great-power standing can
improve them to 75/20/5. Bespoke negotiations disclose their own actual odds.

After annexation India must choose:

- restore a sovereign government and seek access or partnership;
- establish a protected government at a political cost;
- retain direct rule with dissent, belligerence and annual upkeep; or
- defer the constitutional decision for a limited period.

-----------------------------------------------------------------------
 JAPANESE PARTNERSHIP
-----------------------------------------------------------------------

The Delhi-Tokyo route now distinguishes a formal alliance from a strategic
compact. Under the compact India can lead the southern campaign while Japan
handles China, the Philippines and the Pacific, and India can open an
independent Soviet war without automatically involving Japan.

The southern ledger tracks:

- Rangoon, Imphal and Port Blair for the Burma-Andaman approach.
- Singapore and Kuala Lumpur for Malaya.
- Palembang, Batavia and Soerabaja for the East Indies.
- Darwin, Canberra and Sydney for Australia.

Japanese occupation inside India's agreed theatre can transfer to Indian
control while legal ownership waits for peace. India can settle Malaya,
Indonesia and Australia before the entire Pacific war ends.

Tibet is not transferred automatically. A victorious partnership improves the
terms only after India fights a real Tibetan campaign, controls the verified
objective and completes the constitutional settlement.

The earlier second-proposal deadlock is repaired, influence accounting is
corrected, and a pro-Japanese India no longer receives anti-Japanese criticism
unless it actually fights Japan.

-----------------------------------------------------------------------
 WAR FINANCE, MOBILISATION AND OCCUPATION
-----------------------------------------------------------------------

The peacetime Union Budget begins in 1934. Permanent revenue grows through the
Revenue Service, the 1937 Federal Income Tax Settlement and, from 1940 during an
Indian or global war, the National War Finance Board. Taxation, borrowing and
foreign credit carry visible political or debt costs.

Whenever India is at war without an active account, a War Finance Act opens
with bonds, taxation, external credit or ordinary revenue. Borrowing advances a
cumulative four-tier debt register. A negative treasury can use guarded
emergency credit. At the next wartime-account review after peace, India must
choose redemption, annual service or politically costly repudiation.

India receives one annual trained reserve class from 1934 through 1964. War
also opens limited service, national service or a technical reserve. Further
low-manpower call-ups cost supplies and dissent, and peace opens a real choice
between demobilisation and retained readiness.

Every new direct mandate advances an occupation register. Annual costs scale
with the number of retained administrations. Civilianisation can reduce a high
tier, but direct rule keeps an irreducible tier-one burden until sovereignty
actually changes.

-----------------------------------------------------------------------
 ARMED FORCES AND RESEARCH
-----------------------------------------------------------------------

- 31 additional real Indian and subcontinental officers.
- At least 80 active land leaders in 1938 and 90 in 1940.
- Restored commando leaders for Gurkha, INA, airborne and frontier forces.
- Eight special-unit families with 42 research-linked equipment models.
- Distinct Gurkha, Frontier, Chindit, Airborne, Marine, Pioneer and Guards roles.
- Arabian Sea Fleet: 1 BB, 2 CL and 2 DD.
- Bay of Bengal Fleet: 1 BB, 2 CL and 2 DD.
- Every Indian Ocean programme has a CV, 2 CVL or BC capital core.
- New hulls receive the mature 50-percent model-zero time standard at normal
  daily IC cost; ships already queued keep their saved completion dates.
- Illegal unit and brigade combinations have been removed.
- 31 Indian technology teams and a complete Raj-level research inheritance.
- Air and naval combat favors organization loss and withdrawal over routine
  annihilation, although bad engagements can still destroy units.

Public installations use Darkest Hour Full sprites and ordinary model panels.
Reserved special-unit models currently use the engine's missing-art placeholder
pending original panels. The 41-family animated India sprite rebuild is a
developer-only local option; its donor-derived descriptors, strips, palettes
and panels are excluded from public manifests.

-----------------------------------------------------------------------
 DECISION INFORMATION
-----------------------------------------------------------------------

Major choices disclose money, supplies, manpower, dissent and foreign response
odds before commitment. A decision remains selectable when at least one full
action is affordable; every action keeps its own complete resource gate, while
the description discloses the costs of unavailable alternatives.

Strategic orientation, treaty, formal alliance and declaration of war are
separate steps. Choosing a domestic Gandhi-Nehru government does not by itself
forbid a Japanese, Allied, German, Soviet or sovereign foreign-policy route.

-----------------------------------------------------------------------
 COMPATIBILITY AND TESTING STATUS
-----------------------------------------------------------------------

Start a new 1933 campaign. V3 saves are unsupported, and earlier V4 alpha saves
do not contain the complete Alpha 19 route, economy and campaign state. The
expanded leader roster and scenario research are serialized at game start.

Verified for this build:

- Full static validation: 0 errors and 0 warnings.
- Every file in the active installed manifest: 0 missing and 0 hash mismatches.
- 28,175 every-country checks across 210 generated countries.
- 1,434 canonical wartime checks.
- 595 five-route consequence checks.
- 3,620 special-unit checks and 431 diplomatic-disclosure checks.
- Japan, art, sprites, economy, resources, campaign, combat, construction-cap
  and Steam Deck gates passed.
- Fresh 1933 scenario executable smoke: passed.

Still required:

- A no-cheat 1940/1942 force and economy measurement.
- Real coalition, side-switch, partner-collapse and separate-peace testing.
- At least one complete armistice, annexation, occupation and Delhi-congress run.

The executable still allows only one leader per formation and cannot
automatically find and rebase every threatened air wing. Players must order
aircraft away from an endangered base. An event can also attach only one module
directly to an ordered ship; other legal modules enter the deployment pool.

For a bug report, include the exact campaign date and route, whether the fault
repeats from the same save, the last 100 lines of savedebug.txt, the relevant
save when practical, and any manual edits or other overlays.

-----------------------------------------------------------------------
 CREDITS AND RIGHTS
-----------------------------------------------------------------------

Design and India-specific content:
Mohsin Dingankar, developed with Codex collaboration.

Gameplay is rebased directly on Darkest Hour Full. Public manifests exclude
copied foundation/donor map assets, donor-derived sprites and palettes,
donor-derived model panels and unresolved art. Developer-only local
reconstructions remain subject to their original rights and must not be
redistributed.

This is a non-commercial fan modification. Darkest Hour and Hearts of Iron are
trademarks of their respective owners. See RIGHTS.md and the art/research
credits in the source package before redistribution.

The complete source-side gameplay guide is GAMEPLAY_CHANGES.md.
