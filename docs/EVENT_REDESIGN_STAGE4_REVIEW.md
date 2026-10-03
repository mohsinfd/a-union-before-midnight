# Fresh-campaign revision: navy, Nepal, industry and readability

10 September 2026. Staged work only; **not installed or engine-playtested**.
The player intends to start a new campaign. The existing installation and save
remain protected inputs, not targets for this revision. Old-save migration is
not the priority for the next playable build.

## 1. Battleship appropriations

These are event fees, not total ship prices. Normal daily production IC remains
payable; no hull is promised as already delivered or truly half-completed.

| Project | Old money / supplies | New money / supplies |
| --- | ---: | ---: |
| Arabian Sea Fleet | 650 / 1,500 | 450 / 1,000 |
| Bay of Bengal Fleet | 700 / 1,600 | 500 / 1,100 |
| INS Meru | 900 / 2,200 | 600 / 1,500 |
| INS Trikuta | 1,000 / 2,400 | 550 / 1,400 |

Meru and Trikuta retain the existing current-buildable battleship command and
requested 420-day first-hull schedule. The engine caps that request against
normal build time. Technology, model choice and production funding still matter.

## 2. Extra naval brigades

Removed **65 loose `add_brigade` grants** across the regional/oceanic fleets and
the two capital-ship contracts. These commands create deployment-pool fittings;
they were not extra attachments placed on each ship. The existing supported
attachment on each queued hull remains. Crew reserve checks are strengthened;
these are requirements for queue creation, not another manpower payment.

This change does not remove brigades or ships from an existing save. Other naval
procurement families outside modules 32/40 still require review.

## 3. Overlapping naval programmes

The Arabian fleet's earliest date moves from August to March 1937, still requiring
the earlier naval choices. Subsequent contracts use the elapsed age of a paid
authorisation. They do **not** inspect live queue completion or funding.

| Next opportunity | Elapsed interval | Reference build duration |
| --- | ---: | ---: |
| Bengal after Arabian | 225 days | 360 days |
| Oceanic orders after Bengal | 225 days | 360 days |
| Oceanic support after orders | 170 or 210 days, by programme | 270 or 330 days |
| Modernisation after Naval Board | 60 days | 90 days |
| Trikuta after Meru | 265 days | 420 days |

This is roughly 63–67% of each requested schedule. At earliest prompt choices,
the nominal path reaches Bengal in October 1937 and Oceanic orders in June 1938,
instead of the old October 1938 calendar floor. Cancelling a proposal costs
nothing; completing it closes its paid choice. Old orders without the new dated
record retain their original calendar access rather than receiving invented
elapsed progress. Native date persistence and queue behaviour remain untested.

## 4. Nepal: a merger that can become national territory

The reviewed scenario and revolt definition contain one Nepalese province:
Kathmandu, **1457**. No unrelated Himalayan provinces are added as Indian cores.

- Refusal opens a renewed offer after **360 game days**. Each renewed offer costs
  **650 money, 1,000 supplies and +2 dissent**; acceptance is 65%, refusal 35%.
  Another refusal permits another paid attempt after the same interval.
- A voluntary merger must actually remove Nepal and leave Kathmandu owned and
  controlled by India before its original benefits and integration timer begin.
  **1,080 game days** later, national status can be granted.
- After conquest/annexation, a separate integration project costs **1,500 money,
  2,500 supplies and +5 dissent**, followed by **1,800 game days**. Conquest alone
  does not grant an immediate core.
- If the integration period matures while the required territory is unavailable,
  a completion decision waits for the required ownership/control to return. It
  does not charge again or restart a timer.

The timer measures elapsed time, not uninterrupted occupation. Original cheap
offers cannot bypass the refusal/cooldown rules. Bhutan was unchanged in Stage4;
the later [Himalayan extension](HIMALAYAN_MERGERS.md) applies the same lifecycle
to Bhutan. New IDs 9398200–9398206 are functional negotiations/integration
follow-ups, **not seven extra flavour stories**. Inheritance, British-master
consequences and delayed delivery still need native verification.

## 5. Economic alternatives with distinct purposes

The six central development decisions, **9270200–9270205**, now distinguish
lasting factory capacity from research and near-term logistical resources.
No option's factory total is raised above its original total.

