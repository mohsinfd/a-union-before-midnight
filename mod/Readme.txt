=======================================================================
 A UNION BEFORE MIDNIGHT - V3.4
 For Darkest Hour 1.05.2
=======================================================================

A Union Before Midnight is a focused alternate-history campaign built on Blood and
Iron v1.1. India becomes sovereign on 1 January 1933 and inherits the
territories, armed forces and unresolved institutions of the British Raj.

The campaign is intentionally stronger than historical India, but power is
earned through political bargains, industrial costs, military commitments
and strategic risk. A successful India can become the world's second- or
third-ranked power without receiving an automatic victory.

-----------------------------------------------------------------------
 INSTALLATION
-----------------------------------------------------------------------

Source build:

1. Keep this source folder outside the Darkest Hour game directory.
2. Run BUILD_AND_DEPLOY_V3.bat.
3. The build validates all events, provinces, portraits, AI profiles,
   industrial targets and force-plan targets before it updates the game.
4. Select "India Mod V3" in the Darkest Hour launcher.
5. Start "A Union Before Midnight: India 1933" and select India.

Manual public installation:

1. Install Blood and Iron v1.1.
2. Extract the distributed "India Mod V3" folder into Darkest Hour\Mods.
3. Select "India Mod V3" in the launcher.

V3 requires a new 1933 campaign. V2 save games are not compatible.

-----------------------------------------------------------------------
 CAMPAIGN FEATURES
-----------------------------------------------------------------------

- Sovereign unified India from Delhi to Rangoon, including Burma, Port
  Blair and Lakshadweep.
- British Ceylon, Portuguese Goa, Nepal and Bhutan remain separate at the
  start and have negotiated or coercive later paths.
- Stable full-cabinet government packages prevent routine slider changes
  from alternating national leadership.
- Curated Indian land, naval and air commanders with staged promotions.
- Thirty-one technology teams covering industry, medicine, armour, aviation,
  carrier operations, radar, signals, rocketry and atomic science. Every team
  has bespoke art and validated early- and late-game research coverage.
- Forty-four distinct minister and military portraits, using documented
  archival photographs or clearly labelled plausible painted reconstructions.
- Researched and plausibly embellished traits for all 41 V3 ministers, 29
  V3 military leaders and 31 technology teams.
- Provincial industrial, transport and resource programmes based on the
  live Blood and Iron map IDs.
- Corrected Indian province spellings and selected terrain and
  infrastructure values, with historically grounded oil, coal, iron and
  rare-material redistribution that preserves the map's total resources.
- A validated 150-209 provincial IC core range by 1940, with wartime and
  path-specific expansion beyond it.
- A supported 67-108 effective land-formation range, 10-18 air wings and
  14-32 naval formations by 1940 before normal player queues and path
  bonuses.
- Arabian Sea, Bay of Bengal and Indian Ocean fleets, with one or two
  aviation ships by 1940 and two or three by 1942.
- Complete Indian naming pools for corps, air groups, fleets, divisions,
  wings, missiles, ships, submarines and transports. Event-created battle
  groups use BB + 2 CL or carrier + 2 CA + 2 DD doctrine.
- A complete IND visual namespace: visibly different khaki, rifle-green,
  olive, air-service and naval palettes; Indian unit panels and production
  icons for every inherited model; and dedicated Gurkha coverage.
- The native Blood and Iron Gurkha elite type is available to sovereign
  India through a high-cost 1934 settlement with immediate-corps,
  regimental-recruiting and elite-cadre doctrines.
- Frontier, airborne, long-range penetration and Andaman marine charters
  develop additional Indian elite-force traditions.
- Allied, German, Japanese, Soviet and armed non-aligned strategic
  universes with separate events, doctrine, force priorities and AI.
- Japan is independent from the German route and has a complete India-facing
  campaign around China, Bose, the INA, Imphal, Burma and Asian leadership.
- India can answer seven major global crises from Abyssinia to Poland, with
  diplomatic consequences and route-sensitive choices.
- A common wartime home-front campaign covering finance, national
  service, women's service, logistics, science, civil liberty, veterans
  and industrial reconversion.
- Postwar and Cold War content through 1964.

-----------------------------------------------------------------------
 DESIGN AND TESTING
-----------------------------------------------------------------------

Every major event choice is intended to trade money, supplies, manpower,
dissent, production, autonomy or diplomatic freedom for a distinct reward.
Choices are not intended to be simple strong/weak versions of one another.

BUILD_AND_DEPLOY_V3.bat runs:

- Deterministic regeneration of all Indian formation and unit names.
- Guarded regeneration of the two India-specific Map_1 CSV overrides.
- Deterministic regeneration and structural validation of the Indian
  sprite, unit-panel and production-icon namespaces.
- Province registry regeneration.
- Event syntax, ID, trigger, command and date validation.
- A row-by-row event/decision audit: optional authorizations are decisions;
  deadlines, crises, replies and consequences are events. Automatic
  one-option events cannot silently deduct resources.
- Province ownership and province-role validation.
- Minister, leader, team and portrait validation.
- Exact historical-basis, embellishment and research-source coverage for all
  active V3 ministers, commanders and technology teams.
- B&I technology-component coverage validation for the 1933, 1934, 1936
  and 1944 research phases.
- Rejection of disabled brigade placeholders whose missing display strings
  can crash Darkest Hour unit and deployment tooltips.
- AI build-ratio and event-switch validation.
- Industrial power-curve validation.
- Armed-forces expansion validation.
- A deterministic five-route prewar simulation through 1940, including event
  cadence, resources, global reactions and Japan/Germany separation.
- Source-to-game managed deployment.
- A second validation pass against the deployed game folder.

The automated gates cannot simulate the closed-source Darkest Hour engine.
A consolidated in-game campaign test is still required after deployment.

V3.4 requires a new campaign to see the 1933 independence prologue and
provisional-cabinet sequence. Existing healthy V3.3 saves can continue and
will use the corrected future programme decisions.

-----------------------------------------------------------------------
 CREDITS
-----------------------------------------------------------------------

A Union Before Midnight design, events, validation and India-specific content:
Mohsin Dingankar with Codex collaboration.

Foundation:
Blood and Iron v1.1 by thewanderingknight.

Blood and Iron incorporates work from World in Flames 2, Edge of Darkness,
Total Realism Project, Francesco's Models Mod, Kazoo's SKIF Style Icons,
Decriser's DEC Map, the Official Graphic Pack, Horton13's Graphic
Improvement Project, tioperete's ProvincePics Project and the sprite and
graphics contributors credited in the original Blood and Iron release.

This project should be distributed with appropriate credit to those
foundational authors and subject to their original permissions.

Detailed image provenance, licence records and historical research notes are
included in docs\ART_AND_RESEARCH_CREDITS_V3.2.md and the CSV manifests under
tools\data.
