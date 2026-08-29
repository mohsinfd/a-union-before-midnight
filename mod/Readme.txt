=======================================================================
 A UNION BEFORE MIDNIGHT - V4.2.0 ALPHA 21 - 29 AUG 2026
 For Darkest Hour 1.05.2
 Source version 4.2.0-alpha.21
=======================================================================

Freedom came early. Unity came at a price.

A Union Before Midnight is an independent-India alternate-history campaign
beginning on 1 January 1933. India inherits a united but unsettled continental
state from Ceylon to Burma and must build a working federation, modern economy
and credible armed forces before the world crisis reaches Asia.

The exact personal 41-family India sprite profile has been restored in the
developer's local installation after the previous public deployment. It remains
local-only: donor-derived sprites, palettes and model panels are excluded from
Git and do not ship in the public installer.

Alpha 21 makes the flexible Southeast Asian theatre available under every
Indian route, adds proof-based friendly liberation and a weaker optional
Japanese Southern Armistice, and prevents live or legacy alliance logic from
relabeling a current rival commitment. It remains an alpha playtest build.

-----------------------------------------------------------------------
 PLAYER REQUIREMENTS
-----------------------------------------------------------------------

- Darkest Hour 1.05.2.
- Darkest Hour Full, included with the game.
- A fresh 1933 campaign.

Blood and Iron is not a runtime foundation and is not required to play an
already built local installation. The exact personal sprite profile uses a
locally installed Blood and Iron v1.1 as a donor and records every source hash.
Those donor graphics are local-only and are not cleared for redistribution.

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
 THE ALPHA 21 GAMEPLAY PASS
-----------------------------------------------------------------------

Alpha 19 fixed the unsupported foreign-country event scopes that caused Alpha
18 to abort while loading the 1933 scenario. Alpha 20 retained that validator,
made binding commitments exclusive and added local Batavia, Dutch-colonial and
Malaya dockets plus the first flexible Southeast Asian ledger. Alpha 21 keeps
that history and extends the system rather than replacing it.

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

Alpha 21 applies the complete Southeast Asian theatre to relevant Allied,
German, Soviet, Japanese and sovereign wartime focuses. Four anti-Japanese
friendly-owner liberation chains cover Indochina, the Philippines, Malaya and
Batavia. Each requires recorded Japanese occupation, friendly restoration and
direct Indian control or an Indian land garrison at a published hub.

Eligible liberation credit can satisfy Malacca and South China Sea lane hinges
where the engine returns territory to a friendly legal owner. Java Sea remains
stricter: Batavia and Soerabaja plus sixteen ready surface combatants are still
required. The full theatre needs two different land categories plus one sea
lane, or one land category plus two different lanes. It grants no province and
executes no automatic peace.

The full rules and examples are in docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md.

The 1934 integration review also recognizes the mixed legitimacy-and-capacity
state when no provincial bargain was recorded. That state can no longer stall
the whole constitutional chain.

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
can hold only one binding coalition or compact. Rival alignment events remain
closed until India withdraws while at peace and completes a 90-day sovereign
reset. A compact may still be upgraded within its own family. Coalition
partners cannot be selected as War Cabinet targets.

Alpha 21 repeats this rule in every live-state synchronizer and every direct or
retired legacy entry action. A Berlin-Tokyo faction merger cannot relabel a
current Japanese commitment as German, and missing relationship markers cannot
silently erase a commitment. This is not a lifetime lock: an explicit at-peace
withdrawal still starts the 90-day realignment and then permits a new family.

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
 SOUTHEAST ASIA OPERATIONS
-----------------------------------------------------------------------

- Batavia (1647) opens a local U05 settlement without the national Southern
  route. If the Netherlands legally owns the colony, it uses a separate HOL
  colonial response instead of requiring Amsterdam.
- Singapore (1432) and Kuala Lumpur (1438) open a Malaya-only British
  settlement without requiring Borneo or the whole British campaign.
- East Indies cessions include western New Guinea provinces 1594-1601 only
  when the defeated U05 or HOL government legally owns them. Third-party land
  is never taken.
- Hanoi (1395) plus Saigon (1399), and Manila (1565) plus Davao (1579), record
  standalone Indian land victories without adding another peace docket.
- Bay of Bengal, Malacca, Java Sea and South China Sea achievements require the
  named ports plus 8, 12, 16 and 18 surface ships respectively. Transports and
  submarines do not count.
