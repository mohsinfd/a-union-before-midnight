# Candidate 1: fresh-campaign event redesign

This is a separate script candidate, not the installed play version. The game
has not been launched and the existing campaign has not been changed. Do not
copy the staged event folder into the active installation.

## Changes collected in this candidate

- **Less administration:** redundant route boards and secondary ledgers close
  harmlessly. Reviewed campaign opportunities check current partners, enemies,
  territory and earned milestones instead of requiring repeated route approval.
  Real local choices and one-time rewards remain; this is not the deletion of
  every branch or every historical flag in the mod.
- **Japan as aggressor:** existing foreign observers can record Japanese
  aggression from 1933 without an Indian route opt-in. One notice offers a later,
  optional response. Proof is retained after the original victim's war ends.
  An independent India can already be fighting the Soviets; intervention still
  requires its own valid diplomatic situation and explicit declaration.
- **Peace and puppets:** a common withdrawal implementation covers Siam,
  Indochina and the Nanjing client government. Benefits require the expected
  government and war state. General peace actions require the authority to sign
  and describe full coalition peace, not a falsely promised separate peace.
  Japanese and Chinese stock settlement safeguards are staged alongside them.
- **Replies belong to an offer:** the 210-country global, ten-country regional
  and eight-country bespoke armistice families receive ownership and closure
  checks. Withdrawal uses a labelled 90-day cooldown. The regional and bespoke
  families serialize that cooldown within their own family; other families stay
  usable. Pending offers remain withdrawable if their recipient disappears.
  Full/limited dissent benefits follow peace, rather than being collected before
  cancelling. In the eight-country bespoke family, foreign access and improved
  relations also wait for observed peace. Existing shared callbacks still cannot
  identify arbitrary old-save delivery generations.
- **Smaller safety checks:** the withdrawal action was reduced from 1,029
  commands to at most 17. It checks continued Indian war with Japan and snapshots
  Soviet, British, German and American wars. It does not verify every other war
  in the world, and a post-command check cannot undo an engine-created peace.
- **Navy:** four fleet/capital appropriations are cheaper; 65 unintended loose
  brigade grants are removed from the reviewed procurement families. Later
  programmes unlock at roughly 63–67% of the preceding requested schedule,
  measured by elapsed time since authorisation, not actual queue completion.
  Daily production funding remains necessary.
- **Dockyards and debt:** the standard naval build-time modifier is 25 points
  in peace and 50 in war, with paired transitions to prevent stacking. Existing
  legacy modifier differences are retained. Further borrowing is blocked at the
  fourth debt tier or during overhang; repayment remains available.
- **Economic choices:** six main investment decisions now distinguish factories,
  research, transport and immediate stores. They are not claimed to be equally
  valuable in every situation.
- **Nepal and Bhutan:** verified voluntary mergers become national territory
  after 1,080 days. Conquered territory needs a costly integration project and
  1,800 days. Paid renewed offers become available after 360 days following
  refusal. [Exact odds, costs and conditions](HIMALAYAN_MERGERS.md).
- **Twelve optional Indian stories:** sporting, cultural, relief, harbour and
  home-front choices supplement the economic stories. At most one is offered
  per calendar month; each can be deferred freely and completed once. No story
  silently commits India to an alliance.
- **Readable identification and text:** known generated funding-summary helper
  overrides are removed; revised descriptions and buttons have byte budgets.
  The scenario title and opening event explicitly identify the unverified
  Candidate 1. Main-menu artwork has not been replaced.

The earlier [navy/economy specification](EVENT_REDESIGN_STAGE4_REVIEW.md) contains
exact procurement prices and timing. Its Stage4-only caveats are historical;
this document and the generated manifest describe the current combined stage.

## Validation and remaining work

**Final validation: all 318 redesign tests passed** in the frozen combined
toolchain (491.158 seconds). Command:
`python -m unittest discover -s tools -p "test_aubm_redesign*.py"`.
This includes the integrated build, regional disappearance/refusal recovery,
stale bespoke ratifier, all global armistice families, stock adapters, naval
modifiers, stories and Himalayan follow-ups. The earlier 279-test run and
intermediate ten-test build run are superseded by this final combined run.

The combined build completed: **5,553 original events preserved, 3,062 existing
blocks changed, 32 registered additions, 5,585 staged events**. The additions
are twelve stories, fourteen Himalayan follow-ups and six ported safety
callbacks. No custom duplicate IDs or missing callback references were found.
All forty installed-only custom IDs have an explicit fresh-campaign disposition;
that does not establish complete semantic parity with the installed compiler.

The presentation audit found **zero hard byte-budget/control-code errors** and
**zero remaining generated funding helpers**. Its conservative screening still
flags 1,826 events for possible wrapping, conditional-button count or large
conditions. Those are review candidates, not 1,826 proven broken windows and
not proof of visual correctness. The original colour complaint is not yet
verified as resolved in the engine.

The build rechecked authored modules, the source scenario, toolchain, installed
custom/stock event inputs and the protected 9 May 1942 save. All were unchanged
during artifact generation. Nothing was installed or launched.

Script tests are not native engine tests. Coverage inventories every custom event;
an inventory or a template-wide fix does not establish a full narrative and
lifecycle audit of every individual event.

Before a release, validate a separate fresh-1933 game, diplomacy/peace/puppet
transitions, delayed replies across save/reload, naval timing and actual popup
readability. The remaining installed-compiler reconciliation categories are
Japanese-hostility exclusions, decision prerequisites/single-use protection, and
presentation/AI behavior; existing partial fixes do not sign off those whole
categories. Complete these and the event-level review identified in the reports.
There is no old-save
migration or compatibility promise for this redesign.

Artifacts are under `build/redesign`: `manifest.json`, `coverage.json`,
`reviews.json`, `reconciliation.json`, `presentation-audit.json` and the exact
generated `INDIAN_STORIES.md` text preview. These explicitly retain unverified
and pending statuses rather than treating passing script tests as release proof.
