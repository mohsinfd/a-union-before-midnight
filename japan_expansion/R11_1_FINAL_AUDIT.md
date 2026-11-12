# R11.1 final cold audit

This audit found real faults in R11 that its earlier event-state tests did not model. R11.1 fixes the command contracts and player text without adding event IDs. The game is not launched. Saved campaigns and the separate Germany Overhaul installation are untouched.

## Faults corrected

1. **Manual decisions could remain disabled.** Darkest Hour's shipped `event commands.txt`, Decisions concept point 6, says an absent or empty `decision_trigger` falls back to `trigger`. R11 deliberately disabled automatic human activation through that trigger, while leaving many readiness sections empty. R11.1 gives all 89 affected decisions an explicit readiness condition. Visibility, research, money and map requirements still apply. The validator now rejects an empty Japanese readiness block.
2. **Landing exercises could set the assault limit to one.** The native `max_amphib_mod` command defaults to SET; `when=1` means ADD. The landing-trials result now explicitly adds one to the existing limit. A nonzero-limit test checks 5 becomes 6, not 1.
3. **US support deliveries lacked complete branch and due-date guards.** Separate choice markers and saved funding dates now protect both programmes, with exact cancellation refunds. Revised Chinese aid and regional deliveries independently check their due dates and controller. Early, wrong-choice and repeated deliveries are inert.
4. **Damaged industrial infrastructure could pass an eligibility check.** Infrastructure floors now test current size with `when=now`; construction capacity caps still correctly test maximum size. A city at maximum infrastructure 60 but current infrastructure 20 cannot receive new factories until repaired.
5. **The player-operated launcher expected an obsolete validation status.** The Alpha2 desktop shortcut points to the intended Steam installation. Its PowerShell script now accepts the current validated status and checks that the installation receipt matches the version and destination. The audit parses this script and reads shortcut metadata; it never executes the launcher.
6. **Unit strength was previously inferred from the creation default.** R11.1 explicitly restores only each freshly delivered formation to its existing maximum strength, using the documented named `damage_division` strength-gain command. It does not raise strength caps, attach brigades, restore the whole army or grant organisation. Japanese awards and both American reserve waves are covered. Distinct Western/Central Reserve names prevent a later US wave from healing wounded first-wave units.
7. **Aircraft and ships could be offered after their facilities were destroyed.** Manila air deliveries require a current level-one airfield; Soerabaja ship deliveries require a current level-one port. The same condition governs funding, delivery and refund. Complete model-specific manpower and other costs remain reserved at funding.
8. **The game text contained development explanations and confusing payment notices.** A text-only pass rewrites 356 catalogue entries. It removes console/dashboard/AI/software terminology, describes each selected reward in its completion notice, and separates the original payment from delivery. Exact costs, statistics and waits remain. The pass asserts that it changes no command, condition, ID, date, chance or action order.

## Unit delivery evidence

The shipped command documentation distinguishes `add_division` from an unfunded `build_division` queue entry. New paid units follow an `add_corps` at a verified land/air/naval site. No award uses a negative damaged-unit creation argument or an attachment argument. Native model research and full manpower costs are checked. Named strength restoration then clamps each created formation to its existing maximum, normally 100 for these models. Organisation needs time to recover after deployment; later fighting, supply losses or mobilisation rules still apply.

Fourteen possible Japanese unit awards across the eight military alternatives are checked individually. The American reserve alternatives retain their exclusive researched 1939/1936 paths, six actual divisions per wave and a maximum of twelve across both waves. Their manpower and supply bills remain unchanged. Existing small island garrisons retain their deliberate quarter-strength establishment.

## Installation and reproducibility

The intended installation is `C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\Japan Rising JX1 Alpha2`. Use the **Japan Rising JX1 Alpha2** desktop shortcut and confirm **R11.1** in the scenario and welcome event. The launcher's selected mod, executable working directory, script syntax, manifest, actual registered event files and engine-loaded `config/mods.csv` are checked without starting the game.

The final receipt records the installed validation results. `FINAL_INSTALL_REVIEW.json` records the selected installation, shortcut and file hashes. `EQUIPMENT_DELIVERY_AUDIT.md` records native command evidence, models, crew costs, strength checks and installed parity. `PLAYER_COPY_REVIEW.md` records the editorial scope. The complete event matrix tests eligibility and paid delivery paths; the final integrity tests specifically exercise the native semantics the older model missed.

These are native-contract, source and installed-file checks. They do not substitute for observing engine deployment, the UI, supply handling or a multi-year Hard campaign. The previous assertion that R11 was ready based solely on the older tests was too confident.
