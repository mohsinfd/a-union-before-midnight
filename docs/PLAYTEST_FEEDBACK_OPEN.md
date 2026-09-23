# Open playtest feedback

Living notes from the earlier 1933 campaign. The player authorised implementation
on 13 September 2026. See [the BALANCE1 repair status](BALANCE1_PLAYTEST.md) and
[the economic/world-AI release notes](BALANCE1_RELEASE.md). The observations below
are retained as historical evidence, not a claim that every one is still open.
The ambiguous nationalisation event, broad early-team balance and native popup
colour/layout still need targeted confirmation; additional new bug notes are welcome.

## Balance

- The decision immediately before the Nationalise/Provincialise choices is
  dominated by the `-5 dissent` option. The other choices do not offer a
  comparable benefit, so the choice is effectively predetermined.
- Rebalance that decision so its alternatives have meaningful, comparable
  advantages rather than making dissent reduction overwhelmingly correct.
- Emergency Reconstruction Act: the low-IC option is never an attractive
  choice and needs a meaningful compensating benefit or a lower cost.
- “The Villages Share” decision: only the middle option is feasible; the first
  and third options need viable trade-offs.
- “Princes and the Union” event: the options are unbalanced and need a review
  of their costs, risks, and rewards.
- “Rebuild the Indian Army” event: the army-building outcome is too small, and
  the third option is always the obvious pick. Increase the event’s impact and
  give the alternatives meaningful roles.
- “Delhi Communal Compact” event: option A is again the obvious choice; the
  other options need credible benefits and trade-offs.
- “Quetta–Delhi” event: the event has too little substantive impact and its
  options are unbalanced. Strengthen the outcomes and differentiate the paths.
- “Provincial Forces and Indian Youth” event: the Territorial option is the
  easy dominant choice; the alternatives need meaningful compensating value.
- “Flying Schools” event: granting the Poona airbase makes option B the obvious
  choice; the other options need meaningful strategic value.
- “Airfield Security Act” event: it should provide a balanced package of
  aircraft, airbase capacity, and security. The current choices make C the
  obvious pick because force expansion matters more than security. These are
  internal airfields, and the original goal was to improve airfield gameplay
  broadly, including in conquered territory.
- “Ambedkar Civil Rights” event: one choice imposes higher dissent, making it
  an easy avoid. Rebalance the dissent cost against meaningful benefits.
- “First Standing Division” event: the higher-division option is the obvious
  pick. Give the smaller force option a distinct operational or economic
  advantage.
- “Burma’s Place in the Union” event: the options are unbalanced and autonomy
  is always the obvious pick. The integration alternatives need credible,
  differentiated rewards.
- Technology coverage: India currently has no technology team with Mountain
  Warfare research skill. Add or correct that capability during the technology
  team audit.
- “Tata–Bhilai” event: only the higher-output option is worthwhile. The lower
  option needs a compensating benefit so the choice is not predetermined.
- “Tokyo’s Asian Proposition” event: it fires before the player may want to
  choose a bloc and permanently locks one of three Japan-policy tracks. Add a
  neutral defer/keep-options-open choice, or delay the commitment until India
  deliberately opens a strategic channel.
- “Steel, Coal and Machines” event: one option is too heavily weighted toward
  immediate IC, making it the default choice. The alternatives need stronger
  industrial, resource, or military value.

## Technology teams

- Early Indian technology teams feel underpowered.
- Some capabilities or team coverage may be missing; identify the gaps after
  the remaining playtest pointers arrive.

## Unit availability

- Several Indian units that appear locked do not seem to unlock when India
  enters wartime. Audit the unit activation flags, dates, and wartime guards
  together; do not assume that the visible lock text matches the actual
  trigger.

## Diplomacy

- The India-at-the-League-of-Nations decision currently has only one sensible
  option; the first choice dominates the alternatives. The other choices need
  useful, distinct trade-offs.
- The London Intervention event is unbalanced and needs its options reviewed
  for comparable costs, risks, and rewards.

## Process

- More observations are expected. Keep appending them here before making the
  balancing pass.

## Presentation

- “India–Abyssinia Crisis”: the first option, “Sanctions”, ends with yellow
  text in the event window. Audit the added helper/explanation text for colour
  leakage and readability.
- “Power for a Continent” event: the high-IC option is the obvious pick. The
  lower-IC alternatives need stronger strategic or economic compensation.
- Bhutan/Nepal reopening was initially observed as red/locked, but it later
  became available; treat that observation as disregarded unless it recurs.
- “Authorise Federal Work Compact” is a weak/underwhelming event and needs
  clearer benefits or more interesting consequences.
