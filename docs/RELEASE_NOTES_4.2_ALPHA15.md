# A Union Before Midnight 4.2 Alpha 15

Alpha 15 is a cumulative playtest release covering the specialist-unit,
diplomatic, naval-contract, fleet-identity and aviation-research work completed
after Alpha 13.

## Specialist Formation Progression

- Replaces eight frozen one-model specialist families with 42 equipment models.
- Adds milestone ladders for Gurkha Rifles, Frontier Force Rifles, Chindit
  columns, Indian Airborne, Coromandel Marines, Guards Armour, Guards Motorised
  and Indian Pioneers.
- Connects each ladder to its relevant normal research branch. Pioneers require
  both infantry and engineer advances; the other formations follow mountain,
  airborne, marine, armour or motorised research.
- Embeds model progression in the relevant technology effects rather than using
  brittle event chains or free modernization popups.
- New models enter the ordinary build and upgrade systems. Existing formations
  consume upgrade IC and time; no event grants free upgrade progress.
- Spaces modernization around meaningful wartime and postwar milestones to
  avoid forcing India to upgrade every specialist formation every few years.
- Supplies valid localized model names and interface-art fallbacks for all 42
  models.

## Tokyo Recovery

- Repairs the slept Tokyo assessment dispatcher that stranded second partnership
  proposals in older saves.
- Adds a one-time, no-cost recovery for a pending proposal after the bilateral
  channel has reopened.
- Restores influence credit for India's China-policy concession, recognition of
  Japan's China position and the Indian-led Imphal plan.
- Preserves uncertainty: senior India receives 70 percent acceptance, 25 percent
  counteroffer and 5 percent rejection.
- Allows a strategic partnership to be converted into a formal Delhi-Tokyo
  alliance from the War Cabinet. The alliance remains optional because it merges
  every Indian and Japanese war.

## Diplomatic Information and Leverage

- Shows money, supply, manpower and dissent commitments before the major London,
  Berlin, Moscow, Tokyo, Delhi Pact, Himalayan, Ceylon, Goa and Abyssinian choices.
- Shows foreign acceptance, counteroffer and rejection odds where the engine
  cannot expose them dynamically.
- Protects curated diplomatic descriptions from the automatic decision-ledger
  generator during future builds.
- Improves the expensive dual Himalayan settlement: Bhutan moves from 60 to 75
  percent acceptance and Nepal from 45 to 60 percent.
- Splits the grand Himalayan responses into valid two-action foreign events,
  avoiding ambiguous four-action probability blocks.
- Differentiates Goa escalation: immediate ultimatum 35 percent, customs pressure
  55 percent, civil resistance 65 percent, sustained blockade 75 percent and a
  mediated route with two foreign decisions.
- Adds explicit response ledgers to the Allied, German, Soviet and non-aligned
  strategic conferences.
- Makes the major Allied, German, Soviet and Asian strategic routes communicate
  the political risk before India commits.

## Naval Contracts and Fleet Identity

- Corrects Project Himalaya and its sister super-heavy battleship from an
  ineffective 835-day order to 420 remaining days under India's national-yard
  construction rules.
- Stages the first contract from 1939 at 140 IC and the sister contract from 1941
  at 180 IC, with normal daily shipyard cost.
- Renames the contracts INS Meru and INS Trikuta so they cannot duplicate normal
  player-built ships.
- Gives the Arabian Sea, Bay of Bengal, ocean-carrier, light-carrier and submarine
  programmes event-reserved names rather than consuming the ordinary name pool.
- Leaves most fleet expansion to the player. The reviewed 1941 save contained 56
  combat ships, approximately 19 from events and 37 from player production or
  conversion.

## Aviation Research

- Separates six previously overlapping aviation teams into design, production,
  experimental, frontline doctrine, carrier doctrine and air-staff roles.
- Introduces Tata Air Lines Engineering Works, Walchand's Hindustan Aircraft,
  V. M. Ghatage's Aeronautical Laboratory, No. 1 Squadron, Aspy Engineer's Fleet
  Air Arm and Subroto Mukerjee's Air Staff.
- Keeps carrier aviation research available from the opening independence event.
- Normalizes all 31 Indian technology-team records to the engine's 39-field CSV
  schema.
- Preserves India's full 232-technology British Raj inheritance at campaign start.

## Force Review

- Reviews the November 1941 save at 146 land divisions, 43 air wings and 74 naval
  units.
- Confirms that the player's mobile army, most air wings and most combat ships came
  from player production rather than event grants.
- Avoids a blanket force nerf. Event formations remain strategic seeds while the
  player determines the eventual force structure.
- Uses unique scripted ship names to prevent the duplicate identities found in
  the reviewed save.

## Build and Compatibility

- Generates specialist models, localization, interface fallbacks and events
  deterministically during every build.
- Extends the specialist release gate to validate model progression, technology
  gates, artwork, localization, equipment manpower and normal upgrade behavior.
- The Tokyo proposal recovery remains compatible with the November 1941 autosave
  and does not modify that save file.
- Existing saves retain commissioned specialist formations and receive future
  model unlocks from future research. A new campaign provides the complete
  intended progression, including milestones researched before commissioning.
