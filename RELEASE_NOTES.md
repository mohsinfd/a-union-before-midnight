# Release Notes

## 3.3.0 Public Release

### Force Queue Reliability

- Event-created serials now check the manpower needed for the complete queue,
  matching Darkest Hour's documented `build_division` semantics.
- Removed the separate manpower deductions that previously double-charged the
  player and caused the engine to omit some formations silently.
- Armoured, mechanized, airborne, transport-aircraft and specialist attachment
  types are explicitly enabled before an event queues them.
- Added save-compatible reserve, armoured-corps and air-transport registration
  events. Existing eligible saves receive the correction within several game
  days.

### Construction Limits

- All 195 positive infrastructure, air-base and naval-base commands now inspect
  the province's current and queued maximum before applying.
- Infrastructure is capped at 100.
- Air and naval bases are capped at level 10.
- Long development chains can no longer waste construction or make selected
  hubs exceed engine limits.

### Indian Visual Identity

- Normal Indian units now use alternate Commonwealth animation donors rather
  than the previous nearly identical U02 presentation.
- Land, air and naval service palettes have stronger visual separation.
- India now packages its own map flag and unit icon assets.
- Model panels prefer non-British Commonwealth donors where Blood and Iron
  provides them, with British material retained only as a compatibility
  fallback.
- Gurkhas retain their dedicated green elite presentation.

### Playtest Status

- Human campaign completed from January 1933 through January 1937.
- No India Ascendant parser, event or scenario errors appeared in
  `savedebug.txt`.
- The observed repeated "event has been slept" messages originate from Blood
  and Iron base events rather than India Ascendant namespace.
- Money remains intentionally tight in the opening years, but every strategic
  path remains solvent in the deterministic simulation.

### Known Foundation Behaviour

Blood and Iron defines naval transports as convertible into light carriers.
With automatic upgrades funded, transport flotillas may become light carriers.
This release leaves that global foundation rule unchanged because altering it
would affect every country.

## 3.2.0 Government, Research And Service Update

- Fixed the February 1934 invalid anti-tank attachment crash.
- Rebuilt government packages and stabilized constitutional leadership.
- Expanded historically grounded minister, commander and technology-team
  traits.
- Added complete early and late research coverage, including carrier aviation.
- Separated the Japanese strategic route from the German route.
- Added global-crisis reactions and four elite-force programmes.
- Added bespoke technology-team and personnel art.
- Rebalanced the 1933-34 treasury and supply reserve.

## 3.0.0 Rebuild

- Rebuilt the campaign in the reserved `9270000-9279999` event namespace.
- Added Allied, German, Japanese, Soviet and armed non-aligned paths.
- Added a three-fleet navy, expanded air arm, industrial curve and postwar
  content through 1964.
- Added complete Indian formation naming, provincial corrections and resource
  redistribution.

