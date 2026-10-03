# A Union Before Midnight 4.2.0-alpha.2

This playtest update restores naval conversion refits and makes the upgrade
budget authoritative. It is compatible with an existing V4.2 save after the
game is fully closed and relaunched.

## Decision affordability

- Priced decisions remain listed when their strategic prerequisites are met.
- The decision-panel tooltip shows every outcome and marks unaffordable ones
  red. Darkest Hour itself hides failed action triggers inside the event popup;
  the popup has no disabled-action state.
- The decision becomes selectable when at least one outcome is affordable, and
  every priced action retains its own stockpile guard.

## Naval conversion refits

- Battleships and battlecruisers may be rebuilt as fleet carriers.
- Heavy and light cruisers may be rebuilt as light or escort carriers.
- Suitable transports may be rebuilt as light or escort carriers.
- Refit cost and time use the normal upgrade system. The target carrier model
  must already be available to India.

## Upgrade-budget integrity

- Reinforcement no longer grants free upgrade progress.
- Supplied units no longer receive passive daily upgrade progress.
- Setting the production upgrade slider to zero now stops model upgrades and
  cross-type refits instead of completing them slowly for free.

## Validation

- Naval routes and both zero-progress rules are enforced by the production
  validator and repeat-build test.
- The game is not launched by the build or deployment process.
