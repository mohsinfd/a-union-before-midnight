# CLEANUP1 shared withdrawal safety hotfix

September 8, 2026. Scoped follow-up; no new campaign rewards or objectives.

The cleanup compiler now applies one implementation to all four existing coercive puppet exits: both Nanjing offers, Indochina, and Siam. Country-specific objectives remain in the authored events. A newly added, unregistered end-puppet/leave-alliance chain in the settlement module fails compilation.

Before an accepting foreign government leaves, the event records India's wars against every supported country other than the withdrawing country. Ratification requires the country to exist, have no master, belong to no alliance, and be out of war. India must still be fighting Japan and every recorded other opponent.

Indian-puppet choices now issue the puppet command first and check the actual relationship one day later. Existing rewards, completion flags, and follow-up events are withheld until that check passes. A failed check pays nothing and does not redeclare a war or fabricate a rollback. Independence choices retain their existing rewards but require the same detachment/war checks.

Continue the existing `CLEANUP1_India_1942-02-01.eug` copy after fully restarting the game. This hotfix does not edit that save or the original autosave. Existing pending withdrawals that occurred before the hotfix have no historical war snapshot; their ratification can require the continuing Japan war, but cannot reconstruct other wars already lost. Already completed settlements are not replayed or retroactively repaired.

Verification is executable script checks and installed-file hashes, not a Darkest Hour engine playtest. In particular, engine behavior of alliance withdrawal and puppet creation still needs confirmation during play. The patch detects invalid outcomes and withholds success; it cannot guarantee engine-level war preservation.

Implementation: `tools/aubm_shared_withdrawal.py`, applied by `tools/build_aubm_cleanup.py`. Regression coverage: `tools/test_aubm_shared_withdrawal.py`. The installed build remains 27-CLEANUP1, with the latest timestamp in `CLEANUP1.json` identifying this hotfix installation.
