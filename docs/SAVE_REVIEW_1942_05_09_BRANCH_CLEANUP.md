# May 9 save review and B1 navigation cleanup

Reviewed `whereIndia_1942_May_9.eug`, saved September 8 at 23:57 local time. This is newer than the May 1 autosave. No save content was edited.

## What actually happened

The February 1–May 9 run contains 41 Indian event/choice log entries. Twenty-three are menu-navigation selections; an additional menu selection on March 8 actually chooses autonomous socialism. No log entry is literally named “internal”: this count classifies the navigation entries by function.

On March 8, multiple empty Peace Talks pages led into the global ledger, coalition menus, strategic compacts, and autonomous socialism. On March 9 the previous route contract was invalidated. On March 10 the Socialist War Charter was selected. The save now has a sovereign diplomatic route and a Soviet autonomous political programme. India is not allied to Japan or the USSR. India is still independently fighting JAP, MAN, MEN, U87 and U03. There is no new Japanese alliance entry recorded in this run. Several Tokyo-labelled menus were presented, which made this unnecessarily confusing.

Siam: the 21-day hold started February 6. The old regional menu offered a settlement on February 8 and only an expired-terms exit on February 9 because Siam was still an enemy puppet. The new readiness/government events are absent from the recorded history. Thailand became part of India on March 17 at 22:00. The hold ended the next day because Siam no longer existed. India now owns every minimum province required by the installed Thai revolt definition, including Bangkok and Chiang Mai. Restoring a government is now a post-annexation choice, not a live enemy withdrawal.

The save's dated-event table contains 18 stock event records and no Siam hold start record. Therefore the timestamp-based maturity condition has no surviving record to use. This is a separate runtime/timer defect; B1 does not claim to repair it or other long-war hold timers.

## B1 changes

- Three wartime roots: Campaigns, Peace Talks, War Economy. The old War Cabinet root is closed during war.
- Campaigns goes directly to the China, Japan, Indochina and Soviet progress pages, conditional on actual wars.
- Peace Talks goes directly to the current settlement stage. Thailand gets a post-conquest government entry. Existing country/war/consent/completion checks remain on the actual choices.
- War Economy offers budget, debt repayment, reserve call-up, replacement pool, replacement training and long-war finance. Inapplicable choices remain hidden.
- The legacy coalition choice pages cannot execute political programme/alliance changes during war. Earned Soviet-derived bonuses and the March choices are not rolled back.
- Old numbered page IDs remain as compatibility redirects; they no longer contain lists of more lists. No new event IDs are added.

## Immediate next step

After restart, use the B1 badge and load `whereIndia_1942_May_9.eug`, not the older February copy. Open Peace Talks, then Thailand's post-conquest government. The existing protectorate option costs 4 dissent and attempts to restore Siam as an Indian puppet; the independent-government and continued-administration alternatives remain visible. This engine transition has not been playtested by the agent. Do not mistake opening the page for choosing the outcome.

## Still required before a full gameplay sign-off

- Replace and engine-test the broken timestamp-dependent hold mechanism across Siam, China, Indochina, Japan and the Soviet campaign.
- Audit all automatic political programme introductions and their one-time mutual exclusions, not only the manual coalition menus.
- Verify post-annexation government creation and reward timing in the actual engine.
- Review the remaining native campaign progress pages and off-route objectives. B1 is a bounded rescue of the current menu flow, not a claim that all thousands of events have been redesigned.
