# Candidate 3: four campaigns beyond Japan

10 September 2026. Staged for a new campaign, not installed or engine-tested.
This extends Candidate 2; it does not replace its twelve choice consequences.

## How these stories work

Eight new events make four two-part campaigns. Each starts with a choice of
objective and finishes with a choice of payoff. Starting costs 300 money and
800 supplies. No opening gives troops or bonuses. No story declares war.

Only one of these four campaigns can be open at a time. Its follow-up remains a
manual decision: leave it open for free while you fight, or abandon it permanently
without a refund. Abandonment releases the shared slot but cannot restart the
same campaign. Completing one permits another eligible campaign later; unlike
the older shared primary-war-achievement system, these stories have their own
once-only endings. This is up to four paid campaign rewards, not an unlimited
repeatable bonus.

All start from 1937 onward, for human-controlled sovereign India. Alliance or
compact eligibility uses current relationships, not a new permanent route.
There are no timed callbacks, automatic event popups, compulsory wars, peace
commands, puppet commands or foreign territorial transfers.

## Allied: The Monsoon Soldiers Go West

While an Allied partner fighting Germany or Italy, choose:

- Fighting expedition: six Indian land divisions in Rome and six in Athens.
- Sea road: six Indian land divisions in Suez and six in Rome.

At the ending, keep a transport service for +4 TC modifier, or bring veterans
home for 35 manpower and -3 dissent. Remain an Allied partner and at war with
Germany or Italy to claim the ending.

## Axis: The Maps on the German Table

While a German partner fighting the USSR, choose:

- Oil road: Indian control of Baku, Astrakhan and Stalingrad.
- Inland road: Indian control of Tashkent and Omsk.

Victory offers +4 TC modifier and 1,500 oil, or two factories each in Bombay and
Calcutta. The factories require Indian ownership and control of both cities.

Germany collapsing does not discard your paid campaign. If Germany disappears
or no longer controls both Berlin and Vienna, India can still finish its Soviet
objective, provided it is not at war with Germany. Before the objective is
complete, holding Baku or Tashkent opens a rescue ending: pay 500 money and
recover 20 manpower, with no victory reward. Rescue closes this campaign, so it
cannot be followed by another claim on its victory prize. War with the USSR is
required for either outcome.

This represents rescuing personnel and engineering capability, not actually
moving units off the map. The collapse check is a two-city control proxy, not
a claim that Germany's historical surrender has fired.

## Comintern: What Comes After the Red Flags?

While a Soviet partner fighting Germany, choose scientific teams for Berlin
and Vienna, or railway teams for Rome and Athens. Put six Indian land divisions
in each selected city. To finish, remain a Soviet partner and either continue
the German war or have Germany no longer exist.

Choose an Indian research programme (+3 research modifier, costing 500 money
and +1 dissent), or military workshops (+4 supply-production modifier, costing
1,500 supplies). These are additional ending costs. Nothing automatically
grants Soviet consent or supervisory powers over India.

## Independent: An Ocean Without a Patron

While independent and fighting Persia, Afghanistan, Iraq or Britain, choose:

- Western sea road: Indian control of Aden, Suez and Mombasa while at war.
- Continental frontier: recorded regional victories over Persia and Afghanistan,
  followed by peace with both.

Remain independent to finish. Choose +5 TC modifier for 1,000 oil, or two
factories each in Bombay and Calcutta for 600 money. Factory ownership and
control are checked before payment. These goals do not involve Japan.

## Limits and safeguards

Expedition city checks accept Indian control, or control by Britain, America
or the USSR in an actual alliance with India and not hostile to India. A compact
alone does not make foreign-controlled cities qualify. Six Indian land divisions
must be present in each city: this is a current deployment check, not a count of
battles won or a timed hold. Current losses can therefore delay completion.

Choice flags are mutually exclusive at the victory check. Payment, ownership,
relationship, objective and unclaimed status are checked again on the reward
action. No reward is promised merely because the card is visible. If relations
change, the free defer and permanent-abandon actions remain available.

These are substantial optional side campaigns, not complete replacements for
the older alliance content. Negotiated Allied decolonisation, actual competing
German territorial settlements, negotiated limits with Moscow and the full
Indian Ocean federation story remain unfinished. Do not mistake domestic
factory or research rewards for those diplomatic outcomes.

The earlier release blockers still apply: remaining event-chain review,
installed-compiler safety parity, native transitions and popup readability.
Pale jade is still a separate uninstalled visual choice. Neither installation
nor GitHub publication is performed by this revision.

## Validation

23 tests passed: eleven campaign tests, two version tests and ten full-pipeline
integration tests. The integration run took 129.063 seconds. The broader prior
regression suite was not rerun in full. During development, tests caught an
Axis-condition grouping error and a collision with Nepal's event IDs; both were
corrected before the final successful build. The campaigns use IDs 9398500-07.

The frozen build completed at `build/redesign/candidate3` as
`EVENT-REDESIGN-CANDIDATE3`: 5,553 original events preserved, 5,593 total events
including 40 registered additions (eight new here, 32 inherited). All 58 custom
modules remain accounted for. Fingerprints verified that authored inputs,
installed custom/stock files, toolchain and the protected May 9, 1942 save stayed
unchanged during generation. Candidate 1 and Candidate 2 outputs remain intact.
The manifest explicitly says `installable: false`. These checks are not native
gameplay or balance verification.
