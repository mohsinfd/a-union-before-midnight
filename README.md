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
redistribute Darkest Hour. V4 has no Blood and Iron dependency.

## Installation

1. Install Darkest Hour.
2. Download and extract the latest A Union Before Midnight release.
3. Run `INSTALL.bat`.
4. Select **A Union Before Midnight V4** in the Darkest Hour launcher.
5. Start **A Union Before Midnight: India 1933** in the scenario list.

The installer detects the standard Steam location, verifies every overlay file,
copies Darkest Hour Full into an isolated mod folder and applies A Union Before
Midnight content. Existing saves in that mod folder are preserved during updates.

For a non-standard Steam library:

```powershell
powershell -ExecutionPolicy Bypass -File installer\Install-A-Union-Before-Midnight.ps1 `
  -GameRoot "D:\SteamLibrary\steamapps\common\Darkest Hour A HOI Game"
```

For development, `BUILD_AND_DEPLOY_V4.bat` performs the complete rebase,
repeat-build stability check, static audit, manifest generation and verified
deployment. Passing `-ValidateOnly` rebuilds and audits without touching the
installed mod.

## V4 Direct-DH Alpha

V4 rebases the campaign directly onto Darkest Hour Full and removes the
Blood and Iron runtime dependency. It adds a grounded union-integration layer,
global reactions, operational command, procurement and war-settlement systems.

Air and naval combat now emphasizes organization loss and withdrawal over
routine destruction. Twelve three-division field corps, faster prepared
reserves, airfield security, dispersal fields and scramble missions reduce
wartime micromanagement within the limits of the Darkest Hour executable.

All current source gates pass. V4 has not yet been handed to the user for its
first in-game scenario-load and campaign test.

## Campaign

- **255 India-focused entries** across 31 isolated event modules.
- **44 player-timed decisions** for optional authorizations and **211 events**
  for deadlines, crises, replies, implementation disputes and milestones.
- Stable constitutional governments, complete cabinets and leadership
  transitions tied to genuine political milestones.
- **Five strategic universes:** Allied, German, Japanese, Soviet and armed
  non-alignment.
- Japan follows an independent India-facing route around China, Bose, the INA,
  Imphal, Burma and Asian leadership rather than acting as an appendage of
  Germany.
- Indian responses to Abyssinia, Spain, China, Anschluss, Munich, Prague,
  Albania and the invasion of Poland.
- Meaningful choices that trade money, supplies, manpower, dissent, autonomy
  and diplomatic freedom for distinct rewards.
- Wartime finance, national service, women's service, logistics, science,
  civil liberty, veterans and industrial reconversion.
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

V4 includes 80 byte-distinct custom event pictures, including one
subject-specific reconstruction for every new V4 event and unique scenes for
the political routes, global crises and elite formations. Generated scenes are
explicitly disclosed as alternate-history reconstructions rather than archival
photographs. The event-ID manifest, source sheets and review galleries are
included in the repository.

![India event art](assets/event-gallery.png)

V4 now includes an original India map-sprite package: 13 visual families cover
32 Darkest Hour unit types through 595 India-specific descriptors and 234
indexed bitmap or palette files. The source sheets, build script, manifest,
review preview and strict sprite audit are included in the repository.

![India service sprites](assets/sprite-comparison.png)

Darkest Hour Full model and production-screen art remains in use. The removed
V3 donor-derived sprite and model overrides are not part of the direct-DH
package; original India model panels are the next visual phase.

India can react to the major crises of the 1930s and pursue separate Allied,
German, Japanese, Soviet or armed non-aligned strategic relationships.

## Reliability

The release pipeline rejects:

- malformed events, duplicate IDs and unsupported commands;
- non-owned or geographically invalid construction targets;
- infrastructure above 100 and air or naval bases above level 10, including
  construction already in progress;
- event force serials that lack the manpower required by Darkest Hour;
- advanced units queued before their type and model are enabled;
- invalid or display-string-less division attachments;
- missing event pictures and malformed personnel records;
- strategic paths that fail the deterministic economy and force-plan gates.

The V4 build pipeline also verifies the opening treasury, event-built unit
availability, combat pacing, cumulative construction caps and every installer
file hash before deployment.

See [Release Notes](RELEASE_NOTES.md), [Design Notes](docs/DESIGN.md) and
[Art and Research Credits](docs/ART_AND_RESEARCH_CREDITS.md). The complete
[event/decision policy](docs/EVENT_AND_DECISION_DESIGN.md) and
[row-by-row audit](docs/event_decision_audit.csv) are also included. The
[forum release audit](docs/FORUM_RELEASE_AUDIT.md) records the remaining
permission and moderator-approval work.

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

