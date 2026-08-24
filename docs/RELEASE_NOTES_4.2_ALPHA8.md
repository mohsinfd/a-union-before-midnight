# A Union Before Midnight 4.2.0-alpha.8

## Great-Power Campaigns

- Added full Allied, German, Soviet, Japanese and non-aligned campaign systems
  with treaty negotiations, reusable war entry, theatre commands, operational
  AI profiles, performance ledgers and postwar settlements.
- Rebuilt the Delhi-Tokyo route as a sovereign strategic partnership. India and
  Japan can divide theatres without automatically inheriting one another's
  wars; an optional formal alliance clearly warns that it merges every war.
- Added Indian seniority bargaining over Burma, Malaya, Singapore, Indonesia,
  Australia and the Indian Ocean, while Japan retains China, the Philippines
  and the Pacific under the strongest accepted settlement.
- Added a simultaneous independent Indian campaign against the Soviet Union.
  Japan may remain neutral, apply pressure, intervene, or condemn the war.
- Added an earned Tibetan protectorate after victory on the Japanese route,
  including safe legal-owner transfers when Tibet no longer exists.
- Added performance-based influence, sovereign-state, protectorate and direct
  retention settlements across Southeast Asia, the Gulf, Central Asia and the
  East African coast. Foreign acceptance, counteroffers and refusals all have
  playable consequences.
- Replaced critical predecessor-only chains with state-based fallbacks, so a
  missing intermediary cannot silently erase strategic content.

## Forces And Decisions

- Added eight separately addressable Indian formations: Gurkha Rifles,
  Frontier Force, Chindit Columns, Indian Airborne, Coromandel Marines, Guards
  Armour, Guards Motorised and Indian Pioneers.
- Added two one-ship super-heavy battleship programmes. Each hull enters the
  queue half complete at normal cost, avoiding both instant gifts and a second
  multi-year wait after the technology unlock.
- Preserved normal-cost, current-model event procurement and the single-unit
  queue contract everywhere else.
- Extended transparent decision funding to money, supplies, manpower and oil.
  Every outcome remains visible; only unaffordable actions are disabled.

## Animated India

- Added 41 independently addressable India sprite families covering every
  stock division type and all eight special Indian types.
- Installed 591 India descriptors, 553 animated bitmap strips and 44 palettes,
  with eight-direction movement and genuine multi-frame combat throughout.
- Removed the old fallback that deleted the bespoke sprite tree during every
  rebase.
- Added manifest-owned cleanup, donor provenance, palette-index transparency
  checks, unique stand signatures and byte-for-byte repeat-build validation.
- The personal sprite profile imports Blood and Iron v1.1 assets locally. It is
  not cleared for public redistribution without permission from the donor mod.

## Verification

- Full direct-Darkest-Hour rebase is byte-stable across 4,251 overlay files.
- Static event validation: 0 errors and 0 warnings after installer-manifest
  regeneration.
- Campaign audit: 818 entries across 47 modules, 102 decisions, 47 prewar
  world-state events and zero brittle external-effect chains.
- Research inheritance: 232 India technologies against 232 British baseline
  technologies, with zero missing.
- Opening economy, sustained cash and manpower, construction caps, combat
  pacing, event art, special-unit and sprite gates pass.
- This release requires a new 1933 campaign for the intended strategic flags,
  unit registry, technology inheritance and settlement systems.
