# Third staged pass: something new for India

10 September 2026. This is staged content and cleanup, **not an installed or
engine-playtested release**. The existing campaign is not advanced or modified.

## Six optional Indian stories

The user requested fresh Indian content alongside the cleanup. A dedicated
content agent implemented six small stories; another agent independently
reviewed their conditions, choices and balance against the latest save.

| Story | When offered | Choice |
| --- | --- | --- |
| The Workshop After the Whistle | January–February, at peace | Buy repair kits, or sell surplus stores to support the evening workshop |
| A Map Folded at the Pass | March–April, at peace | Prepare fuel caches, or buy pack supplies |
| Night Shift at the Railway Yard | May–June, at war | Use money and metal for a larger supply delivery, or pay more for a smaller supply-and-fuel delivery |
| Canvas Before the Rains | July–August, at peace, with dissent | Release depot stocks or pay civilian suppliers for relief |
| The Cargo Before Dawn | September–October, at war | Charter a fuel cargo or a field-stores cargo |
| A Bed on the Homeward Train | November–December, at war | Fund rehabilitation for eight manpower, or support families to reduce existing dissent |

All begin in 1934 or later. India must exist and not be a puppet; alliances are
allowed. Each requires an affordable option. At most one story is offered in a
month, so adding this content to a future compatible continuation cannot expose
all six immediately. A missed season can return the following year if the story
is still unfinished and its peace/war conditions apply.

These are **optional one-time stories**, not a new political path or a management
board. “Not now” is free and leaves the story open. Either substantive choice
permanently closes that story's alternatives. The events introduce no war,
alliance, peace, puppetry, follow-up chains, units or permanent modifiers.

The resource rewards are deliberately modest. Most of the new stories are
procurement tradeoffs, with medical recovery and relief adding some variety.
This is a small narrative refresh, not a claim to have built a new campaign or
solved the mod's broader manpower/supply balance. Native enjoyment and pacing
still need a playtest.

### What fits the current campaign?

In the reviewed 9 May 1942 wartime state, the new candidate is **Night Shift at the
Railway Yard**. Its alternatives are:

- Spend 200 money and 300 metal for 700 supplies.
- Spend 350 money for 350 supplies and 100 oil.
- Leave the offer open without paying anything.

The save's observed money is sufficient for the carriers choice. The preview is
not an assertion that the content is installed, that native UI visibility has
been demonstrated, or that the older save is migrated for the wider redesign.

Read the exact staged descriptions, seasonal tooltips and buttons in
`build/redesign/INDIAN_STORIES.md`. It is generated directly from the staged
scripts, not paraphrased concept art.

## Loading and safety

New IDs are explicitly limited to **9398100–9398105**. The content agent checked
them against 6,825 authored/game TXT files, including stock and installed mods;
the builder also checks for collisions with the active installed custom corpus.
The six definitions are appended to the existing loaded
`32_national_consolidation.txt`, avoiding a new-module include dependency in old
saves. This does **not** migrate the rest of the redesign's pending callbacks.

Every paid action repeats current context, affordability and its one-time closure
condition. Persistent event definitions allow free cancellation without silently
consuming the event. The generator rejects missing/tampered marked story bodies,
and limits descriptions and buttons to the staged presentation budgets.

Existing event art is reused and its installed bitmap was verified. No new
visual assets were generated or changed by this pass.

## Cleanup continued in parallel

The four remaining independent great-power reply families—Britain, America,
the Soviet Union and Japan—now have paired dispatch/reply checks and explicit
offer/selected-answer records. This pass changes dispatch `9281501` and the
sixteen reply events `9281520–35`.

An old acceptance cannot consume its country's pending counteroffer. Delivered
replies recheck current wars, sovereignty, commitments, affordability and the
named third countries. Explicit withdrawal and obsolete-reply handling clear
only the relevant pending records. Existing effects and delays remain.

Japan's China-exclusion bargain cannot be chosen while an accepted, allied or
pending Chinese partnership contradicts it. Enforcement against future choices
is still an explicit unresolved item, not a promised finished system.

Native delivery, same-offer retry generations, vanished-country recovery,
elapsed-time expiry, undoing earlier foreign effects and old-save token migration
remain unverified or unfinished. The stage must not be copied into the live game.

## Verification

The full integrated suite passed all **130 tests**, including the content agent's
13 tests and the great-power reply agent's 12 tests. Independent review found no
blocking new regression. The rebuilt `EVENT-REDESIGN-STAGE3` manifest confirms
5,553 original authored IDs preserved, 374 existing event blocks changed across
the staged redesign, and six additions: 5,559 staged custom events in total.
Protected inputs are unchanged and `installable` remains `false`.

The existing 5,553 authored custom IDs must all survive; the builder permits only
the six explicitly registered additions. No installation, game launch or GitHub
deployment is performed by the staging builder.
