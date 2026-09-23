# SETTLEMENT1: September 1942 continuation

Load **SETTLEMENT1 - India 2 September 1942** in **AUBM Terrain Prototype P1**
after completely restarting Darkest Hour. File:
`SETTLEMENT1_India_1942_September_2.eug`. The September 2 manual save is the
source; the September 1 autosave precedes the Indonesian settlement.

## What the save actually records

On August 30, India chose **Sponsor a sovereign Indonesian partner**. On
September 1 the Dutch accepted, India inherited the East Indies, and Indonesia
was released with an Indian guarantee. Independence was the selected outcome;
there was no missing puppet command for that choice. The protected option would
instead have cost 500 supplies and 4 dissent. No choice is changed by this repair.

India entered the Axis on August 5, inheriting its Allied and Soviet wars.
Xinjiang, already a Soviet puppet, joined the Soviet alliance and war on August 6.
This history does not substantiate a separate Indian declaration or refundable
dissent penalty. Japan remains outside India's alliance and at peace with India.

The earlier assessment that Indonesia's settlement did not exist was incorrect.
The flags inspected first were temporary selectors cleared after completion;
`ind_aubm_regional_settled_u05 = 1` and the event history establish completion.

## Recovery save

- Refreshes the existing fictional reserve officers' portrait references using
  the installed CONTINUE1 roster. This changes 347 picture fields, including
  references nested inside assigned forces. Historical leaders are excluded.
- Transfers Indian title to four former Dutch provinces, IDs **1639, 1652,
  1653, 1656**, to independent Indonesia. Japan remains their controller.
- Keeps Indonesia independent. India neither receives Japan's territory nor
  declares another war. The ownership correction does not resolve occupation
  diplomatically or force Japanese withdrawal.
- Preserves every other byte outside picture fields, the save title/configuration
  reference, and the two affected owned-province lists. Verification reverses
  those edits and reconstructs the exact original save.
- Preserves units, commanders' statistics and assignments, production, money,
  supplies, dissent, manpower, wars, alliances, event queues, flags and history.

The original manual save and autosave remain available. Installation also backs
them up together with every overwritten event module. Exact paths and hashes
are in `build/settlement1/manifest.json` and installed `SETTLEMENT1.json`.

## Shared mod correction

The same leftover-title problem can occur whenever an Indian scripted release
creates a state while another power occupies some of its territory. After each
covered release, a single next-day callback checks for remaining Indian-owned
territory in that country's release list. It transfers title only if:

- the released state exists and is independent or India's puppet;
- India is sovereign and at peace with that state;
- the province is that state's core and is not an Indian core;
- India still owns it, but neither India nor rebels control it.

The documented `secedeprovince ... when = 1` form preserves third-country
control when India does not control the province. The callback does nothing
after a failed release or if a rival has made the new state a puppet. It changes
no peace, alliance, access, army, reward or production state.

One shared generator covers **231 releasable country tags** across the Indian
event modules. These are hidden, queued-only helpers, with no date scanning,
polling loops or new visible decisions. They run once for a release attempt.
Existing stock events and manual diplomacy releases are outside this patch.
U03 and U04 have no revolt definitions in this installation and are excluded;
their existing release options remain a separate audit finding. This is not
certification of all surrender, puppet or alliance event chains.

The generic independent/puppet settlement buttons now state the distinction.
The Batavia description retains the costs and warns that Japan's troops will
not leave automatically. The Xinjiang description explains why Soviet puppets
and enemies cannot offer neutral transit and points to the existing Afghan
corridor. No free corridor or extra declaration is introduced.

`tools/aubm_release_ownership.py` is composed at the end of the future build, so
a rebuild retains the shared correction. The province catalogue comes from the
installed map's revolt definitions; it must be reviewed if the map changes.
Existing CONTINUE1 naval/campaign timers and diplomacy fixes are preserved.

## Suggested campaign

Keep Japan neutral for now. India is already fighting the Allies and Soviets;
a Pacific war would add naval demands without helping the current fronts.
Finish securing the Malayan approaches and convoy protection. Stabilise supply
and reinforcement spending before opening another major offensive. Keep the
independent Indonesia you selected; request military access if you want bases.

Then concentrate on one land approach to the Soviet Union. Xinjiang is already
an enemy, so no new declaration is needed. Secure the road and move into Central
Asia when supplied. Alternatively, review the existing Afghan-Central Asian
corridor, whose local conditions and foreign consent still apply. Avoid opening
both approaches and an Egyptian offensive at once. These are recommendations,
not instructions enacted in the repaired save.

## Validation limits

Tests cover failed releases, rivals, Indian cores, rebel control, preservation
of foreign occupation, repeat execution, and callback order. The installer
checks unique IDs against loaded events, validates new text budgets and image
references, proves the save's bounded changes, and verifies installed bytes.
The future compiler and CONTINUE1 regression suite are checked separately.

Execution result: **27 tests passed** (five shared-release tests and 22
compiler/CONTINUE1 regressions). All nine installed module hashes and the
recovery-save hash matched; both original saves matched their preserved copies.

These are script, simulation and save checks. Darkest Hour has not been launched
for native verification. The first in-game check is loading the named recovery,
viewing the new portraits and confirming Indonesia's ownership/Japan's control.
