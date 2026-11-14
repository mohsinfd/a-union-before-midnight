# Japan Rising R14

R14 repairs the complete source/design review of R13.1, rather than only its first two findings. Start a new 1933 campaign. Old IDs are retained, but this revision does not migrate saved event histories or already granted modifiers.

| Review finding | R14 change |
|---|---|
| Delayed Chinese army destruction | The postwar assessment closes once, at any army size. No whole-army deletion or replacement army. Existing survivors remain. |
| China surrendered on cities alone | Decisive peace now also requires at most 60 surviving own deployed formations, including expeditionary forces. Existing three-city, 55% territory and 65% VP requirements remain. Limited peace remains a different, lesser settlement. |
| Formal Axis entry strands separate peace | Pending talks block formal entry. External alliance/war changes suspend talks cleanly; transfers already completed are retained and no false victory is awarded. |
| Japanese-only objectives | Actual allied victories can count. Independent allies must consent before their enemy-owned occupations enter Japanese allocations. Their own sovereign land is excluded. |
| Giant coalition tooltips | Compact visible conditions; hidden receivers recheck current control, ownership and alliances before effects. |
| Hawaii choice after US acceptance | Japan states the terms first. Returning Hawaii improves relations and offers a five-year pact. Retention needs stronger leverage, worsens relations and gives no pact. |
| Four historic carrier losses imply permanent weakness | Negotiations also check America's current carrier strength. Rebuilding its fleet matters. |
| Weak 1945–50 continuation | Connected civilian/military recovery, Chinese/Indian postwar agreements and US commerce/Hawaii consequences with finite investments, elapsed time, refunds and renewed-war checks. |
| New specialists missing from full-stack arithmetic | All seven active specialist classes and three attachments now have coherent comparisons including research, programme choices, date-eligible ministers, sliders and gearing. Political restrictions are relaxed as an explicitly generous stress bound. |
| Excessive Matsu discount | Base IC and time are each 80% of the parent, replacing 75%/65%. Full manpower remains. ASW and fuel advantages, weak surface armament and shorter range remain. |
| Domestic fuel crowds out southern strategy | A large 12,000-oil batch takes 45 days plus 90 days recovery; small/standard recovery remains 45 days. Costs, low-stock limits and exact cancellation refunds remain. Domestic fuel priority still trades away mineral output. |
| Large India skips partner land AI | Released/puppeted India receives the intended land-defence AI regardless of IC, without extra startup units. |
| Obsolete American emergency infantry | The two finite six-division waves use the newest researched, date-appropriate 1936–48 equipment. Full-strength heals use the exact same mutually exclusive conditions. |
| Cached selections can bypass conditions | Repaired transactions use private execution receipts and fresh command-time guards. Repeat/reload, changed-front, funding and interruption cases are tested offline. |

The existing unique artwork, first-issue unlocks, normal research upgrades, 31 small island detachments and shipping allowance remain. Enemy transport protections from R13.1 remain; the engine can regroup fleets, so universal escorts are not guaranteed.

See R14_CHINA.md, R14_PEACE.md, R14_AFTERWAR.md, R14_CONSTRUCTION_AUDIT.md and R14_COLD_AUDIT.json for gates, cascades and evidence. R14_REVIEW_SOURCE.json retains the original review and reviewed commit.

No game launch is part of this work. Offline checks establish source/installed parity, documented-command logic and tested state transitions. Startup, real tooltip rendering, actual Hard AI operations, combat balance and long campaigns remain player tests; there is no honest guarantee of a days-long crash-free campaign without running it.
