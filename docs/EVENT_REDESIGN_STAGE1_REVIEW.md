# First staged implementation: review findings

10 September 2026. This records code review, not an engine playtest or release.

Final staged verification: **66 script tests passed** using
`python -m unittest discover -s tools -p "test_aubm_redesign*.py"`.
The final builder preserved all **5,553 authored IDs**, changed **279 event
blocks**, and separately inventoried **5,593 installed IDs**, including **40
installed-only definitions**. It found no missing custom-module callbacks.
Authored inputs, installed custom event files and the named latest save passed
the before/after unchanged checks. The manifest remains `installable: false`.

The independent reviewer was assigned after the first implementation. The final
staging tree must be regenerated from authored inputs after these corrections.

| Finding | Correction | Evidence scope |
| --- | --- | --- |
| Stale Commonwealth reply could clear a newer naval offer | Obsolete cleanup requires the matching proposal and Allied ownership; unrelated old replies close without effects | Proposal-switch regression test |
| Free Cancel could strand a pending Allied reply | No blind free cancellation on transaction replies | Pending-reply eligibility tests |
| German/Soviet queued joiners had the same cancellation problem | Free Cancel uses an explicit menu/request allowlist; these replies get owned failure exits | War/alliance/puppet-change and unrelated-offer tests |
| German acceptance blocked during an unrelated war but original fallback did not cover that state | Failure eligibility follows the complete success conditions | Wartime German acceptance test |
| A legacy government flag could close recovery although release/puppetry failed | Constitutional closure checks the actual sovereign or Indian-puppet relationship, or an explicit direct-rule choice | Missing-country/wrong-master and actual-outcome tests |
| A new no-effect exit on the persistent partner crisis would reopen the popup | Only the player-invoked eastern request receives the added free exit | No new effect-free calendar-crisis loop test |
| Callback graph used the wrong field for foreign recipients | Read `where`, preserving the older `country` fallback | Foreign receiver and delay test |
| Test evaluator interpreted multi-condition NOT incorrectly | Use documented NOR semantics; explicit NOT-of-AND remains distinct | Four-case truth table against local engine documentation |
| Integration size check included unchanged legacy conditions | Check newly changed gates for growth; separately flag large retained gates | New/changed gate-size test plus per-event follow-up register |

The last item is not a waiver that old large tooltips are safe. They remain part
of the unresolved native-layout and crash review.

## Still unresolved

- Repeated generations of the **same** diplomatic offer cannot reliably be
  distinguished by the current shared flags.
- Most foreign reply families, crisis completion ordering and global route
  dependencies have not received a full lifecycle rewrite.
- Government release eligibility, reward/cost ordering, coalition peace effects,
  hold timers and old-save compatibility have not been demonstrated in-game.
- The installed build contains generated events and safety changes absent from
  the authored staging baseline. Those require explicit reconciliation before
  making a playable build.

No event has full lifecycle or native-engine signoff. The builder records all
event IDs as pending in those dimensions while attaching the narrower work
performed. `build/redesign/manifest.json` records the final toolchain and protected
input hashes; `STATUS.md` records the generated counts. The execution specification
is `docs/EVENT_REDESIGN_EXECUTION.md`.
