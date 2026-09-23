# Candidate 4: freedom at the peace table

Staged on 10 September 2026. Not installed or engine-playtested. This pass adds
an actual diplomatic outcome to the Allied campaign, not another domestic bonus
standing in for foreign consent.

## Three earned negotiations

India may ask Britain to end its mastery over Egypt, Iraq or Oman. All three
are British puppets in the installed 1933 scenario files checked for this pass.
The event still checks their current status: if a country has already become
independent, disappeared or acquired a different master, this proposal is not
available.

Eligibility requires human-controlled, sovereign India, from 1937 onward:

- A current Allied relationship (formal alliance or supported existing compact).
- A recorded successful Suez defence (`ind_lib1_suez_reward`) or completion of
  the existing Allied continental focus.
- Britain existing, sovereign and not hostile to India.
- India, Britain and the target all completely at peace.
- The target still being a British puppet.

Candidate 3's abandoned/completed side-campaign flag is deliberately not used
as proof: that flag also marks abandonment and would wrongly reward failure.
An American compact may qualify under the existing Allied relationship rules,
but Britain must still meet all the British consent and mastery checks.

## The choices and their consequences

| Indian choice | Immediate cost | British AI acceptance |
| --- | --- | --- |
| Standard diplomatic campaign | 250 money | 60% |
| Stronger diplomatic campaign | 750 money | 80% |
| Not now | Nothing | No request sent |

Fees pay for the diplomatic campaign, are not transferred to the target, and
are explicitly non-refundable even after refusal or changed circumstances.
There is one attempt per country, not a repeatable chance to purchase the same
outcome. A human playing Britain may choose either valid response; percentages
are AI weights, not a forced outcome for a human.

The British reply is queued for two days later. Britain can accept and execute
`end_mastery` on its own puppet, or refuse without changing sovereignty. The
reply checks the current relationship, peace and mastery again. A request that
has been closed or overtaken by events cannot cause a late release.

India's follow-up stays a manual decision, with free waiting and permanent
closure. Recognition is available only after a British acceptance AND an
observed existing country with no puppet master, while not hostile to India.
Recognition gives -2 dissent and +30 relations with that country, once. An
acceptance flag cannot award this if the command failed or another master took
over. Closing after an actual release does not reverse independence; it can
forfeit the unclaimed Indian recognition reward.

## What this does not do

No Indian puppet is created. No provinces, military access or alliances are
transferred. Existing alliance membership is left alone. No peace or war
command is present. An independent country remaining in the Allies is a valid
outcome, not a failed release. Whether native `end_mastery` behaves as documented
still needs an engine test.

There is only one active decolonisation negotiation at a time. Up to three
country opportunities may be visible before selecting one; after selection,
the pending-review card owns the process. This slot is separate from the one
active Candidate 3 expedition. No new national route or ledger hub is added.

Nine new events (9398600-08) implement a shared three-step pattern: Indian
proposal, British reply, Indian observation. They append to an already-loaded
module, with explicit collision checks and a registered ID range.

## Still unfinished

The larger German territorial dispute, negotiated limits with Moscow and full
Indian Ocean federation remain unimplemented. This is a limited three-country
Allied decolonisation family, not a general colonial settlement engine. Previous
release blockers, pale-jade installation and native gameplay validation remain.

## Verification

Focused tests cover every target, both funding levels, acceptance/refusal,
changed war/master/alignment, cancellation before the reply, failed releases,
repeat rewards, affordability and foreign command ownership. All 22 tests passed:
ten decolonisation tests, two version tests and ten full-pipeline integration
tests (130.056 seconds for integration). The entire older regression suite was
not rerun. No existing save is migrated.

The frozen build completed as `EVENT-REDESIGN-CANDIDATE4` under
`build/redesign/candidate4`, preserving all 5,553 original event IDs. It contains
5,602 events across 58 modules: 49 registered additions, nine introduced here.
The build rechecked authored inputs, installed custom/stock files, toolchain and
the protected May 9, 1942 save; all stayed unchanged during generation. Earlier
candidate outputs remain intact. The manifest retains `installable: false`.
