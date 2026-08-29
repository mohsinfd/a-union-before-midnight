# A Union Before Midnight

![A Union Before Midnight](assets/a-union-before-midnight-banner.png)

**An independent India alternate-history campaign for Darkest Hour, beginning on 1 January 1933.**

A Union Before Midnight asks a simple question: what if the British Raj transferred
power before the global crisis of the 1930s, leaving a united but unsettled
Indian state to choose its own place in the world?

*Freedom came early. Unity came at a price.*

India begins sovereign from Delhi to Rangoon. It has enormous potential, weak
institutions, uneven infrastructure and an inherited military that is large on
paper but not ready for modern war. Political bargains, industrial investment,
research institutions and strategic commitments can turn it into the world's
second- or third-ranked power, but no route grants an automatic victory.

## Requirements

- Darkest Hour 1.05.2
- Darkest Hour Full, included with the game
- A new 1933 campaign

This repository contains only the **A Union Before Midnight overlay**. It does not
redistribute Darkest Hour. Players do not need Blood and Iron to run an already
built local installation. Rebuilding the personal animated-sprite overlay does
require Blood and Iron v1.1 to be installed locally; the pipeline imports those
assets and records their provenance. The donor binaries require author
permission before redistribution.

## Installation

1. Install Darkest Hour.
2. Download and extract the latest A Union Before Midnight release.
3. Run `INSTALL.bat`.
4. Select **A Union Before Midnight V4.2** in the Darkest Hour launcher.
5. Start **A Union Before Midnight: India 1933** in the scenario list.

The installer detects the standard Steam location, verifies every overlay file,
copies Darkest Hour Full into an isolated mod folder and applies A Union Before
Midnight content. Existing saves in that mod folder are preserved during updates.
Public installer manifests exclude copied foundation files, donor map payloads,
donor-derived sprites and palettes, donor-derived model panels, unresolved art,
temporary QA material and private test state. A developer build may reconstruct
personal sprites from the user's own installed mods without committing those
binaries.

For a non-standard Steam library:

```powershell
powershell -ExecutionPolicy Bypass -File installer\Install-A-Union-Before-Midnight.ps1 `
  -GameRoot "D:\SteamLibrary\steamapps\common\Darkest Hour A HOI Game"
