# India Mod V3 Design

## Product Goal

India begins 1933 as a newly sovereign but institutionally fragile state with approximately 40 base IC. A successful player can build 180-230 effective industrial capacity by 1940 and exceed that during the war, becoming the second- or third-ranked power without receiving a free victory.

## Baseline

- World, AI, map presentation, music, animation frame sheets, and global
  event framework: Blood and Iron v1.1.
- Indian sprite selection, model panels, production icons, palettes and
  elite-force presentation: V3 country-specific overlay.
- Scenario date: January 1, 1933.
- Starting territory: unified British Indian Empire, including Burma and the Indian island possessions.
- Ceylon remains British and Goa remains Portuguese.
- Nepal and Bhutan remain independent.

## Design Rules

1. Every major reward has a meaningful cost.
2. No action is a strictly smaller version of another action.
3. Industrial growth uses provincial IC, infrastructure, resources, and permanent modifiers deliberately.
4. Free combat units are rare. Most military programmes unlock technology, reduce build time through legal queues, or provide one cadre formation.
5. Alliance paths are complete campaigns, not single relation bonuses.
6. Province commands use the authoritative live map registry.
7. Unit commands follow the official Darkest Hour command definitions.
8. Events are modular and use the reserved `9270000-9279999` ID range.

## Strategic Paths

- Allied partnership: finance, aviation, naval cooperation, and access to Western blueprints; costs strategic autonomy.
- German alignment: armour, doctrine, and machine tools; carries blockade, diplomatic, and late-war collapse risks.
- Japanese compact: naval aviation and Asian trade; creates conflict over China, Burma, and Indian Ocean leadership.
- Soviet partnership: heavy industry, mass production, and land doctrine; risks capital flight and political polarisation.
- Non-aligned great power: maximum autonomy and multi-vector trade; receives fewer free blueprints and must self-finance defence.

## Test Gates

1. Static syntax and brace validation.
2. Event ID uniqueness, trigger-target and action-probability validation.
3. Command-schema validation against Darkest Hour command semantics.
4. Province ownership, location and curated-role validation against Map_1.
5. Active portrait and custom visual format validation.
6. Automated 1933-1940 provincial IC curve validation.
7. AI force-ratio and construction-location validation.
8. Automated 1933-1940 effective land, air, navy and carrier-plan validation.
9. Strategic-path root flags are mutually exclusive.
10. Deterministic five-route event, resource and diplomatic simulation through 1940.
11. Exact art, provenance and historical-trait manifest coverage.
12. Source and deployed game trees must both pass.
13. A fresh game is required at each scenario-schema milestone.

## Implemented V3 Systems

- Sovereign IND start on 1 January 1933 with unified Raj territory, Burma, Port Blair and Lakshadweep.
- Independent Nepal and Bhutan, British Ceylon and Portuguese Goa at start.
- Three constitutional state models and three 1936 political mandates.
- Physical province-based industrial programmes reaching 150-209 base IC by 1940 before wartime expansion.
- Army, aviation, naval, armaments and eastern-defence programmes using legal production queues.
- Non-aligned, Allied, German, Soviet and Japanese strategic paths, with Japan
  explicitly separated from Germany and developed through China, Bose, the
  INA, Imphal and an Indian-led Asian settlement.
- Seven Indian reaction chains for Abyssinia, Spain, China, Anschluss, Munich,
  Prague and Albania, and the invasion of Poland.
- Frontier, airborne, long-range penetration and Andaman marine elite-force
  charters.
- Negotiated Bhutan, Nepal, Ceylon and Goa accession chains executed by the owning country.
- Wartime mobilization, emergency industry, war finance and eastern-front strategy.
- Wartime home-front decisions covering national service, women in service,
  ocean logistics, science, civil liberty, veterans and reconversion.
- Atomic, electronics, aeronautics, oceanic-fleet and 1942-44 great-power programmes.
- Path-specific Allied, German, Japanese, Soviet and non-aligned AI build profiles.
- 205 India events across 25 independently validated V3 modules.
- Twenty-eight V3 event images, 31 bespoke technology-team images and 44
  distinct personnel portraits with independent source and rendered-hash
  validation.
- Historical-basis, alternate-history embellishment and source records for all
  101 V3 minister, commander and technology-team assignments.
- Self-contained technology-team portraits and Indian command, fleet, air and ship names.

## Automated Build

Run `BUILD_AND_DEPLOY_V3.bat` from the V3 source folder. It rebuilds the province
registry, runs every static and balance gate, generates the managed overlay, copies
only a valid build into `Darkest Hour A HOI Game\Mods\India Mod V3`, and validates
the deployed copy. A failed source build does not update the game folder.

Optional `smoke_test_v3.ps1` and `engine_scenario_test_v3.ps1` tools are kept
outside the automatic build. They launch the closed-source game only when a
deliberate engine test is requested.
