# BALANCE1 playtest repair overlay

Scope: fresh-campaign repairs explicitly authorised on 13 September 2026.
The earlier observation-only restriction in PLAYTEST_FEEDBACK_OPEN.md is
superseded by that authorisation. This module does not install anything, alter
saves, rebalance the navy or economy, or change peace/puppet commands.

Implementation: `tools/aubm_balance1_playtest.py`, a pure
`transform(files) -> (updated_files, records)` function. Input keys are
slash-relative installed paths. It changes 21 existing events in ten files
and appends four hidden events. Reapplication is idempotent; partial overlays
and reserved-ID collisions fail closed. No old event ID is removed.

## Concrete repairs

| Event | Fresh-campaign change |
|---|---|
| 9270101, The Village's Share | Land reform dissent +5 becomes +1. Property settlement +4 becomes +1; revenue 500 becomes 350 and recruit loss 15 becomes 5. Irrigation keeps its more costly infrastructure and calming role. |
| 9271301, Civil Service Settlement | Provincial recruitment no longer adds two dissent; its money cost becomes 100, equal to the professional service. Existing manpower/transport versus industrial choice remains. |
| 9271302, Princes and Union | Negotiated accession dissent -4 becomes -2. Statutory integration +5 becomes +1, revenue 200 becomes 150. Existing infrastructure, manpower and professional-service differences remain. |
| 9271303, Communal Compact | Plural safeguards -5 becomes -2 dissent. Civil code +2 becomes zero; keeps 30 recruits and its research point. Text correctly says either choice permits the later citizenship bill. |
| 9271304, Equal Citizenship | Enforceable rights no longer adds three dissent; recruits 35 become 45. Gradual reform retains its cheaper calming option. |
| 9271305, Burma | Autonomy dissent -4 becomes -2. Eastern administration +3 becomes zero and adds 20 recruits. Neither releases Burma; infrastructure and policy differences remain. |
| 9280300, League | Decolonisation dissent +2 becomes -1 and brings ten volunteers. Sovereignty also eases dissent by one. Relations, money and intervention differentiate the three choices; no bloc is selected. |
| 9280301, London Settlement | Commercial dissent -2 becomes -1. Defence supplies cost 400 becomes 250. Clean break removes +3 dissent and retains 120 money, at its existing large diplomatic cost. |
| 9270300, Rebuild Army | Citizen dissent becomes zero; mobile becomes +1. Professional alternative adds +2 infantry morale. Text identifies mobile formations as cavalry/infantry, not tanks; existing formations, payments and research-team wake remain. |
| 9271202, Quetta-Delhi | General school adds +3 HQ organisation. Branch schools cost 175 rather than 225 money and add +3 morale to mountain troops/marines. No broad global combat buff. |
| 9271203, Standing Divisions | Smaller cadre costs 100 money/300 supplies instead of 150/400; professionalism penalty becomes +1, with +2 infantry morale. Larger corps remains available. Both actions and event eligibility now check money, supplies and crew costs. |
| 9271001, Flying Schools | Central schools add +2 air organisation, making training quality compete with reserve clubs' manpower and broader basing. No aircraft are promised by this event. |
| 9280111, Provincial Forces | One-army dissent penalty removed and initial recruit debit 12 becomes 6. Territorial immediate recruits 25 become 15. Cadre debit 20 becomes 10. Existing annual recruitment differences remain. Every option releases the inherited state troops. |
| 9280152, Airfield Security | Replaces the old 6/4/8-ground-division choice with three complete aircraft/base/two-guard packages, detailed below. |
| 9280162, Operational Air Group | Description now distinguishes later production orders from the first aircraft delivered by Airfield Security. Existing one-time order and compatibility guards remain. |
| 9280303, Tokyo Proposition | Adds free defer with no bloc/channel commitment. Crucially, it does **not** set the old early-policy flag: that would block the existing late-opening condition. Offer suppressed during Japanese war or another great-power commitment/alliance. |
| 9270450, Abyssinia | Shorter plain labels and description retain the real costs, fixed outcome odds and context guards. No explicit colour-control leak was present in the installed event text. Actual colour rendering remains unverified. |
| 9281932/9281942/9281954/9281955 | Northern ledger, recognition, reversal and recovery use the same deeper objectives and a sustained-hold timer. Details below. |

### Airfield packages

All deployed at Indian-controlled Delhi, with conditional base construction in
two listed Indian-owned/controlled provinces. The field guards can be moved by
the player; garrisons need ordinary strategic redeployment. There is no promise
of automatic protection, automatic rebasing or aircraft rescue.