```

For development, `BUILD_AND_DEPLOY_V4.bat` performs the complete public rebase,
repeat-build stability check, static audit, manifest generation and verified
deployment. Passing `-ValidateOnly` rebuilds and audits without touching the
installed mod. Developers with their own Blood and Iron v1.1 installation may
add `-IncludePersonalSprites` to build and validate the local-only visual
overlay; the default remains donor-free.

## V4 Direct-DH Alpha

V4 rebases the campaign directly onto Darkest Hour Full and removes the
Blood and Iron runtime dependency. It adds a grounded union-integration layer,
global reactions, operational command, procurement and war-settlement systems.

Air and naval combat now emphasizes organization loss and withdrawal over
routine destruction. Twelve three-division field corps, faster prepared
reserves, airfield security, dispersal fields and scramble missions reduce
wartime micromanagement within the limits of the Darkest Hour executable.

Alpha 22, dated **29 Aug 2026**, is the first implemented subset of the
Gameplay Fun Rework: **A Clean Opening and Audited Early Game**. A fresh 1933
campaign now has three pre-union windows instead of nine: one short premise
acknowledgment at scenario opening, then genuine choices of cabinet during the
opening 72 hours and union method on 6 January. Core state
initialization and the Union Register are folded into those choices, while the
War Cabinet remains unavailable until India has actually chosen its union.

Fresh starts pre-sleep **218 events total**: 216 retired legacy wartime/route
IDs plus the two generic V3 Gurkha and frontier decisions, leaving the unique
V4 paths. Upgrade saves retain compatibility helpers under clearer names,
without receiving fresh-start money or manpower again. The accompanying
existing-event audit made the 1934 and 1936 constitutional reviews mutually
exclusive, made all 18 founding branch identities pay one modest remembered
dividend in the first July 1934 Union report, implemented two advertised
research rewards that previously did nothing, stopped foreign credit charging
its own prior-service fee, redirected unsafe old War Cabinet menus, disclosed
opening costs and closed duplicate Gurkha/frontier entry paths.

Alpha 21, dated **29 Aug 2026**, restores the developer's exact personal
41-family India sprite profile locally after the previous public deployment.
That profile remains a local-only overlay: donor-derived sprite and model-panel
assets are excluded from the current V4 Git tree and do not ship in the public
installer.

Gameplay now applies one flexible Southeast Asian land-and-sea system under
every Indian command route. Four anti-Japanese friendly-owner liberation
chains require prior Japanese occupation plus direct Indian control or an
Indian land garrison; their credit can support the appropriate sea-lane hinges
without making peace with, or taking land from, the friendly owner. The full
theatre result requires two distinct land categories plus one sea lane, or one
land category plus two lanes. It can help unlock an optional weaker pairwise
Japanese Southern Armistice only while the Japan war and current Japanese
leverage remain live: either the recoverable direct limited-victory flag, or the
permanent theatre award backed by at least one currently active anti-Japanese
friendly liberation. An old route-neutral theatre award alone is insufficient.
The response remains 45/35/20 accept/counter/refuse with a guarded 90-day
refusal retry. Southern in-flight state plus a shared great-power terms-dispatch
lock prevents initial, retry and cross-opponent popups racing; if live leverage
has lapsed at day 90, the offer waits for recovery. Decisive
victory uses the normal great-power board and supersedes this weaker path.

Alliance synchronizers and every direct or retired legacy entry path now
respect the current binding commitment, including Berlin-Tokyo faction-merger
artifacts. Alpha 20's explicit at-peace withdrawal and 90-day realignment are
retained; the commitment is exclusive while active, not a lifetime lock. Alpha
20's local Batavia and Malaya dockets, Alpha 19's 1933 parser correction and
their regression gates remain part of the current source.

Alpha 21 passed its final deterministic build, complete static acceptance,
public-manifest generation, deployment verification and fresh executable smoke
on **29 Aug 2026**. The public installer manages **342 files** and excludes the
personal visual overlay. A fresh 1933 India campaign reached the playable map
and opening AUBM events with **0 logged engine errors**, no new crash dump and
all existing saves unchanged. A human wartime and postwar playthrough is still
required before this alpha can be treated as a proven stable campaign.

Alpha 22 passed its deterministic 4,434-file build, complete public and
personal static suites, 342-file donor-safe manifest, 1,531-file personal local
deployment and fresh executable smoke on **29 Aug 2026**. The user's 1 February
1933 autosave records all three opening IDs followed only by the Army Oath
(`9271200`), no Compatibility Review ID, an opened Union Register and the War
Cabinet becoming available only after the union. The executable log contains 0 exact `ERROR :`
lines, province validation reported no errors and no crash dump appeared. A
complete human wartime and postwar playthrough is still required.

Alpha 18 completed wartime play around a canonical War Cabinet. Allied, German,
Soviet, Japanese and sovereign routes each receive a four-doctrine war charter,
measurable battlefield achievements and a postwar Delhi congress. Great-power,
regional and 210 generated country campaigns now open from live world state,
survive reversals, permit country-specific armistices and require an explicit
constitutional settlement after annexation. Together with 26 bespoke opponents,
India can prosecute 236 country-specific campaigns without committing to a
permanent bloc. At-peace withdrawal, partner collapse and Bitter Peace now
preserve India's verified battlefield ledger. Mobilisation, annual war budgets,
cumulative debt and scalable, reducible occupation upkeep make conquest
consequential.

Alpha 16's disclosed diplomatic odds and Alpha 15's specialist equipment,
naval, command and research improvements remain intact.

For a player-facing explanation of the complete campaign loop, route choices,
war economy, mobilisation, settlement rules, verification status and remaining
playtest risks, see [Gameplay Changes and Alpha 22 Status](GAMEPLAY_CHANGES.md).
The all-route land, liberation, sea-lane and armistice rules are specified in
the [Southeast Asia Victory Matrix](docs/SOUTHEAST_ASIA_VICTORY_MATRIX.md).
The earlier reviewed-save chronology remains in
[Alpha 20 Save and Playtest Review](docs/ALPHA20_SAVE_AND_PLAYTEST_REVIEW.md).

## Campaign

- A fresh 1933 start presents only the premise and cabinet in the first 72
  hours, followed by the union choice on 6 January; compatibility bookkeeping
  no longer competes with those decisions.
- The retained Alpha 21 global fallback matrix validates **3,433 generated
  campaign events** across 210 countries as part of **40,357 checks**; the
  complete parser suite passes with 0 errors and 0 warnings.
- Stable constitutional governments, complete cabinets and leadership
  transitions tied to genuine political milestones.
- **Five strategic universes:** Allied, German, Japanese, Soviet and armed
  non-alignment.
- A permanent War Cabinet can accept one binding coalition or
  separate-command compact at a time, return to sovereign command while at
  peace, declare independent wars against non-partners and inspect every live
  theatre.
- Route-specific wartime charters turn battlefield objectives into political
  standing, then convert a completed war into a sovereign concert, security
  sphere or renewed strategic autonomy at a Delhi peace congress.
- Every major, regional and fallback opponent has a campaign brief, live
  objective, reversal, recovery, armistice response and post-annex settlement;
  old prerequisite chains no longer silently erase a campaign.
- Formal Allied, German, Soviet and Japanese alliances have deterministic
  entry and current-commitment guards. Live synchronizers and legacy choices
  cannot relabel a rival route, while at-peace withdrawal and the 90-day reset
  still permit a legitimate later realignment.
- Japan follows an independent India-facing route around China, Bose, the INA,
  Imphal, Burma and Asian leadership rather than acting as an appendage of
  Germany.
- Batavia, Malaya, Indochina and the Philippines have direct and
  friendly-liberation outcomes; Bay of Bengal, Malacca, Java Sea and South
  China Sea milestones interoperate with eligible friendly-owner hubs and feed
  the flexible three-result theatre victory under every route.
- Indian responses to Abyssinia, Spain, China, Anschluss, Munich, Prague,
  Albania and the invasion of Poland.
- Meaningful choices that trade money, supplies, manpower, dissent, autonomy
  and diplomatic freedom for distinct rewards.
- Annual wartime finance, cumulative debt, emergency credit, national service,
  scalable occupation upkeep, logistics, science, civil liberty, veterans and
  industrial reconversion.
- Postwar and Cold War content through 1964.

## Industry And Forces

- Core 1933-1940 provincial IC range of **150-209**, with a representative
  middle route of 182 and further wartime expansion.
- Resource development based on the actual oil, coal, iron, chromite and
  manganese belts of the subcontinent.
- Event-supported **67-108 effective land formations**, **10-18 air wings** and
  **14-31 naval formations** by 1940 before ordinary player queues and
  strategic-path bonuses.
- Arabian Sea, Bay of Bengal and Indian Ocean commands.
- Zero to two naval-aviation ships by 1940 and one to three by 1942,
  depending on doctrine.
- Gurkhas, frontier forces, airborne formations, long-range penetration groups
  and Andaman marine charters.
- Eight separately researchable Indian special-unit types and two half-built
  super-heavy capital ships unlocked through late naval programmes.
- The developer's exact **41-family personal India sprite profile** is restored
  in the local installation with eight-direction movement and multi-frame
  combat animation. It remains local-only; public builds inherit Darkest Hour
  Full map sprites and do not contain its donor-derived assets.
- Complete Indian naming pools for corps, divisions, air groups, wings, fleets,
  ships, submarines, transports and missiles.

## Research And Leadership

- **31 technology teams** covering industry, medicine, armour, aircraft,
  carrier aviation, naval doctrine, radar, signals, rocketry and atomic
  science.
- Historically researched and plausibly embellished traits for ministers,
  commanders and technology teams.
- Staged military promotions and service development rather than a fully
  modern command structure on day one.
- Bespoke team art and a documented distinction between archival portraits and
  plausible painted reconstructions.

![Indian technology teams](assets/tech-teams-gallery.png)

![Indian political and military leadership](assets/leaders-gallery.png)

## Visuals And World Events

V4 includes 102 byte-distinct custom event pictures covering the political
routes, global crises, campaign system and elite formations. Generated scenes
are explicitly disclosed as alternate-history reconstructions rather than
archival photographs. The event-ID manifest, source sheets and review galleries
are included in the repository.

![India event art](assets/event-gallery.png)

Public builds inherit Darkest Hour Full unit sprites and production panels. The
exact 41-family personal profile was restored locally after the previous public
deployment, but its descriptors, animation strips, palettes and donor-derived
model panels remain outside the current V4 Git tree and public manifests and
are not cleared for redistribution. Every donor path and hash is recorded in the generated personal
sprite manifest.

![India service sprites](assets/sprite-comparison.png)

India's eight special-unit families retain their gameplay, localization,
counters and technology ladders. Original redistribution-safe India sprites
and model panels remain future art work. Cleared India-specific counters,
portraits, event art and flags remain part of the direct-DH package; copied
foundation/donor map payloads and unresolved visual overrides do not.

India can react to the major crises of the 1930s and pursue separate Allied,
German, Japanese, Soviet or armed non-aligned strategic relationships.

## Reliability

The release pipeline rejects:

- malformed events, duplicate IDs and unsupported commands;
- unsupported foreign-country trigger scopes inside event commands;
- non-owned or geographically invalid construction targets;
- infrastructure above 100 and air or naval bases above level 10, including
  construction already in progress;
- event force serials that lack the manpower required by Darkest Hour;
- advanced units queued before their type and model are enabled;
- invalid or display-string-less division attachments;
- missing event pictures and malformed personnel records;
- strategic paths that fail the deterministic economy and force-plan gates;
- any file matching the nonredistributable or personal-overlay deny lists.

The V4 build pipeline also verifies the opening treasury, event-built unit
availability, combat pacing, cumulative construction caps and every installer
file hash before deployment.

See [Release Notes](RELEASE_NOTES.md), [Design Notes](docs/DESIGN.md) and
[Art and Research Credits](docs/ART_AND_RESEARCH_CREDITS.md). The complete
[event/decision policy](docs/EVENT_AND_DECISION_DESIGN.md) and
[row-by-row audit](docs/event_decision_audit.csv) are also included. The
[forum release audit](docs/FORUM_RELEASE_AUDIT.md) records the remaining
permission and moderator-approval work.

Current playtest changes are summarized at the top of the release notes. Steam
Deck controls, installation standards and hardware checks are documented in the
[Steam Deck Product Standard](docs/STEAM_DECK.md).

## Compatibility

- A new campaign is required for the intended force, economy, route and
  research curve.
- V3 saves are not supported by V4.
- Other mods that replace the Darkest Hour Full 1933 scenario, India data or
  global event files are not supported.

## Credits

Design and India-specific content by **Mohsin Dingankar**, developed with Codex
collaboration.

V4 is built directly on the user's installed **Darkest Hour Full** foundation.
V3 was developed against Blood and Iron; that historical dependency is not
redistributed or required by V4. See the full
[credit and provenance record](docs/ART_AND_RESEARCH_CREDITS.md).

Darkest Hour and Hearts of Iron are trademarks of their respective owners.
This is a non-commercial fan modification and is not affiliated with or
endorsed by the original publishers.

## Rights

This is a mixed-origin fan project. No blanket licence is granted over
third-party game or mod assets. See [RIGHTS.md](RIGHTS.md) before redistributing
or incorporating material into another project.

