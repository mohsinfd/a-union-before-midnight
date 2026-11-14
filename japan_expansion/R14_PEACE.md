# R14 peace and allied occupation repair

This pass changes peace execution and allied participation. It does not start the game or modify a save. The builder applies `r14_peace.apply()` after the existing catalogue, before final integrity, equipment delivery and player copy. Existing event IDs stay unchanged.

## What changes for the player

- A country can be defeated when a genuine Japanese ally or puppet holds the required cities. Friendly neutral countries and unrelated co-belligerents do not qualify.
- An existing enemy government may surrender after that coalition victory. An independent ally keeps its own sovereign land. Allocating enemy colonial territory held by that ally requires its agreement first.
- One optional diplomatic decision asks allied governments for that agreement. Each may accept or refuse; a refusal can be reconsidered after six months. Puppet occupations follow Japanese policy. The agreement grants no right to an ally's own provinces.
- Reserved Japanese bases still require prior Japanese occupation. Coalition victory does not invent a Japanese reservation on a port that Japan never held.
- A country that has already become neutral is not forcibly puppeted by an obsolete queued withdrawal or finalisation event. The implementation must carry a receipt from the actual enemy withdrawal or Japanese release.

## Pacific armistice

1. After two years of the Pacific war, hold Hawaii, Singapore and Manila for six months, keep at least six Japanese carriers and lose less than five percent of Japan.
2. America must currently have fewer than five carriers. Four cumulative carrier losses are an alternative only while America has fewer than nine carriers **and** has lost at least 15 percent of its national territory. A rebuilt American fleet therefore closes this shortcut.
3. Choose Hawaiian terms **before** Washington answers. Returning Hawaii improves relations by 35 and provides a five-year non-aggression pact. Keeping Hawaii requires America to have fewer than five carriers and either 25 percent territorial loss or ten Japanese carriers. Retention worsens relations by 60 and grants no pact.
4. Accepted terms record the eligible enemy-owned provinces before transferring them. Non-American signatories must actually belong to America's alliance and be at war with Japan. Neutral owners, independent allies' own provinces, and unrelated wars are excluded.
5. Ownership is checked before peace. A blocked handover is retried twice, then suspended without recording victory. Land already ceded stays ceded; there is no duplicate award or forced restart of a war.
6. The successful receipt records `JX_US_PEACE` and the selected `JX_US_RETURN_HAWAII` or `JX_US_KEEP_HAWAII`. These flags are the postwar-content interface. No commercial income is awarded here; the separate paid postwar purchase remains distinct.

The limited armistice remains unavailable in Germany's alliance. Formal entry is blocked while limited American or Soviet talks are pending. External diplomacy can still change an alliance, so all implementation stages independently recheck it and recover rather than making an unintended German peace.

Five-year treaty renewal is guarded by the verified return-Hawaii peace, elapsed time, absence of renewed war and a one-time consideration receipt. A stale renewal cannot grant a non-aggression treaty during a new war.

## Soviet eastern agreement

Deep Siberian objectives remain necessary. Allied captures can count, while allocations still require enemy ownership and authorised occupation. The selected direct-control or Far Eastern-client terms are recorded before acceptance, transferred once, verified, then followed by peace. The German-Soviet war and Japan's American war remain separate.

A new Far Eastern client may be created from Japan's own agreed gains. A pre-existing independent Far Eastern government cannot be seized as a free treaty reward. Local reconstruction aid has a one-time receipt.

## Technical safeguards and audit limits

Public conditions use compact, daily updated occupation flags. Each affected action immediately calls a hidden receiver that checks the actual current alliances and controllers before executing. A stale flag may leave an offer visible briefly; it cannot authorise a transfer or a peace. Hidden receivers have empty action names and contain the larger legal checks. Named action gates are tested below 3,000 characters to avoid repeating the earlier large-tooltip failure pattern.

Transfers use separate provincial authority receipts, refreshed synchronously immediately before every receiver batch. Each refresh clears its old receipt before checking the current controller, alliance and independent ally's consent. The full condition is stored once per province, keeping generated files below the earlier oversized build. Every transfer still independently checks the actual current owner and the owner's war. A cached national surrender snapshot cannot erase or replace frozen claims.

Execution receipts check an action's complete gate once immediately before its command batch. The batch can then set its pending flags or end the war without invalidating its own remaining commands. Cached actions are tested by deliberately bypassing their visible gate and executing their command list directly.

Primary engine reference: the installed `Modding documentation/event commands.txt`, especially the documented distinction between alliance and separate peace, `secedeprovince when=1/2`, and control's `-3` scope. The tests model the new ownership/controller behaviour explicitly. Native engine behaviour remains a user playtest item; no runtime launch is claimed.

Run the offline suite with `python r14_peace_review.py`. It covers both Hawaiian bargains, rebuilt American carriers, late Axis entry, separate wars, duplicate callbacks, interrupted or partly blocked transfers, allied consent and refusal, neutral ownership, stale coalition flags, Soviet cached actions, country finalisation after external peace, and treaty renewal during war.