| Package | Delivered force | Bases | Payment |
|---|---|---|---|
| Defended hubs | 1 interceptor; 2 garrisons with AA | Delhi, Calcutta +2 each, capped at 10 | 350 money, 900 supplies, 27 manpower |
| Forward group | 1 interceptor, 1 tactical bomber; 2 militia with police | Delhi, Bombay +2 each, capped at 10 | 450 money, 1200 supplies, 27 manpower |
| Dispersed bases | 1 transport wing; 2 militia | Delhi, Karachi +2 each, capped at 10 | 250 money, 700 supplies, 23 manpower |

Crew debits conservatively cover the highest manpower requirement of all
installed models for every delivered unit/attachment. No production queue is
created here, so there is no second automatic production manpower debit.
Only valid installed brigade combinations are used. Every choice sets the
existing one-time completion flag. The later air-group expansion remains a
separate, normal-production programme, not a repeated grant.

The new package uses explicit, starting-tech-verified zero-based models:
interceptor 7 (1930), tactical bomber 5 (1932), transport aircraft 0 (1926),
garrison 4 (1931) and militia 4 (1921). These are early aircraft, not a free
latest-model grant. Ordinary research and upgrade funding remain necessary.
No new package command relies on the unverified `when = -1` convention.

### Locked units: actual cause and fix

The 1933 British Raj scenario declares eight state-force divisions locked:
type 12700, IDs 9057, 9058, 9060, 9061, 9063, 9065, 9067, 9069. No Indian
unlock commands were present in the installed Indian event files.

Every Provincial Forces choice unlocks exactly these divisions. Hidden event
9318103 also releases them at India's first war if the oath has not already
done so. Each command checks that its original division still exists. The
event does not create replacements, strengthen troops, unlock technology or
remove movement restrictions inherent to a garrison unit type.

### Northern campaign: not instant victory at Baku plus Tashkent

Provisional recognition now requires either:

- Baku, Astrakhan and Stalingrad; or
- Samarkand, Tashkent, Alma-Ata and Sverdlovsk.

The required objectives must remain held for 60 days while India is at war
with the USSR. This is a named-objective test, not a claim that the engine has
verified every intervening supply-road province. The false “connected centres”
claim has been removed.

Hidden 9318100 starts one saved 60-day callback. Hidden 9318101 checks daily
for a lost objective or ended war and invalidates that attempt. 9318102 has
no automatic date or trigger: it is the delayed callback only, rechecks the
live conditions, grants readiness if uninterrupted, and always clears the
pending timer. A broken attempt cannot revive because a city is retaken just
before the callback. A fresh full attempt starts after the old callback clears.

Daily polling can miss a loss and recovery entirely between two polls; this is
an engine-script limitation, not native proof of hour-by-hour continuity.
The invalidator also clears readiness if a centre is lost after the callback
but before recognition. Reversal suspends current leverage; recovery requires
the same fresh 60-day hold. The one-time recognition reward stays one-time.
Neither this recognition nor its callbacks makes peace or grants provinces,
independence or puppets. Final Soviet settlement conditions are unchanged.

## Checked, deliberately not duplicated

- Quetta-Delhi team 250027 already has valid `mountain_training`, skill 8,
  a 1933 start and is woken by **both** Army Oath choices. The complaint predates
  the installed correction. Creating another team or buffing every team would
  not repair a present coverage gap.
- Naval clocks, saved recovery orders, settlement fixes and all untouched
  event blocks remain byte-for-byte unchanged by this module.
- Economic feedback on reconstruction, factories, resources and Federal Works
  belongs to the separate BALANCE1 economy module. No duplicate economic pass.
- No literal Nationalise/Provincialise or London Intervention title was found
  in the current scoped files. London Settlement is the identified counterpart;
  the ambiguous nationalisation observation is not claimed separately repaired.
- New unnamed playtest bugs are not guessed at. Additional user notes still
  need a concrete reproduction or event name.

## Verification and limits

`tools/test_aubm_balance1_playtest.py` checks syntax, idempotence, partial-state
rejection, untouched-event preservation, old choice flags, package costs and
allowed brigades, crew requirements against installed models, exact locked
scenario IDs, Tokyo defer eligibility, northern map/depth/war/time gates,
loss invalidation and absence of new peace/puppet/economy commands.
It also checks every new package's explicit model against the actual starting
Indian tech applications and rejects a model already scrapped by those techs.

This is static and simulated trigger validation. No save was modified and no
game was launched by this work. Popup layout, actual AI behaviour and fresh
campaign pacing still require native playtesting after integration.
