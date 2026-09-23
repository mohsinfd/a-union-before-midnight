# Cold route audit: continuation, 10 September 2026

Read-only continuation by three separate reviewers. Installed build remains B1; the latest actual campaign remains the 9 May 1942 save. No gameplay code, installation or save was changed. This report records new findings, not implemented fixes.

## Japanese branch

Reviewed the 1935 channel, conference `9281100–1124`, China policy `9281130–32`, investments/seniority `9281133–37`, southern activation `9281140–46`, settlement `9281150–69`, formal entry/withdrawal `9281914`, and selected later partner-crisis events.

1. `9281135 → 9281136`: a seniority reply arrives three days after requesting it. India can withdraw during that interval. The reply checks absence of war but not the continuing partnership, so it can award partnership rank and install partnership AI after withdrawal. If war interrupts it, the fallback does not clear the pending review. Both are source-level lifecycle defects.
2. `9281120`, “Buy full sphere,” deducts 1,500 money, 3,000 supplies and 1,500 oil but lacks those resource conditions. The initial proposal only requires 350 money/600 supplies. The exact engine handling of insufficient stockpiles is untested; the missing affordability gate is established.
3. `9281140` presents activation of a southern command ledger, but the action can declare wars on ENG/U05/HOL/AST when they are fighting Japan. Informational navigation conceals consequential war orders.
4. Formal Japanese entry in `9281914` uses `setflag which = ind_aubm_jp_influence` without a numeric value, overwriting influence with the documented default of 1 despite preserving other rank flags.
5. `9281165` records settlement completion after conditional independence/puppet commands without verifying the requested governments actually exist in the intended relationship.
6. Advertised proposal and seniority retries reuse response events that omit `persistent=yes`. This is a repeatability contract risk requiring an engine test, not a demonstrated universal hang.

Keep the distinction between separate-command compact and formal alliance, disclosed foreign response choices, and meaningful country outcomes. Rebuild transaction, withdrawal, retry and completion rules. Paid reversal of a commercial-only policy is explicitly disclosed and was not classified as a bug merely because it permits a later change.

## Allied branch

Reviewed early London approach `9280950–52`, all conference request/response/outcome nodes `9281200–16`, treaty closure `9281935/36`, route reconciliation, and the Eastern focus through its postwar congress.

The Cabinet doorway `9281919 → 9281200` does not exclude an existing compact or completed negotiation. Those exclusions exist on the conference event header but not its actionable choices. After Commonwealth ratification `9281205` awards supplies, `9281935` clears negotiating flags while retaining the treaty, allowing the doorway again. Another selection can stack a naval compact flag without clearing Commonwealth. Several response paths also contain supplies or naval organisation rewards.

Missing entry/leaf exclusions and contradictory treaty flags are source-confirmed. Whether every proposed repeat executes in this executable still depends on called-event behaviour. A deliberate upgrade or renegotiation should be distinct from replaying the initial award.

The sampled Eastern focus `9283210 → 9289505 → 9289509 → 9289513 → 9289517 → 9283270` has explicit milestone/completion flags; intermediate arrows include flag-based automatic progression, not only direct calls. The postwar congress correctly requires peace and records a global one-time congress completion. The other focus variants were inventoried, not fully traced.

## German branch

Reviewed early Berlin approach `9280953–55`, main negotiation `9281300–13`, Persia/Afghanistan/Xinjiang corridor request/reply/refusal/reopening chains, and the Eurasian focus through `9283271`.

1. Crisis `9289541` marks the German partner crisis resolved when selecting “Seek formal entry,” then opens a Cabinet page. B1 blocks the actual German joining action during war. The player can therefore consume the crisis while accomplishing nothing; Cancel does not undo that premature completion. Several Allied/crisis review choices share this intent-versus-completion pattern.
2. German requests/reopening timers are persistent but many response/outcome events are not. Example: `9281314 → 9281320 → 9281332 → 9281339 → 9281314`. Confirm second-attempt execution in-engine before relying on the advertised retry.

The sampled Eurasian focus and once-only congress contain useful milestone and terminal checks. Many old German/Allied campaign events are asleep in fresh 1933: 48 of 65 events in module36 and 40 of 78 in module37. Their raw presence must not be advertised as live new-game content.

## Soviet and independent integration findings

The reviewer confirmed three additional source defects:

- Independent anti-Japanese cooperation `9281455` receives a permanent compiler completion flag. Refusal `9281459` promises another review next year via `9281446`, but that reset clears request/deferral flags and never clears the compiler's completion flag. The advertised retry cannot reopen the original decision. B1 also removes its human wartime decision access despite its Japanese-war prerequisite.
- Actual accepted independent bilateral partnerships set `ind_v43_nam_china/siam/persia/afghan_partner`. The later bespoke partner-war trigger `9289661` does not consume these records and instead uses other pact/alliance flags. A historical general pact can qualify follow-up without the relevant bilateral acceptance, while an actual accepted bilateral partner alone does not qualify. The systems disagree on what a partner is.
- Non-Aligned conference `9281501` sends offers over 2–39 days, but sampled Siam/Persian/Afghan reply chains do not recheck intervening war, puppetry, political change or cancellation before recording partnership outcomes. The Soviet eastern-cooperation replies also lack the obsolete-response checks present in the initial Moscow compact.

Coverage included initial Moscow programme/counteroffer/refusal `9281400–14`, the three corridor alternatives, eastern cooperation `9281455–59`, independent doctrine/partner replies `9281500–37`, and Soviet/independent culmination and congress predicates. The initial Moscow response guards and one-time congress structures are useful patterns to retain. Much of the old military/settlement tail is retired: 36 of 83 Soviet-module events and 44 of 90 independent-module events are slept by the retirement system. The current deep Soviet outcome still depends on the unverified hold mechanism before its substantive peace, successor-state and lasting-investment checks.

## Loaded-reference and test coverage

The coordinating reviewer attempted all 157 event files referenced by the current save. Across 156 successfully parsed files there were 7,603 unique event IDs, no duplicate definitions and no unresolved `event`/`trigger` command targets. The audit parser rejected the stock `AI_ministers.txt` with a brace error; this is a limitation of this scan, not a confirmed game-engine parse failure. No completeness claim is made for that file.

The reference scan found B1's War Economy linking to `9270503`, an event listed asleep in this save. A complete reachability test needs to include sleeping, event history, current conditions and queued calls—not just whether an ID exists.

Existing route validators largely inspect authored source structure, flag/keyword presence and expected generator output. These remain useful checks, but do not demonstrate native execution, retries, cancellation or whole-campaign exclusivity.

## Architectural assessment: fewer global branches

The findings favour removing global route/charter/focus dependencies as the gatekeeper for ordinary gameplay. Politics, diplomacy and current wars should be distinct facts, not several overlapping interpretations of a selected route.

Use actual alliance/puppet/war/territorial state, plus a small number of explicit records for non-engine treaty agreements, pending offers, cooldowns and completed outcomes. Offer country objectives and settlements when those facts make them relevant. Preserve short local choices—accept/refuse, separate command/formal alliance, independence/protectorate/direct administration—without forcing the entire campaign into one preselected event tree.

Historical expertise can remain earned after diplomacy changes. Current partnership benefits and foreign replies must recheck the current relationship. Every permanent outcome must close its own original choice; later reversal, if supported, should be an explicit new decision with disclosed consequences.

This is a recommended design direction, not permission inferred to implement it. The continuation remains broad branch sampling; not every focus variant, territorial writer, foreign AI interaction or native engine transition has been certified.
