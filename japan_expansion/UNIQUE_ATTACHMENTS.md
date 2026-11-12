# Japanese attachments

`unique_attachments.py` registers three new brigade types in the native predefined sequence: **b_01 / index 41**, **b_02 / index 42**, and **b_03 / index 43**. Importing the module allocates no events and changes no files. The event module owns their introductions and two free first issues; further attachments use ordinary production and operating resources.

| Attachment | First model | Base cost / days / manpower | Role and cost of choosing it |
| --- | --- | --- | --- |
| Type 93 Oxygen Torpedoes | 1935, Destroyer research 3060 | 0.65 IC / 100 days / 0 MP | +3 sea attack, +2 convoy attack; 0.55 daily supplies. Stronger surface attack than the generic torpedo fit, with higher ammunition and supply demand. Occupies a naval attachment slot that could carry AA, radar or ASW. |
| Dokuritsu Konsei Mixed Brigade | 1937, Infantry research 1100 | 3 IC / 120 days / 4 MP | +8 suppression, +8 defensiveness, +3 soft attack, +2 organisation; 0.45 supplies, no fuel, speed cap 4. A substantial occupation/defence attachment rather than a cheap Military Police duplicate; consumes more men, IC and supplies. |
| Ka-Mi Naval Tank Detachment | 1942, amphibious armour research 2050 | 4.5 IC / 140 days / 2 MP | +4 soft attack, +2 defensiveness/toughness, +3 organisation; 0.6 supplies and 1 fuel. Shore attack +15 and river attack +12 percentage points. Smaller tank complement, lower anti-armour attack and less armour coverage than a full amphibious armour brigade. |

The native early amphibious brigade costs 7 IC for 170 days, uses 2.5 manpower and 3 fuel, and has +3 soft attack with -2 defensiveness/toughness. The new detachment has +0 hard attack rather than the generic +1, and softness -2 rather than -3. Later detachment models progress to +5/+6 soft attack and +1/+2 hard attack, with fuel use 0.95/0.9. It is an infantry-assault specialist rather than full armour at a universally better price. The native `amph_armor` models and Japanese Type 2 Ka-Mi/Type 5 To-Ku names remain unchanged.

## Research and production

| Type | Model years | Required technology for each model |
| --- | --- | --- |
| b_01 | 1935, 1942, 1945, 1948 | 3060, 12000, 3080, 3780 |
| b_02 | 1937, 1939, 1942, 1945, 1948 | 1100, 1110, 1120, 1130, 1140 |
| b_03 | 1942, 1944, 1949 | 2050, 2060, 1630 |

Every model needs both its researched technology and service year. Model zero is implicit in Darkest Hour and is never redundantly added with `new_model`. An early research completion cannot release a future-dated model. `upgrade_event_specs()` provides nine once-only resolvers so a known technology catches up when its service year arrives. The event module appends those resolvers without changing old IDs.

`latest_model_conditions(unit)` selects exactly one currently eligible model, including when the player has researched future technologies. Cross-tree research is handled explicitly: 2050 plus 1630 without 2060 can release b_03 model 2 in 1949 and removes every older custom model. Researching 2060 later cannot bring model 1 back. The equivalent sparse naval research path is covered for b_01. Model receipts and research-bonus receipts are separate; an early research bonus never prematurely closes the later model resolver.

Concrete native attachment effects are mirrored from `naval_torpedoes_s`, `police` or `amph_armor` once per researched technology. Relative assembly bonuses are first converted using the **native base model zero**, preventing the modern custom model from receiving an exaggerated relative rebate. The relevant build-time reductions are torpedoes -28 days, mixed brigades -14 and naval tanks -34. Native benefits and penalties are both retained: for example, technology 7630 adds 1 IC, reduces manpower by 0.2 and defensiveness/toughness by 1 for the naval tank detachment.

