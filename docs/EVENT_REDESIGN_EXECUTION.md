# Event redesign: execution specification and honest coverage

10 September 2026. This is an implementation workspace, **not a released build**.
The active installation and the 9 May 1942 campaign must remain untouched.

## What the player should get

India should be strong, interesting and readable. The challenge should come from
choosing objectives and sustaining wars, not finding the right administrative
menu or guessing which invisible political flag an event expects.

Domestic politics, diplomatic agreements and actual wars are separate. Choosing
a cabinet must not secretly choose India's future enemies. A treaty can offer
cooperation without joining its partner's wars. Formal alliance entry must say
that it joins the alliance's wars and must not permit switching directly between
rival alliances. Historical training and expertise are not revoked just because
today's diplomatic relationship changes.

Ordinary campaigns should depend on the current opponent, territorial control
and earned achievements. They must not require a national route, a charter, a
focus and a ledger activation before the same battlefield success counts.

## The small branch we actually need

```text
Current situation makes an opportunity relevant
  ├─ Leave it alone → no cost, no commitment, no forced next menu
  └─ Make a real choice → disclose cost, war/alliance effect and risk
       ├─ Diplomacy → wait for this offer's reply
       │    ├─ Accepted and still valid → apply the agreement once
       │    └─ Refused / obsolete → close this offer; honour any stated retry
       └─ Campaign → fight; progress follows battlefield facts
            └─ Terms earned → choose the country's postwar outcome
                 → verify the actual result → award once → close this choice
```

This is a target design, not a diagram of a fully implemented new engine.
Joining, leaving, releasing countries and ending coalition wars need native game
tests; checking flags afterward cannot undo an incorrect peace command.

## Work allocation

| Workstream | Responsibility | Deliverable |
| --- | --- | --- |
| Coverage | Every custom ID, including foreign replies and installed-only IDs | Per-event inventory, links, review dimensions and outstanding work |
| Diplomacy | Current commitments, action-level eligibility, delayed replies, cancellation, retries | Pure staged transforms and adversarial script tests |
| Settlements | One terminal choice per target; no concealed wider peace; verify governments before rewards | Shared rules across country families, then native transaction tests |
| Writing | Specific narrative and honest button labels based on actual commands | Explicit authored catalog, command-preservation tests |
| Integration | Keep authored, installed and staged versions distinct; prevent deployment before validation | Separate artifacts, source/save hashes, release blockers |
| Independent review | Challenge changes made by another agent | Regression findings and tests, not self-certification |

## Every-event acceptance record

`build/redesign/coverage.json` accounts for every event occurrence. Every record
has its country, title, actions, commands, direct incoming/outgoing links, calendar
and decision entry points, persistence, fresh-1933 sleep observation and structural
follow-up candidates. Foreign receivers are included: they can change India's
campaign even when India never sees their window.

Each event needs separate answers for:

1. **Purpose:** story, choice, reward, diplomacy reply, internal maintenance or
   compatibility only. A bureaucratic title is a candidate for review, not proof
   that an event can safely be removed.
2. **Entry:** what real situation makes it available, and whether a direct or
   delayed call can bypass its header. Action-level conditions protect effects.
3. **Choice:** exactly what changes, what is paid, and whether doing nothing is
   genuinely possible. No war order hidden in “open” or “record” actions.
4. **Ownership:** which specific pending offer owns a callback and its cleanup.
   An old response must not clear a newer offer or another partner's negotiation.
5. **Closure:** which choice is permanent; what can legitimately recur; what
   resets a refused offer; what happens if a country disappears or changes sides.
6. **Consequences:** wars, alliances, puppet relationships, territory, resources,
   modifiers, subsequent events, AI changes and any recurring occupation burden.
7. **Writing:** a concrete situation and stakes, short readable choices, honest
   costs and uncertainty. No fictional territorial transfers or guaranteed
   governments where the implementation merely attempts them.
8. **Proof:** structural checks, state-sequence tests, independent review and
   engine evidence recorded separately. No engine proof is inferred from a unit
   test that manually supplies the expected diplomatic outcome.

Final dispositions are keep, rewrite, retire or pending. A partial fix to one
dimension does **not** mark the whole event complete. Unreviewed IDs stay pending.
Sleeping IDs are not deleted automatically: old saves may still reference them.

## Implemented in the first staged pass

- Diplomacy: current-state locks on Indian alliance-command leaves; initial
  Allied conference replay exclusions; selected Allied/Japanese reply checks;
  the full Japanese sphere purchase checks its full resource bill; existing
  Japanese influence is preserved; opening the southern ledger no longer
  declares wars.
- Settlement closure: the shared rule covers all 10 regional and 210 global
  constitutional-settlement entries. Direct-rule records and sovereign/protected
  records backed by the actual government close the original choice; direct administration records closure;
  immediate returns to the old ledger are removed where present; a no-effect
  exit is available. These are template-level closure fixes, **not 220 fully
  redesigned or engine-tested peace chains**.
  A claimed government that never appeared does not permanently lock recovery;
  legacy `settled` alone is not proof of a constitutional outcome. Release costs
  and rewards still need verified transaction ordering.
- Narrative: an explicit first-batch catalog rewrites individually inspected
  event text. Its tests require command and trigger preservation. Other text is
  not represented as rewritten merely because a keyword scan visited it.
