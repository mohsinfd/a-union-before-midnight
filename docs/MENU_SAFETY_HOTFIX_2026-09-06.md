# MENU-SAFETY1 — safe Cabinet exits

Local hotfix for Alpha 27 / HYBRID-WORLD1, 6 September 2026.

## Resume this campaign

Restart Darkest Hour with **AUBM Terrain Prototype P1** selected. Load
**AUBM_1939-01-01_safe_cabinet**, dated **1 January 1939**.
No new campaign is needed. The original autosave remains untouched.

When the Tokyo/Sovereign War Cabinet appears, use **Cancel - close without changes**.
Do not join Japan or withdraw merely to close the menu. Cancel ends the current
menu chain without scheduling another menu. Any menu already pending in the save
is preserved and can also be cancelled.

## What changed

- Added a human-only, effect-free Cancel action to 39 connected Cabinet, coalition,
  theatre and strategic-route menus. It is placed before the existing actions and
  has no peace, war, alliance, resource or cooldown condition.
- Preserved every original event ID, existing action and trigger. AI choices are
  unchanged: the additional option is only available to human players.
- Clarified the Delhi–Tokyo board: its multi-theatre ledger requires the wartime
  charter, a continuing Japanese relationship, and 1937 or later. Waiting at peace
  alone cannot unlock it.
- The generated strategic-route file and build checks now retain and validate
  these exits, preventing regeneration from silently removing them.

## What did not change

No campaign time, wars, alliances, compact commitments, dissent, resources, units,
technology, production, event history or pending events were changed in the save.
The separately named copy differs only in its companion settings filename; those
settings are copied exactly. The earlier missing route-file repair is already
present in this latest autosave and was not added a second time.

Only four event files in the active prototype installation were replaced. Their
original bytes and the original save pair are backed up under
`tmp/menu-safety-2026-09-06/backup` in the maintained repository. The installation
receipt is also recorded as `MENU_SAFETY_HOTFIX.json` in the prototype mod.
The other installation, visuals, loading screen and base Alpha 27 version label
were not changed. This is a local menu hotfix, not a new alpha release.

The known Africa milestone and final China-posture award issues are outside this
hotfix. No victory conditions or alliance eligibility rules were changed.

## Verification

Static checks cover all 39 exits, byte preservation of original event choices,
generator reproducibility, Japanese partnership rules, wartime systems and the
Cabinet. Save verification compares both the complete original bytes (allowing
only the settings-path substitution) and the full parsed gameplay state.

Darkest Hour's installed modding documentation explicitly supports additional
unnumbered `action` blocks; the base game also uses them alongside `action_a`.
No game was launched or advanced for this repair. In-engine confirmation is still
needed: after reloading, verify the Tokyo/Sovereign menu displays Cancel and that
selecting it leaves the compact intact and does not reopen the menu by itself.
