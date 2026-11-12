# Human Japan event-flow audit

Reviewed 11 November 2026. Scope: source catalogue/build preparation, compiled installed R8 scripts, the offline state model, and Germany Overhaul Campaign's actual `db/events/GMO` lifecycle scripts. Germany was read only. No installation, save change or game launch was performed by this audit.

## Findings and changes

| Finding in the reviewed build | Applied correction |
| --- | --- |
| All 17 country settlements were both decision cards and automatic events. Selecting a three-month delay could generate another puppet/neutral-state popup every quarter. | All 17 are manual decisions. Closing the terms leaves the same card available without scheduling a reminder. Permanent dismissal still permanently dismisses that country's offer. |
| Seven remaining prewar offers charged small additional bills for marginal service allocation, morale, attack or transport modifiers, despite R8's larger service programmes. | Retired `allocations1933`, `deck1935`, `colleges1936`, `rail1937`, `materials1938`, `nomonhan1939`, `instructors1940`. IDs and old completion/expiry receivers remain registered. Existing funded legacy effects can still finish or expire. |
| The three US purchases, the Soviet commercial offer and the captured-railway project opened automatically. | Existing offers become manual decisions. Tomozuru and the 1935 typhoon remain historical story events. No new preparation offers or country routes were added. |
| Even a manual paid card's postponement scheduled a visible `*_return` event. The renderer's empty descriptions do not establish silent execution. | Closing a manual paid offer leaves it available immediately and schedules no reminder. Genuine refunds retain their 90-day cooldown and old receivers remain registered. |
| Country `verify` could reopen failure after a completed agreement; several other scheduled diplomatic receivers had no pending check. | All meaningful prepare/create/withdraw/commit/local/verify/failure actions require a live pending agreement. Inert fallbacks safely absorb stale scheduled receivers. Confirmation is guarded by settled and not already announced. |
| Failed settlement retry jumped directly to commit, skipping the withdrawal/release preparation that might have failed. A chosen retry could cycle to another failure popup in six days. | Explicit retry re-enters preparation after 30 days, retains the same terms and charges no new fee. Stopping dismisses that agreement while retaining the actual map/diplomacy state. |
| A normal successful country sequence scheduled both a separate Japanese preparation acknowledgement and a separate confirmation after verification. | Preparation runs in the chosen terms action, in the original command order. Original one-day creation and three-day commitment delays remain. Verification is the final confirmation. Old helper IDs remain for older queued events. |
| Paid proposal actions relied on the enclosing event to block another payment. Delayed finish events could have no valid action once another receiver cleared their pending state. | Payment actions recheck their complete offer gate. Paid finish actions require pending and not done, with an inert stale fallback. Existing site, research, manpower, relationship and exact-refund conditions are preserved. |
| Guangxi/Yunnan local development money and supplies had no independent receipt, unlike their common national starter support. Replaying the local receiver could repeat the paid grant; repeated confirmation could also refund again. | One grant receipt per region, plus pending/done checks on regional release/commit/confirmation/refund. National starter support keeps its existing guarded policy. |

## Concrete player flow

The prewar player can choose existing industry, shipping, service priorities and imports when funds and resources permit. Ignoring a manual card has no cost or strategic consequence. Closing it leaves it in Decisions; permanent dismissal remains explicit. The historical diplomatic opening and disaster stories remain events.

After military victory, China and the 16 other country settlements remain available under their original military/geographic requirements. China remains the pre-Pearl exception. The player opens the named country's terms, selects puppet/base/neutral terms, and receives a checked final confirmation. Other wars continue. A settlement is never created just because its requirements became true.

This does not promise zero acknowledgements. Create, commit and verification receivers can still be visible to human Japan; a failed check has a separate explanatory notice. Legacy `*_return` receivers, refund cooldowns and resource-batch resets may also appear when genuinely scheduled. The installed documentation contains no general silent-event declaration; `AI_EVENT` is not evidence that a human-country callback is hidden. Germany's internal AI bookkeeping uses AI-country receivers and `AI_EVENT`, which cannot be treated as a guarantee for human Japan.

## Verification

`python japan_expansion/FLOW_review.py`: **13 tests passed**, including 51 country/terms combinations (all 17 countries, all three terms), four annexed/foreign-owner release cases, human-only counterfactual compiled triggers, ignoring/dismissing offers, repeat payment/delivery/refund attempts, stale diplomatic callbacks, regional grant receipts, original creation/commit delays, and unrelated-war preservation. Tests use an explicitly human-aware extension because the shared simulator otherwise treats both `ai = yes` and `ai = no` as true.

Visible Japanese offer gates remain below 2,500 characters. Measured maximum visible gate: 1,321 characters (captured-railway completion refund); maximum offer gate: 1,186. China settlement actions use 1,169 gate characters and at most 13 commands after preparation is inlined. The largest existing visible action has 22 commands (`base_gaps_b2_apply`), outside the settlement edits.

The broad 77-review discovery initially exposed legacy test-model limitations: the restricted construction simulator lacked `ispuppet` and other full offer-gate predicates. The subsequent [legacy reconciliation](FLOW_LEGACY_RECONCILIATION.md) models those predicates and corrects stale opportunity fixtures without changing gameplay guards: the integrated `simulate.py` suite now passes all 98 tests. Two separately observed broad-discovery failures concerned an old B2 save registry and the now capacity-gated wartime fuel packet, owned by other work streams; they are not included in that 98-test suite or counted as passing in the 13 focused tests.

The tests verify the declared command/state contract; they do not establish observed engine government-change timing, UI silence, or transport/production results in a running game. Source IDs are preserved against the existing `events.json` registry. No new events are introduced by `campaign_flow.apply()`.

## Integration

Import `campaign_flow` and call `campaign_flow.apply()` after `human_campaign.apply()` and after other new campaign patch modules, before refreshing the builder's ID map. The renderer must only automatically offer a settlement when `e.module == 'settlements' and not getattr(e, 'manual_only', False)`; manual settlements use the builder's existing AI-only automatic trigger path. Keep the module identity `settlements`, including for source province names and support-policy discovery.