- Cooperation: staged corrections connect selected accepted bilateral partners
  to their follow-up and repair the eastern-cooperation retry contract. Exact
  implemented records and limitations are emitted by the transform.
- Inventory and staging: all authored custom modules, a separate installed
  inventory, installed-only ID reconciliation, per-event dimension records,
  unchanged-input checks and a non-installable manifest.

The generated `STATUS.md` and `manifest.json` contain exact counts from the actual
run. They take precedence over estimates in conversation.

## Second staged pass

See `docs/EVENT_REDESIGN_STAGE2_REVIEW.md` for the implemented campaign-access,
partner-crisis and foreign-reply changes, plus the stock surrender bridge.
The 40 installed-only definitions now have explicit component dispositions in
`reconciliation.json`; classification is not yet a completed safety-code port.
All changes remain staged and non-installable.

## Third staged pass: optional new Indian content

At the user's request, six small India-specific story decisions are now included
alongside the continuing cleanup. They add no national route, follow-up chain or
permanent bonus. See `docs/EVENT_REDESIGN_STAGE3_REVIEW.md` and the generated
`build/redesign/INDIAN_STORIES.md` for their seasonal availability and exact text.
The remaining independent great-power reply families also receive staged
ownership/current-state corrections. Native behavior and old-save migration are
not signed off.

## Remaining implementation, in order

The fifth staged pass is documented in
`docs/EVENT_REDESIGN_STAGE5_REVIEW.md`: bounded navigation retirement, Japanese
seniority and corridor replies, fourteen actual-state regional opportunities,
and the shared minor-withdrawal unit. These are partial implementations of the
remaining work below, not completion of those whole workstreams.

The player has now chosen a **new campaign**, not save continuation. See
`docs/EVENT_REDESIGN_STAGE4_REVIEW.md` for the naval, Nepal, core-development and
presentation revision. Protect the old save, but do not make its migration the
critical path for the fresh-game release. More flavour is secondary to finishing
the functional event overhaul.

1. Reconcile every installed-only event and every existing safety transformation.
   The authored staging tree is not a replacement for the installed B1 overlay.
2. Finish current relationship checks for all foreign offer and response families,
   including same-proposal retries, delayed delivery and vanished countries.
3. Replace global route/charter/focus gatekeeping with actual situation checks.
   Preserve earned milestones and sensible local political choices; do not
   delete flag references indiscriminately.
4. Rebuild country exit/peace/government creation as explicit transactions. Siam,
   Nanjing and Indochina must use the same tested rule where their engine states
   are equivalent. Do not duplicate a broken country-specific exception.
5. Replace or prove hold timers. Define uninterrupted control, interrupted holds,
   restarting and save/load behavior; do not infer native dates from simulated
   event history.
6. Remove manual progress-recording and navigation loops after their real effects
   have been moved. Do not retire reward content merely to make the panel small.
7. Complete the prose pass by family and by unique event. Each generated family
   needs an authored rule and per-instance verification; substantive outcomes
   still need specific descriptions, not generic “framework” substitutions.
8. Complete fresh-game and continuation coverage. Old agreements and rewards
   must survive; stale offers must close without rewriting past wars or choices.

## Minimum engine test matrix before release

| Case | Required result |
| --- | --- |
| New 1933 game, first month | Readable opening; no accidental internal-menu cascade; stable load/save |
| Existing independent Japan war | No Japanese alliance reward or cooperation offer while hostile |
| Treaty → formal alliance | Explicit inheritance of alliance wars; no free rival-alliance switch |
| Delayed reply after withdrawal / new offer | No stale reward; no cleanup of someone else's offer |
| Refuse and retry | Retry happens when advertised and can actually execute again |
| Cancel every actionable menu | No resource charge or hidden commitment; no stranded transaction |
| Siam alive as Japanese puppet/ally | Correct country detaches; India's Japan war continues |
| Siam annexed | Legal release/puppet outcome verified before success is recorded |
| Nanjing / Indochina equivalent states | Same verified exit rule; no separate patch assumptions |
| India simultaneously fighting Japan and USSR | One settlement cannot silently end the other conflict |
| Direct administration twice via different entry points | Second original choice is unavailable; no duplicate cost |
| Hold interrupted, restarted, saved and reloaded | Correct elapsed control requirement and single reward |
| Peace/puppetry fails in engine | No false victory reward; clear recovery path |
| High event load and long tooltips | No crash, inaccessible action or oversized nested-condition tooltip |

No game is launched by the staging builder. Native verification needs a separate
isolated test session; it must not advance the user's campaign or bring the game
forward without permission. Until those checks pass, the installed version and
save remain unchanged, and this work is not published as a playable alpha.

## Reproduce the staged artifacts

From the repository root:

```powershell
python -m unittest discover -s tools -p "test_aubm_redesign*.py"
python tools/build_aubm_redesign.py
```

`--installed-root` optionally adds read-only installed-module reconciliation.
`--save` fingerprints a named save before and after the run; it does not modify
or migrate that save. Output is constrained to `build/redesign` or its children.

Do not run the old cleanup installer against this intermediate tree. No
deployment or migration is part of this specification's first staged pass.
