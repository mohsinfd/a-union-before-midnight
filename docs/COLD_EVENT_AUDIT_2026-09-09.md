# Independent cold audit: political decisions through final peace

Date: 9 September 2026, local time. Three fresh-context reviewers independently inspected decision graphs, engine contracts, and actual save evidence. The coordinating reviewer separately inspected test assumptions and loaded-file coverage. No game files, saves, or implementation code were changed during this audit. This document is the only new artifact.

## Verdict

Do not treat B1 or the 153 passing script tests as a playable-campaign sign-off. There are demonstrated terminal-state errors, a wartime alliance-lock bypass, inaccessible wartime content, and callback construction that conflicts with the engine documentation. The correct repair is to consolidate state ownership and navigation across the lifecycle, not add another country-specific exception.

This is a broad, time-boxed first-pass audit, not exhaustive engine certification. The reviewers covered all lifecycle stages by sampling and graph inspection; they did not execute every branch of all five diplomatic routes. The two Indian event folders contain 58 modules and 5,593 definitions. The latest save loads 157 event files, including foreign, AI and stock systems outside those folders.

## 1. Opening politics, 1933–1936: retain the sampled core

The inspected bootstrap and domestic sequence is comparatively coherent:

- Fresh 1933 starts sovereign India outside an alliance.
- `9270000` establishes sovereignty; `9270002` provides cabinets and sets the common started flag; `9270001` completes integration.
- `9270100 → 9270101 → 9270102 → 9270103` covers constitution, land, language and the 1936 mandate. Options supply the prerequisites for the next stage.
- Sampled minister IDs exist and their availability years match.
- Cabinet restoration events `9270780–9270782` stop using opening-cabinet flags once the 1936 mandate exists.
- The bootstrap sleeps selected stock Indian elections and Gandhi events.

No blocking source defect was found in this sample. This does not certify all early political choices. Wholesale deletion of the opening events is not justified by the evidence.

## 2. Political direction and alliances: multiple systems own the same progression

World programme `9270400`, partner choices `9270401–03`, Strategic Council `9280500–02`, commitment review `9280510–11`, later Cabinet membership/treaty menus, and route-charter reconciliation coexist. Some reversibility is intentional and has cooldowns; not every cycle is a bug.

The problem is the absence of one authoritative transition owner. For example, the current custom scripts have seven `ind_v4_strategy_*` flags written by 46 events, and five `ind_aubm_commitment_*` flags written by 50 events. Charter and focus flags form additional systems. These counts indicate overlapping responsibility, not proof that every writer is incorrect.

### Confirmed B1 wartime alliance-lock bypass

A conditional path still connects settlement navigation to Allied entry:

`9297102 → 9282212 → 9282201 → 9282205 → 9282002 → 9281931 → 9281980 → 9281981 → 9281910 → 9281934`.

It requires conquered Siam and another eligible pending western settlement; this is not a claim that every current save can follow it immediately. At `9281934`, joining Britain or Washington executes alliance and commitment commands without `atwar = no`. An independent India fighting Japan or the USSR can satisfy the other conditions.

The compiler guards only four hardcoded menu IDs and misses this actual joining leaf. See [compiler political guards](</C:/Users/Mohsin Dingankar/Downloads/India Ascendant/tools/build_aubm_cleanup.py:435>) and installed `41_wartime_state.txt`, event `9281934`, around line 1282.

**Required consolidation:** distinguish historical expertise, political programme, actual treaty commitment, and active enemy campaigns. One deliberate transition must own each change. A choice should close competing choices at their entry points and at their effect-bearing leaves, not only hide a menu.

## 3. War entry and current-war context: confirmed misleading policy

The actual save records India declaring war on Japan on 13 January 1942. On 15 January, event `9280704`, War Across the Pacific, still offers “Declare armed neutrality: -500 supplies.” Its installed trigger checks Japan–USA war and absence of an India–Japan alliance, but does not exclude India already fighting Japan.

This is a real context error. It does not establish that an actual neutrality treaty was created. Historical Japan expertise flags also remain after withdrawal; those must not be erased wholesale, but later events must not mistake them for current partnership.

## 4. Conquest and timed holds: actual failure, uncertain engine cause

The latest save is `whereIndia_1942_May_9.eug`, saved 8 September at 23:57:39 local. Its full history contains 4,971 log records. The February–May run contains 41 Indian event/choice entries, of which exactly 23 are navigation selections.

Siam's actual sequence:

- 6 February: `9297000` starts the 21-day hold.
- 8–9 February: the old settlement board leads to `9282212` and an expired-terms exit, because live Siam remains a Japanese puppet and ally.
- 17 March, 22:00: the log explicitly records Thailand becoming part of India.
- 18 March: `9297001` ends the hold because Siam no longer exists.

The save has no dated record for `9297000` and no logged readiness/government outcome. The timed chain did not complete. However, the reviewers cannot prove from this alone that persistent events universally fail to record dates: that specific engine behaviour needs an isolated test.

The tests manually seed event dates and explicitly construct the expected detached-country state. See [timer assumptions](</C:/Users/Mohsin Dingankar/Downloads/India Ascendant/tools/test_aubm_siam_settlement.py:38>) and [supplied engine result](</C:/Users/Mohsin Dingankar/Downloads/India Ascendant/tools/test_aubm_siam_settlement.py:44>). These tests cannot establish actual timestamp persistence or alliance/puppet mutation.

