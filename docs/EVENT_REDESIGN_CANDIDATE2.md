# Candidate 2: more than the Japanese war

Staged gameplay revision, 10 September 2026. Not installed, not an engine-tested
release. Candidate 1's safety and installation blockers still apply. This is a
bounded first response to the alignment audit, not a claim of equal depth across
all five alignments.

## Western war against Britain

Limited victory can now be earned by holding Aden, Suez and Mombasa. Add Cape
Town for the western major victory. Singapore is not required for this option.
The previous Singapore/Kuala Lumpur route remains available. Leverage loss and
recovery use the same qualifying maps, and recovering ground does not repay the
historical milestone rewards. Peace still goes through the guarded armistice
process: a victory notification does not itself end the war.

## Choices that change the result

Twelve existing choices now have distinct extra, one-time rewards. No new event
IDs, national routes, callback chains or recurring decisions were added.

| Existing campaign | Choice and objective | Extra reward |
| --- | --- | --- |
| Allied continental expedition | Main front: six Indian land divisions in each of Berlin and Vienna | +2 research modifier |
| Allied continental expedition | Mediterranean: six in each of Rome and Athens | +3 transport-capacity modifier |
| Allied continental expedition | Separate command: either deployment pair or the previous German victory milestone | 1,200 supplies |
| German Eurasian offensive | Caucasus: Indian control of Baku and Astrakhan, at war with the USSR | 1,500 oil |
| German Eurasian offensive | Central Asia: Indian control of Tashkent and Omsk, at war with the USSR | +3 transport-capacity modifier |
| German Eurasian offensive | Mobile front: previous northern/Soviet victory milestone | 1,200 supplies |
| Comintern anti-fascist expedition | Joint plans: six Indian land divisions in each of Berlin and Vienna | +2 research modifier |
| Comintern anti-fascist expedition | Mediterranean: six in each of Rome and Athens | +3 transport-capacity modifier |
| Comintern anti-fascist expedition | Free command: either deployment pair or the previous German victory milestone | 1,200 supplies |
| Independent continental campaign | Buffer league, after the existing continental victory objective | -3 dissent |
| Independent continental campaign | Base network, after that objective | +3 transport-capacity modifier |
| Independent continental campaign | Mobile guarantees, after that objective | 1,200 supplies |

Expedition deployments require war with Germany. Each city must be controlled
by India or by Britain, America or the USSR in an actual alliance with India;
hostility with the controller disqualifies it. An ally taking cities without
Indian troops does not qualify. These are current deployment checks, not battle
participation or sustained-hold checks. They also provide an alternative to the
two expedition intermediate milestones, so coalition-controlled territory does
not strand the sequence before the choice.

Existing focus activation, current relationship, intermediate, choice and
completion prerequisites remain. The existing shared war-achievement and
postwar-congress locks remain: these are not twelve stackable farmable rewards.
Conflicting choice flags block the new ending rather than paying multiple
packages. This targets a new campaign; it is not a repair for contradictory old
save flags.

The extra rewards are added to the normal culmination rewards. They represent
Indian logistics, experience and political gains, not foreign concessions.
None grants land, a base treaty, a puppet, or separate-peace rights. Choosing a
frontier base policy does not magically place bases in another country.

## What is still unfinished

This pass does not implement negotiated Allied decolonisation, competing German
territorial claims, new partner-collapse continuations, or a complete independent
Ocean federation story. The remaining 48 strategic choice flags have not gained
new endings here. Japan remains the deepest content family. All-event lifecycle
audit, installed-compiler safety parity and native playtesting remain blockers.

The pale-jade colour selection is separate and is still not installed. No saves
or live game files are changed by this staged revision.

## Verification

26 tests passed: five focus-outcome tests, nine western-campaign tests, two
version-identification tests and ten full-pipeline integration tests. The
integration run completed in 123.983 seconds. An independent agent also reviewed
the focus changes and tested the western transform against Candidate 1's staged
input. The entire 318-test Candidate 1 suite was not rerun for this bounded pass.

Automated checks cannot establish the game's native garrison interpretation,
popup fit, event polling or campaign balance.

The completed build is `build/redesign/candidate2`, identified as
`EVENT-REDESIGN-CANDIDATE2`. It preserves all 5,553 original event IDs and contains
5,585 events including Candidate 1's existing 32 additions. This pass adds no
IDs. Build fingerprints confirm authored inputs, installed custom and stock
modules, toolchain and the protected May 9, 1942 save stayed unchanged during
generation. Candidate 1's output remains in place. The manifest explicitly marks
Candidate 2 `installable: false`.