- Every local claim suspends when its ports, live war or legal-owner condition
  is lost, recovers when the published conditions return and pays its material
  reward only once. Naval milestones transfer no territory.
- The flexible theatre result is accepted by Allied Eastern Ocean and
  anti-colonial focuses; German anti-imperial and southern-resource focuses;
  Soviet ocean-war and republican-Asia focuses; Japan's Indian Southern Sphere;
  and the sovereign Indian Ocean League.
- Friendly liberation of Indochina, the Philippines, Malaya or Batavia counts
  only after Japan first occupied the complete hubs and an Indian land unit or
  direct Indian control proves participation when the friendly owner returns.
- Friendly Malaya, Batavia, Indochina and Philippine credit can operate the
  appropriate Malacca or South China Sea hinges. Batavia liberation alone does
  not satisfy Java Sea Command.
- The flexible theatre requires either two different land categories and one
  sea lane, or one land category and two different lanes. Three results from
  only one arm do not qualify.
- Liberation and lane awards make no peace and transfer no land. Every local
  settlement remains pairwise and legal-owner-only.

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

The optional weaker Southern Armistice has a live Japan-specific gate. India
must still be at war with Japan and have either the current recoverable direct
limited-victory claim, or the permanent flexible-theatre record backed by at
least one currently active anti-Japanese friendly liberation. Old route-neutral
theatre history alone cannot be carried through a route switch into free terms;
loss of all current leverage suspends eligibility until recovery. Decisive
victory uses the normal great-power armistice board instead of this weaker path.

Japan answers at 45 percent acceptance, 35 percent counteroffer and 20 percent
refusal. Southern in-flight state plus a shared great-power terms-dispatch lock
prevents initial, retry and cross-opponent dockets racing into duplicate or
disabled popups; a decisive victory reached during cooldown returns the retry
to the normal board. Acceptance or counteroffer ends only the India-Japan war.
After refusal, Japan's docket waits 90 days and reopens only if the live gate
still holds; otherwise it waits for leverage to recover. Transfers require
Japanese legal ownership and Indian control; friendly-owner British, Malaysian,
Singaporean, U05, Dutch or Indonesian land is never taken.

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
The developer's exact 41-family animated India profile is restored locally
after the previous public deployment, including its distinct specialist-family
keys. Its donor-derived descriptors, strips, palettes and panels remain outside
Git and public manifests and must not be redistributed.

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

Start a new 1933 campaign for the intended Alpha 21 test. V3 saves are
unsupported, and earlier V4 alpha saves do not contain the complete liberation,
lane, armistice, economy and campaign state. The expanded leader roster and
scenario research are serialized at game start.

The newest reviewed file, the 28 Aug autosave, is only a fresh 1934 campaign.
The 23 Aug manual save has India non-aligned and not at war. Neither validates
the new wartime behavior.

The final Alpha 21 acceptance run on 29 Aug 2026 passed:

- 40,357 every-country checks across 210 generated countries.
- 1,860 canonical wartime checks.
- 668 five-route consequence checks.
- 2,957 special-unit checks and 431 diplomatic-disclosure checks.
- 305 southern-settlement checks, 25 union-integration checks and the 21-event
  Southeast Asia operations contract with four liberation chains and four
  fleet-backed lanes.
- Japan partnership and unsupported launch-syntax regression gates passed.
- Deterministic repeat-build, full static, art, economy, resource, campaign,
  combat, construction-cap and Steam Deck gates passed.
- Public installer manifest: 342 managed files; copied foundation, donor and
  unresolved assets excluded.
- Installed public payload: 342/342 files verified.
- Fresh fullscreen 1933 India campaign reached the playable map with 0 logged
  errors, no new crash dump and all 27 existing saves unchanged; province
  validation ended with "No errors found."
- Local-only personal visuals: 41 unique families, 591 descriptors, 553 bitmap
  strips, 44 palettes and 820 model graphics verified after deployment with 0
  missing files or hash mismatches.

These checks verify the build, parser, installer and initial launch. They do
not replace a complete human wartime and postwar playthrough.

Still required:

- A no-cheat 1940/1942 force and economy measurement.
- Real commitment/faction-merger, at-peace withdrawal and 90-day reset testing.
- Friendly-owner liberation with Indian garrison proof, lane interoperability,
  mixed three-result theatre and 45/35/20 Japanese armistice testing.
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

The complete source-side gameplay guide is GAMEPLAY_CHANGES.md. The canonical
Alpha 21 operational specification is docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md.