## 5. Peace and government outcomes: demonstrated terminal-state errors

### A. Repeatable direct administration in B1

The new Peace Talks link to `9282212` checks that Siam is absent, Bangkok belongs to India, and `regional_settled_sia` is not set. The direct-administration action instead sets `regional_direct_sia`, but not `regional_settled_sia`. Neither parent nor leaf excludes the direct-administration terminal flag.

Therefore the same choice can repeatedly charge 7 dissent and 3 belligerence and queue occupation upkeep. It can also be followed by a different government outcome later. This is a confirmed script-level branch-closure bug, not merely a suspected engine problem. See [B1 parent gate](</C:/Users/Mohsin Dingankar/Downloads/India Ascendant/tools/build_aubm_cleanup.py:297>) and installed `46_regional_campaigns.txt:475–481`.

### B. Failed verification can strand a surviving Siam

Shared callback `9297202` clears only `ind_exit_sia_verifying` on failure. The earlier `ind_lib1_siam_break_pending` cleanup was deferred into success. If a recorded unrelated war ends while puppet creation is being checked, failure can leave the surviving Siam permanently pending. The normal offer/restart path excludes pending, and `9297008` cleans up only if Siam does not exist.

Every pending state needs a defined success, refusal, interruption and recovery exit. Withholding rewards is not itself recovery.

### C. Queued callbacks conflict with the documented format

The shared compiler inserts event-level success triggers into `9289852`, `9289905`, `9294015` and `9297005`, although installed engine documentation says queued targets should have no trigger/date/offset. Failure actions cannot help if an event-level success gate prevents the callback from being delivered.

This is a documentation-contract mismatch. Whether this executable ignores those gates or drops the callback remains an engine question. See [shared insertion](</C:/Users/Mohsin Dingankar/Downloads/India Ascendant/tools/aubm_shared_withdrawal.py:67>) and the installed engine's `Modding documentation/event commands.txt:702–707`.

### D. Earlier Japanese settlement sequencing also needs rebuilding

Japanese-route event `9281160` makes India leave its alliance with white peace, pays costs, issues peace, then queues foreign cessions three days later. The East Indies callback `9282000` still requires Indian control of Batavia. If peace returns that occupation, the callback lapses after India already paid and ended wars. The order and mismatched conditions are source-confirmed; the actual territorial consequence needs engine observation.

### E. War snapshots do not preserve wars

The new shared system records wars before engine mutations and checks them afterward. It cannot stop or undo an unintended peace. The registry contains 340 tags, adding 676 snapshot commands per withdrawal; some generated conditions span tens of thousands of characters. This is excessive duplicated complexity, not an established parser-size limit.

## 6. B1 navigation: fewer visible buttons, but not a coherent branch system

All 140 original Indian decision roots are hidden during human wartime play. A generous graph traversal from the three new roots reaches only 18 of them; 122 have no incoming scripted calls in the two Indian folders.

This is **not** a claim of 122 newly broken features. Some were already asleep or peace-only, and static reachability does not model automatic polling. Concrete missing direct wartime surfaces include army rebuilding `9270300`, airborne creation `9281803`, Japanese credit/carrier programmes `9281133–34`, independent anti-German entry `9281450`, Malaya petition `9289810`, Chinese sovereignty offer `9289850`, and Central Asian investment `9289916`.

Other parent links advertise outcomes after they are completed or before their real prerequisites hold. For example, Central Asian reconstruction omits peace and completion requirements at the link; Japan's investment link omits its terminal reward flag. The old War Cabinet is deliberately impossible (`atwar=yes` and `atwar=no`), not a functioning fourth menu.

## 7. What can be salvaged

Keep the save's armies, war, conquered territory and earned expertise. India is currently outside all alliances, fighting JAP/MAN/MEN/U87/U03 independently. The March autonomous-socialism programme coexisting with a sovereign diplomatic route is intentional separation of politics and alliance status, not by itself corrupt state. Do not silently reverse that selection.

Siam is now a post-annexation government problem. India owns all nine minimum release provinces. Do not force it back into a live enemy-withdrawal chain. The current post-annexation choices still need their terminal-state and engine-outcome checks repaired before recommending repeated playtests.

Keep the sampled early constitutional chain, useful authored country outcomes, progress information and free Cancel actions. Remove duplicate policy entry points, legacy cross-links back into unrelated tasks, inert moved-menu scaffolding, and completed choices. Rebuild the shared political/treaty transition rules and conquest-to-peace progression around explicit states with one owner per decision.

## Acceptance standard before another release

1. Inventory the full 1933-start event load and assign each political, alliance, conquest and peace event to an owning branch; mark keep, retire or rebuild.
2. Cover every available initial political and diplomatic path, including refusal, cancellation, changed wars, defeated/annexed targets and save/reload.
3. Prove that a committed choice closes competing outcomes, while intended upgrades within the same treaty remain possible.
4. Give every negotiation a recoverable terminal state and every completed outcome a shared parent/leaf exclusion.
5. Run tiny engine tests for timestamp holds, queued success/failure, peace scope, independence and puppet creation before scaling those patterns across countries.
6. Test parent-to-leaf reachability and settlement-to-parent returns, not just isolated predicates or keywords.
7. Verify initial and existing-save behaviour separately. B1 was installed after this May save, so the save is not evidence that B1 works in-game.

No full lifecycle sign-off is justified yet. This report is an audit result, not a deployment or a claim that the listed repairs have been implemented.
