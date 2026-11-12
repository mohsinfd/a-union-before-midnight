# R11.1 final player-copy review

The final `player_copy.apply()` pass rewrites 356 of the 1,773 catalogue entries after all mechanical passes. Its before/after assertion preserves IDs, commands, conditions, dates, countries, action order and chances. Seven editorial regression tests pass. The generated Japan Rising English localisation and all thirteen command-derived Japanese minister descriptions contain no forbidden development terminology.

The main corrections are concrete:

- The 1933 welcome discusses Japan's resources, Army-Navy competition and future choices. It no longer predicts Pearl Harbor or discusses revisions, withdrawn unit classes or campaign compatibility.
- All six prewar offers retain their two bills, outcomes and waits. Twelve completion notices describe the paid outcome. Nagoya's notice says its 25-manpower workforce was assigned when work began, avoiding the appearance of a second deduction.
- Home and wartime fuel works retain every provincial increment and setup cost. Each completion describes only its chosen allocation. Storage and batch descriptions explain costs, reserve floors, capacity and cancellation without references to software limits or previous awards.
- Army production now explicitly lists mobile benefits previously omitted from its main description: Motorised Infantry -3 IC / -47.25 days, Cavalry -1.2 IC / -49.5 days, Armour -4.2 IC / -51.75 days, and transport capacity +10%. Army and naval descriptions are derived from their actual completion commands.
- Chinese expeditionary support uses liaison and home-defence language. American negotiations, campaign reserves and territorial reports describe the military situation and consequences. Settlement reports describe envoys, access and bases rather than verification procedures.
- Regional completion notices identify the ships, formations or cargo actually selected. Paid formations arrive at full strength and need time to recover organisation. Manila and Soerabaja require a maintained operational airfield or port, stated plainly.
- Reachable construction callbacks have ordinary titles such as Construction Orders and Construction Report. Legacy queued text is cleaned as well as current offers.

No literal console or dashboard wording existed in the audited Japanese catalogue. The problems were broader: descriptions explicitly discussed the engine, AI, callbacks, old revisions and repeated transaction tests. The final whole-word scan is empty for AI, dashboard, console, callback, receiver, receipt, scripted, engine, native, manual, template, legacy, retired, packet, package, docket, ledger, ahistorical, counterfactual, playtest and replay. Airfields and air groups remain normal military terms. IC, AA, morale, organisation and transport capacity remain because they are useful displayed game statistics. A technical mission describes a research delegation.

The actual installed `config/mods.csv` was read during the cold audit and still contained the earlier wording before regeneration. The source pass and regenerated Japan Rising localisation are clean; the parent build must regenerate/install its final copy before claiming the installed strings match. Two inherited localisation entries discuss AI for British and American events (9300087 and 9300187); their events belong to ENG and USA, so they do not appear in a human Japan campaign. No German or save files were edited.

The same cold review caught a mechanical error outside this text-only pass: `max_amphib_mod` defaults to setting the absolute limit. The prewar landing experiment now explicitly uses `value = 1 when = 1`, and its focused test checks an existing limit of five becomes six. Ten prewar tests pass. The final integrity pass separately handles current infrastructure and explicit decision readiness; neither is altered by the copy pass.

Files: `player_copy.py`, `PLAYER_COPY_review.py`, `PLAYER_COPY_REVIEW.json`. Run `python japan_expansion/PLAYER_COPY_review.py` after catalogue preparation. No game was launched, no save changed, and no active installation was changed by this work.
