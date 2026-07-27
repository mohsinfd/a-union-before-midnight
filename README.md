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
- Blood and Iron v1.1 installed as `Mods\Blood and Iron v1.1`
- A new 1933 campaign is recommended

This repository contains only the **A Union Before Midnight overlay**. It does not
redistribute Darkest Hour or the complete Blood and Iron mod.

## Installation

1. Install Darkest Hour and Blood and Iron v1.1.
2. Download and extract the latest A Union Before Midnight release.
3. Run `INSTALL.bat`.
4. Select **A Union Before Midnight** in the Darkest Hour launcher.
5. Start **A Union Before Midnight: India 1933** in the scenario list.

The installer detects the standard Steam location, verifies every overlay file,
copies Blood and Iron into an isolated mod folder and applies A Union Before
Midnight content. Existing saves in that mod folder are preserved during updates.

For a non-standard Steam library:

```powershell
powershell -ExecutionPolicy Bypass -File installer\Install-A-Union-Before-Midnight.ps1 `
  -GameRoot "D:\SteamLibrary\steamapps\common\Darkest Hour A HOI Game"
```

## Campaign

- **209 India-focused entries** across 25 isolated event modules.
- **41 player-timed decisions** for optional authorizations and **168 events**
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
  **14-32 naval formations** by 1940 before ordinary player queues and
  strategic-path bonuses.
- Arabian Sea, Bay of Bengal and Indian Ocean commands.
- One or two naval-aviation ships by 1940 and two or three by 1942.
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

India has a complete `IND` visual namespace with Indian service palettes,
model panels, production icons, national flags and dedicated Gurkha coverage.
The map animation geometry remains compatible with Blood and Iron.

![Indian sprite comparison](assets/sprite-comparison.png)

Major world events and strategic-route events use a curated visual library.

<details>
<summary>Open the event-art gallery</summary>

![Event-art gallery](assets/event-gallery.png)

</details>

## Reliability

The release pipeline rejects:

- malformed events, duplicate IDs and unsupported commands;
- non-owned or geographically invalid construction targets;
- infrastructure above 100 and air or naval bases above level 10, including
  construction already in progress;
- event force serials that lack the manpower required by Darkest Hour;
- advanced units queued before their type and model are enabled;
- invalid or display-string-less division attachments;
- broken portraits, sprite palettes, model panels and production icons;
- strategic paths that fail the deterministic economy and force-plan gates.

The public release passed source and installed-mod validation, all five
deterministic prewar simulations and a human campaign through January 1937
without India-event namespace errors in `savedebug.txt`.

See [Release Notes](RELEASE_NOTES.md), [Design Notes](docs/DESIGN.md) and
[Art and Research Credits](docs/ART_AND_RESEARCH_CREDITS.md). The complete
[event/decision policy](docs/EVENT_AND_DECISION_DESIGN.md) and
[row-by-row audit](docs/event_decision_audit.csv) are also included.

## Compatibility

- A new campaign provides the intended force and economic curve.
- A new campaign is required to see the independence prologue and provisional
  cabinet sequence introduced in V3.4.
- Healthy V3.3 saves can continue and will use the corrected future decisions.
- Units silently omitted by the engine before the V3.3 queue fix cannot be
  reconstructed automatically.
- Other mods that replace the Blood and Iron 1933 scenario, India data or
  global event files are not supported.

## Credits

Design and India-specific content by **Mohsin Dingankar**, developed with Codex
collaboration.

Built on **Blood and Iron v1.1** by thewanderingknight, which incorporates work
from the projects and contributors listed in the original Blood and Iron
credits. See the full [credit and provenance record](docs/ART_AND_RESEARCH_CREDITS.md).

Darkest Hour and Hearts of Iron are trademarks of their respective owners.
This is a non-commercial fan modification and is not affiliated with or
endorsed by the original publishers.

## Rights

This is a mixed-origin fan project. No blanket licence is granted over
third-party game or mod assets. See [RIGHTS.md](RIGHTS.md) before redistributing
or incorporating material into another project.

