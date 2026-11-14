# Purchase audit — 1 April 1936

Read-only audit of the latest autosave. No game launch, save repair or installation change.

The convoy purchases reconcile exactly. Two paid training programmes are overdue and undelivered; two paid oil contracts are absent before their intended expiry. R15.1 cannot be described as fully repaired.

| Purchase | Finding | Evidence |
|---|---|---|
| The next industrial investment | delivered | Tokyo/Hiroshima factory additions are present; the February 1934 checkpoint already has 13 and 10 IC respectively. |
| Supply the expanding army | consistent | Done; saved supply modifier 1.38 and TC modifier 1.89. These totals include research and other effects, so the individual 15-point contributions are not isolated by the completion flag alone. |
| Equip a larger army | delivered | Saved unit cost modifiers: Infantry -1 IC, Mountain Infantry -1.2 IC, Marines -1.6 IC; Marine build time -63 days. This choice awards production savings, not completed divisions. |
| Rural recovery: workshops or reserve rolls? | previously_repaired | The original completion failed. The February repaired save closes it and restores 3 IC; the current save retains DONE=1. |
| Expand fuel and supply reserves | delivered | Oil/supply storage modifier is 2.8 in peace and 3 in war, consistent with the selected +200 percentage-point addition. |
| Expand the merchant marine | delivered | Starting 640 transports + purchased 160 = 800 total now. Starting 100 escorts + purchased 40 + later Manchukuo 25 = 165 now. |
| Build an air force Japan can afford | delivered | Saved bomber-priority modifiers: Tactical bomber -5 IC/-46 days; Naval bomber -4 IC/-48 days; Transport aircraft -5 IC/-48 days; fighters -1.5 IC/-18 days. |
| Tomozuru: too much weight above the waterline | delivered | Stability study retained; destroyer sea-defence vulnerability is -1 after both structural events. The temporary production penalty has expired. |
| The carrier safety commission | failed_overdue | Selected aircrew school remains PENDING=1, DONE=0, CANCELLED=0. No completion or callback is queued. CAG/light-CAG +8 morale and +5 organisation were not delivered. |
| The oil law needs an actual reserve | contract_missing | The purchased additional 24 oil/day agreement should run until August 1937, but is absent. Its script permits cancellation (value=0). The save cannot prove whether it never appeared or was later cancelled/merged. |
| A commercial agreement with Manchukuo | delivered | Selected 25 convoy escorts; the escort pool increased from 140 at the February 1934 checkpoint to 165 now. |
| Buy oil for a larger fleet | contract_missing | The selected 24 oil/day plus 12 metal/day agreement should run until November 1936, but is absent. Its script permits cancellation (value=0); who/what ended it is not established. |
| Choose the next shipyard expansion | delivered | Saved fleet/light carrier cost and time modifiers are -0.38 IC/-153 days and -0.23 IC/-147 days. CAG savings are also present; fractional day values are stored as whole days. |
| Navigation trials or a coastal warning belt? | failed_overdue | Selected maritime trials remain PENDING=1, DONE=0, CANCELLED=0. No completion or callback is queued; Naval Bomber range +300 km and surface detection +2 are absent. |
| Build the home fuel and minerals complex | delivered | Kushiro base resources are now 217 energy/40 metal/12 rares, matching +160/+40/+10. Tokyo oil is 20; Yokohama energy is 27, matching the -20 input. |
| The typhoon exposes the fleet's weak seams | delivered | Second structural study completed; destroyer/light-cruiser vulnerability is reduced. Temporary +8-day destroyer construction penalty ended on 26 March 1936. |
| Keep civilian hulls ready for a wider war | not_due | The +60-transports delivery is still queued: event 28600667, 105 game hours from the 1 April save, due 5 April 1936 at 09:00. |

## Shipping ledger

- Start: 640 convoy transports and 100 escorts.
- Completed merchant expansion: +160 transports and +40 escorts.
- Completed Manchukuo choice: +25 escorts.
- Current: 716 free +84 assigned =800 transports; 165 escorts. No failure demonstrated for these rewards.
- Merchant reserve: +60 transports is not due yet; 105 game hours remain, to 5 April at 09:00.

## Confirmed missing training rewards

- Aircrew school, funded 20 July 1934: due 20 March 1935. Owed +8 morale/+5 organisation to CAG and light CAG. Paid 60 money, 450 supplies and 250 oil; pending, without refund or queued completion.
- Maritime trials, funded 23 March 1935: due 23 September 1935. Owed Naval Bomber range +300 km and surface detection +2. Paid 75 money, 600 supplies, 500 metal and 1,000 energy; pending, without refund or queued completion.

## Wider dispatch risk

108 event/trigger commands across 65 events contain quoted numeric targets; 82 target the new timing handoffs. Both stalled purchases use that formatting. Their completions are absent from the saved queue, completion flags and player log. The ordinary shipping rewards use unquoted targets and reconcile.

This is the leading source-level explanation. It has not been proved by launching the engine. The existing Python parser strips the quotation distinction, so its simulated deliveries and installed AST comparisons did not validate that behaviour.

Risk extends to regional purchases, American campaign support, recovery/strategic preparations, enemy response deliveries and postwar grants/refunds. Those future outcomes have not occurred in this campaign; they are exposed paths, not claimed observed failures.

## Oil contracts

The August 1934 +24-oil/day and November 1934 +24-oil/+12-metal/day purchases should still be active (until August 1937 and November 1936). Neither promised treaty is in the save. The scripts create cancellable trades and close the offers as DONE. The only US oil agreement present is the inherited 50-oil trade. Current evidence does not establish whether the paid contracts never appeared, were cancelled, or were replaced by trade automation.

## Other verified effects

Army, bomber-priority aircraft and carrier production savings are present. The home-resource project changed the named provincial outputs exactly. The storage expansion is present. The two free Type 93 torpedo attachments are in the deployment pool; they are not missing units.

## Repair scope recommended

Correct event-target integer rendering centrally; audit compiled text rather than only parsed equivalence. Recover only the two confirmed unpaid training outcomes in a separate current-save copy, without charging again. Reconcile the missing oil contracts separately before restoring any trade or backpay. Preserve shipping already delivered and the +60 reward still awaiting its due date. Do not add those shipping pools again.

The original autosave and installation were left untouched.
