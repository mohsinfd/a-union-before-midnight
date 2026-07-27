# Release Notes

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