Only concrete minister `extra` effects for the matching base are copied, and only for personalities present in the Japanese roster. Existing land/naval/all group effects are not copied again. The clean-roster test copies five applicable commands for mixed brigades/naval tanks; no division-only `unit` effect is misapplied to attachments. `install_personnel()` can safely be called again after final roster writers. There are currently no active Japan catalogue production effects aimed specifically at the three native attachment bases, so the main army/naval division discounts are not duplicated onto them.

## Japan-only availability and compatibility

Brigade registration has no documented `production = no` field; none is invented. The installer writes native country `allowed_brigades` entries setting only b_01/b_02/b_03 to `no` in all 88 source-derived 1933 country blocks. The actual engine-written Japanese save establishes this separate country-level brigade-availability schema. Native technology 1010 also receives documented `deactivate_unit_type` commands for non-Japanese countries and Japan before introduction. This provides a second guard when a newly released country initialises inherited research.

Only Japanese introduction commands can activate these classes. All positive technology hooks require Japan and the correct active-class flag. Other countries researching every relevant technology receive no custom model or production permission, even after Japan has activated the globally named receipts. This is a new-1933-game design; existing saves are not migrated.

- Type 93 fits ordinary Destroyers, Light Cruisers, Heavy Cruisers and the Akizuki escort class d_13. The Akizuki's weaker base surface attack and higher cost remain, while the attachment competes for its equipment slots.
- Mixed brigades fit Infantry, Garrisons and Militia.
- Naval tank detachments fit Infantry and Marines.
- Flying boats and Teishin airborne divisions receive no land/torpedo attachment leakage. Their original allowed attachments remain intact.

## Native files and art

`install(source, target, read, write, parse, serialise)` follows `unique_divisions.install`. It edits the current target brigade registry, new model files, allowed attachment lists, brigade terrain columns and existing technology files. It preserves prior custom-division technology hooks. Repeating the research installation does not duplicate hooks or receipts. Generic attachment models are untouched.

`brigade_modifiers.csv` gains exactly three columns before `X`, with a matching EOF row. All 53 rows have 47 fields. New columns inherit their native base terrain behavior with explicit role overrides: mixed brigades gain urban/jungle defence, naval tanks gain shore/river attack. Existing columns are preserved.

The native small auxiliary atlas contains an extra unregistered final cell. Both auxiliary atlases are packaged to **44 registered cells**: `auxiliary.bmp` 704x16 and `auxiliarybig.bmp` 880x20. Registered native cells 0-40 remain pixel-exact. New cells 41-43 use native symbols with readable T93/MB/NT marks. Both files retain the native 24-bit RGB format; these source atlases are not indexed images.

Provided artwork is used for real native large attachment pictures `ill_bri_JAP_INDEX_MODEL.bmp`, 192x104, and generic `ill_bri_INDEX_MODEL.bmp` fallbacks. Event art is `jx_ARTKEY.bmp`, 400x116, matching the native newspaper asset. No invented small-brigade filename is required for gameplay. `localisation_rows()` exposes 33 type-name, description and generic/Japanese model-name pairs for insertion in the parent's loaded localisation payload before EOF.

## Validation and limits

`python japan_expansion/unique_attachments_review.py` passes **10 tests**. They cover registered indices/schema, twelve model stages, all-country initial locks, non-Japanese research/release counterfactuals, activation date/research requirements, replay protection, sparse/out-of-order upgrades, early research/year catch-up, unique free-issue model selection, native relative-rebate semantics, penalty parity, exact compatibility boundaries, unchanged generic model bytes, terrain/EOF width, preserved third-party hooks, repeat installation, old atlas pixels, distinct new symbols and 24-bit model art.

The installation test uses an isolated temporary workspace target and removes it afterwards. It reads actual Blood and Iron files and provided art. No game, save, Germany mod or active Japan installation is edited. These checks validate native file contracts and state transitions; initial parser/UI behavior, attachment assignment and combat performance still need the player's engine test. The event agent separately validates that the two free brigades enter the deployment pool through native `add_brigade value = TYPE when = MODEL` commands.
