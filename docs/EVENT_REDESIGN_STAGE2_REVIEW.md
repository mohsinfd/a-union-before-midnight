# Event redesign: second staged implementation

10 September 2026. **Not installed, not engine-playtested, not a playable release.**
This continues the first staged pass; it does not replace the user's campaign.

Final verification: **105 script tests passed**. The rebuilt stage preserves
all 5,553 authored custom IDs and changes **358 custom event blocks cumulatively**
(279 in Stage 1), plus stock Japanese surrender event 2011028 in a separate
staged file. All 40 installed-only IDs have component dispositions, with no
unexpected/missing IDs or reassessment flags. The builder verified that authored
sources, installed custom modules, the installed stock input and the named
9 May 1942 save were unchanged. No native engine test was run.

## Gameplay changes implemented in staging

### Campaign objectives follow the war, not a selected route

The campaign-access pass inspects 61 explicitly listed lifecycle events and
changes 56 of them in `43_wartime_settlements.txt`. It replaces 309 exact old
access predicates, not arbitrary flag strings throughout the mod.

The covered families are Siam, Nanjing, Indochina, the Japanese home islands and
the deep Soviet campaign, including their selected foreign replies and failure
branches. Actual wars, territorial requirements, consent, costs, sustained-control
requirements, pending offers and completed outcomes remain. Friendly alliances
no longer prevent these ordinary enemy objectives; India must remain sovereign
and cannot be allied to the relevant opponent.

Their war-observation events no longer require opening a ledger to opt in.
This removes an entry requirement, **not** the unresolved internal notices or
the need to validate hold timers in the executable.

### Reviewing a war no longer spends the political choice

The five Allied, German, Soviet, Japanese and independent partner-war crises
become player-invoked decisions. Only the relevant current relationship and war
can qualify; they no longer need a national route. They retain real support
costs and rewards, and closed outcomes remain closed.

Opening an alliance/withdrawal/war review no longer sets a completed-choice or
intent flag. A free exit closes the decision without effects. The five linked
war-review pages use current relationships instead of requiring the earlier
intent flag or an old route contract. Their return buttons close the page rather
than reopening another board. Actual war declarations remain in the existing
downstream confirmation/execution chain, which is not certified by this pass.

The modern independent bilateral agreements also qualify in the linked review:
Chinese/Siamese partners can lead to the Japanese review, and Persian/Afghan
partners to the Soviet review. An independent partnership does not imply India
has joined any war.

### Foreign replies recheck the world before awarding outcomes

The reply pass changes 25 events: eastern Soviet replies `9281456–59`, the
independent outreach dispatch `9281501`, four regional reply families
`9281502–17`, and their protocol callbacks `9281536–39`.

Replies check current hostility, sovereignty, relevant commitments and their
own pending offer. Fixed costs require sufficient resources. Explicit withdrawal
or an obsolete offer clears only its own pending state; it does not cancel
another country's negotiation. The regional system adds country-owned pending
records, not new global routes or event IDs.

Soviet eastern replies additionally require a continuing Indian, Chinese or
Soviet war with Japan. China-bilateral choices require an existing sovereign,
nonhostile China. The earlier reward commands and nonjoining alternatives remain.

Important continuation limitation: an old queued independent offer lacks the new
pending record. These saves have **not** been migrated; do not copy this staging
tree into the active installation.

### Stock surrender protection follows the new access rule

Removing the opt-in requirement exposed a dependency: stock Japan surrender
`2011028` had previously protected Indian home-island control only when that
opt-in flag was set. The separate staged stock bridge removes that flag from the
exact existing protection expression, while preserving the Indian war and
home-island-control conditions, every stock outcome command and a harmless
fallback. Header and action guards are updated together.

This file is emitted under `staged-stock`, from the actual installed stock input,
only when the builder receives `--installed-root`. It is not installed. Other
stock and coalition-safety components still need explicit reconciliation.

## Independent review findings corrected

- Modern partner agreements qualified for the crisis but not the following war
  review. The menu now uses the same country-specific accepted-partner facts.
- Eastern Soviet replies could award anti-Japanese cooperation after all the
  qualifying Japanese wars ended. They now close the obsolete offer instead.
- Route-free home-island access initially bypassed the opt-in-dependent stock
  surrender safeguard. The staged stock bridge follows the new access rule.
- Route removal shrinks some already oversized legacy predicates. Integration
  testing permits shrinkage but rejects new growth beyond the existing size;
  those retained oversized predicates remain flagged for native tooltip review.

## Installed-only code is accounted for, not silently deleted

`reconciliation.json` gives every one of the 40 installed-only definitions an
explicit proposed component disposition and dependencies:

- Four menu roots need replacement or callable compatibility exits.
- Twenty-nine moved-menu stubs retain compatibility IDs without proactive surfacing.
- Three dockyard state events must travel with their modifier/migration logic.
- The old build notice must be replaced without losing historical initialization.
- Three U87/Indochina/Siam verification callbacks must travel with their complete
  withdrawal and reward transactions.

The report also identifies nine safety components, including coalition peace,
Japanese hostility checks, debt caps, decision prerequisites, dockyard state,
presentation/AI behavior and stock Japanese/Chinese settlement safeguards.
Classifying these components does not mean they have all been ported.

## What remains

Full national-route removal, the remaining event prose, great-power independent
replies, same-offer retry generations, vanished-country recovery, government and
reward ordering, hold timers, old-save migration, and native peace/puppetry tests
remain open. No custom event has full lifecycle/engine signoff.

The final `build/redesign/manifest.json` and `STATUS.md` record generated counts,
toolchain hashes, protected-input checks and release blockers. This stage adds
no custom event IDs and runs no game process.