| Decision | Three revised factory totals | Important distinction |
| --- | --- | --- |
| Emergency reconstruction | 24 / 16 / 6 | Large industrial outlay; dispersed relief; business contract with ready stores |
| Transport grid | 8 / 5 / 4 | Trunk TC; ports and merchant fleet; frontier supplies/fuel |
| Steel and machine tools | 32 / 16 / 10 | State capacity; mixed firms and raw reserves; lower-outlay private contracts |
| Power development | 24 / 18 / 8 | Long-term river power; immediate coal reserves; local relief |
| Science | 10 / 0 / 6 | Applied institutes; research-only universities; defence laboratories and stores |
| Second national plan | 34 / 20 / 12 | Maximum industry; transport/fuel; research-led development |

The university option no longer **pays India 250 money** while also granting
factories and top research: it costs 350 money and concentrates on +4 research,
without factories. Second-plan industrial modifiers are now +5 / 0 / +1;
the balanced choice instead gets +5 TC and 1,000 oil. These are deliberate
opportunity costs, not claims of mathematically equal value in every campaign.

Paid actions recheck resources, current prerequisites, dates, completion and
ownership of funded sites. All retain existing branch/completion flags, unlocks
and construction caps. A free defer leaves the choice open. Other resource,
military and later economic boosts remain outside this six-decision revision.
Exact before/after command ledgers are emitted in `build/redesign/reviews.json`.

## 6. Added helper text and popup readability

The user clarified that the unreadable text was the extra explanatory helper
layer added in an earlier version, rather than the authored event story.

Evidence so far:

- Authored and installed custom event descriptions already obeyed the old
  500-byte description and 58-byte button budgets. None contained explicit
  section-sign colour controls. Those checks alone did not establish readability.
- Found **47 generated `Cabinet funding estimates` decision descriptions** in
  both source and installation, produced by `ensure_decision_visibility.py`.
  These are a plausible match to the reported helper layer, not a visually
  confirmed diagnosis of the colour failure.
- The revised naval/economic choices replace their old helper summaries and
  stale amounts. A final pass removes remaining automatically generated funding
  `decision_desc` overrides, restoring the engine's fallback to the event story.
  Explicitly manual descriptions and bespoke diplomatic/war warnings are kept;
  native option-cost/effect tooltips and all commands are unchanged. This removes
  the redundant layer, not the actual costs. No colour markup is introduced.
- Shortened eight opening/military/domestic descriptions and 21 overlong titles.
  The integrated audit also caught two overlong new Nepal buttons; both were
  corrected and covered by a regression test.
- `presentation-audit.json` now inventories **every staged custom event**, not
  just changed text: remaining legacy helpers, conservative word-wrap risks,
  authored button counts and large condition tooltips. These are review flags,
  not proof that every flagged popup is broken.

**The helper removal is implemented; native colour/overflow is not signed off.**
The engine documentation explicitly assigns `decision_desc` to the decision
tooltip. A separate read-only scan found no second custom explanatory UI field in
the installed events. A screenshot or isolated native inspection is still needed
to confirm the resulting contrast and layout. No game window was opened here.

## Verification and remaining work

The final integrated suite passed **171 tests**. The rebuilt manifest confirms
5,553 original authored IDs preserved, **457 existing blocks changed** across
all redesign stages, and 13 additions (six stories plus seven Nepal follow-ups),
for 5,566 staged custom events. No legacy generated funding helpers remain:
ten were replaced during the substantive rewrites and 37 were removed by the
final cleanup. No hard presentation-budget/control-code errors remain, but
1,368 conservative layout candidates still need disposition; this count does
not mean 1,368 confirmed broken popups. Protected inputs are unchanged and
`installable` remains `false`.

Focused tests cover naval costs/queues/timing, economy costs/closure, Nepal
negotiation/core sequencing, and presentation preservation/budgets. Independent
review checked the navy, economy and Nepal changes; its naval findings were
addressed before integration. Script tests do not certify native rendering,
queue persistence, diplomatic engine transactions or campaign balance.

This is not completion of the full event overhaul. Remaining global route/menu
replacement, installed safety reconciliation, coalition settlements and native
fresh-1933 testing still matter. The six small stories from the preceding pass
are unchanged; they are not represented as enough new campaign content. The
priority here is repairing substantial existing choices before adding more.
