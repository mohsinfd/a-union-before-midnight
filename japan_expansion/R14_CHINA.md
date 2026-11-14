# China in R14

Japan must defeat the Chinese army as well as capture its cities before imposing a decisive settlement.

| Settlement | Requirements and result |
| --- | --- |
| Decisive victory | Japan controls Nanjing, Shanghai and Chongqing; China has lost at least 55% of its national territory and 65% of its victory points; the defeated national government has **60 or fewer surviving deployed land formations**. Puppet and independent terms remain separate choices, with the existing Shanghai base alternatives. |
| Limited peace | Japan controls Nanjing, Shanghai and Wuhan; China has lost at least 35% of its national territory. Chinese acceptance is still required. China remains independent, keeps its army and grants access. Shanghai is the sole possible Japanese territorial concession. There is no puppet reward. |

The decisive army and victory-point tests apply to Nationalist China or an already-existing hostile Chinese successor. Own troops serving abroad count. Foreign expeditionary troops, dormant templates and construction orders do not. The engine's documented daily own-force statistic is used, so a threshold crossing may take one daily update to appear. All land types count, including headquarters and garrisons. The three objectives must be Japanese-controlled; allied control alone does not qualify or authorise taking an ally's land.

Clean Blood and Iron's 1933 Nationalist China file contains **143 deployed formations** (117 infantry, 19 militia, six headquarters and one cavalry), plus **85 dormant formations**. Sixty survivors requires eliminating roughly 58% of the deployed starting army, before accounting for wartime construction and activation. This is materially harder than the former city-and-territory settlement. It does not require destroying every Chinese unit. The existing demanding land and victory-point requirements remain in force.

## Preserving the postwar army

The old army replacement is removed. It could wait several years until a small puppet army grew past 96 formations, then delete the entire deployed army and replace it with dormant templates. R14 preserves survivors and subsequently built troops. It creates no replacement 96-division army and applies no new movement locks.

The same existing event ID now records a one-time assessment regardless of army size, war status, ownership of Nanjing or independence. A later war or army growth cannot reopen it. Old saves with already-locked, identifiable B1 formations retain their existing unlock waves. Those waves only unlock their recorded unit identities; they never remove troops or generate replacements. Independent China also releases its surviving known locks.

## Stale and inherited events

The decisive CHI/U87 receivers recheck the army, territorial, victory-point and city conditions before peace or a national tag change. A delayed callback cannot turn a recovered Chinese position into a decisive surrender.

The material actions also recheck their conditions when executing commands, using a private receipt for each action. This covers a player leaving an event open while conditions change. The receipt allows a valid action to finish after its own peace or flag commands change the original conditions.

Limited peace now requires a live offer and recorded Chinese acceptance. Lost objectives cancel negotiations with a 90-day delay; stale acceptance or confirmation cannot impose a peace. Unrelated Japanese wars continue.

The installer guards both B&I offer roots and their directly triggered receivers/callbacks: **2011012, 2012017, 2011013, 2011014, 2011015, 2012018, 2011016 and 2011017**. Active Japan Rising uses its own settlement chain. A stale stock callback has only an inert acknowledgement. Non-Japan-Rising campaigns retain the original actions.

A wider source scan also identified Japan's defeat/surrender events (2011018, 2011028, 2011037 and 2011030), the early Sino-Soviet intervention settlement (2181014), and 1914-only paths. These are distinct from Japan imposing a Chinese puppet surrender and are retained. In particular, a Japanese defeat must still be possible.

## Installation and checks

- Call `r14_china.apply()` after the R13 appenders and before final integrity/equipment/player-copy passes.
- Call `r14_china.install(source, target, read, write, parse, serialise)` **after** `patch_baseline()`; it preserves the builder's other native-file fixes and is idempotent.
- No event IDs are allocated or renumbered. All 1,822 baseline IDs remain intact. Unit upgrade/model IDs are untouched.
- Run `python r14_china_review.py`. All 13 offline tests pass. The suite reproduces the old delayed-wipe eligibility, checks final compiled decisions at 60/61 survivors, dormant/expeditionary cases, successor China, delayed wartime assessment, independence, stale receivers and cached selections, limited peace and repeated native-file patching.

This is a source and scripted-state audit. The game is not launched, so actual engine delivery and the difficulty of reaching the new surrender threshold remain playtest observations.
