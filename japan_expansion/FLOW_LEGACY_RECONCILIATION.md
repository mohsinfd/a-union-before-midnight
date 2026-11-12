# Integrated R9 legacy regression reconciliation

11 November 2026. Ran `python japan_expansion/simulate.py` against the integrated source catalogue. Initial result: 95 tests, 15 failures and one error. Final result: **98 tests passed**. No gameplay source guards, resource ownership rules, installed files or saves were changed in this reconciliation.

## Initial failures

| Failure group | Diagnosis | Correction |
| --- | --- | --- |
| Ten construction tests stopped at `Unmodelled predicate ispuppet`. | Restricted test-model limitation. Full payment gates now include the original human/independence eligibility. The model also previously returned true for every AI, existence, war and alliance condition. | Model these predicates explicitly: human Japan versus AI recipients, actual puppet map, country set, war pairs, alliance groups, year and recorded history. Keep all full gameplay gates. |
| Three Chinese settlement/merge tests could no longer start. | Stale fixtures. They bypassed the event's military gate before the gate was repeated on the payment/terms action. They did not establish China's required VP loss; one also lacked controlled objective cities. | Establish 80% national/VP loss and the required controlled territory, and assert the initial action succeeds before checking inherited armies, disappearance of the rump state and neutral status. |
| Existing Indonesian base-transfer test did not start. | Stale fixture. It called Indonesia an existing national state but left the rest of its homeland under the 1933 Dutch colonial owner. So it did not hold the required Indonesian capital. | The existing-state helper now assigns its source homeland to that state and controls its homeland/objectives. Separate colonial-transfer tests retain the colonial owners and exercise the release branch. |
| Materials availability test expected a later China war to reopen the offer. | Obsolete feature expectation: the small-stat materials offer is deliberately retired in R9. The broad simulator's intentionally simplified AI predicate could falsely satisfy both contradictory AI conditions. | Assert the retirement gate cannot be satisfied by either AI value. Test its retained funded completion separately as an older-save receipt. |
| Parallel Thai/Persian settlements errored on a missing completion flag. | Stale fixtures. Neither country's required centres were controlled when the strengthened terms gates were checked. | Control the two enemy homelands, establish their national losses, assert both starts succeed, and retain the checks for independent completion and continuing Soviet war. |

No actual gameplay defect was discovered among these 16 initial failing cases. Their corrections make the tests reach the intended current or legacy behavior instead of weakening eligibility.

## Other misleading tests corrected

Several tests passed only because the shared broad simulator treats both `ai = yes` and `ai = no` as true. They directly selected retired airborne, air-defence, medicine, SNLF, landing, Australian, Mediterranean, allocation and materials offers. Those are now explicitly named **legacy** tests.

Their helper first asserts the parent is retired, then seeds the command state representing a funded older-save choice. The tests exercise the retained delayed completion, refunds, discount/organisation/recruitment effects, research catch-up and expiry idempotency. They do not claim those retired offers can be selected in a new campaign. The current human-aware flow suite separately proves retired parents are unavailable.

The captured-railway refund test also previously passed without starting or charging anything: its fixture already had the Pacific flag and did not establish the China-front objectives. It now establishes the real prewar opportunity, asserts payment was taken, loses the required centre and verifies both payments are returned with no completion. The restricted infrastructure-scaling test likewise explicitly uses a pre-Pacific state.

## Added negative coverage

Three new restricted-model tests verify that a Japanese puppet cannot fund home industry, a lost Chinese puppet relationship blocks payment, a lost required base blocks payment, closing an eligible manual card schedules no reminder or payment, and the prewar captured-railway offer cannot charge after the Pacific opening.

The final 98-test suite preserves original construction ownership/research/refund assertions, country troop and base transfers, unrelated-war preservation and once-only receipts. The parent's `free_manpower`, `wartime_ic`, repair-property and manpower-stream ledger support in the broad `World` class was left unchanged. Only test methods/helpers in `simulate.py` and the restricted model/tests in `construction_safety_review.py` were edited.

This is offline state-contract verification. It does not constitute a running-engine playtest or verification that callbacks are visually silent.
